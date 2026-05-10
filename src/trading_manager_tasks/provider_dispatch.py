"""Approval-gated provider acquisition dispatch helpers.

This module is deliberately narrow: it validates ``live_call_approval_v1`` before
any provider-backed trading-data command may run. Without the explicit execute
flag it only prints the reviewed dispatch plan.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .historical_training import prepare_layer_one_historical_training_batch
from .live_call_gate import validate_live_call_approvals
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")


@dataclass(frozen=True)
class ProviderDispatchItem:
    request_id: str
    task_key_path: str
    runtime_task_key_path: str | None
    command: list[str]
    receipt_path: str
    status: str
    return_code: int | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderDispatchSummary:
    contract_type: str
    stage_id: str
    request_count: int
    approval_id: str | None
    validation_count: int
    dispatch_count: int
    provider_calls: int
    dispatch_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    items: tuple[ProviderDispatchItem, ...]

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "stage_id": self.stage_id,
            "request_count": self.request_count,
            "approval_id": self.approval_id,
            "validation_count": self.validation_count,
            "dispatch_count": self.dispatch_count,
            "provider_calls": self.provider_calls,
            "dispatch_performed": self.dispatch_performed,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "items": [item.summary_row() for item in self.items],
        }


def _task_key_path(storage_root: Path, request: Mapping[str, Any]) -> Path:
    parameter_ref = str(request.get("parameter_ref") or "")
    prefix = "storage://trading-manager/"
    if not parameter_ref.startswith(prefix):
        raise TaskSystemError(f"unsupported parameter_ref for provider dispatch: {parameter_ref}")
    return storage_root / parameter_ref.removeprefix(prefix)


def _approved_task_key(task_key: Mapping[str, Any], approval: Mapping[str, Any]) -> dict[str, Any]:
    approved = dict(task_key)
    approved["dry_run"] = False
    controls = dict(approved.get("manager_controls") or {})
    controls["allow_live_provider_calls"] = True
    controls["approval_id"] = approval.get("approval_id")
    approved["manager_controls"] = controls
    approved["live_call_policy"] = {
        "allow_live_calls": True,
        "approval_id": approval.get("approval_id"),
        "allowed_providers": list(approval.get("allowed_providers") or []),
        "max_requests": approval.get("max_requests"),
        "expires_at_utc": approval.get("expires_at_utc"),
    }
    params = dict(approved.get("params") or {})
    params["manager_dry_run"] = False
    approved["params"] = params
    return approved


def _run_id(request_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{request_id}_approved_provider_{stamp}"


def _command(task_key_path: Path, request_id: str) -> list[str]:
    return [
        "python3",
        "-m",
        "data_feed.01_feed_alpaca_bars",
        str(task_key_path),
        "--run-id",
        _run_id(request_id),
    ]


def dispatch_layer_one_provider_acquisition(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    approval_path: Path,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    execute_approved_provider_calls: bool = False,
) -> ProviderDispatchSummary:
    """Validate approval and optionally dispatch Layer 1 Alpaca bars acquisition."""

    summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        write=False,
        persist_sql=False,
        validate_handoff=False,
    )
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    if not isinstance(approval, Mapping):
        raise TaskSystemError("approval artifact must be a JSON object")
    live_requests = []
    for row in requests:
        policy_refs = list(row.get("policy_refs") or [])
        for required_policy in ("live_call_policy_required", "live_call_approval_gate_v1"):
            if required_policy not in policy_refs:
                policy_refs.append(required_policy)
        live_requests.append(dict(row) | {"dry_run": False, "policy_refs": policy_refs})
    validations = validate_live_call_approvals(live_requests, approval)

    items: list[ProviderDispatchItem] = []
    dispatch_count = 0
    for request in live_requests:
        source_path = _task_key_path(storage_root, request)
        if not source_path.exists():
            raise TaskSystemError(f"task key does not exist: {source_path}")
        task_key = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(task_key, Mapping):
            raise TaskSystemError(f"task key must be a JSON object: {source_path}")
        runtime_task_key = storage_root / "runtime" / "approved_provider_task_keys" / request["request_id"] / "task_key.json"
        command_path = source_path
        if execute_approved_provider_calls:
            runtime_task_key.parent.mkdir(parents=True, exist_ok=True)
            runtime_task_key.write_text(json.dumps(_approved_task_key(task_key, approval), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            command_path = runtime_task_key
        command = _command(command_path, str(request["request_id"]))
        receipt_path = str(Path(str(task_key.get("output_root") or "storage")) / "completion_receipt.json")
        status = "validated_not_dispatched"
        return_code = None
        if execute_approved_provider_calls:
            result = subprocess.run(
                command,
                cwd=trading_data_root,
                env={**os.environ, "PYTHONPATH": str(trading_data_root / "src")},
                check=False,
                text=True,
                capture_output=True,
            )
            return_code = result.returncode
            status = "dispatched_succeeded" if result.returncode == 0 else "dispatched_failed"
            dispatch_count += 1
            if result.returncode != 0:
                raise TaskSystemError(f"provider dispatch failed for {request['request_id']}: {result.stderr[-500:]}")
        items.append(
            ProviderDispatchItem(
                request_id=str(request["request_id"]),
                task_key_path=str(source_path),
                runtime_task_key_path=str(runtime_task_key) if execute_approved_provider_calls else None,
                command=command,
                receipt_path=receipt_path,
                status=status,
                return_code=return_code,
            )
        )
    return ProviderDispatchSummary(
        contract_type="manager_provider_dispatch_summary_v1",
        stage_id="layer_01_market_regime.data_acquisition",
        request_count=summary.request_count,
        approval_id=str(approval.get("approval_id")) if approval.get("approval_id") else None,
        validation_count=len(validations),
        dispatch_count=dispatch_count,
        provider_calls=dispatch_count,
        dispatch_performed=execute_approved_provider_calls,
        model_activation_performed=False,
        broker_execution_performed=False,
        items=tuple(items),
    )


def write_dispatch_summary(summary: ProviderDispatchSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and optionally dispatch approved Layer 1 provider acquisition.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--approval", required=True, type=Path, help="Reviewed live_call_approval_v1 JSON artifact.")
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument(
        "--execute-approved-provider-calls",
        action="store_true",
        help="Actually run approved trading-data provider commands. Omit for validation/plan-only mode.",
    )
    args = parser.parse_args(argv)
    summary = dispatch_layer_one_provider_acquisition(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        approval_path=args.approval,
        trading_data_root=args.trading_data_root,
        execute_approved_provider_calls=args.execute_approved_provider_calls,
    )
    write_dispatch_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "ProviderDispatchItem",
    "ProviderDispatchSummary",
    "dispatch_layer_one_provider_acquisition",
    "write_dispatch_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

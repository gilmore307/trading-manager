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
from .failure_register import accepted_failure_request_ids_from_register
from .historical_training import prepare_layer_historical_training_batch
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .live_call_gate import validate_live_call_approvals
from .request_payloads import DEFAULT_STORAGE_ROOT
from .stage_coverage import collect_stage_coverage

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
    error_summary: str | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderDispatchSummary:
    contract_type: str
    stage_id: str
    request_count: int
    approval_id: str | None
    approval_validation_ref: str | None
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
            "approval_validation_ref": self.approval_validation_ref,
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


def _filter_requests(
    requests: Sequence[Mapping[str, Any]],
    *,
    symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    symbol_filter = {item.strip().upper() for item in symbols if item.strip()}
    request_filter = {item.strip() for item in request_ids if item.strip()}
    filtered = []
    for row in requests:
        symbol_ok = not symbol_filter or str(row.get("symbol") or "").upper() in symbol_filter
        request_ok = not request_filter or str(row.get("request_id") or "") in request_filter
        if symbol_ok and request_ok:
            filtered.append(dict(row))
    if symbol_filter:
        found = {str(row.get("symbol") or "").upper() for row in filtered}
        missing = sorted(symbol_filter - found)
        if missing:
            raise TaskSystemError("requested symbols are not in the planned provider batch: " + ",".join(missing))
    if request_filter:
        found_ids = {str(row.get("request_id") or "") for row in filtered}
        missing_ids = sorted(request_filter - found_ids)
        if missing_ids:
            raise TaskSystemError("requested ids are not in the planned provider batch: " + ",".join(missing_ids))
    if limit is not None:
        if limit <= 0:
            raise TaskSystemError("limit must be positive")
        filtered = filtered[:limit]
    if not filtered:
        raise TaskSystemError("provider dispatch filter selected no requests")
    return filtered


def _validate_approval_validation_artifact(
    *,
    approval_validation_path: Path | None,
    approval: Mapping[str, Any],
    model_layer: str,
    live_requests: Sequence[Mapping[str, Any]],
    execute_approved_provider_calls: bool,
) -> str | None:
    if not live_requests:
        return None
    if approval_validation_path is None:
        if execute_approved_provider_calls:
            raise TaskSystemError("executing provider calls requires --approval-validation from validate_live_call_approval_proposal.py")
        return None
    validation = json.loads(approval_validation_path.read_text(encoding="utf-8"))
    if not isinstance(validation, Mapping):
        raise TaskSystemError("approval validation artifact must be a JSON object")
    if validation.get("contract_type") != "manager_live_call_approval_proposal_validation_v1":
        raise TaskSystemError("approval validation contract_type must be manager_live_call_approval_proposal_validation_v1")
    if validation.get("approval_id") != approval.get("approval_id"):
        raise TaskSystemError("approval validation approval_id must match approval.approval_id")
    expected_stage_id = f"{model_layer}.data_acquisition"
    if validation.get("stage_id") != expected_stage_id:
        raise TaskSystemError("approval validation stage_id must match provider dispatch stage")
    expected_ids = tuple(str(row.get("request_id") or "") for row in live_requests)
    validation_ids = tuple(str(item) for item in validation.get("request_ids") or [])
    if set(expected_ids) != set(validation_ids) or len(expected_ids) != len(validation_ids):
        raise TaskSystemError("approval validation request_ids must exactly match executable live requests")
    skipped_overlap = sorted(set(validation_ids).intersection(str(item) for item in validation.get("skipped_registered_request_ids") or []))
    if skipped_overlap:
        raise TaskSystemError("approval validation includes registered skip ids: " + ",".join(skipped_overlap))
    if int(validation.get("gate_validation_count") or -1) != len(live_requests):
        raise TaskSystemError("approval validation gate_validation_count must match executable live request count")
    if validation.get("provider_calls") not in (0, None):
        raise TaskSystemError("approval validation must be plan-only with provider_calls=0")
    if validation.get("dispatch_performed") not in (False, None):
        raise TaskSystemError("approval validation must be plan-only with dispatch_performed=false")
    return str(approval_validation_path)


def dispatch_layer_provider_acquisition(
    *,
    model_layer: str = LAYER_ONE_MODEL_LAYER,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    approval_path: Path,
    approval_validation_path: Path | None = None,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    execute_approved_provider_calls: bool = False,
    continue_on_error: bool = False,
    skip_registered_failures: bool = False,
    reject_terminal_coverage: bool = False,
    database_url: str | None = None,
) -> ProviderDispatchSummary:
    """Validate approval and optionally dispatch a layer Alpaca-bars acquisition batch."""

    if model_layer not in {LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER}:
        raise TaskSystemError(f"unsupported provider dispatch model_layer: {model_layer}")
    summary, requests, _payloads, _validations = prepare_layer_historical_training_batch(
        model_layer=model_layer,
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
    selected_requests = _filter_requests(requests, symbols=symbols, request_ids=request_ids, limit=limit)
    registered_skip_ids: set[str] = set()
    registered_skip_refs: tuple[str, ...] = ()
    if skip_registered_failures:
        skip_ids, registered_skip_refs = accepted_failure_request_ids_from_register(
            database_url=database_url,
            stage_id=f"{model_layer}.data_acquisition",
            start_month=start_month,
            end_month=end_month,
        )
        registered_skip_ids = set(skip_ids)
    live_requests = []
    skipped_requests = []
    for row in selected_requests:
        if str(row.get("request_id") or "") in registered_skip_ids:
            skipped_requests.append(dict(row))
            continue
        policy_refs = list(row.get("policy_refs") or [])
        for required_policy in ("live_call_policy_required", "live_call_approval_gate_v1"):
            if required_policy not in policy_refs:
                policy_refs.append(required_policy)
        live_requests.append(dict(row) | {"dry_run": False, "policy_refs": policy_refs})
    if execute_approved_provider_calls and reject_terminal_coverage and live_requests:
        report = collect_stage_coverage(
            stage_id=f"{model_layer}.data_acquisition",
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
        )
        if report.failed_request_ids:
            raise TaskSystemError("stage has unreviewed failed requests; review/register failures before executing more live calls: " + ",".join(report.failed_request_ids))
        terminal_ids = {str(item) for item in (*report.ready_request_ids, *report.accepted_failed_request_ids)}
        repeated_ids = sorted(str(row.get("request_id") or "") for row in live_requests if str(row.get("request_id") or "") in terminal_ids)
        if repeated_ids:
            raise TaskSystemError("refusing to execute provider calls for terminal stage requests: " + ",".join(repeated_ids))
    validations = validate_live_call_approvals(live_requests, approval) if live_requests else []
    approval_validation_ref = _validate_approval_validation_artifact(
        approval_validation_path=approval_validation_path,
        approval=approval,
        model_layer=model_layer,
        live_requests=live_requests,
        execute_approved_provider_calls=execute_approved_provider_calls,
    )

    items: list[ProviderDispatchItem] = [
        ProviderDispatchItem(
            request_id=str(request["request_id"]),
            task_key_path=str(_task_key_path(storage_root, request).resolve()),
            runtime_task_key_path=None,
            command=[],
            receipt_path="",
            status="skipped_registered_accepted_failure",
            return_code=None,
            error_summary=";".join(registered_skip_refs) if registered_skip_refs else "registered accepted failure",
        )
        for request in skipped_requests
    ]
    dispatch_count = 0
    for request in live_requests:
        source_path = _task_key_path(storage_root, request).resolve()
        if not source_path.exists():
            raise TaskSystemError(f"task key does not exist: {source_path}")
        task_key = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(task_key, Mapping):
            raise TaskSystemError(f"task key must be a JSON object: {source_path}")
        runtime_task_key = (storage_root / "runtime" / "approved_provider_task_keys" / request["request_id"] / "task_key.json").resolve()
        command_path = source_path
        if execute_approved_provider_calls:
            runtime_task_key.parent.mkdir(parents=True, exist_ok=True)
            runtime_task_key.write_text(json.dumps(_approved_task_key(task_key, approval), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            command_path = runtime_task_key
        command = _command(command_path, str(request["request_id"]))
        relative_receipt_path = Path(str(task_key.get("output_root") or "storage")) / "completion_receipt.json"
        receipt_path = str((trading_data_root / relative_receipt_path).resolve()) if execute_approved_provider_calls else str(relative_receipt_path)
        status = "validated_not_dispatched"
        return_code = None
        error_tail = None
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
            error_tail = "\n".join(part for part in (result.stdout[-500:], result.stderr[-500:]) if part) if result.returncode != 0 else None
            if result.returncode != 0 and not continue_on_error:
                raise TaskSystemError(f"provider dispatch failed for {request['request_id']}: {error_tail}")
        items.append(
            ProviderDispatchItem(
                request_id=str(request["request_id"]),
                task_key_path=str(source_path),
                runtime_task_key_path=str(runtime_task_key) if execute_approved_provider_calls else None,
                command=command,
                receipt_path=receipt_path,
                status=status,
                return_code=return_code,
                error_summary=error_tail,
            )
        )
    return ProviderDispatchSummary(
        contract_type="manager_provider_dispatch_summary_v1",
        stage_id=f"{model_layer}.data_acquisition",
        request_count=len(selected_requests),
        approval_id=str(approval.get("approval_id")) if approval.get("approval_id") else None,
        approval_validation_ref=approval_validation_ref,
        validation_count=len(validations),
        dispatch_count=dispatch_count,
        provider_calls=dispatch_count,
        dispatch_performed=execute_approved_provider_calls,
        model_activation_performed=False,
        broker_execution_performed=False,
        items=tuple(items),
    )


def dispatch_layer_one_provider_acquisition(**kwargs: Any) -> ProviderDispatchSummary:
    """Backward-compatible wrapper for Layer 1 provider dispatch."""

    return dispatch_layer_provider_acquisition(model_layer=LAYER_ONE_MODEL_LAYER, **kwargs)


def write_dispatch_summary(summary: ProviderDispatchSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and optionally dispatch approved layer provider acquisition.")
    parser.add_argument("--model-layer", default=LAYER_ONE_MODEL_LAYER, choices=(LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER))
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--approval", required=True, type=Path, help="Reviewed live_call_approval_v1 JSON artifact.")
    parser.add_argument("--approval-validation", type=Path, help="manager_live_call_approval_proposal_validation_v1 artifact required when executing provider calls.")
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--symbol", action="append", default=[], help="Limit dispatch to one symbol; repeat for multiple symbols.")
    parser.add_argument("--request-id", action="append", default=[], help="Limit dispatch to one request id; repeat for multiple ids.")
    parser.add_argument("--limit", type=int, help="Limit dispatch to the first N selected requests after symbol/request filtering.")
    parser.add_argument(
        "--execute-approved-provider-calls",
        action="store_true",
        help="Actually run approved trading-data provider commands. Omit for validation/plan-only mode.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue the approved batch after an individual provider command fails, preserving per-request failure receipts for control-plane ingestion.",
    )
    parser.add_argument("--skip-registered-failures", action="store_true", help="Skip requests with accepted_skip entries in the manager failure register.")
    parser.add_argument("--database-url")
    parser.add_argument("--reject-terminal-coverage", action="store_true", help="When executing, reject request ids already ready or reviewed-terminal in stage coverage.")
    parser.add_argument("--write", action="store_true", help="Write dispatch summary JSON to --output-path.")
    parser.add_argument("--output-path", type=Path, help="Optional dispatch summary output path.")
    args = parser.parse_args(argv)
    summary = dispatch_layer_provider_acquisition(
        model_layer=args.model_layer,
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        approval_path=args.approval,
        approval_validation_path=args.approval_validation,
        trading_data_root=args.trading_data_root,
        symbols=args.symbol,
        request_ids=args.request_id,
        limit=args.limit,
        execute_approved_provider_calls=args.execute_approved_provider_calls,
        continue_on_error=args.continue_on_error,
        skip_registered_failures=args.skip_registered_failures,
        reject_terminal_coverage=args.reject_terminal_coverage,
        database_url=args.database_url,
    )
    if args.write:
        if args.output_path is None:
            raise TaskSystemError("--write requires --output-path")
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_dispatch_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "ProviderDispatchItem",
    "ProviderDispatchSummary",
    "dispatch_layer_provider_acquisition",
    "dispatch_layer_one_provider_acquisition",
    "write_dispatch_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

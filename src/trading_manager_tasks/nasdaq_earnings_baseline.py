"""Prepare Nasdaq future earnings EPS-baseline snapshot requests.

This module formalizes the accepted future EPS-consensus route. It writes
component-readable `calendar_discovery` task keys for trading-execution, but it
performs no provider calls, starts no scheduler, activates no model, and touches
no broker/account state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator, TextIO

from .request_payloads import DEFAULT_STORAGE_ROOT, storage_uri_to_local_path

DEFAULT_REQUESTED_BY = "trading-manager.nasdaq_earnings_baseline"
SOURCE_ID = "nasdaq_earnings_calendar"
TARGET_COMPONENT_ID = "calendar_discovery"
TARGET_REPO_ID = "trading-execution"
REQUEST_KIND = "expectation_baseline_snapshot"
POLICY_REFS = (
    "future_eps_consensus_snapshot_route",
    "point_in_time_baseline_capture",
    "exclude_post_event_actual_or_surprise_fields",
    "no_model_activation",
    "no_broker_execution",
)


@dataclass(frozen=True)
class NasdaqBaselineTaskKey:
    request_id: str
    snapshot_date: str
    parameter_ref: str
    local_path: str
    output_root: str
    byte_size: int
    content_hash: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NasdaqBaselinePreparationSummary:
    contract_type: str
    start_date: str
    end_date: str
    request_count: int
    task_key_count: int
    write_performed: bool
    provider_calls: int
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    task_keys: tuple[NasdaqBaselineTaskKey, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["task_keys"] = [task.summary_row() for task in self.task_keys]
        return row


def iter_dates(start_date: str, end_date: str) -> Iterator[date]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be >= start_date")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _path_date(value: date) -> str:
    return value.isoformat()


def _request_id(snapshot_date: date) -> str:
    return f"mgrreq_expectation_baseline_nasdaq_earnings_calendar_{snapshot_date.strftime('%Y_%m_%d')}"


def _parameter_ref(snapshot_date: date) -> str:
    return f"storage://trading-manager/earnings_guidance_baseline/{SOURCE_ID}/{_path_date(snapshot_date)}/task_key.json"


def _expected_outputs(snapshot_date: date) -> list[str]:
    return [f"storage://trading-execution/earnings_guidance_baseline/{SOURCE_ID}/{_path_date(snapshot_date)}/"]


def _output_root(snapshot_date: date) -> str:
    return f"storage/earnings_guidance_baseline/{SOURCE_ID}/{_path_date(snapshot_date)}"


def plan_nasdaq_baseline_snapshot_requests(
    *,
    start_date: str,
    end_date: str,
    requested_by: str = DEFAULT_REQUESTED_BY,
) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for snapshot_date in iter_dates(start_date, end_date):
        requests.append(
            {
                "request_id": _request_id(snapshot_date),
                "contract_type": "manager_request",
                "request_kind": REQUEST_KIND,
                "status": "requested",
                "requested_by": requested_by,
                "target_component_id": TARGET_COMPONENT_ID,
                "target_component_kind": "calendar_discovery",
                "target_repo_id": TARGET_REPO_ID,
                "expected_outputs": _expected_outputs(snapshot_date),
                "policy_refs": list(POLICY_REFS),
                "priority": "normal",
                "parameter_ref": _parameter_ref(snapshot_date),
                "dry_run": True,
                "snapshot_date": _path_date(snapshot_date),
                "calendar_source": SOURCE_ID,
                "baseline_type": "eps_consensus",
                "availability_note": "Future Nasdaq earnings-calendar snapshot for EPS-consensus baseline capture; provider dispatch must occur before the event date and must not use post-event actual/surprise fields as baseline values.",
            }
        )
    return requests


def _task_key_payload(request: dict[str, Any]) -> dict[str, Any]:
    snapshot_date = str(request["snapshot_date"])
    return {
        "task_id": str(request["request_id"]),
        "request_id": str(request["request_id"]),
        "bundle": TARGET_COMPONENT_ID,
        "output_root": _output_root(date.fromisoformat(snapshot_date)),
        "params": {
            "calendar_source": SOURCE_ID,
            "date": snapshot_date,
            "baseline_capture_mode": "future_pre_event_eps_consensus_snapshot",
            "manager_request_id": str(request["request_id"]),
            "manager_dry_run": bool(request.get("dry_run", True)),
        },
        "expected_outputs": list(request.get("expected_outputs") or []),
        "policy_refs": list(request.get("policy_refs") or []),
        "manager_controls": {
            "parameter_ref": str(request["parameter_ref"]),
            "allow_live_provider_calls": not bool(request.get("dry_run", True)),
            "baseline_use_policy": "use_epsForecast_only_when_captured_before_event;exclude_eps_actual_and_surprise_fields",
            "secrets_policy": "none_required_for_public_nasdaq_calendar_route",
            "model_activation_performed": False,
            "broker_execution_performed": False,
        },
    }


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def prepare_nasdaq_baseline_snapshots(
    *,
    start_date: str,
    end_date: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    write_files: bool = False,
) -> NasdaqBaselinePreparationSummary:
    requests = plan_nasdaq_baseline_snapshot_requests(start_date=start_date, end_date=end_date)
    task_keys: list[NasdaqBaselineTaskKey] = []
    for request in requests:
        payload = _task_key_payload(request)
        content = _canonical_bytes(payload)
        content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        local_path = storage_uri_to_local_path(str(request["parameter_ref"]), storage_root=storage_root)
        if write_files:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)
        task_keys.append(
            NasdaqBaselineTaskKey(
                request_id=str(request["request_id"]),
                snapshot_date=str(request["snapshot_date"]),
                parameter_ref=str(request["parameter_ref"]),
                local_path=str(local_path),
                output_root=str(payload["output_root"]),
                byte_size=len(content),
                content_hash=content_hash,
            )
        )
    return NasdaqBaselinePreparationSummary(
        contract_type="manager_nasdaq_earnings_baseline_snapshot_preparation",
        start_date=start_date,
        end_date=end_date,
        request_count=len(requests),
        task_key_count=len(task_keys),
        write_performed=write_files,
        provider_calls=0,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        task_keys=tuple(task_keys),
    )


def write_summary(summary: NasdaqBaselinePreparationSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Nasdaq future EPS-baseline snapshot task keys without provider calls.")
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--write-files", action="store_true")
    args = parser.parse_args(argv)
    summary = prepare_nasdaq_baseline_snapshots(
        start_date=args.start_date,
        end_date=args.end_date,
        storage_root=args.storage_root,
        write_files=args.write_files,
    )
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "NasdaqBaselinePreparationSummary",
    "NasdaqBaselineTaskKey",
    "plan_nasdaq_baseline_snapshot_requests",
    "prepare_nasdaq_baseline_snapshots",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

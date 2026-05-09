"""Deterministic task-system rehearsal for manager request/receipt flow.

The rehearsal exercises the control-plane lifecycle without calling providers or
mutating SQL:

manager_request_v1 -> component completion receipt -> run_manifest_v1 /
artifact_ref_v1 / ready_signal_v1 -> task_summary-like rows.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Literal, TextIO

from .control_plane import (
    TASK_PRIORITY_RANKS,
    CompletionReceiptRows,
    normalize_completion_receipt,
    persist_completion_rows,
    persist_manager_requests,
    validate_manager_request,
    write_jsonl,
)
from .monthly_backfill import DEFAULT_START_MONTH, plan_monthly_backfill_requests

DEFAULT_REHEARSAL_TS = "2026-05-09T06:00:00Z"
REHEARSAL_STATUS_PATTERN: tuple[str, ...] = ("succeeded", "partial", "failed")


def _source_id_from_request(request: Mapping[str, Any]) -> str:
    outputs = request.get("expected_outputs")
    if isinstance(outputs, Sequence) and not isinstance(outputs, (str, bytes)) and outputs:
        output = str(outputs[0]).rstrip("/")
        parts = output.split("/")
        if len(parts) >= 2:
            return parts[-2] if parts[-1].count("-") == 1 else parts[-1]
    component_id = str(request.get("target_component_id") or "component")
    return component_id


def build_rehearsal_receipt(
    request: Mapping[str, Any],
    *,
    status: str = "succeeded",
    started_at_utc: str = DEFAULT_REHEARSAL_TS,
) -> dict[str, Any]:
    """Build one deterministic component completion receipt for a request."""
    normalized = validate_manager_request(request)
    request_id = normalized["request_id"]
    source_id = _source_id_from_request(normalized)
    run_id = "run_" + request_id.removeprefix("mgrreq_")
    output_base = str((normalized.get("expected_outputs") or [f"storage://trading-data/rehearsal/{request_id}/"])[0]).rstrip("/")
    row_count = 1000 if status == "succeeded" else 400 if status == "partial" else 0
    receipt: dict[str, Any] = {
        "contract_type": "component_completion_receipt_v1",
        "request_id": request_id,
        "rehearsal_only": True,
        "runs": [
            {
                "run_id": run_id,
                "status": status,
                "started_at": started_at_utc,
                "completed_at": started_at_utc,
                "outputs": [
                    {
                        "uri": f"{output_base}/rehearsal_output.parquet",
                        "artifact_kind": "monthly_backfill_rehearsal_output",
                        "schema_ref": "monthly_backfill_output_v1",
                        "row_count": row_count,
                        "content_hash": f"sha256:rehearsal-{request_id}-{status}",
                        "media_type": "application/x-parquet",
                    }
                ]
                if status != "failed"
                else [],
                "row_counts": {source_id: row_count},
                "error": None if status != "failed" else {"type": "RehearsalProviderError", "message": "simulated provider failure"},
            }
        ],
    }
    if status == "partial":
        receipt["runs"][0]["error"] = {"type": "RehearsalPartialOutput", "message": "simulated partial month; review required"}
    return receipt


def _latest_by_request(run_rows: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    latest: dict[str, Mapping[str, Any]] = {}
    for row in run_rows:
        latest[str(row["request_id"])] = row
    return latest


def _signals_by_run(signal_rows: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {str(row["producer_run_id"]): row for row in signal_rows}


def _artifact_counts_by_run(artifact_rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in artifact_rows:
        run_id = str(row["producer_run_id"])
        counts[run_id] = counts.get(run_id, 0) + 1
    return counts


def build_rehearsal_task_summary(
    requests: Sequence[Mapping[str, Any]],
    *,
    run_rows: Sequence[Mapping[str, Any]],
    artifact_rows: Sequence[Mapping[str, Any]],
    ready_signal_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build task_summary-like rows from in-memory rehearsal rows."""
    latest_run = _latest_by_request(run_rows)
    signal_by_run = _signals_by_run(ready_signal_rows)
    artifact_counts = _artifact_counts_by_run(artifact_rows)
    summary: list[dict[str, Any]] = []
    for request in requests:
        normalized = validate_manager_request(request)
        run = latest_run.get(normalized["request_id"])
        signal = signal_by_run.get(str(run["run_id"])) if run else None
        task_status = signal.get("status") if signal else run.get("status") if run else normalized["status"]
        summary.append(
            {
                "request_id": normalized["request_id"],
                "request_kind": normalized["request_kind"],
                "task_status": task_status,
                "request_status": normalized["status"],
                "priority": normalized["priority"],
                "priority_rank": TASK_PRIORITY_RANKS[normalized["priority"]],
                "deadline_at_utc": normalized.get("deadline_at_utc"),
                "target_repo_id": normalized["target_repo_id"],
                "target_component_id": normalized["target_component_id"],
                "target_component_kind": normalized["target_component_kind"],
                "dry_run": normalized["dry_run"],
                "latest_run_id": run.get("run_id") if run else None,
                "latest_run_status": run.get("status") if run else None,
                "latest_ready_signal_id": signal.get("ready_signal_id") if signal else None,
                "latest_ready_signal_status": signal.get("status") if signal else None,
                "latest_ready_signal_review_required": signal.get("review_required") if signal else None,
                "latest_ready_signal_blocking_reason": signal.get("blocking_reason") if signal else None,
                "artifact_count": artifact_counts.get(str(run["run_id"]), 0) if run else 0,
            }
        )
    return sorted(summary, key=lambda row: (row["priority_rank"], row["deadline_at_utc"] or "9999-99-99T99:99:99Z", row["request_id"]))


def _rehearsal_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return a request copy with rehearsal-only ids/refs to avoid live collisions."""
    normalized = validate_manager_request(request)
    original_request_id = normalized["request_id"]
    rehearsal_id = "mgrreq_rehearsal_" + original_request_id.removeprefix("mgrreq_")
    output_source = _source_id_from_request(normalized)
    output_month = str(request.get("month") or "unknown_month")
    normalized.update(
        {
            "request_id": rehearsal_id,
            "expected_outputs": [f"storage://trading-manager/rehearsals/monthly_backfill/{output_source}/{output_month}/outputs/"],
            "parameter_ref": f"storage://trading-manager/rehearsals/monthly_backfill/{output_source}/{output_month}/task_key.json",
            "dry_run": True,
        }
    )
    return normalized


def rehearse_monthly_backfill_task_system(
    *,
    start_month: str = DEFAULT_START_MONTH,
    end_month: str,
    limit: int = 3,
    scenario: Literal["success", "mixed"] = "mixed",
    requested_by: str = "openclaw",
) -> dict[str, Any]:
    """Run an in-memory monthly backfill task-system rehearsal."""
    if limit < 1:
        raise ValueError("limit must be >= 1")
    planned = plan_monthly_backfill_requests(start_month=start_month, end_month=end_month, requested_by=requested_by)[:limit]
    requests = [_rehearsal_request(request) for request in planned]
    run_rows: list[dict[str, Any]] = []
    artifact_rows: list[dict[str, Any]] = []
    ready_signal_rows: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    for index, request in enumerate(requests):
        status = "succeeded" if scenario == "success" else REHEARSAL_STATUS_PATTERN[index % len(REHEARSAL_STATUS_PATTERN)]
        receipt = build_rehearsal_receipt(request, status=status)
        receipts.append(receipt)
        rows = normalize_completion_receipt(
            receipt,
            request_id=request["request_id"],
            component_id=request["target_component_id"],
            component_kind=request["target_component_kind"],
            repo_id=request["target_repo_id"],
            receipt_uri=f"storage://trading-manager/rehearsals/monthly_backfill/{request['request_id']}/completion_receipt.json",
            receipt_hash=f"sha256:rehearsal-receipt-{request['request_id']}",
            parameter_ref=request.get("parameter_ref"),
            consumer_hint="monthly_backfill_rehearsal",
        )
        run_rows.extend(rows.run_manifests)
        artifact_rows.extend(rows.artifact_refs)
        ready_signal_rows.extend(rows.ready_signals)
    summary = build_rehearsal_task_summary(requests, run_rows=run_rows, artifact_rows=artifact_rows, ready_signal_rows=ready_signal_rows)
    return {
        "contract_type": "manager_task_system_rehearsal_v1",
        "rehearsal_only": True,
        "scenario": scenario,
        "request_count": len(requests),
        "requests": requests,
        "receipts": receipts,
        "run_manifests": run_rows,
        "artifact_refs": artifact_rows,
        "ready_signals": ready_signal_rows,
        "task_summary": summary,
    }


def persist_rehearsal(rehearsal: Mapping[str, Any], *, database_url: str | None = None) -> None:
    """Persist rehearsal-only request and completion rows to manager SQL tables."""
    persist_manager_requests(rehearsal["requests"], database_url=database_url)
    persist_completion_rows(
        CompletionReceiptRows(
            run_manifests=list(rehearsal["run_manifests"]),
            artifact_refs=list(rehearsal["artifact_refs"]),
            ready_signals=list(rehearsal["ready_signals"]),
        ),
        database_url=database_url,
    )


def write_rehearsal_output(rehearsal: Mapping[str, Any], *, output: TextIO, output_format: Literal["json", "jsonl"] = "json") -> None:
    if output_format == "jsonl":
        rows: list[dict[str, Any]] = []
        rows.extend({"section": "manager_request", **row} for row in rehearsal["requests"])
        rows.extend({"section": "run_manifest", **row} for row in rehearsal["run_manifests"])
        rows.extend({"section": "artifact_ref", **row} for row in rehearsal["artifact_refs"])
        rows.extend({"section": "ready_signal", **row} for row in rehearsal["ready_signals"])
        rows.extend({"section": "task_summary", **row} for row in rehearsal["task_summary"])
        write_jsonl(rows, output)
        return
    json.dump(rehearsal, output, indent=2, sort_keys=True)
    output.write("\n")


def rehearsal_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run an in-memory manager task-system rehearsal without provider calls or SQL writes.")
    parser.add_argument("--start-month", default=DEFAULT_START_MONTH)
    parser.add_argument("--end-month", default=DEFAULT_START_MONTH)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--scenario", choices=["success", "mixed"], default="mixed")
    parser.add_argument("--requested-by", default="openclaw")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json")
    parser.add_argument("--write", action="store_true", help="Persist rehearsal-only rows to manager SQL tables.")
    parser.add_argument("--database-url")
    args = parser.parse_args(argv)
    rehearsal = rehearse_monthly_backfill_task_system(
        start_month=args.start_month,
        end_month=args.end_month,
        limit=args.limit,
        scenario=args.scenario,
        requested_by=args.requested_by,
    )
    if args.write:
        persist_rehearsal(rehearsal, database_url=args.database_url)
    write_rehearsal_output(rehearsal, output=sys.stdout, output_format=args.format)
    return 0


__all__ = [
    "build_rehearsal_receipt",
    "build_rehearsal_task_summary",
    "rehearse_monthly_backfill_task_system",
    "persist_rehearsal",
    "rehearsal_main",
    "write_rehearsal_output",
]

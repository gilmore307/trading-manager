"""Manager failure register helpers.

Failed component requests are durable facts. A failure can be corrected,
retried, left unresolved, or accepted as a normal skip only after agent review.
The register preserves the failed state instead of rewriting it to ready.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError, _db_url, load_json_or_jsonl, write_jsonl

FAILURE_REGISTER_COLUMNS = (
    "failure_id",
    "contract_type",
    "request_id",
    "run_id",
    "stage_id",
    "target_component_id",
    "source_id",
    "symbol",
    "start_month",
    "end_month",
    "failure_status",
    "failure_kind",
    "observed_status",
    "error_summary",
    "agent_review_ref",
    "operator_approval_ref",
    "correction_ref",
    "skip_future_matching",
    "evidence_refs",
    "note",
)

FAILURE_STATUSES = {"observed", "agent_review_required", "retry_required", "corrected", "accepted_skip", "unresolved"}


def _stable_token(value: str) -> str:
    token = "".join(char.lower() if char.isalnum() else "_" for char in value)
    return "_".join(part for part in token.split("_") if part)[:120] or "unknown"


def validate_failure_register_row(row: Mapping[str, Any]) -> dict[str, Any]:
    request_id = str(row.get("request_id") or "").strip()
    if not request_id:
        raise TaskSystemError("failure register row missing request_id")
    stage_id = str(row.get("stage_id") or "").strip()
    if not stage_id:
        raise TaskSystemError("failure register row missing stage_id")
    target_component_id = str(row.get("target_component_id") or "").strip()
    if not target_component_id:
        raise TaskSystemError("failure register row missing target_component_id")
    failure_status = str(row.get("failure_status") or "observed").strip().lower()
    if failure_status not in FAILURE_STATUSES:
        raise TaskSystemError(f"unsupported failure_status: {failure_status}")
    failure_kind = str(row.get("failure_kind") or "unclassified_failure").strip()
    if not failure_kind:
        raise TaskSystemError("failure register row missing failure_kind")
    agent_review_ref = str(row.get("agent_review_ref") or "").strip() or None
    if failure_status in {"accepted_skip", "corrected"} and not agent_review_ref:
        raise TaskSystemError(f"{failure_status} failure rows require agent_review_ref")
    skip_future_matching = bool(row.get("skip_future_matching", False))
    if skip_future_matching and failure_status != "accepted_skip":
        raise TaskSystemError("skip_future_matching is allowed only for accepted_skip failures")
    failure_id = str(row.get("failure_id") or "").strip() or f"fail_{_stable_token(request_id)}"
    evidence_refs = row.get("evidence_refs") or []
    if isinstance(evidence_refs, str):
        evidence_refs = [evidence_refs]
    if not isinstance(evidence_refs, list):
        raise TaskSystemError("evidence_refs must be a list")
    return {
        "failure_id": failure_id,
        "contract_type": "manager_failure_register",
        "request_id": request_id,
        "run_id": row.get("run_id"),
        "stage_id": stage_id,
        "target_component_id": target_component_id,
        "source_id": row.get("source_id"),
        "symbol": str(row.get("symbol") or "").upper() or None,
        "start_month": row.get("start_month"),
        "end_month": row.get("end_month"),
        "failure_status": failure_status,
        "failure_kind": failure_kind,
        "observed_status": row.get("observed_status"),
        "error_summary": row.get("error_summary"),
        "agent_review_ref": agent_review_ref,
        "operator_approval_ref": row.get("operator_approval_ref"),
        "correction_ref": row.get("correction_ref"),
        "skip_future_matching": skip_future_matching,
        "evidence_refs": evidence_refs,
        "note": row.get("note"),
    }


def persist_failure_register_rows(rows: Sequence[Mapping[str, Any]], *, database_url: str | None = None) -> None:
    if not rows:
        return
    import psycopg
    from psycopg.types.json import Jsonb

    normalized = [validate_failure_register_row(row) for row in rows]
    columns = FAILURE_REGISTER_COLUMNS
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)
    update_sql = ", ".join(f"{column}=EXCLUDED.{column}" for column in columns[1:]) + ", updated_at_utc=NOW()"
    sql = f"INSERT INTO trading_manager.failure_register ({col_sql}) VALUES ({placeholders}) ON CONFLICT (failure_id) DO UPDATE SET {update_sql}"
    values = [tuple(Jsonb(row.get(column) or []) if column == "evidence_refs" else row.get(column) for column in columns) for row in normalized]
    with psycopg.connect(_db_url(database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(sql, values)
        connection.commit()


def mark_failure_register_requests_corrected(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    corrected_request_refs: Mapping[str, str],
    database_url: str | None = None,
) -> int:
    """Mark stale failure-register rows corrected after latest receipts succeed."""

    if not corrected_request_refs:
        return 0
    rows = fetch_failure_register_rows(
        database_url=database_url,
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
    )
    mutable_statuses = {"observed", "agent_review_required", "retry_required", "unresolved"}
    corrected_rows: list[dict[str, Any]] = []
    for row in rows:
        request_id = str(row.get("request_id") or "")
        correction_ref = corrected_request_refs.get(request_id)
        if not correction_ref or str(row.get("failure_status") or "") not in mutable_statuses:
            continue
        evidence_refs = row.get("evidence_refs") or []
        if isinstance(evidence_refs, str):
            evidence_refs = [evidence_refs]
        corrected_rows.append(
            {
                **row,
                "failure_status": "corrected",
                "agent_review_ref": "manager_provider_stage_reconcile:latest_receipt_succeeded",
                "correction_ref": correction_ref,
                "evidence_refs": [*evidence_refs, correction_ref],
                "note": "Latest provider completion receipt succeeded; previous failure is retained as corrected and no longer blocks current stage progress.",
            }
        )
    persist_failure_register_rows(corrected_rows, database_url=database_url)
    return len(corrected_rows)


def fetch_failure_register_rows(
    *,
    database_url: str | None = None,
    stage_id: str | None = None,
    start_month: str | None = None,
    end_month: str | None = None,
    failure_status: str | None = None,
    skip_future_matching: bool | None = None,
) -> list[dict[str, Any]]:
    import psycopg
    from psycopg.rows import dict_row

    predicates = []
    params: list[Any] = []
    if stage_id:
        predicates.append("stage_id = %s")
        params.append(stage_id)
    if start_month:
        predicates.append("start_month = %s")
        params.append(start_month)
    if end_month:
        predicates.append("end_month = %s")
        params.append(end_month)
    if failure_status:
        predicates.append("failure_status = %s")
        params.append(failure_status)
    if skip_future_matching is not None:
        predicates.append("skip_future_matching = %s")
        params.append(skip_future_matching)
    where_sql = " WHERE " + " AND ".join(predicates) if predicates else ""
    sql = f"SELECT {', '.join(FAILURE_REGISTER_COLUMNS)} FROM trading_manager.failure_register{where_sql} ORDER BY stage_id, request_id"
    with psycopg.connect(_db_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]


def accepted_failure_request_ids_from_register(
    *,
    database_url: str | None = None,
    stage_id: str,
    start_month: str,
    end_month: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    rows = fetch_failure_register_rows(
        database_url=database_url,
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        failure_status="accepted_skip",
        skip_future_matching=True,
    )
    request_ids = tuple(str(row["request_id"]) for row in rows)
    refs = tuple(dict.fromkeys(str(row.get("agent_review_ref")) for row in rows if row.get("agent_review_ref")))
    return request_ids, refs


def register_failure_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or persist manager_failure_register rows.")
    parser.add_argument("path", type=Path, help="JSON, JSON array, or JSONL failure-register rows.")
    parser.add_argument("--write", action="store_true", help="Persist rows to trading_manager.failure_register.")
    parser.add_argument("--database-url")
    args = parser.parse_args(argv)
    rows = [validate_failure_register_row(row) for row in load_json_or_jsonl(args.path)]
    if args.write:
        persist_failure_register_rows(rows, database_url=args.database_url)
    else:
        write_jsonl(rows, sys.stdout)
    return 0


def list_failure_register_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List manager failure register rows.")
    parser.add_argument("--database-url")
    parser.add_argument("--stage-id")
    parser.add_argument("--start-month")
    parser.add_argument("--end-month")
    parser.add_argument("--failure-status")
    parser.add_argument("--skip-future-matching", action="store_true")
    args = parser.parse_args(argv)
    rows = fetch_failure_register_rows(
        database_url=args.database_url,
        stage_id=args.stage_id,
        start_month=args.start_month,
        end_month=args.end_month,
        failure_status=args.failure_status,
        skip_future_matching=True if args.skip_future_matching else None,
    )
    write_jsonl(rows, sys.stdout)
    return 0


__all__ = [
    "FAILURE_REGISTER_COLUMNS",
    "accepted_failure_request_ids_from_register",
    "fetch_failure_register_rows",
    "mark_failure_register_requests_corrected",
    "persist_failure_register_rows",
    "validate_failure_register_row",
]

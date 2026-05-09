"""Unified manager task-system helpers.

The task system has one durable shape across component repositories:

- `manager_request_v1` rows record what the manager asked a component to do.
- component completion receipts are normalized into `run_manifest_v1`,
  `artifact_ref_v1`, and `ready_signal_v1` rows.

Component-owned payloads stay behind artifact/parameter refs. This module keeps
row construction and validation importable; scripts own CLI behavior and optional
SQL persistence.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

REQUEST_COLUMNS = (
    "request_id",
    "contract_type",
    "request_kind",
    "status",
    "requested_by",
    "target_component_id",
    "target_component_kind",
    "target_repo_id",
    "expected_outputs",
    "policy_refs",
    "parameter_ref",
    "dry_run",
)

RUN_MANIFEST_COLUMNS = (
    "run_id",
    "contract_type",
    "request_id",
    "component_id",
    "component_kind",
    "repo_id",
    "status",
    "started_at_utc",
    "ended_at_utc",
    "parameter_ref",
    "error_summary",
)

ARTIFACT_REF_COLUMNS = (
    "artifact_id",
    "contract_type",
    "artifact_kind",
    "producer_run_id",
    "uri",
    "content_hash",
    "schema_ref",
    "row_count",
    "lifecycle_status",
    "media_type",
)

READY_SIGNAL_COLUMNS = (
    "ready_signal_id",
    "contract_type",
    "signal_kind",
    "producer_component_id",
    "producer_run_id",
    "artifact_refs",
    "status",
    "consumer_hint",
    "blocking_reason",
    "review_required",
)

TERMINAL_SUCCESS_STATUSES = {"succeeded", "success", "completed", "complete", "ready"}
TERMINAL_PARTIAL_STATUSES = {"partial", "partial_ready"}
TERMINAL_FAILURE_STATUSES = {"failed", "failure", "error", "cancelled", "blocked"}


class TaskSystemError(ValueError):
    """Raised when a manager task-system payload is invalid."""


def _required(mapping: Mapping[str, Any], key: str) -> Any:
    value = mapping.get(key)
    if value in (None, "", []):
        raise TaskSystemError(f"missing required field: {key}")
    return value


def _list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _ready_status(run_status: str) -> str:
    status = _status(run_status)
    if status in TERMINAL_SUCCESS_STATUSES:
        return "ready"
    if status in TERMINAL_PARTIAL_STATUSES:
        return "partial"
    if status in TERMINAL_FAILURE_STATUSES:
        return "failed" if status in {"failed", "failure", "error"} else status
    return "blocked"


def _error_summary(run: Mapping[str, Any]) -> str | None:
    error = run.get("error")
    if error in (None, "", {}):
        return None
    if isinstance(error, str):
        return error[:500]
    if isinstance(error, Mapping):
        parts = [str(error.get(key)) for key in ("type", "message", "error") if error.get(key)]
        return ": ".join(parts)[:500] if parts else json.dumps(error, sort_keys=True)[:500]
    return str(error)[:500]


def _output_refs(run: Mapping[str, Any]) -> list[Any]:
    for key in ("output_refs", "outputs", "artifacts"):
        value = run.get(key)
        if value not in (None, "", []):
            return _list(value)
    return []


def _output_uri(output: Any) -> str | None:
    if isinstance(output, str):
        return output
    if isinstance(output, Mapping):
        for key in ("uri", "ref", "path"):
            value = output.get(key)
            if value:
                return str(value)
    return None


def _output_artifact_row(run_id: str, index: int, output: Any, ready_status: str) -> dict[str, Any] | None:
    uri = _output_uri(output)
    if not uri:
        return None
    if isinstance(output, Mapping):
        artifact_kind = str(output.get("artifact_kind") or output.get("kind") or "component_output")
        content_hash = output.get("content_hash") or output.get("hash")
        schema_ref = str(output.get("schema_ref") or "component_output_ref_v1")
        row_count = output.get("row_count")
        media_type = output.get("media_type") or output.get("mime_type")
    else:
        artifact_kind = "component_output"
        content_hash = None
        schema_ref = "component_output_ref_v1"
        row_count = None
        media_type = None
    return {
        "artifact_id": f"art_output_{run_id}_{index:03d}",
        "contract_type": "artifact_ref_v1",
        "artifact_kind": artifact_kind,
        "producer_run_id": run_id,
        "uri": uri,
        "content_hash": content_hash,
        "schema_ref": schema_ref,
        "row_count": row_count,
        "lifecycle_status": "active" if ready_status in {"ready", "partial"} else "failed",
        "media_type": media_type,
    }


def _receipt_runs(receipt: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    runs = receipt.get("runs")
    if isinstance(runs, list) and runs:
        normalized = []
        for item in runs:
            if not isinstance(item, Mapping):
                raise TaskSystemError("receipt.runs entries must be objects")
            normalized.append(item)
        return normalized
    # Accept single-run receipts from component-local scripts.
    if receipt.get("run_id") or receipt.get("status"):
        return [receipt]
    raise TaskSystemError("completion receipt must contain runs[] or a top-level run_id/status")


def validate_manager_request(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize one manager_request_v1 row dictionary."""

    normalized = {column: row.get(column) for column in REQUEST_COLUMNS}
    normalized["request_id"] = str(_required(row, "request_id"))
    normalized["contract_type"] = str(row.get("contract_type") or "manager_request_v1")
    if normalized["contract_type"] != "manager_request_v1":
        raise TaskSystemError("request.contract_type must be manager_request_v1")
    normalized["request_kind"] = str(_required(row, "request_kind"))
    normalized["status"] = str(row.get("status") or "requested")
    normalized["requested_by"] = str(_required(row, "requested_by"))
    normalized["target_component_id"] = str(_required(row, "target_component_id"))
    normalized["target_component_kind"] = str(row.get("target_component_kind") or "component")
    normalized["target_repo_id"] = str(_required(row, "target_repo_id"))
    normalized["expected_outputs"] = _list(row.get("expected_outputs"))
    normalized["policy_refs"] = _list(row.get("policy_refs"))
    normalized["parameter_ref"] = row.get("parameter_ref")
    normalized["dry_run"] = bool(row.get("dry_run", True))
    return normalized


@dataclass(frozen=True)
class CompletionReceiptRows:
    """Normalized control-plane rows derived from a component receipt."""

    run_manifests: list[dict[str, Any]] = field(default_factory=list)
    artifact_refs: list[dict[str, Any]] = field(default_factory=list)
    ready_signals: list[dict[str, Any]] = field(default_factory=list)

    def jsonl_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        rows.extend({"table": "trading_manager.run_manifest", **row} for row in self.run_manifests)
        rows.extend({"table": "trading_manager.artifact_ref", **row} for row in self.artifact_refs)
        rows.extend({"table": "trading_manager.ready_signal", **row} for row in self.ready_signals)
        return rows


def normalize_completion_receipt(
    receipt: Mapping[str, Any],
    *,
    request_id: str,
    component_id: str,
    component_kind: str,
    repo_id: str,
    receipt_uri: str,
    receipt_hash: str | None = None,
    parameter_ref: str | None = None,
    ready_signal_kind: str = "component_task_ready",
    receipt_schema_ref: str = "component_completion_receipt_v1",
    consumer_hint: str | None = None,
) -> CompletionReceiptRows:
    """Normalize a component completion receipt into manager control-plane rows."""

    request_id = str(_required({"request_id": request_id}, "request_id"))
    component_id = str(_required({"component_id": component_id}, "component_id"))
    repo_id = str(_required({"repo_id": repo_id}, "repo_id"))
    receipt_uri = str(_required({"receipt_uri": receipt_uri}, "receipt_uri"))
    component_kind = str(component_kind or "component")

    manifests: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []

    for index, run in enumerate(_receipt_runs(receipt), start=1):
        run_id = str(run.get("run_id") or f"{request_id}_run_{index:03d}")
        status = _status(run.get("status") or "failed")
        started = run.get("started_at") or run.get("started_at_utc")
        completed = run.get("completed_at") or run.get("ended_at_utc")
        if not started:
            raise TaskSystemError(f"run {run_id} missing started_at")

        artifact_id = f"art_receipt_{run_id}"
        ready_signal_id = f"ready_{run_id}"
        ready_status = _ready_status(status)
        row_count = None
        row_counts = run.get("row_counts")
        if isinstance(row_counts, Mapping):
            numeric_values = [value for value in row_counts.values() if isinstance(value, int)]
            row_count = sum(numeric_values) if numeric_values else None

        manifests.append(
            {
                "run_id": run_id,
                "contract_type": "run_manifest_v1",
                "request_id": request_id,
                "component_id": component_id,
                "component_kind": component_kind,
                "repo_id": repo_id,
                "status": "succeeded" if status in TERMINAL_SUCCESS_STATUSES else ready_status,
                "started_at_utc": started,
                "ended_at_utc": completed,
                "parameter_ref": parameter_ref,
                "error_summary": _error_summary(run),
            }
        )
        artifacts.append(
            {
                "artifact_id": artifact_id,
                "contract_type": "artifact_ref_v1",
                "artifact_kind": "component_completion_receipt",
                "producer_run_id": run_id,
                "uri": receipt_uri,
                "content_hash": receipt_hash,
                "schema_ref": receipt_schema_ref,
                "row_count": row_count,
                "lifecycle_status": "active" if ready_status in {"ready", "partial"} else "failed",
                "media_type": "application/json",
            }
        )
        signal_artifact_refs = [artifact_id]
        for output_index, output in enumerate(_output_refs(run), start=1):
            output_row = _output_artifact_row(run_id, output_index, output, ready_status)
            if output_row is None:
                continue
            artifacts.append(output_row)
            signal_artifact_refs.append(output_row["artifact_id"])
        signals.append(
            {
                "ready_signal_id": ready_signal_id,
                "contract_type": "ready_signal_v1",
                "signal_kind": ready_signal_kind,
                "producer_component_id": component_id,
                "producer_run_id": run_id,
                "artifact_refs": signal_artifact_refs,
                "status": ready_status,
                "consumer_hint": consumer_hint,
                "blocking_reason": _error_summary(run) if ready_status not in {"ready", "partial"} else None,
                "review_required": ready_status == "partial",
            }
        )
    return CompletionReceiptRows(manifests, artifacts, signals)


def _json_default(value: Any) -> Any:
    return value


def write_jsonl(rows: Iterable[Mapping[str, Any]], output: TextIO) -> None:
    for row in rows:
        output.write(json.dumps(dict(row), sort_keys=True, default=_json_default) + "\n")


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    stripped = text.lstrip()
    if stripped.startswith("["):
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise TaskSystemError("JSON array expected")
        return [dict(item) for item in payload]
    if stripped.startswith("{") and "\n" not in stripped.strip():
        payload = json.loads(text)
        if not isinstance(payload, Mapping):
            raise TaskSystemError("JSON object expected")
        return [dict(payload)]
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise TaskSystemError("JSONL rows must be objects")
        rows.append(dict(payload))
    return rows


def _db_url(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("DATABASE_URL")
    if env:
        return env
    secret_path = Path("/root/secrets/openclaw/database-url")
    if secret_path.exists():
        return secret_path.read_text(encoding="utf-8").strip()
    raise TaskSystemError("database URL required: pass --database-url or set DATABASE_URL")


def _execute_many(database_url: str, table: str, columns: Sequence[str], rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    import psycopg
    from psycopg.types.json import Jsonb

    jsonb_columns = {"expected_outputs", "policy_refs"}
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)
    update_sql = ", ".join(f"{column}=EXCLUDED.{column}" for column in columns[1:])
    pk = columns[0]
    sql = f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders}) ON CONFLICT ({pk}) DO UPDATE SET {update_sql}"
    values = [
        tuple(Jsonb(row.get(column) or []) if column in jsonb_columns else row.get(column) for column in columns)
        for row in rows
    ]
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(sql, values)
        connection.commit()


def persist_manager_requests(rows: Sequence[Mapping[str, Any]], *, database_url: str | None = None) -> None:
    normalized = [validate_manager_request(row) for row in rows]
    _execute_many(_db_url(database_url), "trading_manager.manager_request", REQUEST_COLUMNS, normalized)


def persist_completion_rows(rows: CompletionReceiptRows, *, database_url: str | None = None) -> None:
    url = _db_url(database_url)
    _execute_many(url, "trading_manager.run_manifest", RUN_MANIFEST_COLUMNS, rows.run_manifests)
    _execute_many(url, "trading_manager.artifact_ref", ARTIFACT_REF_COLUMNS, rows.artifact_refs)
    _execute_many(url, "trading_manager.ready_signal", READY_SIGNAL_COLUMNS, rows.ready_signals)


def submit_requests_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or persist manager_request_v1 rows.")
    parser.add_argument("path", type=Path, help="JSON, JSON array, or JSONL request rows.")
    parser.add_argument("--write", action="store_true", help="Persist rows to trading_manager.manager_request.")
    parser.add_argument("--database-url")
    args = parser.parse_args(argv)
    rows = [validate_manager_request(row) for row in load_json_or_jsonl(args.path)]
    if args.write:
        persist_manager_requests(rows, database_url=args.database_url)
    else:
        write_jsonl(rows, sys.stdout)
    return 0


def record_receipt_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize or persist a component completion receipt.")
    parser.add_argument("receipt", type=Path, help="Component completion receipt JSON.")
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--component-id", required=True)
    parser.add_argument("--component-kind", default="component")
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--receipt-uri", required=True)
    parser.add_argument("--receipt-hash")
    parser.add_argument("--parameter-ref")
    parser.add_argument("--ready-signal-kind", default="component_task_ready")
    parser.add_argument("--consumer-hint")
    parser.add_argument("--write", action="store_true", help="Persist derived rows to manager control-plane tables.")
    parser.add_argument("--database-url")
    args = parser.parse_args(argv)
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if not isinstance(receipt, Mapping):
        raise TaskSystemError("completion receipt must be a JSON object")
    rows = normalize_completion_receipt(
        receipt,
        request_id=args.request_id,
        component_id=args.component_id,
        component_kind=args.component_kind,
        repo_id=args.repo_id,
        receipt_uri=args.receipt_uri,
        receipt_hash=args.receipt_hash,
        parameter_ref=args.parameter_ref,
        ready_signal_kind=args.ready_signal_kind,
        consumer_hint=args.consumer_hint,
    )
    if args.write:
        persist_completion_rows(rows, database_url=args.database_url)
    else:
        write_jsonl(rows.jsonl_rows(), sys.stdout)
    return 0

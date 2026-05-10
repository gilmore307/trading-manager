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
    "priority",
    "deadline_at_utc",
    "parameter_ref",
    "dry_run",
)

INPUT_BINDING_COLUMNS = (
    "binding_id",
    "contract_type",
    "request_id",
    "run_id",
    "input_role",
    "input_ref",
    "available_at_utc",
    "as_of_utc",
    "version_ref",
    "entity_scope",
    "time_window",
    "schema_ref",
    "quality_ref",
    "lineage_ref",
)

TASK_PRIORITY_RANKS = {
    "critical": 10,
    "high": 20,
    "normal": 30,
    "low": 40,
    "backlog": 50,
}

TASK_SUMMARY_ORDER_BY = "priority_rank ASC, deadline_at_utc ASC NULLS LAST, created_at_utc ASC, request_id ASC"

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


def _canonical_storage_uri(value: str, *, repo_id: str) -> str:
    text = value.strip()
    if text.startswith("storage://"):
        return text
    if text.startswith("storage/"):
        return f"storage://{repo_id}/{text.removeprefix('storage/')}"
    return text


def _output_uri(output: Any, *, repo_id: str) -> str | None:
    if isinstance(output, str):
        return _canonical_storage_uri(output, repo_id=repo_id)
    if isinstance(output, Mapping):
        for key in ("uri", "ref", "path"):
            value = output.get(key)
            if value:
                return _canonical_storage_uri(str(value), repo_id=repo_id)
    return None


def _media_type_from_uri(uri: str) -> str | None:
    suffix = Path(uri).suffix.lower()
    return {
        ".csv": "text/csv",
        ".json": "application/json",
        ".jsonl": "application/jsonl",
        ".parquet": "application/vnd.apache.parquet",
    }.get(suffix)


def _matching_row_count(row_counts: Any, uri: str) -> Any:
    if not isinstance(row_counts, Mapping) or not row_counts:
        return None
    name = Path(uri).stem
    if name in row_counts:
        return row_counts[name]
    numeric_values = [value for value in row_counts.values() if isinstance(value, int)]
    return numeric_values[0] if len(numeric_values) == 1 else None


def _row_count_for_output(run: Mapping[str, Any], output: Any, uri: str) -> Any:
    if isinstance(output, Mapping) and output.get("row_count") is not None:
        return output.get("row_count")
    return _matching_row_count(run.get("row_counts"), uri)


def _artifact_kind_for_output(output: Any, uri: str) -> str:
    if isinstance(output, Mapping):
        return str(output.get("artifact_kind") or output.get("kind") or Path(uri).stem or "component_output")
    return Path(uri).stem or "component_output"


def _artifact_id_token(value: str) -> str:
    token = "".join(char.lower() if char.isalnum() else "_" for char in value)
    token = "_".join(part for part in token.split("_") if part)
    return token[:80] or "artifact"


def _step_reference_artifact_kind(step_name: str, uri: str) -> str:
    stem = Path(uri).stem
    if stem == "schema":
        return f"{_artifact_id_token(step_name)}_schema"
    if stem == "request_manifest":
        return "request_manifest"
    if step_name:
        return f"{_artifact_id_token(step_name)}_{_artifact_id_token(stem)}"
    return _artifact_id_token(stem)


def _step_reference_artifact_rows(
    run_id: str,
    *,
    run: Mapping[str, Any],
    ready_status: str,
    repo_id: str,
    known_uris: set[str],
    start_index: int = 1,
) -> list[dict[str, Any]]:
    steps = run.get("steps")
    if not isinstance(steps, Mapping):
        return []
    rows: list[dict[str, Any]] = []
    index = start_index
    for step_name, step_payload in sorted(steps.items(), key=lambda item: str(item[0])):
        if not isinstance(step_payload, Mapping):
            continue
        row_counts = step_payload.get("row_counts")
        for reference in _list(step_payload.get("references")):
            uri = _output_uri(reference, repo_id=repo_id)
            if not uri or uri in known_uris:
                continue
            known_uris.add(uri)
            artifact_kind = _step_reference_artifact_kind(str(step_name), uri)
            rows.append(
                {
                    "artifact_id": f"art_step_{run_id}_{index:03d}",
                    "contract_type": "artifact_ref_v1",
                    "artifact_kind": artifact_kind,
                    "producer_run_id": run_id,
                    "uri": uri,
                    "content_hash": None,
                    "schema_ref": "component_step_reference_v1",
                    "row_count": _matching_row_count(row_counts, uri),
                    "lifecycle_status": "active" if ready_status in {"ready", "partial"} else "failed",
                    "media_type": _media_type_from_uri(uri),
                }
            )
            index += 1
    return rows


def _output_artifact_row(run_id: str, index: int, output: Any, ready_status: str, *, run: Mapping[str, Any], repo_id: str) -> dict[str, Any] | None:
    uri = _output_uri(output, repo_id=repo_id)
    if not uri:
        return None
    if isinstance(output, Mapping):
        artifact_kind = _artifact_kind_for_output(output, uri)
        content_hash = output.get("content_hash") or output.get("hash")
        schema_ref = str(output.get("schema_ref") or "component_output_ref_v1")
        row_count = _row_count_for_output(run, output, uri)
        media_type = output.get("media_type") or output.get("mime_type") or _media_type_from_uri(uri)
    else:
        artifact_kind = _artifact_kind_for_output(output, uri)
        content_hash = None
        schema_ref = "component_output_ref_v1"
        row_count = _row_count_for_output(run, output, uri)
        media_type = _media_type_from_uri(uri)
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
    priority = str(row.get("priority") or "normal").strip().lower()
    if priority not in TASK_PRIORITY_RANKS:
        raise TaskSystemError(f"priority must be one of: {', '.join(TASK_PRIORITY_RANKS)}")
    normalized["priority"] = priority
    normalized["deadline_at_utc"] = row.get("deadline_at_utc")
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
        known_uris = {receipt_uri}
        for output_index, output in enumerate(_output_refs(run), start=1):
            output_row = _output_artifact_row(run_id, output_index, output, ready_status, run=run, repo_id=repo_id)
            if output_row is None:
                continue
            known_uris.add(str(output_row["uri"]))
            artifacts.append(output_row)
            signal_artifact_refs.append(output_row["artifact_id"])
        step_rows = _step_reference_artifact_rows(
            run_id,
            run=run,
            ready_status=ready_status,
            repo_id=repo_id,
            known_uris=known_uris,
        )
        artifacts.extend(step_rows)
        signal_artifact_refs.extend(row["artifact_id"] for row in step_rows)
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
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


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


def persist_input_bindings(rows: Sequence[Mapping[str, Any]], *, database_url: str | None = None) -> None:
    _execute_many(_db_url(database_url), "trading_manager.input_binding", INPUT_BINDING_COLUMNS, rows)


def fetch_manager_requests(
    *,
    database_url: str | None = None,
    request_kind: str | None = None,
    status: str | None = None,
    request_ids: Sequence[str] | None = None,
    limit: int | None = None,
    include_rehearsals: bool = False,
) -> list[dict[str, Any]]:
    """Fetch manager_request rows for downstream helper scripts."""

    import psycopg
    from psycopg.rows import dict_row

    predicates = []
    params: list[Any] = []
    if request_kind:
        predicates.append("request_kind = %s")
        params.append(request_kind)
    if status:
        predicates.append("status = %s")
        params.append(status)
    if request_ids:
        predicates.append("request_id = ANY(%s)")
        params.append(list(request_ids))
    if not include_rehearsals:
        predicates.append("request_id NOT LIKE 'mgrreq_rehearsal_%%'")
    where_sql = " WHERE " + " AND ".join(predicates) if predicates else ""
    limit_sql = ""
    if limit is not None:
        if limit < 1:
            raise TaskSystemError("limit must be >= 1")
        limit_sql = " LIMIT %s"
        params.append(limit)
    sql = f"SELECT {', '.join(REQUEST_COLUMNS)} FROM trading_manager.manager_request{where_sql} ORDER BY created_at_utc ASC, request_id ASC{limit_sql}"
    with psycopg.connect(_db_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]


def fetch_input_bindings(
    *,
    database_url: str | None = None,
    request_ids: Sequence[str] | None = None,
    input_role: str | None = None,
    schema_ref: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch input_binding rows for request handoff validation."""

    import psycopg
    from psycopg.rows import dict_row

    predicates = []
    params: list[Any] = []
    if request_ids:
        predicates.append("request_id = ANY(%s)")
        params.append(list(request_ids))
    if input_role:
        predicates.append("input_role = %s")
        params.append(input_role)
    if schema_ref:
        predicates.append("schema_ref = %s")
        params.append(schema_ref)
    where_sql = " WHERE " + " AND ".join(predicates) if predicates else ""
    sql = f"SELECT {', '.join(INPUT_BINDING_COLUMNS)} FROM trading_manager.input_binding{where_sql} ORDER BY request_id ASC, binding_id ASC"
    with psycopg.connect(_db_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]


def persist_completion_rows(rows: CompletionReceiptRows, *, database_url: str | None = None) -> None:
    url = _db_url(database_url)
    _execute_many(url, "trading_manager.run_manifest", RUN_MANIFEST_COLUMNS, rows.run_manifests)
    _execute_many(url, "trading_manager.artifact_ref", ARTIFACT_REF_COLUMNS, rows.artifact_refs)
    _execute_many(url, "trading_manager.ready_signal", READY_SIGNAL_COLUMNS, rows.ready_signals)


def fetch_task_summary(
    *,
    database_url: str | None = None,
    status: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Fetch global manager task summary rows sorted by accepted priority order."""

    import psycopg
    from psycopg.rows import dict_row

    predicates = []
    params: list[Any] = []
    if status:
        predicates.append("task_status = %s")
        params.append(status)
    where_sql = " WHERE " + " AND ".join(predicates) if predicates else ""
    limit_sql = ""
    if limit is not None:
        if limit < 1:
            raise TaskSystemError("limit must be >= 1")
        limit_sql = " LIMIT %s"
        params.append(limit)
    sql = f"SELECT * FROM trading_manager.task_summary{where_sql} ORDER BY {TASK_SUMMARY_ORDER_BY}{limit_sql}"
    with psycopg.connect(_db_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]


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


def list_task_summary_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List global manager task summary rows by priority.")
    parser.add_argument("--database-url")
    parser.add_argument("--status", help="Optional task_status filter.")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    rows = fetch_task_summary(database_url=args.database_url, status=args.status, limit=args.limit)
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

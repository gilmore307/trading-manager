"""Unified server-error agent handoff helpers.

This module is intentionally component-neutral. Any server-side workflow can call
it after an error to create one standard agent diagnosis/repair request. The
request is evidence-first, repair-capable, and constrained by the server error
repair skill; optional agent invocation is behind an explicit runner command
supplied by reviewed runtime configuration.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

from .control_plane import TaskSystemError, _db_url
from .storage_paths import manager_storage_root

SERVER_ERROR_AGENT_REQUEST_CONTRACT = "server_error_agent_request"
AGENT_ERROR_DIAGNOSIS_CONTRACT = "agent_error_diagnosis"
AGENT_ERROR_HANDLING_RESULT_CONTRACT = "agent_error_handling_result"
SERVER_ERROR_CATALOG_ENTRY_CONTRACT = "server_error_catalog_entry"
SERVER_ERROR_CATALOG_OCCURRENCE_CONTRACT = "server_error_catalog_occurrence"
DEFAULT_AGENT_REF = "codex_cli_gpt_5_5"
DEFAULT_OUTPUT_ROOT = manager_storage_root() / "runtime" / "agent_error_handling"
DEFAULT_ERROR_CATALOG_NAME = "server_error_catalog.jsonl"
DEFAULT_ERROR_CATALOG_LOCK_NAME = ".server_error_catalog.lock"
SERVER_ERROR_CATALOG_TABLE = "trading_manager.server_error_catalog"
DEFAULT_DEDUP_WINDOW_SECONDS = 60 * 60
DEFAULT_DISCORD_TARGET = "channel:1504100135200620665"
DEFAULT_DISCORD_SERVER_ID = "1480186849241731084"
ALLOWED_SEVERITIES = {"info", "warning", "error", "critical"}
CATALOG_STORAGES = {"sql", "jsonl"}
SERVER_ERROR_CATALOG_COLUMNS = (
    "catalog_row_id",
    "contract_type",
    "schema_version",
    "error_number",
    "error_ref",
    "error_fingerprint",
    "request_id",
    "duplicate_of_request_id",
    "request_path",
    "diagnosis_path",
    "source_component",
    "source_repo",
    "error_scope",
    "error_kind",
    "severity",
    "summary",
    "exit_code",
    "occurred_at_utc",
    "first_seen_at_utc",
    "last_seen_at_utc",
    "created_at_utc",
    "deduplicated",
    "dedup_window_seconds",
    "catalog_payload_json",
)
SAFE_ALLOWED_ACTIONS = (
    "inspect referenced logs, receipts, status artifacts, source files, docs, and tests",
    "diagnose root cause and classify whether the failure is code, config, data, environment, provider, or operator-boundary related",
    "edit internal source, tests, scripts, config templates, or docs when the repair is narrow, evidence-backed, and within repository boundaries",
    "run verification commands such as tests, compile checks, lint/diff checks, dry-runs, and status inspection",
    "rerun failed internal stages, regenerate missing internal artifacts, or write runtime/model outputs only when required to verify or complete the repair",
    "restart internal services or perform storage maintenance only when required by the repair skill and when broker/account/order/fill/position state is untouched",
    "commit and push repository edits after verification so the repaired workspace is durable",
    "recommend retry or closure only after the suspected cause is fixed, superseded, no longer applicable, or classified as transient",
)
FORBIDDEN_ACTIONS = (
    "do not mutate broker, account, order, fill, position, buying-power, or funds state",
    "do not exfiltrate secrets or print secret values; use aliases and redacted evidence only",
    "do not broaden the repair beyond the supplied error evidence and accepted current project contracts",
    "do not perform destructive deletion, system package changes, or unrelated repository rewrites without an explicit higher-level approval path",
    "do not mark failures accepted, corrected, or skipped without durable diagnosis evidence and the appropriate review reference",
)


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _env_truthy(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise TaskSystemError(f"{name} must be an integer") from exc
    if parsed < 0:
        raise TaskSystemError(f"{name} must be non-negative")
    return parsed


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _as_list(values: Iterable[str] | None) -> list[str]:
    return [str(value) for value in values or [] if str(value)]


def _bounded_file_excerpt(path: str | None, *, max_chars: int = 4000) -> str | None:
    if not path:
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def build_agent_prompt(request: Mapping[str, Any]) -> str:
    """Build the standard prompt given to the diagnostic agent."""

    return "\n".join(
        [
            "You are the server-wide error diagnosis and repair agent for the trading system.",
            "Use the fixed workspace skill server-error-repair.",
            "Diagnose the failure from the supplied evidence, repair it when possible, verify the repair, and leave the workspace in a durable state.",
            "Return the strict JSON repair receipt required by server-error-repair, including diagnosis_status, root_cause, repair_attempted, files_changed, verification, retry_recommendation, and blockers.",
            "",
            "Allowed actions:",
            *[f"- {item}" for item in request.get("allowed_actions", [])],
            "",
            "Forbidden actions:",
            *[f"- {item}" for item in request.get("forbidden_actions", [])],
            "",
            f"Error number: {request.get('error_ref') or 'unassigned'}",
            "Error request:",
            json.dumps({key: value for key, value in request.items() if key != "agent_prompt"}, indent=2, sort_keys=True),
        ]
    )


def build_server_error_agent_request(
    *,
    source_component: str,
    summary: str,
    source_repo: str | None = None,
    error_scope: str = "server",
    error_kind: str = "unclassified_error",
    severity: str = "error",
    command: Iterable[str] | None = None,
    exit_code: int | None = None,
    stdout_path: str | None = None,
    stderr_path: str | None = None,
    working_directory: str | None = None,
    evidence_refs: Iterable[str] | None = None,
    occurred_at_utc: str | None = None,
    agent_ref: str = DEFAULT_AGENT_REF,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a component-neutral request for agent diagnosis/repair."""

    if not source_component:
        raise TaskSystemError("source_component is required")
    if not summary:
        raise TaskSystemError("summary is required")
    normalized_severity = severity.strip().lower()
    if normalized_severity not in ALLOWED_SEVERITIES:
        raise TaskSystemError(f"severity must be one of: {', '.join(sorted(ALLOWED_SEVERITIES))}")
    normalized_command = [str(part) for part in command or []]
    normalized_evidence = _as_list(evidence_refs)
    if stdout_path:
        normalized_evidence.append(f"stdout:{stdout_path}")
    if stderr_path:
        normalized_evidence.append(f"stderr:{stderr_path}")
    occurred = occurred_at_utc or _now_utc()
    error_fingerprint = _stable_id(
        "errfp",
        source_component,
        source_repo,
        error_scope,
        error_kind,
        summary,
        normalized_command,
        exit_code,
    )
    stable_request_id = request_id or _stable_id(
        "erragent",
        error_fingerprint,
        stdout_path,
        stderr_path,
        occurred,
    )
    request: dict[str, Any] = {
        "contract_type": SERVER_ERROR_AGENT_REQUEST_CONTRACT,
        "schema_version": "1",
        "request_id": stable_request_id,
        "error_fingerprint": error_fingerprint,
        "source_component": source_component,
        "source_repo": source_repo,
        "error_scope": error_scope,
        "error_kind": error_kind,
        "severity": normalized_severity,
        "summary": summary,
        "command": normalized_command,
        "exit_code": exit_code,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "stdout_excerpt": _bounded_file_excerpt(stdout_path),
        "stderr_excerpt": _bounded_file_excerpt(stderr_path),
        "working_directory": working_directory,
        "evidence_refs": normalized_evidence,
        "agent_ref": agent_ref,
        "allowed_actions": list(SAFE_ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "occurred_at_utc": occurred,
        "created_at_utc": _now_utc(),
    }
    request["agent_prompt"] = build_agent_prompt(request)
    validate_server_error_agent_request(request)
    return request


def _catalog_path(output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / DEFAULT_ERROR_CATALOG_NAME


def _catalog_lock_path(output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / DEFAULT_ERROR_CATALOG_LOCK_NAME


def _read_catalog_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _catalog_row_id(row: Mapping[str, Any]) -> str:
    return str(row.get("catalog_row_id") or _stable_id("errcat", row.get("contract_type"), row.get("request_id")))


def _json_safe_catalog_row(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    for key, value in list(normalized.items()):
        if isinstance(value, datetime):
            normalized[key] = value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return normalized


def _catalog_sql_rows(database_url: str | None = None, *, error_ref: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    import psycopg
    from psycopg.rows import dict_row

    predicates = []
    params: list[Any] = []
    if error_ref:
        predicates.append("error_ref = %s")
        params.append(error_ref.strip().upper())
    where_sql = " WHERE " + " AND ".join(predicates) if predicates else ""
    limit_sql = " LIMIT %s" if limit is not None else ""
    if limit is not None:
        params.append(max(int(limit), 0))
    order_sql = (
        "ORDER BY error_number DESC, created_at_utc DESC, request_id DESC"
        if limit is not None and not error_ref
        else "ORDER BY error_number ASC, created_at_utc ASC, request_id ASC"
    )
    sql = (
        f"SELECT {', '.join(SERVER_ERROR_CATALOG_COLUMNS)} "
        f"FROM {SERVER_ERROR_CATALOG_TABLE}{where_sql} "
        f"{order_sql}"
        f"{limit_sql}"
    )
    with psycopg.connect(_db_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = [_json_safe_catalog_row(row) for row in cursor.fetchall()]
            return list(reversed(rows)) if limit is not None and not error_ref else rows


def fetch_server_error_catalog_rows(
    *,
    database_url: str | None = None,
    error_ref: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    return _catalog_sql_rows(database_url, error_ref=error_ref, limit=limit)


def persist_server_error_catalog_rows(rows: Iterable[Mapping[str, Any]], *, database_url: str | None = None) -> None:
    normalized = [validate_server_error_catalog_entry(row) for row in rows]
    if not normalized:
        return
    import psycopg
    from psycopg.types.json import Jsonb

    columns = SERVER_ERROR_CATALOG_COLUMNS
    placeholders = ", ".join(["%s"] * len(columns))
    col_sql = ", ".join(columns)
    update_sql = ", ".join(f"{column}=EXCLUDED.{column}" for column in columns[1:]) + ", updated_at_utc=NOW()"
    sql = f"INSERT INTO {SERVER_ERROR_CATALOG_TABLE} ({col_sql}) VALUES ({placeholders}) ON CONFLICT (catalog_row_id) DO UPDATE SET {update_sql}"
    values = [
        tuple(Jsonb(row.get(column) or {}) if column == "catalog_payload_json" else row.get(column) for column in columns)
        for row in normalized
    ]
    with psycopg.connect(_db_url(database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(sql, values)
        connection.commit()


def _parse_utc(value: object) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def _within_dedup_window(row: Mapping[str, Any], occurred_at_utc: str, *, dedup_window_seconds: int) -> bool:
    current = _parse_utc(occurred_at_utc) or datetime.now(UTC)
    seen = _parse_utc(row.get("last_seen_at_utc") or row.get("occurred_at_utc") or row.get("created_at_utc"))
    if seen is None:
        return False
    return abs(current - seen) <= timedelta(seconds=dedup_window_seconds)


def _format_alert_time(value: object) -> str:
    parsed = _parse_utc(value)
    if parsed is None:
        return str(value or "unknown")
    eastern = parsed.astimezone(ZoneInfo("America/New_York"))
    return f"{parsed.strftime('%Y-%m-%d %H:%M:%S UTC')} / {eastern.strftime('%Y-%m-%d %H:%M:%S %Z')}"


def register_error_in_catalog(
    request: Mapping[str, Any],
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    dedup_window_seconds: int | None = None,
    database_url: str | None = None,
    catalog_storage: str = "sql",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Assign a durable human-facing error number and append the catalog row.

    New error fingerprints receive refs such as ERR-000123. Repeated errors
    within the dedup window reuse the original ref and append an occurrence row
    instead of allocating a new owner-facing number or sending another alert.
    """

    if catalog_storage not in CATALOG_STORAGES:
        raise TaskSystemError(f"catalog_storage must be one of: {', '.join(sorted(CATALOG_STORAGES))}")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    catalog_path = _catalog_path(root)
    lock_path = _catalog_lock_path(root)
    window = _env_int("MANAGER_AGENT_ERROR_DEDUP_SECONDS", dedup_window_seconds or DEFAULT_DEDUP_WINDOW_SECONDS)
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            rows = fetch_server_error_catalog_rows(database_url=database_url) if catalog_storage == "sql" else _read_catalog_rows(catalog_path)
            request_id = str(request["request_id"])
            fingerprint = str(request.get("error_fingerprint") or request_id)
            existing = next((row for row in rows if str(row.get("request_id")) == request_id), None)
            if existing is not None:
                numbered_request = dict(request)
                numbered_request["error_number"] = existing["error_number"]
                numbered_request["error_ref"] = existing["error_ref"]
                numbered_request["error_catalog_path"] = SERVER_ERROR_CATALOG_TABLE if catalog_storage == "sql" else str(catalog_path)
                numbered_request["error_deduplicated"] = bool(existing.get("deduplicated"))
                numbered_request["agent_prompt"] = build_agent_prompt(numbered_request)
                validate_server_error_agent_request(numbered_request)
                return numbered_request, existing

            duplicate_base = next(
                (
                    row
                    for row in reversed(rows)
                    if row.get("contract_type") in {SERVER_ERROR_CATALOG_ENTRY_CONTRACT, SERVER_ERROR_CATALOG_OCCURRENCE_CONTRACT}
                    and str(row.get("error_fingerprint")) == fingerprint
                    and _within_dedup_window(row, str(request.get("occurred_at_utc")), dedup_window_seconds=window)
                ),
                None,
            )
            if duplicate_base is not None:
                numbered_request = dict(request)
                numbered_request["error_number"] = int(duplicate_base["error_number"])
                numbered_request["error_ref"] = duplicate_base["error_ref"]
                numbered_request["error_catalog_path"] = SERVER_ERROR_CATALOG_TABLE if catalog_storage == "sql" else str(catalog_path)
                numbered_request["error_deduplicated"] = True
                numbered_request["duplicate_of_request_id"] = duplicate_base.get("request_id") or duplicate_base.get("duplicate_of_request_id")
                numbered_request["agent_prompt"] = build_agent_prompt(numbered_request)
                row = {
                    "contract_type": SERVER_ERROR_CATALOG_OCCURRENCE_CONTRACT,
                    "schema_version": "1",
                    "error_number": numbered_request["error_number"],
                    "error_ref": numbered_request["error_ref"],
                    "error_fingerprint": fingerprint,
                    "request_id": request_id,
                    "duplicate_of_request_id": numbered_request.get("duplicate_of_request_id"),
                    "request_path": str(default_request_path(numbered_request, root)),
                    "diagnosis_path": str(default_diagnosis_path(numbered_request, root)),
                    "source_component": numbered_request.get("source_component"),
                    "source_repo": numbered_request.get("source_repo"),
                    "error_scope": numbered_request.get("error_scope"),
                    "error_kind": numbered_request.get("error_kind"),
                    "severity": numbered_request.get("severity"),
                    "summary": numbered_request.get("summary"),
                    "exit_code": numbered_request.get("exit_code"),
                    "occurred_at_utc": numbered_request.get("occurred_at_utc"),
                    "created_at_utc": _now_utc(),
                    "deduplicated": True,
                    "dedup_window_seconds": window,
                    "catalog_payload_json": {},
                }
                row = validate_server_error_catalog_entry(row)
                validate_server_error_agent_request(numbered_request)
                if catalog_storage == "sql":
                    persist_server_error_catalog_rows([row], database_url=database_url)
                else:
                    with catalog_path.open("a", encoding="utf-8") as catalog_file:
                        catalog_file.write(json.dumps(row, sort_keys=True) + "\n")
                return numbered_request, row

            next_number = max([int(row.get("error_number") or 0) for row in rows] or [0]) + 1
            error_ref = f"ERR-{next_number:06d}"
            numbered_request = dict(request)
            numbered_request["error_number"] = next_number
            numbered_request["error_ref"] = error_ref
            numbered_request["error_catalog_path"] = SERVER_ERROR_CATALOG_TABLE if catalog_storage == "sql" else str(catalog_path)
            numbered_request["error_deduplicated"] = False
            numbered_request["agent_prompt"] = build_agent_prompt(numbered_request)
            row = {
                "contract_type": SERVER_ERROR_CATALOG_ENTRY_CONTRACT,
                "schema_version": "1",
                "error_number": next_number,
                "error_ref": error_ref,
                "error_fingerprint": fingerprint,
                "request_id": request_id,
                "request_path": str(default_request_path(numbered_request, root)),
                "diagnosis_path": str(default_diagnosis_path(numbered_request, root)),
                "source_component": numbered_request.get("source_component"),
                "source_repo": numbered_request.get("source_repo"),
                "error_scope": numbered_request.get("error_scope"),
                "error_kind": numbered_request.get("error_kind"),
                "severity": numbered_request.get("severity"),
                "summary": numbered_request.get("summary"),
                "exit_code": numbered_request.get("exit_code"),
                "occurred_at_utc": numbered_request.get("occurred_at_utc"),
                "first_seen_at_utc": numbered_request.get("occurred_at_utc"),
                "last_seen_at_utc": numbered_request.get("occurred_at_utc"),
                "created_at_utc": _now_utc(),
                "deduplicated": False,
                "dedup_window_seconds": window,
                "catalog_payload_json": {},
            }
            row = validate_server_error_catalog_entry(row)
            validate_server_error_agent_request(numbered_request)
            if catalog_storage == "sql":
                persist_server_error_catalog_rows([row], database_url=database_url)
            else:
                with catalog_path.open("a", encoding="utf-8") as catalog_file:
                    catalog_file.write(json.dumps(row, sort_keys=True) + "\n")
            return numbered_request, row
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def validate_server_error_catalog_entry(row: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["catalog_row_id"] = _catalog_row_id(normalized)
    normalized.setdefault("catalog_payload_json", {})
    required = (
        "contract_type",
        "schema_version",
        "error_number",
        "error_ref",
        "request_id",
        "error_fingerprint",
        "request_path",
        "diagnosis_path",
        "source_component",
        "error_scope",
        "error_kind",
        "severity",
        "summary",
        "occurred_at_utc",
        "created_at_utc",
    )
    for field in required:
        if normalized.get(field) in (None, ""):
            raise TaskSystemError(f"missing required server error catalog field: {field}")
    if normalized["contract_type"] not in {SERVER_ERROR_CATALOG_ENTRY_CONTRACT, SERVER_ERROR_CATALOG_OCCURRENCE_CONTRACT}:
        raise TaskSystemError(f"contract_type must be {SERVER_ERROR_CATALOG_ENTRY_CONTRACT} or {SERVER_ERROR_CATALOG_OCCURRENCE_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if not isinstance(normalized["error_number"], int) or normalized["error_number"] < 1:
        raise TaskSystemError("error_number must be a positive integer")
    expected_ref = f"ERR-{normalized['error_number']:06d}"
    if normalized["error_ref"] != expected_ref:
        raise TaskSystemError(f"error_ref must be {expected_ref}")
    if normalized["severity"] not in ALLOWED_SEVERITIES:
        raise TaskSystemError(f"unsupported severity: {normalized['severity']}")
    return normalized


def validate_server_error_agent_request(request: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(request)
    required = (
        "contract_type",
        "schema_version",
        "request_id",
        "error_fingerprint",
        "source_component",
        "error_scope",
        "error_kind",
        "severity",
        "summary",
        "agent_ref",
        "allowed_actions",
        "forbidden_actions",
        "occurred_at_utc",
        "created_at_utc",
        "agent_prompt",
    )
    for field in required:
        value = normalized.get(field)
        if value in (None, "", []):
            raise TaskSystemError(f"missing required server error agent request field: {field}")
    if normalized["contract_type"] != SERVER_ERROR_AGENT_REQUEST_CONTRACT:
        raise TaskSystemError(f"contract_type must be {SERVER_ERROR_AGENT_REQUEST_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if normalized["severity"] not in ALLOWED_SEVERITIES:
        raise TaskSystemError(f"unsupported severity: {normalized['severity']}")
    for field in ("command", "evidence_refs", "allowed_actions", "forbidden_actions"):
        if not isinstance(normalized.get(field, []), list):
            raise TaskSystemError(f"{field} must be a list")
        normalized[field] = normalized.get(field, [])
    return normalized


def write_json_artifact(payload: Mapping[str, Any], *, path: Path | None = None, output: TextIO | None = None) -> None:
    content = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if output is not None:
        output.write(content)


def default_request_path(request: Mapping[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / str(request["request_id"]) / "server_error_agent_request.json"


def default_diagnosis_path(request: Mapping[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / str(request["request_id"]) / "agent_error_diagnosis.json"


def call_agent_runner(
    request: Mapping[str, Any],
    *,
    runner_command: str,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    """Call the configured agent runner with the request JSON on stdin."""

    argv = shlex.split(runner_command)
    if not argv:
        raise TaskSystemError("agent runner command is empty")
    started = _now_utc()
    try:
        result = subprocess.run(
            argv,
            input=json.dumps(dict(request), sort_keys=True),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        if result.returncode == 0:
            try:
                parsed_stdout = json.loads(stdout)
            except json.JSONDecodeError:
                parsed_stdout = None
            if isinstance(parsed_stdout, dict) and parsed_stdout.get("contract_type") == AGENT_ERROR_DIAGNOSIS_CONTRACT:
                return validate_agent_error_diagnosis(parsed_stdout)
        status = "completed" if result.returncode == 0 else "agent_call_failed"
    except subprocess.TimeoutExpired as exc:
        return_code = None
        stdout = str(exc.stdout or "")
        stderr = f"agent runner timed out after {timeout_seconds} seconds\n{exc.stderr or ''}"
        status = "agent_call_failed"
    completed = _now_utc()
    diagnosis = {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request["request_id"], started, return_code, stdout, stderr),
        "request_ref": request["request_id"],
        "agent_ref": request["agent_ref"],
        "runner_command": runner_command,
        "status": status,
        "return_code": return_code,
        "stdout": stdout[-8000:],
        "stderr": stderr[-8000:],
        "started_at_utc": started,
        "completed_at_utc": completed,
    }
    validate_agent_error_diagnosis(diagnosis)
    return diagnosis


def build_queued_diagnosis(request: Mapping[str, Any], *, reason: str = "agent runner not configured") -> dict[str, Any]:
    diagnosis = {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request["request_id"], reason),
        "request_ref": request["request_id"],
        "agent_ref": request["agent_ref"],
        "runner_command": None,
        "status": "queued",
        "return_code": None,
        "stdout": "",
        "stderr": reason,
        "started_at_utc": None,
        "completed_at_utc": _now_utc(),
    }
    validate_agent_error_diagnosis(diagnosis)
    return diagnosis


def validate_agent_error_diagnosis(diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(diagnosis)
    required = ("contract_type", "schema_version", "diagnosis_id", "request_ref", "agent_ref", "status", "completed_at_utc")
    for field in required:
        value = normalized.get(field)
        if value in (None, ""):
            raise TaskSystemError(f"missing required agent error diagnosis field: {field}")
    if normalized["contract_type"] != AGENT_ERROR_DIAGNOSIS_CONTRACT:
        raise TaskSystemError(f"contract_type must be {AGENT_ERROR_DIAGNOSIS_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if normalized["status"] not in {"queued", "completed", "agent_call_failed"}:
        raise TaskSystemError(f"unsupported agent diagnosis status: {normalized['status']}")
    return normalized



def _discord_message(request: Mapping[str, Any], diagnosis: Mapping[str, Any], *, server_id: str | None = None) -> str:
    severity = str(request.get("severity") or "error").upper()
    component = request.get("source_component") or "unknown component"
    summary = request.get("summary") or "server error"
    error_kind = request.get("error_kind") or "unclassified_error"
    scope = request.get("error_scope") or "server"
    exit_code = request.get("exit_code")
    request_id = request.get("request_id")
    error_ref = request.get("error_ref") or request.get("request_id")
    diagnosis_status = diagnosis.get("status")
    occurred_at = _format_alert_time(request.get("occurred_at_utc"))
    created_at = _format_alert_time(request.get("created_at_utc"))
    dedup_note = "yes" if request.get("error_deduplicated") else "no"
    stderr_path = request.get("stderr_path")
    stdout_path = request.get("stdout_path")
    lines = [
        f"🚨 Trading server error [{severity}]",
        f"Component: {component}",
        f"Scope: {scope}",
        f"Kind: {error_kind}",
        f"Summary: {summary}",
        f"Occurred: {occurred_at}",
        f"Recorded: {created_at}",
        f"Agent diagnosis: {diagnosis_status}",
        f"Manager Error No: {error_ref}",
        f"Deduplicated: {dedup_note}",
        f"Agent Request: {request_id}",
    ]
    if server_id:
        lines.insert(1, f"Discord server: {server_id}")
    if exit_code is not None:
        lines.append(f"Exit code: {exit_code}")
    if stderr_path:
        lines.append(f"stderr: {stderr_path}")
    elif stdout_path:
        lines.append(f"stdout: {stdout_path}")
    lines.append("Boundaries: no provider calls, broker/account mutation, or destructive repair without separate approval.")
    return "\n".join(lines)


def notify_discord_for_error(
    request: Mapping[str, Any],
    diagnosis: Mapping[str, Any],
    *,
    target: str | None = None,
    server_id: str | None = None,
    account_id: str | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Send a best-effort Discord notification through OpenClaw's message CLI."""

    resolved_target = target or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_TARGET", "").strip() or DEFAULT_DISCORD_TARGET
    resolved_server_id = server_id or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_SERVER_ID", "").strip() or DEFAULT_DISCORD_SERVER_ID
    resolved_account_id = account_id or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_ACCOUNT_ID", "").strip() or None
    if not resolved_target:
        return {"status": "skipped", "reason": "discord target not configured"}
    message = _discord_message(request, diagnosis, server_id=resolved_server_id)
    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        "discord",
        "--target",
        resolved_target,
        "--message",
        message,
    ]
    if resolved_account_id:
        cmd.extend(["--account", resolved_account_id])
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "failed", "reason": str(exc), "target": resolved_target}
    return {
        "status": "sent" if result.returncode == 0 else "failed",
        "target": resolved_target,
        "return_code": result.returncode,
        "stdout": result.stdout[-1000:],
        "stderr": result.stderr[-1000:],
    }


def handle_server_error(
    *,
    source_component: str,
    summary: str,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    call_agent: bool = False,
    runner_command: str | None = None,
    notify_discord: bool | None = None,
    discord_target: str | None = None,
    discord_server_id: str | None = None,
    discord_account_id: str | None = None,
    database_url: str | None = None,
    catalog_storage: str = "sql",
    **request_kwargs: Any,
) -> dict[str, Any]:
    """Create the standard request and optionally call the configured agent runner."""

    request = build_server_error_agent_request(source_component=source_component, summary=summary, **request_kwargs)
    request, catalog_entry = register_error_in_catalog(
        request,
        output_root=output_root,
        database_url=database_url,
        catalog_storage=catalog_storage,
    )
    request_path = default_request_path(request, output_root)
    write_json_artifact(request, path=request_path)
    configured_runner = runner_command or os.environ.get("MANAGER_AGENT_ERROR_RUNNER_COMMAND", "").strip()
    effective_call_agent = call_agent or _env_truthy("MANAGER_AGENT_ERROR_AUTOCALL")
    if effective_call_agent and configured_runner:
        diagnosis = call_agent_runner(request, runner_command=configured_runner)
    else:
        diagnosis = build_queued_diagnosis(request, reason="agent runner not configured" if effective_call_agent else "agent call not requested")
    should_notify_discord = (
        bool(notify_discord)
        if notify_discord is not None
        else (_env_truthy("MANAGER_AGENT_ERROR_NOTIFY_DISCORD") or bool(discord_target) or bool(os.environ.get("MANAGER_AGENT_ERROR_DISCORD_TARGET")))
    )
    notify_duplicates = _env_truthy("MANAGER_AGENT_ERROR_NOTIFY_DUPLICATES")
    if should_notify_discord and request.get("error_deduplicated") and not notify_duplicates:
        discord_notification = {
            "status": "deduplicated",
            "reason": "duplicate error within dedup window; notification suppressed",
            "error_ref": request.get("error_ref"),
        }
    else:
        discord_notification = (
            notify_discord_for_error(
                request,
                diagnosis,
                target=discord_target,
                server_id=discord_server_id,
                account_id=discord_account_id,
            )
            if should_notify_discord
            else {"status": "skipped", "reason": "discord notification not requested"}
        )
    diagnosis = dict(diagnosis)
    diagnosis["discord_notification"] = discord_notification
    diagnosis_path = default_diagnosis_path(request, output_root)
    write_json_artifact(diagnosis, path=diagnosis_path)
    result = {
        "contract_type": AGENT_ERROR_HANDLING_RESULT_CONTRACT,
        "schema_version": "1",
        "error_number": request["error_number"],
        "error_ref": request["error_ref"],
        "error_fingerprint": request["error_fingerprint"],
        "error_deduplicated": bool(request.get("error_deduplicated")),
        "error_catalog_entry": catalog_entry,
        "request_id": request["request_id"],
        "request_path": str(request_path),
        "diagnosis_id": diagnosis["diagnosis_id"],
        "diagnosis_path": str(diagnosis_path),
        "status": diagnosis["status"],
        "discord_notification": discord_notification,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a server-wide agent diagnosis/repair request for an observed error.")
    parser.add_argument("--source-component", required=True)
    parser.add_argument("--source-repo")
    parser.add_argument("--error-scope", default="server")
    parser.add_argument("--error-kind", default="unclassified_error")
    parser.add_argument("--severity", default="error", choices=tuple(sorted(ALLOWED_SEVERITIES)))
    parser.add_argument("--summary", required=True)
    parser.add_argument("--command", action="append", default=[], help="Command token or full command string associated with the error; may be repeated.")
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--stdout-path")
    parser.add_argument("--stderr-path")
    parser.add_argument("--working-directory")
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--occurred-at-utc")
    parser.add_argument("--agent-ref", default=DEFAULT_AGENT_REF)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--call-agent", action="store_true", help="Invoke the configured agent runner; otherwise only queue/write the request artifacts.")
    parser.add_argument("--agent-runner-command", help="Reviewed local command that accepts request JSON on stdin and returns diagnosis text/JSON on stdout.")
    parser.add_argument("--notify-discord", action="store_true", help="Send a Discord alert through OpenClaw's message CLI after writing diagnosis artifacts.")
    parser.add_argument("--discord-target", default=None, help="Discord target such as channel:1504100135200620665; defaults to MANAGER_AGENT_ERROR_DISCORD_TARGET.")
    parser.add_argument("--discord-server-id", default=None, help="Optional Discord server/guild id for alert context.")
    parser.add_argument("--discord-account-id", default=None, help="Optional OpenClaw Discord account id; defaults to plugin account resolution.")
    parser.add_argument("--database-url", help="Database URL for SQL-backed server error catalog; defaults to DATABASE_URL or local secret.")
    parser.add_argument("--catalog-storage", choices=tuple(sorted(CATALOG_STORAGES)), default="sql")
    args = parser.parse_args(argv)
    result = handle_server_error(
        source_component=args.source_component,
        source_repo=args.source_repo,
        error_scope=args.error_scope,
        error_kind=args.error_kind,
        severity=args.severity,
        summary=args.summary,
        command=args.command,
        exit_code=args.exit_code,
        stdout_path=args.stdout_path,
        stderr_path=args.stderr_path,
        working_directory=args.working_directory,
        evidence_refs=args.evidence_ref,
        occurred_at_utc=args.occurred_at_utc,
        agent_ref=args.agent_ref,
        output_root=args.output_root,
        call_agent=args.call_agent,
        runner_command=args.agent_runner_command,
        notify_discord=args.notify_discord,
        discord_target=args.discord_target,
        discord_server_id=args.discord_server_id,
        discord_account_id=args.discord_account_id,
        database_url=args.database_url,
        catalog_storage=args.catalog_storage,
    )
    write_json_artifact(result, output=sys.stdout)
    return 0


__all__ = [
    "AGENT_ERROR_DIAGNOSIS_CONTRACT",
    "AGENT_ERROR_HANDLING_RESULT_CONTRACT",
    "CATALOG_STORAGES",
    "DEFAULT_ERROR_CATALOG_NAME",
    "SERVER_ERROR_CATALOG_TABLE",
    "SERVER_ERROR_AGENT_REQUEST_CONTRACT",
    "SERVER_ERROR_CATALOG_ENTRY_CONTRACT",
    "SERVER_ERROR_CATALOG_OCCURRENCE_CONTRACT",
    "build_agent_prompt",
    "build_queued_diagnosis",
    "build_server_error_agent_request",
    "call_agent_runner",
    "fetch_server_error_catalog_rows",
    "handle_server_error",
    "notify_discord_for_error",
    "persist_server_error_catalog_rows",
    "register_error_in_catalog",
    "validate_agent_error_diagnosis",
    "validate_server_error_catalog_entry",
    "validate_server_error_agent_request",
    "write_json_artifact",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

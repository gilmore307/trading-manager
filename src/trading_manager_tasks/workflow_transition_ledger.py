"""Canonical historical workflow transition ledger.

The scheduler may still maintain specialized workflow state files, decision
logs, stage receipts, and dashboard read models.  This ledger is the narrow
runtime contract that records each observed transition in one place so status
surfaces and repair loops do not infer the current task from divergent sources.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .storage_paths import manager_storage_root

DEFAULT_RUNTIME_DIR = manager_storage_root() / "runtime"
DEFAULT_TRANSITION_LOG_PATH = DEFAULT_RUNTIME_DIR / "historical_workflow_transitions.jsonl"
DEFAULT_LATEST_TRANSITION_PATH = DEFAULT_RUNTIME_DIR / "historical_workflow_transition_latest.json"
DEFAULT_TRANSITION_LOG_MAX_BYTES = 8 * 1024 * 1024


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string(value: Any) -> str:
    return str(value or "").strip()


def _first_string(*values: Any) -> str | None:
    for value in values:
        text = _string(value)
        if text:
            return text
    return None


def _extract_workflow_plan(row: Mapping[str, Any]) -> Mapping[str, Any]:
    execution_summary = _as_mapping(row.get("execution_summary"))
    return _as_mapping(execution_summary.get("workflow_plan"))


def _extract_fold_scope(row: Mapping[str, Any]) -> Mapping[str, Any]:
    execution_summary = _as_mapping(row.get("execution_summary"))
    return _as_mapping(execution_summary.get("fold_scope"))


def _extract_scope(row: Mapping[str, Any]) -> dict[str, str | None]:
    workflow_plan = _extract_workflow_plan(row)
    fold_scope = _extract_fold_scope(row)
    execution_summary = _as_mapping(row.get("execution_summary"))
    start_month = _first_string(
        row.get("start_month"),
        row.get("month_start"),
        fold_scope.get("start_month"),
        execution_summary.get("start_month"),
        execution_summary.get("month_start"),
        workflow_plan.get("start_month"),
    )
    end_month = _first_string(
        row.get("end_month"),
        row.get("month_end"),
        fold_scope.get("end_month"),
        execution_summary.get("end_month"),
        execution_summary.get("month_end"),
        workflow_plan.get("end_month"),
    )
    target_symbol = _first_string(
        row.get("selected_target_symbol"),
        row.get("target_symbol"),
        row.get("target_ref"),
        fold_scope.get("target_symbol"),
        execution_summary.get("selected_target_symbol"),
        execution_summary.get("target_symbol"),
        workflow_plan.get("selected_target_symbol"),
    )
    if target_symbol:
        target_symbol = target_symbol.upper()
    fold_id = _first_string(row.get("fold_id"), fold_scope.get("fold_id"))
    if not fold_id and start_month and end_month:
        fold_id = f"fold_{start_month}_{end_month}"
    return {
        "start_month": start_month,
        "end_month": end_month,
        "fold_id": fold_id,
        "target_symbol": target_symbol,
    }


def _event_type(row: Mapping[str, Any]) -> str:
    decision_status = _string(row.get("decision_status"))
    reason_code = _string(row.get("reason_code"))
    if decision_status == "error":
        return "task_failed"
    if decision_status == "executed":
        return "task_step_completed"
    if decision_status == "ready":
        return "task_ready"
    if "failed" in reason_code or "error" in reason_code:
        return "task_failed"
    if decision_status == "backoff":
        return "task_waiting"
    return "task_observed"


def _task_status(row: Mapping[str, Any]) -> str:
    decision_status = _string(row.get("decision_status"))
    reason_code = _string(row.get("reason_code"))
    if decision_status == "error":
        return "failed"
    if decision_status == "executed":
        return "completed"
    if decision_status == "ready":
        return "ready"
    if "failed" in reason_code or "error" in reason_code:
        return "failed"
    if decision_status == "backoff":
        return "waiting"
    return decision_status or "observed"


def _next_action(row: Mapping[str, Any]) -> str | None:
    execution_summary = _as_mapping(row.get("execution_summary"))
    return _first_string(
        execution_summary.get("required_next_step"),
        execution_summary.get("required_next_action"),
        row.get("next_internal_stage"),
        row.get("reason"),
    )


def _transition_id(row: Mapping[str, Any], recorded_at_utc: str) -> str:
    identity = {
        "recorded_at_utc": recorded_at_utc,
        "now_utc": row.get("now_utc"),
        "selected_work": row.get("selected_work"),
        "reason_code": row.get("reason_code"),
        "decision_status": row.get("decision_status"),
        "worker_id": row.get("worker_id"),
    }
    digest = hashlib.sha1(json.dumps(identity, sort_keys=True, default=str).encode("utf-8")).hexdigest()
    return f"hwf-{digest[:16]}"


def transition_from_decision_row(row: Mapping[str, Any], *, recorded_at_utc: str | None = None) -> dict[str, Any]:
    """Build the canonical transition row from a scheduler decision row."""

    recorded = recorded_at_utc or utc_now_iso()
    scope = _extract_scope(row)
    selected_work = _first_string(row.get("selected_work"), row.get("next_internal_stage")) or "historical_scheduler"
    decision_status = _string(row.get("decision_status")) or None
    reason_code = _string(row.get("reason_code")) or None
    transition = {
        "contract_type": "manager_historical_workflow_transition",
        "schema_version": 1,
        "transition_id": _transition_id(row, recorded),
        "recorded_at_utc": recorded,
        "source": "historical_scheduler_decision",
        "source_decision_utc": _first_string(row.get("now_utc"), row.get("generated_at_utc")),
        "now_utc": _first_string(row.get("now_utc"), row.get("generated_at_utc"), recorded),
        "event_type": _event_type(row),
        "task_status": _task_status(row),
        "selected_work": selected_work,
        "worker_id": _first_string(row.get("worker_id")),
        "decision_status": decision_status,
        "reason_code": reason_code,
        "reason": _first_string(row.get("reason")),
        "next_internal_stage": _first_string(row.get("next_internal_stage")),
        "next_action": _next_action(row),
        "start_month": scope["start_month"],
        "end_month": scope["end_month"],
        "fold_id": scope["fold_id"],
        "target_symbol": scope["target_symbol"],
        "provider_calls": int(row.get("provider_calls") or 0),
        "dispatch_performed": bool(row.get("dispatch_performed", False)),
        "model_activation_performed": bool(row.get("model_activation_performed", False)),
        "broker_execution_performed": bool(row.get("broker_execution_performed", False)),
        "storage_lifecycle_mutation_performed": bool(row.get("storage_lifecycle_mutation_performed", False)),
        "repair_error_ref": _first_string(row.get("error_ref"), row.get("agent_error_ref")),
    }
    return transition


def read_latest_transition(path: Path = DEFAULT_LATEST_TRANSITION_PATH) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def append_transition(
    row: Mapping[str, Any],
    *,
    log_path: Path = DEFAULT_TRANSITION_LOG_PATH,
    latest_path: Path = DEFAULT_LATEST_TRANSITION_PATH,
    recorded_at_utc: str | None = None,
    max_bytes: int = DEFAULT_TRANSITION_LOG_MAX_BYTES,
) -> dict[str, Any]:
    transition = transition_from_decision_row(row, recorded_at_utc=recorded_at_utc)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(transition, sort_keys=True) + "\n")
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = latest_path.with_suffix(latest_path.suffix + ".tmp")
    tmp.write_text(json.dumps(transition, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(latest_path)
    compact_transition_log_tail(log_path, max_bytes=max_bytes)
    return transition


def compact_transition_log_tail(path: Path, *, max_bytes: int = DEFAULT_TRANSITION_LOG_MAX_BYTES) -> None:
    if max_bytes <= 0 or not path.exists() or path.stat().st_size <= max_bytes:
        return
    with path.open("rb") as handle:
        handle.seek(-max_bytes, os.SEEK_END)
        payload = handle.read()
    first_newline = payload.find(b"\n")
    if first_newline < 0:
        return
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_bytes(payload[first_newline + 1 :])
    os.replace(temp_path, path)


__all__ = [
    "DEFAULT_LATEST_TRANSITION_PATH",
    "DEFAULT_TRANSITION_LOG_PATH",
    "append_transition",
    "compact_transition_log_tail",
    "read_latest_transition",
    "transition_from_decision_row",
]

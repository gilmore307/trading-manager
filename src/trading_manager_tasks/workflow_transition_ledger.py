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


def _load_json_mapping(path_ref: Any) -> Mapping[str, Any]:
    path_text = _string(path_ref)
    if not path_text:
        return {}
    try:
        payload = json.loads(Path(path_text).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


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
    training_fold = _as_mapping(execution_summary.get("training_fold"))
    evaluation_receipt = _load_json_mapping(execution_summary.get("model_group_evaluation_receipt"))
    start_month = _first_string(
        row.get("start_month"),
        row.get("month_start"),
        fold_scope.get("start_month"),
        training_fold.get("start_month"),
        evaluation_receipt.get("start_month"),
        execution_summary.get("start_month"),
        execution_summary.get("month_start"),
        workflow_plan.get("start_month"),
    )
    end_month = _first_string(
        row.get("end_month"),
        row.get("month_end"),
        fold_scope.get("end_month"),
        training_fold.get("end_month"),
        evaluation_receipt.get("end_month"),
        execution_summary.get("end_month"),
        execution_summary.get("month_end"),
        workflow_plan.get("end_month"),
    )
    target_symbol = _first_string(
        row.get("selected_target_symbol"),
        row.get("target_symbol"),
        row.get("target_ref"),
        fold_scope.get("target_symbol"),
        training_fold.get("target_symbol"),
        evaluation_receipt.get("target_symbol"),
        evaluation_receipt.get("candidate_training_target"),
        execution_summary.get("selected_target_symbol"),
        execution_summary.get("target_symbol"),
        workflow_plan.get("selected_target_symbol"),
    )
    if target_symbol:
        target_symbol = target_symbol.upper()
    fold_id = _first_string(
        row.get("fold_id"),
        fold_scope.get("fold_id"),
        training_fold.get("fold_id"),
        evaluation_receipt.get("fold_id"),
        evaluation_receipt.get("candidate_fold_id"),
    )
    if not fold_id and start_month and end_month:
        fold_id = f"fold_{start_month}_{end_month}"
    return {
        "start_month": start_month,
        "end_month": end_month,
        "fold_id": fold_id,
        "target_symbol": target_symbol,
    }


def _extract_candidate_scope(row: Mapping[str, Any], *, fold_id: str | None, target_symbol: str | None) -> dict[str, str | None]:
    execution_summary = _as_mapping(row.get("execution_summary"))
    training_fold = _as_mapping(execution_summary.get("training_fold"))
    replay_receipt = _as_mapping(execution_summary.get("replay_execution_receipt"))
    evaluation_receipt = _load_json_mapping(execution_summary.get("model_group_evaluation_receipt"))
    candidate_model_ref = _first_string(
        row.get("candidate_model_ref"),
        execution_summary.get("candidate_model_ref"),
        training_fold.get("candidate_model_ref"),
        replay_receipt.get("candidate_model_ref"),
        evaluation_receipt.get("candidate_model_ref"),
        execution_summary.get("model_group_ref"),
    )
    candidate_fold_id = _first_string(
        row.get("candidate_fold_id"),
        execution_summary.get("candidate_fold_id"),
        training_fold.get("candidate_fold_id"),
        replay_receipt.get("candidate_fold_id"),
        evaluation_receipt.get("candidate_fold_id"),
        training_fold.get("fold_id"),
        evaluation_receipt.get("fold_id"),
        fold_id,
    )
    candidate_training_target = _first_string(
        row.get("candidate_training_target"),
        execution_summary.get("candidate_training_target"),
        training_fold.get("candidate_training_target"),
        replay_receipt.get("candidate_training_target"),
        evaluation_receipt.get("candidate_training_target"),
        target_symbol,
    )
    if candidate_training_target:
        candidate_training_target = candidate_training_target.upper()
    replay_execution_run_id = _first_string(
        row.get("replay_execution_run_id"),
        execution_summary.get("replay_execution_run_id"),
        replay_receipt.get("replay_execution_run_id"),
        evaluation_receipt.get("replay_execution_run_id"),
    )
    return {
        "candidate_model_ref": candidate_model_ref,
        "candidate_fold_id": candidate_fold_id,
        "candidate_training_target": candidate_training_target,
        "replay_execution_run_id": replay_execution_run_id,
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


def _selection_status(reason_code: str | None) -> tuple[str, str]:
    reason = _string(reason_code)
    if reason.startswith("waiting_") or reason.startswith("blocked_") or "holds_" in reason:
        return "task_waiting", "waiting"
    return "task_selected", "selected"


def _selection_work(reason_code: str | None) -> tuple[str, str]:
    reason = _string(reason_code)
    if reason.startswith("model_group_lifecycle") or "lifecycle_holds" in reason:
        return "model_group.lifecycle", "model_group_lifecycle"
    if "model_worker_fold" in reason or reason in {"complete_foundation_fold_ready", "resume_open_model_worker_fold"}:
        return "model_worker.fold", "model_worker_1"
    if reason.startswith("waiting_"):
        return "historical_scheduler.wait", "historical_scheduler"
    return "single_month_work_loop", "historical_training_work_loop"


def _task_id_for(selected_work: str | None) -> str | None:
    work = _string(selected_work)
    if not work:
        return None
    if work.startswith("model_group."):
        return work
    if "." in work:
        return work.split(".", 1)[0]
    return work


def _timeline_fields(
    *,
    recorded_at_utc: str,
    task_status: str,
    source_started_at: Any = None,
    source_ended_at: Any = None,
    source_updated_at: Any = None,
) -> dict[str, str | None]:
    """Return stable task-clock fields for every ledger transition.

    Upstream scheduler decisions historically omitted start/end clocks for
    many route-level observations.  The ledger is the current task contract,
    so it must still provide a usable clock to dashboard and repair surfaces
    instead of leaking "Runtime Not started".
    """

    started = _first_string(source_started_at)
    ended = _first_string(source_ended_at)
    updated = _first_string(source_updated_at, recorded_at_utc) or recorded_at_utc
    status = _string(task_status)
    if status in {"completed", "failed"}:
        ended = ended or updated
        started = started or ended
    elif status in {"selected", "ready", "waiting", "observed"}:
        started = started or updated
    return {
        "created_at": recorded_at_utc,
        "created_at_utc": recorded_at_utc,
        "started_at": started,
        "ended_at": ended,
        "status_updated_at": updated,
        "status_updated_at_utc": updated,
    }


def transition_from_work_selection(
    selection: Mapping[str, Any],
    *,
    selected_target_symbol: str | None = None,
    recorded_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build the canonical transition row from a lane/fold selection.

    Scheduler decisions record work that was evaluated or executed.  The
    resident task system also needs a current owner before a stage decision
    exists, otherwise status surfaces start inferring active work from old
    decisions.  This transition type records the selected lane directly.
    """

    recorded = recorded_at_utc or utc_now_iso()
    reason_code = _first_string(selection.get("reason_code"))
    event_type, task_status = _selection_status(reason_code)
    selected_work, next_internal_stage = _selection_work(reason_code)
    start_month = _first_string(selection.get("start_month"), selection.get("blocked_fold_start_month"))
    end_month = _first_string(selection.get("end_month"), selection.get("blocked_fold_end_month"))
    target_symbol = _first_string(selected_target_symbol, selection.get("blocked_target_symbol"))
    if target_symbol:
        target_symbol = target_symbol.upper()
    fold_id = _first_string(selection.get("fold_id"))
    if not fold_id and start_month and end_month:
        fold_id = f"fold_{start_month}_{end_month}"
    row = {
        "now_utc": recorded,
        "selected_work": selected_work,
        "reason_code": reason_code,
        "decision_status": task_status,
        "worker_id": "scheduler_lane",
    }
    transition = {
        "contract_type": "manager_historical_workflow_transition",
        "schema_version": 1,
        "transition_id": _transition_id(row, recorded),
        "recorded_at_utc": recorded,
        "source": "historical_work_selection",
        "source_decision_utc": None,
        "now_utc": recorded,
        "event_type": event_type,
        "task_status": task_status,
        "task_id": _task_id_for(selected_work),
        "selected_work": selected_work,
        "worker_id": "scheduler_lane",
        "decision_status": task_status,
        "reason_code": reason_code,
        "reason": _first_string(selection.get("reason"), reason_code),
        "next_internal_stage": next_internal_stage,
        "next_action": next_internal_stage,
        "start_month": start_month,
        "end_month": end_month,
        "fold_id": fold_id,
        "target_symbol": target_symbol,
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "repair_error_ref": None,
    }
    transition.update(_timeline_fields(recorded_at_utc=recorded, task_status=task_status))
    return transition


def transition_from_decision_row(row: Mapping[str, Any], *, recorded_at_utc: str | None = None) -> dict[str, Any]:
    """Build the canonical transition row from a scheduler decision row."""

    recorded = recorded_at_utc or utc_now_iso()
    scope = _extract_scope(row)
    selected_work = _first_string(row.get("selected_work"), row.get("next_internal_stage")) or "historical_scheduler"
    decision_status = _string(row.get("decision_status")) or None
    reason_code = _string(row.get("reason_code")) or None
    task_status = _task_status(row)
    candidate_scope = _extract_candidate_scope(
        row,
        fold_id=scope["fold_id"],
        target_symbol=scope["target_symbol"],
    )
    transition = {
        "contract_type": "manager_historical_workflow_transition",
        "schema_version": 1,
        "transition_id": _transition_id(row, recorded),
        "recorded_at_utc": recorded,
        "source": "historical_scheduler_decision",
        "source_decision_utc": _first_string(row.get("now_utc"), row.get("generated_at_utc")),
        "now_utc": _first_string(row.get("now_utc"), row.get("generated_at_utc"), recorded),
        "event_type": _event_type(row),
        "task_status": task_status,
        "task_id": _task_id_for(selected_work),
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
        "candidate_model_ref": candidate_scope["candidate_model_ref"],
        "candidate_fold_id": candidate_scope["candidate_fold_id"],
        "candidate_training_target": candidate_scope["candidate_training_target"],
        "replay_execution_run_id": candidate_scope["replay_execution_run_id"],
        "provider_calls": int(row.get("provider_calls") or 0),
        "dispatch_performed": bool(row.get("dispatch_performed", False)),
        "model_activation_performed": bool(row.get("model_activation_performed", False)),
        "broker_execution_performed": bool(row.get("broker_execution_performed", False)),
        "storage_lifecycle_mutation_performed": bool(row.get("storage_lifecycle_mutation_performed", False)),
        "repair_error_ref": _first_string(row.get("error_ref"), row.get("agent_error_ref")),
    }
    transition.update(
        _timeline_fields(
            recorded_at_utc=recorded,
            task_status=task_status,
            source_started_at=_first_string(
                row.get("started_at"),
                row.get("started_at_utc"),
                row.get("stage_started_at"),
                row.get("stage_started_at_utc"),
            ),
            source_ended_at=_first_string(
                row.get("ended_at"),
                row.get("ended_at_utc"),
                row.get("completed_at"),
                row.get("completed_at_utc"),
                row.get("stage_completed_at"),
                row.get("stage_completed_at_utc"),
            ),
            source_updated_at=_first_string(row.get("now_utc"), row.get("generated_at_utc")),
        )
    )
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


def append_work_selection_transition(
    selection: Mapping[str, Any],
    *,
    selected_target_symbol: str | None = None,
    log_path: Path = DEFAULT_TRANSITION_LOG_PATH,
    latest_path: Path = DEFAULT_LATEST_TRANSITION_PATH,
    recorded_at_utc: str | None = None,
    max_bytes: int = DEFAULT_TRANSITION_LOG_MAX_BYTES,
) -> dict[str, Any]:
    transition = transition_from_work_selection(
        selection,
        selected_target_symbol=selected_target_symbol,
        recorded_at_utc=recorded_at_utc,
    )
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
    "append_work_selection_transition",
    "compact_transition_log_tail",
    "read_latest_transition",
    "transition_from_decision_row",
    "transition_from_work_selection",
]

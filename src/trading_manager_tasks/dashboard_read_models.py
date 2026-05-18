"""Dashboard summary/read-model producers owned by trading-manager.

These helpers build owner-facing semantic summary payloads for the accepted
storage-hosted dashboard read-model contracts.  They do not write the storage
layout themselves, call providers, activate models, submit broker orders, or
mutate account state.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .model_training_state import advance_workflow_state
from .model_training_workflow import FOUNDATION_CATCH_UP_STAGE_TYPES, MONTHLY_SUBSTRATE_LAYERS, build_model_training_workflow_plan
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler_daemon import DEFAULT_MONTH_INGEST_WORKERS, completed_historical_month_cutoff, select_model_worker_fold, select_month_ingest_worker_months
from .scheduler_status import (
    DEFAULT_DAEMON_WRAPPER_PATH,
    DEFAULT_DECISION_LOG_PATH,
    DEFAULT_LOCK_PATH,
    DEFAULT_SERVICE_ENV_PATH,
    DEFAULT_SERVICE_TEMPLATE_PATH,
    DEFAULT_STATE_PATH,
    HistoricalSchedulerStatus,
    collect_historical_scheduler_status,
)
from .agent_error_handler import DEFAULT_ERROR_CATALOG_NAME

HISTORICAL_TASK_PROGRESS_CONTRACT = "historical_task_progress_summary"
HISTORICAL_TASK_PROGRESS_SCHEMA_REF = f"storage/dashboard/schemas/{HISTORICAL_TASK_PROGRESS_CONTRACT}.schema.json"
DEFAULT_STALE_AFTER_SECONDS = 900
MONTHLY_TASK_STAGE_TYPES = {"data_acquisition", "feature_generation"}
FOLD_MODEL_STAGE_TYPES = {"model_generation", "model_evaluation", "promotion_review", "maintenance"}
MONTHS_PER_MODEL_FOLD = 6
MONTHLY_TASKS_PER_FOLD = MONTHS_PER_MODEL_FOLD * 6
MODEL_TASKS_PER_FOLD = 9 * 4
TASKS_PER_MODEL_FOLD = MONTHLY_TASKS_PER_FOLD + MODEL_TASKS_PER_FOLD
BASE_TASK_YEAR = 2016
BASE_TASK_MONTH = 1
MAX_AGENT_ERROR_SUMMARY_ROWS = 50


def now_utc() -> str:
    """Return an ISO-8601 UTC timestamp with Z suffix."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stage_counts(status: HistoricalSchedulerStatus) -> dict[str, int]:
    return dict(status.workflow_checkpoint.stage_counts)


def _progress_percent(stage_counts: Mapping[str, int]) -> float:
    total = sum(int(value) for value in stage_counts.values())
    if total <= 0:
        return 0.0
    terminal = int(stage_counts.get("succeeded", 0)) + int(stage_counts.get("not_applicable", 0))
    return round((terminal / total) * 100.0, 2)


def _resolve_local_path(path: object) -> Path | None:
    if not isinstance(path, str) or not path.strip():
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else Path.cwd() / candidate


def _failure_excerpt(path: object, *, max_chars: int = 800) -> str | None:
    """Return a bounded, human-useful failure excerpt from a local stderr/stdout ref."""

    candidate = _resolve_local_path(path)
    if candidate is None or not candidate.exists() or not candidate.is_file():
        return None
    text = candidate.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    error_lines = [line for line in lines if "Error:" in line or line.endswith("Error") or "Traceback" in line]
    excerpt = error_lines[-1] if error_lines else lines[-1]
    return excerpt[-max_chars:]


def _agent_error_catalog_path(storage_root: Path) -> Path:
    return storage_root / "runtime" / "agent_error_handling" / DEFAULT_ERROR_CATALOG_NAME


def _load_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _agent_result_payload(diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    stdout = diagnosis.get("stdout")
    if not isinstance(stdout, str) or not stdout.strip():
        return {}
    try:
        outer = json.loads(stdout)
    except json.JSONDecodeError:
        return {}
    if not isinstance(outer, Mapping):
        return {}
    if outer.get("diagnosis_status") or outer.get("repair"):
        return dict(outer)
    result = outer.get("result")
    if not isinstance(result, Mapping):
        return {}
    payloads = result.get("payloads")
    if not isinstance(payloads, list) or not payloads:
        return {}
    first = payloads[0]
    if not isinstance(first, Mapping):
        return {}
    text = first.get("text")
    if not isinstance(text, str) or not text.strip():
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"agent_text": text}
    return parsed if isinstance(parsed, dict) else {"agent_text": text}


def _agent_repair_status(diagnosis: Mapping[str, Any], agent_payload: Mapping[str, Any]) -> str:
    diagnosis_status = str(diagnosis.get("status") or "").lower()
    if diagnosis_status == "queued":
        return "queued"
    if diagnosis_status and diagnosis_status != "completed":
        return "agent_call_failed"
    agent_status = str(agent_payload.get("diagnosis_status") or "").lower()
    repair = agent_payload.get("repair")
    nested_repair_status = str(repair.get("repair_status") or "").lower() if isinstance(repair, Mapping) else ""
    verification = agent_payload.get("verification")
    verification_exit_code = verification.get("exit_code") if isinstance(verification, Mapping) else None
    if agent_status in {"repaired", "resolved", "fixed", "repair_verified"} or nested_repair_status == "repaired" or verification_exit_code == 0:
        return "repaired"
    if nested_repair_status in {"not_supported", "blocked", "failed"}:
        return nested_repair_status
    if agent_status in {"no_action_needed", "not_needed", "not_reproducible"}:
        return "no_action_needed"
    if agent_payload.get("repair_attempted") is True:
        return "repair_attempted"
    if diagnosis_status == "completed":
        return "diagnosed"
    return "unknown"


def _agent_error_handling_status(catalog_row: Mapping[str, Any], repair_status: str) -> str:
    if repair_status == "repaired":
        scope = str(catalog_row.get("error_scope") or "")
        component = str(catalog_row.get("source_component") or "")
        if "model_training_stage" in scope or component == "trading-manager.stage_executor":
            return "awaiting_retry"
        return "closed"
    if repair_status == "no_action_needed":
        return "no_action_required"
    return "open"


def _dashboard_error_severity(catalog_row: Mapping[str, Any], handling_status: str) -> str:
    if handling_status in {"closed", "no_action_required"}:
        return "notice"
    if handling_status == "awaiting_retry":
        return "warning"
    severity = str(catalog_row.get("severity") or "error").lower()
    if severity == "critical":
        return "critical"
    if severity == "warning":
        return "warning"
    if severity == "info":
        return "notice"
    return "error"


def _agent_error_summary(storage_root: Path, *, limit: int = MAX_AGENT_ERROR_SUMMARY_ROWS) -> list[dict[str, Any]]:
    catalog_path = _agent_error_catalog_path(storage_root)
    rows = _load_jsonl_objects(catalog_path)
    if not rows:
        return []
    summary_rows: list[dict[str, Any]] = []
    for row in rows[-limit:]:
        diagnosis_path = _resolve_stage_ref_path(row.get("diagnosis_path"), storage_root=storage_root)
        diagnosis: dict[str, Any] = {}
        if diagnosis_path is not None and diagnosis_path.exists():
            try:
                diagnosis = _load_json_object(diagnosis_path)
            except (OSError, ValueError, json.JSONDecodeError):
                diagnosis = {}
        agent_payload = _agent_result_payload(diagnosis)
        repair_status = _agent_repair_status(diagnosis, agent_payload)
        handling_status = _agent_error_handling_status(row, repair_status)
        repair_payload = agent_payload.get("repair") if isinstance(agent_payload.get("repair"), Mapping) else {}
        files_changed = agent_payload.get("files_changed")
        if not isinstance(files_changed, list):
            files_changed = repair_payload.get("files_changed") if isinstance(repair_payload.get("files_changed"), list) else []
        summary_rows.append(
            {
                "error_ref": row.get("error_ref"),
                "error_number": row.get("error_number"),
                "error_kind": row.get("error_kind"),
                "error_scope": row.get("error_scope"),
                "source_component": row.get("source_component"),
                "source_repo": row.get("source_repo"),
                "summary": row.get("summary"),
                "occurred_at_utc": row.get("occurred_at_utc"),
                "created_at_utc": row.get("created_at_utc"),
                "severity": row.get("severity"),
                "dashboard_severity": _dashboard_error_severity(row, handling_status),
                "diagnosis_status": diagnosis.get("status") or "missing",
                "repair_status": repair_status,
                "handling_status": handling_status,
                "retry_recommendation": agent_payload.get("retry_recommendation"),
                "root_cause": agent_payload.get("root_cause"),
                "files_changed": files_changed,
                "request_path": row.get("request_path"),
                "diagnosis_path": row.get("diagnosis_path"),
            }
        )
    return summary_rows


def _latest_stage_execution(status: HistoricalSchedulerStatus) -> dict[str, Any] | None:
    """Return a sanitized latest stage-execution summary for dashboard display."""

    latest_decision = status.latest_decision or {}
    execution_summary = latest_decision.get("execution_summary")
    if not isinstance(execution_summary, Mapping):
        return None
    stage_execution = execution_summary.get("stage_execution")
    if not isinstance(stage_execution, Mapping):
        return None
    stderr_excerpt = _failure_excerpt(stage_execution.get("stderr_path"))
    stdout_excerpt = _failure_excerpt(stage_execution.get("stdout_path")) if stderr_excerpt is None else None
    failure_detail = stderr_excerpt or stdout_excerpt or stage_execution.get("reason")
    return {
        "stage_id": stage_execution.get("stage_id"),
        "status": stage_execution.get("status"),
        "reason": stage_execution.get("reason"),
        "failure_detail": failure_detail,
        "return_code": stage_execution.get("return_code"),
        "stdout_path": stage_execution.get("stdout_path"),
        "stderr_path": stage_execution.get("stderr_path"),
        "receipt_path": stage_execution.get("receipt_path"),
        "provider_calls": int(stage_execution.get("provider_calls") or 0),
        "model_activation_performed": bool(stage_execution.get("model_activation_performed")),
        "broker_execution_performed": bool(stage_execution.get("broker_execution_performed")),
        "agent_error_request_path": stage_execution.get("agent_error_request_path"),
        "agent_error_diagnosis_path": stage_execution.get("agent_error_diagnosis_path"),
        "agent_error_number": stage_execution.get("agent_error_number"),
        "agent_error_ref": stage_execution.get("agent_error_ref"),
    }


def _is_transient_active_scheduler_backoff(status: HistoricalSchedulerStatus) -> bool:
    reason = str(status.blocked_reason or "").lower()
    return status.lock.status == "active" and "no executable scheduler-owned workflow stage" in reason


def _owner_status(status: HistoricalSchedulerStatus) -> tuple[str, str, str]:
    """Return dashboard status, severity, and short summary."""

    workflow = status.workflow_checkpoint
    latest_stage_execution = _latest_stage_execution(status)
    if latest_stage_execution and latest_stage_execution.get("status") == "failed":
        stage_id = latest_stage_execution.get("stage_id") or status.current_stage or "unknown stage"
        reason = latest_stage_execution.get("failure_detail") or latest_stage_execution.get("reason") or "latest stage execution failed"
        dashboard_status = "running_with_failure" if status.lock.status == "active" else "action_required"
        return (
            dashboard_status,
            "medium",
            f"Historical scheduler last execution failed at {stage_id}: {reason}.",
        )
    if not status.service_runtime_ready:
        return (
            "blocked",
            "high",
            "Historical modeling service is not runtime-ready; service files or lock state need review.",
        )
    if status.blocked_reason and not _is_transient_active_scheduler_backoff(status):
        return (
            "blocked",
            "medium",
            f"Historical modeling is blocked at {status.current_stage or 'unknown stage'}: {status.blocked_reason}.",
        )
    if workflow.terminal_complete:
        return (
            "complete",
            "info",
            f"Historical workflow for {status.current_month or 'the selected month'} is complete.",
        )
    if status.lock.status == "active":
        return (
            "running",
            "info",
            f"Historical scheduler is running at {status.current_stage or 'the selected stage'} for {status.current_month or 'the selected month'}.",
        )
    if status.open_operational_items:
        owner_action_required = any(_operational_item_requires_owner_action(item) for item in status.open_operational_items)
        if not owner_action_required:
            return (
                "ready",
                "info",
                f"Historical scheduler is stopped and ready to start; next action is {status.recommended_next_action}.",
            )
        return (
            "action_required",
            "medium",
            f"Historical scheduler is ready for review; next action is {status.recommended_next_action}.",
        )
    return (
        "ready",
        "info",
        f"Historical scheduler can continue at {status.current_stage or 'the next selected stage'} for {status.current_month or 'the selected month'}.",
    )


def _operational_item_requires_owner_action(item: str) -> bool:
    return item in {"review_systemd_template_flags", "remove_or_replace_stale_scheduler_lock_before_service_start"}


def _issue_refs(status: HistoricalSchedulerStatus) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    latest_stage_execution = _latest_stage_execution(status)
    if latest_stage_execution and latest_stage_execution.get("status") == "failed":
        refs.append(
            {
                "issue_type": "historical_stage_execution_failed",
                "issue_id": latest_stage_execution.get("stage_id") or "unknown_stage",
                "severity": "medium",
                "owner_action_required": False,
                "summary": latest_stage_execution.get("reason") or "latest stage execution failed",
            }
        )
    for item in status.open_operational_items:
        refs.append(
            {
                "issue_type": "historical_scheduler_operational_item",
                "issue_id": item,
                "severity": "medium",
                "owner_action_required": _operational_item_requires_owner_action(item),
            }
        )
    if status.blocked_reason and not _is_transient_active_scheduler_backoff(status):
        refs.append(
            {
                "issue_type": "historical_workflow_blocked",
                "issue_id": status.current_stage or "unknown_stage",
                "severity": "medium",
                "owner_action_required": False,
                "summary": status.blocked_reason,
            }
        )
    return refs


def _diagnostic_refs(status: HistoricalSchedulerStatus, stage_coverage: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        {"ref_type": "manager_historical_scheduler_status", "path": "scripts/tasks/inspect_historical_scheduler_status.py"}
    ]
    latest_stage_execution = _latest_stage_execution(status)
    if latest_stage_execution is not None:
        refs.append(
            {
                "ref_type": "manager_stage_execution_summary",
                "stage_id": latest_stage_execution.get("stage_id"),
                "status": latest_stage_execution.get("status"),
                "receipt_path": latest_stage_execution.get("receipt_path"),
                "stdout_path": latest_stage_execution.get("stdout_path"),
                "stderr_path": latest_stage_execution.get("stderr_path"),
                "agent_error_request_path": latest_stage_execution.get("agent_error_request_path"),
                "agent_error_diagnosis_path": latest_stage_execution.get("agent_error_diagnosis_path"),
                "agent_error_number": latest_stage_execution.get("agent_error_number"),
                "agent_error_ref": latest_stage_execution.get("agent_error_ref"),
            }
        )
        if latest_stage_execution.get("agent_error_request_path"):
            refs.append(
                {
                    "ref_type": "server_error_agent_request",
                    "stage_id": latest_stage_execution.get("stage_id"),
                    "path": latest_stage_execution.get("agent_error_request_path"),
                    "diagnosis_path": latest_stage_execution.get("agent_error_diagnosis_path"),
                    "error_number": latest_stage_execution.get("agent_error_number"),
                    "error_ref": latest_stage_execution.get("agent_error_ref"),
                }
            )
    workflow_path = status.workflow_checkpoint.path
    if status.workflow_checkpoint.exists and workflow_path:
        refs.append({"ref_type": "workflow_checkpoint", "path": workflow_path})
    if stage_coverage is not None:
        refs.append(
            {
                "ref_type": "manager_stage_coverage",
                "stage_id": stage_coverage.get("stage_id"),
                "status": stage_coverage.get("status"),
            }
        )
    return refs


def _stage_coverage_chart(stage_coverage: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if stage_coverage is None:
        return None
    return {
        "stage_id": stage_coverage.get("stage_id"),
        "status": stage_coverage.get("status"),
        "expected_count": int(stage_coverage.get("expected_count") or 0),
        "ready_count": int(stage_coverage.get("ready_count") or 0),
        "pending_count": int(stage_coverage.get("pending_count") or 0),
        "failed_count": int(stage_coverage.get("failed_count") or 0),
        "accepted_failed_count": int(stage_coverage.get("accepted_failed_count") or 0),
        "can_unlock_downstream": bool(stage_coverage.get("can_unlock_downstream")),
    }


def _public_stage_name(stage_id: object, stage_type: object) -> str:
    phase = str(stage_type or "").replace("_", " ").strip()
    if phase:
        return phase.title()
    return str(stage_id or "unknown task").replace("_", " ").replace(".", " / ").title()


def _storage_root_from_checkpoint_path(path: object) -> Path:
    candidate = _resolve_local_path(path)
    if candidate is None:
        return DEFAULT_STORAGE_ROOT
    parts = candidate.parts
    if "runtime" in parts:
        runtime_index = parts.index("runtime")
        if runtime_index > 0:
            return Path(*parts[:runtime_index])
    return DEFAULT_STORAGE_ROOT


def _selected_target_symbol_from_service_env(status: HistoricalSchedulerStatus) -> str | None:
    env_path = _resolve_local_path(status.service_env.path)
    if env_path is None or not env_path.exists():
        return None
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "TRADING_MANAGER_SELECTED_TARGET_SYMBOL":
            continue
        symbol = value.strip().strip('"').strip("'").upper()
        return symbol or None
    return None


def _planned_stage_rows(status: HistoricalSchedulerStatus, *, month: str | None = None) -> list[dict[str, Any]]:
    selected_month = month or status.current_month
    if not selected_month:
        return []
    try:
        plan = build_model_training_workflow_plan(
            start_month=selected_month,
            end_month=selected_month,
            storage_root=_storage_root_from_checkpoint_path(status.workflow_checkpoint.path),
            selected_target_symbol=_selected_target_symbol_from_service_env(status),
        )
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for layer in plan.layers:
        rows.extend(stage.summary_row() for stage in layer.stages)
    return rows


def _is_month_key(value: object) -> bool:
    text = str(value or "")
    if len(text) != 7 or text[4] != "-":
        return False
    year_text, month_text = text.split("-", 1)
    if len(year_text) != 4 or len(month_text) != 2 or not year_text.isdigit() or not month_text.isdigit():
        return False
    month_number = int(month_text)
    return 1 <= month_number <= 12


def _month_visible_by_completed_cutoff(month: object, *, max_month: str) -> bool:
    """Return whether a month-scoped dashboard task is safe to expose.

    Provider-backed historical task previews must not create or advertise work
    for the current in-progress calendar month.  The scheduler already applies
    this cutoff for normal worker selection; the dashboard read model repeats
    the guard so stale daemon state or pre-created workflow files cannot leak a
    premature Ready task such as 2026-05 before June begins.
    """

    if not _is_month_key(month):
        return True
    return str(month) <= max_month


def _completed_months(status: HistoricalSchedulerStatus, *, max_month: str) -> list[str]:
    daemon_state = status.daemon_state or {}
    raw_months = daemon_state.get("last_completed_months") if isinstance(daemon_state, Mapping) else None
    if not isinstance(raw_months, list):
        return []
    months: list[str] = []
    seen: set[str] = set()
    for raw_month in raw_months:
        month = str(raw_month or "").strip()
        if (
            month
            and month not in seen
            and month != status.current_month
            and _month_visible_by_completed_cutoff(month, max_month=max_month)
        ):
            months.append(month)
            seen.add(month)
    return months


def _stored_workflow_months(storage_root: Path, *, max_month: str) -> list[str]:
    """Return month-scoped checkpoints visible to the dashboard.

    The daemon state is a recent-progress summary, not the canonical inventory
    of every durable month checkpoint.  Tasks must not lose prior months after
    a restart or after the daemon has advanced its open-lane window.
    """

    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return []
    months: list[str] = []
    seen: set[str] = set()
    for path in sorted(runtime_root.glob("model_training_workflow_state_*.json")):
        month = path.stem.removeprefix("model_training_workflow_state_")
        if not _is_month_key(month) or not _month_visible_by_completed_cutoff(month, max_month=max_month):
            continue
        try:
            payload = _load_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        start_month = str(payload.get("start_month") or month)
        end_month = str(payload.get("end_month") or start_month)
        if start_month != end_month or start_month != month:
            continue
        stages = payload.get("stages")
        if not isinstance(stages, list) or not stages:
            continue
        if month not in seen:
            months.append(month)
            seen.add(month)
    return months


def _workflow_state_payload(storage_root: Path, month: str) -> dict[str, Any] | None:
    path = storage_root / "runtime" / f"model_training_workflow_state_{month}.json"
    try:
        return _load_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _resolve_stage_ref_path(ref: object, *, storage_root: Path) -> Path | None:
    if not isinstance(ref, str) or not ref.strip():
        return None
    candidate = Path(ref)
    if candidate.is_absolute():
        return candidate
    # Workflow state usually stores manager-local refs like
    # storage/runtime/model_training_stage_receipts/.... Resolve those against
    # the repo root inferred from the storage root so dashboard summaries can
    # inspect manager-owned receipt timing metadata without exposing raw files.
    if candidate.parts and candidate.parts[0] == "storage":
        return storage_root.parent / candidate
    return Path.cwd() / candidate


def _min_timestamp(values: list[str]) -> str | None:
    return min(values) if values else None


def _max_timestamp(values: list[str]) -> str | None:
    return max(values) if values else None


def _receipt_timestamp_candidates(path: Path) -> dict[str, list[str]]:
    try:
        payload = _load_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {"started": [], "ended": []}
    started: list[str] = []
    ended: list[str] = []
    for key in ("started_at_utc", "started_at"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            started.append(value)
    for key in ("ended_at_utc", "completed_at_utc", "completed_at", "ended_at"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            ended.append(value)
    runs = payload.get("runs")
    if isinstance(runs, list):
        for run in runs:
            if not isinstance(run, Mapping):
                continue
            for key in ("started_at_utc", "started_at"):
                value = run.get(key)
                if isinstance(value, str) and value:
                    started.append(value)
            for key in ("ended_at_utc", "completed_at_utc", "completed_at", "ended_at"):
                value = run.get(key)
                if isinstance(value, str) and value:
                    ended.append(value)
    return {"started": started, "ended": ended}


def _task_timestamp_fields(raw_stage: Mapping[str, Any], *, storage_root: Path) -> dict[str, str | None]:
    receipt_started: list[str] = []
    receipt_ended: list[str] = []
    receipt_refs = raw_stage.get("receipt_refs") or []
    if isinstance(receipt_refs, list):
        for ref in receipt_refs:
            path = _resolve_stage_ref_path(ref, storage_root=storage_root)
            if path is None or not path.exists() or path.suffix.lower() != ".json":
                continue
            candidates = _receipt_timestamp_candidates(path)
            receipt_started.extend(candidates["started"])
            receipt_ended.extend(candidates["ended"])
    status_updated = raw_stage.get("status_updated_at_utc") or raw_stage.get("status_updated_utc") or raw_stage.get("updated_utc")
    started = raw_stage.get("started_at_utc") or raw_stage.get("started_at") or _min_timestamp(receipt_started)
    ended = raw_stage.get("ended_at_utc") or raw_stage.get("completed_at_utc") or raw_stage.get("completed_at") or _max_timestamp(receipt_ended)
    created = raw_stage.get("created_at_utc") or raw_stage.get("created_utc") or raw_stage.get("created_at")
    return {
        "created_at_utc": str(created) if created else None,
        "started_at_utc": str(started) if started else None,
        "ended_at_utc": str(ended) if ended else None,
        "status_updated_at_utc": str(status_updated) if status_updated else None,
    }


def _active_month_stages(status: HistoricalSchedulerStatus, storage_root: Path) -> tuple[str | None, list[Any]]:
    checkpoint_path = _resolve_local_path(status.workflow_checkpoint.path)
    timeline_month = status.current_month
    payload: dict[str, Any] = {}
    if checkpoint_path is not None and checkpoint_path.exists():
        try:
            payload = _load_json_object(checkpoint_path)
        except (OSError, ValueError, json.JSONDecodeError):
            payload = {}
        else:
            timeline_month = str(payload.get("start_month") or status.current_month or "") or None
    elif status.current_month:
        payload = _workflow_state_payload(storage_root, status.current_month) or {}
        timeline_month = str(payload.get("start_month") or status.current_month or "") or None
    raw_stages = payload.get("stages") or _planned_stage_rows(status, month=timeline_month)
    return timeline_month, raw_stages if isinstance(raw_stages, list) else []



def _month_ingest_worker_info(month: str | None, *, worker_count: int = DEFAULT_MONTH_INGEST_WORKERS) -> dict[str, str]:
    worker_count = max(1, int(worker_count))
    if isinstance(month, str) and len(month) >= 7:
        try:
            year = int(month[:4])
            month_number = int(month[5:7])
            absolute_month = year * 12 + month_number
            base_month = 2016 * 12 + 1
            lane = ((absolute_month - base_month) % worker_count) + 1
        except ValueError:
            lane = 0
    else:
        lane = 0
    if lane <= 0:
        return {
            "worker_id": "month_ingest_worker_unassigned",
            "worker_label": "Month Ingest Worker",
            "worker_kind": "month_ingest_worker",
        }
    return {
        "worker_id": f"month_ingest_worker_{lane}",
        "worker_label": f"Month Ingest Worker {lane}",
        "worker_kind": "month_ingest_worker",
    }


def _month_ingest_worker_info_for_lane(lane: int) -> dict[str, str]:
    if lane <= 0:
        return {
            "worker_id": "month_ingest_worker_unassigned",
            "worker_label": "Month Ingest Worker",
            "worker_kind": "month_ingest_worker",
        }
    return {
        "worker_id": f"month_ingest_worker_{lane}",
        "worker_label": f"Month Ingest Worker {lane}",
        "worker_kind": "month_ingest_worker",
    }


def _model_worker_info() -> dict[str, str]:
    return {"worker_id": "model_worker_1", "worker_label": "Model Worker 1", "worker_kind": "model_worker"}


def _worker_info_for_stage(
    raw_stage: Mapping[str, Any],
    *,
    month: str | None = None,
    month_ingest_worker_count: int = DEFAULT_MONTH_INGEST_WORKERS,
) -> dict[str, str]:
    """Return the public worker assignment shown in task previews.

    This is an operator-facing pipeline lane, not a raw process/thread id.
    Month-scoped data acquisition and feature generation belong to one of the
    accepted month-ingest workers. Fold/model/promotion stages belong to
    the single model worker. Lower-level provider request thread slots remain
    visible separately in provider-dispatch detail previews.
    """

    explicit_id = raw_stage.get("worker_id") or raw_stage.get("worker_ref")
    explicit_label = raw_stage.get("worker_label")
    explicit_kind = raw_stage.get("worker_kind")
    if explicit_id or explicit_label or explicit_kind:
        worker_id = str(explicit_id or explicit_label or explicit_kind)
        worker_label = str(explicit_label or explicit_id or explicit_kind)
        worker_kind = str(explicit_kind or "explicit")
        return {"worker_id": worker_id, "worker_label": worker_label, "worker_kind": worker_kind}

    stage_type = str(raw_stage.get("stage_type") or "unknown")
    if stage_type in {"data_acquisition", "feature_generation"}:
        return _month_ingest_worker_info(month, worker_count=month_ingest_worker_count)
    if stage_type in {"model_generation", "model_evaluation", "promotion_review", "maintenance"}:
        return _model_worker_info()
    return {"worker_id": "scheduler_control_worker", "worker_label": "Scheduler Control Worker", "worker_kind": "scheduler_control"}


def _month_offset(month: str | None) -> int | None:
    if not _is_month_key(month):
        return None
    assert month is not None
    try:
        year = int(month[:4])
        month_number = int(month[5:7])
    except ValueError:
        return None
    return (year - BASE_TASK_YEAR) * 12 + (month_number - BASE_TASK_MONTH)


def _fold_start_month(period: str | None) -> str | None:
    text = str(period or "")
    if ".." not in text:
        return None
    start, _end = text.split("..", 1)
    return start if _is_month_key(start) else None


def _monthly_task_ordinal(raw_stage: Mapping[str, Any]) -> int | None:
    stage_type = str(raw_stage.get("stage_type") or "")
    if stage_type not in MONTHLY_TASK_STAGE_TYPES:
        return None
    try:
        layer = int(raw_stage.get("layer"))
    except (TypeError, ValueError):
        return None
    if layer not in MONTHLY_SUBSTRATE_LAYERS:
        return None
    type_offset = 1 if stage_type == "data_acquisition" else 2
    return (layer - 1) * 2 + type_offset


def _fold_model_task_ordinal(raw_stage: Mapping[str, Any]) -> int | None:
    stage_type = str(raw_stage.get("stage_type") or "")
    stage_offset = {
        "model_generation": 1,
        "model_evaluation": 2,
        "promotion_review": 3,
        "maintenance": 4,
    }.get(stage_type)
    if stage_offset is None:
        return None
    try:
        layer = int(raw_stage.get("layer"))
    except (TypeError, ValueError):
        return None
    if layer <= 0:
        return None
    return (layer - 1) * 4 + stage_offset


def _stable_task_number(raw_stage: Mapping[str, Any], *, task_period: str | None) -> int | None:
    """Return the stable owner-facing task number for a timeline row."""

    fold_start = _fold_start_month(task_period)
    if fold_start:
        offset = _month_offset(fold_start)
        ordinal = _fold_model_task_ordinal(raw_stage)
        if offset is None or ordinal is None:
            return None
        fold_index = max(0, offset // MONTHS_PER_MODEL_FOLD)
        return fold_index * TASKS_PER_MODEL_FOLD + MONTHLY_TASKS_PER_FOLD + ordinal
    offset = _month_offset(task_period)
    ordinal = _monthly_task_ordinal(raw_stage)
    if offset is None or ordinal is None:
        return None
    fold_index = max(0, offset // MONTHS_PER_MODEL_FOLD)
    month_index_in_fold = offset % MONTHS_PER_MODEL_FOLD
    return fold_index * TASKS_PER_MODEL_FOLD + month_index_in_fold * 6 + ordinal


def _stable_task_uid(raw_stage: Mapping[str, Any], *, task_period: str | None) -> str:
    stage_id = str(raw_stage.get("stage_id") or "unknown_stage")
    return f"{task_period or 'unscheduled'}:{stage_id}"


def _presentable_fold_stages(raw_stages: list[Any]) -> list[Any]:
    """Fold states expose only fold-scoped model-worker stages to Tasks."""

    visible: list[Any] = []
    for raw_stage in raw_stages:
        if not isinstance(raw_stage, Mapping):
            continue
        if str(raw_stage.get("stage_type") or "") in FOLD_MODEL_STAGE_TYPES:
            visible.append(raw_stage)
    return visible


def _selected_model_worker_fold_stage_set(
    status: HistoricalSchedulerStatus,
    *,
    storage_root: Path,
    max_dashboard_month: str,
    included_months: set[str],
) -> tuple[str, list[Any], bool] | None:
    selection = select_model_worker_fold(storage_root=storage_root, max_month=max_dashboard_month)
    if selection is None:
        return None
    fold_key = f"{selection.start_month}..{selection.end_month}"
    if fold_key in included_months:
        return None
    try:
        plan = build_model_training_workflow_plan(
            start_month=selection.start_month,
            end_month=selection.end_month,
            storage_root=storage_root,
            selected_target_symbol=_selected_target_symbol_from_service_env(status),
            foundation_catch_up_only=False,
        )
        foundation_stage_ids = [
            stage.stage_id
            for layer in plan.layers
            if layer.layer in MONTHLY_SUBSTRATE_LAYERS
            for stage in layer.stages
            if stage.stage_type in FOUNDATION_CATCH_UP_STAGE_TYPES
        ]
        state = advance_workflow_state(
            start_month=selection.start_month,
            end_month=selection.end_month,
            storage_root=storage_root,
            state_path=Path(selection.state_path) if selection.state_path else None,
            completed_stage_ids=foundation_stage_ids,
            selected_target_symbol=_selected_target_symbol_from_service_env(status),
            foundation_catch_up_only=False,
            write=False,
        )
    except Exception:
        return None
    rows = _presentable_fold_stages([stage.summary_row() for stage in state.stages])
    if not rows:
        return None
    return fold_key, rows, True



def _is_presentable_task_stage(raw_stage: Mapping[str, Any]) -> bool:
    stage_type = str(raw_stage.get("stage_type") or "")
    try:
        layer = int(raw_stage.get("layer"))
    except (TypeError, ValueError):
        layer = 0
    if layer in {5, 6, 7} and stage_type in {"data_acquisition", "feature_generation"}:
        return False
    return True


def _task_timeline(
    status: HistoricalSchedulerStatus,
    *,
    stage_coverage: Mapping[str, Any] | None = None,
    max_reason_chars: int = 220,
) -> list[dict[str, Any]]:
    """Return a sanitized all-stage task timeline for dashboard display.

    The dashboard should show task progress at the operational stage level
    (data acquisition, feature generation, model generation, etc.) without
    requiring the UI to read workflow checkpoint internals directly. Completed
    months remain visible as historical groups; the current month remains the
    only month allowed to expose a `current` row.
    """

    storage_root = _storage_root_from_checkpoint_path(status.workflow_checkpoint.path)
    month_ingest_worker_count = DEFAULT_MONTH_INGEST_WORKERS
    max_dashboard_month = completed_historical_month_cutoff()
    month_stage_sets: list[tuple[str | None, list[Any], bool]] = []
    included_months: set[str] = set()
    durable_months: list[str] = []
    seen_durable_months: set[str] = set()
    for month in [
        *_stored_workflow_months(storage_root, max_month=max_dashboard_month),
        *_completed_months(status, max_month=max_dashboard_month),
    ]:
        if month not in seen_durable_months:
            durable_months.append(month)
            seen_durable_months.add(month)
    for month in durable_months:
        payload = _workflow_state_payload(storage_root, month)
        if payload is None:
            continue
        raw_stages = payload.get("stages")
        if isinstance(raw_stages, list):
            month_key = str(payload.get("start_month") or month)
            month_stage_sets.append((month_key, raw_stages, False))
            included_months.add(month_key)
    lane_months = select_month_ingest_worker_months(
        storage_root=storage_root,
        default_start_month=status.current_month or status.workflow_checkpoint.start_month or "2016-01",
        worker_count=month_ingest_worker_count,
        max_month=max_dashboard_month,
    )
    lane_worker_by_month = {month: _month_ingest_worker_info_for_lane(index + 1) for index, month in enumerate(lane_months)}
    for month in lane_months:
        if month in included_months:
            continue
        payload = _workflow_state_payload(storage_root, month)
        if payload is None:
            continue
        raw_stages = payload.get("stages")
        if isinstance(raw_stages, list):
            month_key = str(payload.get("start_month") or month)
            month_stage_sets.append((month_key, raw_stages, True))
            included_months.add(month_key)
    runtime_root = storage_root / "runtime"
    if runtime_root.exists():
        for fold_path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
            try:
                fold_payload = _load_json_object(fold_path)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            raw_stages = fold_payload.get("stages")
            if not isinstance(raw_stages, list):
                continue
            raw_stages = _presentable_fold_stages(raw_stages)
            if not raw_stages:
                continue
            fold_start = str(fold_payload.get("start_month") or "")
            fold_end = str(fold_payload.get("end_month") or "")
            fold_key = f"{fold_start}..{fold_end}" if fold_start and fold_end else fold_path.stem
            if fold_end and not _month_visible_by_completed_cutoff(fold_end, max_month=max_dashboard_month):
                continue
            if fold_key in included_months:
                continue
            month_stage_sets.append((fold_key, raw_stages, True))
            included_months.add(fold_key)
    selected_fold = _selected_model_worker_fold_stage_set(
        status,
        storage_root=storage_root,
        max_dashboard_month=max_dashboard_month,
        included_months=included_months,
    )
    if selected_fold is not None:
        fold_key, raw_stages, is_active_fold = selected_fold
        month_stage_sets.append((fold_key, raw_stages, is_active_fold))
        included_months.add(fold_key)
    active_month, active_stages = _active_month_stages(status, storage_root)
    if (
        active_stages
        and active_month not in included_months
        and _month_visible_by_completed_cutoff(active_month, max_month=max_dashboard_month)
    ):
        month_stage_sets.append((active_month, active_stages, True))
    if not month_stage_sets:
        return []

    coverage_stage_id = str(stage_coverage.get("stage_id") or "") if stage_coverage else ""
    latest_execution = _latest_stage_execution(status) or {}
    latest_failed_stage = latest_execution.get("stage_id") if latest_execution.get("status") == "failed" else None
    latest_failed_month = None
    if latest_failed_stage and isinstance(status.latest_decision, Mapping):
        latest_failed_month = str(status.latest_decision.get("start_month") or "") or None
    current_lane_heads: set[tuple[str | None, str]] = set()
    current_model_heads: set[tuple[str | None, str]] = set()
    seen_ingest_workers: set[str] = set()
    for timeline_month, raw_stages, _is_active_month in month_stage_sets:
        for raw_stage in raw_stages:
            if not isinstance(raw_stage, Mapping):
                continue
            stage_id = str(raw_stage.get("stage_id") or "")
            if not stage_id or str(raw_stage.get("status") or "") in {"succeeded", "not_applicable"}:
                continue
            if not _is_presentable_task_stage(raw_stage):
                continue
            stage_type = str(raw_stage.get("stage_type") or "")
            if stage_type not in {"data_acquisition", "feature_generation"}:
                continue
            try:
                layer = int(raw_stage.get("layer"))
            except (TypeError, ValueError):
                continue
            if layer not in MONTHLY_SUBSTRATE_LAYERS:
                continue
            task_month = str(raw_stage.get("month") or raw_stage.get("start_month") or timeline_month or "") or None
            worker_info = lane_worker_by_month.get(task_month) or _worker_info_for_stage(
                raw_stage, month=task_month, month_ingest_worker_count=month_ingest_worker_count
            )
            worker_id = worker_info.get("worker_id") or ""
            if worker_info.get("worker_kind") != "month_ingest_worker" or worker_id in seen_ingest_workers:
                continue
            current_lane_heads.add((task_month, stage_id))
            seen_ingest_workers.add(worker_id)
    for timeline_month, raw_stages, _is_active_month in month_stage_sets:
        if current_model_heads:
            break
        for raw_stage in raw_stages:
            if not isinstance(raw_stage, Mapping):
                continue
            stage_id = str(raw_stage.get("stage_id") or "")
            if not stage_id or str(raw_stage.get("status") or "") != "ready":
                continue
            stage_type = str(raw_stage.get("stage_type") or "")
            if stage_type not in {"model_generation", "model_evaluation", "promotion_review", "maintenance"}:
                continue
            task_month = str(raw_stage.get("month") or raw_stage.get("start_month") or timeline_month or "") or None
            current_model_heads.add((task_month, stage_id))
            break
    tasks: list[dict[str, Any]] = []
    first_open_seen = False
    for timeline_month, raw_stages, is_active_month in month_stage_sets:
        for raw_stage in raw_stages:
            if not isinstance(raw_stage, Mapping):
                continue
            stage_id = str(raw_stage.get("stage_id") or "")
            if not stage_id or not _is_presentable_task_stage(raw_stage):
                continue
            stage_status = str(raw_stage.get("status") or "unknown")
            is_terminal = stage_status in {"succeeded", "not_applicable"}
            task_month_for_state = str(raw_stage.get("month") or raw_stage.get("start_month") or timeline_month or "") or None
            is_current = bool((task_month_for_state, stage_id) in current_lane_heads and not is_terminal)
            if not is_current:
                is_current = bool((task_month_for_state, stage_id) in current_model_heads and not is_terminal)
            if not is_current and not current_lane_heads and not current_model_heads:
                is_current = bool(
                    is_active_month and stage_id and stage_id == status.current_stage and stage_status == "ready" and not is_terminal
                )
            if not current_lane_heads and is_active_month and not first_open_seen and stage_status == "ready" and not is_terminal:
                is_current = True
                first_open_seen = True
            if latest_failed_stage and stage_id == latest_failed_stage and (
                not latest_failed_month or task_month_for_state == latest_failed_month
            ):
                task_state = "failed"
            elif is_terminal:
                task_state = "completed" if stage_status == "succeeded" else "skipped"
            elif is_current:
                task_state = "current"
            else:
                task_state = "future"
            reason = str(raw_stage.get("last_reason") or "")
            if len(reason) > max_reason_chars:
                reason = reason[: max_reason_chars - 1] + "…"
            blockers = raw_stage.get("blockers") or []
            if not isinstance(blockers, list):
                blockers = []
            receipt_refs = raw_stage.get("receipt_refs") or []
            if not isinstance(receipt_refs, list):
                receipt_refs = []
            dataset_unit = raw_stage.get("dataset_unit") if isinstance(raw_stage.get("dataset_unit"), Mapping) else None
            task_month = str(raw_stage.get("month") or raw_stage.get("start_month") or timeline_month or "") or None
            task_number = _stable_task_number(raw_stage, task_period=task_month)
            worker_info = lane_worker_by_month.get(task_month) or _worker_info_for_stage(
                raw_stage, month=task_month, month_ingest_worker_count=month_ingest_worker_count
            )
            task: dict[str, Any] = {
                "sequence": len(tasks) + 1,
                "task_number": task_number,
                "task_uid": _stable_task_uid(raw_stage, task_period=task_month),
                "month": task_month,
                "task_id": stage_id,
                "task_label": _public_stage_name(stage_id, raw_stage.get("stage_type")),
                "task_state": task_state,
                "status": stage_status,
                "stage_type": raw_stage.get("stage_type"),
                "layer": raw_stage.get("layer"),
                "layer_key": raw_stage.get("layer_key"),
                "dataset_unit_kind": dataset_unit.get("unit_kind") if dataset_unit else None,
                "dataset_unit_months": dataset_unit.get("unit_months") if dataset_unit else None,
                "target_symbol": dataset_unit.get("target_symbol") if dataset_unit else None,
                "target_required": dataset_unit.get("target_required") if dataset_unit else None,
                **worker_info,
                "updated_at_utc": raw_stage.get("updated_utc"),
                **_task_timestamp_fields(raw_stage, storage_root=storage_root),
                "reason": reason or None,
                "receipt_count": len(receipt_refs),
                "blocker_count": len(blockers),
                "detail": {
                    "blockers": [str(blocker) for blocker in blockers],
                    "receipt_refs": [str(ref) for ref in receipt_refs],
                    "safe_without_provider_calls": raw_stage.get("safe_without_provider_calls"),
                    "provider_calls_allowed": raw_stage.get("provider_calls_allowed"),
                    "model_activation_allowed": raw_stage.get("model_activation_allowed"),
                    "broker_execution_allowed": raw_stage.get("broker_execution_allowed"),
                    "dataset_unit": dataset_unit,
                    "worker": worker_info,
                },
            }
            if (
                coverage_stage_id
                and stage_id == coverage_stage_id
                and stage_coverage is not None
                and (not status.current_month or task_month == status.current_month)
            ):
                task["detail"]["progress"] = _stage_coverage_chart(stage_coverage)
            if latest_execution.get("stage_id") == stage_id and (
                not latest_failed_month or task_month == latest_failed_month
            ):
                task["detail"]["last_execution"] = {
                    "status": latest_execution.get("status"),
                    "return_code": latest_execution.get("return_code"),
                    "reason": latest_execution.get("failure_detail") or latest_execution.get("reason"),
                }
            tasks.append(task)
    return tasks


def build_historical_task_progress_summary(
    status: HistoricalSchedulerStatus,
    *,
    stage_coverage: Mapping[str, Any] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build `historical_task_progress_summary` for storage materialization."""

    generated_at_utc = generated_at_utc or now_utc()
    stage_counts = _stage_counts(status)
    task_timeline = _task_timeline(status, stage_coverage=stage_coverage)
    storage_root = _storage_root_from_checkpoint_path(status.workflow_checkpoint.path)
    agent_error_summary = _agent_error_summary(storage_root)
    if not stage_counts and task_timeline:
        for task in task_timeline:
            task_status = str(task.get("status") or "unknown")
            stage_counts[task_status] = stage_counts.get(task_status, 0) + 1
        stage_counts = dict(sorted(stage_counts.items()))
    progress_percent = _progress_percent(stage_counts)
    dashboard_status, severity, summary = _owner_status(status)
    active_blocker = status.blocked_reason or (status.open_operational_items[0] if status.open_operational_items else None)
    chart_payload: dict[str, Any] = {
        "current_month": status.current_month,
        "active_stage": status.current_stage,
        "progress_percent": progress_percent,
        "stage_counts": stage_counts,
        "terminal_complete": status.workflow_checkpoint.terminal_complete,
        "service_runtime_ready": status.service_runtime_ready,
        "lock_status": status.lock.status,
        "provider_status": status.provider_status.get("status"),
        "next_expected_system_action": status.recommended_next_action,
        "blocker_category": active_blocker,
        "task_timeline": task_timeline,
        "agent_error_summary": agent_error_summary,
    }
    latest_stage_execution = _latest_stage_execution(status)
    if latest_stage_execution is not None:
        chart_payload["last_stage_execution"] = latest_stage_execution
    coverage_chart = _stage_coverage_chart(stage_coverage)
    if coverage_chart is not None:
        chart_payload["stage_coverage"] = coverage_chart
    return {
        "contract_type": HISTORICAL_TASK_PROGRESS_CONTRACT,
        "schema_version": 1,
        "generated_at_utc": generated_at_utc,
        "source_system": "trading-manager",
        "status": dashboard_status,
        "severity": severity,
        "summary": summary,
        "chart_payload": chart_payload,
        "profile_refs": [
            {"registry_ref": "HISTORICAL_TASK_PROGRESS_SUMMARY", "field": "contract_type"},
            {"registry_ref": "DASHBOARD_READ_MODEL_COMMON_ENVELOPE", "field": "common_envelope"},
        ],
        "issue_refs": _issue_refs(status),
        "diagnostic_refs": _diagnostic_refs(status, stage_coverage),
        "lineage_refs": [
            {"contract_type": status.contract_type, "generated_utc": status.generated_utc},
            {"contract_type": "manager_stage_coverage", "included": stage_coverage is not None},
        ],
        "freshness": {
            "class": "runtime_status_snapshot",
            "status": "fresh",
            "stale_after_seconds": DEFAULT_STALE_AFTER_SECONDS,
        },
        "schema_ref": HISTORICAL_TASK_PROGRESS_SCHEMA_REF,
    }


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def write_historical_task_progress_summary(payload: Mapping[str, Any], *, output: TextIO) -> None:
    json.dump(dict(payload), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build historical_task_progress_summary dashboard payload from read-only manager scheduler status."
    )
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--lock-path", type=Path, default=DEFAULT_LOCK_PATH)
    parser.add_argument("--decision-log-path", type=Path, default=DEFAULT_DECISION_LOG_PATH)
    parser.add_argument("--service-template-path", type=Path, default=DEFAULT_SERVICE_TEMPLATE_PATH)
    parser.add_argument("--service-env-path", type=Path, default=DEFAULT_SERVICE_ENV_PATH)
    parser.add_argument("--daemon-wrapper-path", type=Path, default=DEFAULT_DAEMON_WRAPPER_PATH)
    parser.add_argument("--stage-coverage-path", type=Path, help="Optional manager_stage_coverage JSON artifact to summarize.")
    args = parser.parse_args(argv)

    status = collect_historical_scheduler_status(
        storage_root=args.storage_root,
        state_path=args.state_path,
        lock_path=args.lock_path,
        decision_log_path=args.decision_log_path,
        service_template_path=args.service_template_path,
        service_env_path=args.service_env_path,
        daemon_wrapper_path=args.daemon_wrapper_path,
    )
    stage_coverage = _load_json_object(args.stage_coverage_path) if args.stage_coverage_path else None
    payload = build_historical_task_progress_summary(status, stage_coverage=stage_coverage)
    write_historical_task_progress_summary(payload, output=sys.stdout)
    return 0


__all__ = [
    "HISTORICAL_TASK_PROGRESS_CONTRACT",
    "build_historical_task_progress_summary",
    "write_historical_task_progress_summary",
]

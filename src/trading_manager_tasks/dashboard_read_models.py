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

from .model_training_workflow import build_model_training_workflow_plan
from .request_payloads import DEFAULT_STORAGE_ROOT
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

HISTORICAL_TASK_PROGRESS_CONTRACT = "historical_task_progress_summary"
HISTORICAL_TASK_PROGRESS_SCHEMA_REF = f"storage/dashboard/schemas/{HISTORICAL_TASK_PROGRESS_CONTRACT}.schema.json"
DEFAULT_STALE_AFTER_SECONDS = 900


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
    if status.blocked_reason:
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
                "owner_action_required": item in {"review_systemd_template_flags", "remove_or_replace_stale_scheduler_lock_before_service_start"},
            }
        )
    if status.blocked_reason:
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


def _planned_stage_rows(status: HistoricalSchedulerStatus) -> list[dict[str, Any]]:
    if not status.current_month:
        return []
    try:
        plan = build_model_training_workflow_plan(
            start_month=status.current_month,
            end_month=status.current_month,
            storage_root=_storage_root_from_checkpoint_path(status.workflow_checkpoint.path),
        )
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for layer in plan.layers:
        rows.extend(stage.summary_row() for stage in layer.stages)
    return rows


def _task_timeline(
    status: HistoricalSchedulerStatus,
    *,
    stage_coverage: Mapping[str, Any] | None = None,
    max_reason_chars: int = 220,
) -> list[dict[str, Any]]:
    """Return a sanitized all-stage task timeline for dashboard display.

    The dashboard should show task progress at the operational stage level
    (data acquisition, feature generation, model generation, etc.) without
    requiring the UI to read workflow checkpoint internals directly.
    """

    checkpoint_path = _resolve_local_path(status.workflow_checkpoint.path)
    timeline_month = status.current_month
    if checkpoint_path is None or not checkpoint_path.exists():
        raw_stages = _planned_stage_rows(status)
    else:
        try:
            payload = _load_json_object(checkpoint_path)
        except (OSError, ValueError, json.JSONDecodeError):
            payload = {}
        else:
            timeline_month = str(payload.get("start_month") or status.current_month or "") or None
        raw_stages = payload.get("stages") or _planned_stage_rows(status)
    if not isinstance(raw_stages, list):
        return []
    coverage_stage_id = str(stage_coverage.get("stage_id") or "") if stage_coverage else ""
    latest_execution = _latest_stage_execution(status) or {}
    latest_failed_stage = latest_execution.get("stage_id") if latest_execution.get("status") == "failed" else None
    tasks: list[dict[str, Any]] = []
    first_open_seen = False
    for index, raw_stage in enumerate(raw_stages, start=1):
        if not isinstance(raw_stage, Mapping):
            continue
        stage_id = str(raw_stage.get("stage_id") or "")
        stage_status = str(raw_stage.get("status") or "unknown")
        is_terminal = stage_status in {"succeeded", "not_applicable"}
        is_current = bool(stage_id and stage_id == status.current_stage and not is_terminal)
        if not first_open_seen and not is_terminal:
            is_current = True
            first_open_seen = True
        if latest_failed_stage and stage_id == latest_failed_stage:
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
        task: dict[str, Any] = {
            "sequence": index,
            "month": raw_stage.get("month") or raw_stage.get("start_month") or timeline_month,
            "task_id": stage_id,
            "task_label": _public_stage_name(stage_id, raw_stage.get("stage_type")),
            "task_state": task_state,
            "status": stage_status,
            "stage_type": raw_stage.get("stage_type"),
            "layer": raw_stage.get("layer"),
            "layer_key": raw_stage.get("layer_key"),
            "updated_at_utc": raw_stage.get("updated_utc"),
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
            },
        }
        if coverage_stage_id and stage_id == coverage_stage_id and stage_coverage is not None:
            task["detail"]["progress"] = _stage_coverage_chart(stage_coverage)
        if latest_execution.get("stage_id") == stage_id:
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

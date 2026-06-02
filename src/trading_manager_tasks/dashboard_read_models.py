"""Dashboard summary/read-model producers owned by trading-manager.

These helpers build owner-facing semantic summary payloads for the accepted
storage-hosted dashboard read-model contracts.  They do not write the storage
layout themselves, call providers, activate models, submit broker orders, or
mutate account state.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .model_training_state import advance_workflow_state
from .model_training_workflow import (
    FOUNDATION_CATCH_UP_STAGE_TYPES,
    LAYER_METADATA,
    MONTHLY_SUBSTRATE_LAYERS,
    ROLLING_FOLD_SPLIT_MONTHS,
    base_stack_model_generation_splits_complete,
    build_model_training_workflow_plan,
)
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler_daemon import (
    DEFAULT_MONTH_INGEST_WORKERS,
    DEFAULT_TARGET_QUEUE_PATH,
    completed_historical_month_cutoff,
    select_model_worker_fold,
    select_month_ingest_worker_months,
)
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
from .agent_error_handler import DEFAULT_ERROR_CATALOG_NAME, fetch_server_error_catalog_rows
from .task_progress import load_active_task_progress, progress_contract_for_stage

HISTORICAL_TASK_PROGRESS_CONTRACT = "historical_task_progress_summary"
HISTORICAL_TASK_PROGRESS_SCHEMA_REF = f"storage/06_dashboard_cache/schemas/{HISTORICAL_TASK_PROGRESS_CONTRACT}.schema.json"
DEFAULT_STALE_AFTER_SECONDS = 900
MONTHLY_TASK_STAGE_TYPES = {"data_acquisition", "feature_generation"}
FOLD_MODEL_STAGE_TYPES = {
    "model_task",
    "model_training",
    "model_generation",
    "replay",
    "model_10_event_risk_governor",
    "model_evaluation",
    "post_replay_attribution",
    "promotion_review",
    "maintenance",
}
MONTHS_PER_MODEL_FOLD = 6
MODEL_GENERATION_SPLIT_MONTH_COUNT = sum(months for _name, months in ROLLING_FOLD_SPLIT_MONTHS)
MODEL_GROUP_EVALUATION_TESTS = (
    "replay_metrics",
    "guardrail_checks",
    "incumbent_comparison",
    "layer_10_attribution",
)
MODEL_GROUP_PROMOTION_TESTS = (
    "fixed_benchmark",
    "blinded_comparison",
    "uncertainty_review",
    "shadow_readiness",
    "blocking_issue_review",
)
MODEL_GROUP_MAINTENANCE_DATA_KINDS = (
    "promotion_eligibility_decision",
    "promotion_evaluation_review",
    "promotion_readiness_record",
    "activation_guardrails",
)
CRYPTO_REPLAY_TARGET_REFS = {"BTC", "ETH", "SOL"}
BASE_TASK_YEAR = 2016
BASE_TASK_MONTH = 1
MAX_AGENT_ERROR_SUMMARY_ROWS = 50
STAGE_FAILURE_RE = re.compile(r"stage\s+([A-Za-z0-9_.-]+)\s+command", re.IGNORECASE)
FOLD_LABEL_RE = re.compile(r"^(\d{4})-fold([1-9]\d*)$")
TASK_STAGE_SORT_ORDER = {
    "data_acquisition": 10,
    "feature_generation": 20,
    "model_training": 28,
    "model_task": 30,
    "model_generation": 30,
    "replay": 40,
    "post_replay_attribution": 45,
    "model_10_event_risk_governor": 45,
    "model_evaluation": 48,
    "promotion_review_preparation": 45,
    "promotion_review": 50,
    "maintenance": 60,
}


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
        return _agent_result_payload_from_text(stdout)
    if not isinstance(outer, Mapping):
        return {}
    if outer.get("diagnosis_status") or outer.get("repair"):
        return dict(outer)
    result = outer.get("result")
    if not isinstance(result, Mapping):
        return {}
    meta = result.get("meta")
    if isinstance(meta, Mapping):
        final_text = meta.get("finalAssistantRawText") or meta.get("finalAssistantVisibleText")
        if isinstance(final_text, str) and final_text.strip():
            try:
                parsed = json.loads(final_text)
            except json.JSONDecodeError:
                return {"agent_text": final_text}
            return parsed if isinstance(parsed, dict) else {"agent_text": final_text}
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


def _agent_result_payload_from_text(text: str) -> dict[str, Any]:
    """Best-effort parse for truncated OpenClaw stdout envelopes.

    Some runner receipts cap stdout and can drop the opening bytes of the JSON
    envelope while preserving the embedded finalAssistantRawText string. The
    embedded report is still the durable diagnosis content, so recover it when
    the string literal is intact.
    """

    for key in ("finalAssistantRawText", "finalAssistantVisibleText"):
        marker = f'"{key}"'
        marker_index = text.find(marker)
        if marker_index < 0:
            continue
        colon_index = text.find(":", marker_index + len(marker))
        if colon_index < 0:
            continue
        quote_index = text.find('"', colon_index + 1)
        if quote_index < 0:
            continue
        try:
            decoded_text, _ = json.JSONDecoder().raw_decode(text[quote_index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(decoded_text, str) or not decoded_text.strip():
            continue
        try:
            parsed = json.loads(decoded_text)
        except json.JSONDecodeError:
            return {"agent_text": decoded_text}
        return parsed if isinstance(parsed, dict) else {"agent_text": decoded_text}
    return {}


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
    if (
        agent_status
        in {
            "repaired",
            "resolved",
            "fixed",
            "repair_verified",
            "repaired_verified",
            "repaired_awaiting_retry",
            "repaired_with_blockers",
        }
        or nested_repair_status == "repaired"
        or verification_exit_code == 0
    ):
        return "repaired"
    if agent_status == "superseded" or nested_repair_status == "superseded":
        return "superseded"
    if agent_status in {"blocked_gate", "blocked_boundary"}:
        return "blocked"
    if nested_repair_status in {"not_supported", "blocked", "failed"}:
        return nested_repair_status
    if agent_status in {"no_action_needed", "not_needed", "not_reproducible"}:
        return "no_action_needed"
    if agent_payload.get("repair_attempted") is True:
        return "repair_attempted"
    if diagnosis_status == "completed":
        return "diagnosed"
    return "unknown"


def _agent_payload_text(value: object, fallback: object = None) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or _agent_payload_text(fallback)
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        for key in ("summary", "message", "reason", "detail", "description", "root_cause"):
            text = _agent_payload_text(value.get(key))
            if text:
                return text
    if isinstance(value, list):
        parts = [_agent_payload_text(item) for item in value]
        text_parts = [part for part in parts if part]
        if text_parts:
            return " · ".join(text_parts)
    if fallback is not None:
        return _agent_payload_text(fallback)
    return None


def _agent_error_handling_status(
    catalog_row: Mapping[str, Any],
    repair_status: str,
    agent_payload: Mapping[str, Any] | None = None,
) -> str:
    if repair_status == "superseded":
        return "closed"
    if repair_status == "repaired":
        payload = agent_payload or {}
        retry_recommendation = str(payload.get("retry_recommendation") or "").lower()
        blockers = payload.get("blockers")
        if retry_recommendation in {"do_not_retry", "no_retry", "not_applicable"} or retry_recommendation.startswith(
            "do not retry"
        ):
            return "closed"
        if retry_recommendation == "manual_review" and isinstance(blockers, list) and blockers:
            return "closed"
        scope = str(catalog_row.get("error_scope") or "")
        component = str(catalog_row.get("source_component") or "")
        if "model_training_stage" in scope or component == "trading-manager.stage_executor":
            return "awaiting_retry"
        return "closed"
    if repair_status == "no_action_needed":
        return "no_action_required"
    return "open"


def _stage_id_from_error_row(row: Mapping[str, Any]) -> str | None:
    for field in ("summary", "error_scope"):
        text = str(row.get(field) or "")
        match = STAGE_FAILURE_RE.search(text)
        if match:
            return match.group(1)
    return None


def _successful_retry_receipt(storage_root: Path, stage_id: str) -> dict[str, Any] | None:
    receipt_dir = storage_root / "runtime" / "model_training_stage_receipts" / stage_id.replace(".", "__")
    if not receipt_dir.exists():
        return None
    for path in sorted(receipt_dir.glob("*.json"), reverse=True):
        try:
            receipt = _load_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if str(receipt.get("status") or "").lower() != "succeeded":
            continue
        runs = receipt.get("runs")
        if isinstance(runs, list) and runs:
            if not any(isinstance(run, Mapping) and str(run.get("status") or "").lower() == "succeeded" for run in runs):
                continue
        completed_at = receipt.get("completed_at") or receipt.get("completed_at_utc") or receipt.get("updated_utc")
        return {"path": str(path), "completed_at_utc": completed_at}
    return None


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


def _agent_error_summary(
    storage_root: Path,
    *,
    limit: int = MAX_AGENT_ERROR_SUMMARY_ROWS,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    catalog_path = _agent_error_catalog_path(storage_root)
    if catalog_path.exists() and not database_url:
        rows = _load_jsonl_objects(catalog_path)
    elif database_url or storage_root == DEFAULT_STORAGE_ROOT:
        try:
            rows = fetch_server_error_catalog_rows(database_url=database_url, limit=limit)
        except Exception:
            rows = _load_jsonl_objects(catalog_path)
    else:
        rows = []
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
        retry_receipt = None
        stage_id = _stage_id_from_error_row(row)
        if stage_id:
            retry_receipt = _successful_retry_receipt(storage_root, stage_id)
            if retry_receipt and repair_status not in {"superseded", "no_action_needed"}:
                repair_status = "repaired"
        handling_status = _agent_error_handling_status(row, repair_status, agent_payload)
        if retry_receipt and repair_status == "repaired":
            handling_status = "closed"
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
                "runner_command": diagnosis.get("runner_command"),
                "discord_notification": diagnosis.get("discord_notification"),
                "repair_status": repair_status,
                "handling_status": handling_status,
                "retry_recommendation": (
                    f"retry completed successfully at {retry_receipt.get('completed_at_utc') or 'recorded receipt'}"
                    if retry_receipt
                    else _agent_payload_text(agent_payload.get("retry_recommendation"))
                ),
                "root_cause": _agent_payload_text(agent_payload.get("root_cause"), row.get("summary")),
                "files_changed": files_changed,
                "retry_receipt": retry_receipt,
                "request_path": row.get("request_path"),
                "diagnosis_path": row.get("diagnosis_path"),
            }
        )
    return summary_rows


def _mark_superseded_agent_errors(agent_errors: list[dict[str, Any]], task_timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_task_ids = {str(task.get("task_id") or "") for task in task_timeline}
    has_current_layer_ten_event_risk = any(
        task_id == "layer_10_event_risk_governor" or task_id.startswith("layer_10_event_risk_governor.")
        for task_id in current_task_ids
    )
    if not has_current_layer_ten_event_risk:
        return agent_errors
    updated_rows: list[dict[str, Any]] = []
    for row in agent_errors:
        text = " ".join(str(row.get(field) or "") for field in ("summary", "root_cause", "retry_recommendation"))
        if "layer_09_event_risk_governor" in text and "layer_09_event_risk_governor.data_acquisition" not in current_task_ids:
            updated = dict(row)
            updated["repair_status"] = "superseded"
            updated["handling_status"] = "closed"
            updated["dashboard_severity"] = "notice"
            updated["retry_recommendation"] = (
                "Superseded by layer_10_event_risk_governor. "
                "Prepare fold-scoped Layer 4 event-observation artifacts before replay; Layer 10 starts after replay for attribution."
            )
            updated_rows.append(updated)
        else:
            updated_rows.append(row)
    return updated_rows


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


def _public_active_task(status: HistoricalSchedulerStatus, task_timeline: list[dict[str, Any]]) -> dict[str, Any] | None:
    current_tasks: list[dict[str, Any]] = []
    for task in task_timeline:
        if str(task.get("task_state") or "") == "current":
            current_tasks.append(task)
    internal_stage = str(status.current_stage or "")
    if status.lock.status == "active":
        for task in current_tasks:
            if str(task.get("layer_key") or "") == "model_group":
                return task
    if status.lock.status == "active" and internal_stage:
        for task in current_tasks:
            if str(task.get("task_id") or "") == internal_stage:
                return task
    if status.lock.status == "active":
        for task in current_tasks:
            if str(task.get("layer_key") or "") != "model_group":
                return task
    for task in current_tasks:
        if str(task.get("layer_key") or "") == "model_group":
            return task
    ready_tasks: list[dict[str, Any]] = []
    for task in task_timeline:
        if str(task.get("status") or "") == "ready":
            ready_tasks.append(task)
    if status.lock.status == "active" and ready_tasks:
        for task in ready_tasks:
            if str(task.get("layer_key") or "") != "model_group":
                return task
        return ready_tasks[0]
    review_tasks: list[dict[str, Any]] = []
    for task in task_timeline:
        task_status = str(task.get("status") or "").lower()
        progress = task.get("detail", {}).get("progress", {}) if isinstance(task.get("detail"), Mapping) else {}
        if task_status == "review_required" and progress.get("can_unlock_downstream") is False:
            review_tasks.append(task)
    if review_tasks:
        for task in review_tasks:
            if str(task.get("layer_key") or "") == "model_group":
                return task
        return review_tasks[0]
    return None


def _public_active_task_summary(task: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if task is None:
        return None
    return {
        "task_id": task.get("task_id"),
        "task_label": task.get("task_label"),
        "month": task.get("month"),
        "status": task.get("status"),
        "task_state": task.get("task_state"),
        "stage_type": task.get("stage_type"),
        "layer": task.get("layer"),
        "layer_key": task.get("layer_key"),
        "worker_id": task.get("worker_id"),
        "worker_label": task.get("worker_label"),
        "worker_kind": task.get("worker_kind"),
        "target_symbol": task.get("target_symbol"),
    }


def _public_current_period(status: HistoricalSchedulerStatus, public_active_task: Mapping[str, Any] | None) -> str | None:
    if public_active_task is not None:
        value = public_active_task.get("month")
        return str(value) if value else None
    candidate = _public_task_period(status.current_month)
    if candidate and _public_period_visible_by_completed_cutoff(candidate, max_month=completed_historical_month_cutoff()):
        return candidate
    return None


def _owner_status(
    status: HistoricalSchedulerStatus,
    *,
    public_active_task: Mapping[str, Any] | None = None,
) -> tuple[str, str, str]:
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
    if public_active_task is not None:
        label = str(public_active_task.get("task_label") or public_active_task.get("task_id") or "the current task")
        period = str(public_active_task.get("month") or "the selected period")
        task_status = str(public_active_task.get("status") or "").lower()
        if task_status == "blocked":
            return (
                "blocked",
                "medium",
                f"Historical workflow is blocked at {label} for {period}.",
            )
        if task_status == "review_required":
            return (
                "action_required",
                "medium",
                f"Historical workflow requires review at {label} for {period}.",
            )
        if status.lock.status == "active":
            return (
                "running",
                "info",
                f"Historical scheduler is running; current public task is {label} for {period}.",
            )
        return (
            "ready",
            "info",
            f"Historical workflow is ready at {label} for {period}.",
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


def _public_active_task_blocker(public_active_task: Mapping[str, Any] | None) -> str | None:
    if public_active_task is None:
        return None
    if str(public_active_task.get("status") or "").lower() not in {"blocked", "review_required"}:
        return None
    detail = public_active_task.get("detail")
    if isinstance(detail, Mapping):
        blockers = detail.get("blockers")
        if isinstance(blockers, list) and blockers:
            return str(blockers[0])
    return str(public_active_task.get("task_id") or "current_task_blocked")


def _active_blocker(status: HistoricalSchedulerStatus, public_active_task: Mapping[str, Any] | None) -> str | None:
    if public_active_task is not None:
        return _public_active_task_blocker(public_active_task)
    return status.blocked_reason or (status.open_operational_items[0] if status.open_operational_items else None)


def _issue_refs(status: HistoricalSchedulerStatus, public_active_task: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
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
    public_task_blocker = _public_active_task_blocker(public_active_task)
    if public_task_blocker is not None:
        refs.append(
            {
                "issue_type": "historical_workflow_blocked",
                "issue_id": public_active_task.get("task_id") or "current_public_task",
                "severity": "medium",
                "owner_action_required": False,
                "summary": public_task_blocker,
            }
        )
    elif public_active_task is None and status.blocked_reason and not _is_transient_active_scheduler_backoff(status):
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
        "unit_label": stage_coverage.get("unit_label") or "source-month requests",
        "expected_count": int(stage_coverage.get("expected_count") or 0),
        "ready_count": int(stage_coverage.get("ready_count") or 0),
        "pending_count": int(stage_coverage.get("pending_count") or 0),
        "failed_count": int(stage_coverage.get("failed_count") or 0),
        "accepted_failed_count": int(stage_coverage.get("accepted_failed_count") or 0),
        "can_unlock_downstream": bool(stage_coverage.get("can_unlock_downstream")),
        "progress_source": stage_coverage.get("progress_source") or "stage_coverage",
        "progress_basis": stage_coverage.get("progress_basis"),
    }


def _fold_stage_coverage_progress(
    *,
    storage_root: Path,
    stage_id: str | None,
    task_period: str | None,
) -> dict[str, Any] | None:
    if not stage_id or not task_period:
        return None
    months = _child_partitions_for_period(task_period)
    if not months:
        return None
    coverage_root = storage_root / "runtime" / "stage_coverage"
    if not coverage_root.exists():
        return None
    rows: list[dict[str, Any]] = []
    for path in sorted(coverage_root.glob("*.json")):
        payload = _load_optional_json_object(path)
        if payload is None:
            continue
        if str(payload.get("stage_id") or "") != stage_id:
            continue
        month = str(payload.get("start_month") or "")
        if month not in months:
            continue
        rows.append(payload)
    if not rows:
        return None
    expected = sum(int(row.get("expected_count") or 0) for row in rows)
    ready = sum(int(row.get("ready_count") or 0) for row in rows)
    failed = sum(int(row.get("failed_count") or 0) for row in rows)
    accepted_failed = sum(int(row.get("accepted_failed_count") or 0) for row in rows)
    pending = sum(int(row.get("pending_count") or 0) for row in rows)
    complete = expected > 0 and ready + accepted_failed >= expected and failed == accepted_failed
    return {
        "stage_id": stage_id,
        "status": "complete" if complete else ("partial_ready" if ready or accepted_failed or failed else "pending"),
        "unit_label": "source-month requests",
        "expected_count": expected,
        "ready_count": min(ready + accepted_failed, expected),
        "pending_count": max(pending, expected - min(ready + accepted_failed + failed, expected)),
        "failed_count": failed,
        "accepted_failed_count": accepted_failed,
        "can_unlock_downstream": complete,
        "progress_source": "fold_stage_coverage",
        "progress_basis": "download/source partitions required by the six-month fold",
        "covered_partition_count": len(rows),
        "expected_partition_count": len(months),
    }


def _fold_month_partition_progress(
    *,
    stage_id: str,
    stage_status: str,
    task_period: str | None,
    unit_label: str,
    progress_source: str,
    progress_basis: str,
) -> dict[str, Any] | None:
    months = _child_partitions_for_period(task_period)
    if not months:
        return None
    status = str(stage_status or "").lower()
    complete = status in {"succeeded", "not_applicable"}
    failed = 1 if status == "failed" else 0
    expected = len(months)
    ready = expected if complete else 0
    return {
        "stage_id": stage_id,
        "status": "complete" if complete else ("failed" if failed else status or "pending"),
        "unit_label": unit_label,
        "expected_count": expected,
        "ready_count": ready,
        "pending_count": max(expected - ready - failed, 0),
        "failed_count": failed,
        "accepted_failed_count": 0,
        "can_unlock_downstream": complete,
        "progress_source": progress_source,
        "progress_basis": progress_basis,
        "covered_partition_count": ready,
        "expected_partition_count": expected,
    }


def _semantic_stage_progress(
    *,
    stage_id: str,
    stage_type: str,
    stage_status: str,
    task_period: str | None,
) -> dict[str, Any] | None:
    if stage_type == "data_acquisition":
        contract = progress_contract_for_stage(f"{stage_id}.data_acquisition")
        return _fold_month_partition_progress(
            stage_id=stage_id,
            stage_status=stage_status,
            task_period=task_period,
            unit_label=contract["unit_label"],
            progress_source="fold_data_acquisition_partitions",
            progress_basis=contract["progress_basis"],
        )
    if stage_type == "feature_generation":
        contract = progress_contract_for_stage(f"{stage_id}.feature_generation")
        return _fold_month_partition_progress(
            stage_id=stage_id,
            stage_status=stage_status,
            task_period=task_period,
            unit_label=contract["unit_label"],
            progress_source="fold_feature_generation_partitions",
            progress_basis=contract["progress_basis"],
        )
    if stage_type == "model_generation":
        return None
    return None


def _task_status_progress(stage_id: str, stage_status: str) -> dict[str, Any]:
    status = str(stage_status or "unknown").lower()
    if status in {"succeeded", "not_applicable"}:
        return {
            "stage_id": stage_id,
            "status": "complete",
            "unit_label": "task",
            "expected_count": 1,
            "ready_count": 1,
            "pending_count": 0,
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": True,
            "progress_source": "stage_status",
        }
    if status == "failed":
        return {
            "stage_id": stage_id,
            "status": "failed",
            "unit_label": "task",
            "expected_count": 1,
            "ready_count": 0,
            "pending_count": 0,
            "failed_count": 1,
            "accepted_failed_count": 0,
            "can_unlock_downstream": False,
            "progress_source": "stage_status",
        }
    if status == "running":
        return {
            "stage_id": stage_id,
            "status": "running",
            "unit_label": "task",
            "expected_count": 1,
            "ready_count": 0,
            "pending_count": 1,
            "failed_count": 0,
            "accepted_failed_count": 0,
            "can_unlock_downstream": False,
            "progress_source": "stage_status",
        }
    progress_status = status if status in {"ready", "blocked", "pending"} else "unknown"
    return {
        "stage_id": stage_id,
        "status": progress_status,
        "unit_label": "task",
        "expected_count": 1,
        "ready_count": 0,
        "pending_count": 1,
        "failed_count": 0,
        "accepted_failed_count": 0,
        "can_unlock_downstream": False,
        "progress_source": "stage_status",
    }


def _public_stage_name(stage_id: object, stage_type: object) -> str:
    stage_id_text = str(stage_id or "")
    if stage_id_text.startswith("layer_") and stage_type == "model_evaluation":
        return "Local Layer Evaluation"
    phase = str(stage_type or "").replace("_", " ").strip()
    if phase:
        return phase.title()
    return stage_id_text.replace("_", " ").replace(".", " / ").title() or "Unknown Task"


MODEL_NAME_BY_LAYER_KEY = {
    f"layer_{int(meta['layer']):02d}_{meta['slug']}": str(meta["model_name"])
    for meta in LAYER_METADATA
}
MODEL_NAME_BY_LAYER_KEY["layer_10_event_risk_governor"] = "EventRiskGovernor"


def _spaced_model_name(model_name: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", model_name)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    return spaced.replace(" / ", " / ")


def _model_task_label(layer_key: str, layer: int | None = None) -> str:
    model_name = MODEL_NAME_BY_LAYER_KEY.get(layer_key)
    if model_name:
        model_label = _spaced_model_name(model_name)
        if layer is not None:
            return f"Layer {layer} {model_label}"
        return model_label
    if layer == 10:
        return "Layer 10 Event Risk Governor"
    return layer_key.replace("_", " ").title()


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


def _selected_target_symbol_from_latest_decision(status: HistoricalSchedulerStatus) -> str | None:
    latest_decision = status.latest_decision or {}
    if not isinstance(latest_decision, Mapping):
        return None
    symbol = str(latest_decision.get("selected_target_symbol") or "").strip().upper()
    if symbol:
        return symbol
    execution_summary = latest_decision.get("execution_summary")
    workflow_plan = execution_summary.get("workflow_plan") if isinstance(execution_summary, Mapping) else None
    if isinstance(workflow_plan, Mapping):
        symbol = str(workflow_plan.get("selected_target_symbol") or "").strip().upper()
    return symbol or None


def _selected_target_symbol(status: HistoricalSchedulerStatus) -> str | None:
    return _selected_target_symbol_from_latest_decision(status) or _selected_target_symbol_from_service_env(status)


def _planned_stage_rows(status: HistoricalSchedulerStatus, *, month: str | None = None) -> list[dict[str, Any]]:
    selected_month = month or status.current_month
    if not selected_month:
        return []
    try:
        plan = build_model_training_workflow_plan(
            start_month=selected_month,
            end_month=selected_month,
            storage_root=_storage_root_from_checkpoint_path(status.workflow_checkpoint.path),
            selected_target_symbol=_selected_target_symbol(status),
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


def _has_control_plane_month_task_keys(storage_root: Path, month: str) -> bool:
    """Return whether a missing workflow month has prepared control-plane work."""

    monthly_root = storage_root / "monthly_backfill"
    if not monthly_root.exists():
        return False
    return any(month_dir.is_dir() and (month_dir / "task_key.json").exists() for month_dir in monthly_root.glob(f"*/*/{month}"))


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
    if len(candidate.parts) >= 2 and candidate.parts[0] == "storage" and candidate.parts[1] == "runtime":
        return storage_root / Path(*candidate.parts[1:])
    # Workflow state may store control-plane refs relative to the shared
    # trading-storage/storage root. Resolve those against the storage-root
    # parent so dashboard summaries can inspect manager-owned receipt timing
    # metadata without exposing raw files.
    if candidate.parts and candidate.parts[0] in {"storage", "02_control_plane"}:
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


def _stage_started_reason(raw_stage: Mapping[str, Any]) -> bool:
    reason = str(raw_stage.get("last_reason") or "").lower()
    return "stage execution started" in reason or "stage started" in reason


def _effective_dashboard_stage_status(raw_stage: Mapping[str, Any], timestamps: Mapping[str, str | None]) -> str:
    status = str(raw_stage.get("status") or "unknown")
    if status == "ready" and _stage_started_reason(raw_stage) and timestamps.get("started_at_utc") and not timestamps.get("ended_at_utc"):
        return "running"
    return status


def _unresolved_dashboard_blockers(raw_stage: Mapping[str, Any], *, stage_status: str) -> list[str]:
    """Return operator-facing blockers, not the static dependency list."""

    if stage_status in {"ready", "running", "succeeded", "not_applicable"}:
        return []
    reason = str(raw_stage.get("last_reason") or "")
    prefix = "waiting for "
    if reason.startswith(prefix):
        return [item.strip() for item in reason.removeprefix(prefix).split(",") if item.strip()]
    blockers = raw_stage.get("blockers") or []
    if not isinstance(blockers, list):
        return []
    return [str(blocker) for blocker in blockers]


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


def _stage_layer(raw_stage: Mapping[str, Any]) -> int | None:
    try:
        return int(raw_stage.get("layer"))
    except (TypeError, ValueError):
        return None


def _is_monthly_substrate_stage(raw_stage: Mapping[str, Any]) -> bool:
    stage_type = str(raw_stage.get("stage_type") or "")
    layer = _stage_layer(raw_stage)
    return stage_type in MONTHLY_TASK_STAGE_TYPES and layer in MONTHLY_SUBSTRATE_LAYERS


def _worker_info_for_stage(
    raw_stage: Mapping[str, Any],
    *,
    month: str | None = None,
    month_ingest_worker_count: int = DEFAULT_MONTH_INGEST_WORKERS,
) -> dict[str, str]:
    """Return the public worker assignment shown in task previews.

    Historical training exposes fold as the first-class task unit. Month-level
    ingestion lanes may still exist as internal execution detail, but the owner
    dashboard should present Layer 1+ historical stages as fold work so task
    identity stays consistent across layers. Worker fields stay diagnostic and
    should not drive the owner-facing Tasks page.
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
        return _model_worker_info()
    if stage_type in {
        "model_task",
        "model_training",
        "model_generation",
        "replay",
        "model_10_event_risk_governor",
        "model_evaluation",
        "post_replay_attribution",
        "promotion_review",
        "maintenance",
    }:
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
    fold_label = FOLD_LABEL_RE.fullmatch(text)
    if fold_label:
        year = int(fold_label.group(1))
        fold_number = int(fold_label.group(2))
        month_number = (fold_number - 1) * MONTHS_PER_MODEL_FOLD + 1
        if month_number <= 12:
            return f"{year:04d}-{month_number:02d}"
        return None
    if ".." not in text:
        return None
    start, _end = text.split("..", 1)
    return start if _is_month_key(start) else None


def _fold_period_range(start_month: str, end_month: str) -> str:
    return f"{start_month}..{end_month}"


def _fold_period_label(start_month: str, end_month: str) -> str:
    if not _is_month_key(start_month) or not _is_month_key(end_month):
        return _fold_period_range(start_month, end_month)
    try:
        start_year = int(start_month[:4])
        start_month_number = int(start_month[5:7])
        end_year = int(end_month[:4])
    except ValueError:
        return _fold_period_range(start_month, end_month)
    if start_year != end_year:
        return _fold_period_range(start_month, end_month)
    if _month_span_count(start_month, end_month) != MONTHS_PER_MODEL_FOLD:
        return _fold_period_range(start_month, end_month)
    if (start_month_number - 1) % MONTHS_PER_MODEL_FOLD != 0:
        return _fold_period_range(start_month, end_month)
    fold_number = ((start_month_number - 1) // MONTHS_PER_MODEL_FOLD) + 1
    return f"{start_year:04d}-fold{fold_number}"


def _add_months(month: str, offset: int) -> str | None:
    if not _is_month_key(month):
        return None
    try:
        year = int(month[:4])
        month_number = int(month[5:7])
    except ValueError:
        return None
    month_index = year * 12 + month_number - 1 + offset
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def _fold_label_range(period: str | None) -> str | None:
    text = str(period or "")
    fold_start = _fold_start_month(text)
    if fold_start is None or not FOLD_LABEL_RE.fullmatch(text):
        return None
    fold_end = _add_months(fold_start, MONTHS_PER_MODEL_FOLD - 1)
    if fold_end is None:
        return None
    months = _months_in_span(fold_start, fold_end)
    if len(months) != MONTHS_PER_MODEL_FOLD:
        return None
    return _fold_period_range(months[0], months[-1])


def _fold_label_for_month(month: str | None) -> str | None:
    if not _is_month_key(month):
        return None
    assert month is not None
    fold_start_offset = (_month_offset(month) or 0) % MONTHS_PER_MODEL_FOLD
    fold_start = _add_months(month, -fold_start_offset)
    if fold_start is None:
        return None
    fold_end = _add_months(fold_start, MONTHS_PER_MODEL_FOLD - 1)
    if fold_end is None:
        return None
    return _fold_period_label(fold_start, fold_end)


def _fold_window_for_period(period: str | None) -> tuple[str, str] | None:
    fold_start = _fold_start_month(period)
    if fold_start is None:
        return None
    fold_end = _add_months(fold_start, MONTHS_PER_MODEL_FOLD - 1)
    if fold_end is None:
        return None
    return fold_start, fold_end


def _public_task_period(period: str | None) -> str | None:
    """Normalize historical-training public task identity to fold where possible."""

    if not period:
        return None
    if FOLD_LABEL_RE.fullmatch(str(period)) or ".." in str(period):
        return str(period)
    return _fold_label_for_month(str(period)) or str(period)


def _child_partitions_for_period(period: str | None) -> list[str]:
    fold_start = _fold_start_month(period)
    if fold_start:
        fold_end = _add_months(fold_start, MONTHS_PER_MODEL_FOLD - 1)
        if fold_end:
            return _months_in_span(fold_start, fold_end)
    if _is_month_key(period):
        assert period is not None
        return [period]
    return []


def _public_period_visible_by_completed_cutoff(period: str | None, *, max_month: str) -> bool:
    fold_start = _fold_start_month(period)
    if fold_start:
        fold_end = _add_months(fold_start, MONTHS_PER_MODEL_FOLD - 1)
        return bool(fold_end and _month_visible_by_completed_cutoff(fold_end, max_month=max_month))
    return _month_visible_by_completed_cutoff(period, max_month=max_month)


def _stable_task_uid(raw_stage: Mapping[str, Any], *, task_period: str | None) -> str:
    stage_id = str(raw_stage.get("stage_id") or "unknown_stage")
    period = _fold_label_range(task_period) or task_period or "unscheduled"
    return f"{period}:{stage_id}"


def _is_fold_dashboard_stage(raw_stage: Mapping[str, Any]) -> bool:
    stage_type = str(raw_stage.get("stage_type") or "")
    return stage_type in FOLD_MODEL_STAGE_TYPES or stage_type in MONTHLY_TASK_STAGE_TYPES


def _is_fold_worker_stage(raw_stage: Mapping[str, Any]) -> bool:
    return str(raw_stage.get("stage_type") or "") in FOLD_MODEL_STAGE_TYPES


def _presentable_fold_stages(raw_stages: list[Any]) -> list[Any]:
    """Expose fold-scoped model-worker stages to Tasks."""

    visible: list[Any] = []
    for raw_stage in raw_stages:
        if not isinstance(raw_stage, Mapping):
            continue
        if _is_fold_dashboard_stage(raw_stage):
            visible.append(raw_stage)
    return visible


def _is_layer_local_post_generation_stage(raw_stage: Mapping[str, Any]) -> bool:
    stage_type = str(raw_stage.get("stage_type") or "")
    if stage_type not in {"model_evaluation", "promotion_review", "maintenance"}:
        return False
    try:
        return int(raw_stage.get("layer")) > 0
    except (TypeError, ValueError):
        return False


def _aggregate_status(stages: list[Mapping[str, Any]]) -> tuple[str, Mapping[str, Any] | None]:
    terminal_statuses = {"succeeded", "not_applicable"}
    for stage in stages:
        status = str(stage.get("status") or "")
        if status == "failed":
            return "failed", stage
    for stage in stages:
        status = str(stage.get("status") or "")
        if status not in terminal_statuses:
            return status or "unknown", stage
    if any(str(stage.get("status") or "") == "succeeded" for stage in stages):
        return "succeeded", stages[-1] if stages else None
    return "not_applicable", stages[-1] if stages else None


def _model_task_progress(layer_key: str, stages: list[Mapping[str, Any]], status: str) -> dict[str, Any]:
    terminal_statuses = {"succeeded", "not_applicable"}
    model_generation_stages = [stage for stage in stages if str(stage.get("stage_type") or "") == "model_generation"]
    split_months_by_name = {name: months for name, months in ROLLING_FOLD_SPLIT_MONTHS}
    if model_generation_stages:
        counted_stages = [
            stage
            for stage in model_generation_stages
            if isinstance(stage.get("dataset_split"), Mapping)
            and str(stage["dataset_split"].get("split_name") or "") in split_months_by_name
        ]
        expected_count = MODEL_GENERATION_SPLIT_MONTH_COUNT
    else:
        counted_stages = stages
        expected_count = len(counted_stages)
    def stage_weight(stage: Mapping[str, Any]) -> int:
        if not model_generation_stages:
            return 1
        dataset_split = stage.get("dataset_split")
        split_name = str(dataset_split.get("split_name") or "") if isinstance(dataset_split, Mapping) else ""
        return split_months_by_name.get(split_name, 0)

    ready_count = sum(stage_weight(stage) for stage in counted_stages if str(stage.get("status") or "") in terminal_statuses)
    failed_count = sum(stage_weight(stage) for stage in counted_stages if str(stage.get("status") or "") == "failed")
    pending_count = max(expected_count - ready_count - failed_count, 0)
    if expected_count and ready_count == expected_count and failed_count == 0:
        progress_status = "complete"
    elif failed_count:
        progress_status = "failed"
    elif model_generation_stages and str(status or "") in terminal_statuses:
        progress_status = "pending"
    else:
        progress_status = status
    unit_label = "dataset months" if model_generation_stages else "model stages"
    progress_source = "model_generation_dataset_splits" if model_generation_stages else "model_task_internal_stages"
    progress_basis = (
        "chronological train/validation/test month coverage required by the six-month fold: train=4 months, validation=1 month, test=1 month"
        if model_generation_stages
        else "layer-internal model task stages"
    )
    return {
        "stage_id": layer_key,
        "status": progress_status,
        "unit_label": unit_label,
        "expected_count": expected_count,
        "ready_count": ready_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
        "accepted_failed_count": 0,
        "can_unlock_downstream": bool(expected_count and ready_count == expected_count and failed_count == 0),
        "progress_source": progress_source,
        "progress_basis": progress_basis,
        "expected_partition_count": expected_count,
    }


def _aggregate_model_task_stages(raw_stages: list[Any]) -> list[Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    order: list[str] = []
    passthrough: list[Any] = []
    for raw_stage in raw_stages:
        if not isinstance(raw_stage, Mapping):
            continue
        layer_key = str(raw_stage.get("layer_key") or "")
        if not layer_key:
            passthrough.append(raw_stage)
            continue
        if layer_key not in grouped:
            grouped[layer_key] = []
            order.append(layer_key)
        grouped[layer_key].append(raw_stage)

    rows: list[Any] = []
    for layer_key in order:
        stages = grouped[layer_key]
        if not stages:
            continue
        status, active_stage = _aggregate_status(stages)
        first_stage = stages[0]
        active_stage = active_stage or first_stage
        try:
            layer = int(first_stage.get("layer"))
        except (TypeError, ValueError):
            layer = None
        receipt_refs: list[str] = []
        for stage in stages:
            refs = stage.get("receipt_refs")
            if isinstance(refs, list):
                receipt_refs.extend(str(ref) for ref in refs if str(ref))
        dataset_unit = active_stage.get("dataset_unit")
        if not isinstance(dataset_unit, Mapping):
            dataset_unit = first_stage.get("dataset_unit")
        row = dict(active_stage)
        row.update(
            {
                "stage_id": layer_key,
                "stage_type": "model_task",
                "task_label": _model_task_label(layer_key, layer=layer),
                "status": status,
                "layer": layer,
                "layer_key": layer_key,
                "dataset_unit": dataset_unit,
                "blockers": list(active_stage.get("blockers") or []),
                "receipt_refs": receipt_refs,
                "safe_without_provider_calls": all(bool(stage.get("safe_without_provider_calls", True)) for stage in stages),
                "provider_calls_allowed": any(bool(stage.get("provider_calls_allowed")) for stage in stages),
                "model_activation_allowed": any(bool(stage.get("model_activation_allowed")) for stage in stages),
                "broker_execution_allowed": any(bool(stage.get("broker_execution_allowed")) for stage in stages),
                "active_stage_id": active_stage.get("stage_id"),
                "active_stage_type": active_stage.get("stage_type"),
                "model_name": MODEL_NAME_BY_LAYER_KEY.get(layer_key),
                "model_display_name": _spaced_model_name(MODEL_NAME_BY_LAYER_KEY.get(layer_key) or ""),
                "layer_label": f"Layer {layer}" if layer is not None else None,
                "dashboard_progress": _model_task_progress(layer_key, stages, status),
                "internal_stages": [
                    {
                        "stage_id": stage.get("stage_id"),
                        "stage_type": stage.get("stage_type"),
                        "status": stage.get("status"),
                        "blockers": list(stage.get("blockers") or []),
                        "dataset_split": stage.get("dataset_split") if isinstance(stage.get("dataset_split"), Mapping) else None,
                    }
                    for stage in stages
                ],
            }
        )
        rows.append(row)
    rows.extend(passthrough)
    return rows


def _public_task_stages(raw_stages: list[Any]) -> list[Any]:
    rows: list[Any] = []
    for raw_stage in raw_stages:
        if not isinstance(raw_stage, Mapping):
            continue
        if _is_layer_local_post_generation_stage(raw_stage):
            continue
        rows.append(raw_stage)
    return _aggregate_model_task_stages(rows)


def _monthly_dashboard_stage_rows(raw_stage: Mapping[str, Any], *, timeline_month: str | None) -> list[dict[str, Any]]:
    """Return dashboard rows for a source/feature stage.

    Do not expand fold-scoped substrate into month rows. Months are child
    partitions attached to task detail, not top-level historical tasks.
    """

    return [dict(raw_stage)]


def _dashboard_stage_rows(raw_stage: Mapping[str, Any], *, timeline_month: str | None) -> list[dict[str, Any]]:
    return _monthly_dashboard_stage_rows(raw_stage, timeline_month=timeline_month)


def _target_symbol_from_fold_stages(raw_stages: list[Any]) -> str | None:
    for raw_stage in raw_stages:
        if not isinstance(raw_stage, Mapping):
            continue
        dataset_unit = raw_stage.get("dataset_unit")
        if not isinstance(dataset_unit, Mapping):
            continue
        symbol = str(dataset_unit.get("target_symbol") or "").strip().upper()
        if symbol:
            return symbol
    return None


def _target_scope_for_task(layer: object, dataset_unit: Mapping[str, Any] | None) -> str:
    try:
        layer_number = int(layer)
    except (TypeError, ValueError):
        layer_number = 0
    unit_kind = str(dataset_unit.get("unit_kind") if dataset_unit else "")
    target_symbol = str(dataset_unit.get("target_symbol") if dataset_unit else "").strip().upper()
    if layer_number == 1:
        return "market_context_panel"
    if layer_number == 2:
        return "sector_context_panel"
    if target_symbol:
        return "target_symbol"
    if unit_kind:
        return "target_required_unselected"
    return "not_applicable"


def _instrument_scope_for_task(layer: object) -> str:
    try:
        layer_number = int(layer)
    except (TypeError, ValueError):
        return "not_applicable"
    if layer_number == 1:
        return "market_context_proxy_panel"
    if layer_number == 2:
        return "sector_context_proxy_panel"
    if layer_number in {3, 4, 5, 6, 7}:
        return "target_underlying_evidence"
    if layer_number == 8:
        return "underlying_action_plan"
    if layer_number == 9:
        return "option_expression_or_underlying_fallback"
    return "not_applicable"


def _target_queue_summary(storage_root: Path) -> dict[str, Any] | None:
    queue_path = storage_root / "runtime" / DEFAULT_TARGET_QUEUE_PATH.name
    if not queue_path.exists() and DEFAULT_TARGET_QUEUE_PATH.exists():
        queue_path = DEFAULT_TARGET_QUEUE_PATH
    if not queue_path.exists():
        return None
    try:
        payload = _load_json_object(queue_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    raw_targets = payload.get("targets")
    if not isinstance(raw_targets, list):
        return None
    enabled_targets: list[str] = []
    disabled_targets: list[str] = []
    for raw_target in raw_targets:
        if isinstance(raw_target, Mapping):
            symbol = str(raw_target.get("symbol") or "").strip().upper()
            enabled = raw_target.get("enabled") is not False
        else:
            symbol = str(raw_target or "").strip().upper()
            enabled = True
        if not symbol:
            continue
        if enabled:
            enabled_targets.append(symbol)
        else:
            disabled_targets.append(symbol)
    return {
        "contract_type": payload.get("contract_type"),
        "queue_policy": payload.get("queue_policy"),
        "rotation_boundary": payload.get("rotation_boundary"),
        "enabled_targets": enabled_targets,
        "disabled_targets": disabled_targets,
        "target_count": len(enabled_targets),
        "path": str(queue_path),
    }


def _active_model_worker_fold_key(status: HistoricalSchedulerStatus) -> str | None:
    latest_decision = status.latest_decision or {}
    if not isinstance(latest_decision, Mapping):
        return None
    fold_months = latest_decision.get("fold_months")
    if isinstance(fold_months, list) and len(fold_months) >= MONTHS_PER_MODEL_FOLD:
        start = str(fold_months[0] or "")
        end = str(fold_months[MONTHS_PER_MODEL_FOLD - 1] or "")
        if start and end:
            return _fold_period_label(start, end)
    start_month = str(latest_decision.get("start_month") or "")
    end_month = str(latest_decision.get("end_month") or "")
    if not start_month or not end_month:
        execution_summary = latest_decision.get("execution_summary")
        workflow_plan = execution_summary.get("workflow_plan") if isinstance(execution_summary, Mapping) else None
        if isinstance(workflow_plan, Mapping):
            start_month = str(workflow_plan.get("start_month") or "")
            end_month = str(workflow_plan.get("end_month") or "")
    if start_month and end_month and start_month != end_month:
        return _fold_period_label(start_month, end_month)
    return None


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
    fold_key = _fold_period_label(selection.start_month, selection.end_month)
    if fold_key in included_months:
        return None
    try:
        plan = build_model_training_workflow_plan(
            start_month=selection.start_month,
            end_month=selection.end_month,
            storage_root=storage_root,
            selected_target_symbol=_selected_target_symbol(status),
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
            selected_target_symbol=_selected_target_symbol(status),
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
    active_task_progress = load_active_task_progress(storage_root / "runtime" / "task_progress")
    month_ingest_worker_count = DEFAULT_MONTH_INGEST_WORKERS
    max_dashboard_month = completed_historical_month_cutoff()
    month_stage_sets: list[tuple[str | None, list[Any], bool]] = []
    included_months: set[str] = set()
    auto_work_selection = status.auto_work_selection if isinstance(status.auto_work_selection, Mapping) else {}
    auto_start_month = str(auto_work_selection.get("start_month") or "")
    if (
        auto_work_selection.get("reason_code") == "fill_missing_workflow_state_gap"
        and auto_start_month
        and _has_control_plane_month_task_keys(storage_root, auto_start_month)
    ):
        lane_default_start_month = "2016-01"
    else:
        lane_default_start_month = status.current_month or status.workflow_checkpoint.start_month or "2016-01"
    lane_months = select_month_ingest_worker_months(
        storage_root=storage_root,
        default_start_month=lane_default_start_month,
        worker_count=month_ingest_worker_count,
        max_month=max_dashboard_month,
    )
    lane_worker_by_month = {month: _month_ingest_worker_info_for_lane(index + 1) for index, month in enumerate(lane_months)}
    active_public_periods = {
        period
        for period in [_public_task_period(status.current_month), *(_public_task_period(month) for month in lane_months)]
        if period
    }
    runtime_root = storage_root / "runtime"
    selected_target_symbol = _selected_target_symbol(status)
    if runtime_root.exists():
        fold_entries: list[tuple[str, list[Any], str | None, Path]] = []
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
            fold_target_symbol = _target_symbol_from_fold_stages(raw_stages)
            if selected_target_symbol and fold_target_symbol and fold_target_symbol != selected_target_symbol:
                continue
            fold_start = str(fold_payload.get("start_month") or "")
            fold_end = str(fold_payload.get("end_month") or "")
            fold_key = _fold_period_label(fold_start, fold_end) if fold_start and fold_end else fold_path.stem
            if fold_end and not _month_visible_by_completed_cutoff(fold_end, max_month=max_dashboard_month):
                continue
            fold_entries.append((fold_key, raw_stages, fold_target_symbol, fold_path))
        if selected_target_symbol:
            selected_symbol = selected_target_symbol.upper()
            fold_entries.sort(key=lambda entry: (entry[0], 0 if (entry[2] or "").upper() == selected_symbol else 1, entry[3].name))
        for fold_key, raw_stages, _fold_target_symbol, _fold_path in fold_entries:
            if fold_key in included_months:
                continue
            month_stage_sets.append((fold_key, raw_stages, True))
            included_months.add(fold_key)
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
            month_key = _public_task_period(str(payload.get("start_month") or month))
            if month_key and month_key not in included_months and _public_period_visible_by_completed_cutoff(month_key, max_month=max_dashboard_month):
                month_stage_sets.append((month_key, raw_stages, month_key in active_public_periods))
                included_months.add(month_key)
    for month in lane_months:
        if month in included_months:
            continue
        payload = _workflow_state_payload(storage_root, month)
        if payload is None and not _has_control_plane_month_task_keys(storage_root, month):
            continue
        raw_stages = payload.get("stages") if payload is not None else _planned_stage_rows(status, month=month)
        if isinstance(raw_stages, list):
            month_key = _public_task_period(str(payload.get("start_month") or month) if payload is not None else month)
            if month_key and month_key not in included_months and _public_period_visible_by_completed_cutoff(month_key, max_month=max_dashboard_month):
                month_stage_sets.append((month_key, raw_stages, True))
                included_months.add(month_key)
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
        and _public_task_period(active_month) not in included_months
        and _public_period_visible_by_completed_cutoff(_public_task_period(active_month), max_month=max_dashboard_month)
    ):
        month_stage_sets.append((_public_task_period(active_month), active_stages, True))
    if not month_stage_sets:
        return []
    public_stage_sets = [
        (timeline_month, _public_task_stages(raw_stages), is_active_month)
        for timeline_month, raw_stages, is_active_month in month_stage_sets
    ]

    coverage_stage_id = str(stage_coverage.get("stage_id") or "") if stage_coverage else ""
    latest_execution = _latest_stage_execution(status) or {}
    latest_failed_stage = latest_execution.get("stage_id") if latest_execution.get("status") == "failed" else None
    latest_failed_month = None
    if latest_failed_stage and isinstance(status.latest_decision, Mapping):
        latest_failed_month = _public_task_period(str(status.latest_decision.get("start_month") or "")) or None
    current_lane_heads: set[tuple[str | None, str]] = set()
    current_model_heads: set[tuple[str | None, str]] = set()
    active_model_fold_key = _active_model_worker_fold_key(status)
    seen_ingest_workers: set[str] = set()
    for timeline_month, raw_stages, _is_active_month in public_stage_sets:
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
    model_stage_sets = [
        stage_set for stage_set in public_stage_sets if not active_model_fold_key or stage_set[0] == active_model_fold_key
    ]
    if active_model_fold_key and not model_stage_sets:
        model_stage_sets = public_stage_sets
    for timeline_month, raw_stages, _is_active_month in model_stage_sets:
        if current_model_heads:
            break
        for raw_stage in raw_stages:
            if not isinstance(raw_stage, Mapping):
                continue
            stage_id = str(raw_stage.get("stage_id") or "")
            if not stage_id or str(raw_stage.get("status") or "") != "ready":
                continue
            if active_model_fold_key:
                if not _is_fold_dashboard_stage(raw_stage):
                    continue
            elif _is_active_month:
                if not _is_fold_dashboard_stage(raw_stage):
                    continue
            elif str(raw_stage.get("stage_type") or "") not in FOLD_MODEL_STAGE_TYPES:
                continue
            task_month = _public_task_period(str(raw_stage.get("month") or raw_stage.get("start_month") or timeline_month or "")) or None
            current_model_heads.add((task_month, stage_id))
            break
    tasks: list[dict[str, Any]] = []
    first_open_seen = False
    for timeline_month, raw_stages, is_active_month in public_stage_sets:
        for raw_stage in raw_stages:
            if not isinstance(raw_stage, Mapping):
                continue
            for dashboard_stage in _dashboard_stage_rows(raw_stage, timeline_month=timeline_month):
                if not isinstance(dashboard_stage, Mapping):
                    continue
                stage_id = str(dashboard_stage.get("stage_id") or "")
                if not stage_id or not _is_presentable_task_stage(dashboard_stage):
                    continue
                timestamp_fields = _task_timestamp_fields(dashboard_stage, storage_root=storage_root)
                stage_status = _effective_dashboard_stage_status(dashboard_stage, timestamp_fields)
                is_terminal = stage_status in {"succeeded", "not_applicable"}
                task_month_for_state = _public_task_period(str(dashboard_stage.get("month") or dashboard_stage.get("start_month") or timeline_month or "")) or None
                is_current = bool((task_month_for_state, stage_id) in current_lane_heads and not is_terminal)
                if not is_current:
                    is_current = bool((task_month_for_state, stage_id) in current_model_heads and not is_terminal)
                if not is_current and not current_lane_heads and not current_model_heads:
                    current_stage = str(status.current_stage or "")
                    is_current = bool(
                        is_active_month
                        and stage_id
                        and (stage_id == current_stage or current_stage.startswith(f"{stage_id}."))
                        and stage_status == "ready"
                        and not is_terminal
                    )
                if stage_status == "running":
                    is_current = True
                active_fallback_allowed = is_active_month and (
                    not active_model_fold_key or timeline_month == active_model_fold_key or _is_month_key(timeline_month)
                )
                if not current_lane_heads and active_fallback_allowed and not first_open_seen and stage_status == "ready" and not is_terminal:
                    is_current = True
                    first_open_seen = True
                latest_failed_matches_stage = bool(
                    latest_failed_stage and (stage_id == latest_failed_stage or str(latest_failed_stage).startswith(f"{stage_id}."))
                )
                if latest_failed_matches_stage and (
                    not latest_failed_month or task_month_for_state == latest_failed_month
                ):
                    task_state = "failed"
                elif is_terminal:
                    task_state = "completed" if stage_status == "succeeded" else "skipped"
                elif is_current:
                    task_state = "current"
                else:
                    task_state = "future"
                reason = str(dashboard_stage.get("last_reason") or "")
                if len(reason) > max_reason_chars:
                    reason = reason[: max_reason_chars - 1] + "…"
                blockers = _unresolved_dashboard_blockers(dashboard_stage, stage_status=stage_status)
                receipt_refs = dashboard_stage.get("receipt_refs") or []
                if not isinstance(receipt_refs, list):
                    receipt_refs = []
                dataset_unit = dashboard_stage.get("dataset_unit") if isinstance(dashboard_stage.get("dataset_unit"), Mapping) else None
                target_scope = _target_scope_for_task(dashboard_stage.get("layer"), dataset_unit)
                instrument_scope = _instrument_scope_for_task(dashboard_stage.get("layer"))
                task_month = _public_task_period(str(dashboard_stage.get("month") or dashboard_stage.get("start_month") or timeline_month or "")) or None
                child_partitions = _child_partitions_for_period(task_month)
                worker_info = lane_worker_by_month.get(task_month) or _worker_info_for_stage(
                    dashboard_stage, month=task_month, month_ingest_worker_count=month_ingest_worker_count
                )
                task_uid = _stable_task_uid(dashboard_stage, task_period=task_month)
                progress = active_task_progress.get(task_uid)
                if progress is None and dashboard_stage.get("active_stage_id"):
                    progress = active_task_progress.get(
                        _stable_task_uid({"stage_id": dashboard_stage.get("active_stage_id")}, task_period=task_month)
                    )
                dashboard_progress = (
                    dict(dashboard_stage["dashboard_progress"])
                    if isinstance(dashboard_stage.get("dashboard_progress"), Mapping)
                    else None
                )
                if (
                    progress is not None
                    and dashboard_progress is not None
                    and dashboard_progress.get("progress_source") == "model_generation_dataset_splits"
                ):
                    progress = {
                        **dashboard_progress,
                        "status": progress.get("status") or dashboard_progress.get("status"),
                        "stage_id": progress.get("stage_id") or dashboard_progress.get("stage_id"),
                        "nodes": progress.get("nodes", []),
                        "updated_at_utc": progress.get("updated_at_utc"),
                        "worker_id": progress.get("worker_id"),
                    }
                if progress is None and str(dashboard_stage.get("active_stage_type") or dashboard_stage.get("stage_type") or "") == "data_acquisition":
                    progress = _fold_stage_coverage_progress(
                        storage_root=storage_root,
                        stage_id=str(dashboard_stage.get("active_stage_id") or dashboard_stage.get("stage_id") or ""),
                        task_period=task_month,
                    )
                if progress is None:
                    semantic_stage_type = str(dashboard_stage.get("active_stage_type") or dashboard_stage.get("stage_type") or "")
                    progress = _semantic_stage_progress(
                        stage_id=stage_id,
                        stage_type=semantic_stage_type,
                        stage_status=stage_status,
                        task_period=task_month,
                    )
                if progress is None and dashboard_progress is not None:
                    progress = dashboard_progress
                if progress is None:
                    progress = _task_status_progress(stage_id, stage_status)
                task: dict[str, Any] = {
                    "sequence": len(tasks) + 1,
                    "task_number": None,
                    "task_uid": task_uid,
                    "month": task_month,
                    "period": task_month,
                    "fold_label": task_month if task_month and FOLD_LABEL_RE.fullmatch(task_month) else None,
                    "task_id": stage_id,
                    "task_label": str(dashboard_stage.get("task_label") or _public_stage_name(stage_id, dashboard_stage.get("stage_type"))),
                    "task_state": task_state,
                    "status": stage_status,
                    "stage_type": dashboard_stage.get("stage_type"),
                    "layer": dashboard_stage.get("layer"),
                    "layer_key": dashboard_stage.get("layer_key"),
                    "dataset_unit_kind": dataset_unit.get("unit_kind") if dataset_unit else None,
                    "dataset_unit_months": dataset_unit.get("unit_months") if dataset_unit else None,
                    "target_symbol": dataset_unit.get("target_symbol") if dataset_unit else None,
                    "target_required": dataset_unit.get("target_required") if dataset_unit else None,
                    "target_scope": target_scope,
                    "instrument_scope": instrument_scope,
                    **worker_info,
                    "updated_at_utc": dashboard_stage.get("updated_utc"),
                    **timestamp_fields,
                    "reason": reason or None,
                    "receipt_count": len(receipt_refs),
                    "blocker_count": len(blockers),
                    "detail": {
                        "blockers": [str(blocker) for blocker in blockers],
                        "receipt_refs": [str(ref) for ref in receipt_refs],
                        "progress": progress,
                        "safe_without_provider_calls": dashboard_stage.get("safe_without_provider_calls"),
                        "provider_calls_allowed": dashboard_stage.get("provider_calls_allowed"),
                        "model_activation_allowed": dashboard_stage.get("model_activation_allowed"),
                        "broker_execution_allowed": dashboard_stage.get("broker_execution_allowed"),
                        "dataset_unit": dataset_unit,
                        "target_scope": target_scope,
                        "instrument_scope": instrument_scope,
                        "child_partitions": child_partitions,
                        "active_stage_id": dashboard_stage.get("active_stage_id"),
                        "active_stage_type": dashboard_stage.get("active_stage_type"),
                        "model_name": dashboard_stage.get("model_name"),
                        "model_display_name": dashboard_stage.get("model_display_name"),
                        "layer_label": dashboard_stage.get("layer_label"),
                        "internal_stages": dashboard_stage.get("internal_stages") if isinstance(dashboard_stage.get("internal_stages"), list) else None,
                        "worker": worker_info,
                    },
                }
                if (
                    coverage_stage_id
                    and (stage_id == coverage_stage_id or coverage_stage_id.startswith(f"{stage_id}."))
                    and stage_coverage is not None
                    and (not status.current_month or task_month == _public_task_period(status.current_month))
                ):
                    task["detail"]["progress"] = _stage_coverage_chart(stage_coverage)
                latest_execution_stage = str(latest_execution.get("stage_id") or "")
                if (latest_execution_stage == stage_id or latest_execution_stage.startswith(f"{stage_id}.")) and (
                    not latest_failed_month or task_month == latest_failed_month
                ):
                    task["detail"]["last_execution"] = {
                        "status": latest_execution.get("status"),
                        "return_code": latest_execution.get("return_code"),
                        "reason": latest_execution.get("failure_detail") or latest_execution.get("reason"),
                    }
                tasks.append(task)
            continue
    return tasks


def _replay_dataset_root(storage_root: Path, contract_id: str) -> Path:
    return storage_root.parent / "05_replay_datasets" / contract_id


def _load_optional_json_object(path: Path) -> dict[str, Any] | None:
    try:
        return _load_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _replay_coverage_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except OSError:
        return []


def _int_field(payload: Mapping[str, Any], key: str) -> int:
    try:
        return int(payload.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _unique_csv_values(path: Path, field: str) -> set[str]:
    rows = _replay_coverage_rows(path)
    return {str(row.get(field) or "").strip() for row in rows if str(row.get(field) or "").strip()}


def _replay_window_month_count(dataset_root: Path) -> int:
    months = _unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month")
    if months:
        return len(months)
    rows = _replay_coverage_rows(dataset_root / "replay_window_manifest.csv")
    if not rows:
        return 60
    try:
        start = rows[0].get("start_date")
        end = rows[0].get("end_date")
        start_dt = datetime.fromisoformat(str(start)).date()
        end_dt = datetime.fromisoformat(str(end)).date()
    except (TypeError, ValueError):
        return 60
    return max(1, (end_dt.year - start_dt.year) * 12 + end_dt.month - start_dt.month)


def _month_span_count(start_month: str, end_month: str) -> int:
    try:
        start_year, start_month_number = (int(part) for part in start_month.split("-", 1))
        end_year, end_month_number = (int(part) for part in end_month.split("-", 1))
    except ValueError:
        return MONTHS_PER_MODEL_FOLD
    return max(1, (end_year - start_year) * 12 + end_month_number - start_month_number + 1)


def _months_in_span(start_month: str, end_month: str) -> list[str]:
    if not _is_month_key(start_month) or not _is_month_key(end_month):
        return []
    start_year, start_month_number = (int(part) for part in start_month.split("-", 1))
    end_year, end_month_number = (int(part) for part in end_month.split("-", 1))
    start_index = start_year * 12 + start_month_number - 1
    end_index = end_year * 12 + end_month_number - 1
    if end_index < start_index:
        return []
    months: list[str] = []
    for index in range(start_index, end_index + 1):
        year = index // 12
        month = index % 12 + 1
        months.append(f"{year:04d}-{month:02d}")
    return months


def _timeline_period_months(timeline_month: str | None) -> list[str]:
    text = str(timeline_month or "")
    if _is_month_key(text):
        return [text]
    if ".." not in text:
        range_label = _fold_label_range(text)
        if range_label is None:
            return []
        text = range_label
    if ".." not in text:
        return []
    start_month, end_month = text.split("..", 1)
    return _months_in_span(start_month, end_month)


def _task_stage_sort_rank(task: Mapping[str, Any]) -> int:
    return TASK_STAGE_SORT_ORDER.get(str(task.get("stage_type") or ""), 1_000)


def _task_layer_sort_rank(task: Mapping[str, Any]) -> int:
    try:
        layer = int(task.get("layer"))
    except (TypeError, ValueError):
        layer_key = str(task.get("layer_key") or "")
        match = re.match(r"layer_(\d+)_", layer_key)
        if not match:
            return 1_000
        return int(match.group(1))
    return layer if layer > 0 else 1_000


def _task_timeline_sort_key(task: Mapping[str, Any]) -> tuple[int, int, int, int, int, int]:
    month = str(task.get("month") or "")
    months = _timeline_period_months(month)
    if months:
        end_offset = _month_offset(months[-1])
        start_offset = _month_offset(months[0])
    else:
        end_offset = _month_offset(month)
        start_offset = end_offset
    try:
        sequence = int(task.get("sequence"))
    except (TypeError, ValueError):
        sequence = 1_000_000
    period_after_month = 1 if len(months) > 1 or FOLD_LABEL_RE.fullmatch(month) else 0
    return (
        start_offset if start_offset is not None else 1_000_000,
        end_offset if end_offset is not None else 1_000_000,
        period_after_month,
        _task_layer_sort_rank(task),
        _task_stage_sort_rank(task),
        sequence,
    )


def _sort_task_timeline(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_tasks = sorted(tasks, key=_task_timeline_sort_key)
    for index, task in enumerate(sorted_tasks, start=1):
        task["sequence"] = index
        task["task_number"] = index
    return sorted_tasks


def _replay_window_months(dataset_root: Path) -> tuple[str, str]:
    rows = _replay_coverage_rows(dataset_root / "replay_window_manifest.csv")
    if not rows:
        return "2021-01", "2026-01"
    start_date = str(rows[0].get("start_date") or "")
    end_date = str(rows[0].get("end_date") or "")
    start_month = start_date[:7] if _is_month_key(start_date[:7]) else "2021-01"
    end_month = end_date[:7] if _is_month_key(end_date[:7]) else "2026-01"
    return start_month, end_month


def _fold_state_target_symbol(payload: Mapping[str, Any], path: Path | None = None) -> str | None:
    for key in ("target_symbol", "selected_target_symbol", "target_ref"):
        value = str(payload.get(key) or "").strip().upper()
        if value:
            return value
    if path is not None:
        match = re.match(r"^model_training_fold_state_([A-Za-z0-9.-]+)_\d{4}-\d{2}_\d{4}-\d{2}$", path.stem)
        if match:
            return match.group(1).upper()
    raw_stages = payload.get("stages")
    if not isinstance(raw_stages, list):
        return None
    return _target_symbol_from_fold_stages(raw_stages)


def _is_completed_training_fold_state(payload: Mapping[str, Any]) -> bool:
    raw_stages = payload.get("stages")
    if not isinstance(raw_stages, list) or not raw_stages:
        return False
    if not base_stack_model_generation_splits_complete(raw_stages):
        return False
    presentable_stages = _presentable_fold_stages(raw_stages)
    if not presentable_stages:
        return False
    terminal_statuses = {"succeeded", "not_applicable"}
    return all(str(stage.get("status") or "").lower() in terminal_statuses for stage in presentable_stages if isinstance(stage, Mapping))


def _model_group_training_fold_window(
    *,
    storage_root: Path,
    selected_target_symbol: str | None,
) -> tuple[str, str, int]:
    completed_fold = _completed_model_group_training_fold(
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
    )
    if completed_fold is not None:
        start_month, end_month, _target_symbol = completed_fold
        return start_month, end_month, _month_span_count(start_month, end_month)
    return ("2016-01", "2016-06", MONTHS_PER_MODEL_FOLD)


def _completed_model_group_training_fold(
    *,
    storage_root: Path,
    selected_target_symbol: str | None,
) -> tuple[str, str, str | None] | None:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return None
    candidates: list[tuple[str, str, str | None]] = []
    for fold_path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
        try:
            payload = _load_json_object(fold_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not _is_completed_training_fold_state(payload):
            continue
        start_month = str(payload.get("start_month") or "")
        end_month = str(payload.get("end_month") or "")
        if not _is_month_key(start_month) or not _is_month_key(end_month):
            continue
        candidates.append((start_month, end_month, _fold_state_target_symbol(payload, fold_path)))
    if not candidates:
        return None
    selected_symbol = str(selected_target_symbol or "").strip().upper()
    if selected_symbol:
        symbol_candidates = [candidate for candidate in candidates if (candidate[2] or "").upper() == selected_symbol]
        if symbol_candidates:
            return sorted(symbol_candidates)[0]
    return sorted(candidates)[0]


def _pre_replay_fold_complete(
    *,
    storage_root: Path,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
) -> bool:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return False
    selected_symbol = str(selected_target_symbol or "").strip().upper()
    for fold_path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
        try:
            payload = _load_json_object(fold_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if str(payload.get("start_month") or "") != start_month or str(payload.get("end_month") or "") != end_month:
            continue
        if selected_symbol:
            target_symbol = (_fold_state_target_symbol(payload, fold_path) or "").upper()
            if target_symbol and target_symbol != selected_symbol:
                continue
        if _is_completed_training_fold_state(payload):
            return True
    return False


def _model_group_training_fold_target_symbol(
    *,
    storage_root: Path,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
) -> str | None:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return selected_target_symbol
    selected_symbol = str(selected_target_symbol or "").strip().upper()
    for fold_path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
        try:
            payload = _load_json_object(fold_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if str(payload.get("start_month") or "") != start_month or str(payload.get("end_month") or "") != end_month:
            continue
        target_symbol = (_fold_state_target_symbol(payload, fold_path) or "").upper()
        if selected_symbol and target_symbol and target_symbol != selected_symbol:
            continue
        return target_symbol or selected_symbol or None
    return selected_symbol or None


def _replay_dataset_scope_status(
    *,
    dataset_root: Path,
    manifest: Mapping[str, Any] | None,
    selected_target_symbol: str | None,
    completed_training_fold: tuple[str, str, str | None] | None,
) -> dict[str, Any]:
    target_symbol = str(selected_target_symbol or (completed_training_fold[2] if completed_training_fold else "") or "").strip().upper()
    target_refs = _replay_dataset_target_refs(dataset_root=dataset_root, manifest=manifest or {})
    manifest_fold_id = str((manifest or {}).get("candidate_fold_id") or (manifest or {}).get("fold_id") or "").strip()
    if completed_training_fold is not None:
        start_month, end_month, _target = completed_training_fold
        expected_fold_id = _fold_period_label(start_month, end_month)
        expected_fold_range = _fold_period_range(start_month, end_month)
        if manifest_fold_id and manifest_fold_id not in {expected_fold_id, expected_fold_range, f"{start_month}_{end_month}", f"fold_{start_month}_{end_month}"}:
            return {
                "compatible": False,
                "reason": f"Replay dataset fold {manifest_fold_id} does not match completed training fold {expected_fold_id}.",
                "dataset_target_refs": sorted(target_refs),
                "training_target_symbol": target_symbol,
            }
    if not target_symbol:
        return {
            "compatible": False,
            "reason": "Completed training fold has no target symbol for replay scope validation.",
            "dataset_target_refs": sorted(target_refs),
            "training_target_symbol": target_symbol,
        }
    if target_symbol not in target_refs:
        return {
            "compatible": False,
            "reason": f"Replay dataset target_refs must include completed training target {target_symbol}.",
            "dataset_target_refs": sorted(target_refs),
            "training_target_symbol": target_symbol,
        }
    return {
        "compatible": True,
        "reason": "Replay dataset is eligible for fold-bound target replay.",
        "dataset_target_refs": sorted(target_refs),
        "training_target_symbol": target_symbol,
    }


def _replay_dataset_target_refs(*, dataset_root: Path, manifest: Mapping[str, Any]) -> set[str]:
    refs = _string_set(manifest.get("target_refs") or manifest.get("replay_target_refs") or manifest.get("candidate_target_refs"))
    for row in _replay_coverage_rows(dataset_root / "feed_acquisition_plan.csv"):
        source_id = str(row.get("source_id") or "").strip()
        coverage_status = str(row.get("coverage_status") or "").strip().lower()
        if coverage_status not in {"available", "succeeded", "complete", "completed"}:
            continue
        if source_id == "okx_crypto_market_data":
            refs.update(CRYPTO_REPLAY_TARGET_REFS)
        refs.update(_string_set(row.get("target_ref") or row.get("target_symbol") or row.get("symbol")))
        params_text = str(row.get("params_json") or "").strip()
        if params_text:
            try:
                params = json.loads(params_text)
            except json.JSONDecodeError:
                params = None
            if isinstance(params, Mapping):
                refs.update(_string_set(params.get("target_refs") or params.get("symbols") or params.get("target_symbol")))
    return {ref.upper() for ref in refs if ref}


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


def _compatible_replay_run_ids(*, dataset_root: Path) -> set[str]:
    replay_root = dataset_root / "replay_execution_runs"
    run_ids: set[str] = set()
    if not replay_root.exists():
        return run_ids
    for receipt_path in sorted(replay_root.glob("*/replay_execution_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        if "current_deterministic_crypto_policy" in str(receipt.get("candidate_model_ref") or ""):
            continue
        run_id = str(receipt.get("replay_execution_run_id") or receipt_path.parent.name).strip()
        if run_id:
            run_ids.add(run_id)
    return run_ids


def _replay_ready_months(dataset_root: Path, replay_run_ids: set[str] | None = None) -> set[str]:
    ready: set[str] = set()
    for path in sorted((dataset_root / "replay_runs").glob("*.jsonl")) + [dataset_root / "replay_progress.jsonl"]:
        if not path.exists():
            continue
        for row in _load_jsonl_objects(path):
            run_id = str(row.get("replay_execution_run_id") or "").strip()
            if replay_run_ids is not None and run_id not in replay_run_ids:
                continue
            status = str(row.get("status") or row.get("replay_status") or "").lower()
            month = str(row.get("month") or row.get("replay_month") or "").strip()
            if month and status in {"succeeded", "completed", "complete"}:
                ready.add(month)
    return ready


def _replay_month_progress(
    *,
    dataset_root: Path,
    stage_id: str,
    status: str,
    ready_months: set[str] | None = None,
) -> dict[str, Any]:
    expected = _replay_window_month_count(dataset_root)
    ready = len(ready_months or set())
    failed = 0
    pending = max(expected - ready - failed, 0)
    return {
        "stage_id": stage_id,
        "status": "complete" if expected > 0 and ready >= expected else status,
        "unit_label": "replay months",
        "expected_count": expected,
        "ready_count": min(ready, expected),
        "pending_count": pending,
        "failed_count": failed,
        "accepted_failed_count": 0,
        "can_unlock_downstream": expected > 0 and ready >= expected,
        "progress_source": "replay_window_months",
        "progress_basis": "event replay months in the target-bound replay window",
    }


def _replay_dataset_month_operation_progress(
    *,
    dataset_root: Path,
    stage_id: str,
) -> dict[str, Any]:
    rows_by_month: dict[str, list[Mapping[str, str]]] = {}
    for row in _replay_coverage_rows(dataset_root / "feed_acquisition_plan.csv"):
        month = str(row.get("month") or "").strip()
        if month:
            rows_by_month.setdefault(month, []).append(row)
    expected = len(rows_by_month) or _replay_window_month_count(dataset_root)
    ready = 0
    missing_source_months = 0
    deferred_source_months = 0
    for rows in rows_by_month.values():
        month_ready = bool(rows)
        for row in rows:
            status = str(row.get("coverage_status") or "").strip().lower()
            if status not in {"available", "succeeded", "complete", "completed"}:
                month_ready = False
            if status == "missing":
                missing_source_months += 1
            if status == "deferred":
                deferred_source_months += 1
        if month_ready:
            ready += 1
    pending = max(expected - ready, 0)
    return {
        "stage_id": stage_id,
        "status": "complete" if expected > 0 and ready >= expected else "partial_ready",
        "unit_label": "replay months",
        "expected_count": expected,
        "ready_count": ready,
        "pending_count": pending,
        "failed_count": 0,
        "accepted_failed_count": 0,
        "can_unlock_downstream": False,
        "progress_source": "replay_dataset_month_operations",
        "progress_basis": "monthly acquire-replay-cleanup operations required before downstream evaluation",
        "missing_source_month_count": missing_source_months,
        "deferred_source_month_count": deferred_source_months,
    }


def _latest_replay_execution_receipt(dataset_root: Path) -> dict[str, Any] | None:
    replay_root = dataset_root / "replay_execution_runs"
    if not replay_root.exists():
        return None
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for receipt_path in sorted(replay_root.glob("*/replay_execution_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        if str(receipt.get("validation_status") or "") not in {"", "passed", "succeeded"}:
            continue
        created = str(receipt.get("generated_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt_path, receipt))
    if not candidates:
        return None
    _created, _receipt_path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return dict(receipt)


def _latest_replay_decision_rows_path(dataset_root: Path) -> Path | None:
    receipt = _latest_replay_execution_receipt(dataset_root)
    if receipt is None:
        return None
    decision_rows_ref = str(receipt.get("decision_rows_ref") or "")
    if not decision_rows_ref:
        return None
    return Path(decision_rows_ref)


def _replay_row_needs_layer_ten_attribution(row: Mapping[str, Any]) -> bool:
    """Return whether a replay decision row represents an attribution unit.

    Layer 10 owns post-replay failure/residual attribution. For the current
    crypto replay surface, filled negative outcomes and rejected positive
    outcomes are the concrete unit we can count without inventing percentages.
    """

    fill_status = str(row.get("fill_status") or "")
    decision_status = str(row.get("decision_status") or "")
    outcome_label = _int_field(row, "outcome_label")
    realized_return = _safe_float(row.get("realized_return"))
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    filled = fill_status == "simulated_filled" or decision_status in {"filled", "approved", "executed"}
    if filled:
        if outcome_label == 0:
            return True
        if realized_return is not None and realized_return <= baseline_return:
            return True
        return False
    if outcome_label == 1:
        return True
    return False


def _layer_ten_attribution_expected_count(dataset_root: Path) -> int:
    decision_rows_path = _latest_replay_decision_rows_path(dataset_root)
    if decision_rows_path is None:
        return 0
    return sum(1 for row in _load_jsonl_objects(decision_rows_path) if _replay_row_needs_layer_ten_attribution(row))


def _count_jsonl_rows(path: Path) -> int:
    return len(_load_jsonl_objects(path))


def _attribution_ready_count(attribution_artifacts: Mapping[str, Any] | None, *, expected_count: int) -> int:
    if attribution_artifacts is None:
        return 0
    receipt = attribution_artifacts.get("receipt")
    if not isinstance(receipt, Mapping):
        return expected_count
    for key in (
        "attributed_failure_count",
        "resolved_failure_count",
        "attributed_decision_count",
        "processed_failure_count",
        "ready_count",
    ):
        if key in receipt:
            return min(_int_field(receipt, key), expected_count)
    for key in ("attributed_decision_ids", "attributed_failure_ids", "resolved_failure_ids"):
        value = receipt.get(key)
        if isinstance(value, list):
            return min(len(value), expected_count)
    for key in ("attribution_rows_ref", "attribution_jsonl_ref", "output_jsonl_ref"):
        value = receipt.get(key)
        if value:
            return min(_count_jsonl_rows(Path(str(value))), expected_count)
    return expected_count


def _layer_ten_attribution_progress(
    *,
    dataset_root: Path,
    attribution_artifacts: Mapping[str, Any] | None,
    replay_complete: bool,
) -> dict[str, Any]:
    expected = _layer_ten_attribution_expected_count(dataset_root) if replay_complete else 0
    ready = _attribution_ready_count(attribution_artifacts, expected_count=expected)
    pending = max(expected - ready, 0)
    complete = expected > 0 and ready >= expected
    return {
        "stage_id": "model_group.model_10_event_risk_governor",
        "status": "complete" if complete else ("ready" if replay_complete else "blocked"),
        "unit_label": "failure attributions",
        "expected_count": expected,
        "ready_count": ready,
        "pending_count": pending,
        "failed_count": 0,
        "accepted_failed_count": 0,
        "can_unlock_downstream": attribution_artifacts is not None and (expected == 0 or ready >= expected),
        "progress_source": "replay_failure_attribution_units",
        "progress_basis": "replay rows where a filled decision lost money or a rejected decision missed a positive next outcome",
    }


def _checklist_progress(
    *,
    stage_id: str,
    status: str,
    checks: tuple[str, ...],
    ready_checks: set[str],
    unit_label: str,
    progress_source: str,
    progress_basis: str,
    can_unlock_downstream: bool | None = None,
) -> dict[str, Any]:
    expected = len(checks)
    ready = min(len(ready_checks.intersection(checks)), expected)
    complete = expected > 0 and ready >= expected
    return {
        "stage_id": stage_id,
        "status": "complete" if complete else status,
        "unit_label": unit_label,
        "expected_count": expected,
        "ready_count": ready,
        "pending_count": max(expected - ready, 0),
        "failed_count": 0,
        "accepted_failed_count": 0,
        "can_unlock_downstream": complete if can_unlock_downstream is None else can_unlock_downstream,
        "progress_source": progress_source,
        "progress_basis": progress_basis,
        "ready_checks": sorted(ready_checks.intersection(checks)),
        "expected_checks": list(checks),
    }


def _model_group_evaluation_progress(*, status: str, complete: bool) -> dict[str, Any]:
    return _checklist_progress(
        stage_id="model_group.evaluation",
        status=status,
        checks=MODEL_GROUP_EVALUATION_TESTS,
        ready_checks=set(MODEL_GROUP_EVALUATION_TESTS) if complete else set(),
        unit_label="evaluation tests",
        progress_source="model_group_evaluation_test_contract",
        progress_basis="required replay metrics, guardrail, incumbent-comparison, and Layer 10 attribution checks",
        can_unlock_downstream=complete,
    )


def _model_group_promotion_progress(*, status: str, complete: bool, eligible: bool) -> dict[str, Any]:
    return _checklist_progress(
        stage_id="model_group.promotion",
        status=status,
        checks=MODEL_GROUP_PROMOTION_TESTS,
        ready_checks=set(MODEL_GROUP_PROMOTION_TESTS) if complete else set(),
        unit_label="promotion tests",
        progress_source="model_group_promotion_test_contract",
        progress_basis="required benchmark, blinded-comparison, uncertainty, shadow-readiness, and blocker-review checks",
        can_unlock_downstream=eligible,
    )


def _model_group_maintenance_progress(
    *,
    status: str,
    promotion_decision: Mapping[str, Any] | None,
    promotion_review: Mapping[str, Any],
    readiness_record: Mapping[str, Any] | None,
    readiness_complete: bool,
) -> dict[str, Any]:
    ready_checks: set[str] = set()
    if promotion_decision is not None:
        ready_checks.add("promotion_eligibility_decision")
    if promotion_review:
        ready_checks.add("promotion_evaluation_review")
    if readiness_record is not None:
        ready_checks.add("promotion_readiness_record")
    if (
        readiness_record is not None
        and readiness_record.get("model_activation_performed") is False
        and readiness_record.get("active_model_config_written") is False
    ):
        ready_checks.add("activation_guardrails")
    return _checklist_progress(
        stage_id="model_group.maintenance",
        status=status,
        checks=MODEL_GROUP_MAINTENANCE_DATA_KINDS,
        ready_checks=ready_checks,
        unit_label="data types",
        progress_source="model_group_maintenance_data_kinds",
        progress_basis="required maintenance handoff data kinds before execution/shadow admission",
        can_unlock_downstream=readiness_complete,
    )


def _model_group_maintenance_not_applicable_progress() -> dict[str, Any]:
    return _checklist_progress(
        stage_id="model_group.maintenance",
        status="not_applicable",
        checks=MODEL_GROUP_MAINTENANCE_DATA_KINDS,
        ready_checks=set(MODEL_GROUP_MAINTENANCE_DATA_KINDS),
        unit_label="data types",
        progress_source="model_group_maintenance_data_kinds",
        progress_basis="maintenance handoff is not applicable because the candidate was not promotion eligible",
        can_unlock_downstream=True,
    )


def _replay_manifest_refs(manifest: Mapping[str, Any], dataset_root: Path) -> list[str]:
    refs = [
        manifest.get("source_contract_ref"),
        manifest.get("replay_window_manifest_ref") or dataset_root / "replay_window_manifest.csv",
        manifest.get("feed_acquisition_plan_ref") or dataset_root / "feed_acquisition_plan.csv",
        manifest.get("coverage_summary_ref") or dataset_root / "coverage_summary.csv",
    ]
    return [str(ref) for ref in refs if ref]


def _latest_promotion_review_artifacts(dataset_root: Path) -> dict[str, Any] | None:
    review_root = dataset_root / "promotion_review_runs"
    if not review_root.exists():
        return None
    candidates: list[tuple[str, Path, Mapping[str, Any], Mapping[str, Any] | None]] = []
    for decision_path in sorted(review_root.glob("*/promotion_eligibility_decision.json")):
        decision = _load_optional_json_object(decision_path)
        if decision is None:
            continue
        review_path = decision_path.parent / "promotion_evaluation_review.json"
        review = _load_optional_json_object(review_path)
        created = str(decision.get("created_at_utc") or (review or {}).get("created_at_utc") or decision_path.parent.name)
        candidates.append((created, decision_path, decision, review))
    if not candidates:
        return None
    _created, decision_path, decision, review = sorted(candidates, key=lambda item: item[0])[-1]
    refs = [str(decision_path)]
    review_path = decision_path.parent / "promotion_evaluation_review.json"
    if review_path.exists():
        refs.append(str(review_path))
    return {"decision": dict(decision), "review": dict(review or {}), "receipt_refs": refs}


def _latest_post_replay_attribution_artifacts(dataset_root: Path) -> dict[str, Any] | None:
    attribution_root = dataset_root / "post_replay_attribution_runs"
    if not attribution_root.exists():
        return None
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for receipt_path in sorted(attribution_root.glob("*/post_replay_attribution_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        status = str(receipt.get("status") or receipt.get("attribution_status") or "")
        if status not in {"succeeded", "complete", "completed"}:
            continue
        contract_type = str(receipt.get("contract_type") or "")
        if contract_type not in {"post_replay_event_attribution_receipt", "model_10_event_risk_governor_post_replay_attribution"}:
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt_path, receipt))
    if not candidates:
        return None
    _created, receipt_path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return {"receipt": dict(receipt), "receipt_refs": [str(receipt_path)]}


def _latest_promotion_readiness_artifacts(dataset_root: Path) -> dict[str, Any] | None:
    readiness_root = dataset_root / "promotion_readiness_runs"
    if not readiness_root.exists():
        return None
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for readiness_path in sorted(readiness_root.glob("*/promotion_readiness_record.json")):
        readiness = _load_optional_json_object(readiness_path)
        if readiness is None:
            continue
        created = str(readiness.get("created_at_utc") or readiness_path.parent.name)
        candidates.append((created, readiness_path, readiness))
    if not candidates:
        return None
    _created, readiness_path, readiness = sorted(candidates, key=lambda item: item[0])[-1]
    return {"readiness": dict(readiness), "receipt_refs": [str(readiness_path)]}


def _evaluation_worker_info() -> dict[str, str]:
    return {"worker_id": "evaluation_worker_1", "worker_label": "Evaluation Worker 1", "worker_kind": "evaluation_worker"}


def _model_group_replay_timeline_tasks(
    *,
    storage_root: Path,
    generated_at_utc: str,
    starting_sequence: int,
    selected_target_symbol: str | None = None,
    training_start_month: str | None = None,
    training_end_month: str | None = None,
    pre_replay_complete: bool | None = None,
    use_lifecycle_artifacts: bool = True,
) -> list[dict[str, Any]]:
    """Return owner-facing model-group replay and promotion-review tasks."""

    explicit_training_fold = training_start_month is not None and training_end_month is not None
    contract_id = "promotion_replay_candidate_policy"
    dataset_root = _replay_dataset_root(storage_root, contract_id)
    manifest_path = dataset_root / "dataset_manifest.json"
    manifest = _load_optional_json_object(manifest_path) if use_lifecycle_artifacts else None
    worker_info = _evaluation_worker_info()
    if training_start_month is None or training_end_month is None:
        training_start_month, training_end_month, training_unit_months = _model_group_training_fold_window(
            storage_root=storage_root,
            selected_target_symbol=selected_target_symbol,
        )
    else:
        training_unit_months = _month_span_count(training_start_month, training_end_month)
    period = _fold_period_label(training_start_month, training_end_month)
    replay_start_month, replay_end_month = _replay_window_months(dataset_root)
    replay_unit_months = _replay_window_month_count(dataset_root)
    if pre_replay_complete is None:
        completed_training_fold = _completed_model_group_training_fold(
            storage_root=storage_root,
            selected_target_symbol=selected_target_symbol,
        )
        pre_replay_complete = completed_training_fold is not None
    else:
        completed_training_fold = (
            (
                training_start_month,
                training_end_month,
                _model_group_training_fold_target_symbol(
                    storage_root=storage_root,
                    start_month=training_start_month,
                    end_month=training_end_month,
                    selected_target_symbol=selected_target_symbol,
                ),
            )
            if pre_replay_complete
            else None
        )
    lifecycle_artifacts_allowed = use_lifecycle_artifacts and pre_replay_complete
    replay_scope_status = _replay_dataset_scope_status(
        dataset_root=dataset_root,
        manifest=manifest,
        selected_target_symbol=selected_target_symbol,
        completed_training_fold=completed_training_fold,
    )
    lifecycle_artifacts_allowed = lifecycle_artifacts_allowed and bool(replay_scope_status["compatible"])
    layer_key = "model_group"
    tasks: list[dict[str, Any]] = []

    def append_task(
        *,
        task_id: str,
        label: str,
        task_state: str,
        status: str,
        reason: str,
        receipt_refs: list[str] | None = None,
        blockers: list[str] | None = None,
        progress: dict[str, Any] | None = None,
        stage_type: str = "model_evaluation",
    ) -> None:
        sequence = starting_sequence + len(tasks) + 1
        detail: dict[str, Any] = {
            "blockers": blockers or [],
            "receipt_refs": receipt_refs or [],
            "safe_without_provider_calls": True,
            "provider_calls_allowed": False,
            "model_activation_allowed": False,
            "broker_execution_allowed": False,
            "dataset_unit": {
                "unit_kind": "model_group_training_fold",
                "unit_months": training_unit_months,
                "start_month": training_start_month,
                "end_month": training_end_month,
                "target_required": False,
                "description": "Model-group candidate training fold used for replay, promotion review, and maintenance.",
            },
            "replay_window": {
                "unit_kind": "model_group_replay_window",
                "unit_months": replay_unit_months,
                "start_month": replay_start_month,
                "end_month": replay_end_month,
                "contract_id": contract_id,
                "target_required": False,
                "description": "Target-bound replay window used to test the candidate model group.",
            },
            "worker": worker_info,
            "progress": progress,
        }
        tasks.append(
            {
                "sequence": sequence,
                "task_number": None,
                "task_uid": f"{period}:{task_id}",
                "month": period,
                "task_id": task_id,
                "task_label": label,
                "task_state": task_state,
                "status": status,
                "stage_type": stage_type,
                "layer": None,
                "layer_key": layer_key,
                "dataset_unit_kind": "model_group_training_fold",
                "dataset_unit_months": training_unit_months,
                "target_symbol": None,
                "target_required": False,
                **worker_info,
                "updated_at_utc": generated_at_utc,
                "created_at_utc": None,
                "started_at_utc": None,
                "ended_at_utc": None,
                "status_updated_at_utc": generated_at_utc,
                "reason": reason,
                "receipt_count": len(receipt_refs or []),
                "blocker_count": len(blockers or []),
                "detail": detail,
            }
        )

    if not explicit_training_fold and manifest is None and not dataset_root.exists() and completed_training_fold is None:
        return []

    receipt_refs = _replay_manifest_refs(manifest, dataset_root) if manifest is not None else []
    prepared_at = str((manifest or {}).get("prepared_at_utc") or generated_at_utc)
    tasks_updated_at = prepared_at or generated_at_utc

    expected = _int_field(manifest or {}, "feed_acquisition_count")
    ready = _int_field(manifest or {}, "available_feed_acquisition_count")
    deferred = _int_field(manifest or {}, "deferred_feed_acquisition_count")
    missing = _int_field(manifest or {}, "missing_feed_acquisition_count")
    if manifest is not None and expected == 0:
        coverage_rows = _replay_coverage_rows(dataset_root / "coverage_summary.csv")
        expected = sum(int(row.get("required_acquisition_count") or 0) for row in coverage_rows)
        ready = sum(int(row.get("available_acquisition_count") or 0) for row in coverage_rows)
        deferred = sum(int(row.get("deferred_acquisition_count") or 0) for row in coverage_rows)
        missing = sum(int(row.get("missing_acquisition_count") or 0) for row in coverage_rows)

    coverage_complete = manifest is not None and expected > 0 and missing == 0
    freeze_status = str((manifest or {}).get("freeze_status") or "not_frozen")
    freeze_ready = coverage_complete and freeze_status == "frozen"
    compatible_replay_run_ids = (
        _compatible_replay_run_ids(dataset_root=dataset_root)
        if lifecycle_artifacts_allowed
        else set()
    )
    replay_ready_months = (
        _replay_ready_months(dataset_root, replay_run_ids=compatible_replay_run_ids)
        if lifecycle_artifacts_allowed and compatible_replay_run_ids
        else set()
    )
    replay_progress = _replay_month_progress(
        dataset_root=dataset_root,
        stage_id="model_group.replay",
        status=(
            "complete"
            if replay_ready_months and len(replay_ready_months) >= _replay_window_month_count(dataset_root)
            else ("ready" if freeze_ready else "blocked")
        ),
        ready_months=replay_ready_months,
    )
    replay_started = bool(replay_ready_months)
    replay_complete = bool(replay_progress["can_unlock_downstream"])
    attribution_artifacts = _latest_post_replay_attribution_artifacts(dataset_root) if lifecycle_artifacts_allowed and replay_complete else None
    attribution_complete = attribution_artifacts is not None
    attribution_progress = _layer_ten_attribution_progress(
        dataset_root=dataset_root,
        attribution_artifacts=attribution_artifacts,
        replay_complete=replay_complete,
    )
    promotion_artifacts = _latest_promotion_review_artifacts(dataset_root) if lifecycle_artifacts_allowed and attribution_complete else None
    promotion_decision = promotion_artifacts["decision"] if promotion_artifacts else None
    promotion_review = promotion_artifacts["review"] if promotion_artifacts else {}
    promotion_decision_status = str((promotion_decision or {}).get("decision_status") or "")
    promotion_complete = promotion_decision is not None
    promotion_eligible = promotion_decision_status == "eligible"
    promotion_terminal_not_eligible = promotion_complete and not promotion_eligible
    readiness_artifacts = _latest_promotion_readiness_artifacts(dataset_root) if lifecycle_artifacts_allowed and promotion_eligible else None
    readiness_record = readiness_artifacts["readiness"] if readiness_artifacts else None
    readiness_complete = (
        promotion_eligible
        and readiness_record is not None
        and str(readiness_record.get("contract_type") or "") == "promotion_readiness_record"
        and readiness_record.get("model_activation_performed") is False
        and readiness_record.get("active_model_config_written") is False
    )
    promotion_blockers = [
        str(item)
        for item in (
            promotion_review.get("blocking_issues")
            if isinstance(promotion_review, Mapping) and isinstance(promotion_review.get("blocking_issues"), list)
            else []
        )
        if str(item)
    ]

    replay_blockers: list[str] = []
    if not pre_replay_complete:
        replay_blockers.append("fold_layers_01_09_model_generation_complete")
    elif manifest is None:
        replay_blockers.append("replay_dataset_preparation_manifest")
    elif not replay_scope_status["compatible"]:
        replay_blockers.append("replay_dataset_scope_matches_training_fold")
    elif not coverage_complete:
        replay_blockers.append("replay_dataset_coverage_complete")
    elif not freeze_ready:
        replay_blockers.append("model_group_replay_freeze_review")

    replay_state = "completed" if replay_complete else ("current" if pre_replay_complete or replay_started else "future")
    replay_status = "succeeded" if replay_complete else ("ready" if not replay_blockers else "blocked")
    replay_reason = (
        "Model-group replay is complete across the accepted replay window."
        if replay_complete
        else f"Model-group replay has started and completed {len(replay_ready_months)}/{_replay_window_month_count(dataset_root)} replay months."
        if replay_started
        else "Pre-replay Layer 1-9 fold is complete; replay is waiting for its fixed replay dataset preparation manifest."
        if pre_replay_complete and manifest is None
        else str(replay_scope_status["reason"])
        if pre_replay_complete and manifest is not None and not replay_scope_status["compatible"]
        else f"Replay dataset coverage is incomplete: {missing}/{expected} feed acquisitions missing."
        if pre_replay_complete and manifest is not None and not coverage_complete
        else f"Replay dataset is covered but not frozen; current freeze_status={freeze_status}."
        if pre_replay_complete and manifest is not None and coverage_complete and not freeze_ready
        else "Replay dataset is frozen and ready for fold-bound target replay."
        if pre_replay_complete and manifest is not None and freeze_ready and not replay_complete
        else "Waiting for pre-replay Layer 1-9 model generation to complete before replay can run."
    )
    if manifest is not None and replay_scope_status["compatible"] and not coverage_complete:
        replay_progress = _replay_dataset_month_operation_progress(
            dataset_root=dataset_root,
            stage_id="model_group.replay",
        )

    append_task(
        task_id="model_group.replay",
        label="Model Replay",
        task_state=replay_state,
        status=replay_status,
        reason=replay_reason,
        receipt_refs=[str(manifest_path)] if manifest is not None else receipt_refs,
        blockers=replay_blockers,
        progress=replay_progress,
        stage_type="replay",
    )
    tasks[-1]["updated_at_utc"] = tasks_updated_at
    tasks[-1]["status_updated_at_utc"] = tasks_updated_at

    append_task(
        task_id="model_group.model_10_event_risk_governor",
        label="Layer 10 Event Risk Governor",
        task_state="completed" if attribution_complete else ("current" if replay_complete else "future"),
        status="succeeded" if attribution_complete else ("ready" if replay_complete else "blocked"),
        reason=(
            "Layer 10 post-replay event failure/residual attribution is complete."
            if attribution_complete
            else "Layer 10 is ready to attribute replay failures, residuals, missed opportunities, and path deviations."
            if replay_complete
            else "Waiting for model-group replay before Layer 10 attribution can run."
        ),
        receipt_refs=list(attribution_artifacts["receipt_refs"]) if attribution_artifacts else None,
        blockers=[] if replay_complete else ["model_group.replay"],
        stage_type="model_10_event_risk_governor",
        progress=attribution_progress,
    )

    evaluation_complete = promotion_complete
    append_task(
        task_id="model_group.evaluation",
        label="Model Evaluation",
        task_state="completed" if evaluation_complete else ("current" if attribution_complete else "future"),
        status="succeeded" if evaluation_complete else ("ready" if attribution_complete else "blocked"),
        reason=(
            "Model-group evaluation evidence is complete and available for promotion."
            if evaluation_complete
            else "Evaluation is ready to aggregate replay metrics, guardrails, incumbent comparison, and Layer 10 attribution evidence."
            if attribution_complete
            else "Waiting for Layer 10 attribution before evaluation can run."
        ),
        receipt_refs=list(promotion_artifacts["receipt_refs"]) if promotion_artifacts else None,
        blockers=[] if attribution_complete else ["model_group.model_10_event_risk_governor"],
        stage_type="model_evaluation",
        progress=_model_group_evaluation_progress(
            status="succeeded" if evaluation_complete else ("ready" if attribution_complete else "blocked"),
            complete=evaluation_complete,
        ),
    )

    append_task(
        task_id="model_group.promotion",
        label="Model Promotion",
        task_state="completed" if promotion_complete else ("current" if evaluation_complete else "future"),
        status=("succeeded" if promotion_eligible else (promotion_decision_status or "ready")) if evaluation_complete else "blocked",
        reason=(
            str(promotion_decision.get("decision_reason") or "Promotion review completed.") if promotion_decision else
            "Promotion waits for completed model-group evaluation and promotion-evaluation-review evidence."
        ),
        receipt_refs=list(promotion_artifacts["receipt_refs"]) if promotion_artifacts else None,
        blockers=(
            promotion_blockers
            if promotion_complete and not promotion_eligible and evaluation_complete
            else ([] if evaluation_complete else ["model_group.evaluation", "promotion-evaluation-review"])
        ),
        stage_type="promotion_review",
        progress=_model_group_promotion_progress(
            status=(promotion_decision_status or "ready") if evaluation_complete else "blocked",
            complete=promotion_complete and evaluation_complete,
            eligible=promotion_eligible,
        ),
    )
    append_task(
        task_id="model_group.maintenance",
        label="Model Maintenance",
        task_state="completed" if readiness_complete else ("skipped" if promotion_terminal_not_eligible else ("current" if promotion_eligible else "future")),
        status="succeeded" if readiness_complete else ("not_applicable" if promotion_terminal_not_eligible else ("ready" if promotion_eligible else "blocked")),
        reason=(
            "Promotion readiness handoff is complete; execution can admit the promoted model group to market-hours shadow review."
            if readiness_complete
            else "Promotion review did not admit this candidate, so maintenance/shadow handoff is not applicable."
            if promotion_terminal_not_eligible
            else
            "Model-group candidate is eligible for maintenance handoff after promotion."
            if promotion_eligible
            else "Waiting for eligible model-group promotion before maintenance can run."
        ),
        receipt_refs=list(readiness_artifacts["receipt_refs"]) if readiness_artifacts else None,
        blockers=[] if (promotion_eligible or promotion_terminal_not_eligible) else ["model_group.promotion"],
        stage_type="maintenance",
        progress=(
            _model_group_maintenance_not_applicable_progress()
            if promotion_terminal_not_eligible
            else _model_group_maintenance_progress(
                status="succeeded" if readiness_complete else ("ready" if promotion_eligible else "blocked"),
                promotion_decision=promotion_decision,
                promotion_review=promotion_review if isinstance(promotion_review, Mapping) else {},
                readiness_record=readiness_record,
                readiness_complete=readiness_complete,
            )
        ),
    )
    return tasks


def _model_group_lifecycle_tasks_for_visible_folds(
    task_timeline: list[dict[str, Any]],
    *,
    storage_root: Path,
    generated_at_utc: str,
    selected_target_symbol: str | None,
) -> list[dict[str, Any]]:
    """Return fixed replay-through-maintenance task rows for visible folds."""

    visible_periods: list[tuple[str, str, str]] = []
    seen_periods: set[str] = set()
    for task in task_timeline:
        period = str(task.get("month") or "")
        if period in seen_periods:
            continue
        window = _fold_window_for_period(period)
        if window is None:
            continue
        start_month, end_month = window
        visible_periods.append((period, start_month, end_month))
        seen_periods.add(period)

    if not visible_periods:
        return _model_group_replay_timeline_tasks(
            storage_root=storage_root,
            generated_at_utc=generated_at_utc,
            starting_sequence=len(task_timeline),
            selected_target_symbol=selected_target_symbol,
        )

    completed_fold = _completed_model_group_training_fold(
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
    )
    artifact_fold = (completed_fold[0], completed_fold[1]) if completed_fold is not None else None
    if artifact_fold is None and visible_periods and _replay_dataset_root(storage_root, "promotion_replay_candidate_policy").exists():
        _period, start_month, end_month = visible_periods[0]
        artifact_fold = (start_month, end_month)
    tasks: list[dict[str, Any]] = []
    for _period, start_month, end_month in visible_periods:
        pre_replay_complete = _pre_replay_fold_complete(
            storage_root=storage_root,
            start_month=start_month,
            end_month=end_month,
            selected_target_symbol=selected_target_symbol,
        )
        use_lifecycle_artifacts = artifact_fold == (start_month, end_month)
        tasks.extend(
            _model_group_replay_timeline_tasks(
                storage_root=storage_root,
                generated_at_utc=generated_at_utc,
                starting_sequence=len(task_timeline) + len(tasks),
                selected_target_symbol=selected_target_symbol,
                training_start_month=start_month,
                training_end_month=end_month,
                pre_replay_complete=pre_replay_complete,
                use_lifecycle_artifacts=use_lifecycle_artifacts,
            )
        )
    return tasks


def build_historical_task_progress_summary(
    status: HistoricalSchedulerStatus,
    *,
    stage_coverage: Mapping[str, Any] | None = None,
    generated_at_utc: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Build `historical_task_progress_summary` for storage materialization."""

    generated_at_utc = generated_at_utc or now_utc()
    stage_counts = _stage_counts(status)
    task_timeline = _task_timeline(status, stage_coverage=stage_coverage)
    storage_root = _storage_root_from_checkpoint_path(status.workflow_checkpoint.path)
    selected_target_symbol = _selected_target_symbol(status)
    task_timeline.extend(
        _model_group_lifecycle_tasks_for_visible_folds(
            task_timeline,
            storage_root=storage_root,
            generated_at_utc=generated_at_utc,
            selected_target_symbol=selected_target_symbol,
        )
    )
    task_timeline = _sort_task_timeline(task_timeline)
    public_active_task = _public_active_task(status, task_timeline)
    agent_error_summary = _mark_superseded_agent_errors(
        _agent_error_summary(storage_root, database_url=database_url),
        task_timeline,
    )
    if not stage_counts and task_timeline:
        for task in task_timeline:
            task_status = str(task.get("status") or "unknown")
            stage_counts[task_status] = stage_counts.get(task_status, 0) + 1
        stage_counts = dict(sorted(stage_counts.items()))
    progress_percent = _progress_percent(stage_counts)
    dashboard_status, severity, summary = _owner_status(status, public_active_task=public_active_task)
    active_blocker = _active_blocker(status, public_active_task)
    chart_payload: dict[str, Any] = {
        "current_month": _public_current_period(status, public_active_task),
        "active_stage": public_active_task.get("task_id") if public_active_task else None,
        "active_task": _public_active_task_summary(public_active_task),
        "selected_target_symbol": selected_target_symbol,
        "target_queue": _target_queue_summary(storage_root),
        "internal_current_month": status.current_month,
        "internal_active_stage": status.current_stage,
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
        "issue_refs": _issue_refs(status, public_active_task=public_active_task),
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
    parser.add_argument("--database-url", help="Optional database URL for SQL-backed server error catalog rows.")
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
    payload = build_historical_task_progress_summary(status, stage_coverage=stage_coverage, database_url=args.database_url)
    write_historical_task_progress_summary(payload, output=sys.stdout)
    return 0


__all__ = [
    "HISTORICAL_TASK_PROGRESS_CONTRACT",
    "build_historical_task_progress_summary",
    "write_historical_task_progress_summary",
]

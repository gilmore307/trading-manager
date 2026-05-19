"""Runtime status and readiness summary for the historical scheduler service.

This module is intentionally read-only. It inspects durable scheduler state,
decision logs, workflow checkpoints, local failure evidence, and deployment
artifacts so operators can observe the resident historical-modeling service
without driving the workflow manually.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

from .scheduler_daemon import DEFAULT_DECISION_LOG_PATH, DEFAULT_LOCK_PATH, DEFAULT_STATE_PATH, _process_exists, select_next_historical_work
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler_locks import scheduler_lock_plan

DEFAULT_SERVICE_TEMPLATE_PATH = Path("deploy/systemd/trading-manager-historical-scheduler.service")
DEFAULT_SERVICE_ENV_PATH = Path("deploy/systemd/trading-manager-historical-scheduler.env")
DEFAULT_DAEMON_WRAPPER_PATH = Path("scripts/tasks/run_automation_scheduler_daemon.py")
RECOMMENDED_SERVICE_FLAGS = (
    "--execute-safe-preparation",
    "--execute-safe-offline-stages",
    "--execute-autonomous-provider-stages",
    "--auto-select-next-work",
    "--advance-month-on-complete",
)
TERMINAL_STAGE_STATUSES = {"succeeded", "not_applicable"}


@dataclass(frozen=True)
class FileStatus:
    """Small file existence/size summary."""

    path: str
    exists: bool
    size_bytes: int | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LockStatus:
    """Single-instance lock observation."""

    path: str
    status: str
    pid: int | None = None
    age_seconds: float | None = None
    reason: str | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowCheckpointStatus:
    """Status summary for the active month workflow checkpoint."""

    path: str
    exists: bool
    start_month: str | None
    end_month: str | None
    terminal_complete: bool
    stage_counts: dict[str, int]
    next_stage_id: str | None
    next_stage_status: str | None
    next_stage_type: str | None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalSchedulerStatus:
    """Operator-facing historical scheduler status snapshot."""

    contract_type: str
    generated_utc: str
    service_runtime_ready: bool
    recommended_next_action: str
    current_month: str | None
    current_stage: str | None
    blocked_reason: str | None
    state_file: FileStatus
    decision_log_file: FileStatus
    lock: LockStatus
    lock_plan: dict[str, Any]
    service_template: FileStatus
    service_env: FileStatus
    daemon_wrapper: FileStatus
    recommended_service_flags_present: bool
    missing_service_flags: tuple[str, ...]
    daemon_state: dict[str, Any] | None
    latest_decision: dict[str, Any] | None
    auto_work_selection: dict[str, Any]
    workflow_checkpoint: WorkflowCheckpointStatus
    failure_summary: dict[str, Any]
    provider_status: dict[str, Any]
    gated_scope_status: dict[str, Any]
    open_operational_items: tuple[str, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["missing_service_flags"] = list(self.missing_service_flags)
        row["open_operational_items"] = list(self.open_operational_items)
        row["state_file"] = self.state_file.summary_row()
        row["decision_log_file"] = self.decision_log_file.summary_row()
        row["lock"] = self.lock.summary_row()
        row["service_template"] = self.service_template.summary_row()
        row["service_env"] = self.service_env.summary_row()
        row["daemon_wrapper"] = self.daemon_wrapper.summary_row()
        row["workflow_checkpoint"] = self.workflow_checkpoint.summary_row()
        return row


def _now_utc() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat()


def _file_status(path: Path) -> FileStatus:
    try:
        stat = path.stat()
    except OSError:
        return FileStatus(path=str(path), exists=False, size_bytes=None)
    return FileStatus(path=str(path), exists=True, size_bytes=stat.st_size)


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _latest_jsonl_object(path: Path) -> tuple[dict[str, Any] | None, int]:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return None, 0
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload, len(lines)
    return None, len(lines)


def _lock_status(path: Path) -> LockStatus:
    if not path.exists():
        return LockStatus(path=str(path), status="absent", reason="no scheduler lock file is present")
    age_seconds = time.time() - path.stat().st_mtime
    payload = _read_json_object(path) or {}
    pid = int(payload.get("pid") or 0) if str(payload.get("pid") or "").isdigit() else None
    if pid is not None and _process_exists(pid):
        return LockStatus(path=str(path), status="active", pid=pid, age_seconds=age_seconds, reason="lock pid is running")
    return LockStatus(path=str(path), status="stale", pid=pid, age_seconds=age_seconds, reason="lock file exists but pid is not running")


def _workflow_state_path(storage_root: Path, month: str | None) -> Path:
    if month:
        return storage_root / "runtime" / f"model_training_workflow_state_{month}.json"
    return storage_root / "runtime" / "model_training_workflow_state.json"


def _stage_status_counts(stages: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stage in stages:
        status = str(stage.get("status") or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _workflow_checkpoint_status(path: Path) -> WorkflowCheckpointStatus:
    payload = _read_json_object(path)
    if payload is None:
        return WorkflowCheckpointStatus(
            path=str(path),
            exists=path.exists(),
            start_month=None,
            end_month=None,
            terminal_complete=False,
            stage_counts={},
            next_stage_id=None,
            next_stage_status=None,
            next_stage_type=None,
        )
    stages = [stage for stage in payload.get("stages") or [] if isinstance(stage, Mapping)]
    next_stage = None
    for stage in stages:
        if stage.get("status") not in TERMINAL_STAGE_STATUSES:
            next_stage = stage
            break
    return WorkflowCheckpointStatus(
        path=str(path),
        exists=True,
        start_month=str(payload.get("start_month") or "") or None,
        end_month=str(payload.get("end_month") or "") or None,
        terminal_complete=bool(stages) and all(stage.get("status") in TERMINAL_STAGE_STATUSES for stage in stages),
        stage_counts=_stage_status_counts(stages),
        next_stage_id=str(next_stage.get("stage_id") or "") or None if next_stage else None,
        next_stage_status=str(next_stage.get("status") or "") or None if next_stage else None,
        next_stage_type=str(next_stage.get("stage_type") or "") or None if next_stage else None,
    )


def _service_flags(service_template_path: Path) -> tuple[bool, tuple[str, ...]]:
    try:
        text = service_template_path.read_text(encoding="utf-8")
    except OSError:
        return False, RECOMMENDED_SERVICE_FLAGS
    missing = tuple(flag for flag in RECOMMENDED_SERVICE_FLAGS if flag not in text)
    return not missing, missing


def _failure_summary(storage_root: Path) -> dict[str, Any]:
    runtime_root = storage_root / "runtime"
    paths: list[Path] = []
    if runtime_root.exists():
        paths = sorted(
            path
            for path in runtime_root.rglob("*")
            if path.is_file() and "failure" in path.name.lower() and path.suffix.lower() in {".json", ".jsonl"}
        )
    line_count = 0
    for path in paths:
        try:
            if path.suffix.lower() == ".jsonl":
                line_count += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
            else:
                line_count += 1
        except OSError:
            continue
    return {
        "contract_type": "manager_failure_evidence_summary",
        "local_failure_evidence_file_count": len(paths),
        "local_failure_evidence_row_count": line_count,
        "sample_paths": [str(path) for path in paths[:10]],
    }


def _decision_month(decision: Mapping[str, Any] | None) -> str | None:
    if not decision:
        return None
    for key in ("start_month", "month_start"):
        value = str(decision.get(key) or "")
        if value:
            return value
    execution_summary = decision.get("execution_summary")
    if isinstance(execution_summary, Mapping):
        value = str(execution_summary.get("month_start") or execution_summary.get("start_month") or "")
        if value:
            return value
    workflow_state = decision.get("workflow_state")
    if isinstance(workflow_state, Mapping):
        value = str(workflow_state.get("start_month") or "")
        if value:
            return value
    return None


def _completed_months(selection: Mapping[str, Any]) -> set[str]:
    values = selection.get("completed_months") or []
    return {str(value) for value in values if str(value)}


def _is_stale_completed_decision(decision: Mapping[str, Any] | None, selection: Mapping[str, Any]) -> bool:
    month = _decision_month(decision)
    if not month:
        return False
    selected_month = str(selection.get("start_month") or "")
    return month in _completed_months(selection) and selected_month and selected_month != month


def _provider_status(latest_decision: Mapping[str, Any] | None, daemon_state: Mapping[str, Any] | None) -> dict[str, Any]:
    reason_code = str((latest_decision or {}).get("reason_code") or (daemon_state or {}).get("last_reason_code") or "")
    next_stage = str((latest_decision or {}).get("next_internal_stage") or (daemon_state or {}).get("last_next_internal_stage") or "")
    provider_calls = int((latest_decision or {}).get("provider_calls") or 0)
    if provider_calls:
        status = "provider_calls_recorded"
    elif "provider" in next_stage:
        status = "provider_stage_autonomous_ready"
    else:
        status = "no_provider_work_selected"
    return {
        "contract_type": "manager_provider_runtime_status",
        "status": status,
        "reason_code": reason_code or None,
        "next_internal_stage": next_stage or None,
        "provider_calls_latest_decision": provider_calls,
        "dispatch_performed_latest_decision": bool((latest_decision or {}).get("dispatch_performed", False)),
    }


def _gated_scope_status() -> dict[str, Any]:
    return {
        "provider_acquisition": {
            "status": "autonomous_historical_acquisition_after_payload_preparation",
            "required_contracts": ["manager_request", "component_completion_receipt", "manager_stage_coverage"],
        },
        "model_activation": {
            "status": "execution_shadow_cycle_selection_required_not_manager_owned",
            "required_contracts": ["promotion_eligibility_decision", "promotion_readiness_record", "execution_shadow_cycle_selection"],
            "decision_actor": "trading-execution",
            "owner_action_required_by_default": False,
            "mutation_performed_by_status_surface": False,
        },
        "storage_lifecycle_mutation": {
            "status": "rule_evaluated_lifecycle_policy_and_protected_checks_required",
            "required_contracts": ["storage_lifecycle_request", "storage_lifecycle_policy", "protected_set_clearance", "storage_lifecycle_receipt"],
            "agent_storage_lifecycle_decision_role": "policy_decision_evidence_not_owner_approval",
            "owner_action_required_by_default": False,
            "mutation_performed_by_status_surface": False,
        },
        "broker_order_fill_account_mutation": {
            "status": "out_of_scope_for_historical_modeling",
            "mutation_performed_by_status_surface": False,
        },
    }


def _open_operational_items(
    *,
    state_file: FileStatus,
    decision_log_file: FileStatus,
    lock: LockStatus,
    recommended_flags_present: bool,
    workflow: WorkflowCheckpointStatus,
) -> tuple[str, ...]:
    items: list[str] = []
    if not recommended_flags_present:
        items.append("review_systemd_template_flags")
    if not state_file.exists:
        items.append("start_service_or_run_one_shot_smoke_to_create_daemon_state")
    if not decision_log_file.exists:
        items.append("start_service_or_run_one_shot_smoke_to_create_decision_log")
    if lock.status == "stale":
        items.append("remove_or_replace_stale_scheduler_lock_before_service_start")
    if workflow.exists and not workflow.terminal_complete and workflow.next_stage_status == "blocked":
        items.append("resolve_current_workflow_blocked_stage")
    return tuple(items)


def collect_historical_scheduler_status(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    state_path: Path = DEFAULT_STATE_PATH,
    lock_path: Path = DEFAULT_LOCK_PATH,
    decision_log_path: Path = DEFAULT_DECISION_LOG_PATH,
    service_template_path: Path = DEFAULT_SERVICE_TEMPLATE_PATH,
    service_env_path: Path = DEFAULT_SERVICE_ENV_PATH,
    daemon_wrapper_path: Path = DEFAULT_DAEMON_WRAPPER_PATH,
) -> HistoricalSchedulerStatus:
    """Collect a read-only status snapshot for service operation review."""

    state_file = _file_status(state_path)
    decision_log_file = _file_status(decision_log_path)
    daemon_state = _read_json_object(state_path)
    latest_decision, decision_log_rows = _latest_jsonl_object(decision_log_path)
    auto_work_selection = select_next_historical_work(storage_root=storage_root).summary_row()
    stale_completed_decision = _is_stale_completed_decision(latest_decision, auto_work_selection)
    current_decision = None if stale_completed_decision else latest_decision
    state_month = str((daemon_state or {}).get("start_month") or "")
    selected_month = str(auto_work_selection.get("start_month") or "")
    stale_completed_state = bool(
        state_month in _completed_months(auto_work_selection) and selected_month and selected_month != state_month
    )
    if stale_completed_state:
        state_month = ""
    current_month = str(
        state_month
        or (current_decision or {}).get("start_month")
        or selected_month
        or ""
    ) or None
    workflow = _workflow_checkpoint_status(_workflow_state_path(storage_root, current_month))
    lock = _lock_status(lock_path)
    service_template = _file_status(service_template_path)
    service_env = _file_status(service_env_path)
    daemon_wrapper = _file_status(daemon_wrapper_path)
    flags_present, missing_flags = _service_flags(service_template_path)
    current_daemon_state = None if stale_completed_state else daemon_state
    provider_status = _provider_status(current_decision, current_daemon_state)
    blocked_reason = None
    if current_decision and current_decision.get("decision_status") == "backoff":
        blocked_reason = str(current_decision.get("reason") or current_decision.get("reason_code") or "") or None
    current_stage = workflow.next_stage_id or str((current_decision or {}).get("selected_work") or "") or None
    if current_stage is None and current_month:
        current_stage = "prepare_layer_one_historical_training_batch" if not workflow.exists else "historical_work_selected"
    current_next_internal_stage = str((current_decision or {}).get("next_internal_stage") or workflow.next_stage_type or "") or None
    current_lock_plan = (current_decision or {}).get("lock_plan")
    if not isinstance(current_lock_plan, Mapping):
        current_lock_plan = scheduler_lock_plan(
            month=current_month,
            selected_work=current_stage,
            next_internal_stage=current_next_internal_stage,
        )
    service_runtime_ready = bool(
        service_template.exists
        and service_env.exists
        and daemon_wrapper.exists
        and flags_present
        and lock.status in {"absent", "active"}
    )
    operational_items = _open_operational_items(
        state_file=state_file,
        decision_log_file=decision_log_file,
        lock=lock,
        recommended_flags_present=flags_present,
        workflow=workflow,
    )
    if not service_runtime_ready:
        recommended_next_action = "fix_service_template_or_runtime_files_before_host_activation"
    elif operational_items:
        recommended_next_action = operational_items[0]
    elif lock.status == "active":
        recommended_next_action = "observe_service_status_and_decision_log"
    else:
        recommended_next_action = "operator_may_enable_or_restart_service_after_review"
    reported_daemon_state = daemon_state
    if stale_completed_state and daemon_state is not None:
        reported_daemon_state = dict(daemon_state)
        reported_daemon_state.pop("last_next_internal_stage", None)
        reported_daemon_state["superseded_by_auto_work_selection"] = True
    if stale_completed_decision:
        latest_decision = None
    elif latest_decision is not None:
        latest_decision = dict(latest_decision)
        latest_decision["decision_log_row_count"] = decision_log_rows
    return HistoricalSchedulerStatus(
        contract_type="manager_historical_scheduler_status",
        generated_utc=_now_utc(),
        service_runtime_ready=service_runtime_ready,
        recommended_next_action=recommended_next_action,
        current_month=current_month,
        current_stage=current_stage,
        blocked_reason=blocked_reason,
        state_file=state_file,
        decision_log_file=decision_log_file,
        lock=lock,
        lock_plan=dict(current_lock_plan),
        service_template=service_template,
        service_env=service_env,
        daemon_wrapper=daemon_wrapper,
        recommended_service_flags_present=flags_present,
        missing_service_flags=missing_flags,
        daemon_state=reported_daemon_state,
        latest_decision=latest_decision,
        auto_work_selection=auto_work_selection,
        workflow_checkpoint=workflow,
        failure_summary=_failure_summary(storage_root),
        provider_status=provider_status,
        gated_scope_status=_gated_scope_status(),
        open_operational_items=operational_items,
    )


def write_historical_scheduler_status(status: HistoricalSchedulerStatus, *, output: TextIO) -> None:
    json.dump(status.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect historical scheduler service status without mutating runtime state.")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--lock-path", type=Path, default=DEFAULT_LOCK_PATH)
    parser.add_argument("--decision-log-path", type=Path, default=DEFAULT_DECISION_LOG_PATH)
    parser.add_argument("--service-template-path", type=Path, default=DEFAULT_SERVICE_TEMPLATE_PATH)
    parser.add_argument("--service-env-path", type=Path, default=DEFAULT_SERVICE_ENV_PATH)
    parser.add_argument("--daemon-wrapper-path", type=Path, default=DEFAULT_DAEMON_WRAPPER_PATH)
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
    write_historical_scheduler_status(status, output=sys.stdout)
    return 0


__all__ = [
    "HistoricalSchedulerStatus",
    "LockStatus",
    "WorkflowCheckpointStatus",
    "collect_historical_scheduler_status",
    "write_historical_scheduler_status",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

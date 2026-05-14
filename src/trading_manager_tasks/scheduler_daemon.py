"""Persistent historical-training scheduler daemon.

This module turns the one-shot scheduler tick into a resumable background loop.
It persists a small state checkpoint after every iteration, keeps a single-instance
lock, appends decision JSONL for operations review, and still delegates actual
work admission to ``trading_manager_tasks.scheduler``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from .request_handoff import DEFAULT_TRADING_DATA_SRC
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import (
    DEFAULT_MARKET_HOURS_PROTECTION_ENABLED,
    DEFAULT_MAX_LOAD_PER_CPU,
    DEFAULT_MIN_AVAILABLE_MEMORY_MB,
    DEFAULT_MIN_FREE_DISK_GB,
    SchedulerConfig,
    SchedulerDecision,
    run_scheduler_once,
)

DEFAULT_RUNTIME_DIR = Path("storage/runtime")
DEFAULT_STATE_PATH = DEFAULT_RUNTIME_DIR / "historical_scheduler_state.json"
DEFAULT_LOCK_PATH = DEFAULT_RUNTIME_DIR / "historical_scheduler.lock"
DEFAULT_DECISION_LOG_PATH = DEFAULT_RUNTIME_DIR / "historical_scheduler_decisions.jsonl"
DEFAULT_INTERVAL_SECONDS = 300.0
DEFAULT_STALE_LOCK_SECONDS = 6 * 60 * 60
DEFAULT_DRAIN_MAX_STEPS = 50
DEFAULT_DRAIN_MAX_SECONDS = 300.0
DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT = "trading-storage-dashboard-read-model-refresh.service"
WORKFLOW_STATE_GLOB = "model_training_workflow_state_*.json"


def next_month(month: str) -> str:
    """Return the next YYYY-MM month for chronological service progression."""

    year_text, month_text = month.split("-", 1)
    year = int(year_text)
    month_number = int(month_text)
    if month_number < 1 or month_number > 12:
        raise ValueError(f"invalid month: {month}")
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _month_from_workflow_state_path(path: Path) -> str | None:
    stem = path.stem
    prefix = "model_training_workflow_state_"
    if not stem.startswith(prefix):
        return None
    month = stem.removeprefix(prefix)
    parts = month.split("-")
    if len(parts) != 2:
        return None
    year_text, month_text = parts
    if len(year_text) != 4 or len(month_text) != 2 or not year_text.isdigit() or not month_text.isdigit():
        return None
    month_number = int(month_text)
    if month_number < 1 or month_number > 12:
        return None
    return month


def _workflow_payload_is_complete(payload: dict[str, Any]) -> bool:
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        return False
    statuses = [stage.get("status") for stage in stages if isinstance(stage, dict)]
    return bool(statuses) and all(status in {"succeeded", "not_applicable"} for status in statuses)


@dataclass(frozen=True)
class HistoricalWorkSelection:
    """Service bootstrap decision for the next historical workflow month."""

    contract_type: str = "manager_historical_work_selection"
    start_month: str = "2016-01"
    end_month: str = "2016-01"
    reason_code: str = "no_prior_workflow_state"
    completed_months: tuple[str, ...] = ()
    open_months: tuple[str, ...] = ()

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["completed_months"] = list(self.completed_months)
        row["open_months"] = list(self.open_months)
        return row


def select_next_historical_work(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    default_start_month: str = "2016-01",
    default_end_month: str = "2016-01",
) -> HistoricalWorkSelection:
    """Inspect completed/open workflow checkpoints and choose the next month.

    The service should not need a human to say where to continue. It first
    resumes the earliest open month-scoped workflow state; if every discovered
    month is complete, it advances to the next chronological month after the
    latest complete state; if no workflow state exists, it starts from the
    configured default bootstrap month.
    """

    runtime_root = storage_root / "runtime"
    completed: list[str] = []
    open_months: list[str] = []
    if runtime_root.exists():
        for path in sorted(runtime_root.glob(WORKFLOW_STATE_GLOB)):
            month = _month_from_workflow_state_path(path)
            if month is None:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                open_months.append(month)
                continue
            state_month = str(payload.get("start_month") or month)
            if state_month != month:
                month = state_month
            if _workflow_payload_is_complete(payload):
                completed.append(month)
            else:
                open_months.append(month)

    completed_tuple = tuple(sorted(set(completed)))
    open_tuple = tuple(sorted(set(open_months)))
    if open_tuple:
        selected = open_tuple[0]
        return HistoricalWorkSelection(
            start_month=selected,
            end_month=selected,
            reason_code="resume_earliest_open_workflow_state",
            completed_months=completed_tuple,
            open_months=open_tuple,
        )
    if completed_tuple:
        selected = next_month(completed_tuple[-1])
        return HistoricalWorkSelection(
            start_month=selected,
            end_month=selected,
            reason_code="advance_after_latest_completed_workflow_state",
            completed_months=completed_tuple,
            open_months=open_tuple,
        )
    return HistoricalWorkSelection(
        start_month=default_start_month,
        end_month=default_end_month,
        reason_code="no_prior_workflow_state",
        completed_months=completed_tuple,
        open_months=open_tuple,
    )


@dataclass(frozen=True)
class SchedulerDaemonState:
    """Durable checkpoint for the historical-training scheduler daemon."""

    contract_type: str = "manager_scheduler_daemon_state"
    daemon_id: str = "manager_historical_training_scheduler"
    resume_supported: bool = True
    start_month: str = "2016-01"
    end_month: str = "2016-01"
    total_ticks: int = 0
    successful_ticks: int = 0
    backoff_ticks: int = 0
    failed_ticks: int = 0
    consecutive_errors: int = 0
    last_tick_started_utc: str | None = None
    last_tick_completed_utc: str | None = None
    last_decision_status: str | None = None
    last_reason_code: str | None = None
    last_next_internal_stage: str | None = None
    last_error: str | None = None
    updated_utc: str | None = None
    service_managed: bool = True
    service_manager: str = "systemd"
    last_work_selection_reason: str | None = None
    last_completed_months: tuple[str, ...] = ()
    last_open_months: tuple[str, ...] = ()

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["last_completed_months"] = list(self.last_completed_months)
        row["last_open_months"] = list(self.last_open_months)
        return row


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_daemon_state(
    path: Path,
    *,
    start_month: str,
    end_month: str,
    resume_month_cursor: bool = False,
) -> SchedulerDaemonState:
    """Load a checkpoint if present; otherwise create an initial state.

    ``resume_month_cursor`` preserves the checkpoint's month scope even when the
    service template still carries the original bootstrap month. This is the
    normal system-service mode after automatic chronological advancement.
    """

    if not path.exists():
        return SchedulerDaemonState(start_month=start_month, end_month=end_month, updated_utc=utc_now_iso())
    payload = json.loads(path.read_text(encoding="utf-8"))
    state = SchedulerDaemonState(**payload)
    state = replace(
        state,
        last_completed_months=tuple(state.last_completed_months),
        last_open_months=tuple(state.last_open_months),
    )
    if resume_month_cursor:
        return state
    if state.start_month != start_month or state.end_month != end_month:
        return replace(state, start_month=start_month, end_month=end_month, updated_utc=utc_now_iso())
    return state


def write_daemon_state(path: Path, state: SchedulerDaemonState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def apply_auto_work_selection(
    state: SchedulerDaemonState,
    *,
    storage_root: Path,
    default_start_month: str,
    default_end_month: str,
) -> SchedulerDaemonState:
    """Align daemon scope with the currently selected historical work.

    The resident service is not the only actor allowed to complete safe
    historical workflow stages. Operator-reviewed provider dispatches and
    repair/smoke runs can advance month-scoped workflow checkpoints while the
    daemon is sleeping. Re-select before each tick so the service resumes the
    earliest open month or jumps past externally completed months instead of
    walking one already-complete month per interval.
    """

    selection = select_next_historical_work(
        storage_root=storage_root,
        default_start_month=default_start_month,
        default_end_month=default_end_month,
    )
    scope_changed = state.start_month != selection.start_month or state.end_month != selection.end_month
    selection_changed = (
        state.last_work_selection_reason != selection.reason_code
        or state.last_completed_months != selection.completed_months
        or state.last_open_months != selection.open_months
    )
    if not scope_changed and not selection_changed:
        return state
    return replace(
        state,
        start_month=selection.start_month,
        end_month=selection.end_month,
        last_next_internal_stage="historical_work_selected",
        last_work_selection_reason=selection.reason_code,
        last_completed_months=selection.completed_months,
        last_open_months=selection.open_months,
        updated_utc=utc_now_iso(),
    )


def append_decision_log(path: Path, decision: SchedulerDecision) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision.summary_row(), sort_keys=True) + "\n")


def _process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def acquire_daemon_lock(path: Path, *, stale_after_seconds: int = DEFAULT_STALE_LOCK_SECONDS) -> None:
    """Create a single-instance lock, immediately replacing dead-PID locks.

    Age gating is only for malformed locks that do not identify a dead owner. If
    the lock records a PID and that process no longer exists, keeping the lock
    blocks systemd recovery and creates an alert loop without protecting an
    active daemon instance.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"pid": os.getpid(), "created_utc": utc_now_iso()}
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    except FileExistsError as exc:
        existing_text = path.read_text(encoding="utf-8") if path.exists() else "{}"
        try:
            existing = json.loads(existing_text)
        except json.JSONDecodeError:
            existing = {}
        existing_pid = int(existing.get("pid") or 0)
        age = time.time() - path.stat().st_mtime if path.exists() else 0
        if existing_pid > 0:
            if _process_exists(existing_pid):
                raise RuntimeError(f"scheduler daemon lock is active: {path}") from exc
        elif age < stale_after_seconds:
            raise RuntimeError(f"scheduler daemon lock is active: {path}") from exc
        path.unlink(missing_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, sort_keys=True)
        handle.write("\n")


def release_daemon_lock(path: Path) -> None:
    path.unlink(missing_ok=True)


def update_state_from_decision(
    state: SchedulerDaemonState,
    *,
    started_utc: str,
    completed_utc: str,
    decision: SchedulerDecision,
) -> SchedulerDaemonState:
    return replace(
        state,
        total_ticks=state.total_ticks + 1,
        successful_ticks=state.successful_ticks + (1 if decision.decision_status in {"ready", "executed"} else 0),
        backoff_ticks=state.backoff_ticks + (1 if decision.decision_status == "backoff" else 0),
        consecutive_errors=0,
        last_tick_started_utc=started_utc,
        last_tick_completed_utc=completed_utc,
        last_decision_status=decision.decision_status,
        last_reason_code=decision.reason_code,
        last_next_internal_stage=decision.next_internal_stage,
        last_error=None,
        updated_utc=completed_utc,
    )


def refresh_dashboard_read_models(
    *,
    enabled: bool,
    service_unit: str = DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT,
    command: tuple[str, ...] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Trigger storage-owned dashboard read-model refresh after progress events.

    The manager daemon does not materialize dashboard payloads directly. It only
    nudges the storage-owned oneshot refresh service so the dashboard websocket
    can push the newly materialized ``latest.json`` snapshots immediately after
    each scheduler decision that changes workflow progress.
    """

    if not enabled:
        return {"status": "disabled", "service_unit": service_unit}
    refresh_command = command or ("systemctl", "start", service_unit)
    try:
        completed = subprocess.run(
            refresh_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - defensive operational path.
        return {
            "status": "failed",
            "service_unit": service_unit,
            "command": list(refresh_command),
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "status": "succeeded" if completed.returncode == 0 else "failed",
        "service_unit": service_unit,
        "command": list(refresh_command),
        "return_code": completed.returncode,
        "stdout": completed.stdout[-1000:],
        "stderr": completed.stderr[-1000:],
    }


def _decision_should_continue_drain(decision: SchedulerDecision, *, advanced_month: bool) -> bool:
    if decision.decision_status == "executed":
        return True
    if advanced_month:
        return True
    return False


def update_state_from_error(
    state: SchedulerDaemonState,
    *,
    started_utc: str,
    completed_utc: str,
    error: BaseException,
) -> SchedulerDaemonState:
    return replace(
        state,
        total_ticks=state.total_ticks + 1,
        failed_ticks=state.failed_ticks + 1,
        consecutive_errors=state.consecutive_errors + 1,
        last_tick_started_utc=started_utc,
        last_tick_completed_utc=completed_utc,
        last_decision_status="error",
        last_reason_code="scheduler_iteration_error",
        last_next_internal_stage="historical_training_work_loop",
        last_error=f"{type(error).__name__}: {error}",
        updated_utc=completed_utc,
    )


def run_daemon_loop(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    state_path: Path = DEFAULT_STATE_PATH,
    lock_path: Path = DEFAULT_LOCK_PATH,
    decision_log_path: Path = DEFAULT_DECISION_LOG_PATH,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    max_iterations: int | None = None,
    execute_safe_preparation: bool = False,
    execute_safe_offline_stages: bool = False,
    execute_autonomous_provider_stages: bool = False,
    provider_stage_next_limit: int = 5,
    provider_stage_max_workers: int = 4,
    selected_target_symbol: str | None = None,
    auto_select_next_work: bool = False,
    advance_month_on_complete: bool = False,
    drain_ready_stages: bool = False,
    drain_max_steps: int = DEFAULT_DRAIN_MAX_STEPS,
    drain_max_seconds: float = DEFAULT_DRAIN_MAX_SECONDS,
    refresh_dashboard_on_decision: bool = False,
    dashboard_refresh_service_unit: str = DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT,
    dashboard_refresh_command: tuple[str, ...] | None = None,
    config: SchedulerConfig = SchedulerConfig(),
    output: TextIO | None = None,
) -> SchedulerDaemonState:
    """Run the persistent scheduler loop and return the latest checkpoint.

    ``max_iterations`` is provided for tests, smoke runs, and one-shot service
    validation. ``None`` means run until the process is stopped by the service
    manager.
    """

    acquire_daemon_lock(lock_path)
    state = load_daemon_state(
        state_path,
        start_month=start_month,
        end_month=end_month,
        resume_month_cursor=advance_month_on_complete,
    )
    if auto_select_next_work:
        state = apply_auto_work_selection(
            state,
            storage_root=storage_root,
            default_start_month=start_month,
            default_end_month=end_month,
        )
    active_start_month = state.start_month
    active_end_month = state.end_month
    iterations = 0
    try:
        while max_iterations is None or iterations < max_iterations:
            drain_started_monotonic = time.monotonic()
            drain_steps = 0
            while max_iterations is None or iterations < max_iterations:
                if auto_select_next_work:
                    state = apply_auto_work_selection(
                        state,
                        storage_root=storage_root,
                        default_start_month=active_start_month,
                        default_end_month=active_end_month,
                    )
                    active_start_month = state.start_month
                    active_end_month = state.end_month
                started = utc_now_iso()
                should_continue_drain = False
                try:
                    decision = run_scheduler_once(
                        config=config,
                        start_month=active_start_month,
                        end_month=active_end_month,
                        storage_root=storage_root,
                        component_src_root=component_src_root,
                        execute_safe_preparation=execute_safe_preparation,
                        execute_safe_offline_stages=execute_safe_offline_stages,
                        execute_autonomous_provider_stages=execute_autonomous_provider_stages,
                        provider_stage_next_limit=provider_stage_next_limit,
                        provider_stage_max_workers=provider_stage_max_workers,
                        selected_target_symbol=selected_target_symbol,
                    )
                    append_decision_log(decision_log_path, decision)
                    completed = utc_now_iso()
                    state = update_state_from_decision(state, started_utc=started, completed_utc=completed, decision=decision)
                    advanced_month = False
                    if advance_month_on_complete and decision.reason_code == "month_workflow_complete" and active_start_month == active_end_month:
                        advanced_month = True
                        advanced_month_value = next_month(active_end_month)
                        active_start_month = advanced_month_value
                        active_end_month = advanced_month_value
                        state = replace(
                            state,
                            start_month=advanced_month_value,
                            end_month=advanced_month_value,
                            last_next_internal_stage="chronological_month_advanced",
                            updated_utc=completed,
                        )
                    if decision.decision_status == "executed" or advanced_month:
                        refresh_dashboard_read_models(
                            enabled=refresh_dashboard_on_decision,
                            service_unit=dashboard_refresh_service_unit,
                            command=dashboard_refresh_command,
                        )
                    should_continue_drain = _decision_should_continue_drain(decision, advanced_month=advanced_month)
                    if output is not None:
                        output.write(json.dumps(decision.summary_row(), sort_keys=True) + "\n")
                        output.flush()
                except Exception as exc:  # pragma: no cover - exercised via direct state helper tests.
                    completed = utc_now_iso()
                    state = update_state_from_error(state, started_utc=started, completed_utc=completed, error=exc)
                    if output is not None:
                        output.write(json.dumps(state.summary_row(), sort_keys=True) + "\n")
                        output.flush()
                write_daemon_state(state_path, state)
                iterations += 1
                drain_steps += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break
                if not drain_ready_stages:
                    break
                if drain_steps >= max(1, drain_max_steps):
                    break
                if time.monotonic() - drain_started_monotonic >= max(0.0, drain_max_seconds):
                    break
                if not should_continue_drain:
                    break
            if max_iterations is not None and iterations >= max_iterations:
                break
            if interval_seconds > 0:
                time.sleep(interval_seconds)
    finally:
        release_daemon_lock(lock_path)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the persistent historical-training automation scheduler daemon.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--component-src-root", type=Path, default=DEFAULT_TRADING_DATA_SRC)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--lock-path", type=Path, default=DEFAULT_LOCK_PATH)
    parser.add_argument("--decision-log-path", type=Path, default=DEFAULT_DECISION_LOG_PATH)
    parser.add_argument("--interval-seconds", type=float, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--max-iterations", type=int, help="Run a bounded number of daemon iterations for smoke tests.")
    parser.add_argument("--once", action="store_true", help="Alias for --max-iterations 1.")
    parser.add_argument("--execute-safe-preparation", action="store_true", help="Allow safe task-key preparation. No provider calls are performed.")
    parser.add_argument("--execute-safe-offline-stages", action="store_true", help="Allow one ready offline workflow stage per tick. Provider stages use --execute-autonomous-provider-stages instead.")
    parser.add_argument("--execute-autonomous-provider-stages", action="store_true", help="Allow one bounded autonomous provider-dispatch/reconcile slice per tick when provider acquisition is ready.")
    parser.add_argument("--provider-stage-next-limit", type=int, default=5, help="Maximum provider requests to dispatch in one daemon tick.")
    parser.add_argument("--provider-stage-max-workers", type=int, default=4, help="Maximum dynamic provider worker threads in one daemon tick.")
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for Layer 3+ six-month dataset units.")
    parser.add_argument("--auto-select-next-work", action="store_true", help="Inspect month-scoped workflow states and choose the next open or planned chronological month automatically.")
    parser.add_argument("--advance-month-on-complete", action="store_true", help="Advance the daemon month cursor automatically after a month workflow reaches terminal completion.")
    parser.add_argument("--drain-ready-stages", action="store_true", help="After a scheduler-owned task completes, immediately continue to the next runnable safe task until no task is ready or drain limits are reached.")
    parser.add_argument("--drain-max-steps", type=int, default=DEFAULT_DRAIN_MAX_STEPS, help="Maximum scheduler decisions to run back-to-back inside one drain cycle.")
    parser.add_argument("--drain-max-seconds", type=float, default=DEFAULT_DRAIN_MAX_SECONDS, help="Maximum wall-clock seconds for one back-to-back drain cycle.")
    parser.add_argument("--refresh-dashboard-on-decision", action="store_true", help="Trigger the storage-owned dashboard read-model refresh service after each executed scheduler decision.")
    parser.add_argument("--dashboard-refresh-service-unit", default=DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT, help="systemd service unit to start for event-driven dashboard read-model refresh.")
    parser.add_argument("--disable-market-hours-protection", action="store_true", help="Allow historical training during regular US equity market hours while no production model is active. Provider, promotion, and broker gates remain hard.")
    parser.add_argument("--min-available-memory-mb", type=int, default=DEFAULT_MIN_AVAILABLE_MEMORY_MB)
    parser.add_argument("--min-free-disk-gb", type=float, default=DEFAULT_MIN_FREE_DISK_GB)
    parser.add_argument("--max-load-per-cpu", type=float, default=DEFAULT_MAX_LOAD_PER_CPU)
    args = parser.parse_args(argv)

    max_iterations = 1 if args.once else args.max_iterations
    config = SchedulerConfig(
        market_hours_protection_enabled=not args.disable_market_hours_protection and DEFAULT_MARKET_HOURS_PROTECTION_ENABLED,
        min_available_memory_mb=args.min_available_memory_mb,
        min_free_disk_gb=args.min_free_disk_gb,
        max_load_per_cpu=args.max_load_per_cpu,
    )
    state = run_daemon_loop(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        component_src_root=args.component_src_root,
        state_path=args.state_path,
        lock_path=args.lock_path,
        decision_log_path=args.decision_log_path,
        interval_seconds=args.interval_seconds,
        max_iterations=max_iterations,
        execute_safe_preparation=args.execute_safe_preparation,
        execute_safe_offline_stages=args.execute_safe_offline_stages,
        execute_autonomous_provider_stages=args.execute_autonomous_provider_stages,
        provider_stage_next_limit=args.provider_stage_next_limit,
        provider_stage_max_workers=args.provider_stage_max_workers,
        selected_target_symbol=args.target_symbol,
        auto_select_next_work=args.auto_select_next_work,
        advance_month_on_complete=args.advance_month_on_complete,
        drain_ready_stages=args.drain_ready_stages,
        drain_max_steps=args.drain_max_steps,
        drain_max_seconds=args.drain_max_seconds,
        refresh_dashboard_on_decision=args.refresh_dashboard_on_decision,
        dashboard_refresh_service_unit=args.dashboard_refresh_service_unit,
        config=config,
        output=sys.stdout,
    )
    print(json.dumps(state.summary_row(), indent=2, sort_keys=True), file=sys.stderr)
    return 0


__all__ = [
    "DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT",
    "DEFAULT_DECISION_LOG_PATH",
    "DEFAULT_DRAIN_MAX_SECONDS",
    "DEFAULT_DRAIN_MAX_STEPS",
    "DEFAULT_INTERVAL_SECONDS",
    "DEFAULT_LOCK_PATH",
    "DEFAULT_RUNTIME_DIR",
    "DEFAULT_STATE_PATH",
    "HistoricalWorkSelection",
    "SchedulerDaemonState",
    "acquire_daemon_lock",
    "apply_auto_work_selection",
    "append_decision_log",
    "load_daemon_state",
    "release_daemon_lock",
    "next_month",
    "refresh_dashboard_read_models",
    "run_daemon_loop",
    "select_next_historical_work",
    "update_state_from_decision",
    "update_state_from_error",
    "write_daemon_state",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

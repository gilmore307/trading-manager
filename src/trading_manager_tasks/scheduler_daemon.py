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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO
from zoneinfo import ZoneInfo

from .request_handoff import DEFAULT_TRADING_DATA_SRC
from .scheduler_locks import DEFAULT_DAEMON_LOCK_PATH
from .model_training_state import advance_workflow_state
from .model_training_workflow import FOUNDATION_CATCH_UP_STAGE_TYPES, MONTHLY_SUBSTRATE_LAYERS, build_model_training_workflow_plan
from .request_payloads import DEFAULT_STORAGE_ROOT
from .source_existing_bootstrap import run_source_existing_bootstrap
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
DEFAULT_LOCK_PATH = DEFAULT_DAEMON_LOCK_PATH
DEFAULT_DECISION_LOG_PATH = DEFAULT_RUNTIME_DIR / "historical_scheduler_decisions.jsonl"
DEFAULT_INTERVAL_SECONDS = 300.0
DEFAULT_STALE_LOCK_SECONDS = 6 * 60 * 60
DEFAULT_DRAIN_MAX_STEPS = 50
DEFAULT_DRAIN_MAX_SECONDS = 300.0
DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT = "trading-storage-dashboard-read-model-refresh.service"
WORKFLOW_STATE_GLOB = "model_training_workflow_state_*.json"
DEFAULT_MONTH_INGEST_WORKERS = 3
COMPLETED_MONTH_CUTOFF_TZ = "America/New_York"


def previous_month(month: str) -> str:
    """Return the previous YYYY-MM month."""

    year_text, month_text = month.split("-", 1)
    year = int(year_text)
    month_number = int(month_text)
    if month_number < 1 or month_number > 12:
        raise ValueError(f"invalid month: {month}")
    if month_number == 1:
        return f"{year - 1:04d}-12"
    return f"{year:04d}-{month_number - 1:02d}"


def completed_historical_month_cutoff(now: datetime | None = None) -> str:
    """Return latest completed calendar month allowed for provider downloads.

    Historical provider downloads must not target the current in-progress month.
    Runtime uses the operator/project timezone so a new month does not open early
    at UTC midnight while the US/Eastern trading day is still in the prior month.
    """

    current = now or datetime.now(ZoneInfo(COMPLETED_MONTH_CUTOFF_TZ))
    if current.tzinfo is None:
        current = current.replace(tzinfo=ZoneInfo(COMPLETED_MONTH_CUTOFF_TZ))
    current_local = current.astimezone(ZoneInfo(COMPLETED_MONTH_CUTOFF_TZ))
    return previous_month(current_local.strftime("%Y-%m"))


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


def _workflow_payload_foundation_catch_up_complete(payload: dict[str, Any]) -> bool:
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        return False
    required = {
        (layer, stage_type)
        for layer in MONTHLY_SUBSTRATE_LAYERS
        for stage_type in FOUNDATION_CATCH_UP_STAGE_TYPES
    }
    satisfied: set[tuple[int, str]] = set()
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        try:
            layer = int(stage.get("layer"))
        except (TypeError, ValueError):
            continue
        stage_type = str(stage.get("stage_type") or "")
        if (layer, stage_type) in required and stage.get("status") in {"succeeded", "not_applicable"}:
            satisfied.add((layer, stage_type))
    return required <= satisfied


def _workflow_payload_is_complete(payload: dict[str, Any]) -> bool:
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        return False
    statuses = [stage.get("status") for stage in stages if isinstance(stage, dict)]
    if bool(statuses) and all(status in {"succeeded", "not_applicable"} for status in statuses):
        return True
    return _workflow_payload_foundation_catch_up_complete(payload)


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
    max_month: str | None = None,
) -> HistoricalWorkSelection:
    """Inspect completed/open workflow checkpoints and choose the next month.

    The service should not need a human to say where to continue. It first
    resumes the earliest open month-scoped workflow state; if every discovered
    month is complete, it advances to the next chronological month after the
    latest complete state; if no workflow state exists, it starts from the
    configured default bootstrap month.
    """

    max_month = max_month or completed_historical_month_cutoff()
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
    eligible_open_tuple = tuple(month for month in open_tuple if month <= max_month)
    if eligible_open_tuple:
        selected = eligible_open_tuple[0]
        return HistoricalWorkSelection(
            start_month=selected,
            end_month=selected,
            reason_code="resume_earliest_open_workflow_state",
            completed_months=completed_tuple,
            open_months=open_tuple,
        )
    if completed_tuple:
        selected = next_month(completed_tuple[-1])
        if selected > max_month:
            capped_month = min(completed_tuple[-1], max_month)
            return HistoricalWorkSelection(
                start_month=capped_month,
                end_month=capped_month,
                reason_code="waiting_for_next_calendar_month_to_complete",
                completed_months=completed_tuple,
                open_months=open_tuple,
            )
        return HistoricalWorkSelection(
            start_month=selected,
            end_month=selected,
            reason_code="advance_after_latest_completed_workflow_state",
            completed_months=completed_tuple,
            open_months=open_tuple,
        )
    if default_start_month > max_month:
        return HistoricalWorkSelection(
            start_month=max_month,
            end_month=max_month,
            reason_code="waiting_for_next_calendar_month_to_complete",
            completed_months=completed_tuple,
            open_months=open_tuple,
        )
    return HistoricalWorkSelection(
        start_month=default_start_month,
        end_month=min(default_end_month, max_month),
        reason_code="no_prior_workflow_state",
        completed_months=completed_tuple,
        open_months=open_tuple,
    )


def select_month_ingest_worker_months(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    default_start_month: str = "2016-01",
    worker_count: int = DEFAULT_MONTH_INGEST_WORKERS,
    max_month: str | None = None,
) -> tuple[str, ...]:
    """Return up to `worker_count` month-scoped ingest lanes to work now.

    This selector is intentionally narrower than ``select_next_historical_work``:
    it only considers the Layer 1/2 foundation substrate as ingest work. Months
    whose Layer 1/2 data acquisition and feature generation are complete are not
    assigned to month-ingest workers even if their later Layer 3+ stages are
    blocked behind foundation catch-up. New months are appended after the latest
    known month so all three ingest lanes can stay filled by default.
    """

    worker_count = max(1, int(worker_count))
    max_month = max_month or completed_historical_month_cutoff()
    runtime_root = storage_root / "runtime"
    known_months: list[str] = []
    open_ingest_months: list[str] = []
    if runtime_root.exists():
        for path in sorted(runtime_root.glob(WORKFLOW_STATE_GLOB)):
            month = _month_from_workflow_state_path(path)
            if month is None:
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                known_months.append(month)
                open_ingest_months.append(month)
                continue
            state_month = str(payload.get("start_month") or month)
            month = state_month if state_month else month
            known_months.append(month)
            if not _workflow_payload_foundation_catch_up_complete(payload):
                open_ingest_months.append(month)

    selected: list[str] = []
    for month in sorted(set(open_ingest_months)):
        if month > max_month:
            continue
        if month not in selected:
            selected.append(month)
        if len(selected) >= worker_count:
            return tuple(selected)

    if known_months:
        next_candidate = next_month(max(known_months))
    else:
        next_candidate = default_start_month
    while len(selected) < worker_count and next_candidate <= max_month:
        if next_candidate not in selected:
            selected.append(next_candidate)
        next_candidate = next_month(next_candidate)
    return tuple(selected)


@dataclass(frozen=True)
class ModelWorkerFoldSelection:
    """Model-worker selection for the next complete non-overlapping six-month fold."""

    contract_type: str = "manager_model_worker_fold_selection"
    fold_id: str = "fold_2016-01_2016-06"
    start_month: str = "2016-01"
    end_month: str = "2016-06"
    fold_months: tuple[str, ...] = ()
    reason_code: str = "no_complete_fold_available"
    state_path: str | None = None

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["fold_months"] = list(self.fold_months)
        return row


def rolling_fold_months(start_month: str, *, month_count: int = 6) -> tuple[str, ...]:
    """Return the inclusive month sequence for one frozen six-month fold."""

    months = [start_month]
    while len(months) < month_count:
        months.append(next_month(months[-1]))
    return tuple(months)


def _advance_fold_start_month(start_month: str, *, month_count: int = 6) -> str:
    """Return the next non-overlapping fold start month."""

    month = start_month
    for _ in range(month_count):
        month = next_month(month)
    return month


def model_worker_fold_state_path(start_month: str, end_month: str, *, root: Path = DEFAULT_RUNTIME_DIR) -> Path:
    """Return the fold-scoped Model Worker checkpoint path."""

    return root / f"model_training_fold_state_{start_month}_{end_month}.json"


def _model_worker_fold_id(start_month: str, end_month: str) -> str:
    return f"fold_{start_month}_{end_month}"


def _workflow_payload_all_stages_complete(payload: dict[str, Any]) -> bool:
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        return False
    statuses = [stage.get("status") for stage in stages if isinstance(stage, dict)]
    return bool(statuses) and all(status in {"succeeded", "not_applicable"} for status in statuses)


def _fold_payload_has_open_model_worker_stage(payload: dict[str, Any]) -> bool:
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        return True
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        if str(stage.get("stage_type") or "") in {"model_generation", "model_evaluation", "promotion_review", "maintenance"} and str(
            stage.get("status") or ""
        ) not in {"succeeded", "not_applicable"}:
            return True
    return False


def _month_foundation_ready(storage_root: Path, month: str) -> bool:
    path = storage_root / "runtime" / f"model_training_workflow_state_{month}.json"
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return _workflow_payload_foundation_catch_up_complete(payload)


def _model_worker_fold_is_ready(storage_root: Path, start_month: str) -> tuple[bool, tuple[str, ...]]:
    months = rolling_fold_months(start_month)
    return all(_month_foundation_ready(storage_root, month) for month in months), months


def select_model_worker_fold(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    default_start_month: str = "2016-01",
    max_month: str | None = None,
) -> ModelWorkerFoldSelection | None:
    """Select the earliest complete non-overlapping six-month fold with open Model Worker work."""

    max_month = max_month or completed_historical_month_cutoff()
    runtime_root = storage_root / "runtime"
    known_months: set[str] = set()
    if runtime_root.exists():
        for path in sorted(runtime_root.glob(WORKFLOW_STATE_GLOB)):
            month = _month_from_workflow_state_path(path)
            if month is not None:
                known_months.add(month)
    if not known_months:
        known_months.add(default_start_month)

    start = min(known_months | {default_start_month})
    last_start = previous_month(previous_month(previous_month(previous_month(previous_month(max_month)))))
    if start > last_start:
        return None
    candidate = start
    while candidate <= last_start:
        ready, months = _model_worker_fold_is_ready(storage_root, candidate)
        end_month = months[-1]
        state_path = model_worker_fold_state_path(candidate, end_month, root=runtime_root)
        if ready:
            if state_path.exists():
                try:
                    payload = json.loads(state_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    payload = {}
                if not _workflow_payload_all_stages_complete(payload) and _fold_payload_has_open_model_worker_stage(payload):
                    return ModelWorkerFoldSelection(
                        fold_id=_model_worker_fold_id(candidate, end_month),
                        start_month=candidate,
                        end_month=end_month,
                        fold_months=months,
                        reason_code="resume_open_model_worker_fold",
                        state_path=str(state_path),
                    )
            else:
                return ModelWorkerFoldSelection(
                    fold_id=_model_worker_fold_id(candidate, end_month),
                    start_month=candidate,
                    end_month=end_month,
                    fold_months=months,
                    reason_code="complete_foundation_fold_ready",
                    state_path=str(state_path),
                )
        candidate = _advance_fold_start_month(candidate)
    return None


def seed_model_worker_fold_state(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    selection: ModelWorkerFoldSelection,
    selected_target_symbol: str | None = None,
) -> Path:
    """Create/refresh a fold-scoped state seeded from completed Layer 1/2 substrate months."""

    state_path = Path(selection.state_path) if selection.state_path else model_worker_fold_state_path(
        selection.start_month, selection.end_month, root=storage_root / "runtime"
    )
    plan = build_model_training_workflow_plan(
        start_month=selection.start_month,
        end_month=selection.end_month,
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=False,
    )
    foundation_stage_ids = [
        stage.stage_id
        for layer in plan.layers
        if layer.layer in MONTHLY_SUBSTRATE_LAYERS
        for stage in layer.stages
        if stage.stage_type in FOUNDATION_CATCH_UP_STAGE_TYPES
    ]
    advance_workflow_state(
        start_month=selection.start_month,
        end_month=selection.end_month,
        storage_root=storage_root,
        state_path=state_path,
        completed_stage_ids=foundation_stage_ids if not state_path.exists() else (),
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=False,
        write=True,
    )
    return state_path


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



def _run_model_worker_decision(
    *,
    storage_root: Path,
    component_src_root: Path,
    config: SchedulerConfig,
    execute_safe_offline_stages: bool,
    selected_target_symbol: str | None,
) -> tuple[ModelWorkerFoldSelection, SchedulerDecision] | None:
    selection = select_model_worker_fold(storage_root=storage_root)
    if selection is None:
        return None
    state_path = seed_model_worker_fold_state(
        storage_root=storage_root,
        selection=selection,
        selected_target_symbol=selected_target_symbol,
    )
    decision = run_scheduler_once(
        config=config,
        start_month=selection.start_month,
        end_month=selection.end_month,
        storage_root=storage_root,
        component_src_root=component_src_root,
        execute_safe_preparation=False,
        execute_safe_offline_stages=execute_safe_offline_stages,
        execute_autonomous_provider_stages=False,
        selected_target_symbol=selected_target_symbol,
        state_path=state_path,
        foundation_catch_up_only=False,
    )
    return selection, decision

def _run_month_ingest_worker_decisions(
    *,
    months: tuple[str, ...],
    config: SchedulerConfig,
    storage_root: Path,
    component_src_root: Path,
    execute_safe_preparation: bool,
    execute_safe_offline_stages: bool,
    execute_autonomous_provider_stages: bool,
    provider_stage_next_limit: int,
    provider_stage_max_workers: int,
    selected_target_symbol: str | None,
) -> list[tuple[str, SchedulerDecision]]:
    if not months:
        return []
    per_lane_next_limit = max(1, (provider_stage_next_limit + len(months) - 1) // len(months))
    per_lane_provider_workers = max(1, provider_stage_max_workers // len(months))

    def run_month(month: str) -> tuple[str, SchedulerDecision]:
        return (
            month,
            run_scheduler_once(
                config=config,
                start_month=month,
                end_month=month,
                storage_root=storage_root,
                component_src_root=component_src_root,
                execute_safe_preparation=execute_safe_preparation,
                execute_safe_offline_stages=execute_safe_offline_stages,
                execute_autonomous_provider_stages=execute_autonomous_provider_stages,
                provider_stage_next_limit=per_lane_next_limit,
                provider_stage_max_workers=per_lane_provider_workers,
                selected_target_symbol=selected_target_symbol,
            ),
        )

    by_month: dict[str, SchedulerDecision] = {}
    with ThreadPoolExecutor(max_workers=len(months)) as executor:
        futures = {executor.submit(run_month, month): month for month in months}
        for future in as_completed(futures):
            month, decision = future.result()
            by_month[month] = decision
    return [(month, by_month[month]) for month in months]


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
    month_ingest_workers: int = 1,
    selected_target_symbol: str | None = None,
    auto_select_next_work: bool = False,
    advance_month_on_complete: bool = False,
    drain_ready_stages: bool = False,
    drain_max_steps: int = DEFAULT_DRAIN_MAX_STEPS,
    drain_max_seconds: float = DEFAULT_DRAIN_MAX_SECONDS,
    refresh_dashboard_on_decision: bool = False,
    dashboard_refresh_service_unit: str = DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT,
    dashboard_refresh_command: tuple[str, ...] | None = None,
    source_existing_bootstrap: bool = True,
    source_bootstrap_database_url: str | None = None,
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
    if source_existing_bootstrap:
        run_source_existing_bootstrap(
            start_month=start_month,
            end_month=completed_historical_month_cutoff(),
            selected_target_symbol=selected_target_symbol,
            storage_root=storage_root,
            database_url=source_bootstrap_database_url,
            write=True,
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
                started = utc_now_iso()
                should_continue_drain = False
                decisions_this_cycle = 0
                try:
                    use_month_ingest_lanes = auto_select_next_work and month_ingest_workers > 1
                    if use_month_ingest_lanes:
                        remaining_iterations = None if max_iterations is None else max_iterations - iterations
                        lane_limit = month_ingest_workers if remaining_iterations is None else min(month_ingest_workers, max(1, remaining_iterations))
                        months = select_month_ingest_worker_months(
                            storage_root=storage_root,
                            default_start_month=active_start_month,
                            worker_count=lane_limit,
                        )
                        decisions = _run_month_ingest_worker_decisions(
                            months=months,
                            config=config,
                            storage_root=storage_root,
                            component_src_root=component_src_root,
                            execute_safe_preparation=execute_safe_preparation,
                            execute_safe_offline_stages=execute_safe_offline_stages,
                            execute_autonomous_provider_stages=execute_autonomous_provider_stages,
                            provider_stage_next_limit=provider_stage_next_limit,
                            provider_stage_max_workers=provider_stage_max_workers,
                            selected_target_symbol=selected_target_symbol,
                        )
                        completed = utc_now_iso()
                        if months:
                            active_start_month = months[0]
                            active_end_month = months[-1]
                            state = replace(
                                state,
                                start_month=active_start_month,
                                end_month=active_end_month,
                                last_next_internal_stage="month_ingest_worker_lanes",
                                last_work_selection_reason="month_ingest_worker_lanes_selected",
                                last_open_months=months,
                                updated_utc=completed,
                            )
                        refresh_needed = False
                        for month, decision in decisions:
                            append_decision_log(decision_log_path, decision)
                            state = update_state_from_decision(state, started_utc=started, completed_utc=completed, decision=decision)
                            state = replace(
                                state,
                                start_month=active_start_month,
                                end_month=active_end_month,
                                last_next_internal_stage="month_ingest_worker_lanes",
                                last_work_selection_reason="month_ingest_worker_lanes_selected",
                                last_open_months=months,
                                updated_utc=completed,
                            )
                            refresh_needed = refresh_needed or decision.decision_status == "executed"
                            should_continue_drain = should_continue_drain or _decision_should_continue_drain(decision, advanced_month=False)
                            decisions_this_cycle += 1
                            if output is not None:
                                row = decision.summary_row()
                                row["worker_month"] = month
                                output.write(json.dumps(row, sort_keys=True) + "\n")
                                output.flush()
                        model_worker_result = _run_model_worker_decision(
                            storage_root=storage_root,
                            component_src_root=component_src_root,
                            config=config,
                            execute_safe_offline_stages=execute_safe_offline_stages,
                            selected_target_symbol=selected_target_symbol,
                        )
                        if model_worker_result is not None:
                            model_selection, model_decision = model_worker_result
                            append_decision_log(decision_log_path, model_decision)
                            completed = utc_now_iso()
                            state = update_state_from_decision(state, started_utc=started, completed_utc=completed, decision=model_decision)
                            state = replace(
                                state,
                                start_month=active_start_month,
                                end_month=active_end_month,
                                last_next_internal_stage="model_worker_1",
                                last_work_selection_reason=model_selection.reason_code,
                                updated_utc=completed,
                            )
                            refresh_needed = refresh_needed or model_decision.decision_status == "executed"
                            should_continue_drain = should_continue_drain or _decision_should_continue_drain(model_decision, advanced_month=False)
                            decisions_this_cycle += 1
                            if output is not None:
                                row = model_decision.summary_row()
                                row["worker_id"] = "model_worker_1"
                                row["fold_id"] = model_selection.fold_id
                                row["fold_months"] = list(model_selection.fold_months)
                                output.write(json.dumps(row, sort_keys=True) + "\n")
                                output.flush()
                        if refresh_needed:
                            refresh_dashboard_read_models(
                                enabled=refresh_dashboard_on_decision,
                                service_unit=dashboard_refresh_service_unit,
                                command=dashboard_refresh_command,
                            )
                    else:
                        if auto_select_next_work:
                            state = apply_auto_work_selection(
                                state,
                                storage_root=storage_root,
                                default_start_month=active_start_month,
                                default_end_month=active_end_month,
                            )
                            active_start_month = state.start_month
                            active_end_month = state.end_month
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
                            advanced_month_value = next_month(active_end_month)
                            if advanced_month_value <= completed_historical_month_cutoff():
                                advanced_month = True
                                active_start_month = advanced_month_value
                                active_end_month = advanced_month_value
                                state = replace(
                                    state,
                                    start_month=advanced_month_value,
                                    end_month=advanced_month_value,
                                    last_next_internal_stage="chronological_month_advanced",
                                    updated_utc=completed,
                                )
                            else:
                                state = replace(
                                    state,
                                    last_next_internal_stage="calendar_month_cutoff_wait",
                                    last_work_selection_reason="waiting_for_next_calendar_month_to_complete",
                                    updated_utc=completed,
                                )
                        if decision.decision_status == "executed" or advanced_month:
                            refresh_dashboard_read_models(
                                enabled=refresh_dashboard_on_decision,
                                service_unit=dashboard_refresh_service_unit,
                                command=dashboard_refresh_command,
                            )
                        should_continue_drain = _decision_should_continue_drain(decision, advanced_month=advanced_month)
                        decisions_this_cycle = 1
                        if output is not None:
                            output.write(json.dumps(decision.summary_row(), sort_keys=True) + "\n")
                            output.flush()
                except Exception as exc:  # pragma: no cover - exercised via direct state helper tests.
                    completed = utc_now_iso()
                    state = update_state_from_error(state, started_utc=started, completed_utc=completed, error=exc)
                    decisions_this_cycle = 1
                    if output is not None:
                        output.write(json.dumps(state.summary_row(), sort_keys=True) + "\n")
                        output.flush()
                write_daemon_state(state_path, state)
                iterations += max(1, decisions_this_cycle)
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
    parser.add_argument("--month-ingest-workers", type=int, default=DEFAULT_MONTH_INGEST_WORKERS, help="Number of month-ingest worker lanes to keep filled for month-scoped acquisition and feature generation.")
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for Layer 3+ six-month dataset units.")
    parser.add_argument("--auto-select-next-work", action="store_true", help="Inspect month-scoped workflow states and choose the next open or planned chronological month automatically.")
    parser.add_argument("--advance-month-on-complete", action="store_true", help="Advance the daemon month cursor automatically after a month workflow reaches terminal completion.")
    parser.add_argument("--drain-ready-stages", action="store_true", help="After a scheduler-owned task completes, immediately continue to the next runnable safe task until no task is ready or drain limits are reached.")
    parser.add_argument("--drain-max-steps", type=int, default=DEFAULT_DRAIN_MAX_STEPS, help="Maximum scheduler decisions to run back-to-back inside one drain cycle.")
    parser.add_argument("--drain-max-seconds", type=float, default=DEFAULT_DRAIN_MAX_SECONDS, help="Maximum wall-clock seconds for one back-to-back drain cycle.")
    parser.add_argument("--refresh-dashboard-on-decision", action="store_true", help="Trigger the storage-owned dashboard read-model refresh service after each executed scheduler decision.")
    parser.add_argument("--dashboard-refresh-service-unit", default=DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT, help="systemd service unit to start for event-driven dashboard read-model refresh.")
    parser.add_argument("--disable-source-existing-bootstrap", action="store_true", help="Disable startup source-existing bootstrap. Default service startup inspects source tables and seeds workflow acquisition state so existing source data is reused.")
    parser.add_argument("--source-bootstrap-database-url", help="Database URL for startup source-existing bootstrap; defaults to OpenClaw database resolution.")
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
        month_ingest_workers=args.month_ingest_workers,
        selected_target_symbol=args.target_symbol,
        auto_select_next_work=args.auto_select_next_work,
        advance_month_on_complete=args.advance_month_on_complete,
        drain_ready_stages=args.drain_ready_stages,
        drain_max_steps=args.drain_max_steps,
        drain_max_seconds=args.drain_max_seconds,
        refresh_dashboard_on_decision=args.refresh_dashboard_on_decision,
        dashboard_refresh_service_unit=args.dashboard_refresh_service_unit,
        source_existing_bootstrap=not args.disable_source_existing_bootstrap,
        source_bootstrap_database_url=args.source_bootstrap_database_url,
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

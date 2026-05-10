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
import sys
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

from .request_handoff import DEFAULT_TRADING_DATA_SRC
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import (
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


@dataclass(frozen=True)
class SchedulerDaemonState:
    """Durable checkpoint for the historical-training scheduler daemon."""

    contract_type: str = "manager_scheduler_daemon_state_v1"
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

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_daemon_state(path: Path, *, start_month: str, end_month: str) -> SchedulerDaemonState:
    """Load a checkpoint if present; otherwise create an initial state."""

    if not path.exists():
        return SchedulerDaemonState(start_month=start_month, end_month=end_month, updated_utc=utc_now_iso())
    payload = json.loads(path.read_text(encoding="utf-8"))
    state = SchedulerDaemonState(**payload)
    if state.start_month != start_month or state.end_month != end_month:
        return replace(state, start_month=start_month, end_month=end_month, updated_utc=utc_now_iso())
    return state


def write_daemon_state(path: Path, state: SchedulerDaemonState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


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
    """Create a single-instance lock, replacing stale locks only."""

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
        if _process_exists(existing_pid) or age < stale_after_seconds:
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
    config: SchedulerConfig = SchedulerConfig(),
    output: TextIO | None = None,
) -> SchedulerDaemonState:
    """Run the persistent scheduler loop and return the latest checkpoint.

    ``max_iterations`` is provided for tests, smoke runs, and one-shot service
    validation. ``None`` means run until the process is stopped by the service
    manager.
    """

    acquire_daemon_lock(lock_path)
    state = load_daemon_state(state_path, start_month=start_month, end_month=end_month)
    iterations = 0
    try:
        while max_iterations is None or iterations < max_iterations:
            started = utc_now_iso()
            try:
                decision = run_scheduler_once(
                    config=config,
                    start_month=start_month,
                    end_month=end_month,
                    storage_root=storage_root,
                    component_src_root=component_src_root,
                    execute_safe_preparation=execute_safe_preparation,
                )
                append_decision_log(decision_log_path, decision)
                completed = utc_now_iso()
                state = update_state_from_decision(state, started_utc=started, completed_utc=completed, decision=decision)
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
    parser.add_argument("--execute-safe-preparation", action="store_true", help="Allow safe Layer 1 task-key preparation. No provider calls are performed.")
    parser.add_argument("--min-available-memory-mb", type=int, default=DEFAULT_MIN_AVAILABLE_MEMORY_MB)
    parser.add_argument("--min-free-disk-gb", type=float, default=DEFAULT_MIN_FREE_DISK_GB)
    parser.add_argument("--max-load-per-cpu", type=float, default=DEFAULT_MAX_LOAD_PER_CPU)
    args = parser.parse_args(argv)

    max_iterations = 1 if args.once else args.max_iterations
    config = SchedulerConfig(
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
        config=config,
        output=sys.stdout,
    )
    print(json.dumps(state.summary_row(), indent=2, sort_keys=True), file=sys.stderr)
    return 0


__all__ = [
    "DEFAULT_DECISION_LOG_PATH",
    "DEFAULT_INTERVAL_SECONDS",
    "DEFAULT_LOCK_PATH",
    "DEFAULT_RUNTIME_DIR",
    "DEFAULT_STATE_PATH",
    "SchedulerDaemonState",
    "acquire_daemon_lock",
    "append_decision_log",
    "load_daemon_state",
    "release_daemon_lock",
    "run_daemon_loop",
    "update_state_from_decision",
    "update_state_from_error",
    "write_daemon_state",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

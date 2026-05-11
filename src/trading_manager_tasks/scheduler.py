"""Capacity-aware manager scheduler gates and first safe work loop.

The scheduler is intentionally conservative. Historical provider acquisition is
an internal training stage, not an external dependency, but provider/API calls
still pass through the internal ``live_call_approval_v1`` safety gate. This tick
can plan or execute safe offline preparation work, but it does not call live
providers, activate models, or touch broker/execution state. Model activation
remains gated by an approving review decision.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Literal, TextIO
from zoneinfo import ZoneInfo

from .historical_training import prepare_layer_one_historical_training_batch
from .model_training_state import advance_workflow_state, next_ready_or_blocked_stage, workflow_state_path_for_month
from .model_training_workflow import LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS, build_model_training_workflow_plan
from .request_handoff import DEFAULT_TRADING_DATA_SRC
from .stage_executor import execute_next_ready_stage
from .request_payloads import DEFAULT_STORAGE_ROOT

NEW_YORK = ZoneInfo("America/New_York")
PROTECTION_START = time(9, 20)
PROTECTION_END = time(16, 10)
DEFAULT_MIN_AVAILABLE_MEMORY_MB = 2048
DEFAULT_MIN_FREE_DISK_GB = 10.0
DEFAULT_MAX_LOAD_PER_CPU = 0.70


@dataclass(frozen=True)
class SchedulerConfig:
    """Runtime gates for one scheduler tick."""

    protected_start_et: str = "09:20"
    protected_end_et: str = "16:10"
    min_available_memory_mb: int = DEFAULT_MIN_AVAILABLE_MEMORY_MB
    min_free_disk_gb: float = DEFAULT_MIN_FREE_DISK_GB
    max_load_per_cpu: float = DEFAULT_MAX_LOAD_PER_CPU


@dataclass(frozen=True)
class ResourceSnapshot:
    """Host resource snapshot used for historical-worker admission control."""

    cpu_count: int
    load_1m: float | None
    available_memory_mb: int | None
    free_disk_gb: float | None


@dataclass(frozen=True)
class GateResult:
    """One scheduler gate result."""

    allowed: bool
    reason_code: str
    reason: str


@dataclass(frozen=True)
class SchedulerDecision:
    """One durable scheduler tick decision."""

    contract_type: str
    now_utc: str
    now_et: str
    decision_status: Literal["ready", "backoff", "executed"]
    reason_code: str
    reason: str
    market_protection_active: bool
    resource_pressure_active: bool
    selected_work: str | None
    command: list[str]
    next_internal_stage: str | None = None
    approval_gate_required: str | None = None
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    execution_summary: dict[str, Any] | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _parse_hhmm(value: str) -> time:
    try:
        hour_text, minute_text = value.split(":", 1)
        parsed = time(int(hour_text), int(minute_text))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError("protected time must be HH:MM") from exc
    return parsed


def _nth_weekday(year: int, month: int, weekday: int, ordinal: int) -> date:
    current = date(year, month, 1)
    offset = (weekday - current.weekday()) % 7
    return current + timedelta(days=offset + 7 * (ordinal - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    current = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return current - timedelta(days=(current.weekday() - weekday) % 7)


def _observed_fixed_holiday(year: int, month: int, day: int) -> date:
    actual = date(year, month, day)
    if actual.weekday() == 5:  # Saturday observed Friday.
        return actual - timedelta(days=1)
    if actual.weekday() == 6:  # Sunday observed Monday.
        return actual + timedelta(days=1)
    return actual


def _easter_date(year: int) -> date:
    """Return Gregorian Easter date using Anonymous Gregorian algorithm."""

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def us_equity_market_holidays(year: int) -> set[date]:
    """Return standard full-day US equity market holidays for `year`.

    This covers the recurring full closures needed by the scheduler gate. It is
    intentionally local/deterministic; future production integration may replace
    it with an exchange-calendar feed for ad-hoc closures.
    """

    holidays = {
        _observed_fixed_holiday(year, 1, 1),
        _nth_weekday(year, 1, 0, 3),  # Martin Luther King Jr. Day.
        _nth_weekday(year, 2, 0, 3),  # Washington's Birthday / Presidents Day.
        _easter_date(year) - timedelta(days=2),  # Good Friday.
        _last_weekday(year, 5, 0),  # Memorial Day.
        _observed_fixed_holiday(year, 7, 4),
        _nth_weekday(year, 9, 0, 1),  # Labor Day.
        _nth_weekday(year, 11, 3, 4),  # Thanksgiving.
        _observed_fixed_holiday(year, 12, 25),
    }
    if year >= 2022:
        holidays.add(_observed_fixed_holiday(year, 6, 19))
    return holidays


def is_regular_us_equity_trading_day(day: date) -> bool:
    """Return whether `day` is an ordinary US equity trading day."""

    if day.weekday() >= 5:
        return False
    return day not in us_equity_market_holidays(day.year)


def market_hours_gate(now_utc: datetime, config: SchedulerConfig = SchedulerConfig()) -> GateResult:
    """Gate historical-heavy work during protected trading-day market hours."""

    now_et = now_utc.astimezone(NEW_YORK)
    if not is_regular_us_equity_trading_day(now_et.date()):
        return GateResult(True, "not_regular_trading_day", "market-hours protection is inactive on non-trading days")
    start = _parse_hhmm(config.protected_start_et)
    end = _parse_hhmm(config.protected_end_et)
    if start <= now_et.time() <= end:
        return GateResult(
            False,
            "regular_trading_day_market_hours_protection",
            "historical-heavy work is paused during 09:20-16:10 ET on regular US equity trading days",
        )
    return GateResult(True, "outside_market_hours_protection", "outside regular-trading-day protection window")


def _read_available_memory_mb() -> int | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                return int(parts[1]) // 1024
    return None


def collect_resource_snapshot(path: Path = Path("/")) -> ResourceSnapshot:
    cpu_count = os.cpu_count() or 1
    try:
        load_1m = os.getloadavg()[0]
    except (AttributeError, OSError):
        load_1m = None
    try:
        usage = shutil.disk_usage(path)
        free_disk_gb = usage.free / (1024**3)
    except OSError:
        free_disk_gb = None
    return ResourceSnapshot(
        cpu_count=cpu_count,
        load_1m=load_1m,
        available_memory_mb=_read_available_memory_mb(),
        free_disk_gb=free_disk_gb,
    )


def resource_gate(snapshot: ResourceSnapshot, config: SchedulerConfig = SchedulerConfig()) -> GateResult:
    """Return whether historical work can start without crowding live systems."""

    reasons: list[str] = []
    if snapshot.load_1m is not None:
        load_per_cpu = snapshot.load_1m / max(snapshot.cpu_count, 1)
        if load_per_cpu > config.max_load_per_cpu:
            reasons.append(f"load_per_cpu={load_per_cpu:.2f}>{config.max_load_per_cpu:.2f}")
    if snapshot.available_memory_mb is not None and snapshot.available_memory_mb < config.min_available_memory_mb:
        reasons.append(f"available_memory_mb={snapshot.available_memory_mb}<{config.min_available_memory_mb}")
    if snapshot.free_disk_gb is not None and snapshot.free_disk_gb < config.min_free_disk_gb:
        reasons.append(f"free_disk_gb={snapshot.free_disk_gb:.2f}<{config.min_free_disk_gb:.2f}")
    if reasons:
        return GateResult(False, "resource_pressure", ";".join(reasons))
    return GateResult(True, "resource_budget_available", "resource budget is available after reserving live-system headroom")


def _safe_prep_command(start_month: str, end_month: str, *, execute: bool) -> list[str]:
    command = [
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/prepare_layer_one_historical_training.py",
        "--start-month",
        start_month,
        "--end-month",
        end_month,
        "--format",
        "json",
    ]
    if execute:
        command.append("--write-files-only")
    return command


def run_scheduler_once(
    *,
    now_utc: datetime | None = None,
    config: SchedulerConfig = SchedulerConfig(),
    resource_snapshot: ResourceSnapshot | None = None,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    execute_safe_preparation: bool = False,
    execute_safe_offline_stages: bool = False,
) -> SchedulerDecision:
    """Run one scheduler tick.

    The first executable work item is Layer 1 historical-training preparation. It
    writes task-key payloads only when ``execute_safe_preparation`` is true and
    never dispatches providers, activates models, or touches broker execution.
    """

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    market_gate = market_hours_gate(now, config)
    snapshot = resource_snapshot or collect_resource_snapshot(storage_root)
    res_gate = resource_gate(snapshot, config)
    now_et = now.astimezone(NEW_YORK)

    if not market_gate.allowed:
        return SchedulerDecision(
            contract_type="manager_scheduler_decision_v1",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="backoff",
            reason_code=market_gate.reason_code,
            reason=market_gate.reason,
            market_protection_active=True,
            resource_pressure_active=not res_gate.allowed,
            selected_work=None,
            command=[],
            next_internal_stage="historical_training_work_loop",
        )
    if not res_gate.allowed:
        return SchedulerDecision(
            contract_type="manager_scheduler_decision_v1",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="backoff",
            reason_code=res_gate.reason_code,
            reason=res_gate.reason,
            market_protection_active=False,
            resource_pressure_active=True,
            selected_work=None,
            command=[],
            next_internal_stage="historical_training_work_loop",
        )

    workflow_plan = build_model_training_workflow_plan(start_month=start_month, end_month=end_month, storage_root=storage_root)
    workflow_state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=workflow_state_path_for_month(start_month, root=storage_root / "runtime"),
        write=False,
    )
    workflow_next_stage = next_ready_or_blocked_stage(workflow_state)
    if workflow_next_stage and workflow_next_stage.status == "ready":
        if not execute_safe_offline_stages:
            return SchedulerDecision(
                contract_type="manager_scheduler_decision_v1",
                now_utc=now.isoformat(),
                now_et=now_et.isoformat(),
                decision_status="ready",
                reason_code="safe_offline_stage_ready",
                reason="safe offline workflow stage is ready; rerun with --execute-safe-offline-stages to execute it",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work=workflow_next_stage.stage_id,
                command=workflow_next_stage.command,
                next_internal_stage=workflow_next_stage.stage_type,
                execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
            )
        execution, updated_workflow_state = execute_next_ready_stage(
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            state_path=workflow_state_path_for_month(start_month, root=storage_root / "runtime"),
            receipt_root=storage_root / "runtime" / "model_training_stage_receipts",
            log_root=storage_root / "runtime" / "model_training_stage_logs",
            write=True,
        )
        return SchedulerDecision(
            contract_type="manager_scheduler_decision_v1",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="executed",
            reason_code="safe_offline_stage_executed",
            reason="executed one ready safe offline workflow stage and recorded its receipt/state",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=workflow_next_stage.stage_id,
            command=workflow_next_stage.command,
            next_internal_stage=workflow_next_stage.stage_type,
            provider_calls=execution.provider_calls,
            model_activation_performed=execution.model_activation_performed,
            broker_execution_performed=execution.broker_execution_performed,
            execution_summary={
                "stage_execution": execution.summary_row(),
                "workflow_plan": workflow_plan.summary_row(),
                "workflow_state": updated_workflow_state.summary_row(),
            },
        )
    if workflow_plan.layer_one_task_key_count >= LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS:
        next_stage = workflow_next_stage or workflow_plan.next_stage
        return SchedulerDecision(
            contract_type="manager_scheduler_decision_v1",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="backoff",
            reason_code="waiting_owner_observed_agent_review",
            reason="Layer 1 provider acquisition is the next internal historical-training stage and requires owner-observed agent-reviewed live_call_approval_v1 plus proposal validation",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=next_stage.stage_id if next_stage else "model_training_workflow",
            command=next_stage.command if next_stage else [],
            next_internal_stage="owner_observed_agent_reviewed_provider_acquisition",
            approval_gate_required="live_call_approval_v1",
            execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
        )

    selected_work = "prepare_layer_one_historical_training_batch"
    command = _safe_prep_command(start_month, end_month, execute=execute_safe_preparation)
    if not execute_safe_preparation:
        return SchedulerDecision(
            contract_type="manager_scheduler_decision_v1",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="ready",
            reason_code="safe_offline_work_ready",
            reason="safe Layer 1 historical-training preparation is ready; rerun with --execute-safe-preparation to write payload files",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=selected_work,
            command=command,
            next_internal_stage="owner_observed_agent_reviewed_provider_acquisition",
            approval_gate_required="live_call_approval_v1",
            execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
        )

    summary, _requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        component_src_root=component_src_root,
        write=True,
        persist_sql=False,
        validate_handoff=True,
    )
    refreshed_workflow_plan = build_model_training_workflow_plan(start_month=start_month, end_month=end_month, storage_root=storage_root)
    refreshed_workflow_state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=workflow_state_path_for_month(start_month, root=storage_root / "runtime"),
        write=False,
    )
    return SchedulerDecision(
        contract_type="manager_scheduler_decision_v1",
        now_utc=now.isoformat(),
        now_et=now_et.isoformat(),
        decision_status="executed",
        reason_code="safe_offline_preparation_executed",
        reason="completed Layer 1 internal acquisition preparation; next internal stage is owner-observed agent-reviewed provider acquisition",
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=command,
        next_internal_stage="owner_observed_agent_reviewed_provider_acquisition",
        approval_gate_required="live_call_approval_v1",
        execution_summary=summary.summary_row()
        | {"workflow_plan": refreshed_workflow_plan.summary_row(), "workflow_state": refreshed_workflow_state.summary_row()},
    )


def write_scheduler_decision(decision: SchedulerDecision, *, output: TextIO) -> None:
    json.dump(decision.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one safe manager automation-scheduler tick.")
    parser.add_argument("--now-utc", help="ISO-8601 timestamp for deterministic testing/replay.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--component-src-root", type=Path, default=DEFAULT_TRADING_DATA_SRC)
    parser.add_argument("--execute-safe-preparation", action="store_true", help="Write Layer 1 task-key payload files and validate handoff shape. No provider calls are performed.")
    parser.add_argument("--execute-safe-offline-stages", action="store_true", help="Execute one ready offline workflow stage and record its receipt/state. No provider calls or activation are performed.")
    parser.add_argument("--min-available-memory-mb", type=int, default=DEFAULT_MIN_AVAILABLE_MEMORY_MB)
    parser.add_argument("--min-free-disk-gb", type=float, default=DEFAULT_MIN_FREE_DISK_GB)
    parser.add_argument("--max-load-per-cpu", type=float, default=DEFAULT_MAX_LOAD_PER_CPU)
    args = parser.parse_args(argv)

    now = None
    if args.now_utc:
        text = args.now_utc
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        now = datetime.fromisoformat(text).astimezone(UTC)
    config = SchedulerConfig(
        min_available_memory_mb=args.min_available_memory_mb,
        min_free_disk_gb=args.min_free_disk_gb,
        max_load_per_cpu=args.max_load_per_cpu,
    )
    decision = run_scheduler_once(
        now_utc=now,
        config=config,
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        component_src_root=args.component_src_root,
        execute_safe_preparation=args.execute_safe_preparation,
        execute_safe_offline_stages=args.execute_safe_offline_stages,
    )
    write_scheduler_decision(decision, output=sys.stdout)
    return 0


__all__ = [
    "GateResult",
    "ResourceSnapshot",
    "SchedulerConfig",
    "SchedulerDecision",
    "collect_resource_snapshot",
    "is_regular_us_equity_trading_day",
    "market_hours_gate",
    "resource_gate",
    "run_scheduler_once",
    "us_equity_market_holidays",
    "write_scheduler_decision",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

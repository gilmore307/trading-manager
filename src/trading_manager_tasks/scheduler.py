"""Capacity-aware manager scheduler gates and historical training work loop.

Historical provider acquisition is an internal training stage and advances
automatically after request payload preparation. Provider/data acquisition may
call historical data APIs through autonomous manager dispatch, but broker/order/account mutation and model
activation remain blocked unless a separate approved decision exists.
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

from .historical_training import prepare_layer_historical_training_batch, prepare_layer_one_historical_training_batch
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .model_training_state import advance_workflow_state, mark_stage_started, next_ready_or_blocked_stage, workflow_state_path_for_month, write_workflow_state
from .model_training_workflow import LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS, LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS, build_model_training_workflow_plan
from .request_handoff import DEFAULT_TRADING_DATA_SRC
from .stage_executor import execute_next_ready_stage
from .stage_reconcile import DEFAULT_COMPONENT_STORAGE_ROOT, reconcile_provider_stage
from .stage_run_controller import run_stage_controller_step
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler_locks import scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
PROTECTION_START = time(9, 20)
PROTECTION_END = time(16, 10)
DEFAULT_MIN_AVAILABLE_MEMORY_MB = 2048
DEFAULT_MIN_FREE_DISK_GB = 10.0
DEFAULT_MAX_LOAD_PER_CPU = 0.70


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", "disabled"}


DEFAULT_MARKET_HOURS_PROTECTION_ENABLED = _env_bool("TRADING_MANAGER_MARKET_HOURS_PROTECTION_ENABLED", default=True)


@dataclass(frozen=True)
class SchedulerConfig:
    """Runtime gates for one scheduler tick."""

    market_hours_protection_enabled: bool = DEFAULT_MARKET_HOURS_PROTECTION_ENABLED
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
    storage_lifecycle_mutation_performed: bool = False
    execution_summary: dict[str, Any] | None = None
    lock_plan: dict[str, Any] | None = None

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

    if not config.market_hours_protection_enabled:
        return GateResult(
            True,
            "market_hours_protection_disabled_pre_promotion",
            "market-hours historical-training protection is disabled while no production model is active",
        )
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


PROVIDER_STAGE_MODEL_LAYERS = {
    "layer_01_market_regime.data_acquisition": LAYER_ONE_MODEL_LAYER,
    "layer_02_sector_context.data_acquisition": LAYER_TWO_MODEL_LAYER,
}


def _safe_prep_command(start_month: str, end_month: str, *, model_layer: str, execute: bool) -> list[str]:
    script = "prepare_layer_one_historical_training.py" if model_layer == LAYER_ONE_MODEL_LAYER else "prepare_layer_two_historical_training.py"
    command = [
        "PYTHONPATH=src",
        "python3",
        f"scripts/tasks/{script}",
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


def _stage_status(workflow_state: Any, stage_id: str) -> str | None:
    for stage in workflow_state.stages:
        if stage.stage_id == stage_id:
            return stage.status
    return None


def _next_preparation_model_layer(*, workflow_plan: Any, workflow_state: Any) -> str | None:
    if (
        _stage_status(workflow_state, "layer_01_market_regime.data_acquisition") != "succeeded"
        and workflow_plan.layer_one_task_key_count < LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS
    ):
        return LAYER_ONE_MODEL_LAYER
    if (
        _stage_status(workflow_state, "layer_01_market_regime.data_acquisition") == "succeeded"
        and _stage_status(workflow_state, "layer_02_sector_context.data_acquisition") != "succeeded"
        and workflow_plan.layer_two_task_key_count < LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS
    ):
        return LAYER_TWO_MODEL_LAYER
    return None


def _preparation_selected_work(model_layer: str) -> str:
    if model_layer == LAYER_ONE_MODEL_LAYER:
        return "prepare_layer_one_historical_training_batch"
    if model_layer == LAYER_TWO_MODEL_LAYER:
        return "prepare_layer_two_historical_training_batch"
    raise ValueError(f"unsupported preparation model layer: {model_layer}")


def _execute_autonomous_provider_stage(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    storage_root: Path,
    component_src_root: Path,
    next_limit: int,
    max_workers: int,
    selected_target_symbol: str | None,
) -> dict[str, Any]:
    model_layer = PROVIDER_STAGE_MODEL_LAYERS[stage_id]
    preparation, _requests, _payloads, _validations = prepare_layer_historical_training_batch(
        model_layer=model_layer,
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        component_src_root=component_src_root,
        write=True,
        persist_sql=True,
        validate_handoff=True,
    )
    state_path = workflow_state_path_for_month(start_month, root=storage_root / "runtime")
    started_state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=state_path,
        selected_target_symbol=selected_target_symbol,
        write=False,
    )
    started_state = mark_stage_started(started_state, stage_id=stage_id, reason="provider acquisition stage started by scheduler")
    write_workflow_state(state_path, started_state)
    controller_receipt, dashboard = run_stage_controller_step(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        packet_storage_root=storage_root,
        next_limit=next_limit,
        max_workers=max_workers,
        dynamic_workers=True,
        auto_execute_provider_calls=True,
    )
    reconcile = reconcile_provider_stage(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        component_storage_root=DEFAULT_COMPONENT_STORAGE_ROOT,
        manager_storage_root=storage_root,
        persist_control_plane=True,
        write_failure_proposal=True,
        persist_failure_register=True,
        collect_coverage=True,
        write_coverage_report=True,
        advance_workflow=True,
        write_workflow_state=True,
        selected_target_symbol=selected_target_symbol,
    )
    refreshed_state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=state_path,
        selected_target_symbol=selected_target_symbol,
        write=False,
    )
    return {
        "preparation": preparation.summary_row(),
        "stage_run_controller": controller_receipt.summary_row(),
        "stage_run_dashboard": dashboard.summary_row(),
        "stage_reconcile": reconcile.summary_row(),
        "workflow_state": refreshed_state.summary_row(),
        "provider_calls": controller_receipt.provider_calls,
        "dispatch_performed": controller_receipt.dispatch_performed,
        "model_activation_performed": controller_receipt.model_activation_performed,
        "broker_execution_performed": controller_receipt.broker_execution_performed,
        "storage_lifecycle_mutation_performed": controller_receipt.storage_lifecycle_mutation_performed,
    }


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
    execute_autonomous_provider_stages: bool = False,
    provider_stage_next_limit: int = 5,
    provider_stage_max_workers: int = 4,
    selected_target_symbol: str | None = None,
    state_path: Path | None = None,
    foundation_catch_up_only: bool = True,
) -> SchedulerDecision:
    """Run one scheduler tick.

    The first executable work item is historical-training preparation. Provider
    stages execute only when ``execute_autonomous_provider_stages`` is true and
    remain bounded to one dispatch/reconcile slice per tick. Model activation,
    broker execution, account mutation, and storage lifecycle mutation stay hard
    blocked.
    """

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    market_gate = market_hours_gate(now, config)
    snapshot = resource_snapshot or collect_resource_snapshot(storage_root)
    res_gate = resource_gate(snapshot, config)
    now_et = now.astimezone(NEW_YORK)

    if not market_gate.allowed:
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
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
            lock_plan=scheduler_lock_plan(month=start_month, selected_work=None, next_internal_stage="historical_training_work_loop"),
        )
    if not res_gate.allowed:
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
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
            lock_plan=scheduler_lock_plan(month=start_month, selected_work=None, next_internal_stage="historical_training_work_loop"),
        )

    workflow_plan = build_model_training_workflow_plan(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=foundation_catch_up_only,
    )
    resolved_state_path = state_path or workflow_state_path_for_month(start_month, root=storage_root / "runtime")
    workflow_state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=resolved_state_path,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=foundation_catch_up_only,
        write=False,
    )
    workflow_next_stage = next_ready_or_blocked_stage(workflow_state)
    if workflow_next_stage is None and all(stage.status in {"succeeded", "not_applicable"} for stage in workflow_state.stages):
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="ready",
            reason_code="month_workflow_complete",
            reason="historical model-training workflow month is complete; service runtime may advance the chronological month cursor",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="advance_chronological_month_cursor",
            command=[],
            next_internal_stage="chronological_month_advance",
            execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
            lock_plan=scheduler_lock_plan(
                month=start_month,
                selected_work="advance_chronological_month_cursor",
                next_internal_stage="chronological_month_advance",
            ),
        )
    if workflow_next_stage and workflow_next_stage.status == "ready" and workflow_next_stage.stage_id in PROVIDER_STAGE_MODEL_LAYERS:
        if not execute_autonomous_provider_stages:
            return SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc=now.isoformat(),
                now_et=now_et.isoformat(),
                decision_status="ready",
                reason_code="autonomous_provider_stage_ready",
                reason="provider acquisition stage is ready; rerun with autonomous provider-stage execution enabled to dispatch one bounded slice",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work=workflow_next_stage.stage_id,
                command=workflow_next_stage.command,
                next_internal_stage="autonomous_historical_provider_acquisition",
                execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
                lock_plan=scheduler_lock_plan(
                    month=start_month,
                    selected_work=workflow_next_stage.stage_id,
                    next_internal_stage="autonomous_historical_provider_acquisition",
                ),
            )
        execution_summary = _execute_autonomous_provider_stage(
            stage_id=workflow_next_stage.stage_id,
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            component_src_root=component_src_root,
            next_limit=provider_stage_next_limit,
            max_workers=provider_stage_max_workers,
            selected_target_symbol=selected_target_symbol,
        )
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="executed",
            reason_code="autonomous_provider_stage_executed",
            reason="executed one bounded autonomous historical provider-dispatch/reconcile slice",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=workflow_next_stage.stage_id,
            command=workflow_next_stage.command,
            next_internal_stage="autonomous_historical_provider_acquisition",
            provider_calls=int(execution_summary.get("provider_calls") or 0),
            dispatch_performed=bool(execution_summary.get("dispatch_performed")),
            model_activation_performed=bool(execution_summary.get("model_activation_performed")),
            broker_execution_performed=bool(execution_summary.get("broker_execution_performed")),
            storage_lifecycle_mutation_performed=bool(execution_summary.get("storage_lifecycle_mutation_performed")),
            execution_summary=execution_summary,
            lock_plan=scheduler_lock_plan(
                month=start_month,
                selected_work=workflow_next_stage.stage_id,
                next_internal_stage="autonomous_historical_provider_acquisition",
            ),
        )
    if workflow_next_stage and workflow_next_stage.status == "ready":
        if not execute_safe_offline_stages:
            return SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc=now.isoformat(),
                now_et=now_et.isoformat(),
                decision_status="ready",
                reason_code="workflow_stage_ready",
                reason="workflow stage is ready; rerun with --execute-safe-offline-stages to execute it",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work=workflow_next_stage.stage_id,
                command=workflow_next_stage.command,
                next_internal_stage=workflow_next_stage.stage_type,
                execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
                lock_plan=scheduler_lock_plan(
                    month=start_month,
                    selected_work=workflow_next_stage.stage_id,
                    next_internal_stage=workflow_next_stage.stage_type,
                ),
            )
        execution, updated_workflow_state = execute_next_ready_stage(
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            state_path=resolved_state_path,
            receipt_root=storage_root / "runtime" / "model_training_stage_receipts",
            log_root=storage_root / "runtime" / "model_training_stage_logs",
            selected_target_symbol=selected_target_symbol,
            foundation_catch_up_only=foundation_catch_up_only,
            write=True,
        )
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="executed",
            reason_code="workflow_stage_executed",
            reason="executed one ready workflow stage and recorded its receipt/state",
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
            lock_plan=scheduler_lock_plan(
                month=start_month,
                selected_work=workflow_next_stage.stage_id,
                next_internal_stage=workflow_next_stage.stage_type,
            ),
        )

    preparation_model_layer = _next_preparation_model_layer(workflow_plan=workflow_plan, workflow_state=workflow_state)
    if preparation_model_layer is None:
        next_stage = workflow_next_stage or workflow_plan.next_stage
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="backoff",
            reason_code="workflow_stage_blocked",
            reason="no executable scheduler-owned workflow stage is currently available",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=next_stage.stage_id if next_stage else "model_training_workflow",
            command=next_stage.command if next_stage else [],
            next_internal_stage=next_stage.stage_type if next_stage else "historical_training_work_loop",
            execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
            lock_plan=scheduler_lock_plan(
                month=start_month,
                selected_work=next_stage.stage_id if next_stage else "model_training_workflow",
                next_internal_stage=next_stage.stage_type if next_stage else "historical_training_work_loop",
            ),
        )

    selected_work = _preparation_selected_work(preparation_model_layer)
    command = _safe_prep_command(start_month, end_month, model_layer=preparation_model_layer, execute=execute_safe_preparation)
    if not execute_safe_preparation:
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc=now.isoformat(),
            now_et=now_et.isoformat(),
            decision_status="ready",
            reason_code="safe_offline_work_ready",
            reason="safe historical-training preparation is ready; rerun with --execute-safe-preparation to write payload files",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=selected_work,
            command=command,
            next_internal_stage="autonomous_historical_provider_acquisition",
            execution_summary={"workflow_plan": workflow_plan.summary_row(), "workflow_state": workflow_state.summary_row()},
            lock_plan=scheduler_lock_plan(
                month=start_month,
                selected_work=selected_work,
                next_internal_stage="autonomous_historical_provider_acquisition",
            ),
        )

    if preparation_model_layer == LAYER_ONE_MODEL_LAYER:
        prepare = prepare_layer_one_historical_training_batch
    else:
        def prepare(**kwargs: Any):
            return prepare_layer_historical_training_batch(model_layer=preparation_model_layer, **kwargs)
    summary, _requests, _payloads, _validations = prepare(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        component_src_root=component_src_root,
        write=True,
        persist_sql=False,
        validate_handoff=True,
    )
    refreshed_workflow_plan = build_model_training_workflow_plan(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=foundation_catch_up_only,
    )
    refreshed_workflow_state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=resolved_state_path,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=foundation_catch_up_only,
        write=False,
    )
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now_et.isoformat(),
        decision_status="executed",
        reason_code="safe_offline_preparation_executed",
        reason="completed internal acquisition preparation; next internal stage is autonomous historical provider acquisition",
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=command,
        next_internal_stage="autonomous_historical_provider_acquisition",
        execution_summary=summary.summary_row()
        | {"workflow_plan": refreshed_workflow_plan.summary_row(), "workflow_state": refreshed_workflow_state.summary_row()},
        lock_plan=scheduler_lock_plan(
            month=start_month,
            selected_work=selected_work,
            next_internal_stage="autonomous_historical_provider_acquisition",
        ),
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
    parser.add_argument("--execute-safe-preparation", action="store_true", help="Write task-key payload files and validate handoff shape. No provider calls are performed.")
    parser.add_argument("--execute-safe-offline-stages", action="store_true", help="Execute one ready offline workflow stage and record its receipt/state. Provider stages use --execute-autonomous-provider-stages instead.")
    parser.add_argument("--execute-autonomous-provider-stages", action="store_true", help="Execute one bounded autonomous provider-dispatch/reconcile slice when a provider acquisition stage is ready.")
    parser.add_argument("--provider-stage-next-limit", type=int, default=5, help="Maximum provider requests to dispatch in one scheduler tick.")
    parser.add_argument("--provider-stage-max-workers", type=int, default=4, help="Maximum dynamic provider worker threads in one scheduler tick.")
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for Layer 3+ six-month dataset units.")
    parser.add_argument("--disable-market-hours-protection", action="store_true", help="Allow historical training during regular US equity market hours while no production model is active. Provider, promotion, and broker gates remain hard.")
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
        market_hours_protection_enabled=not args.disable_market_hours_protection and DEFAULT_MARKET_HOURS_PROTECTION_ENABLED,
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
        execute_autonomous_provider_stages=args.execute_autonomous_provider_stages,
        provider_stage_next_limit=args.provider_stage_next_limit,
        provider_stage_max_workers=args.provider_stage_max_workers,
        selected_target_symbol=args.target_symbol,
    )
    write_scheduler_decision(decision, output=sys.stdout)
    return 0


__all__ = [
    "GateResult",
    "DEFAULT_MARKET_HOURS_PROTECTION_ENABLED",
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

"""Shared option-chain source/cache acquisition for target-state folds.

The manager prepares one ThetaData option-chain source request per target trading
day before Layer 3 feature generation. The source rows are contract-level SQL
cache evidence in ``trading_data.option_chain_state_source``; Layer 3 reduces
them to target-level option state, and Layer 9 derives option-expression context
from the same cache.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO
from zoneinfo import ZoneInfo

from .control_plane import TaskSystemError, fetch_manager_requests, persist_manager_requests
from .provider_dispatch import ProviderDispatchItem, ProviderDispatchSummary, select_provider_worker_count
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

STAGE_ID = "layer_03_target_state_vector.option_chain_data_acquisition"
SOURCE_ID = "option_chain_state_source"
TARGET_COMPONENT_ID = SOURCE_ID
REQUEST_KIND = "option_chain_snapshot"
DEFAULT_SOURCE_OUTPUT_ROOT = data_storage_root() / "layer_03_target_state_vector" / SOURCE_ID
DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_SESSION_START = time(9, 30)
DEFAULT_SESSION_END = time(16, 0)
DEFAULT_WINDOW_MINUTES = 30
DEFAULT_MAX_DTE = 365
DEFAULT_STRIKE_RANGE = 10
DEFAULT_OPTION_BUCKET_POLICY_REF = "TARGET_OPTION_CHAIN_STATE_REDUCTION_POLICY"
OPTION_CHAIN_PROVIDER_CONTROLS = {
    "allowed_providers": ["thetadata"],
    "allowed_endpoint_families": ["option_selection_snapshot"],
    "max_symbols": 1,
    "max_time_window": "1d",
    "timeout_seconds": 120,
    "retry_attempts": 3,
    "retry_backoff_seconds": 1.0,
    "retry_policy_ref": "target_option_chain_state_source_retry",
    "rate_limit_policy_ref": "thetadata_terminal_rest_rate_limit",
}
DEFAULT_THETADATA_TRANSPORT = "terminal_rest"
ET = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class OptionChainRequestPreview:
    """One bounded target-window shared option-chain source/cache request."""

    request_id: str
    underlying: str
    snapshot_time: str
    window_start: str
    window_end: str
    provider: str = "thetadata"
    target_component_id: str = TARGET_COMPONENT_ID
    max_dte: int = DEFAULT_MAX_DTE
    strike_range: int = DEFAULT_STRIKE_RANGE
    option_bucket_policy_ref: str = DEFAULT_OPTION_BUCKET_POLICY_REF

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["source_task_key"] = {
            "task_id": self.request_id,
            "source": SOURCE_ID,
            "params": {
                "underlying": self.underlying,
                "snapshot_time": self.snapshot_time,
                "window_start": self.window_start,
                "window_end": self.window_end,
                "max_dte": self.max_dte,
                "strike_range": self.strike_range,
                "option_bucket_policy_ref": self.option_bucket_policy_ref,
                "thetadata_transport": DEFAULT_THETADATA_TRANSPORT,
                "timeout_seconds": OPTION_CHAIN_PROVIDER_CONTROLS["timeout_seconds"],
                "retry_attempts": OPTION_CHAIN_PROVIDER_CONTROLS["retry_attempts"],
                "retry_backoff_seconds": OPTION_CHAIN_PROVIDER_CONTROLS["retry_backoff_seconds"],
            },
        }
        return row


@dataclass(frozen=True)
class OptionChainSourceReview:
    """No-provider preparation review for shared option-chain source acquisition."""

    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    status: str
    target_symbol: str
    request_count: int
    request_previews: tuple[OptionChainRequestPreview, ...]
    evidence_refs: tuple[str, ...]
    reason: str
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["request_previews"] = [item.summary_row() for item in self.request_previews]
        row["evidence_refs"] = list(self.evidence_refs)
        return row


def _validate_month(month: str) -> tuple[int, int]:
    if len(month) != 7 or month[4] != "-":
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    year = int(month[:4])
    month_number = int(month[5:])
    if not 1 <= month_number <= 12:
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    return year, month_number


def _add_month(month: str) -> str:
    year, month_number = _validate_month(month)
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _iter_months(start_month: str, end_month: str) -> Iterable[str]:
    _validate_month(start_month)
    _validate_month(end_month)
    if start_month > end_month:
        raise TaskSystemError(f"start_month must be <= end_month: {start_month}>{end_month}")
    month = start_month
    while month <= end_month:
        yield month
        month = _add_month(month)


def _nth_weekday(year: int, month: int, weekday: int, ordinal: int) -> date:
    current = date(year, month, 1)
    offset = (weekday - current.weekday()) % 7
    return current + timedelta(days=offset + 7 * (ordinal - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    current = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return current - timedelta(days=(current.weekday() - weekday) % 7)


def _observed_fixed_holiday(year: int, month: int, day: int) -> date:
    actual = date(year, month, day)
    if actual.weekday() == 5:
        return actual - timedelta(days=1)
    if actual.weekday() == 6:
        return actual + timedelta(days=1)
    return actual


def _easter_date(year: int) -> date:
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
    holidays = {
        _observed_fixed_holiday(year, 1, 1),
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        _easter_date(year) - timedelta(days=2),
        _last_weekday(year, 5, 0),
        _observed_fixed_holiday(year, 7, 4),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 11, 3, 4),
        _observed_fixed_holiday(year, 12, 25),
    }
    if year >= 2022:
        holidays.add(_observed_fixed_holiday(year, 6, 19))
    return holidays


def is_regular_us_equity_trading_day(day: date) -> bool:
    return day.weekday() < 5 and day not in us_equity_market_holidays(day.year)


def iter_regular_trading_days(start_month: str, end_month: str) -> Iterable[date]:
    for month in _iter_months(start_month, end_month):
        year, month_number = _validate_month(month)
        next_month = _add_month(month)
        end = date(int(next_month[:4]), int(next_month[5:]), 1)
        current = date(year, month_number, 1)
        while current < end:
            if is_regular_us_equity_trading_day(current):
                yield current
            current += timedelta(days=1)


def _safe_symbol(symbol: str | None) -> str:
    value = (symbol or "").strip().upper()
    if not value:
        raise TaskSystemError("target_symbol is required for shared option-chain source acquisition")
    return value


def _window_request_id(*, symbol: str, start_month: str, window_start: datetime) -> str:
    return (
        f"mgrreq_option_chain_window_{symbol.lower()}_{start_month.replace('-', '_')}_"
        f"{window_start.date().isoformat().replace('-', '_')}_{window_start.strftime('%H%M')}"
    )


def iter_regular_session_windows(start_month: str, end_month: str, *, window_minutes: int = DEFAULT_WINDOW_MINUTES) -> Iterable[tuple[datetime, datetime]]:
    if window_minutes <= 0:
        raise TaskSystemError("window_minutes must be positive")
    step = timedelta(minutes=window_minutes)
    for day in iter_regular_trading_days(start_month, end_month):
        window_start = datetime.combine(day, DEFAULT_SESSION_START, tzinfo=ET)
        session_end = datetime.combine(day, DEFAULT_SESSION_END, tzinfo=ET)
        while window_start < session_end:
            window_end = min(window_start + step, session_end)
            yield window_start, window_end
            window_start = window_end


def _task_key_path_for_request(request_id: str, *, start_month: str, storage_root: Path = DEFAULT_STORAGE_ROOT) -> Path:
    return storage_root / "runtime" / "layer_03_target_state_vector" / SOURCE_ID / start_month / request_id / "task_key.json"


def _task_key_ref_for_request(request_id: str, *, start_month: str) -> str:
    return f"storage://trading-manager/runtime/layer_03_target_state_vector/{SOURCE_ID}/{start_month}/{request_id}/task_key.json"


def _source_output_root_for_request(request_id: str, *, start_month: str, source_output_root: Path = DEFAULT_SOURCE_OUTPUT_ROOT) -> Path:
    return source_output_root / start_month / request_id


def request_previews_for_fold(*, start_month: str, end_month: str, target_symbol: str) -> tuple[OptionChainRequestPreview, ...]:
    symbol = _safe_symbol(target_symbol)
    previews: list[OptionChainRequestPreview] = []
    for window_start_dt, window_end_dt in iter_regular_session_windows(start_month, end_month):
        window_start = window_start_dt.isoformat()
        window_end = window_end_dt.isoformat()
        previews.append(
            OptionChainRequestPreview(
                request_id=_window_request_id(symbol=symbol, start_month=start_month, window_start=window_start_dt),
                underlying=symbol,
                snapshot_time=window_start,
                window_start=window_start,
                window_end=window_end,
            )
        )
    return tuple(previews)


def _parse_replay_decision_time(value: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise TaskSystemError("replay decision timestamp is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TaskSystemError(f"invalid replay decision timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET).replace(second=0, microsecond=0)


def request_previews_for_replay_decision_times(
    *,
    target_symbol: str,
    decision_timestamps: Sequence[str],
    window_minutes: int = DEFAULT_WINDOW_MINUTES,
) -> tuple[OptionChainRequestPreview, ...]:
    """Build bounded option-chain requests for replay decision timestamps.

    Replay only needs point-in-time option context available no later than each
    decision timestamp. The request window therefore ends at the decision time
    and starts one provider window earlier.
    """

    symbol = _safe_symbol(target_symbol)
    if window_minutes <= 0:
        raise TaskSystemError("window_minutes must be positive")
    previews_by_id: dict[str, OptionChainRequestPreview] = {}
    for raw_timestamp in decision_timestamps:
        decision_time = _parse_replay_decision_time(raw_timestamp)
        window_start_dt = decision_time - timedelta(minutes=window_minutes)
        if window_start_dt.date() != decision_time.date():
            raise TaskSystemError(f"replay decision window crosses date boundary: {raw_timestamp}")
        start_month = decision_time.strftime("%Y-%m")
        request_id = _window_request_id(symbol=symbol, start_month=start_month, window_start=decision_time)
        previews_by_id[request_id] = OptionChainRequestPreview(
            request_id=request_id,
            underlying=symbol,
            snapshot_time=decision_time.isoformat(),
            window_start=window_start_dt.isoformat(),
            window_end=decision_time.isoformat(),
        )
    return tuple(previews_by_id[request_id] for request_id in sorted(previews_by_id))


def build_option_chain_source_review(*, start_month: str, end_month: str, target_symbol: str) -> OptionChainSourceReview:
    previews = request_previews_for_fold(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
    return OptionChainSourceReview(
        contract_type="manager_option_chain_state_source_acquisition_review",
        stage_id=STAGE_ID,
        start_month=start_month,
        end_month=end_month,
        status="provider_acquisition_ready" if previews else "no_provider_skip_accepted",
        target_symbol=_safe_symbol(target_symbol),
        request_count=len(previews),
        request_previews=previews,
        evidence_refs=("calendar:manager_us_equity_regular_trading_days",),
        reason=f"{len(previews)} regular-session 30-minute window(s) require shared ThetaData option-chain source/cache acquisition before Layer 3.",
    )


def manager_requests_from_review(
    review: OptionChainSourceReview,
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    source_output_root: Path = DEFAULT_SOURCE_OUTPUT_ROOT,
) -> tuple[dict[str, Any], ...]:
    requests: list[dict[str, Any]] = []
    for preview in review.request_previews:
        task_key_path = _task_key_path_for_request(preview.request_id, start_month=review.start_month, storage_root=storage_root)
        task_key = preview.summary_row()["source_task_key"]
        task_key.update(
            {
                "output_root": str(_source_output_root_for_request(preview.request_id, start_month=review.start_month, source_output_root=source_output_root)),
                "manager_controls": {
                    "allow_live_provider_calls": True,
                    "autonomous_historical_provider_acquisition": True,
                    "stage_id": STAGE_ID,
                    "start_month": review.start_month,
                    "end_month": review.end_month,
                    **OPTION_CHAIN_PROVIDER_CONTROLS,
                },
                "policy_refs": ["autonomous_historical_provider_acquisition", "target_option_chain_state_source_acquisition"],
            }
        )
        requests.append(
            {
                "request_id": preview.request_id,
                "contract_type": "manager_request",
                "request_kind": REQUEST_KIND,
                "status": "requested",
                "requested_by": "trading-manager.option_chain_state_source",
                "target_component_id": TARGET_COMPONENT_ID,
                "target_component_kind": "data_source",
                "target_repo_id": "trading-data",
                "expected_outputs": ["trading_data.option_chain_state_source"],
                "policy_refs": ["autonomous_historical_provider_acquisition", "target_option_chain_state_source_acquisition"],
                "priority": "normal",
                "deadline_at_utc": None,
                "parameter_ref": _task_key_ref_for_request(preview.request_id, start_month=review.start_month),
                "dry_run": False,
                "symbol": preview.underlying,
                "month": review.start_month,
                "_task_key_path": str(task_key_path),
                "_task_key": task_key,
            }
        )
    return tuple(requests)


def write_option_chain_task_keys(requests: Sequence[Mapping[str, Any]]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for request in requests:
        path = Path(str(request["_task_key_path"]))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(request["_task_key"]), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(path)
    return tuple(paths)


def prepare_option_chain_source_acquisition(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    source_output_root: Path = DEFAULT_SOURCE_OUTPUT_ROOT,
    write: bool = False,
    persist_sql: bool = False,
    database_url: str | None = None,
) -> tuple[OptionChainSourceReview, tuple[dict[str, Any], ...], tuple[Path, ...]]:
    review = build_option_chain_source_review(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
    requests = manager_requests_from_review(review, storage_root=storage_root, source_output_root=source_output_root)
    task_key_paths: tuple[Path, ...] = ()
    if write and requests:
        task_key_paths = write_option_chain_task_keys(requests)
    if persist_sql and requests:
        persistable = [{key: value for key, value in request.items() if not key.startswith("_")} for request in requests]
        persist_manager_requests(persistable, database_url=database_url)
    return review, requests, task_key_paths


def _matches_request(row: Mapping[str, Any], *, start_month: str, end_month: str) -> bool:
    if row.get("target_component_id") != TARGET_COMPONENT_ID or row.get("request_kind") != REQUEST_KIND:
        return False
    request_id = str(row.get("request_id") or "")
    if not request_id.startswith("mgrreq_option_chain_window_"):
        return False
    text = " ".join(str(row.get(key) or "") for key in ("request_id", "parameter_ref"))
    return start_month in text or end_month in text


def request_rows(*, start_month: str, end_month: str, request_ids: Sequence[str] = (), database_url: str | None = None) -> list[dict[str, Any]]:
    request_filter = {item.strip() for item in request_ids if item.strip()}
    rows = [dict(row) for row in fetch_manager_requests(database_url=database_url) if _matches_request(row, start_month=start_month, end_month=end_month)]
    if request_filter:
        rows = [row for row in rows if str(row.get("request_id") or "") in request_filter]
        found = {str(row.get("request_id") or "") for row in rows}
        missing = sorted(request_filter - found)
        if missing:
            raise TaskSystemError("requested option-chain source request ids are not available: " + ",".join(missing))
    if not rows:
        raise TaskSystemError("no shared option-chain source requests available for dispatch")
    return sorted(rows, key=lambda row: str(row.get("request_id") or ""))


def _runtime_task_key(task_key: Mapping[str, Any]) -> dict[str, Any]:
    runtime_key = dict(task_key)
    runtime_key["dry_run"] = False
    controls = dict(runtime_key.get("manager_controls") or {})
    controls["allow_live_provider_calls"] = True
    controls["autonomous_historical_provider_acquisition"] = True
    controls.update(OPTION_CHAIN_PROVIDER_CONTROLS)
    runtime_key["manager_controls"] = controls
    params = dict(runtime_key.get("params") or {})
    params["manager_dry_run"] = False
    params.setdefault("thetadata_transport", DEFAULT_THETADATA_TRANSPORT)
    params.setdefault("timeout_seconds", OPTION_CHAIN_PROVIDER_CONTROLS["timeout_seconds"])
    params.setdefault("retry_attempts", OPTION_CHAIN_PROVIDER_CONTROLS["retry_attempts"])
    params.setdefault("retry_backoff_seconds", OPTION_CHAIN_PROVIDER_CONTROLS["retry_backoff_seconds"])
    runtime_key["params"] = params
    return runtime_key


def _run_id(request_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{request_id}_provider_{stamp}"


def dispatch_option_chain_source_acquisition(
    *,
    start_month: str,
    end_month: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    execute_provider_calls: bool = False,
    continue_on_error: bool = False,
    database_url: str | None = None,
    dynamic_workers: bool = True,
    max_workers: int = 4,
) -> ProviderDispatchSummary:
    rows = request_rows(start_month=start_month, end_month=end_month, request_ids=request_ids, database_url=database_url)
    if limit is not None:
        if limit <= 0:
            raise TaskSystemError("limit must be positive")
        rows = rows[:limit]
    provider_max_workers = 1 if execute_provider_calls else max_workers
    worker_selection = select_provider_worker_count(
        request_count=len(rows),
        execute_provider_calls=execute_provider_calls,
        dynamic_workers=dynamic_workers,
        max_workers=provider_max_workers,
    )

    def dispatch_one(row: Mapping[str, Any], *, worker_slot: int) -> ProviderDispatchItem:
        request_id = str(row["request_id"])
        source_path = storage_root / str(row["parameter_ref"]).removeprefix("storage://trading-manager/")
        if not source_path.exists():
            raise TaskSystemError(f"option-chain source task key does not exist: {source_path}")
        task_key = json.loads(source_path.read_text(encoding="utf-8"))
        runtime_task_key = storage_root / "runtime" / "provider_task_keys" / request_id / "task_key.json"
        command_path = source_path
        runtime_retained = False
        if execute_provider_calls:
            runtime_task_key.parent.mkdir(parents=True, exist_ok=True)
            runtime_task_key.write_text(json.dumps(_runtime_task_key(task_key), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            command_path = runtime_task_key
            runtime_retained = True
        command = [sys.executable, "-m", "data_source.option_chain_state_source", str(command_path), "--run-id", _run_id(request_id)]
        receipt_path = str(Path(str(task_key.get("output_root") or "")) / "completion_receipt.json")
        if not execute_provider_calls:
            return ProviderDispatchItem(
                request_id=request_id,
                task_key_path=str(source_path),
                runtime_task_key_path=None,
                runtime_task_key_retained=False,
                command=command,
                receipt_path=receipt_path,
                status="validated_not_dispatched",
                worker_id=f"provider-worker-{worker_slot}",
                worker_slot=worker_slot,
            )
        params = task_key.get("params") if isinstance(task_key.get("params"), Mapping) else {}
        timeout_seconds = max(180, int(params.get("timeout_seconds") or OPTION_CHAIN_PROVIDER_CONTROLS["timeout_seconds"]) + 60)
        try:
            result = subprocess.run(
                command,
                cwd=trading_data_root,
                env={**os.environ, "PYTHONPATH": str(trading_data_root / "src")},
                check=False,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
            stdout = result.stdout
            stderr = result.stderr
            return_code = result.returncode
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            return_code = -1
            timed_out = True
        succeeded = return_code == 0
        runtime_key_path = str(runtime_task_key)
        if succeeded:
            try:
                runtime_task_key.unlink()
                runtime_retained = False
                runtime_key_path = None
            except FileNotFoundError:
                runtime_retained = False
                runtime_key_path = None
        error_tail = None if succeeded else "\n".join(
            part
            for part in (
                f"provider subprocess timed out after {timeout_seconds}s" if timed_out else "",
                stdout[-500:],
                stderr[-500:],
            )
            if part
        )
        if return_code != 0 and not continue_on_error:
            raise TaskSystemError(f"option-chain source dispatch failed for {request_id}: {stderr[-500:] or stdout[-500:] or error_tail}")
        return ProviderDispatchItem(
            request_id=request_id,
            task_key_path=str(source_path),
            runtime_task_key_path=runtime_key_path,
            runtime_task_key_retained=runtime_retained,
            command=command,
            receipt_path=receipt_path,
            status="dispatched_succeeded" if succeeded else "dispatched_failed",
            worker_id=f"provider-worker-{worker_slot}",
            worker_slot=worker_slot,
            return_code=return_code,
            error_summary=error_tail,
        )

    items: list[ProviderDispatchItem] = []
    if execute_provider_calls:
        for row in rows:
            items.append(dispatch_one(row, worker_slot=1))
    else:
        worker_count = max(1, worker_selection.selected_worker_count)
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {executor.submit(dispatch_one, row, worker_slot=(index % worker_count) + 1): index for index, row in enumerate(rows)}
            by_index: dict[int, ProviderDispatchItem] = {}
            for future in as_completed(futures):
                by_index[futures[future]] = future.result()
        items = [by_index[index] for index in range(len(rows))]
    dispatch_count = sum(1 for item in items if item.status in {"dispatched_succeeded", "dispatched_failed"})
    return ProviderDispatchSummary(
        contract_type="manager_provider_dispatch_summary",
        stage_id=STAGE_ID,
        request_count=len(rows),
        validation_count=0,
        dispatch_count=dispatch_count,
        provider_calls=dispatch_count,
        dispatch_performed=execute_provider_calls,
        model_activation_performed=False,
        broker_execution_performed=False,
        items=tuple(items),
        worker_selection=worker_selection,
    )


def write_review(review: OptionChainSourceReview, *, output: TextIO) -> None:
    json.dump(review.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare shared option-chain source acquisition before Layer 3.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--target-symbol", required=True)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--source-output-root", type=Path, default=DEFAULT_SOURCE_OUTPUT_ROOT)
    parser.add_argument("--database-url")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--persist-sql", action="store_true")
    args = parser.parse_args(argv)
    review, _requests, _task_keys = prepare_option_chain_source_acquisition(
        start_month=args.start_month,
        end_month=args.end_month,
        target_symbol=args.target_symbol,
        storage_root=args.storage_root,
        source_output_root=args.source_output_root,
        write=args.write,
        persist_sql=args.persist_sql,
        database_url=args.database_url,
    )
    write_review(review, output=sys.stdout)
    return 0 if review.status in {"provider_acquisition_ready", "no_provider_skip_accepted"} else 2


__all__ = [
    "REQUEST_KIND",
    "SOURCE_ID",
    "STAGE_ID",
    "TARGET_COMPONENT_ID",
    "OptionChainSourceReview",
    "dispatch_option_chain_source_acquisition",
    "is_regular_us_equity_trading_day",
    "iter_regular_trading_days",
    "manager_requests_from_review",
    "prepare_option_chain_source_acquisition",
    "request_previews_for_replay_decision_times",
    "request_previews_for_fold",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

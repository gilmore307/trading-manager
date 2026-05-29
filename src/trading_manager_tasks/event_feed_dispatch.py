"""Bounded dispatcher for Layer 10 event-feed backfill artifacts.

The preparation step writes dry-run-safe task keys. This dispatcher is the
reviewable boundary that may convert a selected key into an autonomous
historical provider acquisition runtime key and invoke the matching
``trading-data`` feed command. It never activates models, constructs or submits
broker orders, mutates accounts, or writes dashboard read models.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .event_feed_backfill import REQUIRED_EVENT_FEED_IDS, SOURCE_BY_FEED_ID, plan_event_feed_requests
from .provider_dispatch import (
    DEFAULT_PROVIDER_STAGE_MAX_WORKERS,
    DEFAULT_TRADING_DATA_ROOT,
    ProviderWorkerSelection,
    select_provider_worker_count,
)
from .request_payloads import DEFAULT_STORAGE_ROOT, storage_uri_to_local_path

FEED_MODULE_BY_ID = {
    "03_feed_alpaca_news": "data_feed.03_feed_alpaca_news",
    "05_feed_gdelt_news": "data_feed.05_feed_gdelt_news",
    "08_feed_sec_company_financials": "data_feed.08_feed_sec_company_financials",
}

PROVIDER_CONTROLS_BY_FEED_ID = {
    "03_feed_alpaca_news": {
        "allowed_providers": ["alpaca"],
        "allowed_endpoint_families": ["news"],
        "max_requests": 10,
        "max_rows": 500,
        "max_symbols": 1,
        "max_time_window": "45d",
    },
    "05_feed_gdelt_news": {
        "allowed_providers": ["gdelt_bigquery"],
        "allowed_endpoint_families": ["news_query"],
        "max_requests": 1,
        "max_rows": 250,
        "max_time_window": "45d",
    },
    "08_feed_sec_company_financials": {
        "allowed_providers": ["sec_edgar"],
        "allowed_endpoint_families": ["company_financials"],
        "max_requests": 1,
    },
}


@dataclass(frozen=True)
class EventFeedDispatchItem:
    request_id: str
    feed_id: str
    source_id: str
    task_key_path: str
    runtime_task_key_path: str | None
    runtime_task_key_retained: bool
    command: list[str]
    receipt_path: str
    status: str
    return_code: int | None = None
    error_summary: str | None = None
    attempt_count: int = 0
    browser_ui_fallback_required: bool = False

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventFeedDispatchSummary:
    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    target_symbol: str
    request_count: int
    validation_count: int
    dispatch_count: int
    provider_calls: int
    dispatch_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    worker_selection: ProviderWorkerSelection
    items: tuple[EventFeedDispatchItem, ...]

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "stage_id": self.stage_id,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "target_symbol": self.target_symbol,
            "request_count": self.request_count,
            "validation_count": self.validation_count,
            "dispatch_count": self.dispatch_count,
            "provider_calls": self.provider_calls,
            "dispatch_performed": self.dispatch_performed,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "dashboard_read_model_writes": self.dashboard_read_model_writes,
            "worker_selection": self.worker_selection.summary_row(),
            "items": [item.summary_row() for item in self.items],
        }


def _run_id(request_id: str, *, attempt: int = 1) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = "" if attempt == 1 else f"_retry_{attempt}"
    return f"{request_id}_event_feed_{stamp}{suffix}"


def _filter_requests(
    requests: Sequence[Mapping[str, Any]],
    *,
    feed_ids: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    feed_filter = {item.strip() for item in feed_ids if item.strip()}
    unknown_feeds = sorted(feed_filter - set(REQUIRED_EVENT_FEED_IDS))
    if unknown_feeds:
        raise TaskSystemError("unsupported event feed ids: " + ",".join(unknown_feeds))
    request_filter = {item.strip() for item in request_ids if item.strip()}
    selected: list[dict[str, Any]] = []
    for row in requests:
        feed_ok = not feed_filter or str(row.get("target_component_id") or "") in feed_filter
        request_ok = not request_filter or str(row.get("request_id") or "") in request_filter
        if feed_ok and request_ok:
            selected.append(dict(row))
    if request_filter:
        found = {str(row.get("request_id") or "") for row in selected}
        missing = sorted(request_filter - found)
        if missing:
            raise TaskSystemError("requested event feed ids are not in the planned batch: " + ",".join(missing))
    if limit is not None:
        if limit <= 0:
            raise TaskSystemError("limit must be positive")
        selected = selected[:limit]
    if not selected:
        raise TaskSystemError("event feed dispatch filter selected no requests")
    return selected


def _autonomous_event_feed_task_key(task_key: Mapping[str, Any]) -> dict[str, Any]:
    runtime_key = dict(task_key)
    feed_id = str(runtime_key.get("feed") or "")
    runtime_key["dry_run"] = False
    runtime_key["production_mode"] = "historical_provider_acquisition"
    controls = dict(runtime_key.get("manager_controls") or {})
    controls["allow_live_provider_calls"] = True
    controls["autonomous_historical_provider_acquisition"] = True
    controls.update(PROVIDER_CONTROLS_BY_FEED_ID.get(feed_id, {}))
    runtime_key["manager_controls"] = controls
    params = dict(runtime_key.get("params") or {})
    params["manager_dry_run"] = False
    if feed_id == "05_feed_gdelt_news":
        params["dry_run"] = False
    runtime_key["params"] = params
    policy_refs = [str(item) for item in runtime_key.get("policy_refs") or []]
    if "autonomous_historical_provider_acquisition" not in policy_refs:
        policy_refs.append("autonomous_historical_provider_acquisition")
    runtime_key["policy_refs"] = policy_refs
    return runtime_key


def _command(feed_id: str, task_key_path: Path, request_id: str, *, attempt: int = 1) -> list[str]:
    module = FEED_MODULE_BY_ID.get(feed_id)
    if module is None:
        raise TaskSystemError(f"unsupported event feed dispatch target: {feed_id}")
    return ["python3", "-m", module, str(task_key_path), "--run-id", _run_id(request_id, attempt=attempt)]


def _pythonpath(trading_data_root: Path) -> str:
    parts = [str(trading_data_root / "src")]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        parts.append(existing)
    # GDELT uses the trading-manager BigQuery helper package.
    manager_src = Path(__file__).resolve().parents[1]
    if str(manager_src) not in parts:
        parts.append(str(manager_src))
    return os.pathsep.join(parts)


def dispatch_event_feed_backfill(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str = "AAPL",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    feed_ids: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    execute_provider_calls: bool = False,
    continue_on_error: bool = False,
    dynamic_workers: bool = True,
    max_workers: int = DEFAULT_PROVIDER_STAGE_MAX_WORKERS,
    te_retry_delay_seconds: int = 60,
) -> EventFeedDispatchSummary:
    """Validate or run selected Layer 10 event-feed backfill task keys."""

    planned = plan_event_feed_requests(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
    selected = _filter_requests(planned, feed_ids=feed_ids, request_ids=request_ids, limit=limit)
    worker_selection = select_provider_worker_count(
        request_count=len(selected),
        execute_provider_calls=execute_provider_calls,
        dynamic_workers=dynamic_workers,
        max_workers=max_workers,
    )
    items: list[EventFeedDispatchItem] = []
    for row in selected:
        request_id = str(row["request_id"])
        feed_id = str(row["target_component_id"])
        source_id = SOURCE_BY_FEED_ID[feed_id]
        task_key_path = storage_uri_to_local_path(str(row["parameter_ref"]), storage_root=storage_root).resolve()
        if not task_key_path.exists():
            raise TaskSystemError(f"prepared event feed task key does not exist: {task_key_path}")
        task_key = json.loads(task_key_path.read_text(encoding="utf-8"))
        if not isinstance(task_key, Mapping):
            raise TaskSystemError(f"event feed task key must be a JSON object: {task_key_path}")
        if str(task_key.get("feed") or "") != feed_id:
            raise TaskSystemError(f"event feed task key feed mismatch for {task_key_path}: expected {feed_id}")
        command_path = task_key_path
        runtime_task_key_path: Path | None = None
        runtime_task_key_retained = False
        status = "validated_not_dispatched"
        return_code = None
        error_summary = None
        if execute_provider_calls:
            runtime_task_key_path = (storage_root / "runtime" / "event_feed_task_keys" / request_id / "task_key.json").resolve()
            runtime_task_key_path.parent.mkdir(parents=True, exist_ok=True)
            runtime_task_key_path.write_text(
                json.dumps(_autonomous_event_feed_task_key(task_key), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            command_path = runtime_task_key_path
            runtime_task_key_retained = True
        command = _command(feed_id, command_path, request_id)
        receipt_path = str((trading_data_root / str(task_key.get("output_root") or "storage") / "completion_receipt.json").resolve())
        attempt_count = 0
        browser_ui_fallback_required = False
        if execute_provider_calls:
            max_attempts = 1
            last_result = None
            for attempt in range(1, max_attempts + 1):
                attempt_count = attempt
                if attempt > 1:
                    if te_retry_delay_seconds > 0:
                        time.sleep(te_retry_delay_seconds)
                    command = _command(feed_id, command_path, request_id, attempt=attempt)
                result = subprocess.run(
                    command,
                    cwd=trading_data_root,
                    env={**os.environ, "PYTHONPATH": _pythonpath(trading_data_root)},
                    check=False,
                    text=True,
                    capture_output=True,
                )
                last_result = result
                if result.returncode == 0:
                    break
            if last_result is None:  # pragma: no cover - execute_provider_calls guards this block.
                raise TaskSystemError("internal dispatch error: no subprocess result")
            return_code = last_result.returncode
            status = "dispatched_succeeded" if last_result.returncode == 0 else "dispatched_failed"
            if last_result.returncode == 0 and runtime_task_key_path is not None:
                try:
                    runtime_task_key_path.unlink()
                    runtime_task_key_retained = False
                except FileNotFoundError:
                    runtime_task_key_retained = False
            if last_result.returncode != 0:
                error_summary = "\n".join(part for part in (last_result.stdout[-500:], last_result.stderr[-500:]) if part)
                if not continue_on_error:
                    raise TaskSystemError(f"event feed dispatch failed for {request_id}: {error_summary}")
        items.append(
            EventFeedDispatchItem(
                request_id=request_id,
                feed_id=feed_id,
                source_id=source_id,
                task_key_path=str(task_key_path),
                runtime_task_key_path=str(runtime_task_key_path) if runtime_task_key_path is not None and runtime_task_key_retained else None,
                runtime_task_key_retained=runtime_task_key_retained,
                command=command,
                receipt_path=receipt_path,
                status=status,
                return_code=return_code,
                error_summary=error_summary,
                attempt_count=attempt_count,
                browser_ui_fallback_required=browser_ui_fallback_required,
            )
        )
    dispatch_count = sum(1 for item in items if item.status in {"dispatched_succeeded", "dispatched_failed", "dispatched_failed_browser_ui_fallback_required"})
    provider_call_count = sum(item.attempt_count for item in items if item.attempt_count)
    return EventFeedDispatchSummary(
        contract_type="manager_layer_10_event_feed_dispatch_summary",
        stage_id="layer_10_event_risk_governor.event_feed_backfill",
        start_month=start_month,
        end_month=end_month,
        target_symbol=target_symbol.upper(),
        request_count=len(selected),
        validation_count=len(selected) if not execute_provider_calls else 0,
        dispatch_count=dispatch_count,
        provider_calls=provider_call_count,
        dispatch_performed=execute_provider_calls,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        worker_selection=worker_selection,
        items=tuple(items),
    )


def write_dispatch_summary(summary: EventFeedDispatchSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or dispatch bounded Layer 10 event-feed backfill task keys.")
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--target-symbol", default="AAPL")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--feed-id", action="append", default=[], choices=REQUIRED_EVENT_FEED_IDS)
    parser.add_argument("--request-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--execute-provider-calls", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dynamic-workers", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_PROVIDER_STAGE_MAX_WORKERS)
    parser.add_argument("--te-retry-delay-seconds", type=int, default=60)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args(argv)
    summary = dispatch_event_feed_backfill(
        start_month=args.start_month,
        end_month=args.end_month,
        target_symbol=args.target_symbol,
        storage_root=args.storage_root,
        trading_data_root=args.trading_data_root,
        feed_ids=args.feed_id,
        request_ids=args.request_id,
        limit=args.limit,
        execute_provider_calls=args.execute_provider_calls,
        continue_on_error=args.continue_on_error,
        dynamic_workers=args.dynamic_workers,
        max_workers=args.max_workers,
        te_retry_delay_seconds=args.te_retry_delay_seconds,
    )
    if args.write:
        if args.output_path is None:
            raise TaskSystemError("--write requires --output-path")
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_dispatch_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "EventFeedDispatchItem",
    "EventFeedDispatchSummary",
    "dispatch_event_feed_backfill",
    "write_dispatch_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

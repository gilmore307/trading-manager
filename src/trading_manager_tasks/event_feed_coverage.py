"""Neutral event-feed coverage helpers for model input gates.

This module only discovers reviewed local event-feed artifacts and counts
requested-window rows. It does not own M03 event-state semantics, M06 residual
attribution, provider dispatch, model activation, broker execution, or storage
lifecycle mutation.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .control_plane import TaskSystemError
from .storage_paths import data_storage_root

DEFAULT_TRADING_STORAGE_ROOT = data_storage_root()
EVENT_FEED_ARTIFACTS = {
    "alpaca_news": "equity_news.csv",
    "gdelt_news": "gdelt_article.csv",
    "sec_company_financials": "sec_company_fact.csv",
    "market_session_calendar": "generated_market_session_calendar",
    "trading_economics_calendar_web": "trading_economics_calendar_event.csv",
    "release_calendar": "release_calendar.csv",
}
REQUIRED_EVENT_FEED_ARTIFACTS = {
    "alpaca_news": EVENT_FEED_ARTIFACTS["alpaca_news"],
    "gdelt_news": EVENT_FEED_ARTIFACTS["gdelt_news"],
    "sec_company_financials": EVENT_FEED_ARTIFACTS["sec_company_financials"],
    "market_session_calendar": EVENT_FEED_ARTIFACTS["market_session_calendar"],
    "trading_economics_calendar_web": EVENT_FEED_ARTIFACTS["trading_economics_calendar_web"],
}
EVENT_FEED_TIME_FIELDS = {
    "alpaca_news": ("created_at", "updated_at"),
    "gdelt_news": ("seen_at", "gdelt_date"),
    "sec_company_financials": ("filing_date", "filed", "end", "report_date"),
    "market_session_calendar": ("event_time", "calendar_date"),
    "trading_economics_calendar_web": ("event_time",),
    "release_calendar": ("release_time", "event_date"),
}
ET = ZoneInfo("America/New_York")


def validate_month(month: str) -> tuple[int, int]:
    if len(month) != 7 or month[4] != "-":
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number < 1 or month_number > 12:
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    return year, month_number


def next_month(month: str) -> str:
    year, month_number = validate_month(month)
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def iter_months(start_month: str, end_month: str) -> Iterable[str]:
    validate_month(start_month)
    validate_month(end_month)
    if start_month > end_month:
        raise TaskSystemError(f"start_month must be <= end_month: {start_month} > {end_month}")
    month = start_month
    while month <= end_month:
        yield month
        month = next_month(month)


def month_bounds(month: str) -> tuple[str, str]:
    year, month_number = validate_month(month)
    next_month_value = next_month(month)
    next_year, next_month_number = int(next_month_value[:4]), int(next_month_value[5:])
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00", f"{next_year:04d}-{next_month_number:02d}-01T00:00:00-05:00"


def range_bounds(start_month: str, end_month: str) -> tuple[str, str]:
    start, _ = month_bounds(start_month)
    _, end = month_bounds(end_month)
    return start, end


def discover_event_feed_artifacts(
    *,
    trading_storage_root: Path | None = None,
    trading_data_root: Path | None = None,
    start_month: str,
    end_month: str,
) -> tuple[list[str], dict[str, int]]:
    """Return reviewed saved feed artifacts available in the requested fold."""

    root = trading_storage_root or (trading_data_root / "storage" if trading_data_root is not None else DEFAULT_TRADING_STORAGE_ROOT)
    base = root / "monthly_backfill"
    paths: list[str] = []
    coverage = {source_id: 0 for source_id in EVENT_FEED_ARTIFACTS}
    for month in iter_months(start_month, end_month):
        for source_id, filename in EVENT_FEED_ARTIFACTS.items():
            candidates = sorted((base / source_id / month).glob(f"runs/*/saved/{filename}"))
            candidates.extend(sorted((base / source_id / month).glob(f"saved/{filename}")))
            unique = [candidate for candidate in dict.fromkeys(candidates) if candidate.exists()]
            if unique:
                latest = max(unique, key=lambda candidate: (candidate.stat().st_mtime_ns, str(candidate)))
                coverage[source_id] += 1
                paths.append(str(latest))
    return paths, coverage


def missing_event_feed_artifacts(coverage: Mapping[str, int]) -> list[str]:
    return [source_id for source_id in REQUIRED_EVENT_FEED_ARTIFACTS if int(coverage.get(source_id) or 0) <= 0]


def parse_event_feed_time(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return datetime.fromisoformat(f"{text}T00:00:00-05:00").astimezone(ET)
    if len(text) == 14 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d%H%M%S").replace(tzinfo=UTC).astimezone(ET)
    if len(text) == 8 and text.isdigit():
        return datetime.strptime(text, "%Y%m%d").replace(tzinfo=UTC).astimezone(ET)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ET)
    return parsed.astimezone(ET)


def event_feed_source_from_path(path: str | Path) -> str | None:
    text = str(path)
    for source_id in EVENT_FEED_ARTIFACTS:
        if f"/{source_id}/" in text or text.startswith(f"{source_id}/"):
            return source_id
    return None


def event_feed_window_row_count(source_id: str, path: Path, *, start: datetime, end: datetime) -> int:
    fields = EVENT_FEED_TIME_FIELDS[source_id]
    count = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            event_time = None
            for field in fields:
                value = row.get(field)
                if value:
                    event_time = parse_event_feed_time(value)
                    if event_time is not None:
                        break
            if event_time is not None and start <= event_time < end:
                count += 1
    return count


def event_feed_row_coverage(event_artifact_paths: Sequence[str], *, start_month: str, end_month: str) -> dict[str, int]:
    start_text, end_text = range_bounds(start_month, end_month)
    start = parse_event_feed_time(start_text)
    end = parse_event_feed_time(end_text)
    if start is None or end is None:
        raise TaskSystemError(f"invalid event-feed coverage bounds: {start_text} -> {end_text}")
    coverage = {source_id: 0 for source_id in EVENT_FEED_ARTIFACTS}
    for raw_path in event_artifact_paths:
        source_id = event_feed_source_from_path(raw_path)
        if source_id is None:
            continue
        path = Path(raw_path)
        if not path.exists():
            continue
        coverage[source_id] += event_feed_window_row_count(source_id, path, start=start, end=end)
    return coverage


def missing_event_feed_rows(row_coverage: Mapping[str, int]) -> list[str]:
    return [source_id for source_id in REQUIRED_EVENT_FEED_ARTIFACTS if int(row_coverage.get(source_id) or 0) <= 0]


def successful_feed_runs(receipt_path: Path) -> tuple[Mapping[str, Any], ...]:
    if not receipt_path.exists():
        return ()
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    runs = receipt.get("runs")
    if not isinstance(runs, list):
        return ()
    return tuple(run for run in runs if isinstance(run, Mapping) and str(run.get("status") or "") == "succeeded")


__all__ = [
    "EVENT_FEED_ARTIFACTS",
    "EVENT_FEED_TIME_FIELDS",
    "REQUIRED_EVENT_FEED_ARTIFACTS",
    "discover_event_feed_artifacts",
    "event_feed_row_coverage",
    "iter_months",
    "missing_event_feed_artifacts",
    "missing_event_feed_rows",
    "month_bounds",
    "range_bounds",
    "successful_feed_runs",
]

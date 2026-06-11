"""Trading Economics calendar storage-source planning.

This module separates canonical storage source maintenance from M06 event
admission. Recent/future calendar polling may acquire Trading Economics rows
into storage source artifacts, but it does not materialize SQL event rows,
activate models, submit broker orders, or mutate accounts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, TextIO

from .control_plane import TaskSystemError
from .monthly_backfill import iter_monthly_windows
from .provider_dispatch import DEFAULT_TRADING_DATA_ROOT
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_TE_MONTHLY_ROOT = data_storage_root() / "monthly_backfill" / "trading_economics_calendar_web"
DEFAULT_RECENT_LOOKAHEAD_DAYS = 45
TE_FEED_ID = "07_feed_trading_economics_calendar_web"


def _te_monthly_root(trading_data_root: Path) -> Path:
    root = Path(trading_data_root)
    if root == DEFAULT_TRADING_DATA_ROOT:
        return DEFAULT_TE_MONTHLY_ROOT
    storage_owned = root / "monthly_backfill" / "trading_economics_calendar_web"
    if storage_owned.exists():
        return storage_owned
    component_local = root / "storage" / "monthly_backfill" / "trading_economics_calendar_web"
    if component_local.exists():
        return component_local
    return storage_owned


@dataclass(frozen=True)
class TeCalendarArtifact:
    month: str
    path: str
    row_count: int
    selected: bool

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TeHistoricalSeedSummary:
    contract_type: str
    start_month: str
    end_month: str
    expected_month_count: int
    covered_month_count: int
    missing_months: tuple[str, ...]
    selected_artifacts: tuple[TeCalendarArtifact, ...]
    task_key_path: str | None
    task_key_hash: str | None
    write_performed: bool
    retired_reason: str | None
    provider_calls: int
    database_writes_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["selected_artifacts"] = [item.summary_row() for item in self.selected_artifacts]
        return row


@dataclass(frozen=True)
class TeRecentPollSummary:
    contract_type: str
    start_date: str
    end_date_exclusive: str
    task_key_path: str | None
    task_key_hash: str | None
    write_performed: bool
    date_range_mode: str
    use_authenticated_cookies: bool
    retired_reason: str | None
    provider_calls: int
    database_writes_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _month_list(start_month: str, end_month: str) -> list[str]:
    return [window.month for window in iter_monthly_windows(start_month, end_month)]


def _parse_event_date(value: str) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    for pattern in ("%A %B %d %Y", "%A %b %d %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    return None


def _read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _in_month_rows(path: Path, *, month: str) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames, rows = _read_csv_rows(path)
    return fieldnames, [row for row in rows if (_parse_event_date(row.get("event_time", "")) or date.min).isoformat().startswith(f"{month}-")]


def _row_count(path: Path, *, month: str | None = None) -> int:
    if month is None:
        return len(_read_csv_rows(path)[1])
    return len(_in_month_rows(path, month=month)[1])


def _month_artifact_paths(month_dir: Path) -> list[Path]:
    return sorted(month_dir.glob("runs/*/saved/trading_economics_calendar_event.csv"))


def _merge_month_rows(*, month: str, paths: list[Path]) -> tuple[list[str], list[dict[str, str]], list[str]]:
    fieldnames: list[str] = []
    rows: list[dict[str, str]] = []
    source_paths: list[str] = []
    for path in paths:
        path_fieldnames, path_rows = _in_month_rows(path, month=month)
        if not path_rows:
            continue
        for field in path_fieldnames:
            if field not in fieldnames:
                fieldnames.append(field)
        rows.extend(path_rows)
        source_paths.append(str(path.resolve()))
    unique: list[dict[str, str]] = []
    seen: set[tuple[str, ...]] = set()
    for row in rows:
        key = tuple(str(row.get(field, "")) for field in fieldnames)
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return fieldnames, unique, source_paths


def _filtered_artifact_path(*, month: str, storage_root: Path) -> Path:
    return storage_root / "runtime" / "te_calendar" / "historical_seed" / "filtered_artifacts" / month / "trading_economics_calendar_event.csv"


def _month_artifact_summary(month_dir: Path, *, storage_root: Path) -> TeCalendarArtifact | None:
    _, rows, _ = _merge_month_rows(month=month_dir.name, paths=_month_artifact_paths(month_dir))
    if not rows:
        return None
    return TeCalendarArtifact(month=month_dir.name, path=str(_filtered_artifact_path(month=month_dir.name, storage_root=storage_root).resolve()), row_count=len(rows), selected=True)


def discover_historical_seed_artifacts(*, start_month: str, end_month: str, trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT, storage_root: Path = DEFAULT_STORAGE_ROOT) -> tuple[list[TeCalendarArtifact], list[str]]:
    root = _te_monthly_root(trading_data_root)
    selected: list[TeCalendarArtifact] = []
    missing: list[str] = []
    for month in _month_list(start_month, end_month):
        artifact = _month_artifact_summary(root / month, storage_root=storage_root)
        if artifact is None:
            missing.append(month)
        else:
            selected.append(artifact)
    return selected, missing


def plan_historical_seed(*, start_month: str, end_month: str, trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT, storage_root: Path = DEFAULT_STORAGE_ROOT, write_files: bool = False) -> TeHistoricalSeedSummary:
    artifacts, missing = discover_historical_seed_artifacts(start_month=start_month, end_month=end_month, trading_data_root=trading_data_root, storage_root=storage_root)
    return TeHistoricalSeedSummary(
        contract_type="te_calendar_historical_seed_retired",
        start_month=start_month,
        end_month=end_month,
        expected_month_count=len(_month_list(start_month, end_month)),
        covered_month_count=len(artifacts),
        missing_months=tuple(missing),
        selected_artifacts=tuple(artifacts),
        task_key_path=None,
        task_key_hash=None,
        write_performed=False,
        retired_reason="TE macro rows stay in canonical storage and are not materialized into model_06_residual_event_governance_data_acquisition until a later accepted M06 route promotes them.",
        provider_calls=0,
        database_writes_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
    )


def _recent_task_key(*, start: date, end: date, output_root: str) -> dict[str, Any]:
    return {
        "feed": TE_FEED_ID,
        "task_id": f"te_calendar_recent_{start.isoformat()}_{end.isoformat()}",
        "output_root": output_root,
        "params": {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "country": "United States",
            "importance": "3",
            "allow_live_fetch": True,
            "date_range_mode": "recent",
            "use_authenticated_cookies": False,
            "persist_failure_diagnostics": True,
            "monthly_backfill_bucketed_output": True,
            "source_materialization_role": "append_to_trading_economics_monthly_backfill",
        },
        "manager_controls": {
            "allow_live_provider_calls": True,
            "autonomous_historical_provider_acquisition": False,
            "realtime_provider_maintenance": True,
            "allowed_providers": ["trading_economics"],
            "allowed_endpoint_families": ["calendar_web"],
            "max_requests": 1,
            "max_time_window": "45d",
            "retry_policy_ref": "trading-data://provider-policy/recent-calendar-single-request",
            "rate_limit_policy_ref": "trading-data://provider-policy/trading-economics-recent-calendar",
            "website_url_persistence": False,
            "database_writes_performed": False,
            "model_activation_performed": False,
            "broker_execution_performed": False,
        },
        "policy_refs": [
            "bounded_recent_future_calendar_fetch",
            "append_to_storage_source_only",
            "no_website_url_persistence",
            "no_m06_sql_materialization",
            "no_model_activation",
            "no_broker_execution",
        ],
    }


def plan_recent_poll(*, as_of_date: date | None = None, lookahead_days: int = DEFAULT_RECENT_LOOKAHEAD_DAYS, storage_root: Path = DEFAULT_STORAGE_ROOT, write_files: bool = False) -> TeRecentPollSummary:
    if lookahead_days <= 0 or lookahead_days > 45:
        raise TaskSystemError("lookahead_days must be between 1 and 45")
    start = as_of_date or datetime.now(UTC).date()
    end = start + timedelta(days=lookahead_days)
    payload = _recent_task_key(start=start, end=end, output_root="storage/monthly_backfill/trading_economics_calendar_web")
    content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    task_hash = "sha256:" + hashlib.sha256(content).hexdigest()
    task_key_path = (storage_root / "runtime" / "te_calendar" / "recent" / f"{start.isoformat()}_task_key.json").resolve()
    if write_files:
        task_key_path.parent.mkdir(parents=True, exist_ok=True)
        task_key_path.write_bytes(content)
    return TeRecentPollSummary(
        contract_type="te_calendar_recent_poll_plan",
        start_date=start.isoformat(),
        end_date_exclusive=end.isoformat(),
        task_key_path=str(task_key_path),
        task_key_hash=task_hash,
        write_performed=write_files,
        date_range_mode="recent",
        use_authenticated_cookies=False,
        retired_reason=None,
        provider_calls=0,
        database_writes_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
    )


def write_summary(summary: TeHistoricalSeedSummary | TeRecentPollSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Trading Economics calendar storage-source task keys.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    seed = subparsers.add_parser("historical-seed")
    seed.add_argument("--start-month", required=True)
    seed.add_argument("--end-month", required=True)
    seed.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    seed.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    seed.add_argument("--write-files", action="store_true")
    recent = subparsers.add_parser("recent-poll")
    recent.add_argument("--as-of-date")
    recent.add_argument("--lookahead-days", type=int, default=DEFAULT_RECENT_LOOKAHEAD_DAYS)
    recent.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    recent.add_argument("--write-files", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "historical-seed":
        summary = plan_historical_seed(start_month=args.start_month, end_month=args.end_month, trading_data_root=args.trading_data_root, storage_root=args.storage_root, write_files=args.write_files)
    else:
        as_of = date.fromisoformat(args.as_of_date) if args.as_of_date else None
        summary = plan_recent_poll(as_of_date=as_of, lookahead_days=args.lookahead_days, storage_root=args.storage_root, write_files=args.write_files)
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "TeCalendarArtifact",
    "TeHistoricalSeedSummary",
    "TeRecentPollSummary",
    "discover_historical_seed_artifacts",
    "plan_historical_seed",
    "plan_recent_poll",
    "write_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Trading Economics calendar seed and realtime maintenance planning.

This module separates the one-time historical seed from the ongoing realtime
recent-calendar maintenance route. It only prepares task keys and summaries; it
never starts services, activates models, submits broker orders, or mutates
accounts.
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

TE_FEED_ID = "07_feed_trading_economics_calendar_web"
TE_SOURCE_ID = "trading_economics_calendar_web"
EVENT_SOURCE_ID = "source_09_event_risk_governor"
DEFAULT_TE_MONTHLY_ROOT = Path("storage/monthly_backfill/trading_economics_calendar_web")
DEFAULT_RECENT_LOOKAHEAD_DAYS = 45


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


def _write_filtered_artifact(*, source: TeCalendarArtifact, storage_root: Path) -> TeCalendarArtifact:
    source_path = Path(source.path)
    fieldnames, rows = _in_month_rows(source_path, month=source.month)
    target = storage_root / "runtime" / "te_calendar" / "historical_seed" / "filtered_artifacts" / source.month / "trading_economics_calendar_event.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "contract_type": "te_calendar_historical_seed_filtered_artifact_v1",
        "month": source.month,
        "source_artifact_path": source.path,
        "filtered_artifact_path": str(target.resolve()),
        "row_count": len(rows),
        "filter": "event_time month equals containing historical backfill month",
        "raw_original_deleted": False,
    }
    (target.parent / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return TeCalendarArtifact(month=source.month, path=str(target.resolve()), row_count=len(rows), selected=True)


def _latest_nonempty_artifact(month_dir: Path) -> TeCalendarArtifact | None:
    candidates: list[tuple[int, float, Path, int]] = []
    for path in month_dir.glob("runs/*/saved/trading_economics_calendar_event.csv"):
        rows = _row_count(path, month=month_dir.name)
        if rows > 0:
            candidates.append((rows, path.stat().st_mtime, path, rows))
    if not candidates:
        return None
    # Prefer the richest in-month artifact, then latest run time. This avoids
    # selecting wrong-window/current-page artifacts saved under an older month.
    _, _, path, rows = sorted(candidates, key=lambda item: (item[0], item[1], str(item[2])))[-1]
    return TeCalendarArtifact(month=month_dir.name, path=str(path.resolve()), row_count=rows, selected=True)


def discover_historical_seed_artifacts(*, start_month: str, end_month: str, trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT) -> tuple[list[TeCalendarArtifact], list[str]]:
    root = trading_data_root / DEFAULT_TE_MONTHLY_ROOT
    selected: list[TeCalendarArtifact] = []
    missing: list[str] = []
    for month in _month_list(start_month, end_month):
        artifact = _latest_nonempty_artifact(root / month)
        if artifact is None:
            missing.append(month)
        else:
            selected.append(artifact)
    return selected, missing


def _historical_seed_task_key(*, start_month: str, end_month: str, artifacts: list[TeCalendarArtifact], output_root: str) -> dict[str, Any]:
    start_date = f"{start_month}-01T00:00:00-05:00"
    end_window = list(iter_monthly_windows(end_month, end_month))[0]
    end_date = f"{end_window.end_date_exclusive}T00:00:00-05:00"
    return {
        "source": EVENT_SOURCE_ID,
        "task_id": f"te_calendar_historical_seed_{start_month.replace('-', '_')}_{end_month.replace('-', '_')}",
        "output_root": output_root,
        "params": {
            "start": start_date,
            "end": end_date,
            "feed_artifact_paths": [artifact.path for artifact in artifacts],
            "source_materialization_role": "historical_seed_to_event_risk_governor_source",
            "raw_artifact_retention": "deletable_after_successful_sql_ingest_and_manifest_review",
        },
        "manager_controls": {
            "provider_calls": 0,
            "database_write_target": "trading_data.source_09_event_risk_governor",
            "model_activation_performed": False,
            "broker_execution_performed": False,
        },
    }


def plan_historical_seed(*, start_month: str, end_month: str, trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT, storage_root: Path = DEFAULT_STORAGE_ROOT, write_files: bool = False) -> TeHistoricalSeedSummary:
    artifacts, missing = discover_historical_seed_artifacts(start_month=start_month, end_month=end_month, trading_data_root=trading_data_root)
    seed_artifacts = [_write_filtered_artifact(source=artifact, storage_root=storage_root) for artifact in artifacts] if write_files else artifacts
    task_key_path: Path | None = None
    task_hash: str | None = None
    if not missing:
        output_root = f"storage/runtime/source_09_event_risk_governor/te_calendar_historical_seed_{start_month}_{end_month}"
        payload = _historical_seed_task_key(start_month=start_month, end_month=end_month, artifacts=seed_artifacts, output_root=output_root)
        content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        task_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        task_key_path = (storage_root / "runtime" / "te_calendar" / "historical_seed" / f"{start_month}_{end_month}_source_09_task_key.json").resolve()
        if write_files:
            task_key_path.parent.mkdir(parents=True, exist_ok=True)
            task_key_path.write_bytes(content)
    return TeHistoricalSeedSummary(
        contract_type="te_calendar_historical_seed_plan_v1",
        start_month=start_month,
        end_month=end_month,
        expected_month_count=len(_month_list(start_month, end_month)),
        covered_month_count=len(artifacts),
        missing_months=tuple(missing),
        selected_artifacts=tuple(seed_artifacts),
        task_key_path=str(task_key_path) if task_key_path is not None else None,
        task_key_hash=task_hash,
        write_performed=write_files,
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
        },
        "manager_controls": {
            "allow_live_provider_calls": True,
            "autonomous_historical_provider_acquisition": False,
            "realtime_provider_maintenance": True,
            "allowed_providers": ["trading_economics"],
            "allowed_endpoint_families": ["calendar_web"],
            "max_requests": 1,
            "max_time_window": "45d",
            "model_activation_performed": False,
            "broker_execution_performed": False,
        },
        "policy_refs": ["logged_out_recent_calendar", "no_api_or_download_export", "no_model_activation", "no_broker_execution"],
    }


def plan_recent_poll(*, as_of_date: date | None = None, lookahead_days: int = DEFAULT_RECENT_LOOKAHEAD_DAYS, storage_root: Path = DEFAULT_STORAGE_ROOT, write_files: bool = False) -> TeRecentPollSummary:
    if lookahead_days <= 0 or lookahead_days > 45:
        raise TaskSystemError("lookahead_days must be between 1 and 45")
    start = as_of_date or datetime.now(UTC).date()
    end = start + timedelta(days=lookahead_days)
    output_root = f"storage/realtime/trading_economics_calendar_web/recent/{start.isoformat()}"
    payload = _recent_task_key(start=start, end=end, output_root=output_root)
    content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    task_hash = "sha256:" + hashlib.sha256(content).hexdigest()
    task_key_path = (storage_root / "runtime" / "te_calendar" / "recent" / f"{start.isoformat()}_task_key.json").resolve()
    if write_files:
        task_key_path.parent.mkdir(parents=True, exist_ok=True)
        task_key_path.write_bytes(content)
    return TeRecentPollSummary(
        contract_type="te_calendar_recent_poll_plan_v1",
        start_date=start.isoformat(),
        end_date_exclusive=end.isoformat(),
        task_key_path=str(task_key_path),
        task_key_hash=task_hash,
        write_performed=write_files,
        date_range_mode="recent",
        use_authenticated_cookies=False,
        provider_calls=0,
        database_writes_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
    )


def write_summary(summary: TeHistoricalSeedSummary | TeRecentPollSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Trading Economics calendar historical seed or recent poll task keys.")
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

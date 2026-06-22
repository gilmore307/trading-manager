"""Safe M06 event-risk input materialization.

This module builds ``model_06_residual_event_governance_data_acquisition`` SQL rows only from already-saved local
M02 bar SQL receipts. It may run the trading-data equity abnormal activity
source-detector, but it performs no provider calls, no model activation, no
broker execution, and no storage lifecycle mutation.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .layer_three_target_state import BAR_SOURCE_TABLE, FeedArtifactRef, _bar_source_ref, _latest_successful_run, discover_target_candidate_feed_artifacts
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_TRADING_STORAGE_ROOT = data_storage_root()
DEFAULT_TRADING_STORAGE_UNIVERSE = Path("/root/projects/trading-storage/main/shared/model_01_background_context_etf_universe.csv")
DEFAULT_OUTPUT_ROOT = Path("runtime") / "model_06_residual_event_governance" / "input_materialization"
LAYER_TWO_MODEL_LAYER = "model_01_sector_context"
DETECTOR_SOURCE = "m06_residual_event_governance_data_acquisition.equity_abnormal_activity"
SOURCE = "m06_residual_event_governance_data_acquisition"
REQUIRED_EVENT_FEED_ARTIFACTS = {
    "alpaca_news": "equity_news.csv",
    "gdelt_news": "gdelt_article.csv",
    "sec_company_financials": "sec_company_fact.csv",
}
EVENT_FEED_SQL_INPUTS = {
    "alpaca_news": {
        "table": "feed_03_alpaca_news",
        "kind": "alpaca_news",
        "columns": ["id", "timeline_headline", "created_at", "updated_at", "symbols", "summary", "event_link_url"],
        "time_column": "created_at",
        "order_by": ["created_at", "id"],
    },
    "gdelt_news": {
        "table": "feed_05_gdelt_article",
        "kind": "gdelt_news",
        "columns": [
            "article_id",
            "seen_at",
            "source_domain",
            "event_link_url",
            "title",
            "source_theme_tags",
            "organizations",
            "tone",
            "impact_scope",
        ],
        "time_column": "seen_at",
        "order_by": ["seen_at", "article_id"],
    },
    "sec_company_financials": {
        "table": "feed_08_sec_company_fact",
        "kind": "sec_company_financials",
        "columns": ["cik", "entity_name", "taxonomy", "tag", "label", "description", "unit", "fy", "fp", "form", "filed", "frame", "end", "value", "accession_number"],
        "time_column": "filed",
        "order_by": ["filed", "accession_number", "tag"],
    },
}
EVENT_FEED_TIME_FIELDS = {
    "alpaca_news": ("created_at", "updated_at"),
    "gdelt_news": ("seen_at", "gdelt_date"),
    "sec_company_financials": ("filing_date", "filed", "end", "report_date"),
}
ET = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class DetectorRunRef:
    symbol: str
    month: str
    task_key_path: str
    receipt_path: str
    saved_event_path: str | None
    event_count: int
    status: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResidualEventGovernanceInputMaterialization:
    contract_type: str
    start_month: str
    end_month: str
    detector_run_count: int
    detector_event_count: int
    source_event_count: int
    detector_runs: tuple[DetectorRunRef, ...]
    event_feed_artifact_paths: tuple[str, ...]
    event_feed_sql_inputs: tuple[dict[str, Any], ...]
    event_feed_coverage: dict[str, int]
    event_feed_row_coverage: dict[str, int]
    source_task_key_path: str
    source_receipt_path: str | None
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "detector_run_count": self.detector_run_count,
            "detector_event_count": self.detector_event_count,
            "source_event_count": self.source_event_count,
            "detector_runs": [item.summary_row() for item in self.detector_runs],
            "event_feed_artifact_paths": list(self.event_feed_artifact_paths),
            "event_feed_sql_inputs": list(self.event_feed_sql_inputs),
            "event_feed_coverage": dict(self.event_feed_coverage),
            "event_feed_row_coverage": dict(self.event_feed_row_coverage),
            "source_task_key_path": self.source_task_key_path,
            "source_receipt_path": self.source_receipt_path,
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
        }


def _validate_month(month: str) -> tuple[int, int]:
    if len(month) != 7 or month[4] != "-":
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number < 1 or month_number > 12:
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    return year, month_number


def _next_month(month: str) -> str:
    year, month_number = _validate_month(month)
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _iter_months(start_month: str, end_month: str) -> Iterable[str]:
    _validate_month(start_month)
    _validate_month(end_month)
    if start_month > end_month:
        raise TaskSystemError(f"start_month must be <= end_month: {start_month} > {end_month}")
    month = start_month
    while month <= end_month:
        yield month
        month = _next_month(month)


def _month_bounds(month: str) -> tuple[str, str]:
    year, month_number = _validate_month(month)
    next_month = _next_month(month)
    next_year, next_month_number = int(next_month[:4]), int(next_month[5:])
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00", f"{next_year:04d}-{next_month_number:02d}-01T00:00:00-05:00"


def _range_bounds(start_month: str, end_month: str) -> tuple[str, str]:
    start, _ = _month_bounds(start_month)
    _, end = _month_bounds(end_month)
    return start, end


def _fold_key(start_month: str, end_month: str) -> str:
    return f"{start_month.replace('-', '_')}_{end_month.replace('-', '_')}"


def _read_layer_two_symbols(universe_path: Path) -> tuple[str, ...]:
    with universe_path.open(newline="", encoding="utf-8") as handle:
        rows = [{str(k): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    symbols = sorted({row["symbol"].upper() for row in rows if row.get("symbol") and row.get("model_layer") == LAYER_TWO_MODEL_LAYER})
    if not symbols:
        raise TaskSystemError(f"no {LAYER_TWO_MODEL_LAYER} symbols found in {universe_path}")
    return tuple(symbols)


def _ref_month(ref: FeedArtifactRef) -> str:
    return str(getattr(ref, "month", "") or "unknown_month")


def _discover_layer_two_feed_artifacts_including_zero_rows(
    *,
    start_month: str,
    trading_data_root: Path,
    trading_storage_root: Path,
    universe_path: Path,
) -> tuple[FeedArtifactRef, ...]:
    refs = list(
        discover_target_candidate_feed_artifacts(
            start_month=start_month,
            trading_data_root=trading_data_root,
            trading_storage_root=trading_storage_root,
            universe_path=universe_path,
            symbols=_read_layer_two_symbols(universe_path),
        )
    )
    if refs:
        return tuple(refs)
    zero_refs: list[FeedArtifactRef] = []
    for symbol in _read_layer_two_symbols(universe_path):
        receipt_path = trading_storage_root / "monthly_backfill" / "alpaca_bars" / symbol / start_month / "completion_receipt.json"
        if not receipt_path.exists():
            continue
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        run = _latest_successful_run(receipt)
        if run is None:
            continue
        row_counts = run.get("row_counts") if isinstance(run.get("row_counts"), Mapping) else {}
        zero_refs.append(
            FeedArtifactRef(
                symbol=symbol,
                month=start_month,
                receipt_path=str(receipt_path),
                bar_source_ref=_bar_source_ref(run),
                run_id=str(run.get("run_id") or ""),
                row_count=int(row_counts.get("equity_bar") or 0),
            )
        )
    return tuple(zero_refs)


def _bar_sql_source(ref: FeedArtifactRef) -> dict[str, Any]:
    month = _ref_month(ref)
    start, end = _month_bounds(month) if month != "unknown_month" else (None, None)
    return {
        "table": BAR_SOURCE_TABLE,
        "source_ref": ref.bar_source_ref,
        "source_symbol": ref.evidence_symbol or ref.symbol,
        "target_symbol": ref.symbol,
        "month": month,
        "start": start,
        "end": end,
        "timeframe": "30Min",
        "receipt_path": ref.receipt_path,
        "run_id": ref.run_id,
        "row_count": ref.row_count,
    }


def _run_detector(
    ref: FeedArtifactRef,
    *,
    output_dir: Path,
    trading_data_output_root: Path,
    trading_data_root: Path,
    run_id: str,
    write: bool,
) -> DetectorRunRef:
    symbol = ref.symbol
    ref_month = _ref_month(ref)
    task_key_path = output_dir / "detectors" / symbol / ref_month / "task_key.json"
    detector_output_root = trading_data_output_root / DETECTOR_SOURCE.replace(".", "_") / symbol / ref_month
    receipt_path = detector_output_root / "completion_receipt.json"
    if ref.row_count <= 0:
        return DetectorRunRef(
            symbol=symbol,
            month=ref_month,
            task_key_path=str(task_key_path),
            receipt_path=str(receipt_path),
            saved_event_path=None,
            event_count=0,
            status="skipped_zero_bar_rows",
        )
    task_key = {
        "task_id": f"model_06_residual_event_governance_detector_{symbol}_{ref_month.replace('-', '_')}_{output_dir.name.replace('-', '_')}",
        "source": DETECTOR_SOURCE,
        "params": {
            "bars_sql_source": _bar_sql_source(ref),
        },
        "output_root": str(detector_output_root),
        "manager_stage_id": "model_06_residual_event_governance.data_acquisition",
        "source_policy": "local_source_detector_over_reviewed_m02_alpaca_bar_sql_receipts_no_provider_calls",
    }
    task_key_path.parent.mkdir(parents=True, exist_ok=True)
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    saved_event_path: str | None = None
    event_count = 0
    status = "prepared"
    if write:
        command = [sys.executable, "-m", "data_source.m06_residual_event_governance_data_acquisition.equity_abnormal_activity", str(task_key_path), "--run-id", f"{run_id}_{symbol.lower()}"]
        result = subprocess.run(command, cwd=trading_data_root, env={**os.environ, "PYTHONPATH": "src"}, text=True, capture_output=True, check=False)
        log_dir = output_dir / "logs" / "detectors"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{symbol}_{ref_month}.stdout.log").write_text(result.stdout, encoding="utf-8")
        (log_dir / f"{symbol}_{ref_month}.stderr.log").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            if "bar input produced zero rows" in result.stdout or "bar input produced zero rows" in result.stderr:
                return DetectorRunRef(
                    symbol=symbol,
                    month=ref_month,
                    task_key_path=str(task_key_path),
                    receipt_path=str(receipt_path),
                    saved_event_path=None,
                    event_count=0,
                    status="skipped_zero_sql_bar_rows",
                )
            raise TaskSystemError(f"M06 detector failed for {symbol}: {result.stderr.strip() or result.stdout.strip()}")
        payload = json.loads(result.stdout)
        status = str(payload.get("status") or "succeeded")
        event_count = int((payload.get("row_counts") or {}).get("equity_abnormal_activity_event") or 0)
        references = [str(item) for item in payload.get("references") or []]
        saved_event_path = next((item for item in references if item.endswith("equity_abnormal_activity_event.csv")), None)
    return DetectorRunRef(symbol=symbol, month=ref_month, task_key_path=str(task_key_path), receipt_path=str(receipt_path), saved_event_path=saved_event_path, event_count=event_count, status=status)


def _read_detector_events(run: DetectorRunRef) -> Iterable[dict[str, Any]]:
    if not run.saved_event_path:
        return []
    path = Path(run.saved_event_path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        rows = [{str(k): str(v or "") for k, v in row.items()} for row in csv.DictReader(handle)]
    events: list[dict[str, Any]] = []
    for row in rows:
        event_id = row.get("event_id") or ""
        event_time = row.get("effective_time") or row.get("event_time")
        events.append(
            {
                "event_id": event_id,
                "canonical_event_id": event_id,
                "dedup_status": "canonical",
                "source_priority": "source_detector",
                "coverage_reason": "local_equity_abnormal_activity_detector_over_reviewed_bars",
                "fold_month": run.month,
                "event_time": event_time,
                "available_time": event_time,
                "information_role_type": "prior_signal",
                "event_category_type": "equity_abnormal_activity",
                "scope_type": "symbol",
                "symbol": row.get("symbol") or run.symbol,
                "title": row.get("title") or f"{run.symbol} abnormal equity activity",
                "summary": row.get("summary") or row.get("abnormal_activity_type") or "Local equity abnormal activity detector event.",
                "source_name": DETECTOR_SOURCE,
                "reference_type": "internal_artifact_path",
                "reference": run.saved_event_path,
            }
        )
    return events



def _discover_event_feed_artifacts(
    *,
    trading_storage_root: Path | None = None,
    trading_data_root: Path | None = None,
    start_month: str,
    end_month: str,
) -> tuple[list[str], dict[str, int]]:
    """Return reviewed saved feed artifacts available for M06 event extraction.

    The bridge is intentionally local-artifact only. It never dispatches feed
    work or performs provider calls; the coverage gate refuses to let M06
    advance when required event feeds are absent.
    """

    root = trading_storage_root or (trading_data_root / "storage" if trading_data_root is not None else DEFAULT_TRADING_STORAGE_ROOT)
    base = root / "monthly_backfill"
    paths: list[str] = []
    coverage = {source_id: 0 for source_id in REQUIRED_EVENT_FEED_ARTIFACTS}
    for month in _iter_months(start_month, end_month):
        for source_id, filename in REQUIRED_EVENT_FEED_ARTIFACTS.items():
            candidates = sorted((base / source_id / month).glob(f"runs/*/saved/{filename}"))
            candidates.extend(sorted((base / source_id / month).glob(f"saved/{filename}")))
            unique = [candidate for candidate in dict.fromkeys(candidates) if candidate.exists()]
            if unique:
                latest = max(unique, key=lambda candidate: (candidate.stat().st_mtime_ns, str(candidate)))
                coverage[source_id] += 1
                paths.append(str(latest))
    return paths, coverage


def _missing_event_feed_artifacts(coverage: Mapping[str, int]) -> list[str]:
    return [source_id for source_id in REQUIRED_EVENT_FEED_ARTIFACTS if int(coverage.get(source_id) or 0) <= 0]


def _parse_event_feed_time(value: str) -> datetime | None:
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


def _event_feed_source_from_path(path: str | Path) -> str | None:
    text = str(path)
    for source_id in REQUIRED_EVENT_FEED_ARTIFACTS:
        if f"/{source_id}/" in text or text.startswith(f"{source_id}/"):
            return source_id
    return None


def _event_feed_window_row_count(source_id: str, path: Path, *, start: datetime, end: datetime) -> int:
    fields = EVENT_FEED_TIME_FIELDS[source_id]
    count = 0
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            event_time = None
            for field in fields:
                value = row.get(field)
                if value:
                    event_time = _parse_event_feed_time(value)
                    if event_time is not None:
                        break
            if event_time is not None and start <= event_time < end:
                count += 1
    return count


def _event_feed_row_coverage(event_artifact_paths: Sequence[str], *, start_month: str, end_month: str) -> dict[str, int]:
    start_text, end_text = _range_bounds(start_month, end_month)
    start = _parse_event_feed_time(start_text)
    end = _parse_event_feed_time(end_text)
    if start is None or end is None:
        raise TaskSystemError(f"invalid M06 event-feed coverage bounds: {start_text} -> {end_text}")
    coverage = {source_id: 0 for source_id in REQUIRED_EVENT_FEED_ARTIFACTS}
    for raw_path in event_artifact_paths:
        source_id = _event_feed_source_from_path(raw_path)
        if source_id is None:
            continue
        path = Path(raw_path)
        if not path.exists():
            continue
        coverage[source_id] += _event_feed_window_row_count(source_id, path, start=start, end=end)
    return coverage


def _missing_event_feed_rows(row_coverage: Mapping[str, int]) -> list[str]:
    return [source_id for source_id in REQUIRED_EVENT_FEED_ARTIFACTS if int(row_coverage.get(source_id) or 0) <= 0]


def _latest_successful_feed_run(receipt_path: Path) -> Mapping[str, Any] | None:
    if not receipt_path.exists():
        return None
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    runs = receipt.get("runs")
    if not isinstance(runs, list):
        return None
    for run in reversed(runs):
        if isinstance(run, Mapping) and str(run.get("status") or "") == "succeeded":
            return run
    return None


def _discover_event_feed_sql_inputs(
    *,
    trading_storage_root: Path,
    start_month: str,
    end_month: str,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, int]]:
    coverage = {source_id: 0 for source_id in REQUIRED_EVENT_FEED_ARTIFACTS}
    row_coverage = {source_id: 0 for source_id in REQUIRED_EVENT_FEED_ARTIFACTS}
    for month in _iter_months(start_month, end_month):
        for source_id in REQUIRED_EVENT_FEED_ARTIFACTS:
            run = _latest_successful_feed_run(trading_storage_root / "monthly_backfill" / source_id / month / "completion_receipt.json")
            if run is None:
                continue
            coverage[source_id] += 1
            row_counts = run.get("row_counts") if isinstance(run.get("row_counts"), Mapping) else {}
            row_coverage[source_id] += sum(int(value or 0) for value in row_counts.values())
    start, end = _range_bounds(start_month, end_month)
    sql_inputs: list[dict[str, Any]] = []
    for source_id, template in EVENT_FEED_SQL_INPUTS.items():
        if coverage[source_id] <= 0 or row_coverage[source_id] <= 0:
            continue
        sql_input = dict(template)
        sql_input["start"] = start
        sql_input["end"] = end
        sql_inputs.append(sql_input)
    return sql_inputs, coverage, row_coverage


def _write_source_task_key(
    *,
    output_dir: Path,
    trading_data_output_root: Path,
    trading_data_root: Path,
    start_month: str,
    end_month: str,
    events: Sequence[Mapping[str, Any]],
    event_artifact_paths: Sequence[str],
    event_sql_inputs: Sequence[Mapping[str, Any]],
) -> Path:
    start, end = _range_bounds(start_month, end_month)
    fold_key = _fold_key(start_month, end_month)
    task_key = {
        "task_id": f"model_06_residual_event_governance_{fold_key}",
        "source": SOURCE,
        "params": {
            "start": start,
            "end": end,
            "events": list(events),
            "event_artifact_paths": list(event_artifact_paths),
            "event_sql_inputs": [dict(item) for item in event_sql_inputs],
        },
        "output_root": str(trading_data_output_root / SOURCE / f"model_06_residual_event_governance_{fold_key}"),
        "manager_stage_id": "model_06_residual_event_governance.data_acquisition",
        "source_policy": "local_event_index_over_source_detector_outputs_no_provider_calls",
    }
    path = output_dir / "m06_residual_event_governance_data_acquisition_task_key.json"
    path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def materialize_residual_event_governance_inputs_inputs(
    *,
    start_month: str,
    end_month: str,
    manager_storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    trading_storage_root: Path = DEFAULT_TRADING_STORAGE_ROOT,
    universe_path: Path = DEFAULT_TRADING_STORAGE_UNIVERSE,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    run_id: str | None = None,
    write: bool = False,
) -> ResidualEventGovernanceInputMaterialization:
    if not manager_storage_root.is_absolute():
        manager_storage_root = Path.cwd() / manager_storage_root
    fold_key = _fold_key(start_month, end_month)
    output_base = output_root if output_root.is_absolute() else manager_storage_root / output_root
    output_dir = output_base / fold_key
    output_dir.mkdir(parents=True, exist_ok=True)
    trading_data_output_root = output_dir / "trading_data_outputs"
    run_id = run_id or f"model_06_residual_event_governance_{fold_key}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    refs = tuple(
        ref
        for month in _iter_months(start_month, end_month)
        for ref in _discover_layer_two_feed_artifacts_including_zero_rows(
            start_month=month,
            trading_data_root=trading_data_root,
            trading_storage_root=trading_storage_root,
            universe_path=universe_path,
        )
    )
    if not refs:
        raise TaskSystemError("no successful M02 feed artifacts are available for M06 event-risk materialization")
    event_artifact_paths, artifact_coverage = _discover_event_feed_artifacts(trading_storage_root=trading_storage_root, start_month=start_month, end_month=end_month)
    artifact_row_coverage = _event_feed_row_coverage(event_artifact_paths, start_month=start_month, end_month=end_month)
    event_sql_inputs, sql_coverage, sql_row_coverage = _discover_event_feed_sql_inputs(trading_storage_root=trading_storage_root, start_month=start_month, end_month=end_month)
    event_feed_coverage = {
        source_id: int(artifact_coverage.get(source_id) or 0) + int(sql_coverage.get(source_id) or 0)
        for source_id in REQUIRED_EVENT_FEED_ARTIFACTS
    }
    event_feed_row_coverage = {
        source_id: int(artifact_row_coverage.get(source_id) or 0) + int(sql_row_coverage.get(source_id) or 0)
        for source_id in REQUIRED_EVENT_FEED_ARTIFACTS
    }
    missing_feed_artifacts = _missing_event_feed_artifacts(event_feed_coverage)
    missing_feed_rows = _missing_event_feed_rows(event_feed_row_coverage)
    if write and missing_feed_artifacts:
        raise TaskSystemError(
            "M06 event-risk coverage is incomplete; missing reviewed feed artifacts for "
            + ",".join(missing_feed_artifacts)
        )
    if write and missing_feed_rows:
        raise TaskSystemError(
            "M06 event-risk coverage is incomplete; reviewed feed artifacts have zero in-window rows for "
            + ",".join(missing_feed_rows)
        )
    detector_runs = tuple(
        _run_detector(
            ref,
            output_dir=output_dir,
            trading_data_output_root=trading_data_output_root,
            trading_data_root=trading_data_root,
            run_id=run_id,
            write=write,
        )
        for ref in refs
    )
    events = [event for detector_run in detector_runs for event in _read_detector_events(detector_run)]
    if not events and not event_artifact_paths and not event_sql_inputs and write:
        raise TaskSystemError("M06 event-risk materialization emitted zero event rows and found no reviewed event feed artifacts; review no-event context policy before advancing")
    source_task_key_path = _write_source_task_key(
        output_dir=output_dir,
        trading_data_output_root=trading_data_output_root,
        trading_data_root=trading_data_root,
        start_month=start_month,
        end_month=end_month,
        events=events,
        event_artifact_paths=event_artifact_paths,
        event_sql_inputs=event_sql_inputs,
    )
    source_receipt_path: str | None = None
    source_event_count = len(events)
    if write:
        command = [sys.executable, "-m", "data_source.m06_residual_event_governance_data_acquisition", str(source_task_key_path), "--run-id", run_id]
        result = subprocess.run(command, cwd=trading_data_root, env={**os.environ, "PYTHONPATH": "src"}, text=True, capture_output=True, check=False)
        log_dir = output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "m06_residual_event_governance_data_acquisition.stdout.log").write_text(result.stdout, encoding="utf-8")
        (log_dir / "m06_residual_event_governance_data_acquisition.stderr.log").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise TaskSystemError(f"{SOURCE} materialization failed: {result.stderr.strip() or result.stdout.strip()}")
        payload = json.loads(result.stdout)
        references = [str(item) for item in payload.get("references") or []]
        source_receipt_path = next((item for item in references if item.endswith("completion_receipt.json")), None)
        source_event_count = int((payload.get("row_counts") or {}).get(SOURCE) or source_event_count)
    summary = ResidualEventGovernanceInputMaterialization(
        contract_type="manager_residual_event_governance_input_materialization",
        start_month=start_month,
        end_month=end_month,
        detector_run_count=len(detector_runs),
        detector_event_count=sum(item.event_count for item in detector_runs),
        source_event_count=source_event_count,
        detector_runs=detector_runs,
        event_feed_artifact_paths=tuple(event_artifact_paths),
        event_feed_sql_inputs=tuple(dict(item) for item in event_sql_inputs),
        event_feed_coverage=event_feed_coverage,
        event_feed_row_coverage=event_feed_row_coverage,
        source_task_key_path=str(source_task_key_path),
        source_receipt_path=source_receipt_path,
    )
    if write:
        (output_dir / "materialization_receipt.json").write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def write_summary(summary: ResidualEventGovernanceInputMaterialization, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize M06 model_06_residual_event_governance_data_acquisition SQL rows from local reviewed artifacts without provider calls.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--manager-storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--trading-storage-root", type=Path, default=DEFAULT_TRADING_STORAGE_ROOT)
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_TRADING_STORAGE_UNIVERSE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-id")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    summary = materialize_residual_event_governance_inputs_inputs(
        start_month=args.start_month,
        end_month=args.end_month,
        manager_storage_root=args.manager_storage_root,
        trading_data_root=args.trading_data_root,
        trading_storage_root=args.trading_storage_root,
        universe_path=args.universe_path,
        output_root=args.output_root,
        run_id=args.run_id,
        write=args.write,
    )
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = ["DetectorRunRef", "ResidualEventGovernanceInputMaterialization", "materialize_residual_event_governance_inputs_inputs"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

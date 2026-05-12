"""Safe Layer 4 event-overlay input materialization.

This module builds ``source_04_event_overlay`` rows only from already-saved local
Layer 2 bar artifacts. It may run the trading-data equity abnormal activity
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
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .layer_three_target_state import FeedArtifactRef, discover_layer_two_feed_artifacts
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_TRADING_STORAGE_ROOT = Path("/root/projects/trading-data/storage")
DEFAULT_TRADING_STORAGE_UNIVERSE = Path("/root/projects/trading-storage/main/shared/market_regime_etf_universe.csv")
DEFAULT_OUTPUT_ROOT = Path("runtime/layer_04_event_overlay/input_materialization")
DETECTOR_SOURCE = "source_04_event_overlay.equity_abnormal_activity"
SOURCE = "source_04_event_overlay"


@dataclass(frozen=True)
class DetectorRunRef:
    symbol: str
    task_key_path: str
    receipt_path: str
    saved_event_path: str | None
    event_count: int
    status: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayerFourEventOverlayMaterialization:
    contract_type: str
    start_month: str
    end_month: str
    detector_run_count: int
    detector_event_count: int
    source_event_count: int
    detector_runs: tuple[DetectorRunRef, ...]
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
            "source_task_key_path": self.source_task_key_path,
            "source_receipt_path": self.source_receipt_path,
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
        }


def _month_bounds(month: str) -> tuple[str, str]:
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number == 12:
        return f"{year:04d}-12-01T00:00:00-05:00", f"{year + 1:04d}-01-01T00:00:00-05:00"
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00", f"{year:04d}-{month_number + 1:02d}-01T00:00:00-05:00"


def _saved_bar_path(ref: FeedArtifactRef) -> Path:
    path = Path(ref.cleaned_bar_path)
    run_dir = path.parents[1]
    saved = run_dir / "saved" / "equity_bar.csv"
    if saved.exists():
        return saved
    raise TaskSystemError(f"saved equity_bar.csv not found for {ref.symbol}: {saved}")


def _run_detector(
    ref: FeedArtifactRef,
    *,
    output_dir: Path,
    trading_data_root: Path,
    run_id: str,
    write: bool,
) -> DetectorRunRef:
    symbol = ref.symbol
    task_key_path = output_dir / "detectors" / symbol / "task_key.json"
    detector_output_root = trading_data_root / "storage" / "runtime" / DETECTOR_SOURCE.replace(".", "_") / symbol / output_dir.name
    receipt_path = detector_output_root / "completion_receipt.json"
    if ref.row_count <= 0:
        return DetectorRunRef(
            symbol=symbol,
            task_key_path=str(task_key_path),
            receipt_path=str(receipt_path),
            saved_event_path=None,
            event_count=0,
            status="skipped_zero_bar_rows",
        )
    task_key = {
        "task_id": f"layer_04_event_overlay_detector_{symbol}_{output_dir.name.replace('-', '_')}",
        "source": DETECTOR_SOURCE,
        "params": {
            "bars_csv_path": str(_saved_bar_path(ref)),
        },
        "output_root": str(detector_output_root),
        "manager_stage_id": "layer_04_event_overlay.data_acquisition",
        "source_policy": "local_source_detector_over_reviewed_layer_02_alpaca_bar_artifacts_no_provider_calls",
    }
    task_key_path.parent.mkdir(parents=True, exist_ok=True)
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    saved_event_path: str | None = None
    event_count = 0
    status = "prepared"
    if write:
        command = ["python3", "-m", "data_source.source_04_event_overlay.equity_abnormal_activity", str(task_key_path), "--run-id", f"{run_id}_{symbol.lower()}"]
        result = subprocess.run(command, cwd=trading_data_root, env={**os.environ, "PYTHONPATH": "src"}, text=True, capture_output=True, check=False)
        log_dir = output_dir / "logs" / "detectors"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{symbol}.stdout.log").write_text(result.stdout, encoding="utf-8")
        (log_dir / f"{symbol}.stderr.log").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise TaskSystemError(f"Layer 4 detector failed for {symbol}: {result.stderr.strip() or result.stdout.strip()}")
        payload = json.loads(result.stdout)
        status = str(payload.get("status") or "succeeded")
        event_count = int((payload.get("row_counts") or {}).get("equity_abnormal_activity_event") or 0)
        references = [str(item) for item in payload.get("references") or []]
        saved_event_path = next((item for item in references if item.endswith("equity_abnormal_activity_event.csv")), None)
    return DetectorRunRef(symbol=symbol, task_key_path=str(task_key_path), receipt_path=str(receipt_path), saved_event_path=saved_event_path, event_count=event_count, status=status)


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


def _write_source_task_key(*, output_dir: Path, trading_data_root: Path, start_month: str, end_month: str, events: Sequence[Mapping[str, Any]]) -> Path:
    start, end = _month_bounds(start_month)
    task_key = {
        "task_id": f"layer_04_event_overlay_{start_month.replace('-', '_')}",
        "source": SOURCE,
        "params": {
            "start": start,
            "end": end,
            "events": list(events),
        },
        "output_root": str(trading_data_root / "storage" / "runtime" / SOURCE / f"layer_04_event_overlay_{start_month.replace('-', '_')}"),
        "manager_stage_id": "layer_04_event_overlay.data_acquisition",
        "source_policy": "local_event_index_over_source_detector_outputs_no_provider_calls",
    }
    path = output_dir / "source_04_task_key.json"
    path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def materialize_layer_four_event_overlay_inputs(
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
) -> LayerFourEventOverlayMaterialization:
    if start_month != end_month:
        raise TaskSystemError("Layer 4 event-overlay materialization currently expects one chronological month per run")
    if not manager_storage_root.is_absolute():
        manager_storage_root = Path.cwd() / manager_storage_root
    output_dir = manager_storage_root / output_root / start_month
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_id or f"layer_04_event_overlay_{start_month.replace('-', '_')}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    refs = discover_layer_two_feed_artifacts(
        start_month=start_month,
        trading_data_root=trading_data_root,
        trading_storage_root=trading_storage_root,
        universe_path=universe_path,
    )
    if not refs:
        raise TaskSystemError("no successful Layer 2 feed artifacts are available for Layer 4 event-overlay materialization")
    detector_runs = tuple(_run_detector(ref, output_dir=output_dir, trading_data_root=trading_data_root, run_id=run_id, write=write) for ref in refs)
    events = [event for detector_run in detector_runs for event in _read_detector_events(detector_run)]
    if not events and write:
        raise TaskSystemError("Layer 4 local detectors emitted zero event rows; review no-event context policy before advancing")
    source_task_key_path = _write_source_task_key(output_dir=output_dir, trading_data_root=trading_data_root, start_month=start_month, end_month=end_month, events=events)
    source_receipt_path: str | None = None
    if write:
        command = ["python3", "-m", "data_source.source_04_event_overlay", str(source_task_key_path), "--run-id", run_id]
        result = subprocess.run(command, cwd=trading_data_root, env={**os.environ, "PYTHONPATH": "src"}, text=True, capture_output=True, check=False)
        log_dir = output_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "source_04.stdout.log").write_text(result.stdout, encoding="utf-8")
        (log_dir / "source_04.stderr.log").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise TaskSystemError(f"source_04_event_overlay materialization failed: {result.stderr.strip() or result.stdout.strip()}")
        payload = json.loads(result.stdout)
        references = [str(item) for item in payload.get("references") or []]
        source_receipt_path = next((item for item in references if item.endswith("completion_receipt.json")), None)
    summary = LayerFourEventOverlayMaterialization(
        contract_type="manager_layer_four_event_overlay_input_materialization",
        start_month=start_month,
        end_month=end_month,
        detector_run_count=len(detector_runs),
        detector_event_count=sum(item.event_count for item in detector_runs),
        source_event_count=len(events),
        detector_runs=detector_runs,
        source_task_key_path=str(source_task_key_path),
        source_receipt_path=source_receipt_path,
    )
    if write:
        (output_dir / "materialization_receipt.json").write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def write_summary(summary: LayerFourEventOverlayMaterialization, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Layer 4 source_04_event_overlay rows from local reviewed artifacts without provider calls.")
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
    summary = materialize_layer_four_event_overlay_inputs(
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


__all__ = ["DetectorRunRef", "LayerFourEventOverlayMaterialization", "materialize_layer_four_event_overlay_inputs"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

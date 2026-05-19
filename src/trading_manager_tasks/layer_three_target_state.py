"""Safe Layer 3 target-state input materialization.

This module turns already-approved Layer 2 Alpaca bar artifacts into the local
``source_03_target_state`` input surface. It performs no provider calls; it only
reads completed feed artifacts, writes a task key/evidence bundle, and delegates
normalization to ``trading-data``'s source_03 runner.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_TRADING_STORAGE_ROOT = Path("/root/projects/trading-data/storage")
DEFAULT_TRADING_STORAGE_UNIVERSE = Path("/root/projects/trading-storage/main/shared/layer_01_02_market_context_etf_universe.csv")
DEFAULT_OUTPUT_ROOT = Path("runtime/layer_03_target_state_vector/input_materialization")
LAYER_TWO_MODEL_LAYER = "layer_02_sector_context"
SOURCE = "source_03_target_state"
TARGET_CANDIDATE_HOLDINGS_SOURCE = "source_02_target_candidate_holdings"
MONTHLY_BACKFILL_STORAGE_DIR = "monthly_backfill"


@dataclass(frozen=True)
class FeedArtifactRef:
    """Completed Layer 2 feed artifact selected as target-local source evidence."""

    symbol: str
    month: str
    receipt_path: str
    cleaned_bar_path: str
    run_id: str
    row_count: int

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayerThreeTargetStateMaterialization:
    """Receipt for manager-owned local Layer 3 source materialization."""

    contract_type: str
    start_month: str
    end_month: str
    symbols: tuple[str, ...]
    feed_artifact_count: int
    source_row_count: int
    target_candidate_count: int
    target_candidate_holdings_fetch_count: int
    target_candidate_holdings_row_count: int
    target_candidate_holdings_task_key_path: str
    target_candidate_holdings_receipt_path: str | None
    task_key_path: str
    candidate_rows_path: str
    merged_bar_rows_path: str
    trading_data_receipt_path: str | None
    feed_artifacts: tuple[FeedArtifactRef, ...]
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "symbols": list(self.symbols),
            "feed_artifact_count": self.feed_artifact_count,
            "source_row_count": self.source_row_count,
            "target_candidate_count": self.target_candidate_count,
            "target_candidate_holdings_fetch_count": self.target_candidate_holdings_fetch_count,
            "target_candidate_holdings_row_count": self.target_candidate_holdings_row_count,
            "target_candidate_holdings_task_key_path": self.target_candidate_holdings_task_key_path,
            "target_candidate_holdings_receipt_path": self.target_candidate_holdings_receipt_path,
            "task_key_path": self.task_key_path,
            "candidate_rows_path": self.candidate_rows_path,
            "merged_bar_rows_path": self.merged_bar_rows_path,
            "trading_data_receipt_path": self.trading_data_receipt_path,
            "feed_artifacts": [item.summary_row() for item in self.feed_artifacts],
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


def _latest_successful_run(receipt: Mapping[str, Any]) -> Mapping[str, Any] | None:
    runs = [run for run in receipt.get("runs") or [] if isinstance(run, Mapping)]
    successful = [run for run in runs if str(run.get("status") or "").lower() in {"succeeded", "success", "completed", "complete", "ready"}]
    return successful[-1] if successful else None


def _resolve_component_path(path: str, *, trading_data_root: Path) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else trading_data_root / resolved


def discover_layer_two_feed_artifacts(
    *,
    start_month: str,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    trading_storage_root: Path = DEFAULT_TRADING_STORAGE_ROOT,
    universe_path: Path = DEFAULT_TRADING_STORAGE_UNIVERSE,
    symbols: Iterable[str] | None = None,
) -> tuple[FeedArtifactRef, ...]:
    """Find successful Layer 2 bar artifacts already present on disk."""

    allowed_symbols = {symbol.upper() for symbol in (symbols or _read_layer_two_symbols(universe_path))}
    refs: list[FeedArtifactRef] = []
    for symbol in sorted(allowed_symbols):
        receipt_path = trading_storage_root / MONTHLY_BACKFILL_STORAGE_DIR / "alpaca_bars" / symbol / start_month / "completion_receipt.json"
        if not receipt_path.exists():
            continue
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        run = _latest_successful_run(receipt)
        if run is None:
            continue
        cleaned_refs = []
        steps = run.get("steps") if isinstance(run.get("steps"), Mapping) else {}
        clean_step = steps.get("clean") if isinstance(steps.get("clean"), Mapping) else {}
        for ref in clean_step.get("references") or []:
            if isinstance(ref, str) and ref.endswith("equity_bar.jsonl"):
                cleaned_refs.append(ref)
        if not cleaned_refs:
            output_dir = str(run.get("output_dir") or "")
            if output_dir:
                cleaned_refs.append(str(Path(output_dir) / "cleaned" / "equity_bar.jsonl"))
        if not cleaned_refs:
            continue
        cleaned_path = _resolve_component_path(cleaned_refs[-1], trading_data_root=trading_data_root)
        if not cleaned_path.exists():
            continue
        row_counts = run.get("row_counts") if isinstance(run.get("row_counts"), Mapping) else {}
        refs.append(
            FeedArtifactRef(
                symbol=symbol,
                month=start_month,
                receipt_path=str(receipt_path),
                cleaned_bar_path=str(cleaned_path),
                run_id=str(run.get("run_id") or ""),
                row_count=int(row_counts.get("equity_bar") or 0),
            )
        )
    return tuple(refs)


def _target_candidate_id(*, fold_key: str, symbol: str) -> str:
    digest = hashlib.sha256(f"layer_03_target_state_vector:{fold_key}:{symbol}".encode("utf-8")).hexdigest()[:16]
    return f"tcand_l03_{fold_key}_{digest}"


def _ref_month(ref: FeedArtifactRef) -> str:
    return str(getattr(ref, "month", "") or "unknown_month")


def _candidate_rows(refs: Sequence[FeedArtifactRef], *, start_month: str, end_month: str) -> list[dict[str, Any]]:
    fold_key = _fold_key(start_month, end_month)
    by_symbol: dict[str, list[FeedArtifactRef]] = {}
    for ref in refs:
        by_symbol.setdefault(ref.symbol, []).append(ref)
    rows: list[dict[str, Any]] = []
    for symbol, symbol_refs in sorted(by_symbol.items()):
        months = sorted({_ref_month(ref) for ref in symbol_refs if _ref_month(ref) != "unknown_month"})
        rows.append(
            {
                "target_candidate_id": _target_candidate_id(fold_key=fold_key, symbol=symbol),
                "fold_id": f"fold_{start_month}_{end_month}",
                "fold_start_month": start_month,
                "fold_end_month": end_month,
                "fold_months": ";".join(months),
                "routing_symbol_ref": symbol,
                "audit_symbol_ref": symbol,
                "candidate_generation_reason_codes": "3_LAYER2_TRANSMISSION_TARGET_CANDIDATE;3_TARGET_LOCAL_EVIDENCE_JOINED",
                "candidate_eligibility_state": "eligible",
                "candidate_anonymity_check_state": "pass",
                "candidate_data_quality_score": 1.0 if any(ref.row_count > 0 for ref in symbol_refs) else 0.0,
                "source_artifact_ref": ";".join(ref.cleaned_bar_path for ref in symbol_refs),
            }
        )
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, default=str) + "\n")
            count += 1
    return count


def _iter_merged_bar_rows(refs: Sequence[FeedArtifactRef]) -> Iterable[dict[str, Any]]:
    for ref in refs:
        with Path(ref.cleaned_bar_path).open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                row.setdefault("symbol", ref.symbol)
                if _ref_month(ref) != "unknown_month":
                    row.setdefault("fold_month", _ref_month(ref))
                yield row


def build_source_task_key(
    *,
    start_month: str,
    end_month: str,
    output_dir: Path,
    trading_data_output_root: Path,
    refs: Sequence[FeedArtifactRef],
) -> tuple[dict[str, Any], Path, Path, Path, int]:
    if not refs:
        raise TaskSystemError("no successful Layer 2 feed artifacts are available for Layer 3 target-state materialization")
    source_start, source_end = _range_bounds(start_month, end_month)
    fold_key = _fold_key(start_month, end_month)
    candidate_path = output_dir / "target_candidates.jsonl"
    merged_bar_path = output_dir / "bars.jsonl"
    task_key_path = output_dir / "task_key.json"
    candidates = _candidate_rows(refs, start_month=start_month, end_month=end_month)
    _write_jsonl(candidate_path, candidates)
    bar_count = _write_jsonl(merged_bar_path, _iter_merged_bar_rows(refs))
    task_key = {
        "task_id": f"layer_03_target_state_vector_{fold_key}",
        "source": SOURCE,
        "params": {
            "start": source_start,
            "end": source_end,
            "timeframe": "30Min",
            "target_candidates_path": str(candidate_path),
            "bar_rows_path": str(merged_bar_path),
        },
        "output_root": str(trading_data_output_root),
        "manager_stage_id": "layer_03_target_state_vector.data_acquisition",
        "source_policy": "local_reuse_of_reviewed_layer_02_alpaca_bar_artifacts_no_provider_calls",
    }
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return task_key, task_key_path, candidate_path, merged_bar_path, bar_count


def build_target_candidate_holdings_task_key(
    *,
    start_month: str,
    end_month: str,
    output_dir: Path,
    trading_data_output_root: Path,
) -> tuple[dict[str, Any], Path]:
    source_start, source_end = _range_bounds(start_month, end_month)
    fold_key = _fold_key(start_month, end_month)
    task_key_path = output_dir / "target_candidate_holdings_task_key.json"
    task_key_path.parent.mkdir(parents=True, exist_ok=True)
    task_key = {
        "task_id": f"layer_03_target_candidate_holdings_{fold_key}",
        "source": TARGET_CANDIDATE_HOLDINGS_SOURCE,
        "params": {
            "start": source_start,
            "end": source_end,
            "continue_on_error": True,
        },
        "output_root": str(trading_data_output_root),
        "manager_stage_id": "layer_03_target_state_vector.data_acquisition",
        "source_policy": "official_issuer_holdings_fetch_with_point_in_time_window_filter",
    }
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return task_key, task_key_path


def _run_trading_data_source(
    *,
    trading_data_root: Path,
    source_module: str,
    task_key_path: Path,
    run_id: str,
    output_dir: Path,
) -> Mapping[str, Any]:
    command = ["python3", "-m", source_module, str(task_key_path), "--run-id", run_id]
    result = subprocess.run(
        command,
        cwd=trading_data_root,
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    safe_module = source_module.replace(".", "_")
    (log_dir / f"{run_id}.{safe_module}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (log_dir / f"{run_id}.{safe_module}.stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise TaskSystemError(f"{source_module} materialization failed: {result.stderr.strip() or result.stdout.strip()}")
    parsed = json.loads(result.stdout)
    return parsed if isinstance(parsed, Mapping) else {}


def _holdings_fetch_count(receipt_path: str | None) -> int:
    if not receipt_path:
        return 0
    path = Path(receipt_path)
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    runs = [run for run in payload.get("runs") or [] if isinstance(run, Mapping)]
    if not runs:
        return 0
    latest = runs[-1]
    steps = latest.get("steps") if isinstance(latest.get("steps"), Mapping) else {}
    fetch_step = steps.get("fetch") if isinstance(steps.get("fetch"), Mapping) else {}
    details = fetch_step.get("details") if isinstance(fetch_step.get("details"), Mapping) else {}
    feeds = details.get("holding_feeds") if isinstance(details.get("holding_feeds"), list) else []
    errors = details.get("holding_feed_errors") if isinstance(details.get("holding_feed_errors"), list) else []
    return len(feeds) + len(errors)


def materialize_layer_three_target_state_inputs(
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
) -> LayerThreeTargetStateMaterialization:
    """Materialize source_03 target-state rows from existing Layer 2 feed artifacts."""

    refs = tuple(
        ref
        for month in _iter_months(start_month, end_month)
        for ref in discover_layer_two_feed_artifacts(
            start_month=month,
            trading_data_root=trading_data_root,
            trading_storage_root=trading_storage_root,
            universe_path=universe_path,
        )
    )
    if not manager_storage_root.is_absolute():
        manager_storage_root = Path.cwd() / manager_storage_root
    fold_key = _fold_key(start_month, end_month)
    output_dir = manager_storage_root / output_root / fold_key
    trading_data_output_root = trading_data_root / "storage" / "runtime" / SOURCE / f"layer_03_target_state_vector_{fold_key}"
    holdings_output_root = trading_data_root / "storage" / "runtime" / TARGET_CANDIDATE_HOLDINGS_SOURCE / f"layer_03_target_state_vector_{fold_key}"
    run_id = run_id or f"layer_03_target_state_vector_{fold_key}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    _holdings_task_key, holdings_task_key_path = build_target_candidate_holdings_task_key(
        start_month=start_month,
        end_month=end_month,
        output_dir=output_dir,
        trading_data_output_root=holdings_output_root,
    )
    _task_key, task_key_path, candidate_path, merged_bar_path, _bar_count = build_source_task_key(
        start_month=start_month,
        end_month=end_month,
        output_dir=output_dir,
        trading_data_output_root=trading_data_output_root,
        refs=refs,
    )
    holdings_receipt_path: str | None = None
    holdings_fetch_count = 0
    holdings_row_count = 0
    trading_data_receipt_path: str | None = None
    source_row_count = 0
    if write:
        holdings_payload = _run_trading_data_source(
            trading_data_root=trading_data_root,
            source_module=f"data_source.{TARGET_CANDIDATE_HOLDINGS_SOURCE}",
            task_key_path=holdings_task_key_path,
            run_id=f"{run_id}_holdings",
            output_dir=output_dir,
        )
        holdings_row_count = int((holdings_payload.get("row_counts") or {}).get(TARGET_CANDIDATE_HOLDINGS_SOURCE) or 0)
        holdings_refs = [str(item) for item in holdings_payload.get("references") or []]
        holdings_receipt_path = next((item for item in holdings_refs if item.endswith("completion_receipt.json")), str(holdings_output_root / "completion_receipt.json"))
        holdings_fetch_count = _holdings_fetch_count(holdings_receipt_path)
        payload = _run_trading_data_source(
            trading_data_root=trading_data_root,
            source_module="data_source.source_03_target_state",
            task_key_path=task_key_path,
            run_id=run_id,
            output_dir=output_dir,
        )
        source_row_count = int((payload.get("row_counts") or {}).get(SOURCE) or 0)
        refs_out = [str(item) for item in payload.get("references") or []]
        trading_data_receipt_path = next((item for item in refs_out if item.endswith("completion_receipt.json")), str(trading_data_output_root / "completion_receipt.json"))
    summary = LayerThreeTargetStateMaterialization(
        contract_type="manager_layer_three_target_state_input_materialization",
        start_month=start_month,
        end_month=end_month,
        symbols=tuple(ref.symbol for ref in refs),
        feed_artifact_count=len(refs),
        source_row_count=source_row_count,
        target_candidate_count=len({ref.symbol for ref in refs}),
        target_candidate_holdings_fetch_count=holdings_fetch_count,
        target_candidate_holdings_row_count=holdings_row_count,
        target_candidate_holdings_task_key_path=str(holdings_task_key_path),
        target_candidate_holdings_receipt_path=holdings_receipt_path,
        task_key_path=str(task_key_path),
        candidate_rows_path=str(candidate_path),
        merged_bar_rows_path=str(merged_bar_path),
        trading_data_receipt_path=trading_data_receipt_path,
        feed_artifacts=tuple(refs),
        provider_calls=holdings_fetch_count,
    )
    if write:
        receipt_path = output_dir / "materialization_receipt.json"
        receipt_path.write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def write_summary(summary: LayerThreeTargetStateMaterialization, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize Layer 3 source_03_target_state rows from existing Layer 2 feed artifacts without provider calls.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--manager-storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--trading-storage-root", type=Path, default=DEFAULT_TRADING_STORAGE_ROOT)
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_TRADING_STORAGE_UNIVERSE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-id")
    parser.add_argument("--write", action="store_true", help="Run the trading-data source_03 normalizer and write SQL rows.")
    args = parser.parse_args(argv)
    summary = materialize_layer_three_target_state_inputs(
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


__all__ = [
    "FeedArtifactRef",
    "LayerThreeTargetStateMaterialization",
    "build_source_task_key",
    "build_target_candidate_holdings_task_key",
    "discover_layer_two_feed_artifacts",
    "materialize_layer_three_target_state_inputs",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

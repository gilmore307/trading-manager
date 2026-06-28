"""Safe M02 target-state input materialization.

This module turns already-approved target-local Alpaca bar receipts into the local
``model_03_target_state_vector_data_acquisition`` SQL input surface. It performs no provider calls; it only
reads completed feed receipts, writes a compact task key/evidence bundle, and delegates
SQL-backed normalization to ``trading-data``'s source_03 runner.
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
from .storage_paths import data_storage_root

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_TRADING_STORAGE_ROOT = data_storage_root()
DEFAULT_HISTORICAL_CANDIDATE_UNIVERSE = Path("/root/projects/trading-storage/main/shared/historical_candidate_universe.csv")
DEFAULT_TARGET_CONTEXT_MAPPING = Path("/root/projects/trading-storage/main/shared/model_02_target_context_mapping.csv")
DEFAULT_OUTPUT_ROOT = Path("runtime") / "model_02_target_state" / "input_materialization"
SOURCE = "m03_target_state_vector_data_acquisition"
OUTPUT_TABLE = "model_03_target_state_vector_data_acquisition"
OPTION_CHAIN_SOURCE_TABLE = "option_chain_state_source"
OPTION_CHAIN_SOURCE_POLICY_REF = "M02_OPTION_CHAIN_ROLE_SELECTOR_POLICY"
MONTHLY_BACKFILL_STORAGE_DIR = "monthly_backfill"
BAR_SOURCE_TABLE = "model_01_market_regime_data_acquisition"
DEFAULT_TARGET_STATE_SOURCE_TIMEFRAME = "1Min"


@dataclass(frozen=True)
class FeedArtifactRef:
    """Completed M02 feed receipt selected as target-local source evidence."""

    symbol: str
    month: str
    receipt_path: str
    bar_source_ref: str
    run_id: str
    row_count: int
    evidence_symbol: str | None = None
    timeframe: str = DEFAULT_TARGET_STATE_SOURCE_TIMEFRAME

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LayerThreeTargetStateMaterialization:
    """Receipt for manager-owned local M02 source materialization."""

    contract_type: str
    start_month: str
    end_month: str
    symbols: tuple[str, ...]
    feed_artifact_count: int
    source_row_count: int
    target_candidate_count: int
    task_key_path: str
    candidate_rows_path: str
    bar_sources_path: str
    trading_data_receipt_path: str | None
    feed_artifacts: tuple[FeedArtifactRef, ...]
    option_chain_source_table: str = OPTION_CHAIN_SOURCE_TABLE
    option_chain_source_policy_ref: str = OPTION_CHAIN_SOURCE_POLICY_REF
    option_chain_source_usage: str = "optional_sql_overlay_for_model_02_target_state_target_level_reduction"
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
            "task_key_path": self.task_key_path,
            "candidate_rows_path": self.candidate_rows_path,
            "bar_sources_path": self.bar_sources_path,
            "trading_data_receipt_path": self.trading_data_receipt_path,
            "feed_artifacts": [item.summary_row() for item in self.feed_artifacts],
            "option_chain_source_table": self.option_chain_source_table,
            "option_chain_source_policy_ref": self.option_chain_source_policy_ref,
            "option_chain_source_usage": self.option_chain_source_usage,
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


def _read_candidate_universe_symbols(universe_path: Path, *, symbol_limit: int | None = None) -> tuple[str, ...]:
    with universe_path.open(newline="", encoding="utf-8") as handle:
        rows = [{str(k): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    symbols: list[str] = []
    seen: set[str] = set()
    for row in rows:
        symbol = str(row.get("symbol") or row.get("target_ref") or "").strip().upper()
        status = str(row.get("replay_candidate_status") or row.get("pool_membership_status") or "active").strip().lower()
        if not symbol or status != "active" or symbol in seen:
            continue
        symbols.append(symbol)
        seen.add(symbol)
        if symbol_limit is not None and len(symbols) >= symbol_limit:
            break
    if not symbols:
        raise TaskSystemError(f"no active candidate symbols found in {universe_path}")
    return tuple(symbols)


def _crypto_context_proxy_symbols(*, target_symbol: str, mapping_path: Path | None = None) -> tuple[str, ...]:
    mapping_path = mapping_path or DEFAULT_TARGET_CONTEXT_MAPPING
    if not mapping_path.exists():
        return ()
    with mapping_path.open(newline="", encoding="utf-8") as handle:
        rows = [{str(k): str(v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    symbols: list[str] = []
    for row in rows:
        if row.get("target_symbol", "").upper() != target_symbol:
            continue
        if row.get("review_status", "").lower() != "accepted":
            continue
        if row.get("target_asset_class", "").lower() != "crypto_spot":
            continue
        layer_two_symbol = row.get("layer2_context_symbol", "").upper()
        if layer_two_symbol:
            symbols.append(layer_two_symbol)
    return tuple(dict.fromkeys(symbols))


def _target_evidence_symbols(target_symbol: str) -> tuple[str, ...]:
    symbol = target_symbol.upper()
    return (symbol,) + tuple(item for item in _crypto_context_proxy_symbols(target_symbol=symbol) if item != symbol)


def _latest_successful_run(receipt: Mapping[str, Any]) -> Mapping[str, Any] | None:
    runs = [run for run in receipt.get("runs") or [] if isinstance(run, Mapping)]
    successful = [run for run in runs if str(run.get("status") or "").lower() in {"succeeded", "success", "completed", "complete", "ready"}]
    return successful[-1] if successful else None


def _bar_source_ref(run: Mapping[str, Any]) -> str:
    outputs = [item for item in run.get("outputs") or [] if isinstance(item, str)]
    steps = run.get("steps") if isinstance(run.get("steps"), Mapping) else {}
    save_step = steps.get("save") if isinstance(steps.get("save"), Mapping) else {}
    outputs.extend(item for item in save_step.get("references") or [] if isinstance(item, str))
    table_refs = [item for item in outputs if not item.endswith((".csv", ".jsonl", ".json", ".ndjson"))]
    return table_refs[-1] if table_refs else f"trading_data.{BAR_SOURCE_TABLE}"


def _source_timeframe(receipt_path: Path) -> str:
    timeframe = ""
    task_key_path = receipt_path.parent / "task_key.json"
    if task_key_path.exists():
        task_key = json.loads(task_key_path.read_text(encoding="utf-8"))
        params = task_key.get("params") if isinstance(task_key.get("params"), Mapping) else {}
        timeframe = str(params.get("timeframe") or "").strip()
        if timeframe:
            return timeframe
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    run = _latest_successful_run(receipt)
    output_dir = str(run.get("output_dir") or "").strip() if run else ""
    if output_dir:
        manifest_path = Path(output_dir) / "request_manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            params = manifest.get("params") if isinstance(manifest.get("params"), Mapping) else {}
            timeframe = str(params.get("timeframe") or "").strip()
            if timeframe:
                return timeframe
    return timeframe or DEFAULT_TARGET_STATE_SOURCE_TIMEFRAME


def discover_target_candidate_feed_artifacts(
    *,
    start_month: str,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    trading_storage_root: Path = DEFAULT_TRADING_STORAGE_ROOT,
    universe_path: Path = DEFAULT_HISTORICAL_CANDIDATE_UNIVERSE,
    symbols: Iterable[str] | None = None,
    symbol_limit: int | None = None,
) -> tuple[FeedArtifactRef, ...]:
    """Find successful target-local SQL-retained bar receipts already present on disk."""

    if symbol_limit is not None and symbol_limit <= 0:
        raise TaskSystemError("symbol_limit must be positive when supplied")
    requested_symbols = tuple(symbol.upper() for symbol in (symbols or _read_candidate_universe_symbols(universe_path, symbol_limit=symbol_limit)))
    allowed_symbols: dict[str, tuple[str, ...]] = {symbol: _target_evidence_symbols(symbol) for symbol in requested_symbols}
    refs: list[FeedArtifactRef] = []
    for target_symbol in sorted(allowed_symbols):
        for evidence_symbol in allowed_symbols[target_symbol]:
            receipt_path = trading_storage_root / MONTHLY_BACKFILL_STORAGE_DIR / "alpaca_bars" / evidence_symbol / start_month / "completion_receipt.json"
            if not receipt_path.exists():
                continue
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            run = _latest_successful_run(receipt)
            if run is None:
                continue
            row_counts = run.get("row_counts") if isinstance(run.get("row_counts"), Mapping) else {}
            row_count = int(row_counts.get("equity_bar") or 0)
            if row_count <= 0:
                continue
            refs.append(
                FeedArtifactRef(
                    symbol=target_symbol,
                    month=start_month,
                    receipt_path=str(receipt_path),
                    bar_source_ref=_bar_source_ref(run),
                    run_id=str(run.get("run_id") or ""),
                    row_count=row_count,
                    evidence_symbol=evidence_symbol,
                    timeframe=_source_timeframe(receipt_path),
                )
            )
            break
    return tuple(refs)


def _target_candidate_id(*, fold_key: str, symbol: str) -> str:
    digest = hashlib.sha256(f"model_02_target_state:{fold_key}:{symbol}".encode("utf-8")).hexdigest()[:16]
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
                "source_artifact_ref": ";".join(ref.receipt_path for ref in symbol_refs),
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


def _bar_sql_sources(refs: Sequence[FeedArtifactRef]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for ref in refs:
        month = _ref_month(ref)
        start, end = _month_bounds(month) if month != "unknown_month" else (None, None)
        sources.append(
            {
                "table": BAR_SOURCE_TABLE,
                "source_ref": ref.bar_source_ref,
                "source_symbol": ref.evidence_symbol or ref.symbol,
                "target_symbol": ref.symbol,
                "month": month,
                "start": start,
                "end": end,
                "timeframe": ref.timeframe,
                "receipt_path": ref.receipt_path,
                "run_id": ref.run_id,
                "row_count": ref.row_count,
            }
        )
    return sources


def build_source_task_key(
    *,
    start_month: str,
    end_month: str,
    output_dir: Path,
    trading_data_output_root: Path,
    refs: Sequence[FeedArtifactRef],
) -> tuple[dict[str, Any], Path, Path, Path, int]:
    if not refs:
        raise TaskSystemError("no successful target-local feed artifacts are available for M02 target-state materialization")
    source_start, source_end = _range_bounds(start_month, end_month)
    fold_key = _fold_key(start_month, end_month)
    candidate_path = output_dir / "target_candidates.jsonl"
    bar_sources_path = output_dir / "bar_sources.json"
    task_key_path = output_dir / "task_key.json"
    candidates = _candidate_rows(refs, start_month=start_month, end_month=end_month)
    _write_jsonl(candidate_path, candidates)
    bar_sources = _bar_sql_sources(refs)
    bar_sources_path.parent.mkdir(parents=True, exist_ok=True)
    bar_sources_path.write_text(json.dumps(bar_sources, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bar_count = sum(ref.row_count for ref in refs)
    task_key = {
        "task_id": f"model_02_target_state_{fold_key}",
        "source": SOURCE,
        "params": {
            "start": source_start,
            "end": source_end,
            "timeframe": refs[0].timeframe,
            "target_candidates_path": str(candidate_path),
            "bar_sql_sources": bar_sources,
        },
        "output_root": str(trading_data_output_root),
        "manager_stage_id": "model_02_target_state.data_acquisition",
        "source_policy": "local_reuse_of_reviewed_m02_alpaca_bar_sql_receipts_no_provider_calls",
        "downstream_feature_inputs": {
            "shared_option_chain_source_table": f"trading_data.{OPTION_CHAIN_SOURCE_TABLE}",
            "shared_option_chain_source_policy_ref": OPTION_CHAIN_SOURCE_POLICY_REF,
            "model_02_target_state_usage": "target_level_option_chain_state_reduction_only",
        },
    }
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return task_key, task_key_path, candidate_path, bar_sources_path, bar_count


def materialize_layer_three_target_state_inputs(
    *,
    start_month: str,
    end_month: str,
    manager_storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    trading_storage_root: Path = DEFAULT_TRADING_STORAGE_ROOT,
    universe_path: Path = DEFAULT_HISTORICAL_CANDIDATE_UNIVERSE,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    target_symbol: str | None = None,
    symbol_limit: int | None = None,
    run_id: str | None = None,
    write: bool = False,
) -> LayerThreeTargetStateMaterialization:
    """Materialize source_03 target-state rows from existing target-local feed receipts."""

    selected_symbols = (target_symbol.strip().upper(),) if target_symbol and target_symbol.strip() else None
    refs = tuple(
        ref
        for month in _iter_months(start_month, end_month)
        for ref in discover_target_candidate_feed_artifacts(
            start_month=month,
            trading_data_root=trading_data_root,
            trading_storage_root=trading_storage_root,
            universe_path=universe_path,
            symbols=selected_symbols,
            symbol_limit=None if selected_symbols else symbol_limit,
        )
    )
    if not manager_storage_root.is_absolute():
        manager_storage_root = Path.cwd() / manager_storage_root
    fold_key = _fold_key(start_month, end_month)
    output_base = output_root if output_root.is_absolute() else manager_storage_root / output_root
    target_scope = f"target_{target_symbol.strip().upper().lower()}" if selected_symbols and target_symbol else None
    output_dir = output_base / fold_key / target_scope if target_scope else output_base / fold_key
    trading_data_output_root = output_dir / "trading_data_outputs" / SOURCE
    run_id = run_id or f"model_02_target_state_{fold_key}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    _task_key, task_key_path, candidate_path, bar_sources_path, _bar_count = build_source_task_key(
        start_month=start_month,
        end_month=end_month,
        output_dir=output_dir,
        trading_data_output_root=trading_data_output_root,
        refs=refs,
    )
    trading_data_receipt_path: str | None = None
    source_row_count = 0
    if write:
        command = [sys.executable, "-m", "data_source.m03_target_state_vector_data_acquisition", str(task_key_path), "--run-id", run_id]
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
        (log_dir / f"{run_id}.stdout.log").write_text(result.stdout, encoding="utf-8")
        (log_dir / f"{run_id}.stderr.log").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            raise TaskSystemError(f"m03_target_state_vector_data_acquisition materialization failed: {result.stderr.strip() or result.stdout.strip()}")
        payload = json.loads(result.stdout)
        row_counts = payload.get("row_counts") if isinstance(payload.get("row_counts"), Mapping) else {}
        source_row_count = int(row_counts.get(OUTPUT_TABLE) or row_counts.get(SOURCE) or 0)
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
        task_key_path=str(task_key_path),
        candidate_rows_path=str(candidate_path),
        bar_sources_path=str(bar_sources_path),
        trading_data_receipt_path=trading_data_receipt_path,
        feed_artifacts=tuple(refs),
    )
    if write:
        receipt_path = output_dir / "materialization_receipt.json"
        receipt_path.write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def write_summary(summary: LayerThreeTargetStateMaterialization, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize M02 model_03_target_state_vector_data_acquisition SQL rows from existing target-local feed artifacts without provider calls.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--manager-storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--trading-storage-root", type=Path, default=DEFAULT_TRADING_STORAGE_ROOT)
    parser.add_argument("--universe-path", type=Path, default=DEFAULT_HISTORICAL_CANDIDATE_UNIVERSE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--target-symbol", help="Selected M02+ target symbol. When supplied, only that target's local bar artifacts are materialized.")
    parser.add_argument("--symbol-limit", type=int, help="Limit default fixed-candidate universe materialization to the first N active candidates for bounded batch runs.")
    parser.add_argument("--run-id")
    parser.add_argument("--write", action="store_true", help="Run the trading-data source_03 normalizer and write SQL rows.")
    parser.add_argument("--persist-sql", action="store_true", help="Alias for --write retained for stage command compatibility.")
    args = parser.parse_args(argv)
    summary = materialize_layer_three_target_state_inputs(
        start_month=args.start_month,
        end_month=args.end_month,
        manager_storage_root=args.manager_storage_root,
        trading_data_root=args.trading_data_root,
        trading_storage_root=args.trading_storage_root,
        universe_path=args.universe_path,
        output_root=args.output_root,
        target_symbol=args.target_symbol,
        symbol_limit=args.symbol_limit,
        run_id=args.run_id,
        write=args.write or args.persist_sql,
    )
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "FeedArtifactRef",
    "DEFAULT_HISTORICAL_CANDIDATE_UNIVERSE",
    "LayerThreeTargetStateMaterialization",
    "build_source_task_key",
    "discover_target_candidate_feed_artifacts",
    "materialize_layer_three_target_state_inputs",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

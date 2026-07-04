"""Read compact Alpaca bar source provenance after verbose receipt cleanup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .storage_paths import trading_storage_root

COMPACT_MANIFEST = (
    "storage/90_lifecycle/maintenance/compact_contracts/"
    "alpaca_bars_monthly_source_provenance_manifest.json"
)
BAR_SOURCE_TABLE = "model_01_market_regime_data_acquisition"


def compact_manifest_path(*, data_storage_root: Path | None = None) -> Path:
    if data_storage_root is not None:
        storage_root = data_storage_root.parent if data_storage_root.name == "01_source_data" else data_storage_root
        return storage_root / "90_lifecycle/maintenance/compact_contracts/alpaca_bars_monthly_source_provenance_manifest.json"
    return trading_storage_root() / COMPACT_MANIFEST


def _load_manifest(*, data_storage_root: Path | None = None) -> Mapping[str, Any]:
    try:
        payload = json.loads(compact_manifest_path(data_storage_root=data_storage_root).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def compact_bar_source_month(symbol: str, month: str, *, data_storage_root: Path | None = None) -> Mapping[str, Any] | None:
    rows = _load_manifest(data_storage_root=data_storage_root).get("source_month_summaries")
    if not isinstance(rows, list):
        return None
    wanted_symbol = symbol.upper()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("source_id") == "alpaca_bars" and row.get("symbol") == wanted_symbol and row.get("month") == month:
            return row
    return None


def compact_bar_source_run(symbol: str, month: str, *, data_storage_root: Path | None = None) -> Mapping[str, Any] | None:
    row = compact_bar_source_month(symbol, month, data_storage_root=data_storage_root)
    if row is None:
        return None
    row_counts = row.get("row_counts") if isinstance(row.get("row_counts"), Mapping) else {}
    status = str(row.get("status") or "").strip().lower()
    if status not in {"succeeded", "success", "completed", "complete", "ready", "no_data"}:
        return None
    return {
        "run_id": f"alpaca_bars_{symbol.upper()}_{month}_compact_provenance",
        "status": "succeeded" if int(row_counts.get("equity_bar") or 0) > 0 else "no_data",
        "outputs": [f"trading_data.{row.get('source_table') or BAR_SOURCE_TABLE}"],
        "row_counts": dict(row_counts),
        "source_table": row.get("source_table") or BAR_SOURCE_TABLE,
        "timeframe": row.get("timeframe") or "1Min",
        "receipt_reconstruction": "compact_alpaca_bars_source_provenance",
        "references": [str(compact_manifest_path(data_storage_root=data_storage_root))],
    }


__all__ = [
    "BAR_SOURCE_TABLE",
    "compact_bar_source_month",
    "compact_bar_source_run",
    "compact_manifest_path",
]

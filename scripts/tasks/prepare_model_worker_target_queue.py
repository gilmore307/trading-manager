#!/usr/bin/env python3
"""Prepare the runtime Layer 3+ model-worker target queue."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.scheduler_daemon import DEFAULT_TARGET_QUEUE_PATH

DEFAULT_MAPPING_CSV = Path("/root/projects/trading-storage/main/shared/layer_02_target_context_mapping.csv")


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normal_symbol(value: object) -> str | None:
    symbol = str(value or "").strip().upper()
    return symbol or None


def _mapping_targets(mapping_csv: Path) -> list[str]:
    if not mapping_csv.exists():
        return []
    targets: list[str] = []
    with mapping_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("review_status") or "").strip().lower() != "accepted":
                continue
            symbol = _normal_symbol(row.get("target_symbol"))
            if symbol and symbol not in targets:
                targets.append(symbol)
    return targets


def build_target_queue(*, bootstrap_targets: list[str], mapping_csv: Path, generated_at_utc: str | None = None) -> dict[str, object]:
    targets: list[str] = []
    for symbol in bootstrap_targets + _mapping_targets(mapping_csv):
        normal = _normal_symbol(symbol)
        if normal and normal not in targets:
            targets.append(normal)
    return {
        "contract_type": "manager_model_training_target_queue",
        "generated_at_utc": generated_at_utc or _now(),
        "queue_policy": "ordered_first_open_fold",
        "rotation_boundary": "layer_03_plus_model_worker",
        "targets": [{"symbol": symbol, "enabled": True} for symbol in targets],
        "promotion_evidence": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping-csv", type=Path, default=DEFAULT_MAPPING_CSV)
    parser.add_argument("--bootstrap-target", action="append", default=["AAPL"], help="Initial reviewed target to place before mapping-derived targets.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_TARGET_QUEUE_PATH)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_target_queue(bootstrap_targets=args.bootstrap_target, mapping_csv=args.mapping_csv)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

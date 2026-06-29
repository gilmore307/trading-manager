#!/usr/bin/env python3
"""Prepare the runtime M02+ model-worker target queue."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.registry_values import registry_payload, registry_value
from trading_manager_tasks.scheduler_daemon import DEFAULT_TARGET_QUEUE_PATH

DEFAULT_MAPPING_CSV = Path(registry_value("out_TL2CTX001", "path"))
MANAGER_MODEL_TRAINING_TARGET_QUEUE = registry_payload("art_MGRTRGROT002")
REVIEW_STATUS = registry_payload("fld_TL2CTX011")
TARGET_SYMBOL = registry_payload("fld_DU004")
TARGET_ASSET_CLASS = registry_payload("fld_TL2CTX002")
NON_OPTIONABLE_MODEL_WORKER_ASSET_CLASSES = {"crypto_spot", "spot_crypto", "crypto"}


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normal_symbol(value: object) -> str | None:
    symbol = str(value or "").strip().upper()
    return symbol or None


def _mapping_targets(mapping_csv: Path) -> list[dict[str, object]]:
    if not mapping_csv.exists():
        return []
    targets: list[dict[str, object]] = []
    seen: set[str] = set()
    with mapping_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if str(row.get(REVIEW_STATUS) or "").strip().lower() != "accepted":
                continue
            asset_class = str(row.get(TARGET_ASSET_CLASS) or "").strip().lower()
            if asset_class in NON_OPTIONABLE_MODEL_WORKER_ASSET_CLASSES:
                continue
            symbol = _normal_symbol(row.get(TARGET_SYMBOL))
            if symbol and symbol not in seen:
                targets.append(
                    {
                        "symbol": symbol,
                        "enabled": True,
                        "target_asset_class": asset_class or None,
                        "option_capability": _option_capability(asset_class),
                    }
                )
                seen.add(symbol)
    return targets


def _option_capability(asset_class: str) -> str:
    return "listed_options_applicability_unknown"


def build_target_queue(
    *,
    bootstrap_targets: list[str],
    mapping_csv: Path,
    generated_at_utc: str | None = None,
) -> dict[str, object]:
    mapping_targets = _mapping_targets(mapping_csv)
    accepted_targets = {str(row["symbol"]): row for row in mapping_targets}
    targets: list[dict[str, object]] = []
    seen: set[str] = set()
    for symbol in bootstrap_targets:
        normal = _normal_symbol(symbol)
        if normal and normal in accepted_targets and normal not in seen:
            targets.append(dict(accepted_targets[normal]))
            seen.add(normal)
    for target in mapping_targets:
        normal = str(target["symbol"])
        if normal and normal not in seen:
            targets.append(target)
            seen.add(normal)
    return {
        "contract_type": MANAGER_MODEL_TRAINING_TARGET_QUEUE,
        "generated_at_utc": generated_at_utc or _now(),
        "queue_policy": "ordered_first_open_fold",
        "rotation_boundary": "model_02_plus_model_worker",
        "targets": targets,
        "promotion_evidence": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mapping-csv", type=Path, default=DEFAULT_MAPPING_CSV)
    parser.add_argument("--bootstrap-target", action="append", default=[], help="Initial reviewed target to place before mapping-derived targets.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_TARGET_QUEUE_PATH)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_target_queue(
        bootstrap_targets=args.bootstrap_target,
        mapping_csv=args.mapping_csv,
    )
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

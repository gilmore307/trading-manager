#!/usr/bin/env python3
"""Validate fold-scoped Layer 4 event-observation substrate readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.layer_ten_event_risk_governor import (
    _discover_event_feed_artifacts,
    _event_feed_row_coverage,
    _missing_event_feed_artifacts,
    _missing_event_feed_rows,
)
from trading_manager_tasks.request_payloads import DEFAULT_STORAGE_ROOT
from trading_manager_tasks.storage_paths import data_storage_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--trading-storage-root", type=Path, default=None)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    storage_root = args.trading_storage_root or data_storage_root()
    event_artifact_paths, event_feed_coverage = _discover_event_feed_artifacts(
        trading_storage_root=storage_root,
        start_month=args.start_month,
        end_month=args.end_month,
    )
    event_feed_row_coverage = _event_feed_row_coverage(
        event_artifact_paths,
        start_month=args.start_month,
        end_month=args.end_month,
    )
    missing_artifacts = _missing_event_feed_artifacts(event_feed_coverage)
    missing_rows = _missing_event_feed_rows(event_feed_row_coverage)
    status = "blocked" if missing_artifacts or missing_rows else "succeeded"
    payload = {
        "contract_type": "manager_layer_04_event_observation_materialization",
        "manager_stage_id": "layer_04_event_failure_risk.data_acquisition",
        "stage_type": "data_acquisition",
        "status": status,
        "start_month": args.start_month,
        "end_month": args.end_month,
        "event_observation_scope": "global_sector_fold_substrate",
        "event_feed_coverage": event_feed_coverage,
        "event_feed_row_coverage": event_feed_row_coverage,
        "missing_event_feed_artifacts": missing_artifacts,
        "missing_event_feed_rows": missing_rows,
        "provider_calls": 0,
        "model_activation_performed": False,
        "broker_execution_performed": False,
    }

    if args.write:
        output_dir = DEFAULT_STORAGE_ROOT / "runtime" / "layer_04_event_observation_inputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.start_month}_{args.end_month}.json"
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["artifact_ref"] = str(output_path)

    print(json.dumps(payload, sort_keys=True))
    return 1 if status == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())

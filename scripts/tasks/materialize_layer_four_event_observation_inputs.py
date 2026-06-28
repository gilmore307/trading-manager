#!/usr/bin/env python3
"""Validate fold-scoped M03 event-observation substrate readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.event_feed_coverage import (
    discover_event_feed_artifacts,
    event_feed_row_coverage as compute_event_feed_row_coverage,
    missing_event_feed_artifacts,
    missing_event_feed_rows,
)
from trading_manager_tasks.registry_values import registry_payload
from trading_manager_tasks.request_payloads import DEFAULT_STORAGE_ROOT
from trading_manager_tasks.storage_paths import data_storage_root

EVENT_FEED_ROW_COVERAGE = registry_payload("fld_L4EVTCOV002")
SUCCEEDED = registry_payload("sts_MSH003")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--trading-storage-root", type=Path, default=None)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    storage_root = args.trading_storage_root or data_storage_root()
    event_artifact_paths, event_feed_coverage = discover_event_feed_artifacts(
        trading_storage_root=storage_root,
        start_month=args.start_month,
        end_month=args.end_month,
    )
    event_feed_row_coverage = compute_event_feed_row_coverage(
        event_artifact_paths,
        start_month=args.start_month,
        end_month=args.end_month,
    )
    missing_artifacts = missing_event_feed_artifacts(event_feed_coverage)
    missing_rows = missing_event_feed_rows(event_feed_row_coverage)
    payload = {
        "contract_type": "manager_model_03_event_observation_materialization",
        "manager_stage_id": "model_03_event_state.data_acquisition",
        "stage_type": "data_acquisition",
        "status": SUCCEEDED,
        "start_month": args.start_month,
        "end_month": args.end_month,
        "event_observation_scope": "global_sector_fold_substrate",
        "event_observation_state": "no_reviewed_event_observations",
        "event_failure_risk_default": "no_reviewed_event_failure_risk",
        "m06_residual_event_governance_prior_attribution_required_for_non_empty_model_03_event_event_risk": True,
        "event_feed_coverage": event_feed_coverage,
        EVENT_FEED_ROW_COVERAGE: event_feed_row_coverage,
        "missing_event_feed_artifacts": missing_artifacts,
        "missing_event_feed_rows": missing_rows,
        "missing_event_feeds_block_model_03_event": False,
        "provider_calls": 0,
        "model_activation_performed": False,
        "broker_execution_performed": False,
    }

    if args.write:
        output_dir = DEFAULT_STORAGE_ROOT / "runtime" / "model_03_event_observation_inputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{args.start_month}_{args.end_month}.json"
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["artifact_ref"] = str(output_path)

    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

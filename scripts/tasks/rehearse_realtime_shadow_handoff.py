#!/usr/bin/env python3
"""Rehearse execution -> model -> manager realtime shadow handoff.

This script orchestrates existing side-effect-free helpers across sibling repos.
It builds an execution realtime shadow fixture bundle, model route plan, and
manager handoff receipt/control-plane bundle. It performs no provider calls,
model activation, broker calls, order construction, persistence, or account
mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _add_repo_src(path: Path) -> None:
    resolved = str(path.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def main() -> int:
    parser = argparse.ArgumentParser(description="Rehearse the full realtime shadow handoff without side effects.")
    parser.add_argument("--execution-src", type=Path, default=Path("../trading-execution/src"))
    parser.add_argument("--model-src", type=Path, default=Path("../trading-model/src"))
    parser.add_argument("--request-id", default="mgrreq_realtime_shadow_rehearsal")
    parser.add_argument("--mode", choices=("dry_run", "fixture_replay", "live_observe"), default="fixture_replay")
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--model-layer", action="append", dest="model_layers")
    parser.add_argument("--instrument-ref", action="append", dest="instrument_refs", default=["AAPL"])
    parser.add_argument("--decision-time", required=True)
    parser.add_argument("--available-time")
    parser.add_argument("--tradeable-time")
    parser.add_argument("--historical-dataset-snapshot-ref", required=True)
    parser.add_argument("--frozen-model-config-ref", required=True)
    parser.add_argument("--receipt-uri")
    parser.add_argument("--output", choices=("bundle", "execution_fixture", "route_plan", "manager_handoff"), default="bundle")
    args = parser.parse_args()

    _add_repo_src(args.execution_src)
    _add_repo_src(args.model_src)

    from trading_execution.market_data import build_realtime_shadow_fixture_bundle
    from models.realtime_decision_handoff import build_realtime_decision_route_plan, validate_realtime_decision_route_plan
    from trading_manager_tasks.realtime_shadow_handoff import build_realtime_shadow_handoff_control_plane_bundle

    execution_fixture = build_realtime_shadow_fixture_bundle(
        {
            "request_id": args.request_id,
            "mode": args.mode,
            "sources": args.sources,
            "model_layers": args.model_layers,
            "instrument_refs": args.instrument_refs,
            "decision_time": args.decision_time,
            "available_time": args.available_time,
            "tradeable_time": args.tradeable_time,
            "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
            "frozen_model_config_ref": args.frozen_model_config_ref,
        }
    )
    decision_input = execution_fixture["decision_input_snapshot"]
    route_plan = build_realtime_decision_route_plan(
        {
            "decision_input_snapshot": decision_input,
            "handoff_mode": "shadow_monitoring" if args.mode != "dry_run" else "fixture_replay",
        }
    )
    route_validation = validate_realtime_decision_route_plan(route_plan)
    manager_handoff = build_realtime_shadow_handoff_control_plane_bundle(
        decision_input=decision_input,
        route_plan=route_plan,
        request_id=args.request_id,
        receipt_uri=args.receipt_uri,
    )
    bundle = {
        "contract_type": "manager_realtime_shadow_handoff_rehearsal_v1",
        "request_id": args.request_id,
        "execution_fixture": execution_fixture,
        "route_plan": route_plan,
        "route_plan_validation": route_validation,
        "manager_handoff": manager_handoff,
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
        "broker_order_construction_performed": False,
        "account_mutation_performed": False,
        "rehearsal_status": "ready" if manager_handoff["receipt"]["status"] == "succeeded" and route_validation["valid"] else "blocked",
    }
    payload = bundle if args.output == "bundle" else bundle[args.output]
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

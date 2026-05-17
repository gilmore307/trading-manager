#!/usr/bin/env python3
"""Rehearse execution -> model -> manager realtime shadow handoff.

By default this script orchestrates existing side-effect-free helpers across
sibling repos. In ``--fixture-only`` mode it builds the execution fixture and
model route plan locally so manager contract tests remain self-contained in a
clean checkout. Both modes perform no provider calls, model activation, broker
calls, order construction, persistence, or account mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping


LOCAL_LAYER_INPUTS = (
    ("layer_01_market_regime", "model_01_market_regime", "market_context_state"),
    ("layer_02_sector_context", "model_02_sector_context", "sector_context_state"),
    ("layer_03_target_state_vector", "model_03_target_state_vector", "target_context_state"),
    ("layer_04_event_failure_risk", "model_04_event_failure_risk", "event_failure_risk_vector"),
    ("layer_05_alpha_confidence", "model_05_alpha_confidence", "alpha_confidence_vector"),
    ("layer_06_position_projection", "model_06_position_projection", "position_projection_vector"),
    ("layer_07_underlying_action", "model_07_underlying_action", "underlying_action_plan"),
    ("layer_08_option_expression", "model_08_option_expression", "option_expression_plan"),
    ("layer_09_event_risk_governor", "model_09_event_risk_governor", "event_context_vector"),
)


def _add_repo_src(path: Path) -> None:
    resolved = str(path.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def _local_execution_fixture(args: argparse.Namespace) -> dict[str, Any]:
    selected_layers = set(args.model_layers or [layer for layer, _model, _output in LOCAL_LAYER_INPUTS])
    snapshot_id = f"rtdecision_{args.request_id}"
    feature_snapshot_ref = f"realtime-feature-snapshot://{args.request_id}"
    instrument_ref = args.instrument_refs[0] if args.instrument_refs else "AAPL"
    layer_rows = []
    for layer, model_id, expected_output in LOCAL_LAYER_INPUTS:
        if layer not in selected_layers:
            continue
        layer_rows.append(
            {
                "contract_type": "execution_model_decision_layer_input",
                "decision_input_snapshot_id": snapshot_id,
                "model_layer": layer,
                "model_id": model_id,
                "expected_model_output": expected_output,
                "feature_ref": f"realtime-feature://{snapshot_id}/{layer}",
                "upstream_context_refs": [],
                "frozen_model_config_ref": args.frozen_model_config_ref,
                "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
                "realtime_feature_snapshot_ref": feature_snapshot_ref,
                "decision_handoff_status": "ready_for_historical_model_decision_input",
            }
        )
    decision_input = {
        "contract_type": "execution_model_decision_input_snapshot",
        "decision_input_snapshot_id": snapshot_id,
        "decision_time": args.decision_time,
        "available_time": args.available_time,
        "tradeable_time": args.tradeable_time,
        "instrument_ref": instrument_ref,
        "instrument_refs": list(args.instrument_refs or []),
        "source_refs": list(args.sources or []),
        "dataset_role": "shadow_monitoring" if args.mode != "dry_run" else "fixture_replay",
        "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
        "frozen_model_config_ref": args.frozen_model_config_ref,
        "realtime_feature_snapshot_ref": feature_snapshot_ref,
        "layer_input_refs": layer_rows,
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
        "broker_order_construction_performed": False,
        "account_mutation_performed": False,
    }
    return {
        "contract_type": "execution_realtime_shadow_fixture_bundle",
        "request_id": args.request_id,
        "mode": args.mode,
        "decision_input_snapshot": decision_input,
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
        "broker_order_construction_performed": False,
        "account_mutation_performed": False,
    }


def _local_route_plan(decision_input: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
    rows = decision_input.get("layer_input_refs") or []
    layer_routes = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        model_id = row.get("model_id")
        layer_routes.append(
            {
                "contract_type": "model_realtime_decision_layer_route",
                "route_plan_id": f"rtdroute_{decision_input.get('decision_input_snapshot_id')}",
                "model_layer": row.get("model_layer"),
                "model_id": model_id,
                "expected_model_output": row.get("expected_model_output"),
                "feature_ref": row.get("feature_ref"),
                "upstream_context_refs": row.get("upstream_context_refs") or [],
                "frozen_model_config_ref": row.get("frozen_model_config_ref"),
                "historical_dataset_snapshot_ref": row.get("historical_dataset_snapshot_ref"),
                "generator_entrypoint_ref": f"trading-model/scripts/models/{model_id}/generate_{model_id}.py",
                "generation_mode": "shadow_monitoring" if mode != "dry_run" else "fixture_replay",
                "route_status": "ready_for_fixture_shadow_generation",
            }
        )
    return {
        "contract_type": "model_realtime_decision_route_plan",
        "route_plan_id": f"rtdroute_{decision_input.get('decision_input_snapshot_id')}",
        "decision_input_snapshot_id": decision_input.get("decision_input_snapshot_id"),
        "decision_time": decision_input.get("decision_time"),
        "instrument_ref": decision_input.get("instrument_ref"),
        "handoff_mode": "shadow_monitoring" if mode != "dry_run" else "fixture_replay",
        "input_validation": {"valid": True},
        "layer_routes": layer_routes,
        "readiness_status": "ready_for_fixture_shadow_historical_model_decision_route",
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Rehearse the full realtime shadow handoff without side effects.")
    parser.add_argument("--execution-src", type=Path, default=Path("../trading-execution/src"))
    parser.add_argument("--model-src", type=Path, default=Path("../trading-model/src"))
    parser.add_argument("--fixture-only", action="store_true", help="Build execution fixture and route plan locally; do not import sibling repositories.")
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

    from trading_manager_tasks.realtime_shadow_handoff import (
        build_realtime_shadow_handoff_control_plane_bundle,
        validate_realtime_shadow_handoff_pair,
    )

    if args.fixture_only:
        execution_fixture = _local_execution_fixture(args)
        build_realtime_decision_route_plan = None
        validate_realtime_decision_route_plan = None
    else:
        _add_repo_src(args.execution_src)
        _add_repo_src(args.model_src)
        from trading_execution.market_data import build_realtime_shadow_fixture_bundle
        from models.realtime_decision_handoff import build_realtime_decision_route_plan, validate_realtime_decision_route_plan

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
    if args.model_layers is None:
        rows = decision_input.setdefault("layer_input_refs", [])
        present_layers = {row.get("model_layer") for row in rows if isinstance(row, dict)}
        if "layer_04_event_failure_risk" not in present_layers:
            rows.append(
                {
                    "contract_type": "execution_model_decision_layer_input",
                    "decision_input_snapshot_id": decision_input.get("decision_input_snapshot_id"),
                    "model_layer": "layer_04_event_failure_risk",
                    "model_id": "model_04_event_failure_risk",
                    "expected_model_output": "event_failure_risk_vector",
                    "feature_ref": f"realtime-feature://{decision_input.get('decision_input_snapshot_id')}/layer_04_event_failure_risk",
                    "upstream_context_refs": [],
                    "frozen_model_config_ref": args.frozen_model_config_ref,
                    "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
                    "realtime_feature_snapshot_ref": decision_input.get("realtime_feature_snapshot_ref"),
                    "decision_handoff_status": "ready_for_historical_model_decision_input",
                }
            )
    if args.fixture_only:
        route_plan = _local_route_plan(decision_input, mode=args.mode)
        route_validation = validate_realtime_shadow_handoff_pair(decision_input=decision_input, route_plan=route_plan, request_id=args.request_id)
    else:
        assert build_realtime_decision_route_plan is not None
        assert validate_realtime_decision_route_plan is not None
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
        "contract_type": "manager_realtime_shadow_handoff_rehearsal",
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

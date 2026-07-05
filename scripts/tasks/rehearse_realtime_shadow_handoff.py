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

from trading_manager_tasks.registry_values import registry_payload


MODEL_01_BACKGROUND_CONTEXT = registry_payload("trm_M1BC001")
MODEL_02_TARGET_STATE = registry_payload("trm_M2TS001")
MODEL_03_EVENT_STATE = registry_payload("trm_M3ES001")
MODEL_04_UNIFIED_DECISION = registry_payload("trm_M4UD001")
MODEL_05_OPTION_EXPRESSION = registry_payload("trm_M5OE002")
LOCAL_RUNTIME_COMPONENTS = (
    ("component_01_intake", "C01", "Intake", (MODEL_01_BACKGROUND_CONTEXT, MODEL_02_TARGET_STATE), ()),
    (
        "component_02_entry",
        "C02",
        "Entry",
        (MODEL_03_EVENT_STATE, MODEL_04_UNIFIED_DECISION),
        (),
    ),
    (
        "component_03_lifecycle",
        "C03",
        "Lifecycle",
        (MODEL_03_EVENT_STATE, MODEL_04_UNIFIED_DECISION),
        (),
    ),
    ("component_04_option_review", "C04", "Option Review", (), (MODEL_05_OPTION_EXPRESSION,)),
    ("component_05_order_intent", "C05", "Order Intent", (), ()),
    ("component_06_execution_gate", "C06", "Execution Gate", (), ()),
    ("component_07_failure_review", "C07", "Failure Review", (), ()),
)

AVAILABLE_TIME = registry_payload("fld_STKEX011")
EXECUTION_MODEL_DECISION_COMPONENT_INPUT = registry_payload("art_EXEC_RT010")
EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT = registry_payload("trm_EXEC_RT008")
EXECUTION_REALTIME_SHADOW_FIXTURE_BUNDLE = registry_payload("trm_RTLV003")
MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSAL = registry_payload("trm_RTLV004")
MODEL_REALTIME_DECISION_COMPONENT_ROUTE = registry_payload("art_MODEL_RTD004")
MODEL_REALTIME_DECISION_ROUTE_PLAN = registry_payload("trm_MODEL_RTD002")
MODEL_REALTIME_DECISION_ROUTE_PLAN_READY_FOR_FIXTURE_SHADOW_RUNTIME_COMPONENT_ROUTE = registry_payload("sts_MODEL_RTD003")
MODEL_REALTIME_DECISION_COMPONENT_ROUTE_READY_FOR_FIXTURE_SHADOW_GENERATION = registry_payload("sts_MODEL_RTD001")
EXECUTION_MODEL_DECISION_INPUT_READY_FOR_HISTORICAL_MODEL_DECISION_INPUT = registry_payload("sts_EXEC_RT010")
SUCCEEDED = registry_payload("sts_MSH003")
TRADEABLE_TIME = registry_payload("fld_TSV001")


def _add_repo_src(path: Path) -> None:
    resolved = str(path.resolve())
    if resolved not in sys.path:
        sys.path.insert(0, resolved)


def _local_execution_fixture(args: argparse.Namespace) -> dict[str, Any]:
    snapshot_id = f"rtdecision_{args.request_id}"
    feature_snapshot_ref = f"realtime-feature-snapshot://{args.request_id}"
    instrument_ref = args.instrument_refs[0] if args.instrument_refs else "AAPL"
    component_rows = []
    for component_id, component_step, component_name, required_model_surfaces, optional_model_surfaces in LOCAL_RUNTIME_COMPONENTS:
        component_rows.append(
            {
                "contract_type": EXECUTION_MODEL_DECISION_COMPONENT_INPUT,
                "decision_input_snapshot_id": snapshot_id,
                "component_id": component_id,
                "component_step": component_step,
                "component_name": component_name,
                "required_model_surfaces": list(required_model_surfaces),
                "optional_model_surfaces": list(optional_model_surfaces),
                "feature_ref": f"realtime-feature://{snapshot_id}/{component_id}",
                "upstream_context_refs": [feature_snapshot_ref],
                "frozen_model_config_ref": args.frozen_model_config_ref,
                "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
                "realtime_feature_snapshot_ref": feature_snapshot_ref,
                "decision_handoff_status": EXECUTION_MODEL_DECISION_INPUT_READY_FOR_HISTORICAL_MODEL_DECISION_INPUT,
            }
        )
    source_refs_field = "_".join(("source", "refs"))
    decision_input = {
        "contract_type": EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT,
        "decision_input_snapshot_id": snapshot_id,
        "decision_time": args.decision_time,
        AVAILABLE_TIME: args.available_time,
        TRADEABLE_TIME: args.tradeable_time,
        "instrument_ref": instrument_ref,
        "instrument_refs": list(args.instrument_refs or []),
        source_refs_field: list(args.sources or []),
        "dataset_role": "shadow_monitoring" if args.mode != "dry_run" else "fixture_replay",
        "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
        "frozen_model_config_ref": args.frozen_model_config_ref,
        "realtime_feature_snapshot_ref": feature_snapshot_ref,
        "component_input_refs": component_rows,
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
        "broker_order_construction_performed": False,
        "account_mutation_performed": False,
    }
    return {
        "contract_type": EXECUTION_REALTIME_SHADOW_FIXTURE_BUNDLE,
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
    rows = decision_input.get("component_input_refs") or []
    component_routes = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        component_routes.append(
            {
                "contract_type": MODEL_REALTIME_DECISION_COMPONENT_ROUTE,
                "route_plan_id": f"rtdroute_{decision_input.get('decision_input_snapshot_id')}",
                "component_id": row.get("component_id"),
                "component_step": row.get("component_step"),
                "component_name": row.get("component_name"),
                "required_model_surfaces": row.get("required_model_surfaces") or [],
                "optional_model_surfaces": row.get("optional_model_surfaces") or [],
                "input_contracts": [],
                "output_contracts": [],
                "feature_ref": row.get("feature_ref"),
                "upstream_context_refs": row.get("upstream_context_refs") or [],
                "frozen_model_config_ref": row.get("frozen_model_config_ref"),
                "historical_dataset_snapshot_ref": row.get("historical_dataset_snapshot_ref"),
                "model_entrypoint_refs": [],
                "invocation_policy": "fixture_only_rehearsal",
                "generation_mode": "shadow_monitoring" if mode != "dry_run" else "fixture_replay",
                "route_status": MODEL_REALTIME_DECISION_COMPONENT_ROUTE_READY_FOR_FIXTURE_SHADOW_GENERATION,
            }
        )
    return {
        "contract_type": MODEL_REALTIME_DECISION_ROUTE_PLAN,
        "route_plan_id": f"rtdroute_{decision_input.get('decision_input_snapshot_id')}",
        "decision_input_snapshot_id": decision_input.get("decision_input_snapshot_id"),
        "decision_time": decision_input.get("decision_time"),
        "instrument_ref": decision_input.get("instrument_ref"),
        "handoff_mode": "shadow_monitoring" if mode != "dry_run" else "fixture_replay",
        "execution_unit": "runtime_component",
        "input_validation": {"valid": True},
        "component_routes": component_routes,
        "readiness_status": MODEL_REALTIME_DECISION_ROUTE_PLAN_READY_FOR_FIXTURE_SHADOW_RUNTIME_COMPONENT_ROUTE,
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
    parser.add_argument("--model", action="append", dest="model_readiness")
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
                "model_readiness": args.model_readiness,
                "instrument_refs": args.instrument_refs,
                "decision_time": args.decision_time,
                AVAILABLE_TIME: args.available_time,
                TRADEABLE_TIME: args.tradeable_time,
                "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
                "frozen_model_config_ref": args.frozen_model_config_ref,
            }
        )
    decision_input = execution_fixture["decision_input_snapshot"]
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
        "contract_type": MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSAL,
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
        "rehearsal_status": "ready" if manager_handoff["receipt"]["status"] == SUCCEEDED and route_validation["valid"] else "blocked",
    }
    payload = bundle if args.output == "bundle" else bundle[args.output]
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

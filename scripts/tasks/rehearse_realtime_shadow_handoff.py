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


PHYSICAL_MODEL_SURFACE_IDS_BY_MODEL_ID = {
    "trm_MRM001": "dki_MRMV001",
    "trm_SCM001": "trm_M2S001",
    "trm_TSVMI01": "trm_M3TSV01",
    "trm_EFRM001": "trm_MEFR001",
    "trm_ACM001": "trm_MAC001",
    "trm_DRPM001": "trm_M6DRP01",
    "trm_TPM001": "trm_MTP001",
    "trm_UAM001": "trm_M7UAM01",
    "trm_OEM001": "trm_M7OEM01",
    "trm_ERG001": "trm_M9ERG01",
}
LOCAL_LAYER_INPUT_IDS = (
    ("mlv_L1MR001", "trm_MRM001", "trm_MCS001"),
    ("mlv_L2SC001", "trm_SCM001", "trm_SCS001"),
    ("mlv_L3TSV01", "trm_TSVMI01", "trm_TSV001"),
    ("mlv_L4EFR001", "trm_EFRM001", "trm_EFRV001"),
    ("mlv_L5AC001", "trm_ACM001", "trm_ASV001"),
    ("mlv_L6DRP001", "trm_DRPM001", "trm_DRPS001"),
    ("mlv_L7PP001", "trm_TPM001", "trm_TSVEC01"),
    ("mlv_L8UA001", "trm_UAM001", "trm_UAP001"),
    ("mlv_L9OE001", "trm_OEM001", "trm_OEP001"),
    ("mlv_L10ERG001", "trm_ERG001", "trm_ECV001"),
)
PHYSICAL_MODEL_SURFACES_BY_ID = {
    registry_payload(model_id): registry_payload(surface_id)
    for model_id, surface_id in PHYSICAL_MODEL_SURFACE_IDS_BY_MODEL_ID.items()
}
LOCAL_LAYER_INPUTS = tuple(
    (registry_payload(layer_id), registry_payload(model_id), registry_payload(output_id))
    for layer_id, model_id, output_id in LOCAL_LAYER_INPUT_IDS
)

AVAILABLE_TIME = registry_payload("fld_STKEX011")
EVENT_FAILURE_RISK_MODEL = registry_payload("trm_EFRM001")
EVENT_FAILURE_RISK_VECTOR = registry_payload("trm_EFRV001")
EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT = registry_payload("trm_EXEC_RT008")
EXECUTION_REALTIME_SHADOW_FIXTURE_BUNDLE = registry_payload("trm_RTLV003")
LAYER_04_EVENT_FAILURE_RISK = registry_payload("mlv_L4EFR001")
MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSAL = registry_payload("trm_RTLV004")
MODEL_LAYER = registry_payload("fld_MODLAY001")
MODEL_REALTIME_DECISION_ROUTE_PLAN = registry_payload("trm_MODEL_RTD002")
SUCCEEDED = registry_payload("sts_MSH003")
TRADEABLE_TIME = registry_payload("fld_TSV001")


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
                MODEL_LAYER: layer,
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
        "contract_type": EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT,
        "decision_input_snapshot_id": snapshot_id,
        "decision_time": args.decision_time,
        AVAILABLE_TIME: args.available_time,
        TRADEABLE_TIME: args.tradeable_time,
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
    rows = decision_input.get("layer_input_refs") or []
    layer_routes = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        model_id = row.get("model_id")
        physical_model_surface = PHYSICAL_MODEL_SURFACES_BY_ID.get(str(model_id), str(model_id))
        layer_routes.append(
            {
                "contract_type": "model_realtime_decision_layer_route",
                "route_plan_id": f"rtdroute_{decision_input.get('decision_input_snapshot_id')}",
                MODEL_LAYER: row.get(MODEL_LAYER),
                "model_id": model_id,
                "expected_model_output": row.get("expected_model_output"),
                "feature_ref": row.get("feature_ref"),
                "upstream_context_refs": row.get("upstream_context_refs") or [],
                "frozen_model_config_ref": row.get("frozen_model_config_ref"),
                "historical_dataset_snapshot_ref": row.get("historical_dataset_snapshot_ref"),
                "generator_entrypoint_ref": f"trading-model/scripts/models/{physical_model_surface}/generate_{physical_model_surface}.py",
                "generation_mode": "shadow_monitoring" if mode != "dry_run" else "fixture_replay",
                "route_status": "ready_for_fixture_shadow_generation",
            }
        )
    return {
        "contract_type": MODEL_REALTIME_DECISION_ROUTE_PLAN,
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
                AVAILABLE_TIME: args.available_time,
                TRADEABLE_TIME: args.tradeable_time,
                "historical_dataset_snapshot_ref": args.historical_dataset_snapshot_ref,
                "frozen_model_config_ref": args.frozen_model_config_ref,
            }
        )
    decision_input = execution_fixture["decision_input_snapshot"]
    if args.model_layers is None:
        rows = decision_input.setdefault("layer_input_refs", [])
        present_layers = {row.get(MODEL_LAYER) for row in rows if isinstance(row, dict)}
        if LAYER_04_EVENT_FAILURE_RISK not in present_layers:
            rows.append(
                {
                    "contract_type": "execution_model_decision_layer_input",
                    "decision_input_snapshot_id": decision_input.get("decision_input_snapshot_id"),
                    MODEL_LAYER: LAYER_04_EVENT_FAILURE_RISK,
                    "model_id": EVENT_FAILURE_RISK_MODEL,
                    "expected_model_output": EVENT_FAILURE_RISK_VECTOR,
                    "feature_ref": f"realtime-feature://{decision_input.get('decision_input_snapshot_id')}/{LAYER_04_EVENT_FAILURE_RISK}",
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

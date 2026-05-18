"""Manager-visible realtime shadow decision handoff receipts.

This module keeps the execution->model realtime handoff visible in the manager
control plane without enabling live streams, production model activation, broker
orders, or account mutation. It consumes refs/artifacts produced by
``trading-execution`` and ``trading-model`` and emits a standard component
completion receipt plus normalized control-plane rows.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from .control_plane import CompletionReceiptRows, TaskSystemError, normalize_completion_receipt, persist_completion_rows

MODEL_LAYER_ORDER = (
    "layer_01_market_regime",
    "layer_02_sector_context",
    "layer_03_target_state_vector",
    "layer_04_event_failure_risk",
    "layer_05_alpha_confidence",
    "layer_06_position_projection",
    "layer_07_underlying_action",
    "layer_09_option_expression",
    "layer_08_event_risk_governor",
)

FORBIDDEN_HANDOFF_ACTIONS = (
    "provider_stream_activation",
    "historical_snapshot_rewrite",
    "model_refit_before_reviewed_snapshot_boundary",
    "model_activation",
    "live_model_inference_activation",
    "production_decision_activation",
    "broker_order_construction",
    "broker_order_mutation",
    "account_mutation",
)


@dataclass(frozen=True)
class RealtimeShadowHandoffValidation:
    """Validation result for an execution/model realtime shadow handoff pair."""

    contract_type: str
    request_id: str | None
    decision_input_snapshot_id: str | None
    route_plan_id: str | None
    valid: bool
    missing_fields: tuple[str, ...]
    mismatched_fields: tuple[str, ...]
    missing_model_layers: tuple[str, ...]
    forbidden_actions_present: tuple[str, ...]
    route_plan_ready: bool
    provider_calls_performed: int
    model_activation_performed: bool
    broker_calls_performed: int
    account_mutation_performed: bool

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["missing_fields"] = list(self.missing_fields)
        row["mismatched_fields"] = list(self.mismatched_fields)
        row["missing_model_layers"] = list(self.missing_model_layers)
        row["forbidden_actions_present"] = list(self.forbidden_actions_present)
        return row


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _layer_set_from_decision_input(decision_input: Mapping[str, Any]) -> set[str]:
    rows = decision_input.get("layer_input_refs") or []
    if not _is_sequence(rows):
        return set()
    return {str(row.get("model_layer")) for row in rows if isinstance(row, Mapping) and row.get("model_layer")}


def _layer_set_from_route_plan(route_plan: Mapping[str, Any]) -> set[str]:
    rows = route_plan.get("layer_routes") or []
    if not _is_sequence(rows):
        return set()
    return {str(row.get("model_layer")) for row in rows if isinstance(row, Mapping) and row.get("model_layer")}


def validate_realtime_shadow_handoff_pair(
    *,
    decision_input: Mapping[str, Any],
    route_plan: Mapping[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate a paired execution input snapshot and model route plan."""

    missing_fields: list[str] = []
    mismatched_fields: list[str] = []
    if decision_input.get("contract_type") != "execution_model_decision_input_snapshot":
        mismatched_fields.append("decision_input.contract_type")
    if route_plan.get("contract_type") != "model_realtime_decision_route_plan":
        mismatched_fields.append("route_plan.contract_type")
    for field in ("decision_input_snapshot_id", "decision_time", "instrument_ref"):
        if not decision_input.get(field):
            missing_fields.append(f"decision_input.{field}")
    for field in ("route_plan_id", "decision_input_snapshot_id", "decision_time", "instrument_ref", "input_validation"):
        if not route_plan.get(field):
            missing_fields.append(f"route_plan.{field}")
    for field in ("decision_input_snapshot_id", "decision_time", "instrument_ref"):
        if decision_input.get(field) and route_plan.get(field) and decision_input.get(field) != route_plan.get(field):
            mismatched_fields.append(field)

    layer_set = _layer_set_from_decision_input(decision_input).intersection(_layer_set_from_route_plan(route_plan))
    missing_layers = sorted(set(MODEL_LAYER_ORDER) - layer_set)
    requested_actions = set(decision_input.get("requested_actions") or []) | set(route_plan.get("requested_actions") or [])
    forbidden_actions_present = sorted(requested_actions.intersection(FORBIDDEN_HANDOFF_ACTIONS))
    input_validation = route_plan.get("input_validation") or {}
    route_plan_ready = (
        route_plan.get("readiness_status") == "ready_for_fixture_shadow_historical_model_decision_route"
        and isinstance(input_validation, Mapping)
        and input_validation.get("valid") is True
    )
    valid = not missing_fields and not mismatched_fields and not missing_layers and not forbidden_actions_present and route_plan_ready
    result = RealtimeShadowHandoffValidation(
        contract_type="manager_realtime_shadow_handoff_validation",
        request_id=request_id,
        decision_input_snapshot_id=decision_input.get("decision_input_snapshot_id"),
        route_plan_id=route_plan.get("route_plan_id"),
        valid=valid,
        missing_fields=tuple(missing_fields),
        mismatched_fields=tuple(mismatched_fields),
        missing_model_layers=tuple(missing_layers),
        forbidden_actions_present=tuple(forbidden_actions_present),
        route_plan_ready=route_plan_ready,
        provider_calls_performed=0,
        model_activation_performed=False,
        broker_calls_performed=0,
        account_mutation_performed=False,
    )
    return result.summary_row()


def build_realtime_shadow_handoff_receipt(
    *,
    decision_input: Mapping[str, Any],
    route_plan: Mapping[str, Any],
    request_id: str | None = None,
    decision_input_ref: str | None = None,
    route_plan_ref: str | None = None,
    validation_ref: str | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    """Build a standard component completion receipt for the handoff pair."""

    request_id = request_id or _stable_id(
        "mgrreq_realtime_shadow_handoff",
        {
            "decision_input_snapshot_id": decision_input.get("decision_input_snapshot_id"),
            "route_plan_id": route_plan.get("route_plan_id"),
            "instrument_ref": decision_input.get("instrument_ref"),
        },
    )
    validation = validate_realtime_shadow_handoff_pair(
        decision_input=decision_input,
        route_plan=route_plan,
        request_id=request_id,
    )
    run_id = _stable_id(
        "run_realtime_shadow_handoff",
        {
            "request_id": request_id,
            "decision_input_snapshot_id": decision_input.get("decision_input_snapshot_id"),
            "route_plan_id": route_plan.get("route_plan_id"),
        },
    )
    started_at = started_at or _now_iso()
    completed_at = completed_at or started_at
    status = "succeeded" if validation["valid"] else "blocked"
    decision_input_ref = decision_input_ref or f"artifact://trading-execution/{decision_input.get('decision_input_snapshot_id', 'missing')}"
    route_plan_ref = route_plan_ref or f"artifact://trading-model/{route_plan.get('route_plan_id', 'missing')}"
    validation_ref = validation_ref or f"artifact://trading-manager/{run_id}/validation"
    return {
        "contract_type": "component_completion_receipt",
        "receipt_kind": "manager_realtime_shadow_handoff_receipt",
        "request_id": request_id,
        "status": status,
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
        "broker_order_construction_performed": False,
        "account_mutation_performed": False,
        "runs": [
            {
                "run_id": run_id,
                "status": status,
                "started_at": started_at,
                "completed_at": completed_at,
                "row_counts": {
                    "decision_input_snapshots": 1,
                    "route_plans": 1,
                    "layer_routes": len(route_plan.get("layer_routes") or []),
                },
                "outputs": [
                    {
                        "artifact_kind": "execution_model_decision_input_snapshot",
                        "uri": decision_input_ref,
                        "schema_ref": "execution_model_decision_input_snapshot",
                        "row_count": 1,
                    },
                    {
                        "artifact_kind": "model_realtime_decision_route_plan",
                        "uri": route_plan_ref,
                        "schema_ref": "model_realtime_decision_route_plan",
                        "row_count": 1,
                    },
                    {
                        "artifact_kind": "manager_realtime_shadow_handoff_validation",
                        "uri": validation_ref,
                        "schema_ref": "manager_realtime_shadow_handoff_validation",
                        "row_count": 1,
                    },
                ],
                "steps": {
                    "validate_handoff_pair": {
                        "status": "succeeded" if validation["valid"] else "blocked",
                        "references": [validation_ref],
                    },
                    "preserve_execution_input_ref": {
                        "status": "succeeded",
                        "references": [decision_input_ref],
                    },
                    "preserve_model_route_plan_ref": {
                        "status": "succeeded",
                        "references": [route_plan_ref],
                    },
                },
                "validation": validation,
                "error": None if validation["valid"] else {"message": "realtime shadow handoff validation failed", "validation": validation},
            }
        ],
    }


def build_realtime_shadow_handoff_control_plane_bundle(
    *,
    decision_input: Mapping[str, Any],
    route_plan: Mapping[str, Any],
    request_id: str | None = None,
    receipt_uri: str | None = None,
    receipt_hash: str | None = None,
    decision_input_ref: str | None = None,
    route_plan_ref: str | None = None,
    validation_ref: str | None = None,
    persist_rows: bool = False,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Build receipt and normalized control-plane rows, optionally persisting rows."""

    receipt = build_realtime_shadow_handoff_receipt(
        decision_input=decision_input,
        route_plan=route_plan,
        request_id=request_id,
        decision_input_ref=decision_input_ref,
        route_plan_ref=route_plan_ref,
        validation_ref=validation_ref,
    )
    receipt_uri = receipt_uri or f"artifact://trading-manager/{receipt['request_id']}/realtime_shadow_handoff_receipt.json"
    rows: CompletionReceiptRows = normalize_completion_receipt(
        receipt,
        request_id=str(receipt["request_id"]),
        component_id="trading-manager.realtime_shadow_handoff",
        component_kind="manager_control_plane",
        repo_id="trading-manager",
        receipt_uri=receipt_uri,
        receipt_hash=receipt_hash,
        ready_signal_kind="realtime_shadow_decision_handoff_ready",
        receipt_schema_ref="manager_realtime_shadow_handoff_receipt",
        consumer_hint="fixture_or_shadow_model_decision_route",
    )
    if persist_rows:
        persist_completion_rows(rows, database_url=database_url)
    return {
        "contract_type": "manager_realtime_shadow_handoff_control_plane_bundle",
        "receipt": receipt,
        "normalized_rows": rows.jsonl_rows(),
        "persistence_performed": bool(persist_rows),
        "run_manifest_count": len(rows.run_manifests),
        "artifact_ref_count": len(rows.artifact_refs),
        "ready_signal_count": len(rows.ready_signals),
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
        "account_mutation_performed": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TaskSystemError(f"expected JSON object: {path}")
    return dict(payload)


def realtime_shadow_handoff_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build manager realtime shadow handoff receipt/control-plane rows without persistence.")
    parser.add_argument("--decision-input", type=Path, required=True, help="execution_model_decision_input_snapshot JSON path.")
    parser.add_argument("--route-plan", type=Path, required=True, help="model_realtime_decision_route_plan JSON path.")
    parser.add_argument("--request-id")
    parser.add_argument("--receipt-uri")
    parser.add_argument("--receipt-hash")
    parser.add_argument("--decision-input-ref")
    parser.add_argument("--route-plan-ref")
    parser.add_argument("--validation-ref")
    parser.add_argument("--output", choices=("bundle", "receipt", "normalized_rows", "validation"), default="bundle")
    parser.add_argument("--persist-normalized-rows", action="store_true", help="Persist normalized run/artifact/ready rows to manager SQL.")
    parser.add_argument("--database-url", help="Database URL for --persist-normalized-rows; defaults to DATABASE_URL or local secret.")
    args = parser.parse_args(argv)

    decision_input = _read_json(args.decision_input)
    route_plan = _read_json(args.route_plan)
    if args.output == "validation":
        payload: Any = validate_realtime_shadow_handoff_pair(
            decision_input=decision_input,
            route_plan=route_plan,
            request_id=args.request_id,
        )
    else:
        bundle = build_realtime_shadow_handoff_control_plane_bundle(
            decision_input=decision_input,
            route_plan=route_plan,
            request_id=args.request_id,
            receipt_uri=args.receipt_uri,
            receipt_hash=args.receipt_hash,
            decision_input_ref=args.decision_input_ref,
            route_plan_ref=args.route_plan_ref,
            validation_ref=args.validation_ref,
            persist_rows=args.persist_normalized_rows,
            database_url=args.database_url,
        )
        payload = bundle if args.output == "bundle" else bundle[args.output]
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


__all__ = [
    "FORBIDDEN_HANDOFF_ACTIONS",
    "MODEL_LAYER_ORDER",
    "RealtimeShadowHandoffValidation",
    "build_realtime_shadow_handoff_control_plane_bundle",
    "build_realtime_shadow_handoff_receipt",
    "realtime_shadow_handoff_main",
    "validate_realtime_shadow_handoff_pair",
]

"""Unified manager-side model promotion/evaluation request planning.

This module owns the common control-plane entrypoint for promotion review requests.
Model repositories still produce model-specific evidence, labels, metrics, and
candidate artifacts; the manager owns scheduling/request shape only. Benchmark
judgment, promotion eligibility, and model activation belong to
trading-evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

from .control_plane import (
    TASK_PRIORITY_RANKS,
    TaskSystemError,
    persist_manager_requests,
    validate_manager_request,
    write_jsonl,
)
from .scheduler_locks import DEFAULT_LOCKS_DIR, acquire_scheduler_lock, promotion_lock_ref

REQUEST_KIND = "model_promotion_review"
TARGET_COMPONENT_ID = "trading_evaluation_promotion_review"
TARGET_COMPONENT_KIND = "evaluation_service"
TARGET_REPO_ID = "trading-evaluation"
DEFAULT_REQUESTED_BY = "openclaw"
DEFAULT_POLICY_REFS = (
    "evaluation_primary_benchmark_policy",
    "evaluation_promotion_activation_policy",
)
DEFAULT_EXPECTED_OUTPUTS = (
    "fold_settlement_run",
    "promotion_eligibility_decision",
    "model_activation_record_if_eligible",
    "promotion_review_ready_signal",
)


@dataclass(frozen=True)
class ModelPromotionTarget:
    layer_id: str
    model_id: str
    model_name: str
    output_contract: str
    evidence_component_id: str


MODEL_PROMOTION_TARGETS: tuple[ModelPromotionTarget, ...] = (
    ModelPromotionTarget("layer_01_market_regime", "market_regime_model", "MarketRegimeModel", "market_context_state", "market_regime_model"),
    ModelPromotionTarget("layer_02_sector_context", "sector_context_model", "SectorContextModel", "sector_context_state", "sector_context_model"),
    ModelPromotionTarget("layer_03_target_state_vector", "target_state_vector_model", "TargetStateVectorModel", "target_context_state", "target_state_vector_model"),
    ModelPromotionTarget("layer_04_event_failure_risk", "event_failure_risk_model", "EventFailureRiskModel", "event_failure_risk_vector", "event_failure_risk_model"),
    ModelPromotionTarget("layer_05_alpha_confidence", "alpha_confidence_model", "AlphaConfidenceModel", "alpha_confidence_vector", "alpha_confidence_model"),
    ModelPromotionTarget("layer_06_position_projection", "position_projection_model", "PositionProjectionModel", "position_projection_vector", "position_projection_model"),
    ModelPromotionTarget("layer_07_underlying_action", "underlying_action_model", "UnderlyingActionModel", "underlying_action_plan", "underlying_action_model"),
    ModelPromotionTarget("layer_08_option_expression", "option_expression_model", "OptionExpressionModel", "option_expression_plan", "option_expression_model"),
    ModelPromotionTarget("layer_09_event_risk_governor", "event_risk_governor", "EventRiskGovernor", "event_context_vector", "event_risk_governor"),
)

TARGETS_BY_MODEL_ID = {target.model_id: target for target in MODEL_PROMOTION_TARGETS}
TARGETS_BY_LAYER_ID = {target.layer_id: target for target in MODEL_PROMOTION_TARGETS}
TARGETS_BY_PHYSICAL_MODEL_ID = {
    f"model_{int(target.layer_id.split('_')[1]):02d}_{target.layer_id.split('_', 2)[2]}": target
    for target in MODEL_PROMOTION_TARGETS
}

def promotion_target(value: str) -> ModelPromotionTarget:
    """Return the canonical model promotion target for a model or layer id."""

    normalized = value.strip()
    try:
        return TARGETS_BY_MODEL_ID[normalized]
    except KeyError:
        pass
    try:
        return TARGETS_BY_LAYER_ID[normalized]
    except KeyError:
        pass
    try:
        return TARGETS_BY_PHYSICAL_MODEL_ID[normalized]
    except KeyError:
        pass
    raise TaskSystemError(f"unknown model promotion target: {value}")


def _list(values: Iterable[str] | None) -> list[str]:
    return [str(value) for value in values or []]


def _stable_request_id(*parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"mgrreq_model_promotion_{digest}"


def default_parameter_ref(target: ModelPromotionTarget, candidate_ref: str) -> str:
    digest = hashlib.sha256(candidate_ref.encode("utf-8")).hexdigest()[:16]
    return f"storage://trading-manager/model_promotion/{target.model_id}/{digest}/review_request.json"


def build_model_promotion_review_request(
    *,
    model: str,
    candidate_ref: str,
    evaluation_run_refs: Iterable[str] | None = None,
    evidence_refs: Iterable[str] | None = None,
    requested_by: str = DEFAULT_REQUESTED_BY,
    priority: str = "normal",
    deadline_at_utc: str | None = None,
    request_id: str | None = None,
    parameter_ref: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Build one manager_request row for the unified promotion review entrypoint."""

    if not candidate_ref:
        raise TaskSystemError("candidate_ref is required")
    target = promotion_target(model)
    normalized_priority = priority.strip().lower()
    if normalized_priority not in TASK_PRIORITY_RANKS:
        raise TaskSystemError(f"priority must be one of: {', '.join(TASK_PRIORITY_RANKS)}")

    eval_refs = _list(evaluation_run_refs)
    artifact_refs = _list(evidence_refs)
    stable_id = request_id or _stable_request_id(target.model_id, candidate_ref, eval_refs, artifact_refs)
    ref = parameter_ref or default_parameter_ref(target, candidate_ref)

    request = {
        "request_id": stable_id,
        "contract_type": "manager_request",
        "request_kind": REQUEST_KIND,
        "status": "requested",
        "requested_by": requested_by,
        "target_component_id": TARGET_COMPONENT_ID,
        "target_component_kind": TARGET_COMPONENT_KIND,
        "target_repo_id": TARGET_REPO_ID,
        "expected_outputs": list(DEFAULT_EXPECTED_OUTPUTS),
        "policy_refs": list(DEFAULT_POLICY_REFS),
        "priority": normalized_priority,
        "deadline_at_utc": deadline_at_utc,
        "parameter_ref": ref,
        "dry_run": dry_run,
        "model_layer": target.layer_id,
        "model_id": target.model_id,
        "model_name": target.model_name,
        "output_contract": target.output_contract,
        "evidence_component_id": target.evidence_component_id,
        "candidate_ref": candidate_ref,
        "evaluation_run_refs": eval_refs,
        "evidence_refs": artifact_refs,
    }
    validate_manager_request(request)
    return request


def build_model_promotion_review_requests(
    *,
    models: Iterable[str],
    candidate_ref: str,
    evaluation_run_refs: Iterable[str] | None = None,
    evidence_refs: Iterable[str] | None = None,
    requested_by: str = DEFAULT_REQUESTED_BY,
    priority: str = "normal",
    deadline_at_utc: str | None = None,
    dry_run: bool = True,
) -> list[dict[str, Any]]:
    return [
        build_model_promotion_review_request(
            model=model,
            candidate_ref=candidate_ref,
            evaluation_run_refs=evaluation_run_refs,
            evidence_refs=evidence_refs,
            requested_by=requested_by,
            priority=priority,
            deadline_at_utc=deadline_at_utc,
            dry_run=dry_run,
        )
        for model in models
    ]


def write_requests(rows: Iterable[Mapping[str, Any]], *, output: TextIO, output_format: str) -> None:
    rows = list(rows)
    if output_format == "json":
        json.dump(rows, output, indent=2, sort_keys=True)
        output.write("\n")
        return
    if output_format == "jsonl":
        write_jsonl(rows, output)
        return
    raise TaskSystemError(f"unsupported output format: {output_format}")


def _parse_models(args: argparse.Namespace) -> list[str]:
    if args.all:
        return [target.model_id for target in MODEL_PROMOTION_TARGETS]
    if not args.model:
        raise TaskSystemError("provide --model or --all")
    return args.model


def model_promotion_review_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan unified manager-side model promotion review requests.")
    parser.add_argument("--model", action="append", help="Model id or layer id. Repeat for multiple models.")
    parser.add_argument("--all", action="store_true", help="Plan one request for every registered model layer.")
    parser.add_argument("--candidate-ref", required=True, help="Promotion candidate ref or artifact URI to review.")
    parser.add_argument("--evaluation-run-ref", action="append", default=[])
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--requested-by", default=DEFAULT_REQUESTED_BY)
    parser.add_argument("--priority", default="normal", choices=tuple(TASK_PRIORITY_RANKS))
    parser.add_argument("--deadline-at-utc")
    parser.add_argument("--format", choices=("jsonl", "json"), default="jsonl")
    parser.add_argument("--write", action="store_true", help="Persist request rows to trading_manager.manager_request.")
    parser.add_argument("--database-url")
    parser.add_argument("--locks-dir", type=Path, default=DEFAULT_LOCKS_DIR)
    args = parser.parse_args(argv)

    rows = build_model_promotion_review_requests(
        models=_parse_models(args),
        candidate_ref=args.candidate_ref,
        evaluation_run_refs=args.evaluation_run_ref,
        evidence_refs=args.evidence_ref,
        requested_by=args.requested_by,
        priority=args.priority,
        deadline_at_utc=args.deadline_at_utc,
        dry_run=not args.write,
    )
    if args.write:
        with ExitStack() as stack:
            for row in sorted(rows, key=lambda item: (str(item.get("model_id")), str(item.get("candidate_ref")))):
                stack.enter_context(
                    acquire_scheduler_lock(
                        promotion_lock_ref(str(row["model_id"]), str(row["candidate_ref"]), locks_dir=args.locks_dir)
                    )
                )
            persist_manager_requests([validate_manager_request(row) for row in rows], database_url=args.database_url)
    write_requests(rows, output=sys.stdout, output_format=args.format)
    return 0

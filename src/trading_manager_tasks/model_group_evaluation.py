"""Manager-owned model-group evaluation execution.

The dashboard can see when replay and M06 attribution are ready, but the
manager must still write concrete evaluation evidence before promotion can
inspect it. This module performs that side-effect-free evidence build over the
local replay dataset.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .model_group_replay import CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES, DEFAULT_REPLAY_CONTRACT_ID
from .model_training_workflow import base_stack_model_generation_splits_complete
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
MODEL_GROUP_EVALUATION_CHECKS = (
    "replay_metrics",
    "guardrail_settlement",
    "incumbent_comparison",
    "residual_event_governance",
    "residual_event_governance_event_focus_proposal",
)
PROMOTION_REVIEW_RECOMMENDATIONS = {"failed", "deferred", "eligible_for_shadow", "insufficient_evidence"}
PROMOTION_REVIEW_CONFIDENCE = {"low", "medium", "high"}
PROMOTION_REVIEW_STATUS = {"passed", "failed", "not_applicable", "insufficient_evidence"}
PROMOTION_COMPARISON_STATUS = {"better", "not_materially_better", "worse", "mixed", "insufficient_evidence"}
PROMOTION_UNCERTAINTY_STATUS = {"acceptable", "too_uncertain", "insufficient_evidence"}
PROMOTION_SHADOW_READINESS_STATUS = {"ready", "not_ready", "not_assessed", "insufficient_evidence"}
DEFAULT_PROMOTION_REVIEW_CODEX_MODEL = "gpt-5.5"
DEFAULT_PROMOTION_REVIEW_CODEX_TIMEOUT_SECONDS = 900
DEFAULT_PROMOTION_REVIEW_CODEX_WORKDIR = Path("/root/.openclaw/workspace")
DEFAULT_PROMOTION_REVIEW_CODEX_ADD_DIR = Path("/root/projects")
FEATURE_DIAGNOSTIC_SAMPLE_LIMIT = 160
FEATURE_DIAGNOSTIC_POINT_LIMIT = 80
DECISION_VARIABLE_SAMPLE_LIMIT = 12
INTENDED_OPERATING_THRESHOLD = 0.70
HIGH_SCORE_TAIL_RISK_THRESHOLD = 0.80
MIN_HIGH_SCORE_TAIL_LOSS_COUNT = 5
MIN_TAIL_RISK_FILLED_SAMPLE = 200
MAX_HIGH_SCORE_GOOD_BAD_SCORE_GAP = 0.02
SHORT_DTE_TAIL_LOSS_DAYS = 7
MAX_ACCEPTABLE_MAX_DRAWDOWN = -0.30
MAX_ACCEPTABLE_BAD_FILL_RATE = 0.55
MAX_ACCEPTABLE_MODEL_MISSED_WINNER_RATE = 0.45
RESIDUAL_EVENT_GOVERNANCE_CONTRACT_TYPES = {
    "post_replay_residual_event_governance_receipt",
    "model_06_residual_event_governance_event_attribution_receipt",
}
M06_COMPLETE_STATUSES = {"succeeded", "complete", "completed"}


def run_model_group_evaluation_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    selected_target_symbol: str | None = None,
    selected_start_month: str | None = None,
    selected_end_month: str | None = None,
    now_utc: datetime | None = None,
    force: bool = False,
    call_agent_review: bool = True,
    agent_reviewer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    codex_bin: str = "codex",
    codex_model: str | None = None,
    codex_timeout_seconds: int = DEFAULT_PROMOTION_REVIEW_CODEX_TIMEOUT_SECONDS,
) -> SchedulerDecision | None:
    """Run one model-group evaluation build when M06 evidence is complete."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    training_fold = _completed_training_fold(
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
        selected_start_month=selected_start_month,
        selected_end_month=selected_end_month,
    )
    if training_fold is None:
        return None
    replay_receipt_path, replay_receipt = _latest_replay_execution_receipt(
        dataset_root,
        training_fold=training_fold,
    )
    if replay_receipt_path is None or replay_receipt is None:
        return None
    decision_rows_path = Path(str(replay_receipt.get("decision_rows_ref") or ""))
    if not decision_rows_path.exists():
        return None
    attribution_receipt_path, attribution_receipt = _latest_attribution_receipt(
        dataset_root,
        decision_rows_ref=str(decision_rows_path),
    )
    if attribution_receipt_path is None or attribution_receipt is None:
        return None
    event_focus_proposals_path = Path(str(attribution_receipt.get("event_focus_proposals_ref") or ""))
    if not event_focus_proposals_path.exists():
        return None
    replay_scope_status = _replay_receipt_scope_status(replay_receipt=replay_receipt, training_fold=training_fold)
    if not replay_scope_status["compatible"]:
        now = (now_utc or datetime.now(UTC)).astimezone(UTC)
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_evaluation_replay_scope_mismatch",
            reason=str(replay_scope_status["reason"]),
            selected_work="model_group.evaluation",
            command=[
                python_executable,
                "scripts/tasks/run_model_group_evaluation.py",
                "--contract-id",
                contract_id,
                "--storage-root",
                str(storage_root),
            ],
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "replay_execution_receipt_ref": str(replay_receipt_path),
                "replay_scope_status": replay_scope_status,
            },
        )
    attribution_scope_status = _attribution_receipt_scope_status(
        replay_receipt=replay_receipt,
        attribution_receipt=attribution_receipt,
    )
    if not attribution_scope_status["compatible"]:
        now = (now_utc or datetime.now(UTC)).astimezone(UTC)
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_evaluation_attribution_scope_mismatch",
            reason=str(attribution_scope_status["reason"]),
            selected_work="model_group.evaluation",
            command=[
                python_executable,
                "scripts/tasks/run_model_group_evaluation.py",
                "--contract-id",
                contract_id,
                "--storage-root",
                str(storage_root),
            ],
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "replay_execution_receipt_ref": str(replay_receipt_path),
                "residual_event_governance_receipt_ref": str(attribution_receipt_path),
                "attribution_scope_status": attribution_scope_status,
            },
        )
    model_artifact_status = _replay_model_artifact_status(replay_receipt)
    if not model_artifact_status["compatible"]:
        now = (now_utc or datetime.now(UTC)).astimezone(UTC)
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_evaluation_candidate_model_not_trained",
            reason=str(model_artifact_status["reason"]),
            selected_work="model_group.evaluation",
            command=[
                python_executable,
                "scripts/tasks/run_model_group_evaluation.py",
                "--contract-id",
                contract_id,
                "--storage-root",
                str(storage_root),
            ],
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "replay_execution_receipt_ref": str(replay_receipt_path),
                "model_artifact_status": model_artifact_status,
                "required_next_step": "train a fold-specific supervised after-cost alpha model before replay promotion evaluation",
            },
        )
    if not force and _latest_promotion_review_artifacts(
        dataset_root,
        replay_result_ref=str(replay_receipt_path),
        residual_event_governance_receipt_ref=str(attribution_receipt_path),
        residual_event_governance_event_focus_proposals_ref=str(event_focus_proposals_path),
        fold_id=str(training_fold["fold_id"]),
        target_symbol=str(training_fold.get("target_symbol") or ""),
        candidate_model_ref=str(training_fold["candidate_model_ref"]),
        minimum_mtime=_state_mtime(training_fold),
    ) is not None:
        return None
    attribution_rows_path = Path(str(attribution_receipt.get("attribution_rows_ref") or ""))
    if not attribution_rows_path.exists():
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    candidate_fold_id = str(
        replay_receipt.get("candidate_fold_id")
        or attribution_receipt.get("candidate_fold_id")
        or training_fold.get("fold_id")
        or ""
    )
    candidate_training_target = str(
        replay_receipt.get("candidate_training_target")
        or attribution_receipt.get("candidate_training_target")
        or training_fold.get("target_symbol")
        or ""
    ).strip().upper()
    replay_execution_run_id = str(
        replay_receipt.get("replay_execution_run_id")
        or attribution_receipt.get("replay_execution_run_id")
        or ""
    )
    run_id = "model_group_evaluation_" + now.strftime("%Y%m%dT%H%M%SZ")
    settlement_root = dataset_root / "fold_settlement_runs" / run_id
    review_root = dataset_root / "promotion_review_runs" / run_id
    settlement_path = settlement_root / "fold_settlement_run.json"
    review_path = review_root / "promotion_evaluation_review.json"
    decision_path = review_root / "promotion_eligibility_decision.json"
    receipt_path = review_root / "model_group_evaluation_receipt.json"
    command = [
        python_executable,
        "scripts/tasks/run_model_group_evaluation.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]

    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_evaluation_ready",
            reason="model-group evaluation is ready to build replay metrics, guardrails, incumbent comparison, and M06 attribution checks",
            selected_work="model_group.evaluation",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "expected_checks": list(MODEL_GROUP_EVALUATION_CHECKS),
                "ready_checks": list(MODEL_GROUP_EVALUATION_CHECKS),
                "replay_execution_receipt_ref": str(replay_receipt_path),
                "residual_event_governance_receipt_ref": str(attribution_receipt_path),
                "residual_event_governance_event_focus_proposals_ref": str(event_focus_proposals_path),
            },
        )

    rows = tuple(_load_jsonl_objects(decision_rows_path))
    attribution_rows = tuple(_load_jsonl_objects(attribution_rows_path))
    check_summary = _evaluation_check_summary(
        rows=rows,
        attribution_rows=attribution_rows,
        attribution_receipt=attribution_receipt,
    )

    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_evaluation:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.evaluation.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        settlement_root.mkdir(parents=True, exist_ok=True)
        review_root.mkdir(parents=True, exist_ok=True)
        settlement = _build_settlement_run(
            fold_id=str(training_fold["fold_id"]),
            target_symbol=str(training_fold.get("target_symbol") or ""),
            candidate_model_ref=str(training_fold["candidate_model_ref"]),
            candidate_fold_id=candidate_fold_id,
            candidate_training_target=candidate_training_target,
            replay_execution_run_id=replay_execution_run_id,
            replay_contract_ref=f"trading-evaluation/replays/{contract_id}.json",
            replay_result_ref=str(replay_receipt_path),
            decision_rows=rows,
            created_at_utc=now.isoformat(),
        )
        review = _build_promotion_review(
            settlement=settlement,
            settlement_ref=str(settlement_path),
            benchmark_contract_ref=f"trading-evaluation/replays/{contract_id}.json",
            residual_event_governance_ref=str(attribution_receipt_path),
            created_at_utc=now.isoformat(),
            call_agent_review=call_agent_review,
            agent_reviewer=agent_reviewer,
            codex_bin=codex_bin,
            codex_model=codex_model,
            codex_timeout_seconds=codex_timeout_seconds,
        )
        eligibility = _build_promotion_eligibility_decision(
            settlement=settlement,
            review=review,
            settlement_ref=str(settlement_path),
            review_ref=str(review_path),
            replay_contract_ref=f"trading-evaluation/replays/{contract_id}.json",
            created_at_utc=now.isoformat(),
        )
        receipt = {
            "contract_type": "model_group_evaluation_receipt",
            "status": "succeeded",
            "stage_id": "model_group.evaluation",
            "run_id": run_id,
            "contract_id": contract_id,
            "fold_id": str(training_fold["fold_id"]),
            "target_symbol": str(training_fold.get("target_symbol") or ""),
            "candidate_model_ref": str(training_fold["candidate_model_ref"]),
            "candidate_fold_id": candidate_fold_id,
            "candidate_training_target": candidate_training_target,
            "replay_execution_run_id": replay_execution_run_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "evaluation_checks": check_summary["checks"],
            "ready_checks": check_summary["ready_checks"],
            "expected_check_count": len(MODEL_GROUP_EVALUATION_CHECKS),
            "ready_check_count": len(set(check_summary["ready_checks"]).intersection(MODEL_GROUP_EVALUATION_CHECKS)),
            "replay_execution_receipt_ref": str(replay_receipt_path),
            "residual_event_governance_receipt_ref": str(attribution_receipt_path),
            "residual_event_governance_event_focus_proposals_ref": str(event_focus_proposals_path),
            "fold_settlement_run_ref": str(settlement_path),
            "promotion_evaluation_review_ref": str(review_path),
            "promotion_eligibility_decision_ref": str(decision_path),
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
        }
        settlement_path.write_text(json.dumps(settlement, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        review_path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        decision_path.write_text(json.dumps(eligibility, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_evaluation_executed",
        reason="executed side-effect-free model-group evaluation and promotion-review evidence build",
        selected_work="model_group.evaluation",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "training_fold": training_fold,
            "model_group_evaluation_receipt": str(receipt_path),
            "fold_settlement_run_ref": str(settlement_path),
            "promotion_evaluation_review_ref": str(review_path),
            "promotion_eligibility_decision_ref": str(decision_path),
            "ready_checks": check_summary["ready_checks"],
            "candidate_model_ref": str(training_fold["candidate_model_ref"]),
            "candidate_fold_id": candidate_fold_id,
            "candidate_training_target": candidate_training_target,
            "target_symbol": str(training_fold.get("target_symbol") or ""),
            "replay_execution_run_id": replay_execution_run_id,
        },
    )


def _decision(
    *,
    now: datetime,
    decision_status: str,
    reason_code: str,
    reason: str,
    selected_work: str,
    command: list[str],
    execution_summary: dict[str, Any],
) -> SchedulerDecision:
    now_et = now.astimezone(NEW_YORK)
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now_et.isoformat(),
        decision_status=decision_status,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=command,
        next_internal_stage="model_group_evaluation",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(month=None, selected_work=selected_work, next_internal_stage="model_group_evaluation"),
    )


def _build_settlement_run(
    *,
    fold_id: str,
    target_symbol: str,
    candidate_model_ref: str,
    candidate_fold_id: str | None = None,
    candidate_training_target: str | None = None,
    replay_execution_run_id: str | None = None,
    replay_contract_ref: str,
    replay_result_ref: str,
    decision_rows: Sequence[Mapping[str, Any]],
    created_at_utc: str,
) -> dict[str, Any]:
    raw_decision_rows = list(decision_rows)
    decision_rows = [row for row in raw_decision_rows if str(row.get("entry_threshold_calibration_role") or "test") != "validation"]
    realized_returns = [_float(row, "net_return", "realized_return", "candidate_return") for row in decision_rows]
    baseline_returns = [_float(row, "baseline_return", "replay_return", "incumbent_return") for row in decision_rows]
    costs = [_float(row, "cost", "trading_cost", "cost_drag") for row in decision_rows]
    net_returns = [value - cost for value, cost in zip(realized_returns, costs, strict=True)]
    scored_rows = _scored_rows(decision_rows, net_returns, baseline_returns, costs)
    decision_variable_schema_diagnostics = _decision_variable_schema_diagnostics(
        decision_rows=decision_rows,
        net_returns=net_returns,
        baseline_returns=baseline_returns,
        costs=costs,
    )
    labels = [int(row["label"]) for row in scored_rows]
    scores = [float(row["score"]) for row in scored_rows]
    auroc = _auroc(labels, scores) if labels and scores else None
    filled_indices = [index for index, row in enumerate(decision_rows) if _is_filled_trade_row(row)]
    filled_net_returns = [net_returns[index] for index in filled_indices]
    net_total = sum(net_returns)
    baseline_total = sum(baseline_returns)
    feature_diagnostics = _feature_space_diagnostics(decision_rows)
    predictive_diagnostics = _predictive_diagnostics(scored_rows)
    calibration_diagnostics = _calibration_diagnostics(scored_rows)
    economic_diagnostics = _economic_diagnostics(net_returns=net_returns, realized_returns=realized_returns, costs=costs)
    data_integrity_diagnostics = _data_integrity_diagnostics(raw_decision_rows=raw_decision_rows, decision_rows=decision_rows)
    temporal_stability_diagnostics = _temporal_stability_diagnostics(scored_rows)
    scorecards = _model_group_scorecards(
        decision_rows=decision_rows,
        scored_rows=scored_rows,
        net_returns=net_returns,
        baseline_returns=baseline_returns,
        realized_returns=realized_returns,
        costs=costs,
        auroc=auroc,
        predictive_diagnostics=predictive_diagnostics,
        calibration_diagnostics=calibration_diagnostics,
        economic_diagnostics=economic_diagnostics,
    )
    high_score_tail_risk_diagnostics = _high_score_tail_risk_diagnostics(
        decision_rows=decision_rows,
        net_returns=net_returns,
    )
    disagreement_report = _evaluation_disagreement_report(
        auroc=auroc,
        scorecards=scorecards,
        net_total=net_total,
        baseline_total=baseline_total,
    )
    baseline_comparison_diagnostics = _baseline_comparison_diagnostics(
        labels=labels,
        scores=scores,
        net_total=net_total,
        baseline_total=baseline_total,
    )
    gate_failures: list[str] = []
    if len(decision_rows) < 20:
        gate_failures.append("decision_row_count_below_minimum")
    if data_integrity_diagnostics.get("leakage_check_status") != "passed":
        gate_failures.append("data_integrity_leakage_failed")
    if net_total <= baseline_total:
        gate_failures.append("excess_return_not_positive")
    max_drawdown = _max_drawdown(net_returns)
    if max_drawdown < MAX_ACCEPTABLE_MAX_DRAWDOWN:
        gate_failures.append("drawdown_too_severe")
    intended_band = scorecards.get("selection_quality", {}).get("intended_operating_threshold_band", {})
    if intended_band.get("selected_count") and (intended_band.get("return_per_selected") or 0.0) <= 0:
        gate_failures.append("intended_threshold_utility_not_positive")
    if (scorecards.get("selection_quality", {}).get("bad_fill_rate") or 0.0) > MAX_ACCEPTABLE_BAD_FILL_RATE:
        gate_failures.append("bad_fill_rate_too_high")
    if (scorecards.get("selection_quality", {}).get("model_missed_winner_rate") or 0.0) > MAX_ACCEPTABLE_MODEL_MISSED_WINNER_RATE:
        gate_failures.append("model_missed_winner_rate_too_high")
    gate_failures.extend(high_score_tail_risk_diagnostics["gate_failures"])
    settlement_id = f"settlement_{_stable_token(fold_id, candidate_model_ref, replay_contract_ref, replay_result_ref)}"
    metrics = {
        "contract_type": "fold_settlement_metric",
        "settlement_run_ref": settlement_id,
        "decision_row_count": len(decision_rows),
        "net_return_total": net_total,
        "baseline_return_total": baseline_total,
        "excess_return_total": net_total - baseline_total,
        "max_drawdown": _max_drawdown(net_returns),
        "turnover_proxy_count": len(filled_indices),
        "hit_rate": sum(1 for value in filled_net_returns if value > 0) / len(filled_net_returns) if filled_net_returns else 0.0,
        "payoff_ratio": _payoff_ratio(filled_net_returns),
        "auroc": auroc,
        "auroc_pair_count": len(labels),
        "pr_auc": predictive_diagnostics.get("pr_auc"),
        "base_rate": predictive_diagnostics.get("base_rate"),
        "brier_score": sum((score - label) ** 2 for label, score in zip(labels, scores, strict=True)) / len(labels) if labels else None,
        "ece": calibration_diagnostics.get("ece"),
        "mce": calibration_diagnostics.get("mce"),
        "brier_reliability": calibration_diagnostics.get("brier_decomposition", {}).get("reliability"),
        "brier_resolution": calibration_diagnostics.get("brier_decomposition", {}).get("resolution"),
        "brier_uncertainty": calibration_diagnostics.get("brier_decomposition", {}).get("uncertainty"),
        "profit_factor": economic_diagnostics.get("profit_factor"),
        "return_per_decision": economic_diagnostics.get("return_per_decision"),
        "tail_loss_p05": economic_diagnostics.get("tail_loss_p05"),
        "cost_sensitivity_2x": economic_diagnostics.get("cost_sensitivity", {}).get("2.0x"),
        "worst_month_return": temporal_stability_diagnostics.get("worst_month_return"),
        "month_slice_count": temporal_stability_diagnostics.get("month_slice_count"),
        "data_integrity_status": data_integrity_diagnostics.get("status"),
        "leakage_check_status": data_integrity_diagnostics.get("leakage_check_status"),
        "feature_column_count": feature_diagnostics["feature_column_count"],
        "feature_row_count": feature_diagnostics["feature_row_count"],
        "feature_sample_count": feature_diagnostics["sample_count"],
        "pca_available": feature_diagnostics["pca"]["available"],
        "pca_variance_pc1": feature_diagnostics["pca"]["explained_variance_ratio"][0] if feature_diagnostics["pca"]["available"] else None,
        "pca_variance_pc2": feature_diagnostics["pca"]["explained_variance_ratio"][1] if feature_diagnostics["pca"]["available"] else None,
        "pca_variance_top2": sum(feature_diagnostics["pca"]["explained_variance_ratio"]) if feature_diagnostics["pca"]["available"] else None,
        "pcoa_available": feature_diagnostics["pcoa"]["available"],
        "pcoa_variance_pc1": feature_diagnostics["pcoa"]["explained_variance_ratio"][0] if feature_diagnostics["pcoa"]["available"] else None,
        "pcoa_variance_pc2": feature_diagnostics["pcoa"]["explained_variance_ratio"][1] if feature_diagnostics["pcoa"]["available"] else None,
        "pcoa_variance_top2": sum(feature_diagnostics["pcoa"]["explained_variance_ratio"]) if feature_diagnostics["pcoa"]["available"] else None,
        "silhouette_outcome_label": feature_diagnostics["silhouette"].get("outcome_label"),
        "silhouette_decision_action": feature_diagnostics["silhouette"].get("decision_action"),
        "decision_variable_schema_status": decision_variable_schema_diagnostics.get("status"),
        "decision_intended_side_unknown_count": decision_variable_schema_diagnostics.get("unknown_counts", {}).get("decision_intended_side"),
        "decision_agency_unknown_count": decision_variable_schema_diagnostics.get("unknown_counts", {}).get("decision_agency"),
        "predictive_diagnostics": predictive_diagnostics,
        "calibration_diagnostics": calibration_diagnostics,
        "economic_diagnostics": economic_diagnostics,
        "data_integrity_diagnostics": data_integrity_diagnostics,
        "decision_variable_schema_diagnostics": decision_variable_schema_diagnostics,
        "scorecards": scorecards,
        "evaluation_disagreement_report": disagreement_report,
        "temporal_stability_diagnostics": temporal_stability_diagnostics,
        "baseline_comparison_diagnostics": baseline_comparison_diagnostics,
        "high_score_tail_risk_diagnostics": high_score_tail_risk_diagnostics,
        "uncertainty_diagnostics": {
            "available": False,
            "reason": "block bootstrap confidence intervals require multiple completed comparable folds",
        },
        "feature_diagnostics": feature_diagnostics,
        "diagnostic_availability": _diagnostic_availability(
            feature_diagnostics=feature_diagnostics,
            scorecards=scorecards,
            decision_variable_schema_diagnostics=decision_variable_schema_diagnostics,
        ),
    }
    return {
        "contract_type": "fold_settlement_run",
        "fold_settlement_run_id": settlement_id,
        "fold_id": fold_id,
        "target_symbol": target_symbol,
        "candidate_model_ref": candidate_model_ref,
        "candidate_fold_id": candidate_fold_id or fold_id,
        "candidate_training_target": (candidate_training_target or target_symbol).strip().upper(),
        "replay_execution_run_id": replay_execution_run_id or "",
        "replay_contract_ref": replay_contract_ref,
        "replay_result_ref": replay_result_ref,
        "baseline_ref": None,
        "created_at_utc": created_at_utc,
        "decision_status": "passed" if not gate_failures else "review_required",
        "gate_failures": gate_failures,
        "metric_refs": [f"{settlement_id}:metrics"],
        "metrics": metrics,
        "agent_review_required": True,
        "agent_review_scope": "promotion-evaluation-review",
        "fold_stack_evidence_ref": candidate_model_ref,
        "fold_stack_status": "complete_m01_m06",
        "model_activation_performed": False,
        "active_model_config_written": False,
        "broker_execution_performed": False,
        "account_mutation_performed": False,
    }


def _scored_rows(
    decision_rows: Sequence[Mapping[str, Any]],
    net_returns: Sequence[float],
    baseline_returns: Sequence[float],
    costs: Sequence[float],
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row, net_return, baseline_return, cost in zip(decision_rows, net_returns, baseline_returns, costs, strict=True):
        label = _label(row)
        score = _score(row)
        if label is None or score is None:
            continue
        scored.append(
            {
                "label": int(label),
                "score": float(score),
                "net_return": float(net_return),
                "baseline_return": float(baseline_return),
                "cost": float(cost),
                "timestamp": str(row.get("timestamp") or row.get("decision_timestamp") or ""),
                "decision_action": str(row.get("decision_action") or row.get("action") or ""),
            }
        )
    return scored


def _normalized_decision_variable_rows(
    *,
    decision_rows: Sequence[Mapping[str, Any]],
    net_returns: Sequence[float],
    baseline_returns: Sequence[float],
    costs: Sequence[float],
) -> list[dict[str, Any]]:
    return [
        _normalized_decision_variable_row(row, net_return=net_return, baseline_return=baseline_return, cost=cost)
        for row, net_return, baseline_return, cost in zip(decision_rows, net_returns, baseline_returns, costs, strict=True)
    ]


def _decision_variable_schema_diagnostics(
    *,
    decision_rows: Sequence[Mapping[str, Any]],
    net_returns: Sequence[float],
    baseline_returns: Sequence[float],
    costs: Sequence[float],
) -> dict[str, Any]:
    normalized_rows = _normalized_decision_variable_rows(
        decision_rows=decision_rows,
        net_returns=net_returns,
        baseline_returns=baseline_returns,
        costs=costs,
    )
    field_names = (
        "decision_intended_side",
        "decision_intended_action",
        "decision_disposition",
        "decision_agency",
        "decision_confidence_band",
        "replay_fill_status",
        "replay_execution_mode",
        "path_conditioning_policy",
        "candidate_set_scope",
        "miss_attribution_layer",
        "eval_outcome_label",
        "eval_economic_class",
        "eval_action_class",
    )
    unknown_counts = {
        name: sum(1 for row in normalized_rows if row.get(name) in (None, "", "unknown"))
        for name in field_names
    }
    coverage = {
        name: {
            "known_count": len(normalized_rows) - unknown_counts[name],
            "unknown_count": unknown_counts[name],
            "values": _value_counts(row.get(name) for row in normalized_rows),
        }
        for name in field_names
    }
    feature_leakage_columns = _feature_namespace_leakage_columns(decision_rows)
    issues: list[dict[str, Any]] = []
    for name in ("decision_intended_action", "decision_disposition", "decision_agency"):
        if unknown_counts[name]:
            issues.append({"issue_code": f"{name}_unknown", "row_count": unknown_counts[name]})
    if unknown_counts["decision_intended_side"]:
        issues.append(
            {
                "issue_code": "decision_intended_side_unknown",
                "row_count": unknown_counts["decision_intended_side"],
                "severity": "notice",
            }
        )
    if feature_leakage_columns:
        issues.append(
            {
                "issue_code": "feature_namespace_contains_replay_or_eval_fields",
                "columns": feature_leakage_columns,
                "severity": "warning",
            }
        )
    status = "warning" if any(issue.get("severity") == "warning" for issue in issues) else "passed"
    return {
        "contract_type": "decision_variable_schema_diagnostic",
        "schema_namespaces": {
            "decision": "point-in-time decision intent, disposition, agency, score, and slice variables",
            "replay": "post-replay fill and economic observations; forbidden as training features",
            "eval": "post-outcome evaluation labels/classes; forbidden as training features",
        },
        "row_count": len(normalized_rows),
        "status": status,
        "label_definition": {
            "eval_outcome_label": "legacy outcome_label/label/realized_label when present, otherwise replay_cost_adjusted_return > 0",
            "eval_economic_class": "accepted decisions use replay_excess_return; unfilled decisions use replay_opportunity_excess_return",
            "eval_action_class": "based on decision_disposition, decision_agency, path-conditioned miss scope, and accepted-or-opportunity excess return",
        },
        "feature_namespace_leakage_status": "warning" if feature_leakage_columns else "passed",
        "feature_namespace_leakage_columns": feature_leakage_columns,
        "unknown_counts": unknown_counts,
        "coverage": coverage,
        "issues": issues,
        "normalized_row_samples": normalized_rows[:DECISION_VARIABLE_SAMPLE_LIMIT],
    }


def _model_group_scorecards(
    *,
    decision_rows: Sequence[Mapping[str, Any]],
    scored_rows: Sequence[Mapping[str, Any]],
    net_returns: Sequence[float],
    baseline_returns: Sequence[float],
    realized_returns: Sequence[float],
    costs: Sequence[float],
    auroc: float | None,
    predictive_diagnostics: Mapping[str, Any],
    calibration_diagnostics: Mapping[str, Any],
    economic_diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    normalized_rows = _normalized_decision_variable_rows(
        decision_rows=decision_rows,
        net_returns=net_returns,
        baseline_returns=baseline_returns,
        costs=costs,
    )
    action_counts = _value_counts(row.get("eval_action_class") for row in normalized_rows)
    accepted_rows = [row for row in normalized_rows if row.get("decision_disposition") == "accepted"]
    taken_good = action_counts.get("taken_good", 0)
    taken_bad = action_counts.get("taken_bad", 0)
    model_missed_good = sum(
        1
        for row in normalized_rows
        if row.get("eval_action_class") == "missed_good" and row.get("decision_agency") in {"model", "unknown"}
    )
    blocked_good_by_agency = _value_counts(
        row.get("decision_agency")
        for row in normalized_rows
        if row.get("eval_action_class") in {"missed_good", "blocked_good"} and row.get("decision_agency") not in {"model", "unknown"}
    )
    positive_opportunities = taken_good + model_missed_good
    threshold_curve = predictive_diagnostics.get("threshold_return_curve")
    threshold_points = threshold_curve if isinstance(threshold_curve, list) else []
    intended_band = _threshold_band_summary(threshold_points, INTENDED_OPERATING_THRESHOLD)
    return {
        "contract_type": "model_group_evaluation_scorecards",
        "ranking_calibration": {
            "auroc": auroc,
            "pr_auc": predictive_diagnostics.get("pr_auc"),
            "base_rate": predictive_diagnostics.get("base_rate"),
            "brier_score": _brier_score([int(row["label"]) for row in scored_rows], [float(row["score"]) for row in scored_rows]),
            "ece": calibration_diagnostics.get("ece"),
            "mce": calibration_diagnostics.get("mce"),
            "score_decile_return": _score_decile_return(scored_rows),
            "ranking_diagnostic_note": "AUROC is ranking evidence only; promotion gating uses economic and selection utility.",
        },
        "selection_quality": {
            "accepted_count": len(accepted_rows),
            "taken_good_count": taken_good,
            "taken_bad_count": taken_bad,
            "model_missed_good_count": model_missed_good,
            "blocked_good_by_agency": blocked_good_by_agency,
            "good_trade_rate": _round_metric(taken_good / len(accepted_rows)) if accepted_rows else None,
            "bad_fill_rate": _round_metric(taken_bad / len(accepted_rows)) if accepted_rows else None,
            "model_missed_winner_rate": _round_metric(model_missed_good / positive_opportunities) if positive_opportunities else None,
            "profitable_opportunity_recall": _round_metric(taken_good / positive_opportunities) if positive_opportunities else None,
            "precision_among_filled_trades": _round_metric(taken_good / (taken_good + taken_bad)) if taken_good + taken_bad else None,
            "eval_action_class_counts": action_counts,
            "intended_operating_threshold_band": intended_band,
        },
        "economic_quality": {
            "net_return_total": _round_metric(sum(net_returns)),
            "baseline_return_total": _round_metric(sum(baseline_returns)),
            "excess_return_total": _round_metric(sum(net_returns) - sum(baseline_returns)),
            "return_per_decision": economic_diagnostics.get("return_per_decision"),
            "return_per_filled_trade": _return_per_filled_trade(normalized_rows),
            "profit_factor": economic_diagnostics.get("profit_factor"),
            "max_drawdown": _round_metric(_max_drawdown(net_returns)),
            "tail_loss_p05": economic_diagnostics.get("tail_loss_p05"),
            "cost_sensitivity": economic_diagnostics.get("cost_sensitivity"),
            "cost_adjusted_return_total": _round_metric(sum(realized - cost for realized, cost in zip(realized_returns, costs, strict=True))),
        },
        "slices": {
            "decision_intended_side": _slice_scorecard(normalized_rows, "decision_intended_side"),
            "decision_intended_action": _slice_scorecard(normalized_rows, "decision_intended_action"),
            "decision_disposition": _slice_scorecard(normalized_rows, "decision_disposition"),
            "decision_confidence_band": _slice_scorecard(normalized_rows, "decision_confidence_band"),
            "decision_agency": _slice_scorecard(normalized_rows, "decision_agency"),
        },
    }


def _diagnostic_availability(
    *,
    feature_diagnostics: Mapping[str, Any],
    scorecards: Mapping[str, Any],
    decision_variable_schema_diagnostics: Mapping[str, Any],
) -> dict[str, Any]:
    pca = feature_diagnostics.get("pca") if isinstance(feature_diagnostics.get("pca"), Mapping) else {}
    pcoa = feature_diagnostics.get("pcoa") if isinstance(feature_diagnostics.get("pcoa"), Mapping) else {}
    silhouette = feature_diagnostics.get("silhouette") if isinstance(feature_diagnostics.get("silhouette"), Mapping) else {}
    slices = scorecards.get("slices") if isinstance(scorecards.get("slices"), Mapping) else {}
    feature_available = bool(pca.get("available") or pcoa.get("available"))
    silhouette_available = bool(any(value is not None for value in silhouette.values()))
    slice_available = bool(any(isinstance(value, list) and value for value in slices.values()))
    schema_status = str(decision_variable_schema_diagnostics.get("status") or "not_reported")
    return {
        "feature_space": {
            "status": "available" if feature_available else "unavailable",
            "reason_code": "feature_space_published" if feature_available else "missing_feature_space_diagnostics",
        },
        "silhouette": {
            "status": "available" if silhouette_available else "unavailable",
            "reason_code": "silhouette_published" if silhouette_available else "missing_silhouette_diagnostics",
        },
        "slice_distribution": {
            "status": "available" if slice_available else "unavailable",
            "reason_code": "scorecard_slices_published" if slice_available else "missing_slice_scorecards",
        },
        "decision_variable_schema": {
            "status": "available" if schema_status in {"passed", "warning"} else "unavailable",
            "reason_code": f"decision_variable_schema_{schema_status}",
        },
    }


def _threshold_band_summary(threshold_points: Sequence[Any], threshold: float) -> dict[str, Any]:
    usable = [point for point in threshold_points if isinstance(point, Mapping)]
    if not usable:
        return {"threshold": threshold, "selected_count": 0, "return_per_selected": None, "net_return_total": 0.0}
    best = min(usable, key=lambda point: abs(_float(point, "threshold", default=threshold) - threshold))
    return {
        "threshold": _float(best, "threshold", default=threshold),
        "selected_count": int(_float(best, "selected_count", default=0.0)),
        "return_per_selected": best.get("return_per_selected"),
        "net_return_total": best.get("net_return_total"),
        "hit_rate": best.get("hit_rate"),
    }


def _return_per_filled_trade(normalized_rows: Sequence[Mapping[str, Any]]) -> float | None:
    filled = [row for row in normalized_rows if row.get("decision_disposition") == "accepted"]
    if not filled:
        return None
    return _round_metric(sum(_float(row, "replay_cost_adjusted_return") for row in filled) / len(filled))


def _score_decile_return(scored_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not scored_rows:
        return []
    ordered = sorted(scored_rows, key=lambda row: float(row["score"]), reverse=True)
    deciles: list[dict[str, Any]] = []
    for index in range(10):
        start = math.floor(index * len(ordered) / 10)
        end = math.floor((index + 1) * len(ordered) / 10)
        bucket = ordered[start:end]
        if not bucket:
            continue
        returns = [float(row["net_return"]) for row in bucket]
        excess = [float(row["net_return"]) - float(row["baseline_return"]) for row in bucket]
        deciles.append(
            {
                "decile": index + 1,
                "score_min": _round_metric(min(float(row["score"]) for row in bucket)),
                "score_max": _round_metric(max(float(row["score"]) for row in bucket)),
                "row_count": len(bucket),
                "net_return_total": _round_metric(sum(returns)),
                "excess_return_total": _round_metric(sum(excess)),
                "return_per_decision": _round_metric(sum(returns) / len(returns)),
                "positive_label_rate": _round_metric(sum(int(row["label"]) for row in bucket) / len(bucket)),
            }
        )
    return deciles


def _slice_scorecard(normalized_rows: Sequence[Mapping[str, Any]], field: str) -> list[dict[str, Any]]:
    by_value: dict[str, list[Mapping[str, Any]]] = {}
    for row in normalized_rows:
        key = str(row.get(field) or "unknown")
        by_value.setdefault(key, []).append(row)
    slices: list[dict[str, Any]] = []
    for value, rows in sorted(by_value.items()):
        returns = [_float(row, "replay_cost_adjusted_return") for row in rows]
        excess = [_float(row, "replay_excess_return") for row in rows]
        action_counts = _value_counts(row.get("eval_action_class") for row in rows)
        slices.append(
            {
                "value": value,
                "row_count": len(rows),
                "accepted_count": sum(1 for row in rows if row.get("decision_disposition") == "accepted"),
                "net_return_total": _round_metric(sum(returns)),
                "excess_return_total": _round_metric(sum(excess)),
                "return_per_decision": _round_metric(sum(returns) / len(rows)) if rows else None,
                "taken_good_count": action_counts.get("taken_good", 0),
                "taken_bad_count": action_counts.get("taken_bad", 0),
                "missed_good_count": action_counts.get("missed_good", 0),
                "blocked_good_count": action_counts.get("blocked_good", 0),
            }
        )
    return slices


def _evaluation_disagreement_report(
    *,
    auroc: float | None,
    scorecards: Mapping[str, Any],
    net_total: float,
    baseline_total: float,
) -> dict[str, Any]:
    ranking = scorecards.get("ranking_calibration") if isinstance(scorecards.get("ranking_calibration"), Mapping) else {}
    selection = scorecards.get("selection_quality") if isinstance(scorecards.get("selection_quality"), Mapping) else {}
    economic = scorecards.get("economic_quality") if isinstance(scorecards.get("economic_quality"), Mapping) else {}
    disagreements: list[dict[str, Any]] = []
    excess_total = net_total - baseline_total
    intended_band = selection.get("intended_operating_threshold_band") if isinstance(selection.get("intended_operating_threshold_band"), Mapping) else {}
    intended_utility = intended_band.get("return_per_selected")
    if auroc is not None and auroc < 0.53 and (excess_total > 0 or (isinstance(intended_utility, (int, float)) and intended_utility > 0)):
        disagreements.append({"type": "auroc_below_old_gate_but_positive_utility", "severity": "notice", "auroc": auroc, "excess_return_total": _round_metric(excess_total), "intended_return_per_selected": intended_utility})
    if auroc is not None and auroc >= 0.53 and excess_total <= 0:
        disagreements.append({"type": "auroc_passed_old_gate_but_negative_excess", "severity": "warning", "auroc": auroc, "excess_return_total": _round_metric(excess_total)})
    if net_total > 0 and excess_total <= 0:
        disagreements.append({"type": "positive_net_return_under_baseline", "severity": "warning", "net_return_total": _round_metric(net_total), "baseline_return_total": _round_metric(baseline_total)})
    if selection.get("taken_bad_count"):
        disagreements.append({"type": "filled_bad_or_under_baseline", "severity": "notice", "count": selection.get("taken_bad_count"), "bad_fill_rate": selection.get("bad_fill_rate")})
    if selection.get("model_missed_good_count"):
        disagreements.append({"type": "model_missed_winner", "severity": "warning", "count": selection.get("model_missed_good_count"), "model_missed_winner_rate": selection.get("model_missed_winner_rate")})
    blocked_good = selection.get("blocked_good_by_agency")
    if isinstance(blocked_good, Mapping) and blocked_good:
        disagreements.append({"type": "non_model_blocked_winner", "severity": "info", "blocked_good_by_agency": dict(blocked_good)})
    return {
        "contract_type": "model_group_evaluation_disagreement_report",
        "old_auroc_gate": 0.53,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "score_decile_return": ranking.get("score_decile_return"),
        "long_short_action_slices": {
            "decision_intended_side": (scorecards.get("slices") or {}).get("decision_intended_side") if isinstance(scorecards.get("slices"), Mapping) else [],
            "decision_intended_action": (scorecards.get("slices") or {}).get("decision_intended_action") if isinstance(scorecards.get("slices"), Mapping) else [],
        },
        "promotion_gate_basis": {
            "auroc_is_hard_gate": False,
            "required_positive_excess_return": True,
            "required_positive_intended_threshold_utility": True,
            "bad_fill_rate_maximum": MAX_ACCEPTABLE_BAD_FILL_RATE,
            "model_missed_winner_rate_maximum": MAX_ACCEPTABLE_MODEL_MISSED_WINNER_RATE,
        },
        "economic_summary": economic,
    }


def _normalized_decision_variable_row(
    row: Mapping[str, Any],
    *,
    net_return: float,
    baseline_return: float,
    cost: float,
) -> dict[str, Any]:
    intended_side = _decision_intended_side(row)
    intended_action = _decision_intended_action(row)
    disposition = _decision_disposition(row, intended_action=intended_action)
    agency, agency_detail = _decision_agency(row, disposition=disposition, intended_action=intended_action)
    replay_fill_status = _replay_fill_status(row)
    replay_execution_mode = _replay_execution_mode(row)
    path_conditioning_policy = _path_conditioning_policy(row)
    candidate_set_scope = _candidate_set_scope(row)
    miss_attribution_layer = _miss_attribution_layer(
        row,
        disposition=disposition,
        instrument_scope=_decision_instrument_scope(row),
    )
    miss_review_scope = _miss_review_scope(
        disposition=disposition,
        path_conditioning_policy=path_conditioning_policy,
        candidate_set_scope=candidate_set_scope,
        miss_attribution_layer=miss_attribution_layer,
    )
    eval_outcome_label = _label(row)
    replay_excess_return = net_return - baseline_return
    is_unfilled_decision = disposition in {"skipped", "rejected", "deferred", "blocked"}
    opportunity_return = (
        _opportunity_return(row, fallback_net_return=net_return, cost=cost, intended_side=intended_side)
        if is_unfilled_decision
        else None
    )
    opportunity_excess_return = opportunity_return - baseline_return if opportunity_return is not None else None
    classification_net_return = opportunity_return if opportunity_return is not None else net_return
    classification_excess_return = opportunity_excess_return if opportunity_excess_return is not None else replay_excess_return
    return {
        "decision_id": str(row.get("decision_id") or row.get("replay_decision_id") or ""),
        "decision_asof_ts": str(row.get("asof_ts") or row.get("timestamp") or row.get("decision_timestamp") or ""),
        "decision_instrument_scope": _decision_instrument_scope(row),
        "decision_intended_side": intended_side,
        "decision_intended_action": intended_action,
        "decision_expression_type": _decision_expression_type(row),
        "decision_disposition": disposition,
        "decision_agency": agency,
        "decision_agency_detail": agency_detail,
        "decision_score": _score(row),
        "decision_confidence_band": _confidence_band(_score(row)),
        "replay_fill_status": replay_fill_status,
        "replay_execution_mode": replay_execution_mode,
        "path_conditioning_policy": path_conditioning_policy,
        "path_scope": _path_scope(row),
        "candidate_set_scope": candidate_set_scope,
        "miss_attribution_layer": miss_attribution_layer,
        "miss_review_scope": miss_review_scope,
        "replay_realized_return": _round_metric(net_return + cost),
        "replay_baseline_return": _round_metric(baseline_return),
        "replay_excess_return": _round_metric(replay_excess_return),
        "replay_cost": _round_metric(cost),
        "replay_cost_adjusted_return": _round_metric(net_return),
        "replay_opportunity_return": _round_metric(opportunity_return) if opportunity_return is not None else None,
        "replay_opportunity_excess_return": _round_metric(opportunity_excess_return) if opportunity_excess_return is not None else None,
        "eval_outcome_label": eval_outcome_label,
        "eval_economic_class": _eval_economic_class(net_return=classification_net_return, excess_return=classification_excess_return),
        "eval_action_class": _eval_action_class(
            disposition=disposition,
            agency=agency,
            excess_return=classification_excess_return,
            miss_review_scope=miss_review_scope,
        ),
    }


def _opportunity_return(
    row: Mapping[str, Any],
    *,
    fallback_net_return: float,
    cost: float,
    intended_side: str,
) -> float:
    explicit = _first_float(
        row,
        "opportunity_return",
        "candidate_opportunity_return",
        "missed_opportunity_return",
        "replay_opportunity_return",
    )
    if explicit is not None:
        return explicit

    option_entry = _first_float(row, "option_entry_price", "selected_option_entry_price")
    option_exit = _first_float(row, "option_exit_price", "selected_option_exit_price")
    if option_entry is not None and option_exit is not None and option_entry > 0:
        return (option_exit - option_entry) / option_entry - cost

    underlying_entry = _first_float(row, "bar_close", "underlying_entry_price", "entry_underlying_price")
    underlying_exit = _first_float(row, "next_bar_close", "underlying_exit_price", "exit_underlying_price")
    if underlying_entry is not None and underlying_exit is not None and underlying_entry > 0:
        gross_return = (underlying_exit - underlying_entry) / underlying_entry
        if intended_side == "short":
            gross_return = -gross_return
        return gross_return - cost

    return fallback_net_return


def _decision_instrument_scope(row: Mapping[str, Any]) -> str:
    expression_type = _decision_expression_type(row)
    if expression_type in {"long_call", "long_put"}:
        return "option"
    if expression_type in {"underlying_only", "no_option_expression"}:
        return "underlying"
    instrument_ref = str(row.get("instrument_ref") or row.get("target_ref") or "").lower()
    if "option" in instrument_ref or "_c" in instrument_ref or "_p" in instrument_ref:
        return "option"
    return "unknown"


def _path_conditioning_policy(row: Mapping[str, Any]) -> str:
    explicit = _first_text(row, "path_conditioning_policy", "replay_path_conditioning_policy")
    if explicit:
        return explicit
    return "upstream_selected_path_only"


def _path_scope(row: Mapping[str, Any]) -> str:
    explicit = _first_text(row, "path_scope", "replay_path_scope")
    if explicit:
        return explicit
    target = _first_text(row, "target_ref", "target_symbol", "symbol", "instrument_ref")
    if target:
        return f"selected_target:{target.split('-')[0].upper()}"
    return "selected_path:unknown"


def _candidate_set_scope(row: Mapping[str, Any]) -> str:
    explicit = _first_text(row, "candidate_set_scope", "replay_candidate_set_scope")
    if explicit:
        return explicit
    if _first_text(row, "selected_option_contract_ref", "selected_contract_ref"):
        return "selected_target_selected_option_contract_path"
    expression_type = _decision_expression_type(row)
    if expression_type in {"long_call", "long_put"}:
        return "selected_target_option_expression_candidates"
    instrument_scope = _decision_instrument_scope(row)
    if instrument_scope == "underlying":
        return "selected_target_underlying_decision"
    return "selected_path_current_decision_set"


def _miss_attribution_layer(row: Mapping[str, Any], *, disposition: str, instrument_scope: str) -> str:
    explicit = _first_text(row, "miss_attribution_layer", "replay_miss_attribution_layer")
    if explicit:
        return explicit
    if disposition == "accepted":
        return "taken_decision"
    if _first_text(row, "selected_option_contract_ref", "selected_contract_ref") or instrument_scope == "option":
        return "model_05_option_expression"
    if instrument_scope == "underlying":
        return "model_04_unified_decision"
    return "current_decision_layer"


def _miss_review_scope(
    *,
    disposition: str,
    path_conditioning_policy: str,
    candidate_set_scope: str,
    miss_attribution_layer: str,
) -> str:
    if disposition == "accepted":
        return "taken_decision"
    if path_conditioning_policy in {"global_hindsight_oracle", "unconditioned_global_universe", "best_path_hindsight"}:
        return "not_path_conditioned"
    if candidate_set_scope.startswith("global_") or miss_attribution_layer in {"global_hindsight_oracle", "best_path_hindsight"}:
        return "not_path_conditioned"
    return "path_conditioned_current_scope"


def _decision_expression_type(row: Mapping[str, Any]) -> str:
    value = _first_text(row, "decision_expression_type", "5_resolved_expression_type", "resolved_expression_type", "expression_type")
    if value in {"long_call", "long_put", "underlying_only_expression", "underlying_only", "no_option_expression"}:
        return "underlying_only" if value == "underlying_only_expression" else value
    return "unknown" if not value else "other"


def _decision_intended_side(row: Mapping[str, Any]) -> str:
    explicit = _first_text(
        row,
        "decision_intended_side",
        "intended_side",
        "resolved_action_side",
        "position_side",
        "action_side",
    )
    normalized = _normalize_side(explicit)
    if normalized != "unknown":
        return normalized
    action_type = _first_text(
        row,
        "4_resolved_underlying_action_type",
        "resolved_underlying_action_type",
        "planned_underlying_action_type",
        "decision_intended_action",
        "decision_action",
        "action",
    )
    if action_type in {"open_long", "increase_long", "reduce_long", "close_long"}:
        return "long"
    if action_type in {"open_short", "increase_short", "reduce_short", "cover_short", "bearish_underlying_path_but_no_short_allowed"}:
        return "short"
    if action_type in {"no_trade", "skip", "hold", "watch", "reject_entry_thesis", "defer_entry_thesis", "simulated_rejected"}:
        return "flat"
    expression_type = _decision_expression_type(row)
    if expression_type == "long_call":
        return "long"
    if expression_type == "long_put":
        return "short"
    if expression_type == "no_option_expression":
        return "flat"
    return "unknown"


def _decision_intended_action(row: Mapping[str, Any]) -> str:
    value = _first_text(
        row,
        "decision_intended_action",
        "4_resolved_underlying_action_type",
        "resolved_underlying_action_type",
        "planned_underlying_action_type",
        "decision_action",
        "action",
    )
    if value in {"open", "open_long", "open_short", "trade", "continue_to_option_review"}:
        return "open"
    if value in {"increase", "increase_long", "increase_short", "add"}:
        return "increase"
    if value in {"reduce", "reduce_long", "reduce_short"}:
        return "reduce"
    if value in {"close", "close_long", "cover_short", "stop", "sell"}:
        return "close"
    if value in {"maintain", "hold"}:
        return "maintain"
    if value in {"no_trade", "skip", "reject_entry_thesis", "bearish_underlying_path_but_no_short_allowed"}:
        return "no_trade"
    if value in {"watch", "watch_only", "monitor_only"}:
        return "watch"
    return "unknown"


def _decision_disposition(row: Mapping[str, Any], *, intended_action: str) -> str:
    explicit = _first_text(row, "decision_disposition", "disposition")
    if explicit in {"accepted", "skipped", "rejected", "deferred", "blocked"}:
        return explicit
    status = _first_text(row, "decision_status", "status")
    fill_status = _first_text(row, "fill_status", "replay_fill_status")
    if status in {"rejected", "rejected_entry_thesis"}:
        return "rejected"
    if fill_status in {"not_filled", "simulated_rejected"}:
        return "skipped"
    if status in {"accepted", "approved", "filled", "executed"} or fill_status in {"filled", "simulated_filled"}:
        return "accepted"
    if status in {"suitable", "continue_to_expression_review"}:
        return "deferred"
    if status == "deferred":
        return "deferred"
    if status == "blocked" or status.startswith("blocked_"):
        return "blocked"
    if intended_action in {"no_trade", "watch", "maintain"}:
        return "skipped"
    return "unknown"


def _decision_agency(row: Mapping[str, Any], *, disposition: str, intended_action: str) -> tuple[str, str | None]:
    explicit = _first_text(row, "decision_agency", "agency")
    if explicit in {"model", "risk", "execution", "capital", "data", "mandate", "operator"}:
        return explicit, _first_text(row, "decision_agency_detail", "agency_detail") or None
    reason_codes = _reason_codes(row)
    joined = " ".join(reason_codes)
    if any(token in joined for token in ("buying_power", "capital", "cash")):
        return "capital", reason_codes[0] if reason_codes else None
    if any(token in joined for token in ("risk", "exposure", "concentration", "event_failure", "hard_block", "halt")):
        return "risk", reason_codes[0] if reason_codes else None
    if any(token in joined for token in ("broker", "order", "fill", "execution")):
        return "execution", reason_codes[0] if reason_codes else None
    if any(token in joined for token in ("missing", "data", "provider")):
        return "data", reason_codes[0] if reason_codes else None
    if any(token in joined for token in ("mandate", "not_allowed", "no_short", "short_borrow")):
        return "mandate", reason_codes[0] if reason_codes else None
    if disposition in {"accepted", "skipped", "rejected", "deferred"} or intended_action in {"no_trade", "watch"}:
        return "model", None
    return "unknown", None


def _replay_fill_status(row: Mapping[str, Any]) -> str:
    value = _first_text(row, "replay_fill_status", "fill_status")
    if value in {"filled", "simulated_filled", "executed"}:
        return "filled"
    if value in {"partial", "partially_filled"}:
        return "partial"
    if value in {"not_filled", "simulated_rejected", "rejected"}:
        return "not_filled"
    return "unknown"


def _replay_execution_mode(row: Mapping[str, Any]) -> str:
    fill_status = _first_text(row, "fill_status", "replay_fill_status")
    if fill_status.startswith("simulated_") or str(row.get("simulation_mode") or "").lower() == "true":
        return "simulated"
    if fill_status in {"filled", "partial", "not_filled"}:
        return "live_or_recorded"
    return "unknown"


def _eval_economic_class(*, net_return: float, excess_return: float) -> str:
    if excess_return > 0:
        return "positive_excess"
    if net_return < 0:
        return "negative_excess"
    if net_return > 0 and excess_return <= 0:
        return "under_baseline"
    if net_return == 0:
        return "neutral"
    return "unknown"


def _eval_action_class(*, disposition: str, agency: str, excess_return: float, miss_review_scope: str) -> str:
    if disposition == "accepted":
        return "taken_good" if excess_return > 0 else "taken_bad"
    if disposition in {"skipped", "rejected", "deferred"}:
        if excess_return > 0 and miss_review_scope != "path_conditioned_current_scope":
            return "unscored_global_good"
        return "missed_good" if excess_return > 0 else "avoided_bad"
    if disposition == "blocked":
        return "blocked_good" if excess_return > 0 else "blocked_bad"
    if agency != "unknown" and excess_return > 0 and miss_review_scope == "path_conditioned_current_scope":
        return "missed_good"
    return "ambiguous"


def _confidence_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 0.70:
        return "high"
    if score >= 0.55:
        return "medium"
    if score >= 0.45:
        return "neutral"
    return "low"


def _predictive_diagnostics(scored_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = [int(row["label"]) for row in scored_rows]
    scores = [float(row["score"]) for row in scored_rows]
    positives = sum(labels)
    row_count = len(scored_rows)
    thresholds = [0.30, 0.40, 0.50, 0.60, 0.70]
    return {
        "contract_type": "predictive_diagnostic",
        "row_count": row_count,
        "positive_count": positives,
        "negative_count": row_count - positives,
        "base_rate": _round_metric(positives / row_count) if row_count else None,
        "pr_auc": _pr_auc(labels, scores),
        "roc_curve": _roc_curve(labels, scores),
        "confusion_by_threshold": [_confusion_at_threshold(scored_rows, threshold) for threshold in thresholds],
        "threshold_return_curve": [_threshold_return(scored_rows, threshold) for threshold in thresholds],
    }


def _calibration_diagnostics(scored_rows: Sequence[Mapping[str, Any]], *, bin_count: int = 10) -> dict[str, Any]:
    if not scored_rows:
        return {
            "contract_type": "calibration_diagnostic",
            "available": False,
            "reason": "no scored rows",
            "ece": None,
            "mce": None,
            "bins": [],
            "brier_decomposition": {"reliability": None, "resolution": None, "uncertainty": None},
        }
    bins: list[dict[str, Any]] = []
    total = len(scored_rows)
    base_rate = sum(int(row["label"]) for row in scored_rows) / total
    reliability = 0.0
    resolution = 0.0
    ece = 0.0
    mce = 0.0
    for index in range(bin_count):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if index == bin_count - 1:
            bucket = [row for row in scored_rows if lower <= float(row["score"]) <= upper]
        else:
            bucket = [row for row in scored_rows if lower <= float(row["score"]) < upper]
        if not bucket:
            bins.append({"lower": lower, "upper": upper, "count": 0, "mean_score": None, "hit_rate": None, "gap": None})
            continue
        mean_score = sum(float(row["score"]) for row in bucket) / len(bucket)
        hit_rate = sum(int(row["label"]) for row in bucket) / len(bucket)
        gap = abs(hit_rate - mean_score)
        weight = len(bucket) / total
        reliability += weight * (mean_score - hit_rate) ** 2
        resolution += weight * (hit_rate - base_rate) ** 2
        ece += weight * gap
        mce = max(mce, gap)
        bins.append(
            {
                "lower": _round_metric(lower),
                "upper": _round_metric(upper),
                "count": len(bucket),
                "mean_score": _round_metric(mean_score),
                "hit_rate": _round_metric(hit_rate),
                "gap": _round_metric(gap),
            }
        )
    return {
        "contract_type": "calibration_diagnostic",
        "available": True,
        "ece": _round_metric(ece),
        "mce": _round_metric(mce),
        "bins": bins,
        "brier_decomposition": {
            "reliability": _round_metric(reliability),
            "resolution": _round_metric(resolution),
            "uncertainty": _round_metric(base_rate * (1 - base_rate)),
        },
    }


def _economic_diagnostics(*, net_returns: Sequence[float], realized_returns: Sequence[float], costs: Sequence[float]) -> dict[str, Any]:
    row_count = len(net_returns)
    return {
        "contract_type": "economic_diagnostic",
        "row_count": row_count,
        "return_per_decision": _round_metric(sum(net_returns) / row_count) if row_count else None,
        "profit_factor": _profit_factor(net_returns),
        "tail_loss_p05": _percentile(net_returns, 0.05),
        "tail_loss_p01": _percentile(net_returns, 0.01),
        "worst_return": min(net_returns) if net_returns else None,
        "cost_sensitivity": {
            f"{multiplier:.1f}x": _round_metric(sum(value - multiplier * cost for value, cost in zip(realized_returns, costs, strict=True)))
            for multiplier in (0.0, 1.0, 2.0, 3.0)
        },
    }


def _high_score_tail_risk_diagnostics(
    *,
    decision_rows: Sequence[Mapping[str, Any]],
    net_returns: Sequence[float],
) -> dict[str, Any]:
    filled_rows: list[dict[str, Any]] = []
    for row, net_return in zip(decision_rows, net_returns, strict=True):
        if not _is_filled_trade_row(row):
            continue
        score = _score(row)
        label = _label(row)
        if score is None or label is None:
            continue
        filled_rows.append(
            {
                "score": float(score),
                "label": int(label),
                "net_return": float(net_return),
                "dte": _selected_option_contract_dte(row),
            }
        )
    high_score_rows = [row for row in filled_rows if row["score"] >= HIGH_SCORE_TAIL_RISK_THRESHOLD]
    high_score_losses = [row for row in high_score_rows if row["net_return"] < 0]
    high_score_controls = [row for row in high_score_rows if row["net_return"] >= 0]
    filled_good_score = _mean(row["score"] for row in filled_rows if row["label"] == 1)
    filled_bad_score = _mean(row["score"] for row in filled_rows if row["label"] == 0)
    good_bad_score_gap = None if filled_good_score is None or filled_bad_score is None else filled_good_score - filled_bad_score
    short_dte_losses = [
        row for row in high_score_losses if row["dte"] is not None and row["dte"] <= SHORT_DTE_TAIL_LOSS_DAYS
    ]
    gate_failures: list[str] = []
    material_regressions: list[str] = []
    if (
        len(high_score_losses) >= MIN_HIGH_SCORE_TAIL_LOSS_COUNT
        and good_bad_score_gap is not None
        and good_bad_score_gap < MAX_HIGH_SCORE_GOOD_BAD_SCORE_GAP
    ):
        gate_failures.append("high_score_tail_loss_overconfidence")
        material_regressions.append("high-score filled losses are not sufficiently separated below filled winners by score")
    if len(high_score_losses) >= MIN_HIGH_SCORE_TAIL_LOSS_COUNT and len(filled_rows) < MIN_TAIL_RISK_FILLED_SAMPLE:
        gate_failures.append("high_score_tail_loss_sample_limited")
        material_regressions.append("high-score tail losses occurred under sample-limited filled-trade evidence")
    option_selection_status = (
        "weakly_supported"
        if len(short_dte_losses) >= MIN_HIGH_SCORE_TAIL_LOSS_COUNT
        else "not_supported_by_current_evidence"
    )
    if option_selection_status == "weakly_supported":
        material_regressions.append("high-score filled losses concentrate in short-DTE option selections")
    return {
        "contract_type": "high_score_tail_risk_diagnostic",
        "high_score_threshold": HIGH_SCORE_TAIL_RISK_THRESHOLD,
        "filled_count": len(filled_rows),
        "minimum_required_filled_count": MIN_TAIL_RISK_FILLED_SAMPLE,
        "sample_sufficiency_status": "sample_limited" if len(filled_rows) < MIN_TAIL_RISK_FILLED_SAMPLE else "sufficient_for_this_diagnostic",
        "high_score_filled_count": len(high_score_rows),
        "high_score_filled_loss_count": len(high_score_losses),
        "high_score_filled_control_count": len(high_score_controls),
        "minimum_high_score_tail_loss_count": MIN_HIGH_SCORE_TAIL_LOSS_COUNT,
        "filled_good_bad_score_gap": _round_metric(good_bad_score_gap) if good_bad_score_gap is not None else None,
        "minimum_required_good_bad_score_gap": MAX_HIGH_SCORE_GOOD_BAD_SCORE_GAP,
        "short_dte_tail_loss_count": len(short_dte_losses),
        "minimum_short_dte_tail_loss_count": MIN_HIGH_SCORE_TAIL_LOSS_COUNT,
        "short_dte_days": SHORT_DTE_TAIL_LOSS_DAYS,
        "model_overconfidence_status": (
            "failed" if "high_score_tail_loss_overconfidence" in gate_failures else "not_supported_by_current_evidence"
        ),
        "option_selection_mechanics_status": option_selection_status,
        "execution_replay_artifact_status": "not_assessed_here",
        "unknown_requires_evidence": {
            "feature_timing_or_leakage": ["pit_feature_trace", "feature_generation_clock", "leakage_check_rows"],
            "liquidity_spread_fill_realism": ["bid_ask_spread", "quote_depth", "slippage_model", "partial_fill_simulation"],
            "regime_event_miss": ["m06_event_overlay", "regime_state", "co_event_controls"],
        },
        "gate_failures": gate_failures,
        "material_regressions": material_regressions,
    }


def _data_integrity_diagnostics(
    *,
    raw_decision_rows: Sequence[Mapping[str, Any]],
    decision_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    validation_rows = len(raw_decision_rows) - len(decision_rows)
    label_horizon_failures = []
    feature_timestamp_failures = []
    missing_timestamp_count = 0
    for row in decision_rows:
        decision_time = _parse_datetime(row.get("timestamp") or row.get("decision_timestamp"))
        next_time = _parse_datetime(row.get("next_timestamp") or row.get("label_timestamp") or row.get("outcome_timestamp"))
        if decision_time is None:
            missing_timestamp_count += 1
        if decision_time is not None and next_time is not None and next_time <= decision_time:
            label_horizon_failures.append(str(row.get("decision_id") or row.get("timestamp") or "unknown"))
        for key, value in row.items():
            if not (key.startswith("feature_") and key.endswith("timestamp")):
                continue
            feature_time = _parse_datetime(value)
            if decision_time is not None and feature_time is not None and feature_time > decision_time:
                feature_timestamp_failures.append(str(row.get("decision_id") or row.get("timestamp") or key))
    leakage_failures = len(label_horizon_failures) + len(feature_timestamp_failures)
    status = "passed" if leakage_failures == 0 and missing_timestamp_count == 0 else "warning"
    return {
        "contract_type": "data_integrity_diagnostic",
        "status": status,
        "leakage_check_status": "passed" if leakage_failures == 0 else "failed",
        "raw_row_count": len(raw_decision_rows),
        "evaluated_row_count": len(decision_rows),
        "validation_row_excluded_count": validation_rows,
        "missing_timestamp_count": missing_timestamp_count,
        "label_horizon_failure_count": len(label_horizon_failures),
        "feature_timestamp_failure_count": len(feature_timestamp_failures),
        "fold_isolation_status": "not_assessed",
        "fold_isolation_reason": "fold boundary evidence is tracked in training workflow state, not replay decision rows",
    }


def _temporal_stability_diagnostics(scored_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_month: dict[str, list[Mapping[str, Any]]] = {}
    for row in scored_rows:
        month = _month_key(row.get("timestamp"))
        if month:
            by_month.setdefault(month, []).append(row)
    slices = []
    for month, rows in sorted(by_month.items()):
        ordered_rows = sorted(enumerate(rows), key=lambda item: (str(item[1].get("timestamp") or ""), item[0]))
        labels = [int(row["label"]) for row in rows]
        scores = [float(row["score"]) for row in rows]
        returns = [float(row["net_return"]) for _index, row in ordered_rows]
        slices.append(
            {
                "month": month,
                "row_count": len(rows),
                "base_rate": _round_metric(sum(labels) / len(labels)) if labels else None,
                "auroc": _auroc(labels, scores),
                "brier_score": _brier_score(labels, scores),
                "net_return_total": _round_metric(sum(returns)),
                "max_drawdown": _round_metric(_max_drawdown(returns)),
                "net_return_path_ohlc": _return_path_ohlc(returns),
            }
        )
    returns_by_month = [float(item["net_return_total"]) for item in slices if item.get("net_return_total") is not None]
    return {
        "contract_type": "temporal_stability_diagnostic",
        "month_slice_count": len(slices),
        "slices": slices,
        "worst_month_return": min(returns_by_month) if returns_by_month else None,
        "best_month_return": max(returns_by_month) if returns_by_month else None,
    }


def _baseline_comparison_diagnostics(
    *,
    labels: Sequence[int],
    scores: Sequence[float],
    net_total: float,
    baseline_total: float,
) -> dict[str, Any]:
    shuffled_labels = _deterministic_shuffle(labels)
    return {
        "contract_type": "baseline_comparison_diagnostic",
        "no_trade_return_total": 0.0,
        "recorded_baseline_return_total": _round_metric(baseline_total),
        "candidate_return_total": _round_metric(net_total),
        "candidate_minus_no_trade": _round_metric(net_total),
        "candidate_minus_recorded_baseline": _round_metric(net_total - baseline_total),
        "randomized_label_auroc": _auroc(shuffled_labels, scores) if shuffled_labels and scores else None,
        "previous_version_comparison": {
            "available": False,
            "reason": "requires at least two comparable model-group versions",
        },
    }


def _pr_auc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    pairs = sorted(zip(scores, labels, strict=True), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    if not pairs or positives == 0:
        return None
    true_positive = 0
    precision_sum = 0.0
    for rank, (_score_value, label) in enumerate(pairs, start=1):
        if label == 1:
            true_positive += 1
            precision_sum += true_positive / rank
    return _round_metric(precision_sum / positives)


def _roc_curve(labels: Sequence[int], scores: Sequence[float]) -> list[dict[str, Any]]:
    pairs = sorted(zip(scores, labels, strict=True), key=lambda item: item[0], reverse=True)
    positives = sum(labels)
    negatives = len(labels) - positives
    if not pairs or positives == 0 or negatives == 0:
        return []
    points: list[dict[str, Any]] = [
        {
            "threshold": None,
            "false_positive_rate": 0.0,
            "true_positive_rate": 0.0,
            "true_positive": 0,
            "false_positive": 0,
        }
    ]
    true_positive = 0
    false_positive = 0
    index = 0
    while index < len(pairs):
        threshold = float(pairs[index][0])
        while index < len(pairs) and float(pairs[index][0]) == threshold:
            if int(pairs[index][1]) == 1:
                true_positive += 1
            else:
                false_positive += 1
            index += 1
        points.append(
            {
                "threshold": _round_metric(threshold),
                "false_positive_rate": _round_metric(false_positive / negatives),
                "true_positive_rate": _round_metric(true_positive / positives),
                "true_positive": true_positive,
                "false_positive": false_positive,
            }
        )
    return points


def _confusion_at_threshold(scored_rows: Sequence[Mapping[str, Any]], threshold: float) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row in scored_rows:
        predicted_positive = float(row["score"]) >= threshold
        actual_positive = int(row["label"]) == 1
        if predicted_positive and actual_positive:
            tp += 1
        elif predicted_positive and not actual_positive:
            fp += 1
        elif not predicted_positive and actual_positive:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "threshold": _round_metric(threshold),
        "true_positive": tp,
        "false_positive": fp,
        "true_negative": tn,
        "false_negative": fn,
        "precision": _round_metric(precision) if precision is not None else None,
        "recall": _round_metric(recall) if recall is not None else None,
    }


def _threshold_return(scored_rows: Sequence[Mapping[str, Any]], threshold: float) -> dict[str, Any]:
    selected = [row for row in scored_rows if float(row["score"]) >= threshold]
    returns = [float(row["net_return"]) for row in selected]
    labels = [int(row["label"]) for row in selected]
    return {
        "threshold": _round_metric(threshold),
        "selected_count": len(selected),
        "net_return_total": _round_metric(sum(returns)) if selected else 0.0,
        "hit_rate": _round_metric(sum(labels) / len(labels)) if labels else None,
        "return_per_selected": _round_metric(sum(returns) / len(returns)) if returns else None,
    }


def _brier_score(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    if not labels:
        return None
    return _round_metric(sum((score - label) ** 2 for label, score in zip(labels, scores, strict=True)) / len(labels))


def _profit_factor(returns: Sequence[float]) -> float | None:
    gains = sum(value for value in returns if value > 0)
    losses = abs(sum(value for value in returns if value < 0))
    if losses == 0:
        return None
    return _round_metric(gains / losses)


def _percentile(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.floor(percentile * (len(ordered) - 1))))
    return _round_metric(ordered[index])


def _parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _month_key(value: Any) -> str | None:
    parsed = _parse_datetime(value)
    return parsed.strftime("%Y-%m") if parsed is not None else None


def _deterministic_shuffle(values: Sequence[int]) -> list[int]:
    keyed = sorted(((_stable_token(index, value), value) for index, value in enumerate(values)), key=lambda item: item[0])
    return [value for _key, value in keyed]


def _feature_space_diagnostics(decision_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    feature_columns = _feature_columns(decision_rows)
    feature_rows, source_rows = _feature_matrix(decision_rows, feature_columns)
    if not feature_rows:
        return _empty_feature_diagnostics(feature_columns)

    active_columns, standardized_rows = _standardize_feature_rows(feature_rows, feature_columns)
    if len(active_columns) < 2 or len(standardized_rows) < 3:
        diagnostics = _empty_feature_diagnostics(active_columns)
        diagnostics["feature_row_count"] = len(standardized_rows)
        return diagnostics

    sampled_rows, sampled_indices = _even_sample(standardized_rows, FEATURE_DIAGNOSTIC_SAMPLE_LIMIT)
    sampled_source_rows = [source_rows[index] for index in sampled_indices]
    pca = _pca_diagnostic(sampled_rows, sampled_source_rows)
    pcoa = _pcoa_diagnostic(sampled_rows, sampled_source_rows)
    silhouette = {
        "outcome_label": _silhouette_for_label(sampled_rows, [_label(row) for row in sampled_source_rows]),
        "decision_action": _silhouette_for_label(
            sampled_rows,
            [str(row.get("decision_action") or row.get("action") or "").strip().lower() or None for row in sampled_source_rows],
        ),
        "decision_intended_side": _silhouette_for_label(sampled_rows, [_decision_intended_side(row) for row in sampled_source_rows]),
        "decision_intended_action": _silhouette_for_label(sampled_rows, [_decision_intended_action(row) for row in sampled_source_rows]),
    }
    return {
        "contract_type": "feature_space_diagnostic",
        "feature_columns": active_columns,
        "feature_column_count": len(active_columns),
        "feature_row_count": len(standardized_rows),
        "sample_count": len(sampled_rows),
        "pca": pca,
        "pcoa": pcoa,
        "silhouette": silhouette,
    }


def _empty_feature_diagnostics(feature_columns: Sequence[str]) -> dict[str, Any]:
    return {
        "contract_type": "feature_space_diagnostic",
        "feature_columns": list(feature_columns),
        "feature_column_count": len(feature_columns),
        "feature_row_count": 0,
        "sample_count": 0,
        "pca": {"available": False, "explained_variance_ratio": [], "points": []},
        "pcoa": {"available": False, "explained_variance_ratio": [], "points": []},
        "silhouette": {
            "outcome_label": None,
            "decision_action": None,
            "decision_intended_side": None,
            "decision_intended_action": None,
        },
    }


def _feature_columns(decision_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    columns: set[str] = set()
    for row in decision_rows:
        for key, value in row.items():
            if key.startswith("feature_") and _finite_float(value) is not None:
                columns.add(key)
    return sorted(columns)


def _feature_matrix(
    decision_rows: Sequence[Mapping[str, Any]],
    feature_columns: Sequence[str],
) -> tuple[list[list[float]], list[Mapping[str, Any]]]:
    rows: list[list[float]] = []
    source_rows: list[Mapping[str, Any]] = []
    for row in decision_rows:
        values = [_finite_float(row.get(column)) for column in feature_columns]
        if values and all(value is not None for value in values):
            rows.append([float(value) for value in values])
            source_rows.append(row)
    return rows, source_rows


def _standardize_feature_rows(rows: Sequence[Sequence[float]], columns: Sequence[str]) -> tuple[list[str], list[list[float]]]:
    if not rows:
        return [], []
    means = [sum(row[index] for row in rows) / len(rows) for index in range(len(columns))]
    variances = [
        sum((row[index] - means[index]) ** 2 for row in rows) / len(rows)
        for index in range(len(columns))
    ]
    active_indices = [index for index, variance in enumerate(variances) if variance > 1e-12]
    active_columns = [columns[index] for index in active_indices]
    standardized = [
        [(row[index] - means[index]) / math.sqrt(variances[index]) for index in active_indices]
        for row in rows
    ]
    return active_columns, standardized


def _even_sample(rows: Sequence[list[float]], limit: int) -> tuple[list[list[float]], list[int]]:
    if len(rows) <= limit:
        return list(rows), list(range(len(rows)))
    if limit <= 1:
        return [rows[0]], [0]
    indices = sorted({round(index * (len(rows) - 1) / (limit - 1)) for index in range(limit)})
    return [rows[index] for index in indices], indices


def _pca_diagnostic(rows: Sequence[Sequence[float]], source_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) < 3 or len(rows[0]) < 2:
        return {"available": False, "explained_variance_ratio": [], "points": []}
    covariance = _covariance_matrix(rows)
    eigenpairs = _jacobi_eigenpairs(covariance)
    positive = [(value, vector) for value, vector in eigenpairs if value > 1e-12]
    if len(positive) < 2:
        return {"available": False, "explained_variance_ratio": [], "points": []}
    total = sum(value for value, _vector in positive)
    axes = [positive[0][1], positive[1][1]]
    points = []
    for row, source in zip(rows[:FEATURE_DIAGNOSTIC_POINT_LIMIT], source_rows[:FEATURE_DIAGNOSTIC_POINT_LIMIT], strict=True):
        points.append(_diagnostic_point(row, axes, source))
    return {
        "available": True,
        "explained_variance_ratio": [_round_metric(positive[0][0] / total), _round_metric(positive[1][0] / total)],
        "points": points,
    }


def _pcoa_diagnostic(rows: Sequence[Sequence[float]], source_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) < 3:
        return {"available": False, "explained_variance_ratio": [], "points": []}
    n = len(rows)
    distances_squared = [[_squared_distance(rows[i], rows[j]) for j in range(n)] for i in range(n)]
    row_means = [sum(row) / n for row in distances_squared]
    column_means = [sum(distances_squared[i][j] for i in range(n)) / n for j in range(n)]
    grand_mean = sum(row_means) / n
    centered = [
        [-0.5 * (distances_squared[i][j] - row_means[i] - column_means[j] + grand_mean) for j in range(n)]
        for i in range(n)
    ]
    eigenpairs = _jacobi_eigenpairs(centered)
    positive = [(value, vector) for value, vector in eigenpairs if value > 1e-12]
    if len(positive) < 2:
        return {"available": False, "explained_variance_ratio": [], "points": []}
    total = sum(value for value, _vector in positive)
    points = []
    for index, source in enumerate(source_rows[:FEATURE_DIAGNOSTIC_POINT_LIMIT]):
        x = positive[0][1][index] * math.sqrt(positive[0][0])
        y = positive[1][1][index] * math.sqrt(positive[1][0])
        points.append(_diagnostic_point_from_xy(x, y, source))
    return {
        "available": True,
        "explained_variance_ratio": [_round_metric(positive[0][0] / total), _round_metric(positive[1][0] / total)],
        "points": points,
    }


def _silhouette_for_label(rows: Sequence[Sequence[float]], labels: Sequence[Any]) -> float | None:
    usable = [(row, label) for row, label in zip(rows, labels, strict=True) if label not in (None, "")]
    if len(usable) < 3:
        return None
    clusters: dict[Any, list[int]] = {}
    for index, (_row, label) in enumerate(usable):
        clusters.setdefault(label, []).append(index)
    if len(clusters) < 2 or any(len(indices) == len(usable) for indices in clusters.values()):
        return None
    matrix = [[_squared_distance(usable[i][0], usable[j][0]) ** 0.5 for j in range(len(usable))] for i in range(len(usable))]
    scores: list[float] = []
    for index, (_row, label) in enumerate(usable):
        own = [other for other in clusters[label] if other != index]
        a = sum(matrix[index][other] for other in own) / len(own) if own else 0.0
        b_values = []
        for other_label, indices in clusters.items():
            if other_label == label:
                continue
            b_values.append(sum(matrix[index][other] for other in indices) / len(indices))
        b = min(b_values) if b_values else 0.0
        denominator = max(a, b)
        scores.append((b - a) / denominator if denominator else 0.0)
    return _round_metric(sum(scores) / len(scores))


def _covariance_matrix(rows: Sequence[Sequence[float]]) -> list[list[float]]:
    n = len(rows)
    columns = len(rows[0])
    return [
        [
            sum(row[i] * row[j] for row in rows) / (n - 1)
            for j in range(columns)
        ]
        for i in range(columns)
    ]


def _jacobi_eigenpairs(matrix: Sequence[Sequence[float]]) -> list[tuple[float, list[float]]]:
    n = len(matrix)
    a = [list(row) for row in matrix]
    vectors = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _iteration in range(80):
        p, q, max_value = 0, 1 if n > 1 else 0, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(a[i][j]) > max_value:
                    p, q, max_value = i, j, abs(a[i][j])
        if max_value < 1e-10:
            break
        if abs(a[p][p] - a[q][q]) < 1e-12:
            angle = math.pi / 4
        else:
            angle = 0.5 * math.atan2(2 * a[p][q], a[q][q] - a[p][p])
        c = math.cos(angle)
        s = math.sin(angle)
        for i in range(n):
            if i not in {p, q}:
                aip = a[i][p]
                aiq = a[i][q]
                a[i][p] = a[p][i] = c * aip - s * aiq
                a[i][q] = a[q][i] = s * aip + c * aiq
        app = a[p][p]
        aqq = a[q][q]
        apq = a[p][q]
        a[p][p] = c * c * app - 2 * s * c * apq + s * s * aqq
        a[q][q] = s * s * app + 2 * s * c * apq + c * c * aqq
        a[p][q] = a[q][p] = 0.0
        for i in range(n):
            vip = vectors[i][p]
            viq = vectors[i][q]
            vectors[i][p] = c * vip - s * viq
            vectors[i][q] = s * vip + c * viq
    pairs = [(a[i][i], [vectors[row][i] for row in range(n)]) for i in range(n)]
    return sorted(pairs, key=lambda item: item[0], reverse=True)


def _diagnostic_point(row: Sequence[float], axes: Sequence[Sequence[float]], source: Mapping[str, Any]) -> dict[str, Any]:
    x = sum(value * axes[0][index] for index, value in enumerate(row))
    y = sum(value * axes[1][index] for index, value in enumerate(row))
    return _diagnostic_point_from_xy(x, y, source)


def _diagnostic_point_from_xy(x: float, y: float, source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "x": _round_metric(x),
        "y": _round_metric(y),
        "outcome_label": _label(source),
        "decision_action": str(source.get("decision_action") or source.get("action") or ""),
        "decision_intended_side": _decision_intended_side(source),
        "decision_intended_action": _decision_intended_action(source),
        "decision_disposition": _decision_disposition(source, intended_action=_decision_intended_action(source)),
        "target_ref": str(source.get("target_ref") or source.get("instrument_ref") or ""),
        "timestamp": str(source.get("timestamp") or ""),
    }


def _squared_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right, strict=True))


def _round_metric(value: float) -> float:
    return round(float(value), 6)


def _mean(values: Iterable[float]) -> float | None:
    values_tuple = tuple(values)
    if not values_tuple:
        return None
    return sum(values_tuple) / len(values_tuple)


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _is_filled_trade_row(row: Mapping[str, Any]) -> bool:
    fill_status = str(row.get("fill_status") or "").strip().lower()
    if fill_status in {"simulated_filled", "filled", "executed"}:
        return True
    if fill_status in {"not_filled", "simulated_rejected", "rejected", "cancelled", "canceled"}:
        return False
    action = str(row.get("action") or row.get("decision") or row.get("decision_action") or "").strip().lower()
    return action not in {"", "hold", "skip", "no_trade", "reject_entry_thesis", "defer_entry_thesis", "simulated_rejected"}


def _selected_option_contract_dte(row: Mapping[str, Any]) -> int | None:
    contract_ref = str(row.get("selected_option_contract_ref") or row.get("selected_contract_ref") or "").strip()
    parts = contract_ref.split("_")
    if len(parts) < 2:
        return None
    try:
        expiry = datetime.fromisoformat(parts[1]).date()
    except ValueError:
        return None
    timestamp = _parse_datetime(row.get("timestamp") or row.get("decision_timestamp"))
    if timestamp is None:
        return None
    return (expiry - timestamp.date()).days


def _build_promotion_review(
    *,
    settlement: Mapping[str, Any],
    settlement_ref: str,
    benchmark_contract_ref: str,
    residual_event_governance_ref: str,
    created_at_utc: str,
    call_agent_review: bool,
    agent_reviewer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
    codex_bin: str,
    codex_model: str | None,
    codex_timeout_seconds: int,
) -> dict[str, Any]:
    packet = _build_promotion_review_packet(
        settlement=settlement,
        settlement_ref=settlement_ref,
        benchmark_contract_ref=benchmark_contract_ref,
        residual_event_governance_ref=residual_event_governance_ref,
        created_at_utc=created_at_utc,
    )
    if agent_reviewer is not None:
        try:
            return _normalize_promotion_agent_review(
                agent_reviewer(packet),
                fallback=packet,
                invocation_status="completed",
                invocation_error="",
            )
        except Exception as exc:  # pragma: no cover - defensive runtime guard.
            return _agent_failed_promotion_review(packet, f"agent_reviewer_failed: {exc}")
    if not call_agent_review:
        packet["agent_invocation_status"] = "not_invoked_local_fallback"
        return packet
    try:
        agent_payload = _invoke_promotion_review_agent(
            review_packet=packet,
            codex_bin=codex_bin,
            codex_model=codex_model,
            timeout_seconds=codex_timeout_seconds,
        )
    except Exception as exc:
        return _agent_failed_promotion_review(packet, f"codex_agent_call_failed: {exc}")
    return _normalize_promotion_agent_review(
        agent_payload,
        fallback=packet,
        invocation_status="completed",
        invocation_error="",
    )


def _build_promotion_review_packet(
    *,
    settlement: Mapping[str, Any],
    settlement_ref: str,
    benchmark_contract_ref: str,
    residual_event_governance_ref: str,
    created_at_utc: str,
) -> dict[str, Any]:
    metrics = settlement.get("metrics") if isinstance(settlement.get("metrics"), Mapping) else {}
    gate_failures = [str(item) for item in settlement.get("gate_failures") or []]
    blocking_issues = []
    if gate_failures:
        blocking_issues.append("settlement gate failures: " + ", ".join(gate_failures))
    high_score_tail_risk = metrics.get("high_score_tail_risk_diagnostics")
    tail_risk_followups: list[str] = []
    tail_risk_regressions: list[str] = []
    if isinstance(high_score_tail_risk, Mapping):
        tail_risk_regressions = _string_list(high_score_tail_risk.get("material_regressions"))
        unknown_evidence = high_score_tail_risk.get("unknown_requires_evidence")
        if isinstance(unknown_evidence, Mapping):
            for cause_name, evidence_codes in unknown_evidence.items():
                codes = ", ".join(_string_list(evidence_codes))
                tail_risk_followups.append(f"attach {cause_name} evidence: {codes}")
    blocking_issues.extend(
        [
            "missing anonymous comparison model result on the same benchmark contract",
            "missing candidate config evidence for shadow-readiness judgment",
            "missing first-run or benchmark query-count evidence",
        ]
    )
    return {
        "contract_type": "promotion_evaluation_review",
        "review_type": "promotion_evaluation_review",
        "review_ref": settlement_ref.replace("fold_settlement_run.json", "promotion_evaluation_review.json"),
        "candidate_label": "model_a",
        "fold_id": str(settlement.get("fold_id") or ""),
        "target_symbol": str(settlement.get("target_symbol") or ""),
        "benchmark_contract_ref": benchmark_contract_ref,
        "comparison_label": "model_b",
        "recommendation": "insufficient_evidence" if blocking_issues else "eligible_for_shadow",
        "confidence": "low",
        "identity_blinding_status": "insufficient_evidence",
        "integrity_status": "passed",
        "hard_guardrail_status": "failed" if gate_failures else "passed",
        "comparison_status": "insufficient_evidence",
        "uncertainty_status": "insufficient_evidence",
        "shadow_readiness_status": "insufficient_evidence",
        "settlement_run_ref": settlement_ref,
        "residual_event_governance_ref": residual_event_governance_ref,
        "first_model_bootstrap": False,
        "bootstrap_baseline_ref": "",
        "candidate_model_ref": str(settlement.get("candidate_model_ref") or ""),
        "replay_contract_ref": str(settlement.get("replay_contract_ref") or ""),
        "metric_refs": list(settlement.get("metric_refs") or []),
        "gate_failures": gate_failures,
        "metrics_summary": {
            "decision_row_count": metrics.get("decision_row_count"),
            "net_return_total": metrics.get("net_return_total"),
            "baseline_return_total": metrics.get("baseline_return_total"),
            "excess_return_total": metrics.get("excess_return_total"),
            "max_drawdown": metrics.get("max_drawdown"),
            "high_score_tail_risk_diagnostics": high_score_tail_risk,
            "hit_rate": metrics.get("hit_rate"),
            "payoff_ratio": metrics.get("payoff_ratio"),
            "turnover_proxy_count": metrics.get("turnover_proxy_count"),
            "auroc": metrics.get("auroc"),
            "pr_auc": metrics.get("pr_auc"),
            "brier_score": metrics.get("brier_score"),
            "feature_column_count": metrics.get("feature_column_count"),
            "feature_row_count": metrics.get("feature_row_count"),
            "ece": metrics.get("ece"),
            "mce": metrics.get("mce"),
            "profit_factor": metrics.get("profit_factor"),
            "tail_loss_p05": metrics.get("tail_loss_p05"),
            "worst_month_return": metrics.get("worst_month_return"),
            "data_integrity_status": metrics.get("data_integrity_status"),
            "pca_variance_top2": metrics.get("pca_variance_top2"),
            "pcoa_variance_top2": metrics.get("pcoa_variance_top2"),
            "silhouette_outcome_label": metrics.get("silhouette_outcome_label"),
            "silhouette_decision_action": metrics.get("silhouette_decision_action"),
            "scorecards": metrics.get("scorecards"),
            "evaluation_disagreement_report": metrics.get("evaluation_disagreement_report"),
        },
        "material_improvements": [f"settlement row count {metrics.get('decision_row_count')} is available"],
        "material_regressions": gate_failures + tail_risk_regressions,
        "blocking_issues": blocking_issues,
        "required_followups": [
            "provide blinded model_a/model_b comparison evidence on the frozen replay contract",
            "attach candidate config and rollback refs before shadow-readiness review",
            "attach first-run/query-count evidence for this candidate lineage",
        ]
        + tail_risk_followups,
        "rationale": (
            f"settlement rows={metrics.get('decision_row_count')}; AUROC={metrics.get('auroc')}; "
            f"excess_return_total={metrics.get('excess_return_total')}; max_drawdown={metrics.get('max_drawdown')}; "
            f"blocking_issues={len(blocking_issues)}"
        ),
        "created_at_utc": created_at_utc,
        "agent_invocation_status": "pending",
        "agent_invocation_error": "",
        "model_activation_performed": False,
        "active_model_config_written": False,
        "broker_execution_performed": False,
        "account_mutation_performed": False,
    }


def _invoke_promotion_review_agent(
    *,
    review_packet: Mapping[str, Any],
    codex_bin: str,
    codex_model: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    prompt = _promotion_review_agent_prompt(review_packet)
    model = codex_model or os.environ.get("TRADING_MANAGER_PROMOTION_REVIEW_CODEX_MODEL") or DEFAULT_PROMOTION_REVIEW_CODEX_MODEL
    with tempfile.TemporaryDirectory(prefix="model-group-promotion-review-") as raw_tmp:
        final_output_path = Path(raw_tmp) / "codex_final_output.txt"
        command = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-C",
            str(DEFAULT_PROMOTION_REVIEW_CODEX_WORKDIR),
            "--output-last-message",
            str(final_output_path),
            "-m",
            model,
            "--add-dir",
            str(DEFAULT_PROMOTION_REVIEW_CODEX_ADD_DIR),
            prompt,
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
        output = final_output_path.read_text(encoding="utf-8") if final_output_path.exists() else result.stdout
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or f"codex exited {result.returncode}").strip()[:2000])
    return _json_object_from_text(output)


def _promotion_review_agent_prompt(review_packet: Mapping[str, Any]) -> str:
    return (
        "Use the promotion-evaluation-review skill. Review this completed model-group promotion candidate as an advisory reviewer only.\n"
        "Do not activate a model, write active configs, call providers, mutate SQL/storage, submit orders, or mutate accounts.\n"
        "Return strict JSON only, with exactly this contract shape and no markdown:\n"
        "{"
        "\"review_type\":\"promotion_evaluation_review\","
        "\"candidate_label\":\"string\","
        "\"fold_id\":\"string\","
        "\"benchmark_contract_ref\":\"string\","
        "\"comparison_label\":\"string\","
        "\"recommendation\":\"failed|deferred|eligible_for_shadow|insufficient_evidence\","
        "\"confidence\":\"low|medium|high\","
        "\"identity_blinding_status\":\"passed|failed|not_applicable|insufficient_evidence\","
        "\"integrity_status\":\"passed|failed|insufficient_evidence\","
        "\"hard_guardrail_status\":\"passed|failed|insufficient_evidence\","
        "\"comparison_status\":\"better|not_materially_better|worse|mixed|insufficient_evidence\","
        "\"uncertainty_status\":\"acceptable|too_uncertain|insufficient_evidence\","
        "\"shadow_readiness_status\":\"ready|not_ready|not_assessed|insufficient_evidence\","
        "\"material_improvements\":[\"string\"],"
        "\"material_regressions\":[\"string\"],"
        "\"blocking_issues\":[\"string\"],"
        "\"required_followups\":[\"string\"],"
        "\"rationale\":\"short evidence-grounded explanation\""
        "}\n"
        "Evidence packet:\n"
        f"{json.dumps(review_packet, indent=2, sort_keys=True, default=str)}\n"
    )


def _json_object_from_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("agent output did not contain a JSON object") from None
        payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("agent output JSON was not an object")
    return payload


def _normalize_promotion_agent_review(
    payload: Mapping[str, Any],
    *,
    fallback: Mapping[str, Any],
    invocation_status: str,
    invocation_error: str,
) -> dict[str, Any]:
    normalized = dict(fallback)
    normalized.update(
        {
            "review_type": "promotion_evaluation_review",
            "candidate_label": _string_choice(payload.get("candidate_label"), fallback.get("candidate_label"), allowed=None),
            "fold_id": _string_choice(payload.get("fold_id"), fallback.get("fold_id"), allowed=None),
            "benchmark_contract_ref": _string_choice(payload.get("benchmark_contract_ref"), fallback.get("benchmark_contract_ref"), allowed=None),
            "comparison_label": _string_choice(payload.get("comparison_label"), fallback.get("comparison_label"), allowed=None),
            "recommendation": _string_choice(payload.get("recommendation"), "insufficient_evidence", allowed=PROMOTION_REVIEW_RECOMMENDATIONS),
            "confidence": _string_choice(payload.get("confidence"), "low", allowed=PROMOTION_REVIEW_CONFIDENCE),
            "identity_blinding_status": _string_choice(payload.get("identity_blinding_status"), "insufficient_evidence", allowed=PROMOTION_REVIEW_STATUS),
            "integrity_status": _string_choice(payload.get("integrity_status"), "insufficient_evidence", allowed={"passed", "failed", "insufficient_evidence"}),
            "hard_guardrail_status": _string_choice(payload.get("hard_guardrail_status"), "insufficient_evidence", allowed={"passed", "failed", "insufficient_evidence"}),
            "comparison_status": _string_choice(payload.get("comparison_status"), "insufficient_evidence", allowed=PROMOTION_COMPARISON_STATUS),
            "uncertainty_status": _string_choice(payload.get("uncertainty_status"), "insufficient_evidence", allowed=PROMOTION_UNCERTAINTY_STATUS),
            "shadow_readiness_status": _string_choice(payload.get("shadow_readiness_status"), "insufficient_evidence", allowed=PROMOTION_SHADOW_READINESS_STATUS),
            "material_improvements": _string_list(payload.get("material_improvements")),
            "material_regressions": _string_list(payload.get("material_regressions")),
            "blocking_issues": _string_list(payload.get("blocking_issues")),
            "required_followups": _string_list(payload.get("required_followups")),
            "rationale": str(payload.get("rationale") or fallback.get("rationale") or ""),
            "agent_invocation_status": invocation_status,
            "agent_invocation_error": invocation_error,
            "model_activation_performed": False,
            "active_model_config_written": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
        }
    )
    return normalized


def _agent_failed_promotion_review(fallback: Mapping[str, Any], error: str) -> dict[str, Any]:
    payload = dict(fallback)
    blocking = _string_list(payload.get("blocking_issues"))
    blocking.append(error)
    payload.update(
        {
            "recommendation": "insufficient_evidence",
            "confidence": "low",
            "identity_blinding_status": "insufficient_evidence",
            "integrity_status": "insufficient_evidence",
            "hard_guardrail_status": "insufficient_evidence",
            "comparison_status": "insufficient_evidence",
            "uncertainty_status": "insufficient_evidence",
            "shadow_readiness_status": "insufficient_evidence",
            "blocking_issues": blocking,
            "required_followups": _string_list(payload.get("required_followups")) + ["rerun promotion-evaluation-review agent successfully"],
            "rationale": f"Promotion review agent did not return accepted evidence: {error}",
            "agent_invocation_status": "agent_call_failed",
            "agent_invocation_error": error,
            "model_activation_performed": False,
            "active_model_config_written": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
        }
    )
    return payload


def _string_choice(value: Any, fallback: Any, *, allowed: set[str] | None) -> str:
    text = str(value or "").strip()
    if not text:
        text = str(fallback or "").strip()
    if allowed is not None and text not in allowed:
        text = str(fallback or "").strip()
        if text not in allowed:
            text = sorted(allowed)[0]
    return text


def _string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item)]
    if value in (None, ""):
        return []
    return [str(value)]


def _build_promotion_eligibility_decision(
    *,
    settlement: Mapping[str, Any],
    review: Mapping[str, Any],
    settlement_ref: str,
    review_ref: str,
    replay_contract_ref: str,
    created_at_utc: str,
) -> dict[str, Any]:
    decision_status = _promotion_decision_status(
        review.get("recommendation"),
        hard_guardrail_status=review.get("hard_guardrail_status"),
    )
    return {
        "contract_type": "promotion_eligibility_decision",
        "promotion_eligibility_decision_id": f"promelig_{_stable_token(settlement.get('fold_id'), settlement_ref, decision_status)}",
        "fold_id": str(settlement.get("fold_id") or ""),
        "target_symbol": str(settlement.get("target_symbol") or ""),
        "candidate_model_ref": str(settlement.get("candidate_model_ref") or ""),
        "replay_contract_ref": replay_contract_ref,
        "settlement_run_ref": settlement_ref,
        "decision_status": decision_status,
        "decision_reason": str(review.get("rationale") or ""),
        "metric_refs": list(settlement.get("metric_refs") or []),
        "guardrail_refs": [review_ref],
        "replay_validation_ref": str(settlement.get("replay_result_ref") or ""),
        "replay_freeze_status": "frozen",
        "fold_stack_evidence_ref": str(settlement.get("fold_stack_evidence_ref") or settlement_ref),
        "fold_stack_status": str(settlement.get("fold_stack_status") or "complete_m01_m06"),
        "guardrail_status": "passed" if review.get("hard_guardrail_status") == "passed" else "failed",
        "incumbent_comparison_ref": "",
        "incumbent_comparison_status": "",
        "agent_review_ref": review_ref,
        "agent_review_recommendation": str(review.get("recommendation") or ""),
        "first_model_bootstrap": False,
        "bootstrap_baseline_ref": "",
        "created_at_utc": created_at_utc,
    }


def _promotion_decision_status(recommendation: Any, *, hard_guardrail_status: Any = None) -> str:
    guardrail_status = str(hard_guardrail_status or "").strip().lower()
    if guardrail_status == "failed":
        return "rejected"
    recommendation_status = str(recommendation or "").strip().lower()
    if recommendation_status == "eligible_for_shadow":
        return "eligible"
    if recommendation_status == "failed":
        return "rejected"
    return "deferred"


def _evaluation_check_summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    attribution_rows: Sequence[Mapping[str, Any]],
    attribution_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    ready_checks: list[str] = []
    checks: list[dict[str, Any]] = []
    replay_metrics_ready = len(rows) > 0
    guardrail_ready = len(rows) >= 20
    comparison_ready = True
    attribution_ready = len(attribution_rows) > 0
    event_focus_count = int(attribution_receipt.get("event_focus_proposal_count") or 0)
    event_focus_ready = bool(str(attribution_receipt.get("event_focus_proposals_ref") or "").strip()) and event_focus_count > 0
    for check, ready, detail in (
        ("replay_metrics", replay_metrics_ready, f"{len(rows)} replay decision rows available"),
        ("guardrail_settlement", guardrail_ready, f"{len(rows)} replay decision rows checked against guardrails"),
        ("incumbent_comparison", comparison_ready, "incumbent comparison recorded as insufficient evidence for promotion"),
        ("residual_event_governance", attribution_ready, f"{len(attribution_rows)} M06 attribution rows linked"),
        ("residual_event_governance_event_focus_proposal", event_focus_ready, f"{event_focus_count} M06 event-focus proposals prepared"),
    ):
        if ready:
            ready_checks.append(check)
        checks.append({"check": check, "status": "passed" if ready else "failed", "detail": detail})
    return {"ready_checks": ready_checks, "checks": checks}


def _completed_training_fold(
    *,
    storage_root: Path,
    selected_target_symbol: str | None,
    selected_start_month: str | None = None,
    selected_end_month: str | None = None,
) -> dict[str, Any] | None:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return None
    selected = str(selected_target_symbol or "").strip().lower()
    selected_start = str(selected_start_month or "").strip()
    selected_end = str(selected_end_month or "").strip()
    candidates: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
        try:
            payload = _load_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if selected and f"_{selected}_" not in path.stem.lower():
            continue
        stages = payload.get("stages")
        if not isinstance(stages, list) or not base_stack_model_generation_splits_complete(stages):
            continue
        start_month = str(payload.get("start_month") or "")
        end_month = str(payload.get("end_month") or "")
        if not start_month or not end_month:
            continue
        if selected_start and start_month != selected_start:
            continue
        if selected_end and end_month != selected_end:
            continue
        target_symbol = _fold_state_target_symbol(path, payload)
        target_ref_part = _candidate_model_ref_target_part(target_symbol)
        candidates.append(
            (
                f"{start_month}:{end_month}:{path}",
                {
                    "start_month": start_month,
                    "end_month": end_month,
                    "state_path": str(path),
                    "fold_id": f"fold_{start_month}_{end_month}",
                    "target_symbol": target_symbol,
                    "candidate_model_ref": f"storage://trading-manager/model_group/{target_ref_part}/{start_month}_{end_month}",
                },
            )
        )
    return sorted(candidates, key=lambda item: item[0])[-1][1] if candidates else None


def _fold_state_target_symbol(path: Path, payload: Mapping[str, Any]) -> str | None:
    import re

    for key in ("target_symbol", "selected_target_symbol", "target_ref"):
        value = str(payload.get(key) or "").strip().upper()
        if value:
            return value
    match = re.match(r"^model_training_fold_state_([A-Za-z0-9.-]+)_\d{4}-\d{2}_\d{4}-\d{2}$", path.stem)
    return match.group(1).upper() if match else None


def _candidate_model_ref_target_part(target_symbol: str | None) -> str:
    target = str(target_symbol or "").strip().upper()
    if not target:
        return "unknown_target"
    return re.sub(r"[^A-Z0-9]+", "_", target).strip("_").lower()


def _replay_receipt_scope_status(*, replay_receipt: Mapping[str, Any], training_fold: Mapping[str, Any]) -> dict[str, Any]:
    candidate_model_ref = str(replay_receipt.get("candidate_model_ref") or "")
    target_refs = _string_set(replay_receipt.get("pre_replay_target_refs") or replay_receipt.get("target_refs") or replay_receipt.get("candidate_target_refs"))
    receipt_target_symbol = str(replay_receipt.get("target_symbol") or "").strip().upper()
    training_target_symbol = str(training_fold.get("target_symbol") or "").strip().upper()
    training_candidate_model_ref = str(training_fold.get("candidate_model_ref") or "")
    receipt_fold_id = str(replay_receipt.get("candidate_fold_id") or replay_receipt.get("fold_id") or "").strip()
    training_fold_id = str(training_fold.get("fold_id") or "").strip()
    receipt_fold_window = _candidate_model_ref_fold_window(candidate_model_ref)
    training_fold_window = _training_fold_window(training_fold)
    if "current_deterministic_crypto_policy" in candidate_model_ref:
        return {
            "compatible": False,
            "reason": "replay receipt used deterministic crypto placeholder policy instead of completed fold model artifacts",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
        }
    if training_candidate_model_ref and candidate_model_ref != training_candidate_model_ref:
        return {
            "compatible": False,
            "reason": "replay receipt candidate_model_ref does not match completed training fold candidate_model_ref",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
        }
    if training_target_symbol and not receipt_target_symbol:
        return {
            "compatible": False,
            "reason": "replay receipt does not declare target_symbol for completed training fold",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
        }
    if training_target_symbol and receipt_target_symbol != training_target_symbol:
        return {
            "compatible": False,
            "reason": f"replay receipt target {receipt_target_symbol} does not match completed training target {training_target_symbol}",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
        }
    asset_class_counts = replay_receipt.get("asset_class_counts")
    if not isinstance(asset_class_counts, Mapping):
        asset_class_counts = {}
    has_equity_or_option_scope = (
        any(ref for ref in target_refs)
        or int(asset_class_counts.get("us_equity") or 0) > 0
        or int(asset_class_counts.get("us_option") or 0) > 0
    )
    if has_equity_or_option_scope:
        portfolio_policy = replay_receipt.get("portfolio_replay_policy")
        if not isinstance(portfolio_policy, Mapping):
            portfolio_policy = {}
        if (
            str(replay_receipt.get("candidate_handoff_status") or "") != "available"
            or str(replay_receipt.get("candidate_handoff_source") or "") not in CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES
        ):
            return {
                "compatible": False,
                "reason": "replay receipt did not use the canonical fixed historical candidate universe",
                "candidate_model_ref": candidate_model_ref,
                "receipt_target_refs": sorted(target_refs),
            }
        if str(portfolio_policy.get("full_budget_replacement_policy") or "") != "continue_scanning_after_budget_full":
            return {
                "compatible": False,
                "reason": "replay receipt did not use the current full-budget replacement policy",
                "candidate_model_ref": candidate_model_ref,
                "receipt_target_refs": sorted(target_refs),
            }
        if (
            str(portfolio_policy.get("residual_cash_replacement_policy") or "")
            != "insufficient_cash_falls_through_to_replacement"
        ):
            return {
                "compatible": False,
                "reason": "replay receipt did not use the current residual-cash replacement policy",
                "candidate_model_ref": candidate_model_ref,
                "receipt_target_refs": sorted(target_refs),
            }
        if (
            str(portfolio_policy.get("portfolio_capacity_policy") or "")
            != "default_5_simultaneous_risk_slots_from_20pct_allocation"
            or int(portfolio_policy.get("max_positions") or 0) != 5
        ):
            return {
                "compatible": False,
                "reason": "replay receipt did not use the current five-slot portfolio-capacity policy",
                "candidate_model_ref": candidate_model_ref,
                "receipt_target_refs": sorted(target_refs),
            }
        if (
            str(portfolio_policy.get("position_sizing_policy") or "")
            != "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up"
        ):
            return {
                "compatible": False,
                "reason": "replay receipt did not use the current target-allocation-floor sizing policy",
                "candidate_model_ref": candidate_model_ref,
                "receipt_target_refs": sorted(target_refs),
            }
    if receipt_fold_id and training_fold_id and receipt_fold_id != training_fold_id:
        return {
            "compatible": False,
            "reason": f"replay receipt fold {receipt_fold_id} does not match completed training fold {training_fold_id}",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
        }
    if receipt_fold_window and training_fold_window and receipt_fold_window != training_fold_window:
        return {
            "compatible": False,
            "reason": (
                f"replay receipt fold {receipt_fold_window} does not match completed training fold {training_fold_window}"
            ),
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
        }
    return {
        "compatible": True,
        "reason": "replay receipt is eligible for fold-bound execution-component-graph replay evaluation",
        "candidate_model_ref": candidate_model_ref,
        "receipt_target_refs": sorted(target_refs),
    }


def _attribution_receipt_scope_status(
    *,
    replay_receipt: Mapping[str, Any],
    attribution_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    expected = {
        "replay_execution_run_id": str(replay_receipt.get("replay_execution_run_id") or "").strip(),
        "candidate_model_ref": str(replay_receipt.get("candidate_model_ref") or "").strip(),
        "candidate_fold_id": str(replay_receipt.get("candidate_fold_id") or replay_receipt.get("fold_id") or "").strip(),
        "candidate_training_target": str(
            replay_receipt.get("candidate_training_target") or replay_receipt.get("target_symbol") or ""
        )
        .strip()
        .upper(),
        "target_symbol": str(replay_receipt.get("target_symbol") or replay_receipt.get("candidate_training_target") or "")
        .strip()
        .upper(),
    }
    for key, expected_value in expected.items():
        if not expected_value:
            continue
        observed_value = str(attribution_receipt.get(key) or "").strip()
        if key in {"candidate_training_target", "target_symbol"}:
            observed_value = observed_value.upper()
        if not observed_value:
            return {
                "compatible": False,
                "reason": f"M06 attribution receipt is missing {key} for replay candidate scope",
                "field": key,
                "expected": expected_value,
            }
        if observed_value != expected_value:
            return {
                "compatible": False,
                "reason": f"M06 attribution receipt {key} does not match replay candidate scope",
                "field": key,
                "expected": expected_value,
                "observed": observed_value,
            }
    return {"compatible": True, "reason": "M06 attribution receipt scope matches replay candidate"}


def _replay_model_artifact_status(replay_receipt: Mapping[str, Any]) -> dict[str, Any]:
    artifact_ref = str(replay_receipt.get("after_cost_alpha_model_ref") or "").strip()
    if not artifact_ref:
        return {
            "compatible": False,
            "reason": "replay receipt does not declare after_cost_alpha_model_ref",
            "after_cost_alpha_model_ref": None,
        }
    artifact_path = Path(artifact_ref)
    if not artifact_path.exists():
        return {
            "compatible": False,
            "reason": "after-cost alpha model artifact is missing",
            "after_cost_alpha_model_ref": artifact_ref,
        }
    artifact = _load_json_object(artifact_path)
    training_summary = artifact.get("training_summary")
    if not isinstance(training_summary, Mapping):
        training_summary = {}
    training_mode = str(training_summary.get("training_mode") or "").strip()
    sample_count = _int_value(training_summary.get("sample_count"))
    if training_mode == "policy_bundle_no_supervised_fit" or sample_count <= 0:
        return {
            "compatible": False,
            "reason": "after-cost alpha artifact is a no-supervised-fit policy bundle, not a trained fold-specific model",
            "after_cost_alpha_model_ref": artifact_ref,
            "training_mode": training_mode or None,
            "sample_count": sample_count,
        }
    return {
        "compatible": True,
        "reason": "after-cost alpha artifact contains fold-specific supervised training evidence",
        "after_cost_alpha_model_ref": artifact_ref,
        "training_mode": training_mode or None,
        "sample_count": sample_count,
    }


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _candidate_model_ref_fold_window(candidate_model_ref: str) -> str | None:
    match = re.search(r"(\d{4}-\d{2}_\d{4}-\d{2})(?:$|[^0-9-])", candidate_model_ref)
    return match.group(1) if match else None


def _training_fold_window(training_fold: Mapping[str, Any]) -> str | None:
    start_month = str(training_fold.get("start_month") or "").strip()
    end_month = str(training_fold.get("end_month") or "").strip()
    return f"{start_month}_{end_month}" if start_month and end_month else None


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


def _latest_replay_execution_receipt(
    dataset_root: Path,
    *,
    training_fold: Mapping[str, Any] | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    replay_root = dataset_root / "replay_execution_runs"
    receipt_path, receipt = _latest_receipt(
        replay_root,
        "replay_execution_receipt.json",
        accepted_statuses=None,
        predicate=(
            (lambda candidate: _replay_receipt_scope_status(replay_receipt=candidate, training_fold=training_fold)["compatible"])
            if training_fold is not None
            else None
        ),
    )
    if receipt_path is not None or training_fold is None:
        return receipt_path, receipt

    latest_path, latest_receipt = _latest_receipt(replay_root, "replay_execution_receipt.json", accepted_statuses=None)
    if latest_path is None or latest_receipt is None:
        return None, None
    latest_scope_status = _replay_receipt_scope_status(replay_receipt=latest_receipt, training_fold=training_fold)
    if "does not match completed training fold" in str(latest_scope_status.get("reason") or ""):
        return None, None
    minimum_mtime = _state_mtime(training_fold)
    if minimum_mtime is not None:
        try:
            if latest_path.stat().st_mtime < minimum_mtime:
                return None, None
        except OSError:
            return None, None
    return latest_path, latest_receipt


def _latest_attribution_receipt(dataset_root: Path, *, decision_rows_ref: str) -> tuple[Path | None, dict[str, Any] | None]:
    attribution_root = dataset_root / "post_replay_attribution_runs"
    return _latest_receipt(
        attribution_root,
        "post_replay_attribution_receipt.json",
        accepted_statuses=M06_COMPLETE_STATUSES,
        required_field=("decision_rows_ref", decision_rows_ref),
        predicate=_is_residual_event_governance_receipt,
    )


def _latest_receipt(
    root: Path,
    filename: str,
    *,
    accepted_statuses: set[str] | None,
    required_field: tuple[str, str] | None = None,
    predicate: Callable[[Mapping[str, Any]], bool] | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if not root.exists():
        return None, None
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for path in sorted(root.glob(f"*/{filename}")):
        receipt = _load_optional_json_object(path)
        if receipt is None:
            continue
        if accepted_statuses is not None:
            status = str(receipt.get("status") or receipt.get("attribution_status") or "")
            if status not in accepted_statuses:
                continue
        if required_field is not None:
            key, expected = required_field
            if str(receipt.get(key) or "") != expected:
                continue
        if predicate is not None and not predicate(receipt):
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt.get("generated_at_utc") or path.parent.name)
        candidates.append((created, path, receipt))
    if not candidates:
        return None, None
    _created, path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return path, dict(receipt)


def _is_residual_event_governance_receipt(receipt: Mapping[str, Any]) -> bool:
    contract_type = str(receipt.get("contract_type") or "")
    if contract_type not in RESIDUAL_EVENT_GOVERNANCE_CONTRACT_TYPES:
        return False
    if receipt.get("event_evidence_consumed") is not True:
        return False
    event_observation_count = _safe_int(receipt.get("event_observation_count"))
    event_candidate_count = _safe_int(receipt.get("event_candidate_count"))
    if (event_observation_count or 0) <= 0 and (event_candidate_count or 0) <= 0:
        return False
    replay_review_status = str(receipt.get("replay_review_scope_status") or receipt.get("replay_review_status") or "")
    if replay_review_status not in {"succeeded", "complete", "completed", "passed"}:
        return False
    control_status = str(receipt.get("control_analysis_status") or receipt.get("controls_status") or "")
    if control_status not in {"succeeded", "complete", "completed", "passed"}:
        return False
    return True


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _state_mtime(training_fold: Mapping[str, Any]) -> float | None:
    state_path = Path(str(training_fold.get("state_path") or ""))
    try:
        return state_path.stat().st_mtime
    except OSError:
        return None


def _latest_promotion_review_artifacts(
    dataset_root: Path,
    *,
    replay_result_ref: str,
    residual_event_governance_receipt_ref: str,
    residual_event_governance_event_focus_proposals_ref: str,
    fold_id: str,
    target_symbol: str,
    candidate_model_ref: str,
    minimum_mtime: float | None = None,
) -> dict[str, Any] | None:
    review_root = dataset_root / "promotion_review_runs"
    if not review_root.exists():
        return None
    candidates: list[Path] = []
    for receipt_path in sorted(review_root.glob("*/model_group_evaluation_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        if str(receipt.get("replay_execution_receipt_ref") or "") != replay_result_ref:
            continue
        if str(receipt.get("residual_event_governance_receipt_ref") or "") != residual_event_governance_receipt_ref:
            continue
        if str(receipt.get("residual_event_governance_event_focus_proposals_ref") or "") != residual_event_governance_event_focus_proposals_ref:
            continue
        decision_path = receipt_path.parent / "promotion_eligibility_decision.json"
        decision = _load_optional_json_object(decision_path)
        if decision is None:
            continue
        if str(receipt.get("fold_id") or decision.get("fold_id") or "") != fold_id:
            continue
        if str(receipt.get("target_symbol") or decision.get("target_symbol") or "").strip().upper() != target_symbol.strip().upper():
            continue
        if str(receipt.get("candidate_model_ref") or decision.get("candidate_model_ref") or "") != candidate_model_ref:
            continue
        newest_artifact_mtime = max(receipt_path.stat().st_mtime, decision_path.stat().st_mtime)
        if minimum_mtime is not None and newest_artifact_mtime < minimum_mtime:
            continue
        candidates.append(receipt_path)
    if not candidates:
        return None
    return {"decision_path": str(max(candidates, key=lambda candidate: candidate.stat().st_mtime))}


def _replay_dataset_root(storage_root: Path, contract_id: str) -> Path:
    return storage_root.parent / "05_replay_datasets" / contract_id


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_optional_json_object(path: Path) -> dict[str, Any] | None:
    try:
        return _load_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _load_jsonl_objects(path: Path) -> Iterable[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, Mapping):
            yield dict(payload)


def _first_text(row: Mapping[str, Any], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value in (None, ""):
            continue
        text = str(value).strip().lower()
        if text:
            return text
    return ""


def _first_float(row: Mapping[str, Any], *names: str) -> float | None:
    for name in names:
        parsed = _finite_float(row.get(name))
        if parsed is not None:
            return parsed
    return None


def _normalize_side(value: str) -> str:
    if value in {"long", "bullish", "buy", "call"}:
        return "long"
    if value in {"short", "bearish", "sell_short", "put"}:
        return "short"
    if value in {"flat", "neutral", "none", "no_trade", "skip"}:
        return "flat"
    return "unknown"


def _reason_codes(row: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("reason_codes", "block_reason_codes", "decision_reason_codes"):
        value = row.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            values.extend(str(item).strip().lower() for item in value if str(item).strip())
        elif isinstance(value, str) and value.strip():
            values.extend(part.strip().lower() for part in re.split(r"[,;| ]+", value) if part.strip())
    hard_blocks = row.get("execution_hard_block_checks")
    if isinstance(hard_blocks, Mapping):
        values.extend(str(key).strip().lower() for key, value in hard_blocks.items() if value is True and str(key).strip())
        nested = hard_blocks.get("reason_codes")
        if isinstance(nested, Sequence) and not isinstance(nested, (str, bytes)):
            values.extend(str(item).strip().lower() for item in nested if str(item).strip())
    return values


def _value_counts(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value if value not in (None, "") else "unknown")
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _feature_namespace_leakage_columns(decision_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    forbidden_tokens = (
        "outcome",
        "label",
        "realized_return",
        "baseline_return",
        "excess_return",
        "cost_adjusted",
        "replay_",
        "eval_",
        "fill_status",
    )
    columns: set[str] = set()
    for row in decision_rows:
        for key in row:
            lowered = key.lower()
            if not lowered.startswith("feature_"):
                continue
            if any(token in lowered for token in forbidden_tokens):
                columns.add(key)
    return sorted(columns)


def _float(row: Mapping[str, Any], *names: str, default: float = 0.0) -> float:
    for name in names:
        value = row.get(name)
        if value in (None, ""):
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            return parsed
    return default


def _label(row: Mapping[str, Any]) -> int | None:
    if _has_missing_option_contract_path(row):
        return None
    value = row.get("outcome_label", row.get("label", row.get("realized_label")))
    text = str(value).strip().lower()
    if text in {"1", "true", "positive", "win", "profitable", "up", "success"}:
        return 1
    if text in {"0", "false", "negative", "loss", "unprofitable", "down", "failure"}:
        return 0
    realized = _float(row, "realized_return", "net_return", "candidate_return", default=float("nan"))
    if math.isfinite(realized):
        return 1 if realized > 0 else 0
    return None


def _has_missing_option_contract_path(row: Mapping[str, Any]) -> bool:
    selected_option = str(row.get("selected_option_contract_ref") or "").strip()
    path_status = str(row.get("option_contract_path_status") or "").strip().lower()
    return bool(selected_option) and path_status == "missing"


def _score(row: Mapping[str, Any]) -> float | None:
    for name in ("prediction_score", "predicted_score", "probability", "confidence_score", "alpha_score", "rank_score"):
        value = row.get(name)
        if value in (None, ""):
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            return parsed
    return None


def _auroc(labels: Sequence[int], scores: Sequence[float]) -> float | None:
    pairs = [(score, label) for label, score in zip(labels, scores, strict=True)]
    positives = sum(1 for _score, label in pairs if label == 1)
    negatives = len(pairs) - positives
    if positives == 0 or negatives == 0:
        return None
    pairs.sort(key=lambda item: item[0])
    rank_sum = 0.0
    for rank, (_score_value, label) in enumerate(pairs, start=1):
        if label == 1:
            rank_sum += rank
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _max_drawdown(returns: Sequence[float]) -> float:
    peak = 0.0
    current = 0.0
    max_dd = 0.0
    for value in returns:
        current += value
        peak = max(peak, current)
        max_dd = min(max_dd, current - peak)
    return max_dd


def _return_path_ohlc(returns: Sequence[float]) -> dict[str, float]:
    current = 0.0
    high = 0.0
    low = 0.0
    for value in returns:
        current += float(value)
        high = max(high, current)
        low = min(low, current)
    return {
        "open": 1.0,
        "high": _round_metric(1.0 + high),
        "low": _round_metric(1.0 + low),
        "close": _round_metric(1.0 + current),
    }


def _payoff_ratio(returns: Sequence[float]) -> float | None:
    wins = [value for value in returns if value > 0]
    losses = [value for value in returns if value <= 0]
    if not wins or not losses:
        return None
    return (sum(wins) / len(wins)) / abs(sum(losses) / len(losses))


def _stable_token(*parts: object) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


__all__ = ["MODEL_GROUP_EVALUATION_CHECKS", "run_model_group_evaluation_if_ready"]

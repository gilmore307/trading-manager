"""Manager-owned model-group evaluation execution.

The dashboard can see when replay and Layer 10 attribution are ready, but the
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

from .model_group_replay import DEFAULT_REPLAY_CONTRACT_ID
from .model_training_workflow import base_stack_model_generation_splits_complete
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
MODEL_GROUP_EVALUATION_CHECKS = (
    "replay_metrics",
    "guardrail_settlement",
    "incumbent_comparison",
    "layer_10_attribution",
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


def run_model_group_evaluation_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    selected_target_symbol: str | None = None,
    now_utc: datetime | None = None,
    force: bool = False,
    call_agent_review: bool = True,
    agent_reviewer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    codex_bin: str = "codex",
    codex_model: str | None = None,
    codex_timeout_seconds: int = DEFAULT_PROMOTION_REVIEW_CODEX_TIMEOUT_SECONDS,
) -> SchedulerDecision | None:
    """Run one model-group evaluation build when Layer 10 evidence is complete."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    replay_receipt_path, replay_receipt = _latest_replay_execution_receipt(dataset_root)
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
    training_fold = _completed_training_fold(storage_root=storage_root, selected_target_symbol=selected_target_symbol)
    if training_fold is None:
        return None
    if not force and _latest_promotion_review_artifacts(
        dataset_root,
        replay_result_ref=str(replay_receipt_path),
        minimum_mtime=_state_mtime(training_fold),
    ) is not None:
        return None
    attribution_rows_path = Path(str(attribution_receipt.get("attribution_rows_ref") or ""))
    if not attribution_rows_path.exists():
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

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
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
    rows = tuple(_load_jsonl_objects(decision_rows_path))
    attribution_rows = tuple(_load_jsonl_objects(attribution_rows_path))
    check_summary = _evaluation_check_summary(rows=rows, attribution_rows=attribution_rows)

    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_evaluation_ready",
            reason="model-group evaluation is ready to build replay metrics, guardrails, incumbent comparison, and Layer 10 attribution checks",
            selected_work="model_group.evaluation",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "expected_checks": list(MODEL_GROUP_EVALUATION_CHECKS),
                "ready_checks": check_summary["ready_checks"],
            },
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
            replay_contract_ref=f"trading-evaluation/replays/{contract_id}.json",
            replay_result_ref=str(replay_receipt_path),
            decision_rows=rows,
            created_at_utc=now.isoformat(),
        )
        review = _build_promotion_review(
            settlement=settlement,
            settlement_ref=str(settlement_path),
            benchmark_contract_ref=f"trading-evaluation/replays/{contract_id}.json",
            layer_10_attribution_ref=str(attribution_receipt_path),
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
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "evaluation_checks": check_summary["checks"],
            "ready_checks": check_summary["ready_checks"],
            "expected_check_count": len(MODEL_GROUP_EVALUATION_CHECKS),
            "ready_check_count": len(set(check_summary["ready_checks"]).intersection(MODEL_GROUP_EVALUATION_CHECKS)),
            "replay_execution_receipt_ref": str(replay_receipt_path),
            "layer_10_attribution_receipt_ref": str(attribution_receipt_path),
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
    baseline_comparison_diagnostics = _baseline_comparison_diagnostics(
        labels=labels,
        scores=scores,
        net_total=net_total,
        baseline_total=baseline_total,
    )
    gate_failures: list[str] = []
    if len(decision_rows) < 20:
        gate_failures.append("decision_row_count_below_minimum")
    if net_total <= baseline_total:
        gate_failures.append("net_return_not_above_baseline")
    if auroc is None:
        gate_failures.append("auroc_unavailable")
    elif auroc < 0.53:
        gate_failures.append("auroc_below_minimum")
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
        "predictive_diagnostics": predictive_diagnostics,
        "calibration_diagnostics": calibration_diagnostics,
        "economic_diagnostics": economic_diagnostics,
        "data_integrity_diagnostics": data_integrity_diagnostics,
        "temporal_stability_diagnostics": temporal_stability_diagnostics,
        "baseline_comparison_diagnostics": baseline_comparison_diagnostics,
        "uncertainty_diagnostics": {
            "available": False,
            "reason": "block bootstrap confidence intervals require multiple completed comparable folds",
        },
        "feature_diagnostics": feature_diagnostics,
    }
    return {
        "contract_type": "fold_settlement_run",
        "fold_settlement_run_id": settlement_id,
        "fold_id": fold_id,
        "target_symbol": target_symbol,
        "candidate_model_ref": candidate_model_ref,
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
        "fold_stack_status": "complete_layer_01_10",
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
        labels = [int(row["label"]) for row in rows]
        scores = [float(row["score"]) for row in rows]
        returns = [float(row["net_return"]) for row in rows]
        slices.append(
            {
                "month": month,
                "row_count": len(rows),
                "base_rate": _round_metric(sum(labels) / len(labels)) if labels else None,
                "auroc": _auroc(labels, scores),
                "brier_score": _brier_score(labels, scores),
                "net_return_total": _round_metric(sum(returns)),
                "max_drawdown": _round_metric(_max_drawdown(returns)),
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
        "silhouette": {"outcome_label": None, "decision_action": None},
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
        "target_ref": str(source.get("target_ref") or source.get("instrument_ref") or ""),
        "timestamp": str(source.get("timestamp") or ""),
    }


def _squared_distance(left: Sequence[float], right: Sequence[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right, strict=True))


def _round_metric(value: float) -> float:
    return round(float(value), 6)


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
    action = str(row.get("action") or row.get("decision") or row.get("decision_action") or "").strip().lower()
    return action not in {"", "hold", "skip", "no_trade", "reject_entry_thesis", "defer_entry_thesis", "simulated_rejected"}


def _build_promotion_review(
    *,
    settlement: Mapping[str, Any],
    settlement_ref: str,
    benchmark_contract_ref: str,
    layer_10_attribution_ref: str,
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
        layer_10_attribution_ref=layer_10_attribution_ref,
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
    layer_10_attribution_ref: str,
    created_at_utc: str,
) -> dict[str, Any]:
    metrics = settlement.get("metrics") if isinstance(settlement.get("metrics"), Mapping) else {}
    gate_failures = [str(item) for item in settlement.get("gate_failures") or []]
    blocking_issues = []
    if gate_failures:
        blocking_issues.append("settlement gate failures: " + ", ".join(gate_failures))
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
        "layer_10_attribution_ref": layer_10_attribution_ref,
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
        },
        "material_improvements": [f"settlement row count {metrics.get('decision_row_count')} is available"],
        "material_regressions": gate_failures,
        "blocking_issues": blocking_issues,
        "required_followups": [
            "provide blinded model_a/model_b comparison evidence on the frozen replay contract",
            "attach candidate config and rollback refs before shadow-readiness review",
            "attach first-run/query-count evidence for this candidate lineage",
        ],
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
    decision_status = _promotion_decision_status(review.get("recommendation"))
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
        "fold_stack_status": str(settlement.get("fold_stack_status") or "complete_layer_01_10"),
        "guardrail_status": "passed" if review.get("hard_guardrail_status") == "passed" else "failed",
        "incumbent_comparison_ref": "",
        "incumbent_comparison_status": "",
        "agent_review_ref": review_ref,
        "agent_review_recommendation": str(review.get("recommendation") or ""),
        "first_model_bootstrap": False,
        "bootstrap_baseline_ref": "",
        "created_at_utc": created_at_utc,
    }


def _promotion_decision_status(recommendation: Any) -> str:
    if recommendation == "eligible_for_shadow":
        return "eligible"
    if recommendation == "failed":
        return "rejected"
    return "deferred"


def _evaluation_check_summary(*, rows: Sequence[Mapping[str, Any]], attribution_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ready_checks: list[str] = []
    checks: list[dict[str, Any]] = []
    replay_metrics_ready = len(rows) > 0
    guardrail_ready = len(rows) >= 20
    comparison_ready = True
    attribution_ready = len(attribution_rows) > 0
    for check, ready, detail in (
        ("replay_metrics", replay_metrics_ready, f"{len(rows)} replay decision rows available"),
        ("guardrail_settlement", guardrail_ready, f"{len(rows)} replay decision rows checked against guardrails"),
        ("incumbent_comparison", comparison_ready, "incumbent comparison recorded as insufficient evidence for promotion"),
        ("layer_10_attribution", attribution_ready, f"{len(attribution_rows)} Layer 10 attribution rows linked"),
    ):
        if ready:
            ready_checks.append(check)
        checks.append({"check": check, "status": "passed" if ready else "failed", "detail": detail})
    return {"ready_checks": ready_checks, "checks": checks}


def _completed_training_fold(*, storage_root: Path, selected_target_symbol: str | None) -> dict[str, Any] | None:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return None
    selected = str(selected_target_symbol or "").strip().lower()
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
        statuses = [stage.get("status") for stage in stages if isinstance(stage, Mapping)]
        if not statuses or any(status not in {"succeeded", "not_applicable"} for status in statuses):
            continue
        start_month = str(payload.get("start_month") or "")
        end_month = str(payload.get("end_month") or "")
        if not start_month or not end_month:
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
    return sorted(candidates, key=lambda item: item[0])[0][1] if candidates else None


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
    target_symbol = str(training_fold.get("target_symbol") or "").strip().upper()
    target_refs = _string_set(replay_receipt.get("target_refs") or replay_receipt.get("candidate_target_refs"))
    receipt_fold_id = str(replay_receipt.get("candidate_fold_id") or replay_receipt.get("fold_id") or "").strip()
    training_fold_id = str(training_fold.get("fold_id") or "").strip()
    if "current_deterministic_crypto_policy" in candidate_model_ref:
        return {
            "compatible": False,
            "reason": "replay receipt used deterministic crypto placeholder policy instead of completed fold model artifacts",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
            "training_target_symbol": target_symbol,
        }
    if receipt_fold_id and training_fold_id and receipt_fold_id != training_fold_id:
        return {
            "compatible": False,
            "reason": f"replay receipt fold {receipt_fold_id} does not match completed training fold {training_fold_id}",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
            "training_target_symbol": target_symbol,
        }
    return {
        "compatible": True,
        "reason": "replay receipt is eligible for fold-bound free-trading evaluation",
        "candidate_model_ref": candidate_model_ref,
        "receipt_target_refs": sorted(target_refs),
        "training_target_symbol": target_symbol,
    }


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


def _latest_replay_execution_receipt(dataset_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    replay_root = dataset_root / "replay_execution_runs"
    return _latest_receipt(replay_root, "replay_execution_receipt.json", accepted_statuses=None)


def _latest_attribution_receipt(dataset_root: Path, *, decision_rows_ref: str) -> tuple[Path | None, dict[str, Any] | None]:
    attribution_root = dataset_root / "post_replay_attribution_runs"
    return _latest_receipt(
        attribution_root,
        "post_replay_attribution_receipt.json",
        accepted_statuses={"succeeded", "complete", "completed"},
        required_field=("decision_rows_ref", decision_rows_ref),
    )


def _latest_receipt(
    root: Path,
    filename: str,
    *,
    accepted_statuses: set[str] | None,
    required_field: tuple[str, str] | None = None,
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
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt.get("generated_at_utc") or path.parent.name)
        candidates.append((created, path, receipt))
    if not candidates:
        return None, None
    _created, path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return path, dict(receipt)


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
    minimum_mtime: float | None = None,
) -> dict[str, Any] | None:
    review_root = dataset_root / "promotion_review_runs"
    if not review_root.exists():
        return None
    candidates: list[Path] = []
    for path in sorted(review_root.glob("*/promotion_eligibility_decision.json")):
        payload = _load_optional_json_object(path)
        if payload is None or str(payload.get("replay_validation_ref") or "") != replay_result_ref:
            continue
        if minimum_mtime is not None and path.stat().st_mtime < minimum_mtime:
            continue
        candidates.append(path)
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

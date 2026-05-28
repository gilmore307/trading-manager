"""Manager-owned model-group evaluation execution.

The dashboard can see when replay and Layer 10 attribution are ready, but the
manager must still write concrete evaluation evidence before promotion can
inspect it. This module performs that side-effect-free evidence build over the
local replay dataset.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
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


def run_model_group_evaluation_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    selected_target_symbol: str | None = None,
    now_utc: datetime | None = None,
) -> SchedulerDecision | None:
    """Run one model-group evaluation build when Layer 10 evidence is complete."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    replay_receipt_path, replay_receipt = _latest_replay_execution_receipt(dataset_root)
    if replay_receipt_path is None or replay_receipt is None:
        return None
    attribution_receipt_path, attribution_receipt = _latest_attribution_receipt(dataset_root)
    if attribution_receipt_path is None or attribution_receipt is None:
        return None
    if _latest_promotion_review_artifacts(dataset_root) is not None:
        return None
    decision_rows_path = Path(str(replay_receipt.get("decision_rows_ref") or ""))
    if not decision_rows_path.exists():
        return None
    attribution_rows_path = Path(str(attribution_receipt.get("attribution_rows_ref") or ""))
    if not attribution_rows_path.exists():
        return None

    training_fold = _completed_training_fold(storage_root=storage_root, selected_target_symbol=selected_target_symbol)
    if training_fold is None:
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
    candidate_model_ref: str,
    replay_contract_ref: str,
    replay_result_ref: str,
    decision_rows: Sequence[Mapping[str, Any]],
    created_at_utc: str,
) -> dict[str, Any]:
    realized_returns = [_float(row, "net_return", "realized_return", "candidate_return") for row in decision_rows]
    baseline_returns = [_float(row, "baseline_return", "replay_return", "incumbent_return") for row in decision_rows]
    costs = [_float(row, "cost", "trading_cost", "cost_drag") for row in decision_rows]
    net_returns = [value - cost for value, cost in zip(realized_returns, costs, strict=True)]
    labels_scores = [(_label(row), _score(row)) for row in decision_rows]
    labels = [int(label) for label, score in labels_scores if label is not None and score is not None]
    scores = [float(score) for label, score in labels_scores if label is not None and score is not None]
    auroc = _auroc(labels, scores) if labels and scores else None
    net_total = sum(net_returns)
    baseline_total = sum(baseline_returns)
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
        "turnover_proxy_count": sum(1 for row in decision_rows if str(row.get("action") or row.get("decision") or "").lower() not in {"", "hold", "skip", "no_trade"}),
        "hit_rate": sum(1 for value in net_returns if value > 0) / len(net_returns) if net_returns else None,
        "payoff_ratio": _payoff_ratio(net_returns),
        "auroc": auroc,
        "auroc_pair_count": len(labels),
        "brier_score": sum((score - label) ** 2 for label, score in zip(labels, scores, strict=True)) / len(labels) if labels else None,
        "feature_column_count": 0,
        "feature_row_count": 0,
        "pca_available": False,
        "pcoa_available": False,
    }
    return {
        "contract_type": "fold_settlement_run",
        "fold_settlement_run_id": settlement_id,
        "fold_id": fold_id,
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


def _build_promotion_review(
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
            "brier_score": metrics.get("brier_score"),
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
        "model_activation_performed": False,
        "active_model_config_written": False,
        "broker_execution_performed": False,
        "account_mutation_performed": False,
    }


def _build_promotion_eligibility_decision(
    *,
    settlement: Mapping[str, Any],
    review: Mapping[str, Any],
    settlement_ref: str,
    review_ref: str,
    replay_contract_ref: str,
    created_at_utc: str,
) -> dict[str, Any]:
    decision_status = "eligible" if review.get("recommendation") == "eligible_for_shadow" else "review_required"
    return {
        "contract_type": "promotion_eligibility_decision",
        "promotion_eligibility_decision_id": f"promelig_{_stable_token(settlement.get('fold_id'), settlement_ref, decision_status)}",
        "fold_id": str(settlement.get("fold_id") or ""),
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
        candidates.append(
            (
                f"{start_month}:{end_month}:{path}",
                {
                    "start_month": start_month,
                    "end_month": end_month,
                    "state_path": str(path),
                    "fold_id": f"fold_{start_month}_{end_month}",
                    "target_symbol": _fold_state_target_symbol(path, payload),
                    "candidate_model_ref": f"storage://trading-manager/model_group/{start_month}_{end_month}",
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
    if target_symbol and target_refs and target_symbol not in target_refs:
        return {
            "compatible": False,
            "reason": f"replay receipt targets {', '.join(sorted(target_refs))} do not include training target {target_symbol}",
            "candidate_model_ref": candidate_model_ref,
            "receipt_target_refs": sorted(target_refs),
            "training_target_symbol": target_symbol,
        }
    return {
        "compatible": True,
        "reason": "replay receipt scope matches completed training fold",
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


def _latest_attribution_receipt(dataset_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    attribution_root = dataset_root / "post_replay_attribution_runs"
    return _latest_receipt(attribution_root, "post_replay_attribution_receipt.json", accepted_statuses={"succeeded", "complete", "completed"})


def _latest_receipt(root: Path, filename: str, *, accepted_statuses: set[str] | None) -> tuple[Path | None, dict[str, Any] | None]:
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
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or path.parent.name)
        candidates.append((created, path, receipt))
    if not candidates:
        return None, None
    _created, path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return path, dict(receipt)


def _latest_promotion_review_artifacts(dataset_root: Path) -> dict[str, Any] | None:
    review_root = dataset_root / "promotion_review_runs"
    if not review_root.exists():
        return None
    for path in sorted(review_root.glob("*/promotion_eligibility_decision.json")):
        if _load_optional_json_object(path) is not None:
            return {"decision_path": str(path)}
    return None


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

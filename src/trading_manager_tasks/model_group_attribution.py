"""Manager-owned replay review execution.

Replay review is the local, replay-derived review task that runs immediately
after model-group replay and before M06 ResidualEventGovernance attribution. It
converts replay failure/miss rows into durable review units and records the
ledger contract for later hierarchical component analysis. It is deliberately
not M06 event attribution because it does not consume point-in-time event
observations, event candidates, controls, co-events, or confounder evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections.abc import Iterable as IterableABC
from collections.abc import Mapping as MappingABC
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .fold_naming import parse_model_worker_fold_id
from .model_group_layer_attribution import build_model_group_layer_attribution
from .model_group_replay import CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES, DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE = "post_replay_review_receipt"
REPLAY_REVIEW_ROW_CONTRACT_TYPE = "post_replay_review_row"
REPLAY_LAYER_REVIEW_ROW_CONTRACT_TYPE = "post_replay_layer_decision_review_row"
REPLAY_REVIEW_DATA_REQUIREMENT_CONTRACT_TYPE = "post_replay_review_data_requirement"
REPLAY_LAYER_REVIEW_LAYERS = (
    ("model_01_background_context", "M01 Background Context"),
    ("model_02_target_state", "M02 Target State"),
    ("model_03_event_state", "M03 Event State"),
    ("model_04_unified_decision", "M04 Unified Decision"),
    ("model_05_option_expression", "M05 Option Expression"),
)
EXCLUDED_REPLAY_LAYER_REVIEW_LAYERS = ("model_06_residual_event_governance",)
REPLAY_LAYER_REVIEW_METHODS = {
    "model_01_background_context": {
        "metric_family": "background_context_state_quality",
        "analysis_method": "point_in_time_context_quality_threshold_review",
        "decision_time_input_fields": [
            "state_quality_score",
            "market_risk_stress_score",
            "transition_risk_score",
        ],
        "post_replay_label_fields": [],
    },
    "model_02_target_state": {
        "metric_family": "target_candidate_selection_quality",
        "analysis_method": "same_timestamp_candidate_rank_and_tradability_review",
        "decision_time_input_fields": [
            "model_rank_within_timestamp",
            "target_direction_score_1D",
            "tradability_score_1D",
            "target_trend_quality_score_1D",
        ],
        "post_replay_label_fields": [],
    },
    "model_03_event_state": {
        "metric_family": "event_state_risk_pressure_quality",
        "analysis_method": "point_in_time_event_pressure_threshold_review",
        "decision_time_input_fields": [
            "event_uncertainty_score_1D",
            "event_entry_block_pressure_score_1D",
            "event_strategy_disable_pressure_score_1D",
            "event_path_risk_score_1D",
        ],
        "post_replay_label_fields": [],
    },
    "model_04_unified_decision": {
        "metric_family": "underlying_action_quality",
        "analysis_method": "post_replay_directional_underlying_label_review",
        "decision_time_input_fields": [
            "resolved_underlying_action_type",
            "resolved_action_side",
            "prediction_score",
        ],
        "post_replay_label_fields": ["directional_underlying_return", "realized_return", "baseline_return"],
    },
    "model_05_option_expression": {
        "metric_family": "option_expression_quality",
        "analysis_method": "selected_option_expression_return_and_direction_consistency_review",
        "decision_time_input_fields": [
            "selected_expression_type",
            "selected_contract_ref",
            "eligible_candidate_count",
            "top_contract_fit_score",
        ],
        "post_replay_label_fields": ["realized_return", "baseline_return", "fill_status"],
    },
}


def run_model_group_replay_review_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    replay_execution_run_id: str | None = None,
    execute: bool = True,
    python_executable: str = sys.executable,
    max_review_rows: int | None = None,
    now_utc: datetime | None = None,
    force: bool = False,
    allow_partial_replay: bool = False,
) -> SchedulerDecision | None:
    """Run one replay review task when replay is complete."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    replay_receipt = _latest_replay_execution_receipt(dataset_root, replay_execution_run_id=replay_execution_run_id)
    if replay_receipt is None:
        return None
    decision_rows_path = Path(str(replay_receipt.get("decision_rows_ref") or ""))
    if not decision_rows_path.exists():
        return None
    if not force and _latest_complete_replay_review_receipt(dataset_root, decision_rows_ref=str(decision_rows_path)) is not None:
        return None
    expected_months = _expected_replay_months(dataset_root)
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "")
    ready_months = _ready_replay_months(dataset_root, replay_run_id=replay_run_id)
    completed_month_count = _int_value(replay_receipt.get("completed_replay_month_count"))
    receipt_declares_full_completion = expected_months > 0 and completed_month_count >= expected_months
    replay_complete = expected_months <= 0 or len(ready_months) >= expected_months
    if receipt_declares_full_completion and _replay_receipt_full_completion_scope(replay_receipt):
        replay_complete = True
    if not replay_complete and not allow_partial_replay:
        return None
    if not replay_complete:
        replay_month = str(replay_receipt.get("replay_month") or "").strip()
        if not ready_months or (replay_month and replay_month not in ready_months):
            return None
        if max_review_rows is not None:
            return None
        if not force:
            return None
    if expected_months > 0 and len(ready_months) < expected_months and not receipt_declares_full_completion and not allow_partial_replay:
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id = "post_replay_review_" + now.strftime("%Y%m%dT%H%M%SZ")
    command = [
        python_executable,
        "scripts/tasks/run_model_group_replay_review.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]
    if replay_execution_run_id:
        command.extend(["--replay-execution-run-id", replay_execution_run_id])
    if max_review_rows is not None:
        command.extend(["--max-review-rows", str(max_review_rows)])
    if allow_partial_replay:
        command.append("--allow-partial-replay")
    requirements = tuple(_review_data_requirements(decision_rows_path, max_rows=max_review_rows))
    if requirements:
        requirements_root = dataset_root / "post_replay_review_requirements" / run_id
        requirements_path = requirements_root / "replay_review_data_requirements.jsonl"
        if execute:
            requirements_root.mkdir(parents=True, exist_ok=True)
            _write_jsonl(requirements_path, requirements)
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_review_data_required",
            reason="replay review requires additional replay outcome data before hindsight scoring can be completed",
            selected_work="model_group.replay_review",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "decision_rows_ref": str(decision_rows_path),
                "requirements_artifact_ref": str(requirements_path) if execute else None,
                "required_replay_review_data_count": len(requirements),
                "required_data_kinds": sorted({kind for item in requirements for kind in item["required_data_kinds"]}),
                "acquisition_routes": sorted({str(item["acquisition_route"]) for item in requirements}),
                "resume_stage_id": "model_group.replay",
                "required_next_step": "repair or acquire the required replay outcome data through the replay-owned provider-gated stages, then rerun model_group.replay and model_group.replay_review",
            },
        )
    if not _jsonl_has_any_object(decision_rows_path):
        existing_rejection = _existing_no_decision_promotion_rejection_for_replay(
            dataset_root=dataset_root,
            replay_receipt=replay_receipt,
        )
        if existing_rejection is not None:
            return None
        rejection_path = _write_no_decision_promotion_rejection(
            dataset_root=dataset_root,
            storage_root=storage_root,
            replay_receipt=replay_receipt,
            decision_rows_path=decision_rows_path,
            now=now,
            execute=execute,
        )
        if rejection_path is not None:
            executing_rejection = execute
            return _decision(
                now=now,
                decision_status="executed" if executing_rejection else "ready",
                reason_code=(
                    "model_group_replay_no_decisions_rejected"
                    if executing_rejection
                    else "model_group_replay_no_decisions_rejection_ready"
                ),
                reason=(
                    "model-group replay completed without decision rows; "
                    + (
                        "wrote terminal promotion rejection evidence so the fold lane can advance"
                        if executing_rejection
                        else "terminal promotion rejection evidence is ready to write"
                    )
                ),
                selected_work="model_group.replay_review",
                command=command,
                execution_summary={
                    "contract_id": contract_id,
                    "dataset_root": str(dataset_root),
                    "decision_rows_ref": str(decision_rows_path),
                    "replay_execution_run_id": replay_run_id,
                    "completed_replay_month_count": completed_month_count,
                    "ready_replay_month_count": len(ready_months),
                    "promotion_eligibility_decision_ref": str(rejection_path),
                    "terminal_decision_status": "rejected",
                    "terminal_decision_reason_code": "no_replay_decisions",
                    "required_next_step": "advance to the next eligible fold after the terminal no-decision replay rejection",
                },
            )
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_review_no_decision_rows",
            reason=(
                "model-group replay completed without decision rows; candidate replay must be rerun or rejected "
                "before replay review can produce attribution evidence"
            ),
            selected_work="model_group.replay_review",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "decision_rows_ref": str(decision_rows_path),
                "replay_execution_run_id": replay_run_id,
                "completed_replay_month_count": completed_month_count,
                "ready_replay_month_count": len(ready_months),
                "required_next_step": (
                    "rerun model_group.replay with a trained fold-scoped candidate scorer; if replay still "
                    "produces no decisions, reject the candidate instead of opening the next fold"
                ),
            },
        )
    output_root = dataset_root / "post_replay_review_runs" / run_id
    review_rows_path = output_root / "replay_review_rows.jsonl"
    layer_review_rows_path = output_root / "replay_layer_decision_review_rows.jsonl"
    receipt_path = output_root / "post_replay_review_receipt.json"
    performance_summary_path = output_root / "replay_review_performance_summary.json"
    layer_attribution_root = output_root / "layer_attribution"

    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_replay_review_ready",
            reason="model-group replay is complete; replay review is ready",
            selected_work="model_group.replay_review",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "decision_rows_ref": str(decision_rows_path),
                "expected_replay_review_rows": "not_counted_during_readiness_probe",
            },
        )

    decision_rows = tuple(_load_jsonl_objects(decision_rows_path))
    review_rows = tuple(_build_review_rows(decision_rows_path, max_rows=max_review_rows))
    replay_receipt_path = (
        dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json"
        if replay_run_id
        else None
    )
    model_candidate_selection_trace_path = _model_candidate_selection_trace_path(replay_receipt, dataset_root=dataset_root)
    trace_rows = (
        tuple(_load_jsonl_objects(model_candidate_selection_trace_path))
        if model_candidate_selection_trace_path is not None
        else ()
    )
    layer_review_rows = tuple(
        _build_layer_review_rows(
            decision_rows=decision_rows,
            trace_rows=trace_rows,
            max_decision_rows=max_review_rows,
        )
    )
    layer_review_summary = _layer_review_diagnostic_summary(layer_review_rows)
    performance_summary = _replay_review_performance_summary(
        decision_rows=decision_rows,
        trace_rows=trace_rows,
        replay_receipt=replay_receipt,
    )
    review_summary = _review_diagnostic_summary(review_rows)
    if replay_complete:
        completion_scope = "bounded_diagnostic" if max_review_rows is not None else "full_replay_review"
    else:
        completion_scope = "completed_replay_run_diagnostic"
    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_replay_review:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.replay_review.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        output_root.mkdir(parents=True, exist_ok=True)
        _write_jsonl(review_rows_path, review_rows)
        _write_jsonl(layer_review_rows_path, layer_review_rows)
        performance_summary_path.write_text(
            json.dumps(performance_summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        layer_attribution_report = build_model_group_layer_attribution(
            decision_rows_path=decision_rows_path,
            output_dir=layer_attribution_root,
            replay_receipt_path=(
                replay_receipt_path
                if replay_receipt_path is not None and replay_receipt_path.exists()
                else None
            ),
            model_candidate_selection_trace_path=model_candidate_selection_trace_path,
            layer_review_rows=layer_review_rows,
            run_id=f"{run_id}_layer_attribution",
            now_utc=now,
        )
        receipt = {
            "contract_type": REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE,
            "status": "succeeded",
            "stage_id": "model_group.replay_review",
            "model_surface": "post_replay_review",
            "run_id": run_id,
            "contract_id": contract_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "decision_rows_ref": str(decision_rows_path),
            "replay_execution_run_id": replay_run_id,
            "candidate_model_ref": replay_receipt.get("candidate_model_ref"),
            "candidate_fold_id": replay_receipt.get("candidate_fold_id"),
            "candidate_training_target": replay_receipt.get("candidate_training_target"),
            "target_symbol": replay_receipt.get("target_symbol") or replay_receipt.get("candidate_training_target"),
            "replay_execution_receipt_ref": str(dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json")
            if replay_run_id
            else None,
            "review_rows_ref": str(review_rows_path),
            "layer_review_rows_ref": str(layer_review_rows_path),
            "replay_review_performance_summary_ref": str(performance_summary_path),
            "replay_review_performance_summary": performance_summary["summary"],
            "layer_attribution_report_ref": str(layer_attribution_root / "layer_attribution_report.json"),
            "layer_attribution_summary": {
                "row_scope": layer_attribution_report.get("row_scope"),
                "model_candidate_selection_summary": layer_attribution_report.get("model_candidate_selection_summary"),
                "pre_option_candidate_quality_summary": layer_attribution_report.get(
                    "pre_option_candidate_quality_summary"
                ),
                "operation_component_metrics_summary": layer_attribution_report.get(
                    "operation_component_metrics_summary"
                ),
                "operation_mechanism_contract_packet_summary": layer_attribution_report.get(
                    "operation_mechanism_contract_packet_summary"
                ),
            },
            "replay_review_completion_scope": completion_scope,
            "max_review_rows": max_review_rows,
            "expected_review_count": len(review_rows),
            "reviewed_failure_count": len(review_rows),
            "processed_review_count": len(review_rows),
            "review_sequence": ["eligibility_ledger", "decision_ledger", "outcome_ledger"],
            "review_scope": "post_replay_component_funnel_review",
            "replay_review_diagnostic_summary": review_summary,
            "layer_review_scope": "model_layers_m01_m05_path_conditioned_replay_review",
            "layer_review_included_layers": [layer_id for layer_id, _label in REPLAY_LAYER_REVIEW_LAYERS],
            "layer_review_excluded_layers": list(EXCLUDED_REPLAY_LAYER_REVIEW_LAYERS),
            "layer_review_row_count": len(layer_review_rows),
            "layer_review_diagnostic_summary": layer_review_summary,
            "cause_family_contract": ["data_insufficiency", "execution_connection_failure", "model_mechanism_defect"],
            "residual_event_governance_status": "not_performed",
            "event_evidence_consumed": False,
            "event_observation_count": 0,
            "event_candidate_count": 0,
            "control_analysis_performed": False,
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_replay_review_executed",
        reason="executed side-effect-free replay review over replay failures and missed opportunities",
        selected_work="model_group.replay_review",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "decision_rows_ref": str(decision_rows_path),
            "post_replay_review_receipt": str(receipt_path),
            "replay_execution_run_id": replay_run_id,
            "candidate_model_ref": replay_receipt.get("candidate_model_ref"),
            "candidate_fold_id": replay_receipt.get("candidate_fold_id"),
            "candidate_training_target": replay_receipt.get("candidate_training_target"),
            "target_symbol": replay_receipt.get("target_symbol") or replay_receipt.get("candidate_training_target"),
            "review_rows_ref": str(review_rows_path),
            "reviewed_failure_count": len(review_rows),
            "layer_review_rows_ref": str(layer_review_rows_path),
            "layer_review_row_count": len(layer_review_rows),
            "layer_review_diagnostic_summary": layer_review_summary,
            "replay_review_performance_summary_ref": str(performance_summary_path),
            "replay_review_performance_summary": performance_summary["summary"],
            "layer_attribution_report_ref": str(layer_attribution_root / "layer_attribution_report.json"),
            "layer_attribution_summary": {
                "row_scope": layer_attribution_report.get("row_scope"),
                "model_candidate_selection_summary": layer_attribution_report.get("model_candidate_selection_summary"),
                "pre_option_candidate_quality_summary": layer_attribution_report.get(
                    "pre_option_candidate_quality_summary"
                ),
                "operation_component_metrics_summary": layer_attribution_report.get(
                    "operation_component_metrics_summary"
                ),
                "operation_mechanism_contract_packet_summary": layer_attribution_report.get(
                    "operation_mechanism_contract_packet_summary"
                ),
            },
            "replay_review_completion_scope": completion_scope,
            "max_review_rows": max_review_rows,
            "replay_review_diagnostic_summary": review_summary,
            "residual_event_governance_status": "not_performed",
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
        next_internal_stage="replay_review",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(
            month=None,
            selected_work=selected_work,
            next_internal_stage="replay_review",
        ),
    )


def _write_no_decision_promotion_rejection(
    *,
    dataset_root: Path,
    storage_root: Path,
    replay_receipt: Mapping[str, Any],
    decision_rows_path: Path,
    now: datetime,
    execute: bool,
) -> Path | None:
    """Write terminal rejection evidence for a scoped full replay with no trades."""

    candidate_fold_id = str(replay_receipt.get("candidate_fold_id") or replay_receipt.get("fold_id") or "").strip()
    candidate_model_ref = str(replay_receipt.get("candidate_model_ref") or "").strip()
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "").strip()
    if not candidate_fold_id or not candidate_model_ref or not replay_run_id:
        return None
    if not _replay_receipt_full_completion_scope(replay_receipt):
        return None
    replay_receipt_path = dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json"
    if not replay_receipt_path.exists():
        return None
    if not execute:
        return dataset_root / "promotion_review_runs" / "not_executed" / "promotion_eligibility_decision.json"

    created_at_utc = now.isoformat()
    candidate_training_target = str(
        replay_receipt.get("candidate_training_target")
        or replay_receipt.get("target_symbol")
        or ""
    ).strip().upper()
    source_fold_state_path = _matching_fold_state_path(
        storage_root=storage_root,
        candidate_fold_id=candidate_fold_id,
        candidate_training_target=candidate_training_target,
    )
    run_id = "no_decision_rejection_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_root = dataset_root / "promotion_review_runs" / run_id
    decision_path = output_root / "promotion_eligibility_decision.json"
    output_root.mkdir(parents=True, exist_ok=True)
    decision = {
        "contract_type": "promotion_eligibility_decision",
        "promotion_eligibility_decision_id": "promelig_" + _stable_token(
            candidate_fold_id,
            candidate_model_ref,
            replay_run_id,
            "no_replay_decisions",
        ),
        "fold_id": candidate_fold_id,
        "candidate_fold_id": candidate_fold_id,
        "target_symbol": candidate_training_target,
        "candidate_training_target": candidate_training_target,
        "candidate_model_ref": candidate_model_ref,
        "replay_contract_ref": str(replay_receipt.get("replay_contract_ref") or ""),
        "replay_execution_run_id": replay_run_id,
        "replay_validation_ref": str(replay_receipt_path),
        "decision_rows_ref": str(decision_rows_path),
        "decision_status": "rejected",
        "decision_reason": "Full replay completed with zero decision rows; no replay performance or attribution evidence can be produced.",
        "decision_reason_code": "no_replay_decisions",
        "agent_review_recommendation": "failed",
        "replay_freeze_status": "frozen",
        "guardrail_status": "failed",
        "fold_stack_status": "complete_m01_m06_replay_no_decisions",
        "metric_refs": [],
        "guardrail_refs": [str(replay_receipt_path)],
        "first_model_bootstrap": False,
        "bootstrap_baseline_ref": "",
        "source_fold_state_path": str(source_fold_state_path) if source_fold_state_path is not None else "",
        "created_at_utc": created_at_utc,
    }
    decision_path.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return decision_path


def _jsonl_has_any_object(path: Path) -> bool:
    for _row in _load_jsonl_objects(path):
        return True
    return False


def _existing_no_decision_promotion_rejection_for_replay(
    *,
    dataset_root: Path,
    replay_receipt: Mapping[str, Any],
) -> Path | None:
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "").strip()
    if not replay_run_id:
        return None
    replay_receipt_path = dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json"
    if not replay_receipt_path.exists():
        return None
    return _existing_no_decision_promotion_rejection(
        dataset_root,
        replay_validation_ref=str(replay_receipt_path),
    )


def _existing_no_decision_promotion_rejection(dataset_root: Path, *, replay_validation_ref: str) -> Path | None:
    review_root = dataset_root / "promotion_review_runs"
    if not review_root.exists():
        return None
    candidates: list[Path] = []
    for decision_path in sorted(review_root.glob("*/promotion_eligibility_decision.json")):
        decision = _load_optional_json_object(decision_path)
        if decision is None:
            continue
        if str(decision.get("contract_type") or "") != "promotion_eligibility_decision":
            continue
        if str(decision.get("replay_validation_ref") or "") != replay_validation_ref:
            continue
        if str(decision.get("decision_status") or "") != "rejected":
            continue
        if str(decision.get("decision_reason_code") or "") != "no_replay_decisions":
            continue
        candidates.append(decision_path)
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def _matching_fold_state_path(
    *,
    storage_root: Path,
    candidate_fold_id: str,
    candidate_training_target: str,
) -> Path | None:
    parts = candidate_fold_id.split("_")
    parsed_current = parse_model_worker_fold_id(candidate_fold_id)
    if parsed_current is not None:
        target_token, training_year = parsed_current
        start_month = f"{training_year}-01"
        end_month = f"{int(training_year) + 1:04d}-06"
        expected_target = candidate_training_target.strip().lower() or target_token
    elif len(parts) == 3 and parts[0] == "fold":
        start_month, end_month = parts[1], parts[2]
        expected_target = candidate_training_target.strip().lower()
    else:
        return None
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return None
    for path in sorted(runtime_root.glob(f"model_training_fold_state_*_{start_month}_{end_month}.json")):
        payload = _load_optional_json_object(path)
        if payload is None:
            continue
        target = str(
            payload.get("target_symbol")
            or payload.get("selected_target_symbol")
            or payload.get("target_ref")
            or ""
        ).strip().upper()
        if expected_target and target and target.lower() != expected_target:
            continue
        return path
    return None


def _stable_token(*parts: Any) -> str:
    raw = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _build_review_rows(decision_rows_path: Path, *, max_rows: int | None) -> Iterable[dict[str, Any]]:
    count = 0
    for index, row in enumerate(_load_jsonl_objects(decision_rows_path), start=1):
        if not _replay_row_needs_attribution(row):
            continue
        count += 1
        if max_rows is not None and count > max_rows:
            break
        yield _review_row(row, decision_index=index, review_index=count)


def _review_data_requirements(decision_rows_path: Path, *, max_rows: int | None) -> Iterable[dict[str, Any]]:
    count = 0
    for index, row in enumerate(_load_jsonl_objects(decision_rows_path), start=1):
        if not _replay_row_needs_attribution(row):
            continue
        count += 1
        if max_rows is not None and count > max_rows:
            break
        requirement = _review_data_requirement(row, decision_index=index, decision_rows_path=decision_rows_path)
        if requirement is not None:
            yield requirement


def _review_data_requirement(row: Mapping[str, Any], *, decision_index: int, decision_rows_path: Path) -> dict[str, Any] | None:
    fill_status = str(row.get("fill_status") or "")
    decision_status = str(row.get("decision_status") or "")
    filled = fill_status == "simulated_filled" or decision_status in {"filled", "approved", "executed"}
    decision_time = _decision_time(row)
    missing_fields: list[str] = []
    required_data_kinds: list[str] = []
    if not _has_material_future_outcome_window(row, decision_time=decision_time):
        missing_fields.append("future_outcome_window")
        required_data_kinds.append("replay_outcome_window_materialization")
    if filled and _filled_realized_return(row) is None:
        missing_fields.append("realized_return")
        required_data_kinds.append("replay_realized_return_materialization")
    if not filled and _opportunity_return(row) is None:
        missing_fields.append("replay_opportunity_return")
        required_data_kinds.append("replay_missed_opportunity_return_materialization")
    if not missing_fields:
        return None
    source_id = str(row.get("decision_id") or row.get("replay_decision_id") or f"decision_row_{decision_index}")
    return {
        "contract_type": REPLAY_REVIEW_DATA_REQUIREMENT_CONTRACT_TYPE,
        "stage_id": "model_group.replay_review",
        "source_decision_id": source_id,
        "source_decision_index": decision_index,
        "decision_rows_ref": str(decision_rows_path),
        "target_symbol": _target_symbol(row),
        "replay_month": _replay_month(row),
        "decision_time": decision_time,
        "fill_status": fill_status,
        "decision_status": decision_status,
        "missing_fields": _dedupe_text(missing_fields),
        "required_data_kinds": _dedupe_text(required_data_kinds),
        "acquisition_route": _review_data_acquisition_route(row),
        "selected_option_contract_ref": _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")),
        "path_conditioning_policy": _path_conditioning_policy(row),
        "candidate_set_scope": _candidate_set_scope(row),
        "miss_attribution_layer": _miss_attribution_layer(row, filled=filled),
    }


def _has_material_future_outcome_window(row: Mapping[str, Any], *, decision_time: str | None) -> bool:
    explicit = _first_text(
        row,
        (
            "future_outcome_window",
            "outcome_window",
            "replay_outcome_window",
            "label_window",
            "holding_window",
        ),
    )
    if explicit:
        return True
    exit_time = _first_text(
        row,
        (
            "exit_time",
            "next_timestamp",
            "label_time",
            "outcome_time",
            "selected_option_exit_time",
            "underlying_exit_time",
        ),
    )
    return bool(decision_time and exit_time)


def _filled_realized_return(row: Mapping[str, Any]) -> float | None:
    value = _safe_float(row.get("realized_return"))
    if value is not None:
        return value
    return _opportunity_return(row)


def _review_data_acquisition_route(row: Mapping[str, Any]) -> str:
    selected_contract = _first_text(row, ("selected_option_contract_ref", "selected_contract_ref"))
    if selected_contract and str(row.get("option_contract_path_status") or "").strip().lower() != "available":
        return "model_group.replay_contract_paths"
    if _target_symbol(row):
        return "model_group.replay_dataset_or_replay_rerun"
    return "replay_row_contract_repair"


def _review_row(row: Mapping[str, Any], *, decision_index: int, review_index: int) -> dict[str, Any]:
    fill_status = str(row.get("fill_status") or "")
    decision_status = str(row.get("decision_status") or "")
    outcome_label = _int_field(row, "outcome_label")
    filled = fill_status == "simulated_filled" or decision_status in {"filled", "approved", "executed"}
    realized_return = _filled_realized_return(row) if filled else _safe_float(row.get("realized_return"))
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    if filled:
        failure_type = "filled_negative_or_underperforming_outcome"
    else:
        failure_type = "rejected_positive_missed_opportunity"
    path_scope = _path_scope(row)
    candidate_set_scope = _candidate_set_scope(row)
    miss_attribution_layer = _miss_attribution_layer(row, filled=filled)
    miss_review_scope = _miss_review_scope(
        filled=filled,
        path_conditioning_policy=_path_conditioning_policy(row),
        candidate_set_scope=candidate_set_scope,
        miss_attribution_layer=miss_attribution_layer,
    )
    source_id = str(row.get("decision_id") or row.get("replay_decision_id") or f"decision_row_{decision_index}")
    decision_time = _decision_time(row)
    impact_profile = _impact_profile(row, failure_type=failure_type, decision_time=decision_time)
    opportunity_return = _opportunity_return(row)
    available_actions = _available_actions(row, filled=filled, opportunity_return=opportunity_return)
    chosen_action = _chosen_action(row, filled=filled)
    best_available_action = _best_available_action_by_future_outcome(
        row,
        filled=filled,
        available_actions=available_actions,
        chosen_action=chosen_action,
        realized_return=realized_return,
        baseline_return=baseline_return,
        opportunity_return=opportunity_return,
    )
    regret_to_best_available = _regret_to_best_available(
        filled=filled,
        chosen_action=chosen_action,
        best_available_action=best_available_action,
        realized_return=realized_return,
        baseline_return=baseline_return,
        opportunity_return=opportunity_return,
    )
    chosen_action_return = _action_return(
        chosen_action,
        filled=filled,
        realized_return=realized_return,
        baseline_return=baseline_return,
        opportunity_return=opportunity_return,
    )
    best_available_action_return = _action_return(
        best_available_action,
        filled=filled,
        realized_return=realized_return,
        baseline_return=baseline_return,
        opportunity_return=opportunity_return,
    )
    first_gap_component = _first_gap_component(
        row,
        filled=filled,
        best_available_action=best_available_action,
        chosen_action=chosen_action,
        miss_attribution_layer=miss_attribution_layer,
    )
    first_gap_mechanism = _first_gap_mechanism(
        row,
        filled=filled,
        best_available_action=best_available_action,
        chosen_action=chosen_action,
    )
    layer_attribution = {
        "first_gap_component": first_gap_component,
        "first_gap_mechanism": first_gap_mechanism,
        "miss_attribution_layer": miss_attribution_layer,
        "miss_review_scope": miss_review_scope,
        "candidate_set_scope": candidate_set_scope,
        "chosen_action": chosen_action,
        "best_available_action_by_future_outcome": best_available_action,
        "chosen_action_return": chosen_action_return,
        "best_available_action_return": best_available_action_return,
        "regret_to_best_available": regret_to_best_available,
        "attribution_basis": _layer_attribution_basis(
            filled=filled,
            best_available_action=best_available_action,
            chosen_action=chosen_action,
            miss_review_scope=miss_review_scope,
        ),
    }
    return {
        "contract_type": REPLAY_REVIEW_ROW_CONTRACT_TYPE,
        "stage_id": "model_group.replay_review",
        "review_id": f"replay_review_{review_index:08d}",
        "source_decision_id": source_id,
        "source_decision_index": decision_index,
        "decision_time": decision_time,
        "impact_exposure_time": impact_profile["impact_exposure_time"],
        "impact_onset_time": impact_profile["impact_onset_time"],
        "impact_onset_basis": impact_profile["impact_onset_basis"],
        "impact_scope_type": impact_profile["impact_scope_type"],
        "impact_direction": impact_profile["impact_direction"],
        "impact_raw_return_delta": impact_profile["impact_raw_return_delta"],
        "impact_magnitude_abs_return": impact_profile["impact_magnitude_abs_return"],
        "impact_normalization_denominator": impact_profile["impact_normalization_denominator"],
        "impact_normalized_severity_score": impact_profile["impact_normalized_severity_score"],
        "impact_severity_basis": impact_profile["impact_severity_basis"],
        "review_status": "reviewed",
        "failure_type": failure_type,
        "cause_family": "model_mechanism_defect",
        "cause_family_basis": "replay row was visible and locally reviewable; event attribution is deferred to M06",
        "eligibility_ledger_status": "reviewable_from_replay_row",
        "decision_ledger_status": "reviewable_from_replay_row",
        "outcome_ledger_status": "reviewable_from_replay_row",
        "available_action": available_actions,
        "chosen_action": chosen_action,
        "future_outcome_window": _future_outcome_window(row, decision_time=decision_time),
        "best_available_action_by_future_outcome": best_available_action,
        "regret_to_best_available": regret_to_best_available,
        "chosen_action_return": chosen_action_return,
        "best_available_action_return": best_available_action_return,
        "first_gap_component": first_gap_component,
        "first_gap_mechanism": first_gap_mechanism,
        "layer_attribution": layer_attribution,
        "path_conditioning_policy": _path_conditioning_policy(row),
        "path_scope": path_scope,
        "candidate_set_scope": candidate_set_scope,
        "miss_attribution_layer": miss_attribution_layer,
        "miss_review_scope": miss_review_scope,
        "replay_month": _replay_month(row),
        "target_symbol": _target_symbol(row),
        "fill_status": fill_status,
        "decision_status": decision_status,
        "outcome_label": outcome_label,
        "realized_return": realized_return,
        "baseline_return": baseline_return,
        "attribution_basis": (
            "filled decision lost money or underperformed baseline"
            if filled
            else "path-conditioned non-taken decision missed a positive next outcome"
        ),
    }


def _build_layer_review_rows(
    *,
    decision_rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
    max_decision_rows: int | None,
) -> Iterable[dict[str, Any]]:
    trace_index = _selected_trace_index(trace_rows)
    for decision_index, row in enumerate(decision_rows, start=1):
        if max_decision_rows is not None and decision_index > max_decision_rows:
            break
        source_id = str(row.get("decision_id") or row.get("replay_decision_id") or f"decision_row_{decision_index}")
        trace_row = trace_index.get((_decision_time(row) or "", str(row.get("target_ref") or _target_symbol(row) or "")))
        for layer_order, (layer_id, layer_label) in enumerate(REPLAY_LAYER_REVIEW_LAYERS, start=1):
            yield _layer_review_row(
                row,
                decision_index=decision_index,
                source_id=source_id,
                layer_order=layer_order,
                layer_id=layer_id,
                layer_label=layer_label,
                trace_row=trace_row,
            )


def _selected_trace_index(trace_rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    indexed: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in trace_rows:
        if not _truthy(row.get("selected_by_replay")):
            continue
        timestamp = str(row.get("replay_time_pointer") or row.get("timestamp") or "").strip()
        target = str(row.get("target_ref") or row.get("target_symbol") or "").strip()
        if timestamp and target:
            indexed.setdefault((timestamp, target), row)
    return indexed


def _layer_review_row(
    row: Mapping[str, Any],
    *,
    decision_index: int,
    source_id: str,
    layer_order: int,
    layer_id: str,
    layer_label: str,
    trace_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    decision_time = _decision_time(row)
    diagnostics = _layer_diagnostics(row, layer_id)
    method = REPLAY_LAYER_REVIEW_METHODS.get(layer_id, {})
    classification = _layer_review_classification(row, layer_id=layer_id, diagnostics=diagnostics, trace_row=trace_row)
    correctness = str(classification["correctness_class"])
    selected_output_ref = _layer_ref(row, layer_id) or diagnostics.get("model_ref") or classification.get("selected_output_ref")
    effective_decision_status = str(classification["effective_decision_status"])
    return {
        "contract_type": REPLAY_LAYER_REVIEW_ROW_CONTRACT_TYPE,
        "stage_id": "model_group.replay_review",
        "review_policy_version": "m01_m05_path_conditioned_layer_review_v1",
        "review_id": f"replay_layer_review_{decision_index:08d}_{layer_order:02d}",
        "source_decision_id": source_id,
        "source_decision_index": decision_index,
        "decision_time": decision_time,
        "impact_exposure_time": _impact_profile(row, failure_type="layer_review_outcome_context", decision_time=decision_time)[
            "impact_exposure_time"
        ],
        "future_outcome_window": _future_outcome_window(row, decision_time=decision_time),
        "replay_month": _replay_month(row),
        "target_symbol": _target_symbol(row),
        "target_ref": str(row.get("target_ref") or _target_symbol(row) or ""),
        "path_conditioning_policy": _path_conditioning_policy(row),
        "path_scope": _path_scope(row),
        "candidate_set_scope": classification["candidate_set_scope"],
        "review_boundary_ref": selected_output_ref or classification["candidate_set_scope"],
        "review_boundary_status": "received_boundary_complete"
        if effective_decision_status == "measured"
        else "received_boundary_missing_evidence",
        "upstream_decision_state_policy": "received_upstream_state_is_fixed_review_input",
        "downstream_review_input_policy": "judge_layer_only_against_received_decision_time_inputs",
        "upstream_error_isolation_scope": "attribute_upstream_defects_to_earliest_layer_or_boundary",
        "responsibility_assignment_policy": "layer_local_correctness_given_received_inputs",
        "layer_id": layer_id,
        "layer_label": layer_label,
        "layer_order": layer_order,
        "metric_family": method.get("metric_family", "unsupported_layer_review"),
        "analysis_method": method.get("analysis_method", "unsupported_layer_review"),
        "decision_time_input_fields": list(method.get("decision_time_input_fields", [])),
        "post_replay_label_fields": list(method.get("post_replay_label_fields", [])),
        "label_role": "post_replay_review_label_not_decision_time_input"
        if method.get("post_replay_label_fields")
        else "point_in_time_diagnostic_only",
        "effective_decision": _effective_layer_decision(row, layer_id=layer_id, diagnostics=diagnostics, trace_row=trace_row),
        "effective_decision_status": effective_decision_status,
        "selected_output_ref": selected_output_ref,
        "chosen_action": classification["chosen_action"],
        "available_action": classification["available_action"],
        "best_available_action_by_future_outcome": classification["best_available_action_by_future_outcome"],
        "chosen_action_return": classification.get("chosen_action_return"),
        "best_available_action_return": classification.get("best_available_action_return"),
        "correctness_class": correctness,
        "acceptability_class": _layer_acceptability_class(correctness),
        "scoring_status": classification["scoring_status"],
        "classification_basis": classification["classification_basis"],
        "regret_to_best_available": classification.get("regret_to_best_available"),
        "impact_normalized_severity_score": classification.get("impact_normalized_severity_score"),
        "cause_family": "model_mechanism_defect" if correctness == "incorrect" else "not_attributed",
        "failure_type": classification["failure_type"],
        "first_gap_component": layer_id if correctness == "incorrect" else "no_gap",
        "first_gap_mechanism": classification["first_gap_mechanism"] if correctness == "incorrect" else "no_gap",
        "outcome_label": _int_field(row, "outcome_label"),
        "realized_return": _round_metric_nullable(_safe_float(row.get("realized_return"))),
        "baseline_return": _round_metric_nullable(_safe_float(row.get("baseline_return"))),
        "directional_underlying_return": _round_metric_nullable(_directional_underlying_return(row)),
        "model_ref": _layer_ref(row, layer_id) or diagnostics.get("model_ref"),
        "layer_diagnostics": dict(diagnostics),
        "trace_evidence": _layer_trace_evidence(layer_id, trace_row),
        "evidence_refs": _layer_evidence_refs(layer_id, trace_row=trace_row),
        "hindsight_caution": "Future returns are post-replay labels for review; they are not decision-time model inputs.",
    }


def _layer_review_classification(
    row: Mapping[str, Any],
    *,
    layer_id: str,
    diagnostics: Mapping[str, Any],
    trace_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if layer_id == "model_01_background_context":
        return _m01_background_context_classification(diagnostics)
    if layer_id == "model_02_target_state":
        return _m02_target_state_classification(row, diagnostics=diagnostics, trace_row=trace_row)
    if layer_id == "model_03_event_state":
        return _m03_event_state_classification(diagnostics)
    if layer_id == "model_04_unified_decision":
        return _m04_unified_decision_classification(row)
    if layer_id == "model_05_option_expression":
        return _m05_option_expression_classification(row, diagnostics=diagnostics)
    return _indeterminate_layer_classification(
        candidate_set_scope="unsupported_layer",
        chosen_action="not_reported",
        basis="layer is outside the M01-M05 replay decision review contract",
    )


def _m01_background_context_classification(diagnostics: Mapping[str, Any]) -> dict[str, Any]:
    state_quality = _safe_float(diagnostics.get("state_quality_score"))
    stress = _safe_float(diagnostics.get("market_risk_stress_score"))
    transition = _safe_float(diagnostics.get("transition_risk_score"))
    if state_quality is None and stress is None and transition is None:
        return _indeterminate_layer_classification(
            candidate_set_scope="background_context_state",
            chosen_action="background_context_not_reported",
            basis="M01 diagnostics are missing from the replay decision row",
        )
    acceptable = (state_quality is None or state_quality >= 0.5) and (stress is None or stress <= 0.8) and (
        transition is None or transition <= 0.8
    )
    severity = _diagnostic_threshold_severity(
        0.5 - state_quality if state_quality is not None else None,
        stress - 0.8 if stress is not None else None,
        transition - 0.8 if transition is not None else None,
    )
    return _simple_layer_classification(
        correct=acceptable,
        candidate_set_scope="background_context_state",
        chosen_action="accept_background_context_state",
        fallback_action="withhold_or_downweight_poor_background_context",
        basis="point_in_time_background_state_quality_and_risk_thresholds",
        failure_type="poor_background_context_accepted",
        first_gap_mechanism="background_context_risk_gate",
        diagnostic_severity_score=severity,
    )


def _m02_target_state_classification(
    row: Mapping[str, Any],
    *,
    diagnostics: Mapping[str, Any],
    trace_row: Mapping[str, Any] | None,
) -> dict[str, Any]:
    rank = _safe_float((trace_row or {}).get("model_rank_within_timestamp"))
    score_available = _truthy((trace_row or {}).get("model_score_available"))
    selected = _truthy((trace_row or {}).get("selected_by_replay")) if trace_row is not None else False
    direction = _safe_float(diagnostics.get("target_direction_score_1D"))
    tradability = _safe_float(diagnostics.get("tradability_score_1D"))
    target_quality = _safe_float(diagnostics.get("target_trend_quality_score_1D"))
    if trace_row is None and direction is None and tradability is None and target_quality is None:
        return _indeterminate_layer_classification(
            candidate_set_scope="selected_target_candidate_handoff",
            chosen_action=f"select_target:{_target_symbol(row) or 'not_reported'}",
            basis="M02 candidate trace and target-state diagnostics are missing",
        )
    acceptable_rank = rank is None or rank <= 25
    acceptable_state = (direction is None or direction >= 0.5) and (tradability is None or tradability >= 0.5) and (
        target_quality is None or target_quality >= 0.5
    )
    acceptable_selection = trace_row is None or selected or not score_available
    correct = acceptable_rank and acceptable_state and acceptable_selection
    rank_severity = (rank - 25.0) / 25.0 if rank is not None else None
    severity = _diagnostic_threshold_severity(
        rank_severity,
        0.5 - direction if direction is not None else None,
        0.5 - tradability if tradability is not None else None,
        0.5 - target_quality if target_quality is not None else None,
        1.0 if not acceptable_selection else 0.0,
    )
    return _simple_layer_classification(
        correct=correct,
        candidate_set_scope="selected_target_candidate_handoff",
        chosen_action=f"select_target:{diagnostics.get('target_ref') or _target_symbol(row) or 'not_reported'}",
        fallback_action="choose_better_ranked_or_more_tradable_target",
        basis="point_in_time_target_state_scores_and_same_timestamp_candidate_rank",
        failure_type="weak_or_low_ranked_target_selected",
        first_gap_mechanism="target_selection_rank_or_quality",
        selected_output_ref=(trace_row or {}).get("model_candidate_trace_status"),
        diagnostic_severity_score=severity,
    )


def _m03_event_state_classification(diagnostics: Mapping[str, Any]) -> dict[str, Any]:
    uncertainty = _safe_float(diagnostics.get("event_uncertainty_score_1D"))
    block = _safe_float(diagnostics.get("event_entry_block_pressure_score_1D"))
    disable = _safe_float(diagnostics.get("event_strategy_disable_pressure_score_1D"))
    path_risk = _safe_float(diagnostics.get("event_path_risk_score_1D"))
    if uncertainty is None and block is None and disable is None and path_risk is None:
        return _indeterminate_layer_classification(
            candidate_set_scope="selected_path_event_state",
            chosen_action="event_state_not_reported",
            basis="M03 event-state diagnostics are missing from the replay decision row",
        )
    correct = (block is None or block <= 0.5) and (disable is None or disable <= 0.5) and (
        uncertainty is None or uncertainty <= 0.8
    ) and (path_risk is None or path_risk <= 0.8)
    severity = _diagnostic_threshold_severity(
        block - 0.5 if block is not None else None,
        disable - 0.5 if disable is not None else None,
        uncertainty - 0.8 if uncertainty is not None else None,
        path_risk - 0.8 if path_risk is not None else None,
    )
    return _simple_layer_classification(
        correct=correct,
        candidate_set_scope="selected_path_event_state",
        chosen_action="allow_path_event_state",
        fallback_action="block_or_downweight_event_risk_path",
        basis="point_in_time_event_pressure_and_uncertainty_thresholds",
        failure_type="event_risk_state_allowed",
        first_gap_mechanism="event_risk_gate",
        diagnostic_severity_score=severity,
    )


def _m04_unified_decision_classification(row: Mapping[str, Any]) -> dict[str, Any]:
    chosen = _decision_intended_action(row) or "underlying_action_not_reported"
    directional_return = _directional_underlying_return(row)
    if directional_return is None:
        return _indeterminate_layer_classification(
            candidate_set_scope="selected_target_underlying_decision",
            chosen_action=chosen,
            basis="directional underlying outcome label is missing",
        )
    baseline = _safe_float(row.get("baseline_return")) or 0.0
    correct = directional_return >= baseline
    return _return_labeled_layer_classification(
        correct=correct,
        candidate_set_scope="selected_target_underlying_decision",
        chosen_action=chosen,
        fallback_action="baseline_action",
        chosen_return=directional_return,
        baseline_return=baseline,
        basis="post_replay_directional_underlying_return_label",
        failure_type="underlying_action_underperformed_baseline",
        first_gap_mechanism="underlying_direction_or_entry_timing",
    )


def _m05_option_expression_classification(row: Mapping[str, Any], *, diagnostics: Mapping[str, Any]) -> dict[str, Any]:
    expression = str(
        diagnostics.get("selected_expression_type")
        or row.get("selected_option_expression_type")
        or row.get("decision_expression_type")
        or "option_expression_not_reported"
    )
    contract = str(
        diagnostics.get("selected_contract_ref")
        or row.get("selected_option_contract_ref")
        or row.get("selected_contract_ref")
        or ""
    )
    chosen = f"{expression} {contract}".strip()
    selected_return = _safe_float(row.get("realized_return"))
    if selected_return is None:
        selected_return = _opportunity_return(row)
    if selected_return is None:
        return _indeterminate_layer_classification(
            candidate_set_scope=_candidate_set_scope(row),
            chosen_action=chosen,
            basis="selected option expression outcome label is missing",
        )
    baseline = _safe_float(row.get("baseline_return")) or 0.0
    direction_ok = _option_direction_consistency_status(row) != "mismatch"
    correct = selected_return >= baseline and direction_ok
    return _return_labeled_layer_classification(
        correct=correct,
        candidate_set_scope=_candidate_set_scope(row),
        chosen_action=chosen,
        fallback_action="baseline_action",
        chosen_return=selected_return,
        baseline_return=baseline,
        basis="post_replay_selected_option_expression_return_label_and_direction_consistency",
        failure_type="option_expression_underperformed_or_mismatched_direction",
        first_gap_mechanism="option_expression_selection",
    )


def _simple_layer_classification(
    *,
    correct: bool,
    candidate_set_scope: str,
    chosen_action: str,
    fallback_action: str,
    basis: str,
    failure_type: str,
    first_gap_mechanism: str,
    selected_output_ref: Any = None,
    diagnostic_severity_score: float | None = None,
) -> dict[str, Any]:
    severity = 0.0 if correct else diagnostic_severity_score
    return {
        "candidate_set_scope": candidate_set_scope,
        "effective_decision_status": "measured",
        "chosen_action": chosen_action,
        "available_action": [chosen_action, fallback_action],
        "best_available_action_by_future_outcome": chosen_action if correct else fallback_action,
        "chosen_action_return": None,
        "best_available_action_return": None,
        "correctness_class": "correct" if correct else "incorrect",
        "scoring_status": "scored_point_in_time_diagnostic",
        "classification_basis": basis,
        "regret_to_best_available": 0.0 if correct else None,
        "impact_normalized_severity_score": _round_metric_nullable(severity),
        "failure_type": "none" if correct else failure_type,
        "first_gap_mechanism": first_gap_mechanism,
        "selected_output_ref": selected_output_ref,
    }


def _return_labeled_layer_classification(
    *,
    correct: bool,
    candidate_set_scope: str,
    chosen_action: str,
    fallback_action: str,
    chosen_return: float,
    baseline_return: float,
    basis: str,
    failure_type: str,
    first_gap_mechanism: str,
) -> dict[str, Any]:
    regret = max(0.0, baseline_return - chosen_return)
    return {
        "candidate_set_scope": candidate_set_scope,
        "effective_decision_status": "measured",
        "chosen_action": chosen_action,
        "available_action": [chosen_action, fallback_action],
        "best_available_action_by_future_outcome": chosen_action if correct else fallback_action,
        "chosen_action_return": _round_metric(chosen_return),
        "best_available_action_return": _round_metric(chosen_return if correct else baseline_return),
        "correctness_class": "correct" if correct else "incorrect",
        "scoring_status": "scored_post_replay_outcome_label",
        "classification_basis": basis,
        "regret_to_best_available": _round_metric(regret),
        "impact_normalized_severity_score": _round_metric(regret) if regret > 0 else 0.0,
        "failure_type": "none" if correct else failure_type,
        "first_gap_mechanism": first_gap_mechanism,
    }


def _indeterminate_layer_classification(*, candidate_set_scope: str, chosen_action: str, basis: str) -> dict[str, Any]:
    return {
        "candidate_set_scope": candidate_set_scope,
        "effective_decision_status": "missing_evidence",
        "chosen_action": chosen_action,
        "available_action": [chosen_action],
        "best_available_action_by_future_outcome": "not_determinable",
        "chosen_action_return": None,
        "best_available_action_return": None,
        "correctness_class": "indeterminate",
        "scoring_status": "missing_layer_review_evidence",
        "classification_basis": basis,
        "regret_to_best_available": None,
        "impact_normalized_severity_score": None,
        "failure_type": "missing_layer_review_evidence",
        "first_gap_mechanism": "missing_evidence",
    }


def _layer_acceptability_class(correctness: str) -> str:
    if correctness == "correct":
        return "acceptable"
    if correctness == "incorrect":
        return "unacceptable"
    return "indeterminate"


def _layer_diagnostics(row: Mapping[str, Any], layer_id: str) -> Mapping[str, Any]:
    diagnostics = row.get("model_layer_diagnostics")
    if not isinstance(diagnostics, MappingABC):
        return {}
    value = diagnostics.get(layer_id)
    return value if isinstance(value, MappingABC) else {}


def _layer_ref(row: Mapping[str, Any], layer_id: str) -> Any:
    refs = row.get("model_layer_refs")
    if isinstance(refs, MappingABC):
        return refs.get(layer_id)
    return None


def _effective_layer_decision(
    row: Mapping[str, Any],
    *,
    layer_id: str,
    diagnostics: Mapping[str, Any],
    trace_row: Mapping[str, Any] | None,
) -> str:
    if layer_id == "model_01_background_context":
        return (
            "background_context_state "
            f"quality={diagnostics.get('state_quality_score')} "
            f"risk={diagnostics.get('market_risk_stress_score')} "
            f"transition={diagnostics.get('transition_risk_score')}"
        )
    if layer_id == "model_02_target_state":
        rank = (trace_row or {}).get("model_rank_within_timestamp")
        return (
            f"selected_target {diagnostics.get('target_ref') or _target_symbol(row) or 'not_reported'} "
            f"direction_1d={diagnostics.get('target_direction_score_1D')} "
            f"tradability_1d={diagnostics.get('tradability_score_1D')} "
            f"same_timestamp_rank={rank}"
        )
    if layer_id == "model_03_event_state":
        return (
            "event_state "
            f"uncertainty_1d={diagnostics.get('event_uncertainty_score_1D')} "
            f"block_pressure_1d={diagnostics.get('event_entry_block_pressure_score_1D')} "
            f"path_risk_1d={diagnostics.get('event_path_risk_score_1D')}"
        )
    if layer_id == "model_04_unified_decision":
        return str(
            diagnostics.get("resolved_underlying_action_type")
            or diagnostics.get("resolved_action_side")
            or row.get("decision_action")
            or row.get("action")
            or "not_reported"
        )
    if layer_id == "model_05_option_expression":
        expression = diagnostics.get("selected_expression_type") or row.get("selected_option_expression_type")
        contract = diagnostics.get("selected_contract_ref") or row.get("selected_option_contract_ref") or row.get("instrument_ref")
        return f"{expression or 'not_reported'} {contract or ''}".strip()
    return "not_reported"


def _layer_trace_evidence(layer_id: str, trace_row: Mapping[str, Any] | None) -> dict[str, Any]:
    if layer_id != "model_02_target_state" or trace_row is None:
        return {}
    fields = (
        "model_candidate_trace_status",
        "selected_by_replay",
        "model_rank_within_timestamp",
        "diagnostic_rank_score",
        "alpha_score",
        "expected_return_score",
        "action_direction_score",
        "trade_intensity_score",
    )
    return {field: trace_row.get(field) for field in fields if field in trace_row}


def _layer_evidence_refs(layer_id: str, *, trace_row: Mapping[str, Any] | None) -> list[str]:
    refs = ["decision_rows.jsonl"]
    if layer_id == "model_02_target_state" and trace_row is not None:
        refs.append("model_candidate_selection_trace.jsonl")
    return refs


def _layer_review_diagnostic_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    material = list(rows)
    by_layer: dict[str, list[Mapping[str, Any]]] = {
        layer_id: [row for row in material if row.get("layer_id") == layer_id]
        for layer_id, _label in REPLAY_LAYER_REVIEW_LAYERS
    }
    return {
        "contract_type": "post_replay_layer_decision_review_summary",
        "row_count": len(material),
        "included_layers": [layer_id for layer_id, _label in REPLAY_LAYER_REVIEW_LAYERS],
        "excluded_layers": list(EXCLUDED_REPLAY_LAYER_REVIEW_LAYERS),
        "layer_summaries": {
            layer_id: {
                "row_count": len(layer_rows),
                "correct_count": sum(1 for row in layer_rows if row.get("correctness_class") == "correct"),
                "incorrect_count": sum(1 for row in layer_rows if row.get("correctness_class") == "incorrect"),
                "indeterminate_count": sum(1 for row in layer_rows if row.get("correctness_class") == "indeterminate"),
                "scoring_status_counts": _count_text(row.get("scoring_status") for row in layer_rows),
                "mean_regret_to_best_available": _round_metric_nullable(
                    _mean_float(
                        _safe_float(row.get("regret_to_best_available"))
                        for row in layer_rows
                        if _safe_float(row.get("regret_to_best_available")) is not None
                    )
                ),
            }
            for layer_id, layer_rows in by_layer.items()
        },
        "classification_policy": {
            "shared_envelope": "M01-M05 rows share identity, evidence refs, scoring status, and label provenance fields; metric families and analysis methods are layer-specific.",
            "m01": REPLAY_LAYER_REVIEW_METHODS["model_01_background_context"]["analysis_method"],
            "m02": REPLAY_LAYER_REVIEW_METHODS["model_02_target_state"]["analysis_method"],
            "m03": REPLAY_LAYER_REVIEW_METHODS["model_03_event_state"]["analysis_method"],
            "m04": REPLAY_LAYER_REVIEW_METHODS["model_04_unified_decision"]["analysis_method"],
            "m05": REPLAY_LAYER_REVIEW_METHODS["model_05_option_expression"]["analysis_method"],
            "hindsight_caution": "Post-replay label fields are review labels only and must not be interpreted as decision-time inputs.",
        },
        "layer_analysis_methods": REPLAY_LAYER_REVIEW_METHODS,
    }


def _review_diagnostic_summary(review_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(review_rows)
    regrets = [_safe_float(row.get("regret_to_best_available")) for row in rows]
    material_regrets = [value for value in regrets if value is not None and value > 0]
    total_regret = sum(material_regrets)
    return {
        "contract_type": "post_replay_review_diagnostic_summary",
        "reviewed_row_count": len(rows),
        "material_regret_row_count": len(material_regrets),
        "total_regret_to_best_available": _round_metric(total_regret),
        "mean_regret_to_best_available": _round_metric(total_regret / len(material_regrets)) if material_regrets else 0.0,
        "max_regret_to_best_available": _round_metric(max(material_regrets)) if material_regrets else 0.0,
        "best_available_action_counts": _count_text(row.get("best_available_action_by_future_outcome") for row in rows),
        "first_gap_component_counts": _count_text(row.get("first_gap_component") for row in rows),
        "first_gap_mechanism_counts": _count_text(row.get("first_gap_mechanism") for row in rows),
        "miss_attribution_layer_counts": _count_text(row.get("miss_attribution_layer") for row in rows),
        "top_regret_rows": _top_regret_rows(rows, limit=5),
    }


def _replay_review_performance_summary(
    *,
    decision_rows: Iterable[Mapping[str, Any]],
    trace_rows: Iterable[Mapping[str, Any]],
    replay_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    decisions = list(decision_rows)
    traces = list(trace_rows)
    filled = [row for row in decisions if str(row.get("fill_status") or "") == "simulated_filled"]
    returns = [_safe_float(row.get("realized_return")) for row in filled]
    material_returns = [value for value in returns if value is not None]
    notional_by_row = [_safe_float(row.get("planned_position_notional_usd")) for row in filled]
    pnl_values = [
        notional * realized
        for notional, realized in zip(notional_by_row, returns)
        if notional is not None and realized is not None
    ]
    initial_capital = _safe_float(replay_receipt.get("initial_capital_usd") or replay_receipt.get("initial_capital"))
    capital_summary = _capital_constrained_performance(filled, initial_capital=initial_capital)
    turnover_notional_total = sum(value for value in notional_by_row if value is not None)
    turnover_pnl_total = sum(pnl_values)
    selected_trace_rows = [row for row in traces if _truthy(row.get("selected_by_replay"))]
    unexecutable_trace_rows = [
        row for row in traces if str(row.get("model_candidate_trace_status") or "") == "option_expression_unexecutable"
    ]
    executable_trace_rows = [
        row
        for row in traces
        if str(row.get("model_candidate_trace_status") or "")
        in {
            "selected_by_replay",
            "selected_by_replay_replacement",
            "held_position_continued",
            "scored_not_selected_by_portfolio",
            "scored_not_selected_switch_threshold",
        }
    ]
    selected_ranks = [_safe_float(row.get("model_rank_within_timestamp")) for row in selected_trace_rows]
    selected_rank_values = [int(value) for value in selected_ranks if value is not None]
    selected_timestamps = [_decision_time(row) for row in filled]
    selected_timestamp_counts = _count_text(value for value in selected_timestamps if value)
    path_status_counts = _count_text(row.get("option_contract_path_status") for row in decisions)
    expression_type_counts = _count_text(
        row.get("selected_option_expression_type") or row.get("decision_expression_type") for row in decisions
    )
    option_route_counts = _count_text(row.get("asset_expression_route") for row in decisions)
    target_rows = _target_performance_rows(filled)
    decision_scope = {
        "decision_row_count": len(decisions),
        "filled_count": len(filled),
        "decision_status_counts": _count_text(row.get("decision_status") for row in decisions),
        "fill_status_counts": _count_text(row.get("fill_status") for row in decisions),
        "selected_target_count": len({str(row.get("target_ref") or _target_symbol(row) or "") for row in filled}),
        "selected_timestamp_count": len(selected_timestamp_counts),
        "selected_timestamp_counts": selected_timestamp_counts,
        "selection_concentration_status": (
            "single_timestamp_batch"
            if len(selected_timestamp_counts) == 1 and len(filled) > 1
            else "multi_timestamp_or_single_decision"
        ),
    }
    target_performance = {
        "filled_target_count": len(filled),
        "positive_return_count": sum(1 for value in material_returns if value > 0),
        "negative_return_count": sum(1 for value in material_returns if value < 0),
        "flat_return_count": sum(1 for value in material_returns if value == 0),
        "mean_realized_return": _round_metric_nullable(_mean_float(material_returns)),
        "median_realized_return": _round_metric_nullable(_median_float(material_returns)),
        "min_realized_return": _round_metric_nullable(min(material_returns)) if material_returns else None,
        "max_realized_return": _round_metric_nullable(max(material_returns)) if material_returns else None,
        "initial_capital_usd": _round_metric_nullable(capital_summary["initial_capital_usd"]),
        "planned_notional_total": _round_metric_nullable(turnover_notional_total),
        "turnover_planned_notional_total": _round_metric_nullable(turnover_notional_total),
        "turnover_gross_pnl_total": _round_metric_nullable(turnover_pnl_total),
        "turnover_return_on_used_notional": _round_metric_nullable(turnover_pnl_total / turnover_notional_total)
        if turnover_notional_total > 0
        else None,
        "gross_pnl_total": _round_metric_nullable(capital_summary["capital_constrained_pnl_total"]),
        "return_on_initial_capital": _round_metric_nullable(capital_summary["return_on_initial_capital"]),
        "capital_constrained_pnl_total": _round_metric_nullable(capital_summary["capital_constrained_pnl_total"]),
        "capital_constrained_return_on_initial_capital": _round_metric_nullable(
            capital_summary["return_on_initial_capital"]
        ),
        "capital_constrained_final_equity_usd": _round_metric_nullable(capital_summary["final_equity_usd"]),
        "capital_constrained_floor_hit": capital_summary["capital_floor_hit"],
        "capital_constrained_trade_count": capital_summary["capital_constrained_trade_count"],
        "capital_accounting_policy": capital_summary["capital_accounting_policy"],
        "top_target_returns": target_rows[:10],
        "worst_target_returns": list(reversed(target_rows[-10:])),
    }
    stock_selection = {
        "trace_available": bool(traces),
        "scored_candidate_row_count": len([row for row in traces if _truthy(row.get("model_score_available"))]),
        "trace_target_count": len({str(row.get("target_ref") or "") for row in traces if str(row.get("target_ref") or "")}),
        "selected_trace_row_count": len(selected_trace_rows),
        "selected_rank_mean_same_timestamp": _round_metric_nullable(_mean_float(selected_rank_values)),
        "selected_top_10_count": sum(1 for rank in selected_rank_values if rank <= 10),
        "selected_top_25_count": sum(1 for rank in selected_rank_values if rank <= 25),
        "selected_outside_top_25_count": sum(1 for rank in selected_rank_values if rank > 25),
        "candidate_trace_status_counts": _count_text(row.get("model_candidate_trace_status") for row in traces),
    }
    replacement_rows = [
        row for row in traces if str(row.get("portfolio_replacement_evaluation_status") or "").strip()
    ]
    replacement_evaluated_rows = [
        row
        for row in replacement_rows
        if str(row.get("portfolio_replacement_evaluation_status") or "")
        not in {
            "not_needed_capacity_available",
            "held_target_continued",
            "not_evaluated_no_positions",
        }
    ]
    replacement_triggered_rows = [
        row for row in replacement_rows if str(row.get("portfolio_replacement_evaluation_status") or "") == "triggered"
    ]
    replacement_review = {
        "trace_available": bool(traces),
        "policy": "continue_scanning_after_budget_full; replace_weakest_held_only_when_new_rank_exceeds_threshold",
        "replacement_status_counts": _count_text(
            row.get("portfolio_replacement_evaluation_status") for row in replacement_rows
        ),
        "replacement_evaluated_count": len(replacement_evaluated_rows),
        "replacement_triggered_count": len(replacement_triggered_rows),
        "replacement_blocked_by_switch_threshold_count": sum(
            1
            for row in replacement_rows
            if str(row.get("portfolio_replacement_evaluation_status") or "") == "blocked_by_switch_threshold"
        ),
        "continued_held_position_count": sum(
            1
            for row in replacement_rows
            if str(row.get("portfolio_replacement_evaluation_status") or "") == "held_target_continued"
        ),
        "candidate_switch_delta_max": _round_metric_nullable(
            max(
                _safe_float(row.get("portfolio_switch_rank_score_delta"))
                for row in replacement_evaluated_rows
                if _safe_float(row.get("portfolio_switch_rank_score_delta")) is not None
            )
        )
        if any(_safe_float(row.get("portfolio_switch_rank_score_delta")) is not None for row in replacement_evaluated_rows)
        else None,
        "triggered_replacements_sample": _replacement_review_rows(replacement_triggered_rows, limit=10),
        "blocked_replacements_sample": _replacement_review_rows(
            [
                row
                for row in replacement_rows
                if str(row.get("portfolio_replacement_evaluation_status") or "") == "blocked_by_switch_threshold"
            ],
            limit=10,
        ),
    }
    option_expression = {
        "selected_option_decision_count": sum(
            1 for row in decisions if _first_text(row, ("selected_option_contract_ref", "selected_contract_ref"))
        ),
        "path_status_counts": path_status_counts,
        "expression_type_counts": expression_type_counts,
        "option_route_counts": option_route_counts,
        "trace_entry_intent_count": sum(1 for row in traces if _truthy(row.get("option_expression_signal_required"))),
        "trace_executable_entry_intent_count": len(executable_trace_rows),
        "trace_unexecutable_entry_intent_count": len(unexecutable_trace_rows),
        "trace_unexecutable_reason_counts": _count_text(
            row.get("option_expression_unexecutable_reason") for row in unexecutable_trace_rows
        ),
        "selected_candidate_count_before_filter_mean": _round_metric_nullable(
            _mean_float(
                _safe_float(row.get("candidate_count_before_filter"))
                for row in selected_trace_rows
            )
        ),
        "selected_candidate_count_after_filter_mean": _round_metric_nullable(
            _mean_float(
                _safe_float(row.get("candidate_count_after_filter"))
                for row in selected_trace_rows
            )
        ),
        "selected_eligible_candidate_count_mean": _round_metric_nullable(
            _mean_float(
                _safe_float(row.get("eligible_candidate_count"))
                for row in selected_trace_rows
            )
        ),
    }
    direction_expression = _direction_expression_summary(filled)
    return {
        "contract_type": "model_group_replay_review_performance_summary",
        "summary_role": "post_replay_layered_review_summary_not_training_or_threshold_input",
        "summary": {
            "decision_scope": decision_scope,
            "target_performance": {
                key: value
                for key, value in target_performance.items()
                if key not in {"top_target_returns", "worst_target_returns"}
            },
            "stock_selection": stock_selection,
            "replacement_review": replacement_review,
            "option_expression": option_expression,
            "direction_expression": direction_expression,
        },
        "decision_scope": decision_scope,
        "target_performance": target_performance,
        "stock_selection": stock_selection,
        "replacement_review": replacement_review,
        "option_expression": option_expression,
        "direction_expression": direction_expression,
        "layer_differentiation": _layer_differentiation_summary(decisions),
        "source_refs": {
            "decision_rows_ref": str(replay_receipt.get("decision_rows_ref") or ""),
            "model_candidate_selection_trace_ref": str(replay_receipt.get("model_candidate_selection_trace_ref") or ""),
            "replay_execution_run_id": str(replay_receipt.get("replay_execution_run_id") or ""),
        },
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _target_performance_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        realized_return = _safe_float(row.get("realized_return"))
        notional = _safe_float(row.get("planned_position_notional_usd"))
        pnl = notional * realized_return if notional is not None and realized_return is not None else None
        output.append(
            {
                "target_ref": str(row.get("target_ref") or _target_symbol(row) or ""),
                "instrument_ref": str(row.get("instrument_ref") or row.get("selected_option_contract_ref") or ""),
                "timestamp": _decision_time(row),
                "realized_return": _round_metric_nullable(realized_return),
                "planned_position_notional_usd": _round_metric_nullable(notional),
                "gross_pnl_usd": _round_metric_nullable(pnl),
                "prediction_score": _round_metric_nullable(_safe_float(row.get("prediction_score"))),
                "selected_option_contract_ref": _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")),
                "selected_option_expression_type": _first_text(
                    row,
                    ("selected_option_expression_type", "decision_expression_type"),
                ),
                "decision_intended_side": _decision_intended_side(row),
                "decision_intended_action": _decision_intended_action(row),
                "underlying_return": _round_metric_nullable(_safe_float(row.get("underlying_return"))),
                "directional_underlying_return": _round_metric_nullable(
                    _directional_underlying_return(row)
                ),
                "selected_option_right": _selected_option_right(row),
                "option_direction_consistency_status": _option_direction_consistency_status(row),
                "option_contract_path_status": str(row.get("option_contract_path_status") or ""),
            }
        )
    output.sort(key=lambda item: (item["realized_return"] is None, item["realized_return"] or 0.0), reverse=True)
    return output


def _capital_constrained_performance(
    rows: Iterable[Mapping[str, Any]],
    *,
    initial_capital: float | None,
) -> dict[str, Any]:
    starting_capital = initial_capital if initial_capital is not None and initial_capital > 0 else 25000.0
    equity = starting_capital
    pnl_total = 0.0
    constrained_trade_count = 0
    capital_floor_hit = False
    sorted_rows = sorted(rows, key=lambda row: _decision_time(row) or str(row.get("decision_id") or ""))
    for row in sorted_rows:
        realized_return = _safe_float(row.get("realized_return"))
        planned_notional = _safe_float(row.get("planned_position_notional_usd"))
        if realized_return is None or planned_notional is None or planned_notional <= 0:
            continue
        if equity <= 0:
            capital_floor_hit = True
            continue
        allocation_fraction = _safe_float(row.get("target_allocation_fraction"))
        if allocation_fraction is None or allocation_fraction <= 0:
            allocation_fraction = _safe_float(row.get("default_target_allocation_fraction")) or 0.20
        capital_notional = min(planned_notional, equity * allocation_fraction)
        if capital_notional <= 0:
            capital_floor_hit = True
            continue
        pnl = capital_notional * max(realized_return, -1.0)
        pnl_total += pnl
        equity = max(0.0, equity + pnl)
        constrained_trade_count += 1
        if equity <= 0:
            capital_floor_hit = True
    return {
        "initial_capital_usd": starting_capital,
        "capital_constrained_pnl_total": pnl_total,
        "return_on_initial_capital": pnl_total / starting_capital if starting_capital > 0 else None,
        "final_equity_usd": equity,
        "capital_floor_hit": capital_floor_hit,
        "capital_constrained_trade_count": constrained_trade_count,
        "capital_accounting_policy": "sequential_equity_curve_capped_by_current_equity_and_target_allocation",
    }


def _direction_expression_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    decisions = list(rows)
    aligned = [row for row in decisions if _option_direction_consistency_status(row) == "aligned"]
    mismatched = [row for row in decisions if _option_direction_consistency_status(row) == "mismatch"]
    direction_returns = [
        value
        for value in (_directional_underlying_return(row) for row in decisions)
        if value is not None
    ]
    return {
        "filled_decision_count": len(decisions),
        "intended_side_counts": _count_text(_decision_intended_side(row) for row in decisions),
        "intended_action_counts": _count_text(_decision_intended_action(row) for row in decisions),
        "selected_option_right_counts": _count_text(_selected_option_right(row) for row in decisions),
        "option_direction_consistency_counts": _count_text(
            _option_direction_consistency_status(row) for row in decisions
        ),
        "aligned_option_expression_count": len(aligned),
        "mismatched_option_expression_count": len(mismatched),
        "mean_directional_underlying_return": _round_metric_nullable(_mean_float(direction_returns)),
        "positive_directional_underlying_return_count": sum(1 for value in direction_returns if value > 0),
        "negative_directional_underlying_return_count": sum(1 for value in direction_returns if value < 0),
        "sample_mismatches": [
            {
                "target_ref": str(row.get("target_ref") or _target_symbol(row) or ""),
                "timestamp": _decision_time(row),
                "decision_intended_side": _decision_intended_side(row),
                "decision_expression_type": _first_text(
                    row,
                    ("decision_expression_type", "selected_option_expression_type"),
                ),
                "selected_option_right": _selected_option_right(row),
                "selected_option_contract_ref": _first_text(
                    row,
                    ("selected_option_contract_ref", "selected_contract_ref"),
                ),
            }
            for row in mismatched[:10]
        ],
    }


def _decision_intended_side(row: Mapping[str, Any]) -> str:
    explicit = _first_text(
        row,
        (
            "decision_intended_side",
            "intended_side",
            "resolved_action_side",
            "position_side",
            "action_side",
        ),
    )
    normalized = _normalize_side(explicit)
    if normalized != "unknown":
        return normalized
    action = _decision_intended_action(row)
    if action in {"open_long", "increase_long", "reduce_long", "close_long"}:
        return "long"
    if action in {"open_short", "increase_short", "reduce_short", "cover_short", "bearish_underlying_path_but_no_short_allowed"}:
        return "short"
    expression_type = _first_text(row, ("decision_expression_type", "selected_option_expression_type"))
    if expression_type == "long_call":
        return "long"
    if expression_type == "long_put":
        return "short"
    if action in {"", "no_trade", "skip", "hold", "reject_entry_thesis"}:
        return "flat"
    return "unknown"


def _decision_intended_action(row: Mapping[str, Any]) -> str:
    return _first_text(
        row,
        (
            "decision_intended_action",
            "4_resolved_underlying_action_type",
            "resolved_underlying_action_type",
            "planned_underlying_action_type",
            "decision_action",
            "action",
        ),
    ) or ""


def _selected_option_right(row: Mapping[str, Any]) -> str:
    explicit = _first_text(row, ("selected_option_right", "option_right", "right"))
    value = str(explicit or "").strip().lower()
    if value in {"c", "call"}:
        return "call"
    if value in {"p", "put"}:
        return "put"
    expression_type = _first_text(row, ("decision_expression_type", "selected_option_expression_type"))
    if expression_type == "long_call":
        return "call"
    if expression_type == "long_put":
        return "put"
    contract_ref = _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")) or ""
    if "_C_" in contract_ref:
        return "call"
    if "_P_" in contract_ref:
        return "put"
    return "none"


def _directional_underlying_return(row: Mapping[str, Any]) -> float | None:
    explicit = _safe_float(row.get("directional_underlying_return"))
    if explicit is not None:
        return explicit
    underlying_return = _safe_float(row.get("underlying_return"))
    if underlying_return is None:
        entry = _safe_float(row.get("bar_close"))
        exit_value = _safe_float(row.get("next_bar_close"))
        if entry is not None and exit_value is not None and entry > 0:
            underlying_return = (exit_value - entry) / entry
    if underlying_return is None:
        return None
    side = _decision_intended_side(row)
    if side == "short":
        return -underlying_return
    if side == "long":
        return underlying_return
    return 0.0


def _option_direction_consistency_status(row: Mapping[str, Any]) -> str:
    explicit = _first_text(row, ("option_direction_consistency_status",))
    if explicit:
        return explicit
    side = _decision_intended_side(row)
    right = _selected_option_right(row)
    expression_type = _first_text(row, ("decision_expression_type", "selected_option_expression_type"))
    expression_type = str(expression_type or "")
    if expression_type == "long_call" or right == "call":
        return "aligned" if side == "long" else "mismatch"
    if expression_type == "long_put" or right == "put":
        return "aligned" if side == "short" else "mismatch"
    if expression_type in {"underlying_equity", "underlying_only_expression", "underlying_only"}:
        return "underlying_expression"
    if expression_type == "no_option_expression":
        return "no_option_expression"
    return "unknown"


def _normalize_side(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"long", "buy", "bullish"}:
        return "long"
    if normalized in {"short", "sell_short", "bearish"}:
        return "short"
    if normalized in {"flat", "none", "cash", "no_trade"}:
        return "flat"
    return "unknown"


def _replacement_review_rows(rows: Iterable[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    ranked = sorted(
        rows,
        key=lambda row: (
            -(_safe_float(row.get("portfolio_switch_rank_score_delta")) or 0.0),
            str(row.get("replay_time_pointer") or row.get("timestamp") or ""),
            str(row.get("target_ref") or ""),
        ),
    )
    return [
        {
            "target_ref": str(row.get("target_ref") or ""),
            "replay_time_pointer": str(row.get("replay_time_pointer") or row.get("timestamp") or ""),
            "portfolio_replacement_evaluation_status": str(row.get("portfolio_replacement_evaluation_status") or ""),
            "portfolio_selection_action": str(row.get("portfolio_selection_action") or ""),
            "portfolio_selection_reason": str(row.get("portfolio_selection_reason") or ""),
            "candidate_rank_score": _round_metric_nullable(_safe_float(row.get("portfolio_candidate_rank_score"))),
            "weakest_held_target_before": str(row.get("portfolio_worst_held_target_before") or ""),
            "weakest_held_rank_score_before": _round_metric_nullable(
                _safe_float(row.get("portfolio_worst_held_rank_score_before"))
            ),
            "switch_rank_score_delta": _round_metric_nullable(_safe_float(row.get("portfolio_switch_rank_score_delta"))),
            "switch_minimum_rank_score_delta": _round_metric_nullable(
                _safe_float(row.get("portfolio_switch_minimum_rank_score_delta"))
            ),
        }
        for row in ranked[:limit]
    ]


def _layer_differentiation_summary(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    decisions = list(rows)
    diagnostics_by_layer: dict[str, list[Mapping[str, Any]]] = {
        "model_01_background_context": [],
        "model_02_target_state": [],
        "model_03_event_state": [],
        "model_04_unified_decision": [],
        "model_05_option_expression": [],
        "model_06_residual_event_governance": [],
    }
    for row in decisions:
        diagnostics = row.get("model_layer_diagnostics")
        if not isinstance(diagnostics, MappingABC):
            continue
        for layer in diagnostics_by_layer:
            value = diagnostics.get(layer)
            if isinstance(value, MappingABC):
                diagnostics_by_layer[layer].append(value)
    return {
        layer: _diagnostic_variation_summary(items)
        for layer, items in diagnostics_by_layer.items()
    }


def _diagnostic_variation_summary(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = list(items)
    scalar_keys: set[str] = set()
    for row in rows:
        for key, value in row.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                scalar_keys.add(str(key))
    varying_keys = []
    constant_keys = []
    for key in sorted(scalar_keys):
        values = {json.dumps(row.get(key), sort_keys=True) for row in rows}
        if len(values) > 1:
            varying_keys.append(key)
        elif values:
            constant_keys.append(key)
    return {
        "row_count": len(rows),
        "scalar_key_count": len(scalar_keys),
        "varying_scalar_keys": varying_keys,
        "constant_scalar_key_count": len(constant_keys),
        "differentiation_status": "has_target_or_time_variation" if varying_keys else ("constant_or_missing" if rows else "missing"),
    }


def _model_candidate_selection_trace_path(replay_receipt: Mapping[str, Any], *, dataset_root: Path) -> Path | None:
    explicit = str(replay_receipt.get("model_candidate_selection_trace_ref") or "").strip()
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "").strip()
    if not replay_run_id:
        return None
    path = dataset_root / "replay_execution_runs" / replay_run_id / "model_candidate_selection_trace.jsonl"
    return path if path.exists() else None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _mean_float(values: Iterable[Any]) -> float | None:
    material = [float(value) for value in values if value is not None]
    if not material:
        return None
    return sum(material) / len(material)


def _median_float(values: Iterable[Any]) -> float | None:
    material = sorted(float(value) for value in values if value is not None)
    if not material:
        return None
    midpoint = len(material) // 2
    if len(material) % 2:
        return material[midpoint]
    return (material[midpoint - 1] + material[midpoint]) / 2


def _round_metric_nullable(value: float | None) -> float | None:
    return None if value is None else _round_metric(float(value))


def _count_text(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        counts[text] = counts.get(text, 0) + 1
    return dict(sorted(counts.items()))


def _top_regret_rows(rows: list[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    ranked: list[tuple[float, Mapping[str, Any]]] = []
    for row in rows:
        regret = _safe_float(row.get("regret_to_best_available"))
        if regret is None or regret <= 0:
            continue
        ranked.append((regret, row))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            "source_decision_id": str(row.get("source_decision_id") or ""),
            "replay_month": row.get("replay_month"),
            "target_symbol": row.get("target_symbol"),
            "first_gap_component": row.get("first_gap_component"),
            "first_gap_mechanism": row.get("first_gap_mechanism"),
            "best_available_action_by_future_outcome": row.get("best_available_action_by_future_outcome"),
            "regret_to_best_available": _round_metric(regret),
        }
        for regret, row in ranked[:limit]
    ]


def _available_actions(row: Mapping[str, Any], *, filled: bool, opportunity_return: float | None) -> list[str]:
    explicit = _explicit_available_actions(row)
    if explicit:
        return explicit
    chosen_action = _chosen_action(row, filled=filled)
    actions = [chosen_action]
    if filled:
        if _safe_float(row.get("baseline_return")) is not None:
            actions.append("baseline_action")
    elif opportunity_return is not None and _miss_review_scope(
        filled=False,
        path_conditioning_policy=_path_conditioning_policy(row),
        candidate_set_scope=_candidate_set_scope(row),
        miss_attribution_layer=_miss_attribution_layer(row, filled=False),
    ) == "path_conditioned_current_scope":
        actions.append("path_conditioned_take_opportunity")
    return _dedupe_text(actions)


def _action_return(
    action: str,
    *,
    filled: bool,
    realized_return: float | None,
    baseline_return: float,
    opportunity_return: float | None,
) -> float | None:
    if _is_no_trade_action(action) or action == "baseline_action":
        return baseline_return
    if action == "path_conditioned_take_opportunity":
        return opportunity_return
    if action == "take_trade":
        return realized_return if filled else opportunity_return
    return realized_return if filled else opportunity_return


def _is_no_trade_action(action: str) -> bool:
    normalized = action.strip().lower()
    if normalized in {"reject_or_no_trade", "no_trade", "hold_cash", "baseline_no_trade"}:
        return True
    return normalized.startswith("reject")


def _first_gap_component(
    row: Mapping[str, Any],
    *,
    filled: bool,
    best_available_action: str,
    chosen_action: str,
    miss_attribution_layer: str,
) -> str:
    explicit = _first_text(
        row,
        (
            "first_gap_component",
            "component_attribution",
            "failure_component",
            "first_failure_component",
        ),
    )
    if explicit:
        return explicit
    if best_available_action == chosen_action:
        return "no_gap"
    if not filled:
        return miss_attribution_layer
    if best_available_action == "baseline_action":
        return "execution_or_position_management"
    return "taken_decision"


def _first_gap_mechanism(
    row: Mapping[str, Any],
    *,
    filled: bool,
    best_available_action: str,
    chosen_action: str,
) -> str:
    explicit = _first_text(
        row,
        (
            "first_gap_mechanism",
            "gap_mechanism",
            "component_gap_mechanism",
            "failure_mechanism",
            "decision_gap_type",
        ),
    )
    if explicit:
        return explicit
    if best_available_action == chosen_action:
        return "no_gap"
    decision_status = str(row.get("decision_status") or "").lower()
    rejection_reason = str(row.get("rejection_reason") or row.get("gate_reason") or row.get("block_reason") or "").lower()
    if not filled:
        if "rank" in rejection_reason or "score" in rejection_reason:
            return "ranking"
        if "threshold" in rejection_reason or "gate" in rejection_reason or "block" in rejection_reason or decision_status in {"rejected", "blocked"}:
            return "gate"
        if "timing" in rejection_reason or "late" in rejection_reason or "early" in rejection_reason:
            return "timing"
        return "filtering"
    if best_available_action == "baseline_action":
        if "size" in rejection_reason or "sizing" in rejection_reason:
            return "sizing"
        if "fill" in rejection_reason or "slippage" in rejection_reason or "execution" in rejection_reason:
            return "execution"
        return "execution_or_position_management"
    return "decision"


def _layer_attribution_basis(
    *,
    filled: bool,
    best_available_action: str,
    chosen_action: str,
    miss_review_scope: str,
) -> str:
    if best_available_action == chosen_action:
        return "chosen action matched the best available action inside the point-in-time action set"
    if not filled:
        return f"missed opportunity was reviewable only within {miss_review_scope}"
    return "filled action underperformed the available baseline action inside the point-in-time action set"


def _explicit_available_actions(row: Mapping[str, Any]) -> list[str]:
    for key in (
        "available_action",
        "available_actions",
        "available_action_set",
        "replay_available_action",
        "replay_available_actions",
        "point_in_time_available_action",
        "point_in_time_available_actions",
    ):
        value = row.get(key)
        actions = _normalize_action_list(value)
        if actions:
            return actions
    return []


def _normalize_action_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return [text]
            return _normalize_action_list(parsed)
        if "," in text:
            return _dedupe_text(part.strip() for part in text.split(","))
        return [text]
    if isinstance(value, MappingABC):
        return [json.dumps(value, sort_keys=True)]
    if isinstance(value, IterableABC):
        normalized: list[str] = []
        for item in value:
            if isinstance(item, MappingABC):
                normalized.append(json.dumps(item, sort_keys=True))
            else:
                text = str(item).strip()
                if text:
                    normalized.append(text)
        return _dedupe_text(normalized)
    text = str(value).strip()
    return [text] if text else []


def _dedupe_text(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _chosen_action(row: Mapping[str, Any], *, filled: bool) -> str:
    explicit = _first_text(
        row,
        (
            "chosen_action",
            "decision_action",
            "action",
            "selected_action",
            "recommended_action",
            "order_action",
            "decision_disposition",
        ),
    )
    if explicit:
        return explicit
    return "take_trade" if filled else "reject_or_no_trade"


def _future_outcome_window(row: Mapping[str, Any], *, decision_time: str | None) -> str | None:
    explicit = _first_text(
        row,
        (
            "future_outcome_window",
            "outcome_window",
            "replay_outcome_window",
            "label_window",
            "holding_window",
        ),
    )
    if explicit:
        return explicit
    exit_time = _first_text(
        row,
        (
            "exit_time",
            "next_timestamp",
            "label_time",
            "outcome_time",
            "selected_option_exit_time",
            "underlying_exit_time",
        ),
    )
    if decision_time and exit_time:
        return f"{decision_time}->{exit_time}"
    return "replay_future_outcome_label"


def _best_available_action_by_future_outcome(
    row: Mapping[str, Any],
    *,
    filled: bool,
    available_actions: list[str],
    chosen_action: str,
    realized_return: float | None,
    baseline_return: float,
    opportunity_return: float | None,
) -> str:
    explicit = _first_text(row, ("best_available_action_by_future_outcome", "best_available_action", "replay_best_available_action"))
    if explicit and explicit in available_actions:
        return explicit
    if filled and "baseline_action" in available_actions and realized_return is not None and baseline_return > realized_return:
        return "baseline_action"
    if not filled and "path_conditioned_take_opportunity" in available_actions and opportunity_return is not None and opportunity_return > baseline_return:
        return "path_conditioned_take_opportunity"
    return chosen_action


def _regret_to_best_available(
    *,
    filled: bool,
    chosen_action: str,
    best_available_action: str,
    realized_return: float | None,
    baseline_return: float,
    opportunity_return: float | None,
) -> float | None:
    if best_available_action == chosen_action:
        return 0.0
    if filled:
        if realized_return is None:
            return None
        return _round_metric(max(0.0, baseline_return - realized_return))
    if opportunity_return is None:
        return None
    return _round_metric(max(0.0, opportunity_return - baseline_return))


def _opportunity_return(row: Mapping[str, Any]) -> float | None:
    explicit = _first_float(
        row,
        (
            "opportunity_return",
            "candidate_opportunity_return",
            "missed_opportunity_return",
            "replay_opportunity_return",
        ),
    )
    if explicit is not None:
        return explicit
    option_entry = _first_float(row, ("option_entry_price", "selected_option_entry_price"))
    option_exit = _first_float(row, ("option_exit_price", "selected_option_exit_price"))
    if option_entry is not None and option_exit is not None and option_entry > 0:
        return (option_exit - option_entry) / option_entry
    underlying_entry = _first_float(row, ("bar_close", "underlying_entry_price", "entry_underlying_price"))
    underlying_exit = _first_float(row, ("next_bar_close", "underlying_exit_price", "exit_underlying_price"))
    if underlying_entry is not None and underlying_exit is not None and underlying_entry > 0:
        return (underlying_exit - underlying_entry) / underlying_entry
    return None


def _first_float(row: Mapping[str, Any], keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = _safe_float(row.get(key))
        if value is not None:
            return value
    return None


def _round_metric(value: float) -> float:
    return round(value, 10)


def _diagnostic_threshold_severity(*breaches: float | None) -> float:
    material = [value for value in breaches if value is not None and value > 0]
    return _round_metric(min(1.0, max(material))) if material else 0.0


def _impact_profile(row: Mapping[str, Any], *, failure_type: str, decision_time: str | None) -> dict[str, Any]:
    explicit_onset = _first_text(
        row,
        (
            "impact_exposure_time",
            "impact_onset_time",
            "impact_start_time",
            "adverse_move_start_time",
            "drawdown_start_time",
            "market_impact_start_time",
        ),
    )
    impact_exposure_time = explicit_onset or decision_time
    realized_return = _safe_float(row.get("realized_return")) or 0.0
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    raw_delta = realized_return - baseline_return
    magnitude = abs(raw_delta)
    denominator = _impact_normalization_denominator(row)
    normalized = magnitude / denominator if denominator and denominator > 0 else magnitude
    if denominator and denominator > 0:
        severity_basis = "target_normalized_return_move"
    else:
        severity_basis = "raw_return_without_target_volatility_normalization"
    if failure_type == "rejected_positive_missed_opportunity":
        direction = "missed_upside"
    elif raw_delta < 0:
        direction = "adverse_downside"
    elif raw_delta > 0:
        direction = "relative_underperformance"
    else:
        direction = "outcome_failure_without_return_delta"
    return {
        "impact_exposure_time": impact_exposure_time,
        "impact_onset_time": impact_exposure_time,
        "impact_onset_basis": "source_impact_clock" if explicit_onset else "decision_time_fallback",
        "impact_scope_type": str(row.get("impact_scope_type") or row.get("scope_type") or "target").strip() or "target",
        "impact_direction": direction,
        "impact_raw_return_delta": raw_delta,
        "impact_magnitude_abs_return": magnitude,
        "impact_normalization_denominator": denominator,
        "impact_normalized_severity_score": normalized,
        "impact_severity_basis": severity_basis,
    }


def _impact_normalization_denominator(row: Mapping[str, Any]) -> float | None:
    for key in (
        "target_expected_move_abs_return",
        "expected_move_abs_return",
        "target_intraday_volatility",
        "target_realized_volatility",
        "realized_volatility",
        "atr_percent",
        "average_true_range_percent",
    ):
        value = _safe_float(row.get(key))
        if value and value > 0:
            return value
    return None


def _first_text(row: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return None


def _decision_time(row: Mapping[str, Any]) -> str | None:
    for key in ("decision_time", "timestamp", "decision_timestamp", "created_at", "created_at_utc"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return None


def _replay_month(row: Mapping[str, Any]) -> str | None:
    explicit_month = str(row.get("month") or row.get("replay_month") or "").strip()
    if explicit_month:
        return explicit_month
    timestamp = str(row.get("timestamp") or row.get("decision_timestamp") or "").strip()
    if len(timestamp) >= 7:
        return timestamp[:7]
    return None


def _target_symbol(row: Mapping[str, Any]) -> str | None:
    for key in ("target_symbol", "symbol", "target_ref"):
        value = str(row.get(key) or "").strip()
        if value:
            return value.split("-")[0].upper()
    instrument_ref = str(row.get("instrument_ref") or "").strip()
    if instrument_ref:
        return instrument_ref.split("-")[0].upper()
    return None


def _path_conditioning_policy(row: Mapping[str, Any]) -> str:
    value = _first_text(row, ("path_conditioning_policy", "replay_path_conditioning_policy"))
    return value or "upstream_selected_path_only"


def _path_scope(row: Mapping[str, Any]) -> str:
    value = _first_text(row, ("path_scope", "replay_path_scope"))
    if value:
        return value
    target = _target_symbol(row)
    if target:
        return f"selected_target:{target}"
    return "selected_path:unknown"


def _candidate_set_scope(row: Mapping[str, Any]) -> str:
    value = _first_text(row, ("candidate_set_scope", "replay_candidate_set_scope"))
    if value:
        return value
    if _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")):
        return "selected_target_selected_option_contract_path"
    instrument_scope = str(row.get("decision_instrument_scope") or "").strip()
    if instrument_scope == "listed_option_contract":
        return "selected_target_option_expression_candidates"
    if instrument_scope == "underlying_equity":
        return "selected_target_underlying_decision"
    return "selected_path_current_decision_set"


def _miss_attribution_layer(row: Mapping[str, Any], *, filled: bool) -> str:
    value = _first_text(row, ("miss_attribution_layer", "replay_miss_attribution_layer"))
    if value:
        return value
    if filled:
        return "taken_decision"
    if _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")):
        return "model_05_option_expression"
    instrument_scope = str(row.get("decision_instrument_scope") or "").strip()
    if instrument_scope == "underlying_equity":
        return "model_04_unified_decision"
    return "current_decision_layer"


def _miss_review_scope(
    *,
    filled: bool,
    path_conditioning_policy: str,
    candidate_set_scope: str,
    miss_attribution_layer: str,
) -> str:
    if filled:
        return "taken_decision"
    if path_conditioning_policy in {"global_hindsight_oracle", "unconditioned_global_universe", "best_path_hindsight"}:
        return "not_path_conditioned"
    if candidate_set_scope.startswith("global_") or miss_attribution_layer in {"global_hindsight_oracle", "best_path_hindsight"}:
        return "not_path_conditioned"
    return "path_conditioned_current_scope"


def _replay_row_needs_attribution(row: Mapping[str, Any]) -> bool:
    fill_status = str(row.get("fill_status") or "")
    decision_status = str(row.get("decision_status") or "")
    outcome_label = _int_field(row, "outcome_label")
    realized_return = _safe_float(row.get("realized_return"))
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    filled = fill_status == "simulated_filled" or decision_status in {"filled", "approved", "executed"}
    if filled:
        if outcome_label == 0:
            return True
        if realized_return is not None and realized_return <= baseline_return:
            return True
        return False
    if outcome_label != 1:
        return False
    return (
        _miss_review_scope(
            filled=False,
            path_conditioning_policy=_path_conditioning_policy(row),
            candidate_set_scope=_candidate_set_scope(row),
            miss_attribution_layer=_miss_attribution_layer(row, filled=False),
        )
        == "path_conditioned_current_scope"
    )


def _latest_replay_execution_receipt(
    dataset_root: Path,
    *,
    replay_execution_run_id: str | None = None,
) -> dict[str, Any] | None:
    replay_root = dataset_root / "replay_execution_runs"
    if not replay_root.exists():
        return None
    if replay_execution_run_id:
        receipt_path = replay_root / replay_execution_run_id / "replay_execution_receipt.json"
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            return None
        if not _replay_receipt_full_completion_scope(receipt):
            return None
        if not _replay_receipt_uses_current_candidate_handoff(receipt):
            return None
        return dict(receipt)
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for receipt_path in sorted(replay_root.glob("*/replay_execution_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        if "current_deterministic_crypto_policy" in str(receipt.get("candidate_model_ref") or ""):
            continue
        if not _replay_receipt_full_completion_scope(receipt):
            continue
        if not _replay_receipt_uses_current_candidate_handoff(receipt):
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt.get("generated_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt_path, receipt))
    if not candidates:
        return None
    _created, _receipt_path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return dict(receipt)


def _replay_receipt_uses_current_candidate_handoff(receipt: Mapping[str, Any]) -> bool:
    target_refs = _string_set(receipt.get("target_refs") or receipt.get("pre_replay_target_refs"))
    asset_class_counts = receipt.get("asset_class_counts")
    if not isinstance(asset_class_counts, Mapping):
        asset_class_counts = {}
    has_equity_or_option_scope = (
        bool(target_refs)
        or int(asset_class_counts.get("us_equity") or 0) > 0
        or int(asset_class_counts.get("us_option") or 0) > 0
    )
    if not has_equity_or_option_scope:
        return True
    portfolio_policy = receipt.get("portfolio_replay_policy")
    if not isinstance(portfolio_policy, MappingABC):
        portfolio_policy = {}
    return (
        str(receipt.get("candidate_handoff_status") or "") == "available"
        and str(receipt.get("candidate_handoff_source") or "") in CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES
        and str(portfolio_policy.get("full_budget_replacement_policy") or "") == "continue_scanning_after_budget_full"
        and str(portfolio_policy.get("residual_cash_replacement_policy") or "")
        == "insufficient_cash_falls_through_to_replacement"
        and str(portfolio_policy.get("portfolio_capacity_policy") or "")
        == "default_5_simultaneous_risk_slots_from_20pct_allocation"
        and int(portfolio_policy.get("max_positions") or 0) == 5
        and str(portfolio_policy.get("position_sizing_policy") or "")
        == "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up"
        and str(portfolio_policy.get("switch_threshold_policy") or "") == "score_scale_aware_absolute_rank_delta"
    )


def _replay_receipt_full_completion_scope(receipt: Mapping[str, Any]) -> bool:
    completion_scope = str(receipt.get("replay_completion_scope") or "").strip()
    if completion_scope:
        return completion_scope == "full_candidate_universe" and receipt.get("max_decision_rows") is None
    return receipt.get("max_decision_rows") is None


def _latest_complete_replay_review_receipt(dataset_root: Path, *, decision_rows_ref: str) -> dict[str, Any] | None:
    review_root = dataset_root / "post_replay_review_runs"
    if not review_root.exists():
        return None
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    for receipt_path in sorted(review_root.glob("*/post_replay_review_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        status = str(receipt.get("status") or receipt.get("attribution_status") or "")
        if status not in {"succeeded", "complete", "completed"}:
            continue
        contract_type = str(receipt.get("contract_type") or "")
        if contract_type != REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE:
            continue
        if str(receipt.get("decision_rows_ref") or "") != decision_rows_ref:
            continue
        completion_scope = str(receipt.get("replay_review_completion_scope") or "").strip()
        if completion_scope and completion_scope != "full_replay_review":
            continue
        if receipt.get("max_review_rows") is not None:
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt))
    if not candidates:
        return None
    _created, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return dict(receipt)


def _expected_replay_months(dataset_root: Path) -> int:
    months = _unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month")
    if months:
        return len(months)
    rows = _csv_rows(dataset_root / "replay_window_manifest.csv")
    if not rows:
        return 60
    try:
        start = datetime.fromisoformat(str(rows[0].get("start_date"))).date()
        end = datetime.fromisoformat(str(rows[0].get("end_date"))).date()
    except (TypeError, ValueError):
        return 60
    return max(1, (end.year - start.year) * 12 + end.month - start.month)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _ready_replay_months(dataset_root: Path, *, replay_run_id: str) -> set[str]:
    ready: set[str] = set()
    paths = sorted((dataset_root / "replay_runs").glob("*.jsonl")) + [dataset_root / "replay_progress.jsonl"]
    for path in paths:
        if not path.exists():
            continue
        for row in _load_jsonl_objects(path):
            if replay_run_id and str(row.get("replay_execution_run_id") or "") != replay_run_id:
                continue
            status = str(row.get("status") or row.get("replay_status") or "").lower()
            month = str(row.get("month") or row.get("replay_month") or "").strip()
            if month and status in {"succeeded", "completed", "complete"}:
                ready.add(month)
    return ready


def _replay_dataset_root(storage_root: Path, contract_id: str) -> Path:
    return storage_root.parent / "05_replay_datasets" / contract_id


def _load_optional_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(dict(row), sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _unique_csv_values(path: Path, field: str) -> set[str]:
    return {str(row.get(field) or "").strip() for row in _csv_rows(path) if str(row.get(field) or "").strip()}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


def _int_field(row: Mapping[str, Any], key: str) -> int | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE",
    "REPLAY_REVIEW_ROW_CONTRACT_TYPE",
    "run_model_group_replay_review_if_ready",
]

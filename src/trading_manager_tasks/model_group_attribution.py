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
import json
import sys
from collections.abc import Iterable as IterableABC
from collections.abc import Mapping as MappingABC
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from .model_group_layer_attribution import build_model_group_layer_attribution
from .model_group_replay import CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES, DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE = "post_replay_review_receipt"
REPLAY_REVIEW_ROW_CONTRACT_TYPE = "post_replay_review_row"
REPLAY_REVIEW_DATA_REQUIREMENT_CONTRACT_TYPE = "post_replay_review_data_requirement"


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
    expected_months = _expected_replay_months(dataset_root)
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "")
    ready_months = _ready_replay_months(dataset_root, replay_run_id=replay_run_id)
    replay_complete = expected_months <= 0 or len(ready_months) >= expected_months
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
    if expected_months > 0 and len(ready_months) < expected_months and not allow_partial_replay:
        return None
    decision_rows_path = Path(str(replay_receipt.get("decision_rows_ref") or ""))
    if not decision_rows_path.exists():
        return None
    if not force and _latest_complete_replay_review_receipt(dataset_root, decision_rows_ref=str(decision_rows_path)) is not None:
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
    output_root = dataset_root / "post_replay_review_runs" / run_id
    review_rows_path = output_root / "replay_review_rows.jsonl"
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

    review_rows = tuple(_build_review_rows(decision_rows_path, max_rows=max_review_rows))
    decision_rows = tuple(_load_jsonl_objects(decision_rows_path))
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
            "replay_execution_receipt_ref": str(dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json")
            if replay_run_id
            else None,
            "review_rows_ref": str(review_rows_path),
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
            "review_rows_ref": str(review_rows_path),
            "reviewed_failure_count": len(review_rows),
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
        "planned_notional_total": _round_metric_nullable(sum(value for value in notional_by_row if value is not None)),
        "gross_pnl_total": _round_metric_nullable(sum(pnl_values)),
        "gross_return_on_used_notional": _round_metric_nullable(
            sum(pnl_values) / sum(value for value in notional_by_row if value is not None)
        )
        if sum(value for value in notional_by_row if value is not None) > 0
        else None,
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
        },
        "decision_scope": decision_scope,
        "target_performance": target_performance,
        "stock_selection": stock_selection,
        "replacement_review": replacement_review,
        "option_expression": option_expression,
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
                "option_contract_path_status": str(row.get("option_contract_path_status") or ""),
            }
        )
    output.sort(key=lambda item: (item["realized_return"] is None, item["realized_return"] or 0.0), reverse=True)
    return output


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
    normalized = magnitude / denominator if denominator and denominator > 0 else None
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

"""Build fixed-input M04/M05 layer-attribution diagnostics for replay rows."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_TAIL_ROW_LIMIT = 20
DEFAULT_HIGH_SCORE_THRESHOLD = 0.8
DEFAULT_PARAMETER_BUCKET_COUNT = 5
DEFAULT_MIN_TRADE_INTENSITY = 0.05
MIN_PARAMETER_SAMPLE_COUNT = 50
MIN_PARAMETER_UNIQUE_VALUES = 3
MIN_PARAMETER_FILLED_COUNT = 30
MIN_PARAMETER_ABS_CORRELATION = 0.08
MIN_PARAMETER_RETURN_SPREAD = 0.01
MIN_PARAMETER_LABEL_RATE_SPREAD = 0.05
MIN_PARAMETER_FILL_RATE_SPREAD = 0.15
SUSPECT_PARAMETER_COUNTERFACTUAL_FIELDNAMES = [
    "parameter_name",
    "parameter_family",
    "expected_direction",
    "primary_followup_mode",
    "reason_codes",
    "all_row_inversion_supported",
    "filled_only_inversion_supported",
    "all_label_inversion_supported",
    "filled_subset_selection_effect_supported",
    "m04_open_filled_inversion_supported",
    "m04_family_suspect_parameter_count",
    "sample_count",
    "filled_count",
    "nonfilled_count",
    "m04_open_count",
    "m04_open_filled_count",
    "value_mean",
    "filled_value_mean",
    "nonfilled_value_mean",
    "label_spearman",
    "return_spearman",
    "filled_return_spearman",
    "m04_open_filled_return_spearman",
    "high_minus_low_label_rate",
    "high_minus_low_return_per_row",
    "filled_high_minus_low_return_per_row",
    "m04_open_filled_high_minus_low_return_per_row",
    "low_bucket_fill_rate",
    "high_bucket_fill_rate",
    "high_minus_low_fill_rate",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M04_COMPONENT_DIAGNOSTIC_FIELDNAMES = [
    "component_name",
    "subset_name",
    "expected_direction",
    "diagnostic_status",
    "reason_codes",
    "row_count",
    "filled_count",
    "value_mean",
    "label_spearman",
    "return_spearman",
    "high_minus_low_label_rate",
    "high_minus_low_return_per_row",
    "low_bucket_fill_rate",
    "high_bucket_fill_rate",
    "high_minus_low_fill_rate",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M05_SELECTION_MECHANICS_FIELDNAMES = [
    "m04_state",
    "m05_state",
    "execution_expression_state",
    "option_feasibility_state",
    "selected_expression_type",
    "primary_filter_reason",
    "row_count",
    "filled_count",
    "filled_good_count",
    "filled_bad_count",
    "label_rate",
    "mean_prediction_score",
    "net_return_total",
    "return_per_row",
    "filled_hit_rate",
    "positive_label_count",
    "positive_underlying_return_total",
    "candidate_count_before_filter_mean",
    "candidate_count_after_filter_mean",
    "eligible_candidate_count_mean",
    "top_contract_fit_score_mean",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M04_VARIANT_COUNTERFACTUAL_FIELDNAMES = [
    "variant_name",
    "subset_name",
    "formula",
    "expected_direction",
    "diagnostic_status",
    "reason_codes",
    "row_count",
    "filled_count",
    "value_mean",
    "label_spearman",
    "return_spearman",
    "high_minus_low_label_rate",
    "high_minus_low_return_per_row",
    "low_bucket_fill_rate",
    "high_bucket_fill_rate",
    "high_minus_low_fill_rate",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
PORTFOLIO_CAPACITY_COUNTERFACTUAL_FIELDNAMES = [
    "variant_name",
    "ranking_metric",
    "max_positions",
    "budget_fraction",
    "selected_count",
    "excluded_count",
    "selected_good_count",
    "selected_bad_count",
    "selected_hit_rate",
    "selected_realized_return_total",
    "selected_return_per_row",
    "excluded_good_count",
    "excluded_bad_count",
    "excluded_realized_return_total",
    "excluded_return_per_row",
    "selected_planned_notional_total",
    "budget_used_fraction",
    "budget_blocked_count",
    "position_blocked_count",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M05_DTE_POLICY_SENSITIVITY_FIELDNAMES = [
    "sensitivity_case",
    "selected_expression_type",
    "primary_filter_reason",
    "diagnostic_status",
    "reason_codes",
    "row_count",
    "positive_label_count",
    "label_rate",
    "underlying_return_total",
    "positive_underlying_return_total",
    "candidate_count_before_filter_mean",
    "candidate_count_after_filter_mean",
    "eligible_candidate_count_mean",
    "dte_fail_count_mean",
    "non_dte_fail_count_mean",
    "dte_fail_share_mean",
    "top_contract_fit_score_mean",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
M05_HARD_FILTER_OVERLAP_FIELDNAMES = [
    "overlap_group",
    "selected_expression_type",
    "primary_filter_reason",
    "filter_reason_set",
    "filter_reason_count",
    "row_count",
    "positive_label_count",
    "label_rate",
    "underlying_return_total",
    "positive_underlying_return_total",
    "candidate_count_before_filter_mean",
    "candidate_count_after_filter_mean",
    "eligible_candidate_count_mean",
    "top_contract_fit_score_mean",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
DECISION_SURFACE_COMPONENT_MATRIX_FIELDNAMES = [
    "decision_id",
    "timestamp",
    "target_ref",
    "decision_status",
    "decision_action",
    "fill_status",
    "first_limiting_surface",
    "first_limiting_surface_reason",
    "settled_metric_eligible",
    "model_01_background_context_ref_status",
    "model_02_target_state_ref_status",
    "model_03_event_state_ref_status",
    "model_04_unified_decision_ref_status",
    "model_05_option_expression_ref_status",
    "model_04_score_coverage_count",
    "model_04_resolved_action",
    "model_04_reason_codes",
    "option_expression_surface_state",
    "selected_option_contract_ref",
    "selected_option_expression_type",
    "selected_option_path_status",
    "prediction_score",
    "outcome_label",
    "realized_return",
    "fixed_input_only",
]
COMPONENT_MODEL_MAPPING_FIELDNAMES = [
    "component_surface",
    "model_layer",
    "explicit_ref_count",
    "evidence_chain_count",
    "diagnostic_surface_count",
    "decision_surface_count",
    "first_limiting_surface_count",
    "settled_metric_eligible_count",
    "mapping_status",
    "fixed_input_only",
]
COMPONENT_SURFACE_ORDER = [
    "C01_background_context_surface",
    "C02_target_state_surface",
    "C03_event_state_surface",
    "C04_underlying_decision_surface",
    "C05_option_expression_surface",
    "C06_selected_option_path_materialization",
    "C07_portfolio_execution_surface",
    "C08_settled_prediction_quality_surface",
]
COMPONENT_SURVIVAL_QUALITY_FLOW_FIELDNAMES = [
    "component_index",
    "component_surface",
    "model_layer",
    "entered_count",
    "first_limiting_count",
    "blocked_count",
    "censored_count",
    "passed_count",
    "settled_metric_eligible_count",
    "settled_metric_excluded_count",
    "outcome_metric_available",
    "mean_prediction_score",
    "score_label_spearman",
    "score_return_spearman",
    "mean_realized_return",
    "hit_rate",
    "tail_loss_count",
    "prior_bad_cohort_count",
    "post_component_bad_cohort_count",
    "stage_verdict",
    "verdict_basis",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
COMPONENT_REVIEW_PACKET_FIELDNAMES = [
    "component_index",
    "component_surface",
    "model_layer",
    "component_role",
    "input_count",
    "output_count",
    "dropped_or_blocked_count",
    "changed_or_transformed_count",
    "settled_metric_eligible_count",
    "survival_verdict",
    "survival_verdict_basis",
    "attribution_coverage_status",
    "point_in_time_evidence_status",
    "outcome_label_role",
    "internal_review_refs",
    "missing_review_outputs",
    "explicit_ref_count",
    "evidence_chain_count",
    "diagnostic_surface_count",
    "decision_surface_count",
    "first_limiting_surface_count",
    "can_assign_model_blame",
    "interpretation_status",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
COMPONENT_ROLE_BY_SURFACE = {
    "C01_background_context_surface": "background_context_selection",
    "C02_target_state_surface": "target_state_selection",
    "C03_event_state_surface": "event_state_context",
    "C04_underlying_decision_surface": "underlying_action_gate",
    "C05_option_expression_surface": "option_expression_selection",
    "C06_selected_option_path_materialization": "selected_contract_path_materialization",
    "C07_portfolio_execution_surface": "portfolio_execution_and_fill",
    "C08_settled_prediction_quality_surface": "settled_outcome_quality",
}
OPERATION_COMPONENT_SPECS = [
    {
        "component_index": 1,
        "operation_component_id": "C01_intake_operation",
        "runtime_component_ref": "component_01_intake",
        "operation_component_label": "C01 Intake",
        "operation_role": "prepare target, context, and point-in-time inputs for an entry decision",
        "entry_path_participant": True,
    },
    {
        "component_index": 2,
        "operation_component_id": "C02_entry_operation",
        "runtime_component_ref": "component_02_entry",
        "operation_component_label": "C02 Entry",
        "operation_role": "decide whether the target should enter a new position",
        "entry_path_participant": True,
    },
    {
        "component_index": 3,
        "operation_component_id": "C03_lifecycle_operation",
        "runtime_component_ref": "component_03_lifecycle",
        "operation_component_label": "C03 Lifecycle",
        "operation_role": "manage open-position continuity, held-target continuation, and replacement policy",
        "entry_path_participant": True,
    },
    {
        "component_index": 4,
        "operation_component_id": "C04_expression_review_operation",
        "runtime_component_ref": "component_04_expression_review",
        "operation_component_label": "C04 Expression Review",
        "operation_role": "choose and materialize the trade expression before order intent",
        "entry_path_participant": True,
    },
    {
        "component_index": 5,
        "operation_component_id": "C05_order_intent_operation",
        "runtime_component_ref": "component_05_order_intent",
        "operation_component_label": "C05 Order Intent",
        "operation_role": "turn an approved expression into sized order intent",
        "entry_path_participant": True,
    },
    {
        "component_index": 6,
        "operation_component_id": "C06_execution_gate_operation",
        "runtime_component_ref": "component_06_execution_gate",
        "operation_component_label": "C06 Execution Gate",
        "operation_role": "apply execution, fill, and broker-safety gates",
        "entry_path_participant": True,
    },
    {
        "component_index": 7,
        "operation_component_id": "C07_failure_review_operation",
        "runtime_component_ref": "component_07_failure_review",
        "operation_component_label": "C07 Failure Review",
        "operation_role": "review residual risk, settlement quality, and failure attribution after action",
        "entry_path_participant": True,
    },
]
OPERATION_COMPONENT_BY_ID = {
    str(spec["operation_component_id"]): spec
    for spec in OPERATION_COMPONENT_SPECS
}
OPERATION_COMPONENT_ANALYSIS_METHODS = {
    "C01_intake_operation": {
        "analysis_method": "point_in_time_source_candidate_and_sector_intake_review",
        "evidence_role": "source_candidate_context_readiness",
        "label_role": "forward_return_labels_only_for_intake_opportunity_review",
    },
    "C02_entry_operation": {
        "analysis_method": "entry_candidate_rank_signal_and_action_gate_review",
        "evidence_role": "entry_gate_and_underlying_action_surface",
        "label_role": "post_replay_return_labels_for_entry_quality_review",
    },
    "C03_lifecycle_operation": {
        "analysis_method": "portfolio_lifecycle_state_transition_and_replacement_policy_review",
        "evidence_role": "open_position_state_and_replacement_policy_evidence",
        "label_role": "operational_state_transition_counts_not_future_return_decision_inputs",
    },
    "C04_expression_review_operation": {
        "analysis_method": "option_expression_funnel_materialization_and_contract_path_review",
        "evidence_role": "option_expression_candidate_set_and_selected_contract_path",
        "label_role": "post_replay_return_labels_for_expression_quality_review",
    },
    "C05_order_intent_operation": {
        "analysis_method": "order_intent_sizing_capacity_and_budget_contract_review",
        "evidence_role": "sizing_notional_capacity_and_order_intent_evidence",
        "label_role": "capacity_counterfactual_labels_are_post_replay_diagnostics",
    },
    "C06_execution_gate_operation": {
        "analysis_method": "execution_path_fill_and_materialization_gate_review",
        "evidence_role": "selected_contract_path_fill_and_execution_gate_evidence",
        "label_role": "fill_coverage_status_not_model_alpha_label",
    },
    "C07_failure_review_operation": {
        "analysis_method": "settled_failure_review_and_residual_gap_explanation_review",
        "evidence_role": "post_action_failure_review_and_settlement_evidence",
        "label_role": "settled_outcomes_are_review_labels_not_model_decision_inputs",
    },
}
OPERATION_COMPONENT_OBJECTIVES = {
    "C01_intake_operation": "publish point-in-time eligible candidates and context without future labels",
    "C02_entry_operation": "admit or suppress model trade intent within the decision-time feasible action set",
    "C03_lifecycle_operation": "apply legal portfolio lifecycle transitions before new exposure or replacement",
    "C04_expression_review_operation": "materialize the requested exposure into the best feasible tradable expression",
    "C05_order_intent_operation": "convert feasible expression into capital-constrained sized order intent",
    "C06_execution_gate_operation": "execute or reject the order plan under replay/live fill and broker-safety rules",
    "C07_failure_review_operation": "classify settled operational failures without feeding labels back into decisions",
}
OPERATION_COMPONENT_LAYER_LABEL_SOURCE = {
    "C02_entry_operation": "model_04_unified_decision",
    "C04_expression_review_operation": "model_05_option_expression",
}
OPERATION_REVIEW_PROJECTION_BY_SURFACE = {
    "C01_background_context_surface": {
        "operation_component_id": "C01_intake_operation",
        "review_projection": "background_context",
        "review_projection_role": "point_in_time_context_input",
    },
    "C02_target_state_surface": {
        "operation_component_id": "C01_intake_operation",
        "review_projection": "target_state",
        "review_projection_role": "target_state_input",
    },
    "C03_event_state_surface": {
        "operation_component_id": "C02_entry_operation",
        "review_projection": "event_state",
        "review_projection_role": "entry_event_context",
    },
    "C04_underlying_decision_surface": {
        "operation_component_id": "C02_entry_operation",
        "review_projection": "underlying_entry_decision",
        "review_projection_role": "entry_action_gate",
    },
    "C05_option_expression_surface": {
        "operation_component_id": "C04_expression_review_operation",
        "review_projection": "option_expression_selection",
        "review_projection_role": "expression_selection_gate",
    },
    "C06_selected_option_path_materialization": {
        "operation_component_id": "C04_expression_review_operation",
        "review_projection": "selected_contract_path_materialization",
        "review_projection_role": "expression_materialization_gate",
    },
    "C07_portfolio_execution_surface": {
        "operation_component_id": "C06_execution_gate_operation",
        "review_projection": "execution_fill",
        "review_projection_role": "fill_and_execution_gate",
    },
    "C08_settled_prediction_quality_surface": {
        "operation_component_id": "C07_failure_review_operation",
        "review_projection": "settled_prediction_quality",
        "review_projection_role": "retrospective_settlement_quality",
    },
}
OPERATION_REVIEW_PROJECTION_MATRIX_FIELDNAMES = [
    "decision_id",
    "timestamp",
    "target_ref",
    "source_decision_surface",
    "source_surface_reason",
    "operation_component_id",
    "runtime_component_ref",
    "operation_component_label",
    "review_projection",
    "review_projection_role",
    "projection_status",
    "settled_metric_eligible",
    "prediction_score",
    "outcome_label",
    "realized_return",
    "fixed_input_only",
]
OPERATION_COMPONENT_FLOW_FIELDNAMES = [
    "component_index",
    "operation_component_id",
    "runtime_component_ref",
    "operation_component_label",
    "operation_role",
    "applicability_status",
    "input_count",
    "output_count",
    "dropped_or_blocked_count",
    "censored_count",
    "settled_metric_eligible_count",
    "settled_metric_excluded_count",
    "first_limiting_projection_count",
    "first_limiting_projections",
    "review_projection_refs",
    "outcome_metric_available",
    "mean_prediction_score",
    "score_label_spearman",
    "score_return_spearman",
    "mean_realized_return",
    "hit_rate",
    "tail_loss_count",
    "stage_verdict",
    "verdict_basis",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
OPERATION_COMPONENT_REVIEW_PACKET_FIELDNAMES = [
    "component_index",
    "operation_component_id",
    "runtime_component_ref",
    "operation_component_label",
    "operation_role",
    "applicability_status",
    "input_count",
    "output_count",
    "dropped_or_blocked_count",
    "settled_metric_eligible_count",
    "survival_verdict",
    "survival_verdict_basis",
    "review_projections",
    "internal_review_refs",
    "missing_review_outputs",
    "metric_effectiveness_status",
    "metric_effectiveness_flags",
    "first_limiting_projection_count",
    "can_assign_operation_fault",
    "interpretation_status",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
OPERATION_COMPONENT_METRIC_FIELDNAMES = [
    "component_index",
    "operation_component_id",
    "runtime_component_ref",
    "operation_component_label",
    "metric_family",
    "metric_name",
    "metric_scope",
    "analysis_method",
    "evidence_role",
    "label_role",
    "required_evidence_status",
    "availability_status",
    "reason_codes",
    "point_in_time_input_fields",
    "future_outcome_fields",
    "row_count",
    "eligible_row_count",
    "selected_count",
    "universe_count_mean",
    "selected_target_present_count",
    "selected_forward_return_mean",
    "selected_forward_return_rank_mean",
    "selected_forward_return_percentile_mean",
    "top_quartile_hit_rate",
    "opportunity_cost_to_best_mean",
    "opportunity_cost_to_median_mean",
    "value",
    "diagnostic_only",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
OPERATION_COMPONENT_ACTION_FIELDNAMES = [
    "operation_action_row_id",
    "source_decision_id",
    "source_decision_index",
    "decision_time",
    "replay_month",
    "target_symbol",
    "operation_component_id",
    "runtime_component_ref",
    "operation_component_label",
    "component_index",
    "operation_action",
    "operation_status",
    "input_ref",
    "input_summary",
    "output_ref",
    "output_summary",
    "block_reason",
    "analysis_method",
    "evidence_role",
    "label_role",
    "trigger_state",
    "pit_feasible_action_set_ref",
    "pit_feasible_action_count",
    "pit_feasible_action_set_status",
    "review_boundary_ref",
    "review_boundary_status",
    "component_objective",
    "chosen_action",
    "best_available_action_by_future_outcome",
    "chosen_action_return",
    "best_available_action_return",
    "chosen_rank_ex_post",
    "component_correctness_class",
    "post_replay_label_basis",
    "upstream_decision_state_policy",
    "downstream_review_input_policy",
    "upstream_error_isolation_scope",
    "responsibility_assignment_policy",
    "decision_time_evidence_fields",
    "post_replay_label_fields",
    "realized_return",
    "regret_to_best_available",
    "impact_normalized_severity_score",
    "review_status",
    "fixed_input_only",
]
MODEL_CANDIDATE_SELECTION_SUMMARY_FIELDNAMES = [
    "timestamp",
    "model_rank_within_timestamp",
    "target_ref",
    "model_candidate_trace_status",
    "selected_by_replay",
    "diagnostic_rank_score",
    "alpha_score",
    "trade_intensity_score",
    "expected_return_score",
    "action_direction_score",
    "underlying_action_type",
    "action_side",
    "selected_option_contract_ref",
    "option_expression_unexecutable_reason",
    "option_expression_route",
    "option_surface_status",
    "selected_expression_type",
    "candidate_count_before_filter",
    "candidate_count_after_filter",
    "eligible_candidate_count",
    "top_contract_fit_score",
    "option_hard_filter_reason_counts",
    "fixed_input_only",
]
PRE_OPTION_CANDIDATE_QUALITY_FIELDNAMES = [
    "cohort_name",
    "cohort_role",
    "row_count",
    "matched_outcome_count",
    "status_counts",
    "option_expression_unexecutable_reason_counts",
    "model_rank_mean",
    "forward_return_mean",
    "global_forward_return_percentile_mean",
    "global_top_quartile_hit_rate",
    "within_sector_forward_return_percentile_mean",
    "within_sector_top_quartile_hit_rate",
    "diagnostic_only",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]
OPERATION_MECHANISM_CONTRACT_FIELDNAMES = [
    "mechanism_contract_id",
    "operation_component_id",
    "runtime_component_ref",
    "mechanism_contract",
    "breach_status",
    "severity",
    "breach_statement",
    "evidence_refs",
    "trigger_metrics",
    "systemic_closure_requirement",
    "acceptance_gate",
    "forbidden_actions",
    "diagnostic_only",
    "threshold_selection_performed",
    "retraining_performed",
    "fixed_input_only",
]


def build_model_group_layer_attribution(
    *,
    decision_rows_path: Path,
    output_dir: Path,
    replay_receipt_path: Path | None = None,
    promotion_review_path: Path | None = None,
    m05_unfilled_diagnostics_path: Path | None = None,
    counterfactual_gate_sweep_path: Path | None = None,
    target_selection_universe_metrics_path: Path | None = None,
    model_candidate_selection_trace_path: Path | None = None,
    layer_review_rows: Sequence[Mapping[str, Any]] = (),
    run_id: str | None = None,
    now_utc: datetime | None = None,
    tail_row_limit: int = DEFAULT_TAIL_ROW_LIMIT,
    high_score_threshold: float = DEFAULT_HIGH_SCORE_THRESHOLD,
) -> dict[str, Any]:
    """Write a compact attribution report and supporting CSVs.

    The diagnostic is intentionally fixed-input: it reads replay decision rows
    and optional prior diagnostic CSV evidence, then writes derived summaries.
    It does not call providers, mutate SQL, activate models, or alter replay
    artifacts.
    """

    rows = tuple(_load_jsonl(decision_rows_path))
    if not rows:
        raise ValueError(f"decision rows are empty: {decision_rows_path}")
    replay_receipt = _load_json_file(replay_receipt_path)
    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id_value = run_id or "model_group_layer_attribution_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_dir.mkdir(parents=True, exist_ok=True)

    cohort_rows = _cohort_rows(rows)
    score_bin_rows = _filled_score_bin_rows(rows)
    tail_rows = _tail_loss_rows(rows, limit=tail_row_limit)
    top_gain_rows = _top_gain_rows(rows, limit=tail_row_limit)
    drawdown_summary = _drawdown_summary(rows)
    m05_unfilled_summary = _m05_unfilled_summary(m05_unfilled_diagnostics_path)
    expression_rows = _load_csv_rows(m05_unfilled_diagnostics_path)
    expression_rows_by_timestamp = _expression_rows_by_timestamp(expression_rows)
    replay_timestamp_counts = Counter(str(row.get("timestamp") or "") for row in rows)
    counterfactual_rows = _counterfactual_rows(rows, expression_rows_by_timestamp, replay_timestamp_counts)
    counterfactual_summary = _counterfactual_summary(
        rows=rows,
        counterfactual_rows=counterfactual_rows,
        score_bin_rows=score_bin_rows,
    )
    decision_surface_rows = _decision_surface_component_matrix_rows(rows)
    component_model_mapping_rows = _component_model_mapping_rows(rows, decision_surface_rows)
    component_survival_quality_flow_rows = _component_survival_quality_flow_rows(
        decision_surface_rows,
        component_model_mapping_rows,
    )
    component_survival_quality_flow_report = _component_survival_quality_flow_report(
        component_survival_quality_flow_rows
    )
    parameter_review = _parameter_replay_review(rows)
    m04_component_rows = _m04_component_diagnostic_rows(rows)
    m05_selection_rows = _m05_selection_mechanics_rows(rows, counterfactual_rows)
    m04_variant_rows = _m04_variant_counterfactual_rows(rows)
    portfolio_capacity_rows = _portfolio_capacity_counterfactual_rows(rows)
    portfolio_capacity_report = _portfolio_capacity_counterfactual_report(portfolio_capacity_rows)
    m05_dte_sensitivity_rows = _m05_dte_policy_sensitivity_rows(rows, counterfactual_rows)
    m05_hard_filter_overlap_rows = _m05_hard_filter_overlap_rows(rows, counterfactual_rows)
    mechanism_review_report = _m04_m05_mechanism_review_report(
        m04_component_rows=m04_component_rows,
        m05_selection_rows=m05_selection_rows,
        m04_variant_rows=m04_variant_rows,
        m05_dte_sensitivity_rows=m05_dte_sensitivity_rows,
        m05_hard_filter_overlap_rows=m05_hard_filter_overlap_rows,
    )
    component_review_packet = _component_review_packet(
        component_survival_quality_flow_rows=component_survival_quality_flow_rows,
        component_model_mapping_rows=component_model_mapping_rows,
        m05_unfilled_summary=m05_unfilled_summary,
        output_dir=output_dir,
    )
    operation_review_projection_rows = _operation_review_projection_matrix_rows(decision_surface_rows)
    operation_component_flow_rows = _operation_component_flow_rows(
        decision_surface_rows,
        operation_review_projection_rows,
        replay_receipt=replay_receipt,
    )
    operation_component_action_rows = _operation_component_action_rows(
        rows=rows,
        decision_surface_rows=decision_surface_rows,
        operation_review_projection_rows=operation_review_projection_rows,
        replay_receipt=replay_receipt,
        layer_review_rows=layer_review_rows,
    )
    target_selection_universe_rows = _load_csv_rows(target_selection_universe_metrics_path)
    model_candidate_selection_trace_path = _resolved_model_candidate_selection_trace_path(
        model_candidate_selection_trace_path=model_candidate_selection_trace_path,
        replay_receipt_path=replay_receipt_path,
    )
    model_candidate_selection_trace_rows = tuple(_load_jsonl(model_candidate_selection_trace_path)) if model_candidate_selection_trace_path else ()
    model_candidate_selection_summary_rows = _model_candidate_selection_summary_rows(
        model_candidate_selection_trace_rows
    )
    model_candidate_selection_summary_report = _model_candidate_selection_summary_report(
        model_candidate_selection_trace_rows,
        model_candidate_selection_summary_rows,
    )
    pre_option_candidate_quality_rows = _pre_option_candidate_quality_rows(
        trace_rows=model_candidate_selection_trace_rows,
        target_selection_universe_rows=target_selection_universe_rows,
    )
    pre_option_candidate_quality_report = _pre_option_candidate_quality_report(pre_option_candidate_quality_rows)
    operation_component_metric_rows = _operation_component_metric_rows(
        rows=rows,
        target_selection_universe_rows=target_selection_universe_rows,
        portfolio_capacity_rows=portfolio_capacity_rows,
        model_candidate_selection_trace_rows=model_candidate_selection_trace_rows,
        replay_receipt=replay_receipt,
    )
    operation_component_metric_report = _operation_component_metric_report(operation_component_metric_rows)
    sector_opportunity_packet_path = _sector_opportunity_packet_path(target_selection_universe_metrics_path)
    operation_component_review_packet = _operation_component_review_packet(
        operation_component_flow_rows=operation_component_flow_rows,
        operation_review_projection_rows=operation_review_projection_rows,
        operation_component_metric_rows=operation_component_metric_rows,
        component_model_mapping_rows=component_model_mapping_rows,
        m05_unfilled_summary=m05_unfilled_summary,
        sector_opportunity_packet_available=sector_opportunity_packet_path is not None,
        model_candidate_selection_trace_available=bool(model_candidate_selection_trace_rows),
        replay_receipt_available=replay_receipt_path is not None,
        output_dir=output_dir,
    )
    operation_mechanism_contract_rows = _operation_mechanism_contract_rows(
        operation_component_metric_rows=operation_component_metric_rows,
        model_candidate_selection_summary=model_candidate_selection_summary_report["summary"],
        pre_option_candidate_quality_rows=pre_option_candidate_quality_rows,
    )
    operation_mechanism_contract_packet = _operation_mechanism_contract_packet(operation_mechanism_contract_rows)
    gate_sweep_summary = _counterfactual_gate_sweep_summary(counterfactual_gate_sweep_path)
    tail_loss_packet, matched_tail_rows = _high_score_tail_loss_attribution_packet(
        rows=rows,
        counterfactual_summary=counterfactual_summary,
        decision_rows_path=decision_rows_path,
        m05_unfilled_diagnostics_path=m05_unfilled_diagnostics_path,
        output_dir=output_dir,
        high_score_threshold=high_score_threshold,
        now_utc=now,
    )

    _write_csv(output_dir / "m04_m05_cohorts.csv", cohort_rows)
    _write_csv(output_dir / "filled_score_bins.csv", score_bin_rows)
    _write_csv(output_dir / "tail_loss_rows.csv", tail_rows)
    _write_csv(output_dir / "top_gain_rows.csv", top_gain_rows)
    _write_csv(output_dir / "row_counterfactual_attribution.csv", counterfactual_rows)
    _write_csv(
        output_dir / "decision_surface_component_matrix.csv",
        decision_surface_rows,
        fieldnames=DECISION_SURFACE_COMPONENT_MATRIX_FIELDNAMES,
    )
    _write_csv(
        output_dir / "component_model_mapping.csv",
        component_model_mapping_rows,
        fieldnames=COMPONENT_MODEL_MAPPING_FIELDNAMES,
    )
    _write_csv(
        output_dir / "component_survival_quality_flow.csv",
        component_survival_quality_flow_rows,
        fieldnames=COMPONENT_SURVIVAL_QUALITY_FLOW_FIELDNAMES,
    )
    _write_csv(
        output_dir / "component_review_packet.csv",
        component_review_packet["component_rows"],
        fieldnames=COMPONENT_REVIEW_PACKET_FIELDNAMES,
    )
    _write_csv(
        output_dir / "operation_review_projection_matrix.csv",
        operation_review_projection_rows,
        fieldnames=OPERATION_REVIEW_PROJECTION_MATRIX_FIELDNAMES,
    )
    _write_csv(
        output_dir / "operation_component_flow.csv",
        operation_component_flow_rows,
        fieldnames=OPERATION_COMPONENT_FLOW_FIELDNAMES,
    )
    _write_csv(
        output_dir / "operation_component_review_packet.csv",
        operation_component_review_packet["component_rows"],
        fieldnames=OPERATION_COMPONENT_REVIEW_PACKET_FIELDNAMES,
    )
    _write_csv(
        output_dir / "operation_component_metrics.csv",
        operation_component_metric_rows,
        fieldnames=OPERATION_COMPONENT_METRIC_FIELDNAMES,
    )
    _write_csv(
        output_dir / "operation_component_action_rows.csv",
        operation_component_action_rows,
        fieldnames=OPERATION_COMPONENT_ACTION_FIELDNAMES,
    )
    _write_csv(
        output_dir / "model_candidate_selection_summary.csv",
        model_candidate_selection_summary_rows,
        fieldnames=MODEL_CANDIDATE_SELECTION_SUMMARY_FIELDNAMES,
    )
    _write_csv(
        output_dir / "pre_option_candidate_quality.csv",
        pre_option_candidate_quality_rows,
        fieldnames=PRE_OPTION_CANDIDATE_QUALITY_FIELDNAMES,
    )
    _write_csv(
        output_dir / "operation_mechanism_contract_packet.csv",
        operation_mechanism_contract_rows,
        fieldnames=OPERATION_MECHANISM_CONTRACT_FIELDNAMES,
    )
    _write_csv(output_dir / "high_score_filled_tail_loss_matches.csv", matched_tail_rows)
    _write_csv(output_dir / "parameter_replay_review.csv", parameter_review["parameter_rows"])
    _write_csv(output_dir / "parameter_bucket_metrics.csv", parameter_review["bucket_rows"])
    _write_csv(output_dir / "categorical_parameter_replay_review.csv", parameter_review["categorical_rows"])
    _write_csv(
        output_dir / "suspect_parameter_counterfactual.csv",
        parameter_review["suspect_counterfactual_rows"],
        fieldnames=SUSPECT_PARAMETER_COUNTERFACTUAL_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m04_component_diagnostics.csv",
        m04_component_rows,
        fieldnames=M04_COMPONENT_DIAGNOSTIC_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m05_selection_mechanics.csv",
        m05_selection_rows,
        fieldnames=M05_SELECTION_MECHANICS_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m04_variant_counterfactual.csv",
        m04_variant_rows,
        fieldnames=M04_VARIANT_COUNTERFACTUAL_FIELDNAMES,
    )
    _write_csv(
        output_dir / "portfolio_capacity_counterfactual.csv",
        portfolio_capacity_rows,
        fieldnames=PORTFOLIO_CAPACITY_COUNTERFACTUAL_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m05_dte_policy_sensitivity.csv",
        m05_dte_sensitivity_rows,
        fieldnames=M05_DTE_POLICY_SENSITIVITY_FIELDNAMES,
    )
    _write_csv(
        output_dir / "m05_hard_filter_overlap.csv",
        m05_hard_filter_overlap_rows,
        fieldnames=M05_HARD_FILTER_OVERLAP_FIELDNAMES,
    )
    (output_dir / "parameter_replay_review_report.json").write_text(
        json.dumps(parameter_review["report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "suspect_parameter_counterfactual_report.json").write_text(
        json.dumps(parameter_review["suspect_counterfactual_report"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "high_score_filled_tail_loss_attribution_packet.json").write_text(
        json.dumps(tail_loss_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "m04_m05_mechanism_review_report.json").write_text(
        json.dumps(mechanism_review_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "portfolio_capacity_counterfactual_report.json").write_text(
        json.dumps(portfolio_capacity_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "component_survival_quality_flow_report.json").write_text(
        json.dumps(component_survival_quality_flow_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "component_review_packet.json").write_text(
        json.dumps(component_review_packet["packet"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "operation_component_review_packet.json").write_text(
        json.dumps(operation_component_review_packet["packet"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "operation_component_metrics_report.json").write_text(
        json.dumps(operation_component_metric_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "model_candidate_selection_summary_report.json").write_text(
        json.dumps(model_candidate_selection_summary_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "pre_option_candidate_quality_report.json").write_text(
        json.dumps(pre_option_candidate_quality_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "operation_mechanism_contract_packet.json").write_text(
        json.dumps(operation_mechanism_contract_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if m05_unfilled_summary["source_status"] == "available":
        _write_csv(output_dir / "m05_unfilled_filter_reasons.csv", m05_unfilled_summary["filter_reason_rows"])

    report = {
        "contract_type": "model_group_layer_attribution_report",
        "run_id": run_id_value,
        "generated_at_utc": now.isoformat(),
        "decision_rows_ref": str(decision_rows_path),
        "replay_receipt_ref": str(replay_receipt_path) if replay_receipt_path else "",
        "promotion_review_ref": str(promotion_review_path) if promotion_review_path else "",
        "m05_unfilled_diagnostics_ref": str(m05_unfilled_diagnostics_path) if m05_unfilled_diagnostics_path else "",
        "counterfactual_gate_sweep_ref": str(counterfactual_gate_sweep_path) if counterfactual_gate_sweep_path else "",
        "target_selection_universe_metrics_ref": (
            str(target_selection_universe_metrics_path) if target_selection_universe_metrics_path else ""
        ),
        "sector_opportunity_packet_ref": str(sector_opportunity_packet_path or ""),
        "model_candidate_selection_trace_ref": str(model_candidate_selection_trace_path or ""),
        "model_candidate_selection_summary_ref": str(output_dir / "model_candidate_selection_summary.csv"),
        "model_candidate_selection_summary_report_ref": str(
            output_dir / "model_candidate_selection_summary_report.json"
        ),
        "model_candidate_selection_summary": model_candidate_selection_summary_report["summary"],
        "pre_option_candidate_quality_ref": str(output_dir / "pre_option_candidate_quality.csv"),
        "pre_option_candidate_quality_report_ref": str(output_dir / "pre_option_candidate_quality_report.json"),
        "pre_option_candidate_quality_summary": pre_option_candidate_quality_report["summary"],
        "operation_mechanism_contract_packet_ref": str(output_dir / "operation_mechanism_contract_packet.json"),
        "operation_mechanism_contract_packet_csv_ref": str(output_dir / "operation_mechanism_contract_packet.csv"),
        "operation_mechanism_contract_packet_summary": operation_mechanism_contract_packet["summary"],
        "row_scope": _row_scope(rows),
        "layer_status": _layer_status(rows),
        "cohorts": cohort_rows,
        "filled_score_bins": score_bin_rows,
        "drawdown_summary": drawdown_summary,
        "tail_loss_rows_ref": str(output_dir / "tail_loss_rows.csv"),
        "top_gain_rows_ref": str(output_dir / "top_gain_rows.csv"),
        "row_counterfactual_attribution_ref": str(output_dir / "row_counterfactual_attribution.csv"),
        "decision_surface_component_matrix_ref": str(output_dir / "decision_surface_component_matrix.csv"),
        "component_model_mapping_ref": str(output_dir / "component_model_mapping.csv"),
        "decision_surface_summary": _decision_surface_summary(decision_surface_rows),
        "component_model_mapping_summary": _component_model_mapping_summary(component_model_mapping_rows),
        "component_survival_quality_flow_ref": str(output_dir / "component_survival_quality_flow.csv"),
        "component_survival_quality_flow_report_ref": str(
            output_dir / "component_survival_quality_flow_report.json"
        ),
        "component_survival_quality_flow_summary": component_survival_quality_flow_report["summary"],
        "component_review_packet_ref": str(output_dir / "component_review_packet.json"),
        "component_review_packet_csv_ref": str(output_dir / "component_review_packet.csv"),
        "component_review_packet_summary": component_review_packet["packet"]["summary"],
        "operation_review_projection_matrix_ref": str(output_dir / "operation_review_projection_matrix.csv"),
        "operation_component_flow_ref": str(output_dir / "operation_component_flow.csv"),
        "operation_component_review_packet_ref": str(output_dir / "operation_component_review_packet.json"),
        "operation_component_review_packet_csv_ref": str(output_dir / "operation_component_review_packet.csv"),
        "operation_component_review_packet_summary": operation_component_review_packet["packet"]["summary"],
        "operation_component_metrics_ref": str(output_dir / "operation_component_metrics.csv"),
        "operation_component_metrics_report_ref": str(output_dir / "operation_component_metrics_report.json"),
        "operation_component_metrics_summary": operation_component_metric_report["summary"],
        "operation_component_action_rows_ref": str(output_dir / "operation_component_action_rows.csv"),
        "operation_component_action_row_count": len(operation_component_action_rows),
        "canonical_operation_components": [
            {
                "operation_component_id": str(spec["operation_component_id"]),
                "runtime_component_ref": str(spec["runtime_component_ref"]),
                "operation_component_label": str(spec["operation_component_label"]),
                "entry_path_participant": bool(spec["entry_path_participant"]),
            }
            for spec in OPERATION_COMPONENT_SPECS
        ],
        "high_score_filled_tail_loss_attribution_packet_ref": str(
            output_dir / "high_score_filled_tail_loss_attribution_packet.json"
        ),
        "high_score_filled_tail_loss_matches_ref": str(output_dir / "high_score_filled_tail_loss_matches.csv"),
        "high_score_filled_tail_loss_summary": tail_loss_packet["headline"],
        "row_counterfactual_summary": counterfactual_summary,
        "parameter_replay_review_ref": str(output_dir / "parameter_replay_review.csv"),
        "parameter_replay_review_report_ref": str(output_dir / "parameter_replay_review_report.json"),
        "parameter_bucket_metrics_ref": str(output_dir / "parameter_bucket_metrics.csv"),
        "categorical_parameter_replay_review_ref": str(output_dir / "categorical_parameter_replay_review.csv"),
        "parameter_replay_review_summary": parameter_review["summary"],
        "suspect_parameter_counterfactual_ref": str(output_dir / "suspect_parameter_counterfactual.csv"),
        "suspect_parameter_counterfactual_report_ref": str(
            output_dir / "suspect_parameter_counterfactual_report.json"
        ),
        "suspect_parameter_counterfactual_summary": parameter_review["suspect_counterfactual_summary"],
        "m04_component_diagnostics_ref": str(output_dir / "m04_component_diagnostics.csv"),
        "m05_selection_mechanics_ref": str(output_dir / "m05_selection_mechanics.csv"),
        "m04_variant_counterfactual_ref": str(output_dir / "m04_variant_counterfactual.csv"),
        "portfolio_capacity_counterfactual_ref": str(output_dir / "portfolio_capacity_counterfactual.csv"),
        "portfolio_capacity_counterfactual_report_ref": str(output_dir / "portfolio_capacity_counterfactual_report.json"),
        "portfolio_capacity_counterfactual_summary": portfolio_capacity_report["summary"],
        "m05_dte_policy_sensitivity_ref": str(output_dir / "m05_dte_policy_sensitivity.csv"),
        "m05_hard_filter_overlap_ref": str(output_dir / "m05_hard_filter_overlap.csv"),
        "m04_m05_mechanism_review_report_ref": str(output_dir / "m04_m05_mechanism_review_report.json"),
        "m04_m05_mechanism_review_summary": mechanism_review_report["summary"],
        "counterfactual_gate_sweep_summary": gate_sweep_summary,
        "m05_unfilled_summary": {
            key: value for key, value in m05_unfilled_summary.items() if key != "filter_reason_rows"
        },
        "verdict": _verdict(
            rows=rows,
            cohort_rows=cohort_rows,
            score_bin_rows=score_bin_rows,
            counterfactual_summary=counterfactual_summary,
        ),
        "side_effects": {
            "provider_call_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
            "sql_mutation_performed": False,
            "storage_source_mutation_performed": False,
            "model_activation_performed": False,
            "active_model_config_written": False,
        },
    }
    (output_dir / "layer_attribution_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _load_json_file(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolved_model_candidate_selection_trace_path(
    *,
    model_candidate_selection_trace_path: Path | None,
    replay_receipt_path: Path | None,
) -> Path | None:
    if model_candidate_selection_trace_path is not None:
        return model_candidate_selection_trace_path if model_candidate_selection_trace_path.exists() else None
    receipt = _load_json_file(replay_receipt_path)
    ref = str(receipt.get("model_candidate_selection_trace_ref") or "").strip()
    if not ref:
        return None
    path = Path(ref)
    return path if path.exists() else None


def _model_candidate_selection_summary_rows(trace_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        trace_rows,
        key=lambda row: (
            str(row.get("replay_time_pointer") or row.get("timestamp") or ""),
            int(_float(row.get("model_rank_within_timestamp"), default=10**9)),
            str(row.get("target_ref") or ""),
        ),
    )
    output: list[dict[str, Any]] = []
    for row in ranked:
        if not _truthy(row.get("model_score_available")):
            continue
        output.append(
            {
                "timestamp": str(row.get("replay_time_pointer") or row.get("timestamp") or ""),
                "model_rank_within_timestamp": int(_float(row.get("model_rank_within_timestamp"), default=0.0)),
                "target_ref": str(row.get("target_ref") or ""),
                "model_candidate_trace_status": str(row.get("model_candidate_trace_status") or ""),
                "selected_by_replay": _truthy(row.get("selected_by_replay")),
                "diagnostic_rank_score": _round(_float(row.get("diagnostic_rank_score"))),
                "alpha_score": _round(_float(row.get("alpha_score"))),
                "trade_intensity_score": _round(_float(row.get("trade_intensity_score"))),
                "expected_return_score": _round(_float(row.get("expected_return_score"))),
                "action_direction_score": _round(_float(row.get("action_direction_score"))),
                "underlying_action_type": str(row.get("underlying_action_type") or ""),
                "action_side": str(row.get("action_side") or ""),
                "selected_option_contract_ref": str(row.get("selected_option_contract_ref") or ""),
                "option_expression_unexecutable_reason": str(row.get("option_expression_unexecutable_reason") or ""),
                "option_expression_route": str(row.get("option_expression_route") or ""),
                "option_surface_status": str(row.get("option_surface_status") or ""),
                "selected_expression_type": str(row.get("selected_expression_type") or ""),
                "candidate_count_before_filter": int(
                    _float(row.get("candidate_count_before_filter"), default=0.0)
                ),
                "candidate_count_after_filter": int(_float(row.get("candidate_count_after_filter"), default=0.0)),
                "eligible_candidate_count": int(_float(row.get("eligible_candidate_count"), default=0.0)),
                "top_contract_fit_score": _round(_float(row.get("top_contract_fit_score"))),
                "option_hard_filter_reason_counts": _json_dumps_sorted(row.get("option_hard_filter_reason_counts")),
                "fixed_input_only": True,
            }
        )
    return output


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _json_dumps_sorted(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "{}"
    return json.dumps(_json_safe_mapping(value), sort_keys=True)


def _json_safe_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, item in sorted(value.items()):
        if isinstance(item, float) and math.isnan(item):
            output[str(key)] = None
        elif isinstance(item, Mapping):
            output[str(key)] = _json_safe_mapping(item)
        else:
            output[str(key)] = item
    return output


def _model_candidate_selection_summary_report(
    trace_rows: Sequence[Mapping[str, Any]],
    summary_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    status_counts = Counter(str(row.get("model_candidate_trace_status") or "unknown") for row in trace_rows)
    unexecutable_reason_counts = Counter(
        str(row.get("option_expression_unexecutable_reason") or "unknown")
        for row in trace_rows
        if str(row.get("model_candidate_trace_status") or "") == "option_expression_unexecutable"
    )
    hard_filter_reason_counts: Counter[str] = Counter()
    for row in trace_rows:
        if str(row.get("model_candidate_trace_status") or "") != "option_expression_unexecutable":
            continue
        reason_counts = row.get("option_hard_filter_reason_counts")
        if not isinstance(reason_counts, Mapping):
            continue
        for reason, count in reason_counts.items():
            hard_filter_reason_counts[str(reason)] += int(_float(count, default=0.0))
    selected_rows = [row for row in summary_rows if _truthy(row.get("selected_by_replay"))]
    top_ranked = [row for row in summary_rows if int(_float(row.get("model_rank_within_timestamp"), default=0.0)) <= 25]
    selected_targets = {str(row.get("target_ref") or "") for row in selected_rows}
    top_ranked_targets = {str(row.get("target_ref") or "") for row in top_ranked}
    selected_rank_values = [
        int(_float(row.get("model_rank_within_timestamp"), default=0.0))
        for row in selected_rows
        if row.get("model_rank_within_timestamp") not in {None, ""}
    ]
    selected_targets_outside_top_25_same_timestamp = sorted(
        str(row.get("target_ref") or "")
        for row in selected_rows
        if int(_float(row.get("model_rank_within_timestamp"), default=0.0)) > 25
    )
    selected_rank_bucket_counts = {
        "rank_1_to_10": sum(1 for rank in selected_rank_values if rank <= 10),
        "rank_11_to_25": sum(1 for rank in selected_rank_values if 10 < rank <= 25),
        "rank_26_to_50": sum(1 for rank in selected_rank_values if 25 < rank <= 50),
        "rank_over_50": sum(1 for rank in selected_rank_values if rank > 50),
    }
    return {
        "contract_type": "model_group_model_candidate_selection_summary_report",
        "summary": {
            "trace_row_count": len(trace_rows),
            "scored_candidate_row_count": len(summary_rows),
            "selected_candidate_row_count": len(selected_rows),
            "status_counts": dict(sorted(status_counts.items())),
            "option_expression_unexecutable_reason_counts": dict(sorted(unexecutable_reason_counts.items())),
            "option_hard_filter_reason_counts": dict(sorted(hard_filter_reason_counts.items())),
            "selected_target_count": len(selected_targets),
            "selected_candidate_rank_mean_same_timestamp": _round(_mean(selected_rank_values)),
            "selected_candidate_top_10_same_timestamp_count": selected_rank_bucket_counts["rank_1_to_10"],
            "selected_candidate_top_25_same_timestamp_count": (
                selected_rank_bucket_counts["rank_1_to_10"] + selected_rank_bucket_counts["rank_11_to_25"]
            ),
            "selected_candidate_outside_top_25_same_timestamp_count": len(
                selected_targets_outside_top_25_same_timestamp
            ),
            "selected_targets_outside_top_25_same_timestamp": selected_targets_outside_top_25_same_timestamp,
            "selected_rank_bucket_counts_same_timestamp": selected_rank_bucket_counts,
            "top_25_ranked_target_count": len(top_ranked_targets),
            "selected_targets_in_top_25_ranked_count": len(selected_targets & top_ranked_targets),
            "selected_targets_outside_top_25_ranked": sorted(selected_targets - top_ranked_targets),
            "top_25_ranked_not_selected_targets": sorted(top_ranked_targets - selected_targets),
            "future_outcome_label_included": False,
            "summary_role": "model_standard_candidate_discovery_and_selection_not_future_return_rank",
        },
        "top_model_ranked_candidates_sample": list(summary_rows[:25]),
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _pre_option_candidate_quality_rows(
    *,
    trace_rows: Sequence[Mapping[str, Any]],
    target_selection_universe_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not trace_rows or not target_selection_universe_rows:
        return []
    outcome_by_key: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in target_selection_universe_rows:
        timestamp = str(row.get("timestamp") or "")
        target_ref = str(row.get("target_ref") or row.get("symbol") or "")
        if timestamp and target_ref:
            outcome_by_key[(timestamp, target_ref)] = row
    scored_rows = [row for row in trace_rows if _truthy(row.get("model_score_available"))]
    if not scored_rows:
        return []

    def rank_between(row: Mapping[str, Any], low: int, high: int) -> bool:
        rank = int(_float(row.get("model_rank_within_timestamp"), default=10**9))
        return low <= rank <= high

    cohorts = [
        ("all_visible_scored", "all point-in-time scored visible candidates", scored_rows),
        (
            "pre_option_entry_intent",
            "candidates with underlying entry intent before option expression",
            [row for row in scored_rows if _truthy(row.get("option_expression_signal_required"))],
        ),
        (
            "model_rank_top_10_pre_option",
            "top 10 model-ranked underlying candidates before option expression",
            [row for row in scored_rows if rank_between(row, 1, 10)],
        ),
        (
            "model_rank_top_25_pre_option",
            "top 25 model-ranked underlying candidates before option expression",
            [row for row in scored_rows if rank_between(row, 1, 25)],
        ),
        (
            "model_rank_top_50_pre_option",
            "top 50 model-ranked underlying candidates before option expression",
            [row for row in scored_rows if rank_between(row, 1, 50)],
        ),
        (
            "option_executable_entry_intent",
            "entry-intent candidates with executable option expression",
            [
                row
                for row in scored_rows
                if str(row.get("model_candidate_trace_status") or "")
                in {"selected_by_replay", "scored_not_selected_by_portfolio"}
            ],
        ),
        (
            "option_unexecutable_entry_intent",
            "entry-intent candidates blocked before order intent by option expression",
            [
                row
                for row in scored_rows
                if str(row.get("model_candidate_trace_status") or "") == "option_expression_unexecutable"
            ],
        ),
        (
            "final_selected_after_option_expression",
            "portfolio-selected candidates after option expression and capital feasibility",
            [row for row in scored_rows if _truthy(row.get("selected_by_replay"))],
        ),
        (
            "no_entry_intent",
            "scored candidates rejected before option expression",
            [
                row
                for row in scored_rows
                if str(row.get("model_candidate_trace_status") or "") == "scored_no_entry_intent"
            ],
        ),
    ]
    return [
        _pre_option_candidate_quality_row(
            cohort_name=name,
            cohort_role=role,
            rows=rows,
            outcome_by_key=outcome_by_key,
        )
        for name, role, rows in cohorts
    ]


def _pre_option_candidate_quality_row(
    *,
    cohort_name: str,
    cohort_role: str,
    rows: Sequence[Mapping[str, Any]],
    outcome_by_key: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, Any]:
    matched: list[Mapping[str, Any]] = []
    ranks: list[float] = []
    returns: list[float] = []
    global_percentiles: list[float] = []
    sector_percentiles: list[float] = []
    global_top_quartile_hits = 0
    sector_top_quartile_hits = 0
    status_counts = Counter(str(row.get("model_candidate_trace_status") or "unknown") for row in rows)
    unexecutable_reason_counts = Counter(
        str(row.get("option_expression_unexecutable_reason") or "unknown")
        for row in rows
        if str(row.get("model_candidate_trace_status") or "") == "option_expression_unexecutable"
    )
    for row in rows:
        rank = _float(row.get("model_rank_within_timestamp"), default=float("nan"))
        if not math.isnan(rank):
            ranks.append(rank)
        timestamp = str(row.get("replay_time_pointer") or row.get("timestamp") or "")
        target_ref = str(row.get("target_ref") or "")
        outcome = outcome_by_key.get((timestamp, target_ref))
        if not outcome:
            continue
        matched.append(outcome)
        forward_return = _target_universe_forward_return(outcome)
        if forward_return is not None:
            returns.append(float(forward_return))
        global_percentile = _float(outcome.get("forward_return_percentile"), default=float("nan"))
        if not math.isnan(global_percentile):
            global_percentiles.append(global_percentile)
        sector_percentile = _float(outcome.get("forward_return_percentile_within_sector"), default=float("nan"))
        if not math.isnan(sector_percentile):
            sector_percentiles.append(sector_percentile)
        if _truthy(outcome.get("top_quartile_candidate")):
            global_top_quartile_hits += 1
        if _truthy(outcome.get("top_quartile_candidate_within_sector")):
            sector_top_quartile_hits += 1
    matched_count = len(matched)
    return {
        "cohort_name": cohort_name,
        "cohort_role": cohort_role,
        "row_count": len(rows),
        "matched_outcome_count": matched_count,
        "status_counts": _json_dumps_sorted(status_counts),
        "option_expression_unexecutable_reason_counts": _json_dumps_sorted(unexecutable_reason_counts),
        "model_rank_mean": _round(_mean(ranks)),
        "forward_return_mean": _round(_mean(returns)),
        "global_forward_return_percentile_mean": _round(_mean(global_percentiles)),
        "global_top_quartile_hit_rate": _round(global_top_quartile_hits / matched_count) if matched_count else None,
        "within_sector_forward_return_percentile_mean": _round(_mean(sector_percentiles)),
        "within_sector_top_quartile_hit_rate": _round(sector_top_quartile_hits / matched_count) if matched_count else None,
        "diagnostic_only": True,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _pre_option_candidate_quality_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows_by_name = {str(row.get("cohort_name") or ""): row for row in rows}
    entry = rows_by_name.get("pre_option_entry_intent", {})
    no_entry = rows_by_name.get("no_entry_intent", {})
    top25 = rows_by_name.get("model_rank_top_25_pre_option", {})
    all_visible = rows_by_name.get("all_visible_scored", {})
    flags: list[str] = []
    entry_percentile = _float(entry.get("global_forward_return_percentile_mean"), default=float("nan"))
    no_entry_percentile = _float(no_entry.get("global_forward_return_percentile_mean"), default=float("nan"))
    all_percentile = _float(all_visible.get("global_forward_return_percentile_mean"), default=float("nan"))
    top25_percentile = _float(top25.get("global_forward_return_percentile_mean"), default=float("nan"))
    if not math.isnan(entry_percentile) and not math.isnan(all_percentile) and entry_percentile < all_percentile:
        flags.append("entry_intent_underperforms_visible_universe")
    if not math.isnan(no_entry_percentile) and not math.isnan(entry_percentile) and no_entry_percentile > entry_percentile:
        flags.append("no_entry_candidates_outperform_entry_intent")
    if not math.isnan(top25_percentile) and top25_percentile > 0.55:
        flags.append("top_ranked_underlying_candidates_have_positive_signal")
    return {
        "contract_type": "model_group_pre_option_candidate_quality_report",
        "summary": {
            "cohort_count": len(rows),
            "entry_intent_global_percentile_mean": _round(entry_percentile if not math.isnan(entry_percentile) else None),
            "no_entry_global_percentile_mean": _round(no_entry_percentile if not math.isnan(no_entry_percentile) else None),
            "top25_global_percentile_mean": _round(top25_percentile if not math.isnan(top25_percentile) else None),
            "flags": flags,
            "fixed_input_only": True,
            "threshold_selection_performed": False,
            "retraining_performed": False,
        },
        "cohort_rows_ref": "pre_option_candidate_quality.csv",
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _operation_mechanism_contract_rows(
    *,
    operation_component_metric_rows: Sequence[Mapping[str, Any]],
    model_candidate_selection_summary: Mapping[str, Any],
    pre_option_candidate_quality_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    metrics_by_name = {str(row.get("metric_name") or ""): row for row in operation_component_metric_rows}
    cohorts_by_name = {str(row.get("cohort_name") or ""): row for row in pre_option_candidate_quality_rows}
    contracts: list[dict[str, Any]] = []

    sector_metric = metrics_by_name.get("selected_sector_bucket_forward_return_rank", {})
    sector_topq = _float(sector_metric.get("top_quartile_hit_rate"), default=float("nan"))
    sector_percentile = _float(sector_metric.get("selected_forward_return_percentile_mean"), default=float("nan"))
    sector_status = str(sector_metric.get("availability_status") or "")
    sector_breached = sector_status == "computed" and (
        (not math.isnan(sector_topq) and sector_topq < 0.25)
        or (not math.isnan(sector_percentile) and sector_percentile < 0.52)
    )
    contracts.append(
        _operation_mechanism_contract_row(
            mechanism_contract_id="mechanism_c01_sector_selection_effectiveness",
            component_id="C01_intake_operation",
            mechanism_contract="C01 must route candidate intake toward point-in-time sectors with measurable opportunity lift.",
            breach_status=_mechanism_breach_status(sector_status, sector_breached),
            severity="high" if sector_breached else "none",
            breach_statement=(
                "Selected sector buckets do not show enough top-quartile opportunity capture before target selection."
                if sector_breached
                else ""
            ),
            evidence_refs=["operation_component_metrics.csv", "target_selection_universe_metrics.csv"],
            trigger_metrics={
                "sector_top_quartile_hit_rate": sector_topq,
                "sector_forward_return_percentile_mean": sector_percentile,
            },
            systemic_closure_requirement=(
                "Maintain a fixed-input C01 sector opportunity contract that compares current sector routing against "
                "point-in-time sector momentum/dispersion/liquidity alternatives without changing thresholds from one run."
            ),
            acceptance_gate=(
                "Across at least 200 filled/evaluable timestamps, selected sector top-quartile hit is above 25% "
                "and mean sector percentile improves versus the current route without using future labels as inputs."
            ),
        )
    )

    entry = cohorts_by_name.get("pre_option_entry_intent", {})
    no_entry = cohorts_by_name.get("no_entry_intent", {})
    top25 = cohorts_by_name.get("model_rank_top_25_pre_option", {})
    entry_percentile = _float(entry.get("global_forward_return_percentile_mean"), default=float("nan"))
    no_entry_percentile = _float(no_entry.get("global_forward_return_percentile_mean"), default=float("nan"))
    top25_percentile = _float(top25.get("global_forward_return_percentile_mean"), default=float("nan"))
    entry_available = bool(str(entry.get("cohort_name") or ""))
    entry_breached = entry_available and (
        (not math.isnan(no_entry_percentile) and not math.isnan(entry_percentile) and no_entry_percentile > entry_percentile)
        or (not math.isnan(top25_percentile) and top25_percentile > entry_percentile + 0.05)
    )
    contracts.append(
        _operation_mechanism_contract_row(
            mechanism_contract_id="mechanism_c02_entry_gate_rank_curve",
            component_id="C02_entry_operation",
            mechanism_contract="C02/C04 entry gating must preserve top-ranked pre-option signal while rejecting weak broad cohorts.",
            breach_status="breached" if entry_breached else ("not_breached" if entry_available else "data_gap"),
            severity="high" if entry_breached else "none",
            breach_statement=(
                "Pre-option top-ranked candidates show signal, but the full entry-intent cohort is weak and "
                "no-entry candidates can outperform entry-intent candidates."
                if entry_breached
                else ""
            ),
            evidence_refs=["pre_option_candidate_quality.csv", "model_candidate_selection_summary.csv"],
            trigger_metrics={
                "entry_intent_global_percentile_mean": entry_percentile,
                "no_entry_global_percentile_mean": no_entry_percentile,
                "top25_global_percentile_mean": top25_percentile,
            },
            systemic_closure_requirement=(
                "Keep fixed-input C04 gate/rank curves for top-K, materiality, trade-intensity, no-trade probability, "
                "and expected-return filters as a standing entry-effectiveness contract."
            ),
            acceptance_gate=(
                "Entry-intent cohort must outperform visible universe and no-entry cohort; top-K lift must remain "
                "positive across multiple months before any threshold or model change is accepted."
            ),
        )
    )

    status_counts = model_candidate_selection_summary.get("status_counts") if isinstance(model_candidate_selection_summary, Mapping) else {}
    unexecutable_count = int(_float(_as_mapping(status_counts).get("option_expression_unexecutable"), default=0.0))
    selected_count = int(_float(model_candidate_selection_summary.get("selected_candidate_row_count"), default=0.0))
    hard_filter_counts = _as_mapping(model_candidate_selection_summary.get("option_hard_filter_reason_counts"))
    top25_selected = int(_float(model_candidate_selection_summary.get("selected_candidate_top_25_same_timestamp_count"), default=0.0))
    expression_evaluable = bool(model_candidate_selection_summary)
    expression_breached = expression_evaluable and unexecutable_count > selected_count
    contracts.append(
        _operation_mechanism_contract_row(
            mechanism_contract_id="mechanism_c04_expression_feasibility_policy",
            component_id="C04_expression_review_operation",
            mechanism_contract="C04 expression review must preserve feasible expression coverage for top-ranked entry candidates.",
            breach_status="breached" if expression_breached else ("not_breached" if expression_evaluable else "data_gap"),
            severity="critical" if expression_breached else "none",
            breach_statement=(
                "Many model-ranked entry candidates cannot become listed-option trades because M05 hard filters "
                "leave zero eligible contracts."
                if expression_breached
                else ""
            ),
            evidence_refs=["model_candidate_selection_summary_report.json", "pre_option_candidate_quality.csv"],
            trigger_metrics={
                "option_expression_unexecutable_count": unexecutable_count,
                "selected_candidate_count": selected_count,
                "hard_filter_reason_counts": dict(hard_filter_counts),
            },
            systemic_closure_requirement=(
                "Maintain fixed-input M05 policy counterfactuals for DTE, delta, spread, and strike-range constraints, "
                "and separate true source coverage gaps from policy infeasibility."
            ),
            acceptance_gate=(
                "Top-25 model-ranked candidate option-feasibility coverage materially improves, and any relaxed "
                "policy must preserve fill/path coverage and not use settlement labels for selection."
            ),
        )
    )

    feedback_breached = expression_evaluable and top25_selected < 15
    contracts.append(
        _operation_mechanism_contract_row(
            mechanism_contract_id="mechanism_c02_c04_feasibility_feedback_loop",
            component_id="C02_entry_operation",
            mechanism_contract="C02/C04 must close the interface between underlying rank and expression feasibility before order intent.",
            breach_status="breached" if feedback_breached else ("not_breached" if expression_evaluable else "data_gap"),
            severity="critical" if feedback_breached else "none",
            breach_statement=(
                "The portfolio receives a filtered executable subset rather than the true top-ranked underlying "
                "candidate list because option feasibility is learned after entry ranking."
                if feedback_breached
                else ""
            ),
            evidence_refs=["model_candidate_selection_summary.csv", "operation_component_flow.csv"],
            trigger_metrics={
                "selected_top25_same_timestamp_count": top25_selected,
                "selected_outside_top25_same_timestamp_count": int(
                    _float(model_candidate_selection_summary.get("selected_candidate_outside_top_25_same_timestamp_count"), default=0.0)
                ),
            },
            systemic_closure_requirement=(
                "C04 expression feasibility and expression-quality diagnostics must return to candidate ranking before "
                "C05 order intent construction, with audit rows for every lower-ranked replacement."
            ),
            acceptance_gate=(
                "Final selected candidates should mostly come from the feasible top-ranked cohort, with explicit "
                "audit rows for any lower-ranked replacement."
            ),
        )
    )

    capacity_metric = metrics_by_name.get("capacity_counterfactual_spread", {})
    capacity_value = _float(capacity_metric.get("value"), default=float("nan"))
    capacity_status = str(capacity_metric.get("availability_status") or "")
    capacity_breached = capacity_status == "computed"
    contracts.append(
        _operation_mechanism_contract_row(
            mechanism_contract_id="mechanism_c05_order_intent_capacity_guard",
            component_id="C05_order_intent_operation",
            mechanism_contract="C05 order intent must prove rank-aware capacity and concentration control over fixed inputs.",
            breach_status=_mechanism_breach_status(capacity_status, capacity_breached),
            severity="medium" if capacity_breached else "none",
            breach_statement=(
                "Order intent currently has only diagnostic capacity variants and must prove protection against noisy "
                "entry ranks, long-call crowding, or budget concentration."
                if capacity_breached
                else ""
            ),
            evidence_refs=["portfolio_capacity_counterfactual.csv", "operation_component_metrics.csv"],
            trigger_metrics={"capacity_counterfactual_best_minus_baseline": capacity_value},
            systemic_closure_requirement=(
                "C05 capacity contracts must include per-sector, per-expression, max-position, budget, and rank-quality "
                "guard variants over fixed inputs."
            ),
            acceptance_gate=(
                "A capacity guard must reduce tail exposure or improve selected cohort quality across multiple "
                "months without merely overfitting top-N on this 25-row sample."
            ),
        )
    )
    return contracts


def _mechanism_breach_status(availability_status: str, breached: bool) -> str:
    if availability_status == "computed":
        return "breached" if breached else "not_breached"
    if availability_status:
        return "data_gap"
    return "data_gap"


def _operation_mechanism_contract_row(
    *,
    mechanism_contract_id: str,
    component_id: str,
    mechanism_contract: str,
    breach_status: str,
    severity: str,
    breach_statement: str,
    evidence_refs: Sequence[str],
    trigger_metrics: Mapping[str, Any],
    systemic_closure_requirement: str,
    acceptance_gate: str,
) -> dict[str, Any]:
    component = OPERATION_COMPONENT_BY_ID.get(component_id) or {}
    return {
        "mechanism_contract_id": mechanism_contract_id,
        "operation_component_id": component_id,
        "runtime_component_ref": str(component.get("runtime_component_ref") or ""),
        "mechanism_contract": mechanism_contract,
        "breach_status": breach_status,
        "severity": severity,
        "breach_statement": breach_statement,
        "evidence_refs": ";".join(evidence_refs),
        "trigger_metrics": _json_dumps_sorted(trigger_metrics),
        "systemic_closure_requirement": systemic_closure_requirement,
        "acceptance_gate": acceptance_gate,
        "forbidden_actions": ";".join(
            [
                "no_training_from_replay_labels",
                "no_threshold_selection_from_single_month",
                "no_model_activation",
                "no_broker_or_account_authority",
            ]
        ),
        "diagnostic_only": True,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _operation_mechanism_contract_packet(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "contract_type": "model_group_operation_mechanism_contract_packet",
        "summary": {
            "mechanism_contract_count": len(rows),
            "breach_status_counts": dict(Counter(str(row.get("breach_status") or "") for row in rows)),
            "severity_counts": dict(Counter(str(row.get("severity") or "") for row in rows)),
            "component_counts": dict(Counter(str(row.get("operation_component_id") or "") for row in rows)),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
            "retraining_performed": False,
        },
        "contract_rows_ref": "operation_mechanism_contract_packet.csv",
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
        "interpretation_notes": [
            "Rows are standing mechanism contracts and current breach states, not one-off patches or approved model changes.",
            "Systemic closure gates require multi-month confirmation before policy or model changes.",
        ],
    }


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _regret_to_best_available(row: Mapping[str, Any]) -> float | None:
    if row.get("regret_to_best_available") not in {None, ""}:
        return _float(row.get("regret_to_best_available"))
    if row.get("best_available_action_return") not in {None, ""} and row.get("chosen_action_return") not in {None, ""}:
        return max(0.0, _float(row.get("best_available_action_return")) - _float(row.get("chosen_action_return")))
    if row.get("baseline_return") not in {None, ""} and row.get("realized_return") not in {None, ""}:
        return max(0.0, _float(row.get("baseline_return")) - _float(row.get("realized_return")))
    return None


def _string_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in {None, ""}]
    text = str(value)
    if not text:
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def _operation_trigger_state(component_id: str, row: Mapping[str, Any], lifecycle_summary: Mapping[str, Any]) -> str:
    if component_id in {"C01_intake_operation", "C07_failure_review_operation"}:
        return "clock_triggered"
    if component_id == "C02_entry_operation":
        if any(row.get(field) not in {None, ""} for field in ("candidate_set_scope", "decision_status", "decision_action", "action")):
            return "candidate_triggered"
        return "missing_candidate_scope"
    if component_id == "C03_lifecycle_operation":
        if lifecycle_summary:
            return "position_or_intent_state_triggered"
        return "missing_lifecycle_state_evidence"
    if component_id == "C04_expression_review_operation":
        if row.get("decision_expression_type") not in {None, ""} or row.get("selected_expression_type") not in {None, ""}:
            return "intent_triggered"
        return "not_triggered_no_expression_intent"
    if component_id == "C05_order_intent_operation":
        if row.get("instrument_ref") not in {None, ""} or row.get("decision_intended_action") not in {None, ""}:
            return "materialized_intent_triggered"
        return "not_triggered_no_materialized_instrument"
    if component_id == "C06_execution_gate_operation":
        if row.get("instrument_ref") not in {None, ""} or row.get("fill_status") not in {None, ""}:
            return "order_plan_or_fill_state_triggered"
        return "not_triggered_no_order_plan"
    return "not_reported"


def _operation_layer_label_row(
    *,
    component_id: str,
    decision_id: str,
    layer_review_by_decision_layer: Mapping[tuple[str, str], Mapping[str, Any]],
) -> Mapping[str, Any]:
    layer_id = OPERATION_COMPONENT_LAYER_LABEL_SOURCE.get(component_id)
    if not layer_id:
        return {}
    return layer_review_by_decision_layer.get((decision_id, layer_id), {})


def _operation_available_actions(row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> list[str]:
    actions = _string_list(layer_label_row.get("available_action"))
    if actions:
        return actions
    return _string_list(row.get("available_action"))


def _operation_feasible_action_set_ref(component_id: str, row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> str:
    if layer_label_row:
        return str(layer_label_row.get("candidate_set_scope") or OPERATION_COMPONENT_LAYER_LABEL_SOURCE.get(component_id) or "")
    if component_id == "C01_intake_operation":
        return str(row.get("candidate_set_scope") or "point_in_time_candidate_universe")
    if component_id == "C02_entry_operation":
        return "decision_time_entry_actions"
    if component_id == "C03_lifecycle_operation":
        return "decision_time_portfolio_lifecycle_transitions"
    if component_id == "C04_expression_review_operation":
        return str(row.get("asset_expression_route") or row.get("candidate_set_scope") or "decision_time_expression_candidates")
    if component_id == "C05_order_intent_operation":
        return "decision_time_capital_and_sizing_actions"
    if component_id == "C06_execution_gate_operation":
        return "decision_time_broker_safe_order_and_fill_states"
    return "settled_component_incident_labels"


def _operation_feasible_action_count(component_id: str, row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> int | None:
    action_count = len(_operation_available_actions(row, layer_label_row))
    if action_count:
        return action_count
    for field in (
        "eligible_candidate_count",
        "candidate_count_after_filter",
        "candidate_count_before_filter",
    ):
        if row.get(field) not in {None, ""}:
            return int(_float(row.get(field)))
    if component_id in {"C02_entry_operation", "C05_order_intent_operation", "C06_execution_gate_operation"}:
        return None
    return None


def _operation_feasible_action_set_status(row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> str:
    if _operation_available_actions(row, layer_label_row):
        return "published"
    if any(row.get(field) not in {None, ""} for field in ("eligible_candidate_count", "candidate_count_after_filter")):
        return "count_only"
    return "not_published"


def _operation_chosen_action(component_id: str, row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> str:
    if layer_label_row.get("chosen_action") not in {None, ""}:
        return str(layer_label_row.get("chosen_action"))
    if component_id == "C01_intake_operation":
        return "publish_inputs"
    if component_id == "C02_entry_operation":
        return str(row.get("chosen_action") or row.get("decision_action") or row.get("action") or "")
    if component_id == "C03_lifecycle_operation":
        return str(row.get("lifecycle_action") or "apply_lifecycle_state")
    if component_id == "C04_expression_review_operation":
        return str(row.get("instrument_ref") or row.get("decision_expression_type") or row.get("selected_expression_type") or "")
    if component_id == "C05_order_intent_operation":
        return str(row.get("decision_intended_action") or row.get("action") or "create_sized_order_intent")
    if component_id == "C06_execution_gate_operation":
        return str(row.get("fill_status") or "simulate_execution")
    return "review_settled_failure"


def _operation_best_available_action(component_id: str, row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> str:
    if layer_label_row.get("best_available_action_by_future_outcome") not in {None, ""}:
        return str(layer_label_row.get("best_available_action_by_future_outcome"))
    explicit = str(row.get("best_available_action_by_future_outcome") or "")
    if explicit:
        return explicit
    if component_id in {"C01_intake_operation", "C03_lifecycle_operation", "C05_order_intent_operation"}:
        return "not_determinable_from_current_review"
    return "not_published"


def _operation_chosen_rank_ex_post(row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> int | None:
    if layer_label_row.get("chosen_rank_ex_post") not in {None, ""}:
        return int(_float(layer_label_row.get("chosen_rank_ex_post")))
    if row.get("chosen_rank_ex_post") not in {None, ""}:
        return int(_float(row.get("chosen_rank_ex_post")))
    chosen = str(layer_label_row.get("chosen_action") or row.get("chosen_action") or "")
    best = str(layer_label_row.get("best_available_action_by_future_outcome") or row.get("best_available_action_by_future_outcome") or "")
    if chosen and best and chosen == best:
        return 1
    if best:
        return None
    return None


def _operation_component_correctness_class(component_id: str, row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> str:
    if layer_label_row.get("correctness_class") not in {None, ""}:
        return str(layer_label_row.get("correctness_class"))
    best = _operation_best_available_action(component_id, row, layer_label_row)
    if best in {"not_published", "not_determinable_from_current_review"}:
        return "not_scored"
    chosen = _operation_chosen_action(component_id, row, layer_label_row)
    regret = _regret_to_best_available(row)
    if chosen and chosen == best:
        return "best_available"
    if regret is not None and regret <= 0:
        return "acceptable_no_regret"
    if regret is not None:
        return "regretful_choice"
    return "not_scored"


def _operation_action_return(row: Mapping[str, Any], layer_label_row: Mapping[str, Any], field: str) -> float | None:
    if layer_label_row.get(field) not in {None, ""}:
        return _round(_float(layer_label_row.get(field)))
    if row.get(field) not in {None, ""}:
        return _round(_float(row.get(field)))
    return None


def _operation_regret_to_best_available(row: Mapping[str, Any], layer_label_row: Mapping[str, Any]) -> float | None:
    if layer_label_row.get("regret_to_best_available") not in {None, ""}:
        return _round(_float(layer_label_row.get("regret_to_best_available")))
    return _round(_regret_to_best_available(row))


def _operation_post_replay_label_basis(component_id: str, row: Mapping[str, Any]) -> str:
    if component_id == "C01_intake_operation":
        return "future labels audit opportunity coverage only; not used to construct candidate inputs"
    if component_id == "C02_entry_operation":
        return "future outcome ranks available entry actions after point-in-time gating"
    if component_id == "C03_lifecycle_operation":
        return "lifecycle correctness requires position-state transition labels; current row labels are diagnostic only"
    if component_id == "C04_expression_review_operation":
        return "future option/underlying outcome ranks only decision-time feasible expressions"
    if component_id == "C05_order_intent_operation":
        return "future outcomes audit sizing opportunity cost under account constraints"
    if component_id == "C06_execution_gate_operation":
        return "future settlement audits fill and execution quality after order plan emission"
    return "settled outcomes classify incidents after replay decisions are fixed"


def _operation_review_boundary_status(
    *,
    feasible_action_set_status: str,
    first_limiting_component: str,
    component_id: str,
    first_limiting_reason: str,
) -> str:
    if first_limiting_component == component_id and first_limiting_reason:
        return "boundary_or_handoff_failure_reported"
    if feasible_action_set_status == "published":
        return "received_boundary_complete"
    if feasible_action_set_status == "count_only":
        return "received_boundary_partial_count_only"
    return "received_boundary_missing"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _m04_diagnostics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return ((row.get("model_layer_diagnostics") or {}).get("model_04_unified_decision") or {})


def _m05_diagnostics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    diagnostics = row.get("model_layer_diagnostics") or {}
    return (
        diagnostics.get("model_05_alpha_confidence")
        or diagnostics.get("model_05_option_expression")
        or {}
    )


def _m05_option_expression_diagnostics(row: Mapping[str, Any]) -> Mapping[str, Any]:
    return ((row.get("model_layer_diagnostics") or {}).get("model_05_option_expression") or {})


def _m04_state(row: Mapping[str, Any]) -> str:
    diag = _m04_diagnostics(row)
    action = str(diag.get("resolved_underlying_action_type") or "unknown")
    side = str(diag.get("resolved_action_side") or "unknown")
    return f"{action}/{side}"


def _m05_state(row: Mapping[str, Any]) -> str:
    status = str(_m05_diagnostics(row).get("alpha_gate_status") or "unknown")
    return f"alpha_{status}"


def _expression_state(row: Mapping[str, Any]) -> str:
    if row.get("fill_status") == "simulated_filled":
        return "filled_contract"
    route = str(row.get("asset_expression_route") or "")
    if route == "option_expression_unfilled":
        return "expression_unfilled"
    return "no_expression"


def _score_bin(row: Mapping[str, Any]) -> str:
    score = _float(row.get("prediction_score"))
    if score >= 0.9:
        return ">=0.9"
    if score >= 0.8:
        return "0.8-0.9"
    if score >= 0.7:
        return "0.7-0.8"
    if score >= 0.6:
        return "0.6-0.7"
    return "<0.6"


def _summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    row_count = len(rows)
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    label_sum = sum(_float(row.get("outcome_label")) for row in rows)
    score_sum = sum(_float(row.get("prediction_score")) for row in rows)
    net_return = sum(_float(row.get("realized_return")) for row in rows)
    filled_good = sum(1 for row in filled if str(row.get("outcome_label")) == "1")
    filled_bad = sum(1 for row in filled if str(row.get("outcome_label")) == "0")
    return {
        "row_count": row_count,
        "filled_count": len(filled),
        "filled_good_count": filled_good,
        "filled_bad_count": filled_bad,
        "label_rate": _round(label_sum / row_count) if row_count else None,
        "mean_prediction_score": _round(score_sum / row_count) if row_count else None,
        "net_return_total": _round(net_return),
        "return_per_row": _round(net_return / row_count) if row_count else None,
        "filled_hit_rate": _round(filled_good / len(filled)) if filled else None,
    }


def _round(value: float | None) -> float | None:
    return None if value is None else round(float(value), 6)


def _cohort_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(_m04_state(row), _m05_state(row), _expression_state(row))].append(row)
    output = []
    for (m04_state, m05_state, expression_state), group_rows in sorted(groups.items()):
        item = {
            "m04_state": m04_state,
            "m05_state": m05_state,
            "expression_state": expression_state,
            **_summary(group_rows),
        }
        output.append(item)
    return output


def _filled_score_bin_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("fill_status") == "simulated_filled":
            groups[_score_bin(row)].append(row)
    order = {"<0.6": 0, "0.6-0.7": 1, "0.7-0.8": 2, "0.8-0.9": 3, ">=0.9": 4}
    return [
        {"score_bin": score_bin, **_summary(groups[score_bin])}
        for score_bin in sorted(groups, key=lambda value: order.get(value, 99))
    ]


def _drawdown_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    cumulative = 0.0
    peak = 0.0
    worst_drawdown = 0.0
    worst_row: Mapping[str, Any] | None = None
    for row in sorted(rows, key=lambda item: str(item.get("timestamp") or "")):
        cumulative += _float(row.get("realized_return"))
        peak = max(peak, cumulative)
        drawdown = cumulative - peak
        if drawdown < worst_drawdown:
            worst_drawdown = drawdown
            worst_row = row
    return {
        "final_cumulative_return": _round(cumulative),
        "max_drawdown": _round(worst_drawdown),
        "max_drawdown_timestamp": str(worst_row.get("timestamp") or "") if worst_row else "",
        "max_drawdown_decision_id": str(worst_row.get("decision_id") or "") if worst_row else "",
        "max_drawdown_contract_ref": str(worst_row.get("selected_option_contract_ref") or "") if worst_row else "",
    }


def _tail_loss_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    return [_row_extract(row) for row in sorted(filled, key=lambda item: _float(item.get("realized_return")))[:limit]]


def _top_gain_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    return [_row_extract(row) for row in sorted(filled, key=lambda item: _float(item.get("realized_return")), reverse=True)[:limit]]


def _row_extract(row: Mapping[str, Any]) -> dict[str, Any]:
    m04 = _m04_diagnostics(row)
    m05 = _m05_diagnostics(row)
    scores = m04.get("dominant_horizon_scores") or {}
    return {
        "timestamp": str(row.get("timestamp") or ""),
        "decision_id": str(row.get("decision_id") or ""),
        "decision_status": str(row.get("decision_status") or ""),
        "fill_status": str(row.get("fill_status") or ""),
        "outcome_label": _text(row.get("outcome_label")),
        "prediction_score": _round(_float(row.get("prediction_score"))),
        "realized_return": _round(_float(row.get("realized_return"))),
        "m04_state": _m04_state(row),
        "m04_reason_codes": ";".join(str(value) for value in (m04.get("reason_codes") or [])),
        "m05_state": _m05_state(row),
        "m05_resolved_alpha_score": _round(_float(m05.get("resolved_alpha_score"))),
        "trade_intensity_score": _round(_float(scores.get("trade_intensity_score"))),
        "selected_option_contract_ref": str(row.get("selected_option_contract_ref") or ""),
        "option_entry_price": _round(_float(row.get("option_entry_price"))),
        "option_exit_price": _round(_float(row.get("option_exit_price"))),
    }


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _row_scope(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "decision_row_count": len(rows),
        "filled_count": sum(1 for row in rows if row.get("fill_status") == "simulated_filled"),
        "simulated_rejected_count": sum(1 for row in rows if row.get("fill_status") == "simulated_rejected"),
        "decision_status_counts": dict(Counter(str(row.get("decision_status") or "") for row in rows)),
        "expression_state_counts": dict(Counter(_expression_state(row) for row in rows)),
    }


def _layer_status(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    m04_counts = Counter(_m04_state(row) for row in rows)
    m05_counts = Counter(_m05_state(row) for row in rows)
    m04_open_m05_pass = [
        row for row in rows if _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
    ]
    m05_pass_m04_blocked = [
        row for row in rows if _m05_state(row) == "alpha_passed" and _m04_state(row) != "open_long/long"
    ]
    return {
        "m04_state_counts": dict(m04_counts),
        "m05_state_counts": dict(m05_counts),
        "m04_open_m05_pass_count": len(m04_open_m05_pass),
        "m04_open_m05_pass_filled_count": sum(
            1 for row in m04_open_m05_pass if _expression_state(row) == "filled_contract"
        ),
        "m04_open_m05_pass_expression_unfilled_count": sum(
            1 for row in m04_open_m05_pass if _expression_state(row) == "expression_unfilled"
        ),
        "m05_pass_but_m04_not_open_count": len(m05_pass_m04_blocked),
        "m05_pass_but_m04_not_open_label_rate": _round(
            sum(_float(row.get("outcome_label")) for row in m05_pass_m04_blocked) / len(m05_pass_m04_blocked)
        )
        if m05_pass_m04_blocked
        else None,
    }


def _decision_surface_component_matrix_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        first_surface, first_surface_reason = _first_limiting_surface(row)
        m04 = _m04_diagnostics(row)
        scores = _m04_component_scores(row)
        output.append(
            {
                "decision_id": str(row.get("decision_id") or ""),
                "timestamp": str(row.get("timestamp") or ""),
                "target_ref": str(row.get("target_ref") or ""),
                "decision_status": str(row.get("decision_status") or ""),
                "decision_action": str(row.get("decision_action") or row.get("action") or ""),
                "fill_status": str(row.get("fill_status") or ""),
                "first_limiting_surface": first_surface,
                "first_limiting_surface_reason": first_surface_reason,
                "settled_metric_eligible": row.get("fill_status") == "simulated_filled",
                "model_01_background_context_ref_status": _model_ref_status(row, "model_01_background_context"),
                "model_02_target_state_ref_status": _model_ref_status(row, "model_02_target_state"),
                "model_03_event_state_ref_status": _model_ref_status(row, "model_03_event_state"),
                "model_04_unified_decision_ref_status": _model_ref_status(row, "model_04_unified_decision"),
                "model_05_option_expression_ref_status": _model_ref_status(row, "model_05_option_expression"),
                "model_04_score_coverage_count": len(scores),
                "model_04_resolved_action": _m04_state(row),
                "model_04_reason_codes": ";".join(str(value) for value in (m04.get("reason_codes") or [])),
                "option_expression_surface_state": _option_expression_surface_state(row),
                "selected_option_contract_ref": str(row.get("selected_option_contract_ref") or ""),
                "selected_option_expression_type": str(
                    row.get("selected_option_expression_type") or row.get("decision_expression_type") or ""
                ),
                "selected_option_path_status": _selected_option_path_status(row),
                "prediction_score": _round(_float(row.get("prediction_score"))),
                "outcome_label": _text(row.get("outcome_label")),
                "realized_return": _round(_float(row.get("realized_return"))),
                "fixed_input_only": True,
            }
        )
    return output


def _first_limiting_surface(row: Mapping[str, Any]) -> tuple[str, str]:
    if not _m04_diagnostics(row):
        return "C04_underlying_decision_surface", "model_04_diagnostics_missing"
    if _m04_state(row) != "open_long/long":
        return "C04_underlying_decision_surface", "m04_resolved_non_open_long"
    if not str(row.get("selected_option_contract_ref") or "").strip():
        if str(row.get("asset_expression_route") or "") == "option_expression_unfilled":
            return "C05_option_expression_surface", "no_selected_option_contract"
        return "C05_option_expression_surface", "option_expression_not_selected"
    path_status = _selected_option_path_status(row)
    if path_status == "missing":
        return "C06_selected_option_path_materialization", "selected_option_contract_path_missing"
    if row.get("fill_status") != "simulated_filled":
        return "C07_portfolio_execution_surface", "selected_contract_not_filled"
    return "C08_settled_prediction_quality_surface", "filled_and_settled"


def _model_ref_status(row: Mapping[str, Any], model_layer: str) -> str:
    refs = row.get("model_layer_refs") or {}
    in_refs = bool(refs.get(model_layer)) if isinstance(refs, Mapping) else False
    in_chain = model_layer in (row.get("model_evidence_chain") or [])
    if in_refs and in_chain:
        return "explicit_ref_and_evidence_chain"
    if in_refs:
        return "explicit_ref_only"
    if in_chain:
        return "evidence_chain_only"
    return "missing"


def _option_expression_surface_state(row: Mapping[str, Any]) -> str:
    status = _m05_state(row)
    selected_contract = bool(str(row.get("selected_option_contract_ref") or "").strip())
    route = str(row.get("asset_expression_route") or "")
    if selected_contract:
        return f"{status}/selected_contract"
    if route == "option_expression_unfilled":
        return f"{status}/expression_unfilled"
    return f"{status}/no_selected_expression"


def _selected_option_path_status(row: Mapping[str, Any]) -> str:
    status = str(row.get("option_contract_path_status") or "").strip()
    if status:
        return status
    if row.get("fill_status") == "simulated_filled":
        return "available"
    if str(row.get("selected_option_contract_ref") or "").strip():
        return "unknown"
    return "not_applicable"


def _component_model_mapping_rows(
    rows: Sequence[Mapping[str, Any]],
    decision_surface_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    component_specs = [
        ("C01_background_context_surface", "model_01_background_context"),
        ("C02_target_state_surface", "model_02_target_state"),
        ("C03_event_state_surface", "model_03_event_state"),
        ("C04_underlying_decision_surface", "model_04_unified_decision"),
        ("C05_option_expression_surface", "model_05_option_expression"),
    ]
    output: list[dict[str, Any]] = []
    for component_surface, model_layer in component_specs:
        explicit_ref_count = _explicit_ref_count(rows, model_layer)
        evidence_chain_count = sum(1 for row in rows if model_layer in (row.get("model_evidence_chain") or []))
        diagnostic_surface_count = _diagnostic_surface_count(rows, model_layer)
        decision_surface_count = _decision_surface_count(rows, model_layer)
        first_limiting_count = sum(
            1 for row in decision_surface_rows if row.get("first_limiting_surface") == component_surface
        )
        settled_count = sum(
            1
            for row in decision_surface_rows
            if _row_maps_to_model_layer(row, model_layer) and row.get("settled_metric_eligible") is True
        )
        output.append(
            {
                "component_surface": component_surface,
                "model_layer": model_layer,
                "explicit_ref_count": explicit_ref_count,
                "evidence_chain_count": evidence_chain_count,
                "diagnostic_surface_count": diagnostic_surface_count,
                "decision_surface_count": decision_surface_count,
                "first_limiting_surface_count": first_limiting_count,
                "settled_metric_eligible_count": settled_count,
                "mapping_status": _component_mapping_status(
                    explicit_ref_count=explicit_ref_count,
                    evidence_chain_count=evidence_chain_count,
                    diagnostic_surface_count=diagnostic_surface_count,
                    decision_surface_count=decision_surface_count,
                ),
                "fixed_input_only": True,
            }
        )
    output.extend(
        [
            {
                "component_surface": "C06_selected_option_path_materialization",
                "model_layer": "",
                "explicit_ref_count": 0,
                "evidence_chain_count": 0,
                "diagnostic_surface_count": 0,
                "decision_surface_count": sum(
                    1
                    for row in decision_surface_rows
                    if row.get("selected_option_path_status") not in {"", "not_applicable"}
                ),
                "first_limiting_surface_count": sum(
                    1
                    for row in decision_surface_rows
                    if row.get("first_limiting_surface") == "C06_selected_option_path_materialization"
                ),
                "settled_metric_eligible_count": _settled_metric_eligible_count(decision_surface_rows),
                "mapping_status": "non_model_surface",
                "fixed_input_only": True,
            },
            {
                "component_surface": "C07_portfolio_execution_surface",
                "model_layer": "",
                "explicit_ref_count": 0,
                "evidence_chain_count": 0,
                "diagnostic_surface_count": 0,
                "decision_surface_count": len(decision_surface_rows),
                "first_limiting_surface_count": sum(
                    1
                    for row in decision_surface_rows
                    if row.get("first_limiting_surface") == "C07_portfolio_execution_surface"
                ),
                "settled_metric_eligible_count": sum(
                    1 for row in decision_surface_rows if row.get("settled_metric_eligible") is True
                ),
                "mapping_status": "non_model_surface",
                "fixed_input_only": True,
            },
            {
                "component_surface": "C08_settled_prediction_quality_surface",
                "model_layer": "",
                "explicit_ref_count": 0,
                "evidence_chain_count": 0,
                "diagnostic_surface_count": 0,
                "decision_surface_count": _settled_metric_eligible_count(decision_surface_rows),
                "first_limiting_surface_count": sum(
                    1
                    for row in decision_surface_rows
                    if row.get("first_limiting_surface") == "C08_settled_prediction_quality_surface"
                ),
                "settled_metric_eligible_count": _settled_metric_eligible_count(decision_surface_rows),
                "mapping_status": "non_model_surface",
                "fixed_input_only": True,
            },
        ]
    )
    return output


def _explicit_ref_count(rows: Sequence[Mapping[str, Any]], model_layer: str) -> int:
    count = 0
    for row in rows:
        refs = row.get("model_layer_refs") or {}
        if isinstance(refs, Mapping) and refs.get(model_layer):
            count += 1
    return count


def _diagnostic_surface_count(rows: Sequence[Mapping[str, Any]], model_layer: str) -> int:
    if model_layer in {
        "model_01_background_context",
        "model_02_target_state",
        "model_03_event_state",
    }:
        return sum(
            1
            for row in rows
            if bool((row.get("model_layer_diagnostics") or {}).get(model_layer))
        )
    if model_layer == "model_04_unified_decision":
        return sum(1 for row in rows if bool(_m04_diagnostics(row)))
    if model_layer == "model_05_option_expression":
        return sum(1 for row in rows if bool(_m05_diagnostics(row)))
    return 0


def _decision_surface_count(rows: Sequence[Mapping[str, Any]], model_layer: str) -> int:
    if model_layer == "model_04_unified_decision":
        return sum(1 for row in rows if bool(_m04_diagnostics(row)))
    if model_layer == "model_05_option_expression":
        return sum(
            1
            for row in rows
            if str(row.get("selected_option_contract_ref") or "").strip()
            or str(row.get("asset_expression_route") or "") == "option_expression_unfilled"
        )
    return _explicit_ref_count(rows, model_layer)


def _row_maps_to_model_layer(row: Mapping[str, Any], model_layer: str) -> bool:
    status = str(row.get(f"{model_layer}_ref_status") or "")
    if status != "missing":
        return True
    if model_layer == "model_04_unified_decision":
        return int(row.get("model_04_score_coverage_count") or 0) > 0
    if model_layer == "model_05_option_expression":
        return str(row.get("option_expression_surface_state") or "") != "alpha_unknown/no_selected_expression"
    return False


def _settled_metric_eligible_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("settled_metric_eligible") is True)


def _component_mapping_status(
    *,
    explicit_ref_count: int,
    evidence_chain_count: int,
    diagnostic_surface_count: int,
    decision_surface_count: int,
) -> str:
    if explicit_ref_count and diagnostic_surface_count:
        return "explicit_ref_and_diagnostic_surface"
    if explicit_ref_count:
        return "explicit_ref_only"
    if diagnostic_surface_count or decision_surface_count:
        return "diagnostic_or_decision_surface_without_explicit_ref"
    if evidence_chain_count:
        return "evidence_chain_only"
    return "missing"


def _decision_surface_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    first_surface_counts = Counter(str(row.get("first_limiting_surface") or "") for row in rows)
    settled_count = sum(1 for row in rows if row.get("settled_metric_eligible") is True)
    return {
        "contract_type": "model_group_decision_surface_component_summary",
        "row_count": len(rows),
        "first_limiting_surface_counts": dict(first_surface_counts),
        "settled_metric_eligible_count": settled_count,
        "settled_metric_excluded_count": len(rows) - settled_count,
        "fixed_input_only": True,
    }


def _component_model_mapping_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "contract_type": "model_group_component_model_mapping_summary",
        "component_surface_count": len(rows),
        "mapping_status_counts": dict(Counter(str(row.get("mapping_status") or "") for row in rows)),
        "first_limiting_surface_counts": {
            str(row.get("component_surface") or ""): int(row.get("first_limiting_surface_count") or 0)
            for row in rows
            if int(row.get("first_limiting_surface_count") or 0) > 0
        },
        "fixed_input_only": True,
    }


def _component_survival_quality_flow_rows(
    decision_surface_rows: Sequence[Mapping[str, Any]],
    component_model_mapping_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    order_index = {surface: index for index, surface in enumerate(COMPONENT_SURFACE_ORDER)}
    mapping_by_surface = {
        str(row.get("component_surface") or ""): row
        for row in component_model_mapping_rows
    }
    previous_bad_rate: float | None = None
    output: list[dict[str, Any]] = []
    for index, component_surface in enumerate(COMPONENT_SURFACE_ORDER, start=1):
        entered_rows = [
            row
            for row in decision_surface_rows
            if order_index.get(str(row.get("first_limiting_surface") or ""), len(COMPONENT_SURFACE_ORDER) - 1)
            >= index - 1
        ]
        first_limiting_rows = [
            row
            for row in entered_rows
            if str(row.get("first_limiting_surface") or "") == component_surface
        ]
        blocked_count = 0 if component_surface == "C08_settled_prediction_quality_surface" else len(first_limiting_rows)
        censored_count = (
            len(first_limiting_rows)
            if component_surface == "C06_selected_option_path_materialization"
            else 0
        )
        passed_rows = entered_rows if component_surface == "C08_settled_prediction_quality_surface" else [
            row
            for row in entered_rows
            if str(row.get("first_limiting_surface") or "") != component_surface
        ]
        entered_settled_rows = _settled_rows(entered_rows)
        passed_settled_rows = _settled_rows(passed_rows)
        prior_bad_count = _bad_outcome_count(entered_settled_rows)
        post_bad_count = _bad_outcome_count(passed_settled_rows)
        bad_rate = (post_bad_count / len(passed_settled_rows)) if passed_settled_rows else None
        mean_realized_return = _mean(_numeric_values(passed_settled_rows, "realized_return"))
        tail_loss_count = sum(1 for row in passed_settled_rows if _float(row.get("realized_return")) <= -0.2)
        verdict, basis = _component_flow_verdict(
            component_surface=component_surface,
            entered_count=len(entered_rows),
            blocked_count=blocked_count,
            censored_count=censored_count,
            settled_count=len(passed_settled_rows),
            post_bad_rate=bad_rate,
            mean_realized_return=mean_realized_return,
            tail_loss_count=tail_loss_count,
            previous_bad_rate=previous_bad_rate,
        )
        if bad_rate is not None:
            previous_bad_rate = bad_rate
        output.append(
            {
                "component_index": index,
                "component_surface": component_surface,
                "model_layer": str((mapping_by_surface.get(component_surface) or {}).get("model_layer") or ""),
                "entered_count": len(entered_rows),
                "first_limiting_count": len(first_limiting_rows),
                "blocked_count": blocked_count,
                "censored_count": censored_count,
                "passed_count": len(passed_rows),
                "settled_metric_eligible_count": len(passed_settled_rows),
                "settled_metric_excluded_count": len(passed_rows) - len(passed_settled_rows),
                "outcome_metric_available": bool(passed_settled_rows),
                "mean_prediction_score": _round(_mean(_numeric_values(passed_settled_rows, "prediction_score"))),
                "score_label_spearman": _round(
                    _spearman_for_key(passed_settled_rows, "prediction_score", "outcome_label")
                ),
                "score_return_spearman": _round(
                    _spearman_for_key(passed_settled_rows, "prediction_score", "realized_return")
                ),
                "mean_realized_return": _round(mean_realized_return),
                "hit_rate": _round(
                    sum(1 for row in passed_settled_rows if str(row.get("outcome_label")) == "1")
                    / len(passed_settled_rows)
                )
                if passed_settled_rows
                else None,
                "tail_loss_count": tail_loss_count,
                "prior_bad_cohort_count": prior_bad_count,
                "post_component_bad_cohort_count": post_bad_count,
                "stage_verdict": verdict,
                "verdict_basis": basis,
                "threshold_selection_performed": False,
                "retraining_performed": False,
                "fixed_input_only": True,
            }
        )
    return output


def _component_survival_quality_flow_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    first_problem_row = next(
        (
            row
            for row in rows
            if str(row.get("stage_verdict") or "") not in {"neutral_measured", "unmeasured", "insufficient_evidence"}
        ),
        None,
    )
    return {
        "contract_type": "model_group_component_survival_quality_flow_report",
        "summary": {
            "component_count": len(rows),
            "first_problem_surface": str((first_problem_row or {}).get("component_surface") or ""),
            "first_problem_verdict": str((first_problem_row or {}).get("stage_verdict") or ""),
            "verdict_counts": dict(Counter(str(row.get("stage_verdict") or "") for row in rows)),
            "dominant_censoring_surfaces": [
                str(row.get("component_surface") or "")
                for row in rows
                if str(row.get("stage_verdict") or "") == "dominant_censoring_point"
            ],
            "settled_quality_surface_status": str(
                next(
                    (
                        row.get("stage_verdict")
                        for row in rows
                        if row.get("component_surface") == "C08_settled_prediction_quality_surface"
                    ),
                    "",
                )
            ),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
            "retraining_performed": False,
        },
        "component_survival_quality_flow_ref": "component_survival_quality_flow.csv",
        "forbidden_uses": [
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_action",
        ],
        "interpretation_notes": [
            "Component flow verdicts localize where degradation is first observed, not causal model blame.",
            "Neutral measured and unmeasured states are separated so missing instrumentation is not read as success.",
            "Path-materialization censored rows are excluded from settled model win/loss metrics.",
            "Outcome fields are labels for settled quality only and must not be treated as point-in-time inputs.",
        ],
    }


def _component_review_packet(
    *,
    component_survival_quality_flow_rows: Sequence[Mapping[str, Any]],
    component_model_mapping_rows: Sequence[Mapping[str, Any]],
    m05_unfilled_summary: Mapping[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    mapping_by_surface = {
        str(row.get("component_surface") or ""): row
        for row in component_model_mapping_rows
    }
    component_rows: list[dict[str, Any]] = []
    for flow_row in component_survival_quality_flow_rows:
        component_surface = str(flow_row.get("component_surface") or "")
        mapping_row = mapping_by_surface.get(component_surface) or {}
        internal_refs = _component_internal_review_refs(
            component_surface=component_surface,
            m05_unfilled_available=m05_unfilled_summary.get("source_status") == "available",
        )
        missing_outputs = _component_missing_review_outputs(
            component_surface=component_surface,
            mapping_row=mapping_row,
            m05_unfilled_available=m05_unfilled_summary.get("source_status") == "available",
        )
        attribution_status = _attribution_coverage_status(mapping_row)
        interpretation_status = _component_interpretation_status(
            survival_verdict=str(flow_row.get("stage_verdict") or ""),
            attribution_coverage_status=attribution_status,
            missing_review_outputs=missing_outputs,
        )
        input_count = int(flow_row.get("entered_count") or 0)
        output_count = int(flow_row.get("passed_count") or 0)
        blocked_count = int(flow_row.get("blocked_count") or 0)
        component_rows.append(
            {
                "component_index": int(flow_row.get("component_index") or 0),
                "component_surface": component_surface,
                "model_layer": str(mapping_row.get("model_layer") or ""),
                "component_role": COMPONENT_ROLE_BY_SURFACE.get(component_surface, ""),
                "input_count": input_count,
                "output_count": output_count,
                "dropped_or_blocked_count": blocked_count,
                "changed_or_transformed_count": _component_changed_or_transformed_count(component_surface, input_count),
                "settled_metric_eligible_count": int(flow_row.get("settled_metric_eligible_count") or 0),
                "survival_verdict": str(flow_row.get("stage_verdict") or ""),
                "survival_verdict_basis": str(flow_row.get("verdict_basis") or ""),
                "attribution_coverage_status": attribution_status,
                "point_in_time_evidence_status": _point_in_time_evidence_status(mapping_row, internal_refs),
                "outcome_label_role": "retrospective_label_only",
                "internal_review_refs": ";".join(internal_refs),
                "missing_review_outputs": ";".join(missing_outputs),
                "explicit_ref_count": int(mapping_row.get("explicit_ref_count") or 0),
                "evidence_chain_count": int(mapping_row.get("evidence_chain_count") or 0),
                "diagnostic_surface_count": int(mapping_row.get("diagnostic_surface_count") or 0),
                "decision_surface_count": int(mapping_row.get("decision_surface_count") or 0),
                "first_limiting_surface_count": int(mapping_row.get("first_limiting_surface_count") or 0),
                "can_assign_model_blame": _can_assign_model_blame(
                    survival_verdict=str(flow_row.get("stage_verdict") or ""),
                    attribution_coverage_status=attribution_status,
                    missing_review_outputs=missing_outputs,
                ),
                "interpretation_status": interpretation_status,
                "threshold_selection_performed": False,
                "retraining_performed": False,
                "fixed_input_only": True,
            }
        )
    packet = {
        "contract_type": "model_group_component_review_packet",
        "component_review_packet_csv_ref": str(output_dir / "component_review_packet.csv"),
        "component_count": len(component_rows),
        "summary": {
            "component_count": len(component_rows),
            "survival_verdict_counts": dict(Counter(str(row["survival_verdict"]) for row in component_rows)),
            "attribution_coverage_status_counts": dict(
                Counter(str(row["attribution_coverage_status"]) for row in component_rows)
            ),
            "interpretation_status_counts": dict(Counter(str(row["interpretation_status"]) for row in component_rows)),
            "components_with_missing_review_outputs": [
                str(row["component_surface"])
                for row in component_rows
                if str(row.get("missing_review_outputs") or "")
            ],
            "model_blame_assignable_components": [
                str(row["component_surface"])
                for row in component_rows
                if row.get("can_assign_model_blame") is True
            ],
            "model_attribution_ready_components": [
                str(row["component_surface"])
                for row in component_rows
                if _model_attribution_ready(
                    str(row.get("attribution_coverage_status") or ""),
                    str(row.get("missing_review_outputs") or "").split(";")
                    if str(row.get("missing_review_outputs") or "")
                    else [],
                )
            ],
            "review_readiness_status": _component_review_readiness_status(component_rows),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
            "retraining_performed": False,
        },
        "component_rows": component_rows,
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
        "interpretation_notes": [
            "Every component row separates point-in-time evidence from retrospective outcome labels.",
            "Outcome labels are evaluation labels and must not be used as decision-time explanatory inputs.",
            "Model blame is assignable only when explicit asset refs and required internal review outputs are present.",
            "Unmeasured or insufficient-attribution components must remain diagnostic gaps, not neutral evidence.",
        ],
    }
    return {"component_rows": component_rows, "packet": packet}


def _operation_review_projection_matrix_rows(
    decision_surface_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in decision_surface_rows:
        source_surface = str(row.get("first_limiting_surface") or "")
        projection = OPERATION_REVIEW_PROJECTION_BY_SURFACE.get(source_surface) or {}
        component_id = str(projection.get("operation_component_id") or "")
        component_spec = OPERATION_COMPONENT_BY_ID.get(component_id) or {}
        output.append(
            {
                "decision_id": str(row.get("decision_id") or ""),
                "timestamp": str(row.get("timestamp") or ""),
                "target_ref": str(row.get("target_ref") or ""),
                "source_decision_surface": source_surface,
                "source_surface_reason": str(row.get("first_limiting_surface_reason") or ""),
                "operation_component_id": component_id,
                "runtime_component_ref": str(component_spec.get("runtime_component_ref") or ""),
                "operation_component_label": str(component_spec.get("operation_component_label") or ""),
                "review_projection": str(projection.get("review_projection") or ""),
                "review_projection_role": str(projection.get("review_projection_role") or ""),
                "projection_status": "first_limiting_projection",
                "settled_metric_eligible": row.get("settled_metric_eligible") is True,
                "prediction_score": _round(_float(row.get("prediction_score"))),
                "outcome_label": _text(row.get("outcome_label")),
                "realized_return": _round(_float(row.get("realized_return"))),
                "fixed_input_only": True,
            }
        )
    return output


def _operation_component_flow_rows(
    decision_surface_rows: Sequence[Mapping[str, Any]],
    operation_review_projection_rows: Sequence[Mapping[str, Any]],
    *,
    replay_receipt: Mapping[str, Any],
) -> list[dict[str, Any]]:
    first_projection_by_decision = {
        str(row.get("decision_id") or ""): row
        for row in operation_review_projection_rows
    }
    entry_path_specs = [spec for spec in OPERATION_COMPONENT_SPECS if bool(spec["entry_path_participant"])]
    entry_order = {
        str(spec["operation_component_id"]): index
        for index, spec in enumerate(entry_path_specs)
    }
    previous_bad_rate: float | None = None
    output: list[dict[str, Any]] = []
    for spec in OPERATION_COMPONENT_SPECS:
        component_id = str(spec["operation_component_id"])
        component_index = int(spec["component_index"])
        if component_id == "C03_lifecycle_operation":
            output.append(_operation_component_lifecycle_flow_row(spec=spec, replay_receipt=replay_receipt))
            continue
        current_order = entry_order[component_id]
        entered_rows = [
            row
            for row in decision_surface_rows
            if _operation_order_for_decision(row, first_projection_by_decision, entry_order) >= current_order
        ]
        first_limiting_rows = [
            row
            for row in entered_rows
            if str((first_projection_by_decision.get(str(row.get("decision_id") or "")) or {}).get("operation_component_id") or "")
            == component_id
        ]
        first_limiting_projections = sorted(
            {
                str((first_projection_by_decision.get(str(row.get("decision_id") or "")) or {}).get("review_projection") or "")
                for row in first_limiting_rows
                if str((first_projection_by_decision.get(str(row.get("decision_id") or "")) or {}).get("review_projection") or "")
            }
        )
        censored_count = sum(
            1
            for row in first_limiting_rows
            if str(row.get("first_limiting_surface") or "") == "C06_selected_option_path_materialization"
        )
        blocked_count = 0 if component_id == "C07_failure_review_operation" else len(first_limiting_rows)
        passed_rows = [
            row
            for row in entered_rows
            if _operation_order_for_decision(row, first_projection_by_decision, entry_order) > current_order
            or component_id == "C07_failure_review_operation"
        ]
        passed_settled_rows = _settled_rows(passed_rows)
        bad_rate = (_bad_outcome_count(passed_settled_rows) / len(passed_settled_rows)) if passed_settled_rows else None
        mean_realized_return = _mean(_numeric_values(passed_settled_rows, "realized_return"))
        tail_loss_count = sum(1 for row in passed_settled_rows if _float(row.get("realized_return")) <= -0.2)
        verdict, basis = _operation_component_flow_verdict(
            component_id=component_id,
            entered_count=len(entered_rows),
            first_limiting_count=len(first_limiting_rows),
            censored_count=censored_count,
            settled_count=len(passed_settled_rows),
            post_bad_rate=bad_rate,
            mean_realized_return=mean_realized_return,
            tail_loss_count=tail_loss_count,
            previous_bad_rate=previous_bad_rate,
            first_limiting_projections=first_limiting_projections,
        )
        if bad_rate is not None:
            previous_bad_rate = bad_rate
        output.append(
            {
                "component_index": component_index,
                "operation_component_id": component_id,
                "runtime_component_ref": str(spec["runtime_component_ref"]),
                "operation_component_label": str(spec["operation_component_label"]),
                "operation_role": str(spec["operation_role"]),
                "applicability_status": "candidate_entry_path",
                "input_count": len(entered_rows),
                "output_count": len(passed_rows),
                "dropped_or_blocked_count": blocked_count,
                "censored_count": censored_count,
                "settled_metric_eligible_count": len(passed_settled_rows),
                "settled_metric_excluded_count": len(passed_rows) - len(passed_settled_rows),
                "first_limiting_projection_count": len(first_limiting_rows),
                "first_limiting_projections": ";".join(first_limiting_projections),
                "review_projection_refs": ";".join(_operation_component_projection_refs(component_id)),
                "outcome_metric_available": bool(passed_settled_rows),
                "mean_prediction_score": _round(_mean(_numeric_values(passed_settled_rows, "prediction_score"))),
                "score_label_spearman": _round(
                    _spearman_for_key(passed_settled_rows, "prediction_score", "outcome_label")
                ),
                "score_return_spearman": _round(
                    _spearman_for_key(passed_settled_rows, "prediction_score", "realized_return")
                ),
                "mean_realized_return": _round(mean_realized_return),
                "hit_rate": _round(
                    sum(1 for row in passed_settled_rows if str(row.get("outcome_label")) == "1")
                    / len(passed_settled_rows)
                )
                if passed_settled_rows
                else None,
                "tail_loss_count": tail_loss_count,
                "stage_verdict": verdict,
                "verdict_basis": basis,
                "threshold_selection_performed": False,
                "retraining_performed": False,
                "fixed_input_only": True,
            }
        )
    return output


def _operation_component_lifecycle_flow_row(
    *,
    spec: Mapping[str, Any],
    replay_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    component_id = str(spec["operation_component_id"])
    summary = _as_mapping(replay_receipt.get("portfolio_selection_summary"))
    if not summary:
        applicability_status = "missing_lifecycle_state_evidence"
        input_count = 0
        output_count = 0
        blocked_count = 0
        eligible_count = 0
        first_limiting_count = 0
        stage_verdict = "insufficient_evidence"
        verdict_basis = "portfolio_lifecycle_summary_missing_from_replay_receipt"
        outcome_metric_available = False
    else:
        replacement_evaluated = int(_float(summary.get("portfolio_replacement_evaluated_count"), default=0.0))
        replacement_triggered = int(_float(summary.get("portfolio_replacement_triggered_count"), default=0.0))
        blocked_count = sum(
            int(_float(summary.get(key), default=0.0))
            for key in (
                "portfolio_replacement_blocked_by_threshold_count",
                "portfolio_replacement_blocked_by_expression_count",
                "portfolio_replacement_blocked_by_allocation_count",
                "portfolio_allocation_contract_violation_count",
            )
        )
        continued_count = int(_float(summary.get("portfolio_existing_position_continued_count"), default=0.0))
        input_count = int(
            _float(
                summary.get("m04_trade_intent_count")
                if summary.get("m04_trade_intent_count") not in {None, ""}
                else summary.get("candidate_count"),
                default=0.0,
            )
        )
        output_count = int(_float(summary.get("final_position_count"), default=0.0))
        eligible_count = replacement_evaluated + continued_count + replacement_triggered
        first_limiting_count = blocked_count
        outcome_metric_available = True
        applicability_status = "portfolio_lifecycle_state_reviewed"
        if int(_float(summary.get("portfolio_allocation_contract_violation_count"), default=0.0)) > 0:
            stage_verdict = "first_observed_deterioration"
            verdict_basis = "portfolio_allocation_contract_violation_present"
        elif blocked_count > replacement_triggered and replacement_evaluated:
            stage_verdict = "lifecycle_replacement_pressure_observed"
            verdict_basis = "replacement_attempts_more_often_blocked_than_triggered"
        elif eligible_count > 0:
            stage_verdict = "neutral_measured"
            verdict_basis = "portfolio_lifecycle_summary_published"
        else:
            stage_verdict = "neutral_or_unmeasured"
            verdict_basis = "no_lifecycle_transitions_reported"
    return {
        "component_index": int(spec["component_index"]),
        "operation_component_id": component_id,
        "runtime_component_ref": str(spec["runtime_component_ref"]),
        "operation_component_label": str(spec["operation_component_label"]),
        "operation_role": str(spec["operation_role"]),
        "applicability_status": applicability_status,
        "input_count": input_count,
        "output_count": output_count,
        "dropped_or_blocked_count": blocked_count,
        "censored_count": 0,
        "settled_metric_eligible_count": eligible_count,
        "settled_metric_excluded_count": 0,
        "first_limiting_projection_count": first_limiting_count,
        "first_limiting_projections": "portfolio_replacement_or_allocation_block" if first_limiting_count else "",
        "review_projection_refs": ";".join(_operation_component_projection_refs(component_id)),
        "outcome_metric_available": outcome_metric_available,
        "mean_prediction_score": None,
        "score_label_spearman": None,
        "score_return_spearman": None,
        "mean_realized_return": None,
        "hit_rate": None,
        "tail_loss_count": 0,
        "stage_verdict": stage_verdict,
        "verdict_basis": verdict_basis,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _operation_component_action_rows(
    *,
    rows: Sequence[Mapping[str, Any]],
    decision_surface_rows: Sequence[Mapping[str, Any]],
    operation_review_projection_rows: Sequence[Mapping[str, Any]],
    replay_receipt: Mapping[str, Any],
    layer_review_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    surface_by_decision = {
        str(row.get("decision_id") or ""): row
        for row in decision_surface_rows
    }
    first_projection_by_decision = {
        str(row.get("decision_id") or ""): row
        for row in operation_review_projection_rows
    }
    layer_review_by_decision_layer = {
        (str(row.get("source_decision_id") or ""), str(row.get("layer_id") or "")): row
        for row in layer_review_rows
    }
    lifecycle_summary = _as_mapping(replay_receipt.get("portfolio_selection_summary"))
    action_rows: list[dict[str, Any]] = []
    for decision_index, row in enumerate(rows, start=1):
        decision_id = str(row.get("decision_id") or f"decision_{decision_index:08d}")
        surface = surface_by_decision.get(decision_id, {})
        first_projection = first_projection_by_decision.get(decision_id, {})
        for component_id in (
            "C01_intake_operation",
            "C02_entry_operation",
            "C03_lifecycle_operation",
            "C04_expression_review_operation",
            "C05_order_intent_operation",
            "C06_execution_gate_operation",
            "C07_failure_review_operation",
        ):
            action_rows.append(
                _operation_component_action_row(
                    row=row,
                    decision_id=decision_id,
                    decision_index=decision_index,
                    component_id=component_id,
                    surface=surface,
                    first_projection=first_projection,
                    lifecycle_summary=lifecycle_summary,
                    layer_label_row=_operation_layer_label_row(
                        component_id=component_id,
                        decision_id=decision_id,
                        layer_review_by_decision_layer=layer_review_by_decision_layer,
                    ),
                )
            )
    return action_rows


def _operation_component_action_row(
    *,
    row: Mapping[str, Any],
    decision_id: str,
    decision_index: int,
    component_id: str,
    surface: Mapping[str, Any],
    first_projection: Mapping[str, Any],
    lifecycle_summary: Mapping[str, Any],
    layer_label_row: Mapping[str, Any],
) -> dict[str, Any]:
    component = OPERATION_COMPONENT_BY_ID[component_id]
    method = OPERATION_COMPONENT_ANALYSIS_METHODS.get(component_id, {})
    target = str(row.get("target_symbol") or row.get("target_ref") or "")
    timestamp = str(row.get("timestamp") or row.get("decision_time") or "")
    replay_month = str(row.get("replay_month") or timestamp[:7])
    first_limiting_component = str(first_projection.get("operation_component_id") or "")
    first_limiting_reason = str(surface.get("first_limiting_surface_reason") or first_projection.get("review_projection") or "")
    chosen_action = _operation_chosen_action(component_id, row, layer_label_row)
    best_available_action = _operation_best_available_action(component_id, row, layer_label_row)
    feasible_action_set_ref = _operation_feasible_action_set_ref(component_id, row, layer_label_row)
    feasible_action_set_status = _operation_feasible_action_set_status(row, layer_label_row)
    common = {
        "source_decision_id": decision_id,
        "source_decision_index": decision_index,
        "decision_time": timestamp,
        "replay_month": replay_month,
        "target_symbol": target,
        "operation_component_id": component_id,
        "runtime_component_ref": str(component.get("runtime_component_ref") or ""),
        "operation_component_label": str(component.get("operation_component_label") or ""),
        "component_index": int(component.get("component_index") or 0),
        "analysis_method": method.get("analysis_method", ""),
        "evidence_role": method.get("evidence_role", ""),
        "label_role": method.get("label_role", ""),
        "trigger_state": _operation_trigger_state(component_id, row, lifecycle_summary),
        "pit_feasible_action_set_ref": feasible_action_set_ref,
        "pit_feasible_action_count": _operation_feasible_action_count(component_id, row, layer_label_row),
        "pit_feasible_action_set_status": feasible_action_set_status,
        "review_boundary_ref": feasible_action_set_ref,
        "review_boundary_status": _operation_review_boundary_status(
            feasible_action_set_status=feasible_action_set_status,
            first_limiting_component=first_limiting_component,
            component_id=component_id,
            first_limiting_reason=first_limiting_reason,
        ),
        "component_objective": OPERATION_COMPONENT_OBJECTIVES.get(component_id, ""),
        "chosen_action": chosen_action,
        "best_available_action_by_future_outcome": best_available_action,
        "chosen_action_return": _operation_action_return(row, layer_label_row, "chosen_action_return"),
        "best_available_action_return": _operation_action_return(row, layer_label_row, "best_available_action_return"),
        "chosen_rank_ex_post": _operation_chosen_rank_ex_post(row, layer_label_row),
        "component_correctness_class": _operation_component_correctness_class(component_id, row, layer_label_row),
        "post_replay_label_basis": _operation_post_replay_label_basis(component_id, row),
        "upstream_decision_state_policy": "received_upstream_state_is_fixed_review_input",
        "downstream_review_input_policy": "judge_component_only_against_received_decision_time_inputs",
        "upstream_error_isolation_scope": "attribute_upstream_defects_to_earliest_layer_or_boundary",
        "responsibility_assignment_policy": "component_local_correctness_given_received_inputs",
        "realized_return": _round(_float(row.get("realized_return"))) if row.get("realized_return") not in {None, ""} else None,
        "regret_to_best_available": _operation_regret_to_best_available(row, layer_label_row),
        "impact_normalized_severity_score": _round(abs(_float(row.get("realized_return")))) if row.get("realized_return") not in {None, ""} else None,
        "review_status": "reviewable_from_replay_row",
        "fixed_input_only": True,
    }
    if component_id == "C01_intake_operation":
        return {
            **common,
            "operation_action_row_id": f"{decision_id}:c01",
            "operation_action": "prepare_point_in_time_inputs",
            "operation_status": "inputs_ready",
            "input_ref": str(row.get("candidate_set_scope") or ""),
            "input_summary": f"{target} at {timestamp}",
            "output_ref": str(row.get("model_evidence_mode") or "model_evidence_chain"),
            "output_summary": ";".join(str(value) for value in row.get("model_evidence_chain") or []),
            "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
            "decision_time_evidence_fields": "model_evidence_chain;candidate_set_scope;model_layer_diagnostics",
            "post_replay_label_fields": "",
        }
    if component_id == "C02_entry_operation":
        status = str(row.get("decision_status") or "")
        return {
            **common,
            "operation_action_row_id": f"{decision_id}:c02",
            "operation_action": str(row.get("decision_action") or row.get("action") or ""),
            "operation_status": status,
            "input_ref": str(row.get("candidate_set_scope") or ""),
            "input_summary": _entry_operation_summary(row),
            "output_ref": str(row.get("decision_intended_side") or row.get("decision_intended_action") or ""),
            "output_summary": str(row.get("decision_action") or row.get("action") or ""),
            "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
            "decision_time_evidence_fields": "prediction_score;decision_action;model_04_unified_decision",
            "post_replay_label_fields": "realized_return;directional_underlying_return",
        }
    if component_id == "C03_lifecycle_operation":
        lifecycle_status = "portfolio_lifecycle_state_reviewed" if lifecycle_summary else "missing_lifecycle_state_evidence"
        return {
            **common,
            "operation_action_row_id": f"{decision_id}:c03",
            "operation_action": "check_portfolio_lifecycle_and_replacement",
            "operation_status": lifecycle_status,
            "input_ref": "portfolio_selection_summary" if lifecycle_summary else "",
            "input_summary": _lifecycle_operation_summary(lifecycle_summary),
            "output_ref": "portfolio_position_state",
            "output_summary": _lifecycle_operation_output(lifecycle_summary),
            "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
            "decision_time_evidence_fields": "portfolio_selection_summary;replacement_review",
            "post_replay_label_fields": "",
        }
    if component_id == "C04_expression_review_operation":
        path_status = str(row.get("selected_option_path_status") or surface.get("selected_option_path_status") or row.get("fill_status") or "")
        return {
            **common,
            "operation_action_row_id": f"{decision_id}:c04",
            "operation_action": str(row.get("decision_expression_type") or row.get("selected_expression_type") or ""),
            "operation_status": path_status,
            "input_ref": str(row.get("asset_expression_route") or ""),
            "input_summary": _option_expression_summary(row),
            "output_ref": str(row.get("instrument_ref") or surface.get("selected_option_contract_ref") or ""),
            "output_summary": str(row.get("decision_instrument_scope") or row.get("asset_class") or ""),
            "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
            "decision_time_evidence_fields": "decision_expression_type;selected_option_path_status;eligible_candidate_count",
            "post_replay_label_fields": "realized_return;baseline_return",
        }
    if component_id == "C05_order_intent_operation":
        return {
            **common,
            "operation_action_row_id": f"{decision_id}:c05",
            "operation_action": "create_sized_order_intent",
            "operation_status": str(row.get("decision_status") or ""),
            "input_ref": str(row.get("account_sleeve_id") or ""),
            "input_summary": _order_intent_summary(row),
            "output_ref": str(row.get("instrument_ref") or ""),
            "output_summary": str(row.get("decision_intended_action") or row.get("action") or ""),
            "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
            "decision_time_evidence_fields": "account_sleeve_id;planned_notional;cost;decision_intended_action",
            "post_replay_label_fields": "",
        }
    if component_id == "C06_execution_gate_operation":
        return {
            **common,
            "operation_action_row_id": f"{decision_id}:c06",
            "operation_action": "simulate_execution_gate_and_fill",
            "operation_status": str(row.get("fill_status") or ""),
            "input_ref": str(row.get("instrument_ref") or ""),
            "input_summary": str(row.get("decision_instrument_scope") or row.get("asset_class") or ""),
            "output_ref": str(row.get("fill_status") or ""),
            "output_summary": _execution_output_summary(row),
            "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
            "decision_time_evidence_fields": "instrument_ref;fill_status;asset_class",
            "post_replay_label_fields": "realized_return;fill_status",
        }
    return {
        **common,
        "operation_action_row_id": f"{decision_id}:c07",
        "operation_action": "review_settled_failure_and_residual_gap",
        "operation_status": "reviewed",
        "input_ref": str(row.get("miss_attribution_layer") or ""),
        "input_summary": str(row.get("miss_attribution_layer") or "settled_outcome_review"),
        "output_ref": str(row.get("first_gap_component") or first_projection.get("review_projection") or ""),
        "output_summary": _failure_review_summary(row),
        "block_reason": first_limiting_reason if first_limiting_component == component_id else "",
        "decision_time_evidence_fields": "decision_status;fill_status;miss_attribution_layer",
        "post_replay_label_fields": "realized_return;baseline_return;regret_to_best_available;outcome_label",
    }


def _entry_operation_summary(row: Mapping[str, Any]) -> str:
    parts = [
        f"score={_round(_float(row.get('prediction_score')))}" if row.get("prediction_score") not in {None, ""} else "",
        f"side={row.get('decision_intended_side')}" if row.get("decision_intended_side") not in {None, ""} else "",
        f"confidence_min={row.get('entry_minimum_alpha_confidence')}" if row.get("entry_minimum_alpha_confidence") not in {None, ""} else "",
    ]
    return "; ".join(part for part in parts if part)


def _lifecycle_operation_summary(summary: Mapping[str, Any]) -> str:
    if not summary:
        return "portfolio lifecycle summary missing"
    return (
        f"continued={int(_float(summary.get('portfolio_existing_position_continued_count'), default=0.0))}; "
        f"replacement_evaluated={int(_float(summary.get('portfolio_replacement_evaluated_count'), default=0.0))}; "
        f"replacement_triggered={int(_float(summary.get('portfolio_replacement_triggered_count'), default=0.0))}"
    )


def _lifecycle_operation_output(summary: Mapping[str, Any]) -> str:
    if not summary:
        return "missing_lifecycle_state_evidence"
    return (
        f"final_positions={int(_float(summary.get('final_position_count'), default=0.0))}; "
        f"allocation_violations={int(_float(summary.get('portfolio_allocation_contract_violation_count'), default=0.0))}"
    )


def _option_expression_summary(row: Mapping[str, Any]) -> str:
    parts = [
        f"expression={row.get('decision_expression_type')}" if row.get("decision_expression_type") not in {None, ""} else "",
        f"route={row.get('asset_expression_route')}" if row.get("asset_expression_route") not in {None, ""} else "",
        f"contract={row.get('instrument_ref')}" if row.get("instrument_ref") not in {None, ""} else "",
    ]
    return "; ".join(part for part in parts if part)


def _order_intent_summary(row: Mapping[str, Any]) -> str:
    parts = [
        f"sleeve={row.get('account_sleeve_id')}" if row.get("account_sleeve_id") not in {None, ""} else "",
        f"cost={_round(_float(row.get('cost')))}" if row.get("cost") not in {None, ""} else "",
        f"action={row.get('decision_intended_action') or row.get('action')}" if (row.get("decision_intended_action") or row.get("action")) not in {None, ""} else "",
    ]
    return "; ".join(part for part in parts if part)


def _execution_output_summary(row: Mapping[str, Any]) -> str:
    parts = [
        f"fill={row.get('fill_status')}" if row.get("fill_status") not in {None, ""} else "",
        f"return={_round(_float(row.get('realized_return')))}" if row.get("realized_return") not in {None, ""} else "",
        f"baseline={_round(_float(row.get('baseline_return')))}" if row.get("baseline_return") not in {None, ""} else "",
    ]
    return "; ".join(part for part in parts if part)


def _failure_review_summary(row: Mapping[str, Any]) -> str:
    parts = [
        f"outcome={row.get('outcome_label')}" if row.get("outcome_label") not in {None, ""} else "",
        f"regret={_round(_regret_to_best_available(row))}",
        f"gap={row.get('first_gap_component') or row.get('miss_attribution_layer')}",
    ]
    return "; ".join(part for part in parts if part)


def _operation_order_for_decision(
    row: Mapping[str, Any],
    first_projection_by_decision: Mapping[str, Mapping[str, Any]],
    entry_order: Mapping[str, int],
) -> int:
    projection_row = first_projection_by_decision.get(str(row.get("decision_id") or "")) or {}
    component_id = str(projection_row.get("operation_component_id") or "")
    return int(entry_order.get(component_id, len(entry_order) - 1))


def _operation_component_flow_verdict(
    *,
    component_id: str,
    entered_count: int,
    first_limiting_count: int,
    censored_count: int,
    settled_count: int,
    post_bad_rate: float | None,
    mean_realized_return: float | None,
    tail_loss_count: int,
    previous_bad_rate: float | None,
    first_limiting_projections: Sequence[str],
) -> tuple[str, str]:
    if entered_count <= 0:
        return "neutral_or_unmeasured", "component_not_reached"
    if censored_count and censored_count / entered_count >= 0.5:
        return "dominant_censoring_point", "majority_of_entered_rows_missing_settled_path"
    if first_limiting_count and component_id != "C07_failure_review_operation":
        return "first_observed_deterioration", "rows_first_limited_at_operation_component"
    if component_id == "C07_failure_review_operation":
        if settled_count < 5 or post_bad_rate is None:
            return "insufficient_evidence", "too_few_settled_rows_for_failure_review"
        if post_bad_rate > 0.5:
            return "first_observed_deterioration", "settled_survivor_cohort_bad_rate_above_half"
        if mean_realized_return is not None and mean_realized_return < 0:
            return "first_observed_deterioration", "settled_survivor_cohort_negative_mean_return"
        if tail_loss_count:
            return "first_observed_deterioration", "settled_survivor_tail_loss_present"
        return "neutral_measured", "settled_survivor_cohort_not_majority_bad"
    if settled_count < 5 or post_bad_rate is None:
        return "insufficient_evidence", "too_few_settled_rows_for_component_quality_flow"
    if previous_bad_rate is None:
        return "unmeasured", "no_prior_observable_bad_rate"
    if post_bad_rate - previous_bad_rate >= 0.15:
        return "amplifies_prior_damage", "post_component_bad_rate_increased"
    if previous_bad_rate - post_bad_rate >= 0.15:
        return "pulls_back_prior_damage", "post_component_bad_rate_decreased"
    return "neutral_measured", "bad_rate_change_below_materiality"


def _operation_component_metric_rows(
    *,
    rows: Sequence[Mapping[str, Any]],
    target_selection_universe_rows: Sequence[Mapping[str, Any]],
    portfolio_capacity_rows: Sequence[Mapping[str, Any]],
    model_candidate_selection_trace_rows: Sequence[Mapping[str, Any]],
    replay_receipt: Mapping[str, Any],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    output.extend(_target_selection_metric_rows(rows, target_selection_universe_rows, model_candidate_selection_trace_rows))
    output.extend(_model_candidate_selection_metric_rows(rows, model_candidate_selection_trace_rows))
    output.append(_entry_signal_metric_row(rows))
    output.extend(_lifecycle_metric_rows(replay_receipt))
    output.append(_option_expression_metric_row(rows))
    output.append(_order_intent_metric_row(rows, portfolio_capacity_rows))
    output.append(_execution_gate_metric_row(rows))
    output.append(_failure_review_metric_row(rows))
    return output


def _model_candidate_selection_metric_rows(
    rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not trace_rows:
        return [
            _operation_component_metric_row(
                component_id="C01_intake_operation",
                metric_family="model_candidate_discovery",
                metric_name="visible_candidate_model_scoring_coverage",
                metric_scope="point_in_time_model_candidate_trace",
                availability_status="data_gap",
                reason_codes=["model_candidate_selection_trace_missing"],
                point_in_time_input_fields=["visible_candidate", "model_score_available"],
                future_outcome_fields=[],
                row_count=len(rows),
            ),
            _operation_component_metric_row(
                component_id="C02_entry_operation",
                metric_family="model_candidate_selection",
                metric_name="model_ranked_candidate_selection_funnel",
                metric_scope="point_in_time_model_candidate_trace",
                availability_status="data_gap",
                reason_codes=["model_candidate_selection_trace_missing"],
                point_in_time_input_fields=["diagnostic_rank_score", "model_rank_within_timestamp", "selected_by_replay"],
                future_outcome_fields=[],
                row_count=len(rows),
            ),
        ]
    scored_rows = [row for row in trace_rows if _truthy(row.get("model_score_available"))]
    selected_rows = [row for row in trace_rows if _truthy(row.get("selected_by_replay"))]
    entry_intent_rows = [row for row in trace_rows if _truthy(row.get("m04_trade_intent"))]
    option_signal_rows = [row for row in trace_rows if _truthy(row.get("option_expression_signal_required"))]
    selected_rank_values = [
        _float(row.get("model_rank_within_timestamp"))
        for row in selected_rows
        if row.get("model_rank_within_timestamp") not in {None, ""}
    ]
    timestamp_counts = Counter(str(row.get("replay_time_pointer") or row.get("timestamp") or "") for row in trace_rows)
    status_counts = Counter(str(row.get("model_candidate_trace_status") or "unknown") for row in trace_rows)
    return [
        _operation_component_metric_row(
            component_id="C01_intake_operation",
            metric_family="model_candidate_discovery",
            metric_name="visible_candidate_model_scoring_coverage",
            metric_scope="point_in_time_model_candidate_trace",
            availability_status="computed",
            reason_codes=[],
            point_in_time_input_fields=["visible_candidate", "model_score_available"],
            future_outcome_fields=[],
            row_count=len(trace_rows),
            eligible_row_count=len(scored_rows),
            selected_count=len(entry_intent_rows),
            universe_count_mean=_mean(timestamp_counts.values()),
            selected_target_present_count=len(scored_rows),
            value=(len(scored_rows) / len(trace_rows)) if trace_rows else None,
        ),
        _operation_component_metric_row(
            component_id="C02_entry_operation",
            metric_family="model_candidate_selection",
            metric_name="model_ranked_candidate_selection_funnel",
            metric_scope="point_in_time_model_candidate_trace",
            availability_status="computed",
            reason_codes=[f"{key}:{value}" for key, value in sorted(status_counts.items())],
            point_in_time_input_fields=[
                "diagnostic_rank_score",
                "model_rank_within_timestamp",
                "m04_trade_intent",
                "option_expression_signal_required",
                "selected_by_replay",
            ],
            future_outcome_fields=[],
            row_count=len(trace_rows),
            eligible_row_count=len(option_signal_rows),
            selected_count=len(selected_rows),
            universe_count_mean=_mean(timestamp_counts.values()),
            selected_forward_return_rank_mean=_mean(selected_rank_values),
            value=(len(selected_rows) / len(option_signal_rows)) if option_signal_rows else None,
        ),
    ]


def _sector_opportunity_packet_path(target_selection_universe_metrics_path: Path | None) -> Path | None:
    if target_selection_universe_metrics_path is None:
        return None
    candidate = target_selection_universe_metrics_path.with_name("sector_opportunity_packet.csv")
    return candidate if candidate.exists() else None


def _target_selection_metric_rows(
    rows: Sequence[Mapping[str, Any]],
    target_selection_universe_rows: Sequence[Mapping[str, Any]],
    model_candidate_selection_trace_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not target_selection_universe_rows:
        if model_candidate_selection_trace_rows:
            return _trace_only_target_selection_metric_rows(rows, model_candidate_selection_trace_rows)
        return [
            _operation_component_metric_row(
                component_id=component_id,
                metric_family="target_selection_quality",
                metric_name=metric_name,
                metric_scope="decision_time_visible_universe",
                availability_status="data_gap",
                reason_codes=["target_selection_universe_metrics_missing"],
                point_in_time_input_fields=["timestamp", "target_ref", "visible_universe_membership"],
                future_outcome_fields=["forward_return"],
                row_count=len(rows),
            )
            for component_id, metric_name in (
                ("C01_intake_operation", "visible_universe_integrity"),
                ("C01_intake_operation", "selected_sector_bucket_forward_return_rank"),
                ("C02_entry_operation", "selected_target_forward_return_rank_within_sector"),
            )
        ]

    universe_by_timestamp: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in target_selection_universe_rows:
        universe_by_timestamp[str(row.get("timestamp") or "")].append(row)

    selected_sector_results: list[dict[str, float]] = []
    selected_target_results: list[dict[str, float]] = []
    visible_universe_counts: list[float] = []
    present_count = 0
    for row in rows:
        timestamp = str(row.get("timestamp") or "")
        target_ref = str(row.get("target_ref") or "")
        universe_rows = universe_by_timestamp.get(timestamp, [])
        visible_rows = [
            item
            for item in universe_rows
            if str(item.get("visible_universe_membership") or "true").strip().lower() in {"true", "1", "yes"}
        ]
        visible_universe_counts.append(float(len(visible_rows)))
        ranked_rows = [
            item
            for item in visible_rows
            if _target_universe_forward_return(item) is not None
        ]
        selected_visible_row = next(
            (item for item in visible_rows if str(item.get("target_ref") or item.get("symbol") or "") == target_ref),
            None,
        )
        if selected_visible_row is None:
            continue
        present_count += 1
        selected_sector_bucket = _target_universe_sector_bucket(selected_visible_row)
        selected_row = next(
            (item for item in ranked_rows if str(item.get("target_ref") or item.get("symbol") or "") == target_ref),
            None,
        )
        sector_ranked_rows = [
            item for item in ranked_rows if _target_universe_sector_bucket(item) == selected_sector_bucket
        ]
        sector_means = _target_universe_sector_return_means(ranked_rows)
        selected_sector_mean = sector_means.get(selected_sector_bucket)
        if selected_sector_mean is not None and sector_means:
            sector_count = len(sector_means)
            sector_rank = 1 + sum(1 for value in sector_means.values() if value > selected_sector_mean)
            sector_percentile = 1.0 if sector_count <= 1 else (sector_count - sector_rank) / (sector_count - 1)
            selected_sector_results.append(
                {
                    "selected_forward_return": selected_sector_mean,
                    "rank": float(sector_rank),
                    "percentile": sector_percentile,
                    "top_quartile_hit": 1.0 if sector_rank <= max(1, int((sector_count + 3) // 4)) else 0.0,
                    "opportunity_cost_to_best": max(sector_means.values()) - selected_sector_mean,
                    "opportunity_cost_to_median": (_median(sector_means.values()) or 0.0) - selected_sector_mean,
                    "universe_count": float(sector_count),
                }
            )
        if selected_row is None:
            continue
        selected_return = _target_universe_forward_return(selected_row)
        if selected_return is None:
            continue
        returns = [_target_universe_forward_return(item) for item in sector_ranked_rows]
        numeric_returns = [float(value) for value in returns if value is not None]
        if not numeric_returns:
            continue
        rank = 1 + sum(1 for value in numeric_returns if value > selected_return)
        universe_count = len(numeric_returns)
        percentile = 1.0 if universe_count <= 1 else (universe_count - rank) / (universe_count - 1)
        best_return = max(numeric_returns)
        median_return = _median(numeric_returns)
        selected_target_results.append(
            {
                "selected_forward_return": selected_return,
                "rank": float(rank),
                "percentile": percentile,
                "top_quartile_hit": 1.0 if rank <= max(1, int((universe_count + 3) // 4)) else 0.0,
                "opportunity_cost_to_best": best_return - selected_return,
                "opportunity_cost_to_median": (median_return or 0.0) - selected_return,
                "universe_count": float(universe_count),
            }
        )

    integrity_status = "computed" if present_count == len(rows) else "partial"
    if present_count <= 0:
        integrity_status = "data_gap"
    if not selected_sector_results:
        sector_status = "data_gap"
    elif len(selected_sector_results) < len(rows):
        sector_status = "partial"
    else:
        sector_status = "computed"
    if not selected_target_results:
        target_status = "data_gap"
    elif len(selected_target_results) < len(rows):
        target_status = "partial"
    else:
        target_status = "computed"
    return [
        _operation_component_metric_row(
            component_id="C01_intake_operation",
            metric_family="target_selection_quality",
            metric_name="visible_universe_integrity",
            metric_scope="decision_time_visible_universe",
            availability_status=integrity_status,
            reason_codes=[] if integrity_status == "computed" else ["selected_target_missing_from_visible_universe"],
            point_in_time_input_fields=["timestamp", "target_ref", "visible_universe_membership"],
            future_outcome_fields=[],
            row_count=len(rows),
            eligible_row_count=present_count,
            selected_count=len(rows),
            selected_target_present_count=present_count,
            universe_count_mean=_mean(visible_universe_counts),
            value=(present_count / len(rows)) if rows else None,
        ),
        _operation_component_metric_row(
            component_id="C01_intake_operation",
            metric_family="sector_selection_effectiveness",
            metric_name="selected_sector_bucket_forward_return_rank",
            metric_scope="decision_time_visible_sector_buckets",
            availability_status=sector_status,
            reason_codes=[] if sector_status == "computed" else ["selected_sector_bucket_forward_return_unavailable"],
            point_in_time_input_fields=[
                "timestamp",
                "target_ref",
                "sector_bucket_ref",
                "visible_universe_membership",
            ],
            future_outcome_fields=["sector_forward_return_mean"],
            row_count=len(rows),
            eligible_row_count=len(selected_sector_results),
            selected_count=len(rows),
            selected_target_present_count=present_count,
            universe_count_mean=_mean(result["universe_count"] for result in selected_sector_results),
            selected_forward_return_mean=_mean(result["selected_forward_return"] for result in selected_sector_results),
            selected_forward_return_rank_mean=_mean(result["rank"] for result in selected_sector_results),
            selected_forward_return_percentile_mean=_mean(result["percentile"] for result in selected_sector_results),
            top_quartile_hit_rate=_mean(result["top_quartile_hit"] for result in selected_sector_results),
            opportunity_cost_to_best_mean=_mean(result["opportunity_cost_to_best"] for result in selected_sector_results),
            opportunity_cost_to_median_mean=_mean(
                result["opportunity_cost_to_median"] for result in selected_sector_results
            ),
            value=_mean(result["percentile"] for result in selected_sector_results),
        ),
        _operation_component_metric_row(
            component_id="C02_entry_operation",
            metric_family="target_selection_effectiveness",
            metric_name="selected_target_forward_return_rank_within_sector",
            metric_scope="decision_time_selected_sector_bucket",
            availability_status=target_status,
            reason_codes=[] if target_status == "computed" else ["selected_target_sector_forward_return_unavailable"],
            point_in_time_input_fields=["timestamp", "target_ref", "sector_bucket_ref", "visible_universe_membership"],
            future_outcome_fields=["forward_return"],
            row_count=len(rows),
            eligible_row_count=len(selected_target_results),
            selected_count=len(rows),
            selected_target_present_count=present_count,
            universe_count_mean=_mean(result["universe_count"] for result in selected_target_results),
            selected_forward_return_mean=_mean(result["selected_forward_return"] for result in selected_target_results),
            selected_forward_return_rank_mean=_mean(result["rank"] for result in selected_target_results),
            selected_forward_return_percentile_mean=_mean(result["percentile"] for result in selected_target_results),
            top_quartile_hit_rate=_mean(result["top_quartile_hit"] for result in selected_target_results),
            opportunity_cost_to_best_mean=_mean(result["opportunity_cost_to_best"] for result in selected_target_results),
            opportunity_cost_to_median_mean=_mean(
                result["opportunity_cost_to_median"] for result in selected_target_results
            ),
            value=_mean(result["percentile"] for result in selected_target_results),
        ),
    ]


def _trace_only_target_selection_metric_rows(
    rows: Sequence[Mapping[str, Any]],
    trace_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    scored_rows = [row for row in trace_rows if _truthy(row.get("model_score_available"))]
    scored_keys = {
        (
            str(row.get("replay_time_pointer") or row.get("timestamp") or ""),
            str(row.get("target_ref") or ""),
        )
        for row in scored_rows
    }
    selected_present_count = sum(
        1
        for row in rows
        if (
            str(row.get("timestamp") or ""),
            str(row.get("target_ref") or ""),
        )
        in scored_keys
    )
    timestamp_counts = Counter(str(row.get("replay_time_pointer") or row.get("timestamp") or "") for row in scored_rows)
    selected_trace_rows = [row for row in scored_rows if _truthy(row.get("selected_by_replay"))]
    selected_rank_values = [
        _float(row.get("model_rank_within_timestamp"))
        for row in selected_trace_rows
        if row.get("model_rank_within_timestamp") not in {None, ""}
    ]
    return [
        _operation_component_metric_row(
            component_id="C01_intake_operation",
            metric_family="target_selection_quality",
            metric_name="visible_universe_integrity",
            metric_scope="point_in_time_model_candidate_trace",
            availability_status="computed",
            reason_codes=["trace_only_visible_universe_membership"],
            point_in_time_input_fields=["replay_time_pointer", "target_ref", "model_score_available"],
            future_outcome_fields=[],
            row_count=len(rows),
            eligible_row_count=len(scored_rows),
            selected_count=len(rows),
            selected_target_present_count=selected_present_count,
            universe_count_mean=_mean(timestamp_counts.values()),
            value=(selected_present_count / len(rows)) if rows else None,
            required_evidence_status="published",
        ),
        _operation_component_metric_row(
            component_id="C01_intake_operation",
            metric_family="sector_selection_effectiveness",
            metric_name="selected_sector_bucket_forward_return_rank",
            metric_scope="decision_time_visible_sector_buckets",
            availability_status="not_applicable",
            reason_codes=["target_selection_universe_metrics_not_supplied_for_trace_only_review"],
            point_in_time_input_fields=["timestamp", "target_ref", "sector_bucket_ref", "visible_universe_membership"],
            future_outcome_fields=["sector_forward_return_mean"],
            row_count=len(rows),
            eligible_row_count=0,
            selected_count=len(rows),
            selected_target_present_count=selected_present_count,
            required_evidence_status="not_required_for_trace_only_review",
        ),
        _operation_component_metric_row(
            component_id="C02_entry_operation",
            metric_family="target_selection_effectiveness",
            metric_name="selected_target_forward_return_rank_within_sector",
            metric_scope="decision_time_selected_sector_bucket",
            availability_status="not_applicable",
            reason_codes=["target_selection_universe_metrics_not_supplied_for_trace_only_review"],
            point_in_time_input_fields=["timestamp", "target_ref", "sector_bucket_ref", "visible_universe_membership"],
            future_outcome_fields=["forward_return"],
            row_count=len(rows),
            eligible_row_count=0,
            selected_count=len(rows),
            selected_target_present_count=selected_present_count,
            required_evidence_status="not_required_for_trace_only_review",
        ),
        _operation_component_metric_row(
            component_id="C02_entry_operation",
            metric_family="target_selection_effectiveness",
            metric_name="selected_target_model_rank_from_trace",
            metric_scope="point_in_time_model_candidate_trace",
            availability_status="computed",
            reason_codes=["trace_only_model_rank_review"],
            point_in_time_input_fields=[
                "replay_time_pointer",
                "target_ref",
                "model_rank_within_timestamp",
                "selected_by_replay",
            ],
            future_outcome_fields=[],
            row_count=len(trace_rows),
            eligible_row_count=len(scored_rows),
            selected_count=len(selected_trace_rows),
            universe_count_mean=_mean(timestamp_counts.values()),
            selected_target_present_count=len(selected_trace_rows),
            selected_forward_return_rank_mean=_mean(selected_rank_values),
            value=(len(selected_trace_rows) / len(scored_rows)) if scored_rows else None,
            required_evidence_status="published",
        ),
    ]


def _target_universe_sector_bucket(row: Mapping[str, Any]) -> str:
    value = str(
        row.get("sector_bucket_ref")
        or row.get("layer2_context_symbol")
        or row.get("tradingview_sector")
        or "UNMAPPED"
    ).strip()
    return value.upper() or "UNMAPPED"


def _target_universe_sector_return_means(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    values_by_sector: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = _target_universe_forward_return(row)
        if value is None:
            continue
        values_by_sector[_target_universe_sector_bucket(row)].append(float(value))
    return {
        sector: sum(values) / len(values)
        for sector, values in values_by_sector.items()
        if values
    }


def _entry_signal_metric_row(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    m04_open_rows = [row for row in rows if _m04_state(row) == "open_long/long"]
    return _operation_component_metric_row(
        component_id="C02_entry_operation",
        metric_family="entry_action_quality",
        metric_name="entry_signal_strength_and_outcome_alignment",
        metric_scope="replay_decision_rows",
        availability_status="computed" if rows else "data_gap",
        reason_codes=[] if rows else ["decision_rows_missing"],
        point_in_time_input_fields=["model_04_unified_decision.dominant_horizon_scores", "prediction_score"],
        future_outcome_fields=["outcome_label", "realized_return"],
        row_count=len(rows),
        eligible_row_count=len(m04_open_rows),
        selected_count=len(m04_open_rows),
        value=_spearman_for_key(rows, "prediction_score", "realized_return"),
        selected_forward_return_mean=_mean(_numeric_values(rows, "realized_return")),
        top_quartile_hit_rate=_round(
            sum(1 for row in rows if str(row.get("outcome_label")) == "1") / len(rows)
        )
        if rows
        else None,
    )


def _lifecycle_metric_rows(replay_receipt: Mapping[str, Any]) -> list[dict[str, Any]]:
    summary = _as_mapping(replay_receipt.get("portfolio_selection_summary"))
    if not summary:
        return [
            _operation_component_metric_row(
                component_id="C03_lifecycle_operation",
                metric_family="portfolio_lifecycle_state",
                metric_name="portfolio_lifecycle_state_evidence_coverage",
                metric_scope="replay_execution_receipt",
                availability_status="data_gap",
                reason_codes=["portfolio_lifecycle_summary_missing"],
                point_in_time_input_fields=["portfolio_state_after", "portfolio_selection_diagnostics"],
                future_outcome_fields=[],
                row_count=0,
                required_evidence_status="missing_required_lifecycle_evidence",
            )
        ]
    replacement_evaluated = int(_float(summary.get("portfolio_replacement_evaluated_count"), default=0.0))
    replacement_triggered = int(_float(summary.get("portfolio_replacement_triggered_count"), default=0.0))
    threshold_blocked = int(_float(summary.get("portfolio_replacement_blocked_by_threshold_count"), default=0.0))
    expression_blocked = int(_float(summary.get("portfolio_replacement_blocked_by_expression_count"), default=0.0))
    allocation_blocked = int(_float(summary.get("portfolio_replacement_blocked_by_allocation_count"), default=0.0))
    allocation_violations = int(_float(summary.get("portfolio_allocation_contract_violation_count"), default=0.0))
    continued_count = int(_float(summary.get("portfolio_existing_position_continued_count"), default=0.0))
    final_position_count = int(_float(summary.get("final_position_count"), default=0.0))
    candidate_count = int(_float(summary.get("candidate_count"), default=0.0))
    return [
        _operation_component_metric_row(
            component_id="C03_lifecycle_operation",
            metric_family="portfolio_lifecycle_state",
            metric_name="held_position_continuity_and_final_state",
            metric_scope="replay_portfolio_selection_summary",
            availability_status="computed",
            reason_codes=[],
            point_in_time_input_fields=[
                "portfolio_existing_position_continued_count",
                "final_position_count",
                "position_invalidation_policy",
            ],
            future_outcome_fields=[],
            row_count=candidate_count,
            eligible_row_count=continued_count + final_position_count,
            selected_count=final_position_count,
            selected_target_present_count=continued_count,
            value=(continued_count / candidate_count) if candidate_count else 0.0,
            required_evidence_status="published",
        ),
        _operation_component_metric_row(
            component_id="C03_lifecycle_operation",
            metric_family="portfolio_replacement_policy",
            metric_name="replacement_evaluation_trigger_block_balance",
            metric_scope="replay_portfolio_selection_summary",
            availability_status="computed",
            reason_codes=[
                f"threshold_blocked:{threshold_blocked}",
                f"expression_blocked:{expression_blocked}",
                f"allocation_blocked:{allocation_blocked}",
                f"allocation_violations:{allocation_violations}",
            ],
            point_in_time_input_fields=[
                "portfolio_replacement_evaluated_count",
                "portfolio_replacement_triggered_count",
                "portfolio_switch_minimum_rank_score_delta",
            ],
            future_outcome_fields=[],
            row_count=replacement_evaluated,
            eligible_row_count=replacement_evaluated,
            selected_count=replacement_triggered,
            selected_target_present_count=final_position_count,
            opportunity_cost_to_best_mean=float(threshold_blocked + expression_blocked + allocation_blocked),
            value=(replacement_triggered / replacement_evaluated) if replacement_evaluated else 0.0,
            required_evidence_status="published",
        ),
    ]


def _option_expression_metric_row(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    expression_rows = [
        row for row in rows if _m05_option_expression_diagnostics(row) or str(row.get("selected_option_contract_ref") or "")
    ]
    before_filter = [
        _float(_m05_option_expression_diagnostics(row).get("candidate_count_before_filter"))
        for row in expression_rows
        if _m05_option_expression_diagnostics(row).get("candidate_count_before_filter") not in {None, ""}
    ]
    eligible = [
        _float(_m05_option_expression_diagnostics(row).get("eligible_candidate_count"))
        for row in expression_rows
        if _m05_option_expression_diagnostics(row).get("eligible_candidate_count") not in {None, ""}
    ]
    selected_count = sum(1 for row in expression_rows if str(row.get("selected_option_contract_ref") or ""))
    path_available = sum(1 for row in expression_rows if _selected_option_path_status(row) == "available")
    return _operation_component_metric_row(
        component_id="C04_expression_review_operation",
        metric_family="option_expression_quality",
        metric_name="candidate_funnel_and_path_materialization",
        metric_scope="m05_option_expression_rows",
        availability_status="computed" if expression_rows else "data_gap",
        reason_codes=[] if expression_rows else ["option_expression_rows_missing"],
        point_in_time_input_fields=[
            "candidate_count_before_filter",
            "eligible_candidate_count",
            "selected_option_contract_ref",
            "option_contract_path_status",
        ],
        future_outcome_fields=["realized_return"],
        row_count=len(rows),
        eligible_row_count=len(expression_rows),
        selected_count=selected_count,
        universe_count_mean=_mean(before_filter),
        selected_target_present_count=path_available,
        selected_forward_return_mean=_mean(_numeric_values([row for row in rows if row.get("fill_status") == "simulated_filled"], "realized_return")),
        value=(path_available / selected_count) if selected_count else None,
        opportunity_cost_to_median_mean=_mean(eligible),
    )


def _order_intent_metric_row(
    rows: Sequence[Mapping[str, Any]],
    portfolio_capacity_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    baseline = next(
        (row for row in portfolio_capacity_rows if str(row.get("variant_name") or "") == "baseline_all_selected"),
        {},
    )
    best = max(
        portfolio_capacity_rows,
        key=lambda row: _float(row.get("selected_realized_return_total"), default=float("-inf")),
        default={},
    )
    selected_count = int(_float(baseline.get("selected_count"), default=0.0))
    return _operation_component_metric_row(
        component_id="C05_order_intent_operation",
        metric_family="order_intent_capacity_quality",
        metric_name="capacity_counterfactual_spread",
        metric_scope="fixed_replay_portfolio_capacity_variants",
        availability_status="computed" if portfolio_capacity_rows else "data_gap",
        reason_codes=[] if portfolio_capacity_rows else ["portfolio_capacity_counterfactual_missing"],
        point_in_time_input_fields=["planned_position_notional_usd", "prediction_score", "portfolio_budget"],
        future_outcome_fields=["realized_return"],
        row_count=len(rows),
        eligible_row_count=selected_count,
        selected_count=selected_count,
        value=_float(best.get("selected_realized_return_total")) - _float(baseline.get("selected_realized_return_total"))
        if best and baseline
        else None,
        selected_forward_return_mean=_float(baseline.get("selected_return_per_row")),
        opportunity_cost_to_best_mean=_float(best.get("selected_realized_return_total"))
        - _float(baseline.get("selected_realized_return_total"))
        if best and baseline
        else None,
    )


def _execution_gate_metric_row(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    selected_rows = [row for row in rows if str(row.get("selected_option_contract_ref") or "")]
    filled_count = sum(1 for row in selected_rows if row.get("fill_status") == "simulated_filled")
    path_missing_count = sum(1 for row in selected_rows if _selected_option_path_status(row) == "missing")
    return _operation_component_metric_row(
        component_id="C06_execution_gate_operation",
        metric_family="execution_gate_quality",
        metric_name="selected_contract_path_and_fill_coverage",
        metric_scope="selected_contract_rows",
        availability_status="computed" if selected_rows else "data_gap",
        reason_codes=[] if selected_rows else ["selected_contract_rows_missing"],
        point_in_time_input_fields=["selected_option_contract_ref", "option_contract_path_status", "fill_status"],
        future_outcome_fields=[],
        row_count=len(rows),
        eligible_row_count=len(selected_rows),
        selected_count=filled_count,
        selected_target_present_count=len(selected_rows) - path_missing_count,
        value=(filled_count / len(selected_rows)) if selected_rows else None,
    )


def _failure_review_metric_row(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    filled_rows = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    return _operation_component_metric_row(
        component_id="C07_failure_review_operation",
        metric_family="settled_failure_review_quality",
        metric_name="settled_score_outcome_surface",
        metric_scope="settled_replay_rows",
        availability_status="computed" if filled_rows else "data_gap",
        reason_codes=[] if filled_rows else ["settled_rows_missing"],
        point_in_time_input_fields=["prediction_score", "model_evidence_chain"],
        future_outcome_fields=["outcome_label", "realized_return"],
        row_count=len(rows),
        eligible_row_count=len(filled_rows),
        selected_count=len(filled_rows),
        selected_forward_return_mean=_mean(_numeric_values(filled_rows, "realized_return")),
        top_quartile_hit_rate=_round(
            sum(1 for row in filled_rows if str(row.get("outcome_label")) == "1") / len(filled_rows)
        )
        if filled_rows
        else None,
        value=_spearman_for_key(filled_rows, "prediction_score", "realized_return"),
    )


def _operation_component_metric_row(
    *,
    component_id: str,
    metric_family: str,
    metric_name: str,
    metric_scope: str,
    availability_status: str,
    reason_codes: Sequence[str],
    point_in_time_input_fields: Sequence[str],
    future_outcome_fields: Sequence[str],
    row_count: int = 0,
    eligible_row_count: int = 0,
    selected_count: int = 0,
    universe_count_mean: float | None = None,
    selected_target_present_count: int = 0,
    selected_forward_return_mean: float | None = None,
    selected_forward_return_rank_mean: float | None = None,
    selected_forward_return_percentile_mean: float | None = None,
    top_quartile_hit_rate: float | None = None,
    opportunity_cost_to_best_mean: float | None = None,
    opportunity_cost_to_median_mean: float | None = None,
    value: float | None = None,
    required_evidence_status: str | None = None,
) -> dict[str, Any]:
    component = OPERATION_COMPONENT_BY_ID.get(component_id) or {}
    method = OPERATION_COMPONENT_ANALYSIS_METHODS.get(component_id, {})
    return {
        "component_index": int(component.get("component_index") or 0),
        "operation_component_id": component_id,
        "runtime_component_ref": str(component.get("runtime_component_ref") or ""),
        "operation_component_label": str(component.get("operation_component_label") or ""),
        "metric_family": metric_family,
        "metric_name": metric_name,
        "metric_scope": metric_scope,
        "analysis_method": method.get("analysis_method", ""),
        "evidence_role": method.get("evidence_role", ""),
        "label_role": method.get("label_role", ""),
        "required_evidence_status": required_evidence_status
        or ("published" if availability_status == "computed" else "missing_or_incomplete"),
        "availability_status": availability_status,
        "reason_codes": ";".join(reason_codes),
        "point_in_time_input_fields": ";".join(point_in_time_input_fields),
        "future_outcome_fields": ";".join(future_outcome_fields),
        "row_count": row_count,
        "eligible_row_count": eligible_row_count,
        "selected_count": selected_count,
        "universe_count_mean": _round(universe_count_mean),
        "selected_target_present_count": selected_target_present_count,
        "selected_forward_return_mean": _round(selected_forward_return_mean),
        "selected_forward_return_rank_mean": _round(selected_forward_return_rank_mean),
        "selected_forward_return_percentile_mean": _round(selected_forward_return_percentile_mean),
        "top_quartile_hit_rate": _round(top_quartile_hit_rate),
        "opportunity_cost_to_best_mean": _round(opportunity_cost_to_best_mean),
        "opportunity_cost_to_median_mean": _round(opportunity_cost_to_median_mean),
        "value": _round(value),
        "diagnostic_only": True,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _target_universe_forward_return(row: Mapping[str, Any]) -> float | None:
    for key in (
        "forward_return",
        "future_return",
        "horizon_forward_return",
        "replay_forward_return",
        "replay_opportunity_return",
        "candidate_opportunity_return",
        "realized_return",
    ):
        if row.get(key) not in {None, ""}:
            return _float(row.get(key))
    return None


def _operation_component_metric_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "contract_type": "model_group_operation_component_metric_report",
        "operation_component_metrics_ref": "operation_component_metrics.csv",
        "summary": {
            "metric_count": len(rows),
            "availability_status_counts": dict(Counter(str(row.get("availability_status") or "") for row in rows)),
            "metric_family_counts": dict(Counter(str(row.get("metric_family") or "") for row in rows)),
            "analysis_method_counts": dict(Counter(str(row.get("analysis_method") or "") for row in rows)),
            "required_evidence_status_counts": dict(
                Counter(str(row.get("required_evidence_status") or "") for row in rows)
            ),
            "components_with_metric_data_gaps": sorted(
                {
                    str(row.get("operation_component_id") or "")
                    for row in rows
                    if _metric_status_has_data_gap(row)
                }
            ),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
            "retraining_performed": False,
        },
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
        "interpretation_notes": [
            "Future outcome fields are ex-post diagnostic labels only.",
            "Target-selection ranks require a fixed point-in-time visible universe input.",
            "Metric data gaps are evidence gaps, not neutral component performance.",
            "Components share the operation metric envelope, but each component owns a distinct analysis_method and evidence_role.",
        ],
    }


def _metric_status_has_data_gap(row: Mapping[str, Any]) -> bool:
    return str(row.get("availability_status") or "") in {"data_gap", "partial"}


def _operation_component_metric_effectiveness_review(
    metric_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    flags: list[str] = []
    computed_rows = [
        row
        for row in metric_rows
        if str(row.get("availability_status") or "") == "computed"
    ]
    for row in computed_rows:
        metric_name = str(row.get("metric_name") or "")
        percentile = _float(row.get("selected_forward_return_percentile_mean"))
        top_quartile = _float(row.get("top_quartile_hit_rate"))
        value = _float(row.get("value"))
        if metric_name == "selected_sector_bucket_forward_return_rank":
            if top_quartile is not None and top_quartile < 0.25:
                flags.append("selected_sector_bucket_top_quartile_hit_below_random_baseline")
            if percentile is not None and percentile < 0.5:
                flags.append("selected_sector_bucket_mean_percentile_below_median")
        elif metric_name == "selected_target_forward_return_rank_within_sector":
            if top_quartile is not None and top_quartile < 0.25:
                flags.append("selected_target_within_sector_top_quartile_hit_below_random_baseline")
            if percentile is not None and percentile < 0.5:
                flags.append("selected_target_within_sector_mean_percentile_below_median")
        elif metric_name == "entry_signal_strength_and_outcome_alignment":
            if value is not None and value < 0:
                flags.append("entry_signal_return_alignment_negative")
        elif metric_name == "model_ranked_candidate_selection_funnel":
            rank_mean = _float(row.get("selected_forward_return_rank_mean"))
            if rank_mean is not None and rank_mean > 25:
                flags.append("selected_candidates_mean_model_rank_outside_top_25")
            if value is not None and value < 0.01:
                flags.append("low_selected_share_of_model_option_signal_candidates")
        elif metric_name == "selected_target_model_rank_from_trace":
            rank_mean = _float(row.get("selected_forward_return_rank_mean"))
            if rank_mean is not None and rank_mean > 25:
                flags.append("selected_targets_mean_model_rank_outside_top_25")
        elif metric_name == "replacement_evaluation_trigger_block_balance":
            blocked = _float(row.get("opportunity_cost_to_best_mean"))
            evaluated = _float(row.get("row_count"))
            if blocked is not None and evaluated is not None and evaluated > 0 and blocked / evaluated > 0.5:
                flags.append("lifecycle_replacements_mostly_blocked")
        elif metric_name == "held_position_continuity_and_final_state":
            if value is not None and value == 0:
                flags.append("no_held_position_continuity_observed")
    if flags:
        return {"status": "weak_effectiveness_observed", "flags": sorted(set(flags))}
    if computed_rows:
        return {"status": "effectiveness_metrics_reviewed", "flags": []}
    if any(_metric_status_has_data_gap(row) for row in metric_rows):
        return {"status": "effectiveness_metrics_incomplete", "flags": ["component_specific_metric_data_gap"]}
    return {"status": "effectiveness_metrics_not_available", "flags": []}


def _operation_component_review_packet(
    *,
    operation_component_flow_rows: Sequence[Mapping[str, Any]],
    operation_review_projection_rows: Sequence[Mapping[str, Any]],
    operation_component_metric_rows: Sequence[Mapping[str, Any]],
    component_model_mapping_rows: Sequence[Mapping[str, Any]],
    m05_unfilled_summary: Mapping[str, Any],
    sector_opportunity_packet_available: bool,
    model_candidate_selection_trace_available: bool,
    replay_receipt_available: bool,
    output_dir: Path,
) -> dict[str, Any]:
    mapping_by_surface = {
        str(row.get("component_surface") or ""): row
        for row in component_model_mapping_rows
    }
    projection_rows_by_component: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in operation_review_projection_rows:
        projection_rows_by_component[str(row.get("operation_component_id") or "")].append(row)
    metric_rows_by_component: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in operation_component_metric_rows:
        metric_rows_by_component[str(row.get("operation_component_id") or "")].append(row)
    component_rows: list[dict[str, Any]] = []
    for flow_row in operation_component_flow_rows:
        component_id = str(flow_row.get("operation_component_id") or "")
        component_metric_rows = metric_rows_by_component.get(component_id, [])
        internal_refs = _operation_component_internal_review_refs(
            component_id=component_id,
            m05_unfilled_available=m05_unfilled_summary.get("source_status") == "available",
            sector_opportunity_packet_available=sector_opportunity_packet_available,
            model_candidate_selection_trace_available=model_candidate_selection_trace_available,
        )
        if component_metric_rows and "operation_component_metrics.csv" not in internal_refs:
            internal_refs.append("operation_component_metrics.csv")
        metric_effectiveness = _operation_component_metric_effectiveness_review(component_metric_rows)
        missing_outputs = _operation_component_missing_review_outputs(
            component_id=component_id,
            mapping_by_surface=mapping_by_surface,
            metric_rows=component_metric_rows,
            m05_unfilled_available=m05_unfilled_summary.get("source_status") == "available",
            replay_receipt_available=replay_receipt_available,
            settled_metric_eligible_count=int(flow_row.get("settled_metric_eligible_count") or 0),
        )
        survival_verdict = str(flow_row.get("stage_verdict") or "")
        can_assign_fault = _can_assign_operation_fault(
            component_id=component_id,
            survival_verdict=survival_verdict,
            missing_review_outputs=missing_outputs,
            applicability_status=str(flow_row.get("applicability_status") or ""),
            first_limiting_projections=str(flow_row.get("first_limiting_projections") or "").split(";")
            if str(flow_row.get("first_limiting_projections") or "")
            else [],
        )
        component_rows.append(
            {
                "component_index": int(flow_row.get("component_index") or 0),
                "operation_component_id": component_id,
                "runtime_component_ref": str(flow_row.get("runtime_component_ref") or ""),
                "operation_component_label": str(flow_row.get("operation_component_label") or ""),
                "operation_role": str(flow_row.get("operation_role") or ""),
                "applicability_status": str(flow_row.get("applicability_status") or ""),
                "input_count": int(flow_row.get("input_count") or 0),
                "output_count": int(flow_row.get("output_count") or 0),
                "dropped_or_blocked_count": int(flow_row.get("dropped_or_blocked_count") or 0),
                "settled_metric_eligible_count": int(flow_row.get("settled_metric_eligible_count") or 0),
                "survival_verdict": survival_verdict,
                "survival_verdict_basis": str(flow_row.get("verdict_basis") or ""),
                "review_projections": ";".join(_operation_component_projection_refs(component_id)),
                "internal_review_refs": ";".join(internal_refs),
                "missing_review_outputs": ";".join(missing_outputs),
                "metric_effectiveness_status": metric_effectiveness["status"],
                "metric_effectiveness_flags": ";".join(metric_effectiveness["flags"]),
                "first_limiting_projection_count": int(flow_row.get("first_limiting_projection_count") or 0),
                "can_assign_operation_fault": can_assign_fault,
                "interpretation_status": _operation_component_interpretation_status(
                    survival_verdict=survival_verdict,
                    missing_review_outputs=missing_outputs,
                    applicability_status=str(flow_row.get("applicability_status") or ""),
                    can_assign_operation_fault=can_assign_fault,
                    metric_effectiveness_status=str(metric_effectiveness["status"]),
                ),
                "threshold_selection_performed": False,
                "retraining_performed": False,
                "fixed_input_only": True,
            }
        )
    first_problem_row = next(
        (
            row
            for row in component_rows
            if str(row.get("survival_verdict") or "") in {
                "first_observed_deterioration",
                "amplifies_prior_damage",
                "dominant_censoring_point",
            }
        ),
        None,
    )
    packet = {
        "contract_type": "model_group_operation_component_review_packet",
        "operation_component_review_packet_csv_ref": str(output_dir / "operation_component_review_packet.csv"),
        "operation_review_projection_matrix_ref": str(output_dir / "operation_review_projection_matrix.csv"),
        "operation_component_flow_ref": str(output_dir / "operation_component_flow.csv"),
        "operation_component_metrics_ref": str(output_dir / "operation_component_metrics.csv"),
        "component_count": len(component_rows),
        "summary": {
            "component_count": len(component_rows),
            "first_problem_operation_component": str((first_problem_row or {}).get("operation_component_id") or ""),
            "first_problem_runtime_component_ref": str((first_problem_row or {}).get("runtime_component_ref") or ""),
            "first_problem_verdict": str((first_problem_row or {}).get("survival_verdict") or ""),
            "survival_verdict_counts": dict(Counter(str(row["survival_verdict"]) for row in component_rows)),
            "interpretation_status_counts": dict(Counter(str(row["interpretation_status"]) for row in component_rows)),
            "first_limiting_projection_counts": dict(
                Counter(str(row.get("review_projection") or "") for row in operation_review_projection_rows)
            ),
            "component_metric_availability_counts": dict(
                Counter(str(row.get("availability_status") or "") for row in operation_component_metric_rows)
            ),
            "metric_effectiveness_status_counts": dict(
                Counter(str(row.get("metric_effectiveness_status") or "") for row in component_rows)
            ),
            "components_with_metric_data_gaps": sorted(
                {
                    str(row.get("operation_component_id") or "")
                    for row in operation_component_metric_rows
                    if _metric_status_has_data_gap(row)
                }
            ),
            "components_with_weak_effectiveness_metrics": [
                str(row["operation_component_id"])
                for row in component_rows
                if str(row.get("metric_effectiveness_status") or "") == "weak_effectiveness_observed"
            ],
            "components_with_missing_review_outputs": [
                str(row["operation_component_id"])
                for row in component_rows
                if str(row.get("missing_review_outputs") or "")
            ],
            "operation_fault_assignable_components": [
                str(row["operation_component_id"])
                for row in component_rows
                if row.get("can_assign_operation_fault") is True
            ],
            "review_readiness_status": _operation_component_review_readiness_status(component_rows),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
            "retraining_performed": False,
        },
        "component_rows": component_rows,
        "projection_rows": list(operation_review_projection_rows),
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
        "interpretation_notes": [
            "Operation components are live/replay action units; review projections are diagnostic lenses under those units.",
            "Model assets are attributed through projections and explicit refs, not by treating models as components.",
            "Rows stopped by materialization or execution are not counted in settled model win/loss metrics.",
            "A missing review output is an attribution gap and must not be read as component success.",
        ],
    }
    return {"component_rows": component_rows, "packet": packet}


def _operation_component_projection_refs(component_id: str) -> list[str]:
    return [
        str(value["review_projection"])
        for value in OPERATION_REVIEW_PROJECTION_BY_SURFACE.values()
        if value.get("operation_component_id") == component_id
    ]


def _operation_component_internal_review_refs(
    *,
    component_id: str,
    m05_unfilled_available: bool,
    sector_opportunity_packet_available: bool,
    model_candidate_selection_trace_available: bool,
) -> list[str]:
    refs_by_component = {
        "C01_intake_operation": [
            "operation_review_projection_matrix.csv",
            "decision_surface_component_matrix.csv",
        ],
        "C02_entry_operation": [
            "operation_review_projection_matrix.csv",
            "m04_component_diagnostics.csv",
            "m04_variant_counterfactual.csv",
            "parameter_replay_review.csv",
            "suspect_parameter_counterfactual.csv",
        ],
        "C03_lifecycle_operation": [
            "replay_execution_receipt.json",
            "portfolio_selection_summary",
            "portfolio_replay_policy",
        ],
        "C04_expression_review_operation": [
            "operation_review_projection_matrix.csv",
            "m05_selection_mechanics.csv",
            "m05_dte_policy_sensitivity.csv",
            "m05_hard_filter_overlap.csv",
            "row_counterfactual_attribution.csv",
            "decision_surface_component_matrix.csv",
        ],
        "C05_order_intent_operation": [
            "portfolio_capacity_counterfactual.csv",
            "portfolio_capacity_counterfactual_report.json",
        ],
        "C06_execution_gate_operation": [
            "operation_review_projection_matrix.csv",
            "decision_surface_component_matrix.csv",
            "replay_execution_receipt.json",
        ],
        "C07_failure_review_operation": [
            "operation_component_flow.csv",
            "filled_score_bins.csv",
            "tail_loss_rows.csv",
            "top_gain_rows.csv",
            "high_score_filled_tail_loss_attribution_packet.json",
            "parameter_replay_review.csv",
        ],
    }
    refs = list(refs_by_component.get(component_id, []))
    if component_id == "C01_intake_operation" and sector_opportunity_packet_available:
        refs.append("sector_opportunity_packet.csv")
        refs.append("sector_opportunity_packet.json")
    if component_id in {"C01_intake_operation", "C02_entry_operation"} and model_candidate_selection_trace_available:
        refs.append("model_candidate_selection_trace.jsonl")
        refs.append("model_candidate_selection_summary.csv")
        refs.append("model_candidate_selection_summary_report.json")
    if component_id == "C04_expression_review_operation" and m05_unfilled_available:
        refs.append("m05_unfilled_filter_reasons.csv")
    return refs


def _operation_component_missing_review_outputs(
    *,
    component_id: str,
    mapping_by_surface: Mapping[str, Mapping[str, Any]],
    metric_rows: Sequence[Mapping[str, Any]],
    m05_unfilled_available: bool,
    replay_receipt_available: bool,
    settled_metric_eligible_count: int,
) -> list[str]:
    missing: list[str] = []
    if any(_metric_status_has_data_gap(row) for row in metric_rows):
        missing.append("component_specific_metric_data_gap")
    if component_id == "C01_intake_operation":
        for surface in ("C01_background_context_surface", "C02_target_state_surface"):
            mapping_row = mapping_by_surface.get(surface) or {}
            if int(mapping_row.get("diagnostic_surface_count") or 0) <= 0:
                missing.append(f"{surface}_internal_score_or_candidate_delta")
    if component_id == "C02_entry_operation":
        event_mapping = mapping_by_surface.get("C03_event_state_surface") or {}
        entry_mapping = mapping_by_surface.get("C04_underlying_decision_surface") or {}
        if int(event_mapping.get("diagnostic_surface_count") or 0) <= 0:
            missing.append("event_state_component_internal_score_or_candidate_delta")
        if int(entry_mapping.get("diagnostic_surface_count") or 0) <= 0:
            missing.append("underlying_entry_decision_score_diagnostics")
    if component_id == "C03_lifecycle_operation":
        if any(str(row.get("availability_status") or "") == "data_gap" for row in metric_rows):
            missing.append("portfolio_lifecycle_state_evidence")
    if component_id == "C04_expression_review_operation":
        m05_mapping = mapping_by_surface.get("C05_option_expression_surface") or {}
        if int(m05_mapping.get("explicit_ref_count") or 0) <= 0:
            missing.append("explicit_model_05_option_expression_ref")
        if int(m05_mapping.get("diagnostic_surface_count") or 0) <= 0:
            missing.append("model_05_alpha_or_selection_score_diagnostics")
        if int(m05_mapping.get("diagnostic_surface_count") or 0) <= 0 and not m05_unfilled_available:
            missing.append("m05_candidate_set_and_selection_delta")
    if component_id == "C06_execution_gate_operation" and not replay_receipt_available:
        missing.append("replay_execution_receipt")
    if component_id == "C07_failure_review_operation":
        if settled_metric_eligible_count <= 0:
            missing.append("settled_outcome_rows")
    return missing


def _can_assign_operation_fault(
    *,
    component_id: str,
    survival_verdict: str,
    missing_review_outputs: Sequence[str],
    applicability_status: str,
    first_limiting_projections: Sequence[str],
) -> bool:
    if component_id == "C07_failure_review_operation" and set(first_limiting_projections) <= {
        "settled_prediction_quality"
    }:
        return False
    return (
        applicability_status != "missing_lifecycle_state_evidence"
        and survival_verdict in {
            "first_observed_deterioration",
            "amplifies_prior_damage",
            "dominant_censoring_point",
        }
        and not missing_review_outputs
    )


def _operation_component_interpretation_status(
    *,
    survival_verdict: str,
    missing_review_outputs: Sequence[str],
    applicability_status: str,
    can_assign_operation_fault: bool,
    metric_effectiveness_status: str,
) -> str:
    if applicability_status == "missing_lifecycle_state_evidence":
        return "operation_review_incomplete_missing_lifecycle_state_evidence"
    if survival_verdict in {
        "first_observed_deterioration",
        "amplifies_prior_damage",
        "dominant_censoring_point",
    }:
        if not missing_review_outputs and not can_assign_operation_fault:
            return "problem_observed_at_failure_review_not_causal_operation_fault"
        if can_assign_operation_fault:
            return "problem_operation_with_complete_component_review"
        return "problem_operation_with_incomplete_component_review"
    if missing_review_outputs:
        return "operation_review_incomplete_no_problem_assigned"
    if metric_effectiveness_status == "weak_effectiveness_observed":
        return "weak_component_effectiveness_observed"
    if survival_verdict in {"insufficient_evidence", "neutral_or_unmeasured", "unmeasured"}:
        return "operation_unmeasured_or_sample_limited"
    return "reviewable_no_problem_observed"


def _operation_component_review_readiness_status(component_rows: Sequence[Mapping[str, Any]]) -> str:
    if any(
        str(row.get("interpretation_status") or "") == "problem_operation_with_incomplete_component_review"
        for row in component_rows
    ):
        return "incomplete_review_outputs_for_problem_operation"
    if any(str(row.get("missing_review_outputs") or "") for row in component_rows):
        return "component_internal_review_outputs_incomplete"
    return "operation_component_review_packet_complete"


def _component_internal_review_refs(*, component_surface: str, m05_unfilled_available: bool) -> list[str]:
    refs_by_surface = {
        "C01_background_context_surface": ["decision_surface_component_matrix.csv"],
        "C02_target_state_surface": ["decision_surface_component_matrix.csv"],
        "C03_event_state_surface": ["decision_surface_component_matrix.csv"],
        "C04_underlying_decision_surface": [
            "m04_component_diagnostics.csv",
            "m04_variant_counterfactual.csv",
            "parameter_replay_review.csv",
            "suspect_parameter_counterfactual.csv",
        ],
        "C05_option_expression_surface": [
            "m05_selection_mechanics.csv",
            "m05_dte_policy_sensitivity.csv",
            "m05_hard_filter_overlap.csv",
            "row_counterfactual_attribution.csv",
        ],
        "C06_selected_option_path_materialization": [
            "decision_surface_component_matrix.csv",
            "replay_execution_receipt.json",
        ],
        "C07_portfolio_execution_surface": [
            "decision_surface_component_matrix.csv",
            "portfolio_capacity_counterfactual.csv",
            "portfolio_capacity_counterfactual_report.json",
            "row_counterfactual_attribution.csv",
        ],
        "C08_settled_prediction_quality_surface": [
            "component_survival_quality_flow.csv",
            "filled_score_bins.csv",
            "tail_loss_rows.csv",
            "top_gain_rows.csv",
            "high_score_filled_tail_loss_attribution_packet.json",
            "parameter_replay_review.csv",
        ],
    }
    refs = list(refs_by_surface.get(component_surface, []))
    if component_surface == "C05_option_expression_surface" and m05_unfilled_available:
        refs.append("m05_unfilled_filter_reasons.csv")
    return refs


def _component_missing_review_outputs(
    *,
    component_surface: str,
    mapping_row: Mapping[str, Any],
    m05_unfilled_available: bool,
) -> list[str]:
    missing: list[str] = []
    mapping_status = str(mapping_row.get("mapping_status") or "")
    if component_surface in {
        "C01_background_context_surface",
        "C02_target_state_surface",
        "C03_event_state_surface",
    } and int(mapping_row.get("diagnostic_surface_count") or 0) <= 0:
        missing.append("component_internal_score_or_candidate_delta")
    if component_surface == "C05_option_expression_surface":
        if int(mapping_row.get("explicit_ref_count") or 0) <= 0:
            missing.append("explicit_model_05_option_expression_ref")
        if int(mapping_row.get("diagnostic_surface_count") or 0) <= 0:
            missing.append("model_05_alpha_or_selection_score_diagnostics")
        if int(mapping_row.get("diagnostic_surface_count") or 0) <= 0 and not m05_unfilled_available:
            missing.append("m05_candidate_set_and_selection_delta")
    if component_surface == "C07_portfolio_execution_surface" and int(mapping_row.get("decision_surface_count") or 0) <= 0:
        missing.append("portfolio_capacity_and_sizing_delta")
    return missing


def _attribution_coverage_status(mapping_row: Mapping[str, Any]) -> str:
    mapping_status = str(mapping_row.get("mapping_status") or "")
    if mapping_status == "explicit_ref_and_diagnostic_surface":
        return "explicit_asset_and_internal_diagnostics"
    if mapping_status == "explicit_ref_only":
        return "explicit_asset_without_internal_diagnostics"
    if mapping_status == "diagnostic_or_decision_surface_without_explicit_ref":
        return "diagnostic_without_explicit_asset_ref"
    if mapping_status == "evidence_chain_only":
        return "evidence_chain_only_insufficient_attribution"
    if mapping_status == "non_model_surface":
        return "non_model_surface"
    return "missing_attribution"


def _point_in_time_evidence_status(mapping_row: Mapping[str, Any], internal_refs: Sequence[str]) -> str:
    decision_surface_count = int(mapping_row.get("decision_surface_count") or 0)
    if decision_surface_count and internal_refs:
        return "point_in_time_evidence_and_review_refs_present"
    if decision_surface_count:
        return "point_in_time_evidence_present_review_refs_missing"
    if internal_refs:
        return "review_refs_present_decision_surface_missing"
    return "point_in_time_evidence_missing"


def _component_changed_or_transformed_count(component_surface: str, input_count: int) -> int:
    if component_surface in {
        "C04_underlying_decision_surface",
        "C05_option_expression_surface",
        "C06_selected_option_path_materialization",
        "C07_portfolio_execution_surface",
    }:
        return input_count
    return 0


def _model_attribution_ready(attribution_coverage_status: str, missing_review_outputs: Sequence[str]) -> bool:
    return attribution_coverage_status == "explicit_asset_and_internal_diagnostics" and not missing_review_outputs


def _can_assign_model_blame(
    *,
    survival_verdict: str,
    attribution_coverage_status: str,
    missing_review_outputs: Sequence[str],
) -> bool:
    return survival_verdict in {
        "first_observed_deterioration",
        "amplifies_prior_damage",
        "dominant_censoring_point",
    } and _model_attribution_ready(attribution_coverage_status, missing_review_outputs)


def _component_interpretation_status(
    *,
    survival_verdict: str,
    attribution_coverage_status: str,
    missing_review_outputs: Sequence[str],
) -> str:
    if survival_verdict in {"first_observed_deterioration", "amplifies_prior_damage", "dominant_censoring_point"}:
        if _model_attribution_ready(attribution_coverage_status, missing_review_outputs):
            return "problem_surface_with_assignable_model_asset"
        if attribution_coverage_status == "non_model_surface":
            return "problem_surface_without_direct_model_asset"
        return "problem_surface_with_insufficient_attribution"
    if missing_review_outputs:
        return "survival_neutral_but_review_incomplete"
    if survival_verdict == "unmeasured":
        return "survival_unmeasured"
    return "reviewable_no_problem_observed"


def _component_review_readiness_status(component_rows: Sequence[Mapping[str, Any]]) -> str:
    if any(str(row.get("interpretation_status") or "").endswith("insufficient_attribution") for row in component_rows):
        return "insufficient_attribution_for_some_problem_surfaces"
    if any(str(row.get("missing_review_outputs") or "") for row in component_rows):
        return "component_internal_review_outputs_incomplete"
    return "component_review_packet_complete"


def _component_flow_verdict(
    *,
    component_surface: str,
    entered_count: int,
    blocked_count: int,
    censored_count: int,
    settled_count: int,
    post_bad_rate: float | None,
    mean_realized_return: float | None,
    tail_loss_count: int,
    previous_bad_rate: float | None,
) -> tuple[str, str]:
    if entered_count <= 0:
        return "neutral_or_unmeasured", "component_not_reached"
    if censored_count and censored_count / entered_count >= 0.5:
        return "dominant_censoring_point", "majority_of_entered_rows_missing_settled_path"
    if blocked_count:
        return "first_observed_deterioration", "rows_first_limited_at_component"
    if settled_count < 5 or post_bad_rate is None:
        return "insufficient_evidence", "too_few_settled_rows_for_quality_flow"
    if component_surface == "C08_settled_prediction_quality_surface":
        if post_bad_rate > 0.5:
            return "first_observed_deterioration", "settled_survivor_cohort_bad_rate_above_half"
        if mean_realized_return is not None and mean_realized_return < 0:
            return "first_observed_deterioration", "settled_survivor_cohort_negative_mean_return"
        if tail_loss_count:
            return "first_observed_deterioration", "settled_survivor_tail_loss_present"
        return "neutral_measured", "settled_survivor_cohort_not_majority_bad"
    if previous_bad_rate is None:
        return "unmeasured", "no_prior_observable_bad_rate"
    if post_bad_rate - previous_bad_rate >= 0.15:
        return "amplifies_prior_damage", "post_component_bad_rate_increased"
    if previous_bad_rate - post_bad_rate >= 0.15:
        return "pulls_back_prior_damage", "post_component_bad_rate_decreased"
    return "neutral_measured", "bad_rate_change_below_materiality"


def _settled_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [row for row in rows if row.get("settled_metric_eligible") is True]


def _bad_outcome_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if str(row.get("outcome_label")) == "0" or _float(row.get("realized_return")) < 0)


def _numeric_values(rows: Sequence[Mapping[str, Any]], key: str) -> list[float]:
    return [_float(row.get(key)) for row in rows if row.get(key) not in {None, ""}]


def _spearman_for_key(rows: Sequence[Mapping[str, Any]], left_key: str, right_key: str) -> float | None:
    pairs = [
        (_float(row.get(left_key)), _float(row.get(right_key)))
        for row in rows
        if row.get(left_key) not in {None, ""} and row.get(right_key) not in {None, ""}
    ]
    if not pairs:
        return None
    return _spearman([left for left, _right in pairs], [right for _left, right in pairs])


def _m05_unfilled_summary(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"source_status": "missing", "row_count": 0, "filter_reason_rows": []}
    rows = _load_csv_rows(path)
    filter_counts: Counter[str] = Counter()
    plan_counts: Counter[str] = Counter()
    labels: Counter[str] = Counter()
    for row in rows:
        labels[str(row.get("outcome_label") or "")] += 1
        for reason in str(row.get("plan_reason_codes") or "").split(";"):
            if reason:
                plan_counts[reason] += 1
        try:
            parsed = ast.literal_eval(str(row.get("fail_reason_counts") or "{}"))
        except (SyntaxError, ValueError):
            parsed = {}
        if isinstance(parsed, Mapping):
            for reason, count in parsed.items():
                filter_counts[str(reason)] += int(count)
    filter_reason_rows = [
        {"reason_code": reason_code, "count": count}
        for reason_code, count in filter_counts.most_common()
    ]
    return {
        "source_status": "available",
        "row_count": len(rows),
        "label_counts": dict(labels),
        "plan_reason_counts": dict(plan_counts),
        "filter_reason_counts": dict(filter_counts),
        "filter_reason_rows": filter_reason_rows,
    }


def _load_csv_rows(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _expression_rows_by_timestamp(rows: Sequence[Mapping[str, str]]) -> dict[str, list[Mapping[str, str]]]:
    by_timestamp: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        timestamp = str(row.get("timestamp") or "")
        if timestamp:
            by_timestamp[timestamp].append(row)
    return by_timestamp


def _counterfactual_rows(
    rows: Sequence[Mapping[str, Any]],
    expression_rows_by_timestamp: Mapping[str, Sequence[Mapping[str, str]]],
    replay_timestamp_counts: Mapping[str, int],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        expression_row, expression_join_status = _expression_row_for_replay_row(
            row=row,
            expression_rows_by_timestamp=expression_rows_by_timestamp,
            replay_timestamp_counts=replay_timestamp_counts,
        )
        m04 = _m04_diagnostics(row)
        scores = m04.get("dominant_horizon_scores") or {}
        expression_state = _expression_state(row)
        intended_trade = _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
        candidate_count_before_filter = _int_from_expression(expression_row, "candidate_count_before_filter")
        candidate_count_after_filter = _int_from_expression(expression_row, "candidate_count_after_filter")
        eligible_candidate_count = _int_from_expression(expression_row, "eligible_candidate_count")
        expression_selected_contract = str((expression_row or {}).get("selected_contract_ref") or "")
        option_feasibility_state = _option_feasibility_state(
            row=row,
            expression_row=expression_row,
            expression_join_status=expression_join_status,
            candidate_count_before_filter=candidate_count_before_filter,
            candidate_count_after_filter=candidate_count_after_filter,
            eligible_candidate_count=eligible_candidate_count,
        )
        model_execution_mismatch = _model_execution_mismatch(
            intended_trade=intended_trade,
            row=row,
            candidate_count_after_filter=candidate_count_after_filter,
            eligible_candidate_count=eligible_candidate_count,
            expression_selected_contract=expression_selected_contract,
        )
        fail_reason_counts = _fail_reason_counts(expression_row)
        bucket, reason_codes = _counterfactual_bucket(
            row=row,
            intended_trade=intended_trade,
            expression_row=expression_row,
            option_feasibility_state=option_feasibility_state,
            model_execution_mismatch=model_execution_mismatch,
        )
        output.append(
            {
                "timestamp": str(row.get("timestamp") or ""),
                "decision_id": str(row.get("decision_id") or ""),
                "decision_status": str(row.get("decision_status") or ""),
                "fill_status": str(row.get("fill_status") or ""),
                "intended_model_trade": intended_trade,
                "execution_expression_state": expression_state,
                "expression_join_status": expression_join_status,
                "model_execution_mismatch": model_execution_mismatch,
                "option_feasibility_state": option_feasibility_state,
                "candidate_count_before_filter": candidate_count_before_filter,
                "candidate_count_after_filter": candidate_count_after_filter,
                "eligible_candidate_count": eligible_candidate_count,
                "top_contract_fit_score": _round(_float((expression_row or {}).get("top_contract_fit_score"))),
                "primary_filter_reason": _primary_filter_reason(fail_reason_counts),
                "filter_reason_counts": json.dumps(fail_reason_counts, sort_keys=True),
                "prediction_score": _round(_float(row.get("prediction_score"))),
                "trade_intensity_score": _round(_float(scores.get("trade_intensity_score"))),
                "outcome_label": _text(row.get("outcome_label")),
                "realized_return": _round(_float(row.get("realized_return"))),
                "underlying_return": _round(_float((expression_row or {}).get("underlying_return"))),
                "selected_option_contract_ref": str(row.get("selected_option_contract_ref") or ""),
                "expression_selected_contract_ref": expression_selected_contract,
                "row_counterfactual_bucket": bucket,
                "bucket_reason_codes": ";".join(reason_codes),
            }
        )
    return output


def _expression_row_for_replay_row(
    *,
    row: Mapping[str, Any],
    expression_rows_by_timestamp: Mapping[str, Sequence[Mapping[str, str]]],
    replay_timestamp_counts: Mapping[str, int],
) -> tuple[Mapping[str, str] | None, str]:
    timestamp = str(row.get("timestamp") or "")
    if not timestamp:
        return None, "missing_timestamp"
    if replay_timestamp_counts.get(timestamp, 0) != 1:
        return None, "replay_timestamp_ambiguous"
    expression_rows = tuple(expression_rows_by_timestamp.get(timestamp) or ())
    if not expression_rows:
        return None, "missing"
    if len(expression_rows) != 1:
        return None, "m05_expression_timestamp_ambiguous"
    return expression_rows[0], "matched"


def _int_from_expression(row: Mapping[str, str] | None, key: str) -> int | None:
    if row is None or row.get(key) in (None, ""):
        return None
    try:
        return int(str(row.get(key)))
    except ValueError:
        return None


def _option_feasibility_state(
    *,
    row: Mapping[str, Any],
    expression_row: Mapping[str, str] | None,
    expression_join_status: str,
    candidate_count_before_filter: int | None,
    candidate_count_after_filter: int | None,
    eligible_candidate_count: int | None,
) -> str:
    if row.get("fill_status") == "simulated_filled":
        return "contract_selected"
    if expression_row is None:
        if expression_join_status.endswith("_ambiguous"):
            return "expression_evidence_ambiguous"
        return "expression_evidence_missing" if _expression_state(row) == "expression_unfilled" else "not_applicable"
    if candidate_count_after_filter and candidate_count_after_filter > 0:
        return "contract_available_after_filter"
    if eligible_candidate_count and eligible_candidate_count > 0:
        return "eligible_contract_available"
    if candidate_count_before_filter is None:
        return "unknown"
    if candidate_count_before_filter == 0:
        return "no_point_in_time_candidates"
    if _expression_state(row) == "expression_unfilled":
        return "hard_filter_zero_eligible"
    return "not_applicable"


def _model_execution_mismatch(
    *,
    intended_trade: bool,
    row: Mapping[str, Any],
    candidate_count_after_filter: int | None,
    eligible_candidate_count: int | None,
    expression_selected_contract: str,
) -> bool:
    if row.get("fill_status") == "simulated_filled":
        return False
    if not intended_trade:
        return False
    return bool(
        expression_selected_contract
        or (candidate_count_after_filter is not None and candidate_count_after_filter > 0)
        or (eligible_candidate_count is not None and eligible_candidate_count > 0)
    )


def _fail_reason_counts(row: Mapping[str, str] | None) -> dict[str, int]:
    if row is None:
        return {}
    try:
        parsed = ast.literal_eval(str(row.get("fail_reason_counts") or "{}"))
    except (SyntaxError, ValueError):
        return {}
    if not isinstance(parsed, Mapping):
        return {}
    output: dict[str, int] = {}
    for reason, count in parsed.items():
        try:
            output[str(reason)] = int(count)
        except (TypeError, ValueError):
            continue
    return output


def _primary_filter_reason(fail_reason_counts: Mapping[str, int]) -> str:
    if not fail_reason_counts:
        return ""
    return max(fail_reason_counts.items(), key=lambda item: item[1])[0]


def _counterfactual_bucket(
    *,
    row: Mapping[str, Any],
    intended_trade: bool,
    expression_row: Mapping[str, str] | None,
    option_feasibility_state: str,
    model_execution_mismatch: bool,
) -> tuple[str, list[str]]:
    if model_execution_mismatch:
        return "execution_connection_failure", ["intended_trade_had_available_contract_but_was_not_filled"]
    if intended_trade and option_feasibility_state in {"expression_evidence_missing", "no_point_in_time_candidates"}:
        return "data_insufficiency", [option_feasibility_state]
    score = _float(row.get("prediction_score"))
    realized_return = _float(row.get("realized_return"))
    if row.get("fill_status") == "simulated_filled" and score >= 0.8 and realized_return < 0:
        return "model_mechanism_defect", ["high_score_filled_tail_loss"]
    if (
        intended_trade
        and option_feasibility_state == "hard_filter_zero_eligible"
        and str(row.get("outcome_label")) == "1"
        and expression_row is not None
    ):
        return "model_mechanism_defect", ["option_expression_filter_blocks_positive_underlying_label"]
    return "not_diagnostic", []


def _counterfactual_summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    counterfactual_rows: Sequence[Mapping[str, Any]],
    score_bin_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    bucket_counts: Counter[str] = Counter(str(row["row_counterfactual_bucket"]) for row in counterfactual_rows)
    bucket_label_sums: Counter[str] = Counter()
    bucket_realized_returns: Counter[str] = Counter()
    for row in counterfactual_rows:
        bucket = str(row["row_counterfactual_bucket"])
        bucket_label_sums[bucket] += _float(row.get("outcome_label"))
        bucket_realized_returns[bucket] += _float(row.get("realized_return"))
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    filled_good = [row for row in filled if str(row.get("outcome_label")) == "1"]
    filled_bad = [row for row in filled if str(row.get("outcome_label")) == "0"]
    score_gap = _mean(_float(row.get("prediction_score")) for row in filled_good)
    bad_score = _mean(_float(row.get("prediction_score")) for row in filled_bad)
    score_gap = None if score_gap is None or bad_score is None else score_gap - bad_score
    intended_unfilled_rows = [
        row
        for row in counterfactual_rows
        if row.get("intended_model_trade") is True and row.get("execution_expression_state") == "expression_unfilled"
    ]
    unfilled_good_count = sum(1 for row in intended_unfilled_rows if str(row.get("outcome_label")) == "1")
    score_bin_status = _filled_score_bin_monotonicity_status(score_bin_rows)
    sample_sufficiency = _sample_sufficiency_status(filled_count=len(filled), score_bin_rows=score_bin_rows)
    high_score_filled_loss_count = sum(
        1 for row in filled if _float(row.get("prediction_score")) >= 0.8 and _float(row.get("realized_return")) < 0
    )
    execution_mismatch_count = sum(1 for row in counterfactual_rows if row.get("model_execution_mismatch") is True)
    mechanism_reason_codes = []
    if score_gap is not None and abs(score_gap) < 0.02:
        mechanism_reason_codes.append("filled_good_bad_score_gap_below_0_02")
    if score_bin_status["status"] == "non_monotonic":
        mechanism_reason_codes.append("filled_score_bins_non_monotonic")
    if high_score_filled_loss_count:
        mechanism_reason_codes.append("high_score_filled_tail_losses_present")
    return {
        "counterfactual_bucket_counts": dict(bucket_counts),
        "counterfactual_bucket_label_rates": {
            bucket: _round(bucket_label_sums[bucket] / count) if count else None
            for bucket, count in bucket_counts.items()
        },
        "counterfactual_bucket_realized_return_totals": {
            bucket: _round(bucket_realized_returns[bucket]) for bucket in bucket_counts
        },
        "m04_open_m05_pass_unfilled_good_count": unfilled_good_count,
        "m04_open_m05_pass_unfilled_positive_underlying_return_total": _round(
            sum(_float(row.get("underlying_return")) for row in intended_unfilled_rows if str(row.get("outcome_label")) == "1")
        ),
        "m04_open_m05_pass_unfilled_csv_count": sum(
            1 for row in intended_unfilled_rows if row.get("expression_join_status") == "matched"
        ),
        "expression_join_status_counts": dict(
            Counter(str(row.get("expression_join_status") or "") for row in counterfactual_rows)
        ),
        "filled_good_bad_score_gap": _round(score_gap),
        "filled_score_bin_monotonicity_status": score_bin_status,
        "execution_connection_mismatch_count": execution_mismatch_count,
        "sample_sufficiency_status": sample_sufficiency,
        "high_score_filled_loss_count": high_score_filled_loss_count,
        "root_cause_assessment": {
            "data_insufficiency": {
                "status": "supported" if sample_sufficiency["status"] == "sample_limited" else "not_supported",
                "reason_codes": sample_sufficiency["reason_codes"],
            },
            "execution_connection_failure": {
                "status": "supported" if execution_mismatch_count else "not_supported_by_current_evidence",
                "reason_codes": ["intended_trade_available_contract_not_filled"] if execution_mismatch_count else [],
            },
            "model_mechanism_defect": {
                "status": "supported" if mechanism_reason_codes else "not_supported",
                "reason_codes": mechanism_reason_codes,
            },
        },
    }


def _filled_score_bin_monotonicity_status(score_bin_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    previous_return: float | None = None
    violations: list[dict[str, Any]] = []
    for row in score_bin_rows:
        current_return = row.get("return_per_row")
        if current_return is None:
            continue
        current_return_float = float(current_return)
        if previous_return is not None and current_return_float < previous_return:
            violations.append(
                {
                    "score_bin": row.get("score_bin"),
                    "return_per_row": _round(current_return_float),
                    "previous_return_per_row": _round(previous_return),
                }
            )
        previous_return = current_return_float
    return {
        "status": "non_monotonic" if violations else "monotonic",
        "violations": violations,
    }


def _sample_sufficiency_status(*, filled_count: int, score_bin_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reason_codes: list[str] = []
    if filled_count < 200:
        reason_codes.append("filled_sample_below_200")
    sparse_bins = [
        str(row.get("score_bin"))
        for row in score_bin_rows
        if row.get("row_count") is not None and int(row["row_count"]) < 30
    ]
    if sparse_bins:
        reason_codes.append("filled_score_bins_below_30:" + ",".join(sparse_bins))
    return {
        "status": "sample_limited" if reason_codes else "sufficient_for_this_diagnostic",
        "filled_count": filled_count,
        "minimum_required_filled_count": 200,
        "sparse_score_bins": sparse_bins,
        "minimum_required_bin_count": 30,
        "reason_codes": reason_codes,
    }


def _parameter_replay_review(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    numeric_values: dict[str, list[tuple[float, Mapping[str, Any]]]] = defaultdict(list)
    categorical_values: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for row in rows:
        for name, value in _numeric_parameter_values(row).items():
            numeric_values[name].append((value, row))
        for name, value in _categorical_parameter_values(row).items():
            categorical_values[name].append((value, row))

    parameter_rows: list[dict[str, Any]] = []
    bucket_rows: list[dict[str, Any]] = []
    categorical_rows: list[dict[str, Any]] = []
    for parameter_name, pairs in sorted(numeric_values.items()):
        parameter_row, parameter_bucket_rows = _numeric_parameter_review_row(parameter_name, pairs, total_row_count=len(rows))
        parameter_rows.append(parameter_row)
        bucket_rows.extend(parameter_bucket_rows)
    for parameter_name, pairs in sorted(categorical_values.items()):
        categorical_rows.extend(_categorical_parameter_review_rows(parameter_name, pairs))
    suspect_counterfactual_rows = _suspect_parameter_counterfactual_rows(parameter_rows, numeric_values)
    suspect_counterfactual_summary = _suspect_parameter_counterfactual_summary(suspect_counterfactual_rows)

    return {
        "report": _parameter_review_report(
            parameter_rows,
            categorical_rows,
            suspect_counterfactual_summary=suspect_counterfactual_summary,
        ),
        "summary": _parameter_review_summary(parameter_rows),
        "parameter_rows": parameter_rows,
        "bucket_rows": bucket_rows,
        "categorical_rows": categorical_rows,
        "suspect_counterfactual_rows": suspect_counterfactual_rows,
        "suspect_counterfactual_summary": suspect_counterfactual_summary,
        "suspect_counterfactual_report": _suspect_parameter_counterfactual_report(suspect_counterfactual_rows),
    }


def _numeric_parameter_values(row: Mapping[str, Any]) -> dict[str, float]:
    output: dict[str, float] = {}
    for key, value in row.items():
        if key.startswith("feature_") or key in {
            "prediction_score",
            "entry_minimum_alpha_confidence",
            "entry_minimum_trade_intensity",
            "bar_close",
        }:
            parsed = _finite_float(value)
            if parsed is not None:
                output[key] = parsed
    output.update(
        _flatten_numeric_parameters(
            row.get("model_layer_diagnostics") or {},
            prefix="model_layer_diagnostics",
        )
    )
    return {
        key: value
        for key, value in output.items()
        if not _parameter_name_is_outcome_or_id(key)
    }


def _flatten_numeric_parameters(value: Any, *, prefix: str) -> dict[str, float]:
    if isinstance(value, Mapping):
        output: dict[str, float] = {}
        for child_key, child_value in value.items():
            output.update(_flatten_numeric_parameters(child_value, prefix=f"{prefix}.{child_key}"))
        return output
    parsed = _finite_float(value)
    return {prefix: parsed} if parsed is not None else {}


def _parameter_name_is_outcome_or_id(name: str) -> bool:
    lowered = name.lower()
    forbidden = ("realized", "return_source", "outcome", "label", "next_", "_ref", "_id")
    return any(token in lowered for token in forbidden)


def _categorical_parameter_values(row: Mapping[str, Any]) -> dict[str, str]:
    diagnostics = row.get("model_layer_diagnostics") or {}
    m04 = diagnostics.get("model_04_unified_decision") or {}
    m05 = diagnostics.get("model_05_alpha_confidence") or {}
    return {
        "decision_action": _text(row.get("decision_action") or row.get("action")),
        "decision_status": _text(row.get("decision_status")),
        "fill_status": _text(row.get("fill_status")),
        "asset_expression_route": _text(row.get("asset_expression_route")),
        "option_contract_path_status": _text(row.get("option_contract_path_status")),
        "selected_option_expression_type": _selected_expression_type(row),
        "model_04.resolved_underlying_action_type": _text(m04.get("resolved_underlying_action_type")),
        "model_04.resolved_action_side": _text(m04.get("resolved_action_side")),
        "model_04.dominant_horizon": _text(m04.get("dominant_horizon")),
        "model_05.alpha_gate_status": _text(m05.get("alpha_gate_status")),
    }


def _numeric_parameter_review_row(
    parameter_name: str,
    pairs: Sequence[tuple[float, Mapping[str, Any]]],
    *,
    total_row_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    values = [value for value, _row in pairs]
    rows = [row for _value, row in pairs]
    buckets = _numeric_parameter_bucket_rows(parameter_name, pairs, bucket_count=DEFAULT_PARAMETER_BUCKET_COUNT)
    expected_direction = _expected_parameter_direction(parameter_name)
    label_correlation = _spearman(values, [_float(row.get("outcome_label")) for row in rows])
    return_correlation = _spearman(values, [_float(row.get("realized_return")) for row in rows])
    filled_pairs = [(value, row) for value, row in pairs if row.get("fill_status") == "simulated_filled"]
    filled_return_correlation = _spearman(
        [value for value, _row in filled_pairs],
        [_float(row.get("realized_return")) for _value, row in filled_pairs],
    )
    filled_buckets = _numeric_parameter_bucket_rows(
        parameter_name,
        filled_pairs,
        bucket_count=DEFAULT_PARAMETER_BUCKET_COUNT,
    )
    low_bucket, high_bucket = _edge_buckets(buckets)
    low_filled_bucket, high_filled_bucket = _edge_buckets(filled_buckets)
    return_spread = None
    label_rate_spread = None
    filled_return_spread = None
    if low_bucket is not None and high_bucket is not None:
        return_spread = _none_subtract(high_bucket.get("return_per_row"), low_bucket.get("return_per_row"))
        label_rate_spread = _none_subtract(high_bucket.get("label_rate"), low_bucket.get("label_rate"))
    if low_filled_bucket is not None and high_filled_bucket is not None:
        filled_return_spread = _none_subtract(
            high_filled_bucket.get("return_per_row"),
            low_filled_bucket.get("return_per_row"),
        )
    classification, reason_codes = _numeric_parameter_classification(
        expected_direction=expected_direction,
        sample_count=len(pairs),
        unique_count=len(set(values)),
        filled_count=len(filled_pairs),
        return_correlation=return_correlation,
        return_spread=return_spread,
        filled_return_correlation=filled_return_correlation,
        filled_return_spread=filled_return_spread,
    )
    return (
        {
            "parameter_name": parameter_name,
            "parameter_family": _parameter_family(parameter_name),
            "expected_direction": _direction_text(expected_direction),
            "classification": classification,
            "reason_codes": ";".join(reason_codes),
            "sample_count": len(pairs),
            "non_null_count": len(pairs),
            "missing_rate": _round(1 - (len(pairs) / total_row_count)) if total_row_count else None,
            "filled_count": len(filled_pairs),
            "unique_value_count": len(set(values)),
            "value_min": _round(min(values)) if values else None,
            "value_max": _round(max(values)) if values else None,
            "value_mean": _round(_mean(values)),
            "label_spearman": _round(label_correlation),
            "return_spearman": _round(return_correlation),
            "filled_return_spearman": _round(filled_return_correlation),
            "high_minus_low_return_per_row": _round(return_spread),
            "filled_high_minus_low_return_per_row": _round(filled_return_spread),
            "high_minus_low_label_rate": _round(label_rate_spread),
            "fixed_input_only": True,
            "threshold_selection_performed": False,
        },
        buckets,
    )


def _numeric_parameter_bucket_rows(
    parameter_name: str,
    pairs: Sequence[tuple[float, Mapping[str, Any]]],
    *,
    bucket_count: int,
) -> list[dict[str, Any]]:
    if not pairs:
        return []
    ordered = sorted(pairs, key=lambda item: item[0])
    groups: list[list[tuple[float, Mapping[str, Any]]]] = []
    for bucket_index in range(bucket_count):
        start = round(bucket_index * len(ordered) / bucket_count)
        end = round((bucket_index + 1) * len(ordered) / bucket_count)
        group = ordered[start:end]
        if group:
            groups.append(group)
    output: list[dict[str, Any]] = []
    for index, group in enumerate(groups, start=1):
        values = [value for value, _row in group]
        group_rows = [row for _value, row in group]
        summary = _summary(group_rows)
        output.append(
            {
                "parameter_name": parameter_name,
                "bucket_index": index,
                "bucket_count": len(groups),
                "value_min": _round(min(values)),
                "value_max": _round(max(values)),
                "value_mean": _round(_mean(values)),
                **summary,
            }
        )
    return output


def _edge_buckets(bucket_rows: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any] | None, Mapping[str, Any] | None]:
    if len(bucket_rows) < 2:
        return None, None
    return bucket_rows[0], bucket_rows[-1]


def _none_subtract(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _numeric_parameter_classification(
    *,
    expected_direction: int | None,
    sample_count: int,
    unique_count: int,
    filled_count: int,
    return_correlation: float | None,
    return_spread: float | None,
    filled_return_correlation: float | None,
    filled_return_spread: float | None,
) -> tuple[str, list[str]]:
    reason_codes: list[str] = []
    if sample_count < MIN_PARAMETER_SAMPLE_COUNT:
        reason_codes.append("sample_count_below_minimum")
    if unique_count < MIN_PARAMETER_UNIQUE_VALUES:
        return "not_reviewable", ["unique_value_count_below_minimum"]
    if filled_count < MIN_PARAMETER_FILLED_COUNT:
        reason_codes.append("filled_sample_below_minimum")
    if reason_codes:
        return "weak_or_sample_limited", reason_codes
    if return_correlation is None or return_spread is None:
        return "weak_or_sample_limited", ["insufficient_numeric_variation"]
    aligned_correlation = return_correlation if expected_direction != -1 else -return_correlation
    aligned_spread = return_spread if expected_direction != -1 else -return_spread
    aligned_filled_correlation = (
        None
        if filled_return_correlation is None
        else filled_return_correlation if expected_direction != -1 else -filled_return_correlation
    )
    aligned_filled_spread = (
        None
        if filled_return_spread is None
        else filled_return_spread if expected_direction != -1 else -filled_return_spread
    )
    if expected_direction is None:
        if abs(return_correlation) >= MIN_PARAMETER_ABS_CORRELATION and abs(return_spread) >= MIN_PARAMETER_RETURN_SPREAD:
            return "empirical_signal_present_direction_unassigned", ["expected_direction_not_registered"]
        return "weak_or_sample_limited", ["weak_empirical_signal_or_unassigned_direction"]
    if aligned_correlation >= MIN_PARAMETER_ABS_CORRELATION and aligned_spread >= MIN_PARAMETER_RETURN_SPREAD:
        return "directionally_useful", ["return_correlation_and_bucket_spread_align"]
    if aligned_correlation <= -MIN_PARAMETER_ABS_CORRELATION and aligned_spread <= -MIN_PARAMETER_RETURN_SPREAD:
        return "suspect_requires_redesign", ["return_correlation_and_bucket_spread_inverted"]
    if (
        aligned_filled_correlation is not None
        and aligned_filled_spread is not None
        and aligned_filled_correlation <= -MIN_PARAMETER_ABS_CORRELATION
        and aligned_filled_spread <= -MIN_PARAMETER_RETURN_SPREAD
    ):
        return "suspect_requires_redesign", ["filled_return_correlation_and_bucket_spread_inverted"]
    if (
        aligned_filled_correlation is not None
        and aligned_filled_spread is not None
        and aligned_filled_correlation >= MIN_PARAMETER_ABS_CORRELATION
        and aligned_filled_spread >= MIN_PARAMETER_RETURN_SPREAD
    ):
        return "directionally_useful", ["filled_return_correlation_and_bucket_spread_align"]
    return "weak_or_sample_limited", ["weak_or_mixed_replay_signal"]


def _expected_parameter_direction(parameter_name: str) -> int | None:
    lowered = parameter_name.lower()
    if "downside_risk" in lowered or "cost" in lowered:
        return -1
    positive_tokens = (
        "prediction_score",
        "alpha",
        "confidence",
        "expected_return",
        "trade_intensity",
        "entry_quality",
        "action_direction",
        "momentum",
        "volume_rank",
        "feature_coverage",
        "signed_edge",
    )
    if any(token in lowered for token in positive_tokens):
        return 1
    return None


def _direction_text(direction: int | None) -> str:
    if direction == 1:
        return "higher_expected_better"
    if direction == -1:
        return "higher_expected_worse"
    return "unassigned"


def _parameter_family(parameter_name: str) -> str:
    if parameter_name.startswith("feature_"):
        return "top_level_feature"
    if "model_04_unified_decision" in parameter_name:
        return "model_04_unified_decision"
    if "model_05_alpha_confidence" in parameter_name:
        return "model_05_alpha_confidence"
    if parameter_name in {"prediction_score", "entry_minimum_alpha_confidence", "entry_minimum_trade_intensity"}:
        return "replay_decision_parameter"
    return "other"


def _categorical_parameter_review_rows(
    parameter_name: str,
    pairs: Sequence[tuple[str, Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for value, row in pairs:
        groups[value or "missing"].append(row)
    output: list[dict[str, Any]] = []
    for value, group_rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        output.append(
            {
                "parameter_name": parameter_name,
                "parameter_value": value,
                **_summary(group_rows),
                "fixed_input_only": True,
                "threshold_selection_performed": False,
            }
        )
    return output


def _parameter_review_summary(parameter_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("classification") or "unknown") for row in parameter_rows)
    top_suspect = [
        str(row.get("parameter_name"))
        for row in parameter_rows
        if row.get("classification") == "suspect_requires_redesign"
    ][:10]
    top_useful = [
        str(row.get("parameter_name"))
        for row in parameter_rows
        if row.get("classification") == "directionally_useful"
    ][:10]
    return {
        "contract_type": "model_group_parameter_replay_review_summary",
        "parameter_count": len(parameter_rows),
        "classification_counts": dict(counts),
        "directionally_useful_parameters": top_useful,
        "suspect_requires_redesign_parameters": top_suspect,
        "fixed_input_only": True,
        "threshold_selection_performed": False,
        "interpretation_limits": [
            "Correlation and bucket spreads are replay diagnostics, not causal feature attribution.",
            "Sparse filled-option rows can make parameter classifications sample-limited.",
            "Unassigned-direction parameters require model-owner interpretation before redesign.",
        ],
    }


def _parameter_review_report(
    parameter_rows: Sequence[Mapping[str, Any]],
    categorical_rows: Sequence[Mapping[str, Any]],
    *,
    suspect_counterfactual_summary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "contract_type": "model_group_parameter_replay_review_report",
        "summary": _parameter_review_summary(parameter_rows),
        "numeric_parameter_rows_ref": "parameter_replay_review.csv",
        "numeric_parameter_bucket_rows_ref": "parameter_bucket_metrics.csv",
        "categorical_parameter_rows_ref": "categorical_parameter_replay_review.csv",
        "suspect_parameter_counterfactual_rows_ref": "suspect_parameter_counterfactual.csv",
        "suspect_parameter_counterfactual_report_ref": "suspect_parameter_counterfactual_report.json",
        "suspect_parameter_counterfactual_summary": suspect_counterfactual_summary,
        "categorical_parameter_count": len({row.get("parameter_name") for row in categorical_rows}),
        "review_role": "fixed_replay_association_diagnostic_only",
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _suspect_parameter_counterfactual_rows(
    parameter_rows: Sequence[Mapping[str, Any]],
    numeric_values: Mapping[str, Sequence[tuple[float, Mapping[str, Any]]]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    m04_suspect_count = sum(
        1
        for row in parameter_rows
        if row.get("classification") == "suspect_requires_redesign"
        and _parameter_family(str(row.get("parameter_name") or "")) == "model_04_unified_decision"
    )
    for parameter_row in parameter_rows:
        if parameter_row.get("classification") != "suspect_requires_redesign":
            continue
        parameter_name = str(parameter_row.get("parameter_name") or "")
        pairs = tuple(numeric_values.get(parameter_name) or ())
        if not pairs:
            continue
        output.append(
            _suspect_parameter_counterfactual_row(
                parameter_name=parameter_name,
                parameter_row=parameter_row,
                pairs=pairs,
                m04_suspect_count=m04_suspect_count,
            )
        )
    return output


def _suspect_parameter_counterfactual_row(
    *,
    parameter_name: str,
    parameter_row: Mapping[str, Any],
    pairs: Sequence[tuple[float, Mapping[str, Any]]],
    m04_suspect_count: int,
) -> dict[str, Any]:
    expected_direction = _expected_parameter_direction(parameter_name)
    all_stats = _parameter_subset_stats(pairs)
    filled_pairs = tuple((value, row) for value, row in pairs if row.get("fill_status") == "simulated_filled")
    nonfilled_pairs = tuple((value, row) for value, row in pairs if row.get("fill_status") != "simulated_filled")
    filled_stats = _parameter_subset_stats(filled_pairs)
    nonfilled_stats = _parameter_subset_stats(nonfilled_pairs)
    m04_open_pairs = tuple((value, row) for value, row in pairs if _m04_state(row) == "open_long/long")
    m04_open_filled_pairs = tuple(
        (value, row)
        for value, row in pairs
        if _m04_state(row) == "open_long/long" and row.get("fill_status") == "simulated_filled"
    )
    m04_open_stats = _parameter_subset_stats(m04_open_pairs)
    m04_open_filled_stats = _parameter_subset_stats(m04_open_filled_pairs)
    all_inversion = _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=all_stats["return_spearman"],
        return_spread=all_stats["high_minus_low_return_per_row"],
    )
    filled_inversion = _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=filled_stats["return_spearman"],
        return_spread=filled_stats["high_minus_low_return_per_row"],
    )
    m04_open_filled_inversion = _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=m04_open_filled_stats["return_spearman"],
        return_spread=m04_open_filled_stats["high_minus_low_return_per_row"],
    )
    label_inversion = _aligned_label_inversion_supported(
        expected_direction=expected_direction,
        label_correlation=all_stats["label_spearman"],
        label_spread=all_stats["high_minus_low_label_rate"],
    )
    fill_rate_spread = all_stats["high_minus_low_fill_rate"]
    selection_effect = (
        filled_inversion
        and not label_inversion
        and (
            not all_inversion
            or (
                fill_rate_spread is not None
                and abs(float(fill_rate_spread)) >= MIN_PARAMETER_FILL_RATE_SPREAD
            )
        )
    )
    parameter_family = _parameter_family(parameter_name)
    primary_mode, reason_codes = _suspect_parameter_primary_mode(
        parameter_family=parameter_family,
        all_inversion=all_inversion,
        filled_inversion=filled_inversion,
        label_inversion=label_inversion,
        selection_effect=selection_effect,
        m04_open_filled_inversion=m04_open_filled_inversion,
        m04_suspect_count=m04_suspect_count,
    )
    return {
        "parameter_name": parameter_name,
        "parameter_family": parameter_family,
        "expected_direction": parameter_row.get("expected_direction"),
        "primary_followup_mode": primary_mode,
        "reason_codes": ";".join(reason_codes),
        "all_row_inversion_supported": all_inversion,
        "filled_only_inversion_supported": filled_inversion,
        "all_label_inversion_supported": label_inversion,
        "filled_subset_selection_effect_supported": selection_effect,
        "m04_open_filled_inversion_supported": m04_open_filled_inversion,
        "m04_family_suspect_parameter_count": m04_suspect_count if parameter_family == "model_04_unified_decision" else 0,
        "sample_count": all_stats["row_count"],
        "filled_count": filled_stats["row_count"],
        "nonfilled_count": nonfilled_stats["row_count"],
        "m04_open_count": m04_open_stats["row_count"],
        "m04_open_filled_count": m04_open_filled_stats["row_count"],
        "value_mean": _round(all_stats["value_mean"]),
        "filled_value_mean": _round(filled_stats["value_mean"]),
        "nonfilled_value_mean": _round(nonfilled_stats["value_mean"]),
        "label_spearman": _round(all_stats["label_spearman"]),
        "return_spearman": _round(all_stats["return_spearman"]),
        "filled_return_spearman": _round(filled_stats["return_spearman"]),
        "m04_open_filled_return_spearman": _round(m04_open_filled_stats["return_spearman"]),
        "high_minus_low_label_rate": _round(all_stats["high_minus_low_label_rate"]),
        "high_minus_low_return_per_row": _round(all_stats["high_minus_low_return_per_row"]),
        "filled_high_minus_low_return_per_row": _round(filled_stats["high_minus_low_return_per_row"]),
        "m04_open_filled_high_minus_low_return_per_row": _round(
            m04_open_filled_stats["high_minus_low_return_per_row"]
        ),
        "low_bucket_fill_rate": _round(all_stats["low_bucket_fill_rate"]),
        "high_bucket_fill_rate": _round(all_stats["high_bucket_fill_rate"]),
        "high_minus_low_fill_rate": _round(fill_rate_spread),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _parameter_subset_stats(pairs: Sequence[tuple[float, Mapping[str, Any]]]) -> dict[str, Any]:
    if not pairs:
        return {
            "row_count": 0,
            "label_spearman": None,
            "return_spearman": None,
            "value_mean": None,
            "high_minus_low_label_rate": None,
            "high_minus_low_return_per_row": None,
            "low_bucket_fill_rate": None,
            "high_bucket_fill_rate": None,
            "high_minus_low_fill_rate": None,
        }
    values = [value for value, _row in pairs]
    rows = [row for _value, row in pairs]
    buckets = _numeric_parameter_bucket_rows("parameter_subset", pairs, bucket_count=DEFAULT_PARAMETER_BUCKET_COUNT)
    low_bucket, high_bucket = _edge_buckets(buckets)
    label_spread = None
    return_spread = None
    fill_rate_spread = None
    low_bucket_fill_rate = None
    high_bucket_fill_rate = None
    if low_bucket is not None and high_bucket is not None:
        label_spread = _none_subtract(high_bucket.get("label_rate"), low_bucket.get("label_rate"))
        return_spread = _none_subtract(high_bucket.get("return_per_row"), low_bucket.get("return_per_row"))
        low_bucket_fill_rate = _fill_rate_from_summary(low_bucket)
        high_bucket_fill_rate = _fill_rate_from_summary(high_bucket)
        fill_rate_spread = _none_subtract(high_bucket_fill_rate, low_bucket_fill_rate)
    return {
        "row_count": len(pairs),
        "label_spearman": _spearman(values, [_float(row.get("outcome_label")) for row in rows]),
        "return_spearman": _spearman(values, [_float(row.get("realized_return")) for row in rows]),
        "value_mean": _mean(values),
        "high_minus_low_label_rate": label_spread,
        "high_minus_low_return_per_row": return_spread,
        "low_bucket_fill_rate": low_bucket_fill_rate,
        "high_bucket_fill_rate": high_bucket_fill_rate,
        "high_minus_low_fill_rate": fill_rate_spread,
    }


def _fill_rate_from_summary(row: Mapping[str, Any]) -> float | None:
    row_count = int(row.get("row_count") or 0)
    if row_count <= 0:
        return None
    return _float(row.get("filled_count")) / row_count


def _aligned_inversion_supported(
    *,
    expected_direction: int | None,
    return_correlation: Any,
    return_spread: Any,
) -> bool:
    if expected_direction is None or return_correlation is None or return_spread is None:
        return False
    aligned_correlation = float(return_correlation) if expected_direction != -1 else -float(return_correlation)
    aligned_spread = float(return_spread) if expected_direction != -1 else -float(return_spread)
    return aligned_correlation <= -MIN_PARAMETER_ABS_CORRELATION and aligned_spread <= -MIN_PARAMETER_RETURN_SPREAD


def _aligned_label_inversion_supported(
    *,
    expected_direction: int | None,
    label_correlation: Any,
    label_spread: Any,
) -> bool:
    if expected_direction is None or label_correlation is None or label_spread is None:
        return False
    aligned_correlation = float(label_correlation) if expected_direction != -1 else -float(label_correlation)
    aligned_spread = float(label_spread) if expected_direction != -1 else -float(label_spread)
    return aligned_correlation <= -MIN_PARAMETER_ABS_CORRELATION and aligned_spread <= -MIN_PARAMETER_LABEL_RATE_SPREAD


def _suspect_parameter_primary_mode(
    *,
    parameter_family: str,
    all_inversion: bool,
    filled_inversion: bool,
    label_inversion: bool,
    selection_effect: bool,
    m04_open_filled_inversion: bool,
    m04_suspect_count: int,
) -> tuple[str, list[str]]:
    if (
        parameter_family == "model_04_unified_decision"
        and filled_inversion
        and m04_open_filled_inversion
        and m04_suspect_count >= 2
    ):
        return "m04_component_weight_or_direction_issue", [
            "multiple_m04_score_components_inverted_in_filled_subset",
            "m04_open_filled_subset_inversion_supported",
        ]
    if selection_effect:
        return "filled_subset_selection_effect", [
            "filled_subset_inversion_without_all_row_inversion",
            "fill_or_label_distribution_differs_across_parameter_buckets",
        ]
    if all_inversion and label_inversion:
        return "parameter_definition_or_direction_inversion", [
            "all_row_return_and_label_direction_inverted",
        ]
    if filled_inversion:
        return "filled_subset_unisolated_inversion", [
            "filled_subset_inversion_supported",
            "all_row_or_label_evidence_not_inverted",
        ]
    return "not_isolated_sample_limited", ["suspect_parameter_review_needs_more_evidence"]


def _suspect_parameter_counterfactual_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    mode_counts = Counter(str(row.get("primary_followup_mode") or "unknown") for row in rows)
    return {
        "contract_type": "model_group_suspect_parameter_counterfactual_summary",
        "suspect_parameter_count": len(rows),
        "primary_followup_mode_counts": dict(mode_counts),
        "filled_subset_selection_effect_parameters": [
            str(row.get("parameter_name"))
            for row in rows
            if row.get("primary_followup_mode") == "filled_subset_selection_effect"
        ],
        "m04_component_weight_or_direction_issue_parameters": [
            str(row.get("parameter_name"))
            for row in rows
            if row.get("primary_followup_mode") == "m04_component_weight_or_direction_issue"
        ],
        "parameter_definition_or_direction_inversion_parameters": [
            str(row.get("parameter_name"))
            for row in rows
            if row.get("primary_followup_mode") == "parameter_definition_or_direction_inversion"
        ],
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
        "interpretation_limits": [
            "This counterfactual compares fixed replay subsets only and is not a causal parameter-importance claim.",
            "Filled-only inversion can indicate selection effects, option-expression mechanics, or M04 score behavior.",
            "Primary follow-up modes are repair triage labels, not automatic model redesign approval.",
        ],
    }


def _suspect_parameter_counterfactual_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "contract_type": "model_group_suspect_parameter_counterfactual_report",
        "summary": _suspect_parameter_counterfactual_summary(rows),
        "suspect_parameter_counterfactual_rows_ref": "suspect_parameter_counterfactual.csv",
        "review_role": "fixed_replay_suspect_parameter_triage_only",
        "fixed_input_only": True,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _m04_component_diagnostic_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    components = [
        "action_direction_score",
        "expected_return_score",
        "trade_intensity_score",
        "materiality_adjusted_action_score",
        "action_confidence_score",
        "entry_quality_score",
        "downside_risk_score",
        "no_trade_probability_score",
    ]
    subsets = {
        "all_rows": tuple(rows),
        "m04_open": tuple(row for row in rows if _m04_state(row) == "open_long/long"),
        "m04_open_m05_pass": tuple(
            row for row in rows if _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
        ),
        "m04_open_m05_pass_filled": tuple(
            row
            for row in rows
            if _m04_state(row) == "open_long/long"
            and _m05_state(row) == "alpha_passed"
            and row.get("fill_status") == "simulated_filled"
        ),
    }
    output: list[dict[str, Any]] = []
    for component in components:
        expected_direction = _m04_component_expected_direction(component)
        for subset_name, subset_rows in subsets.items():
            pairs = tuple(_m04_component_pairs(subset_rows, component))
            stats = _parameter_subset_stats(pairs)
            status, reason_codes = _m04_component_diagnostic_status(
                expected_direction=expected_direction,
                subset_input_count=len(subset_rows),
                subset_name=subset_name,
                stats=stats,
            )
            output.append(
                {
                    "component_name": component,
                    "subset_name": subset_name,
                    "expected_direction": _direction_text(expected_direction),
                    "diagnostic_status": status,
                    "reason_codes": ";".join(reason_codes),
                    "row_count": stats["row_count"],
                    "filled_count": sum(1 for _value, row in pairs if row.get("fill_status") == "simulated_filled"),
                    "value_mean": _round(stats["value_mean"]),
                    "label_spearman": _round(stats["label_spearman"]),
                    "return_spearman": _round(stats["return_spearman"]),
                    "high_minus_low_label_rate": _round(stats["high_minus_low_label_rate"]),
                    "high_minus_low_return_per_row": _round(stats["high_minus_low_return_per_row"]),
                    "low_bucket_fill_rate": _round(stats["low_bucket_fill_rate"]),
                    "high_bucket_fill_rate": _round(stats["high_bucket_fill_rate"]),
                    "high_minus_low_fill_rate": _round(stats["high_minus_low_fill_rate"]),
                    "threshold_selection_performed": False,
                    "retraining_performed": False,
                    "fixed_input_only": True,
                }
            )
    return output


def _m04_component_pairs(rows: Sequence[Mapping[str, Any]], component: str) -> Iterable[tuple[float, Mapping[str, Any]]]:
    for row in rows:
        scores = _m04_component_scores(row)
        parsed = _finite_float(scores.get(component))
        if parsed is not None:
            yield parsed, row


def _m04_component_scores(row: Mapping[str, Any]) -> Mapping[str, Any]:
    scores = dict(_m04_diagnostics(row).get("dominant_horizon_scores") or {})
    if "materiality_adjusted_action_score" not in scores:
        derived = _materiality_adjusted_action_score(
            scores,
            minimum_trade_intensity=_minimum_trade_intensity(row, scores),
        )
        if derived is not None:
            scores["materiality_adjusted_action_score"] = derived
    return scores


def _m04_component_expected_direction(component: str) -> int | None:
    if component in {"downside_risk_score", "no_trade_probability_score"}:
        return -1
    return 1


def _m04_component_diagnostic_status(
    *,
    expected_direction: int | None,
    subset_input_count: int,
    subset_name: str,
    stats: Mapping[str, Any],
) -> tuple[str, list[str]]:
    if subset_input_count > 0 and int(stats["row_count"] or 0) == 0:
        return "missing_component_coverage", [f"{subset_name}_required_component_missing_from_replay_rows"]
    if int(stats["row_count"] or 0) < MIN_PARAMETER_FILLED_COUNT:
        return "sample_limited", ["subset_count_below_minimum"]
    if _aligned_inversion_supported(
        expected_direction=expected_direction,
        return_correlation=stats["return_spearman"],
        return_spread=stats["high_minus_low_return_per_row"],
    ):
        return "inverted_against_expected_direction", [f"{subset_name}_return_correlation_and_spread_inverted"]
    if _aligned_useful_supported(
        expected_direction=expected_direction,
        return_correlation=stats["return_spearman"],
        return_spread=stats["high_minus_low_return_per_row"],
    ):
        return "aligned_with_expected_direction", [f"{subset_name}_return_correlation_and_spread_align"]
    return "weak_or_mixed", [f"{subset_name}_weak_or_mixed_component_signal"]


def _aligned_useful_supported(
    *,
    expected_direction: int | None,
    return_correlation: Any,
    return_spread: Any,
) -> bool:
    if expected_direction is None or return_correlation is None or return_spread is None:
        return False
    aligned_correlation = float(return_correlation) if expected_direction != -1 else -float(return_correlation)
    aligned_spread = float(return_spread) if expected_direction != -1 else -float(return_spread)
    return aligned_correlation >= MIN_PARAMETER_ABS_CORRELATION and aligned_spread >= MIN_PARAMETER_RETURN_SPREAD


def _m05_selection_mechanics_rows(
    rows: Sequence[Mapping[str, Any]],
    counterfactual_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    counterfactual_by_decision_id = {str(row.get("decision_id") or ""): row for row in counterfactual_rows}
    groups: dict[tuple[str, str, str, str, str, str], list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = defaultdict(list)
    for row in rows:
        counterfactual = counterfactual_by_decision_id.get(str(row.get("decision_id") or ""), {})
        key = (
            _m04_state(row),
            _m05_state(row),
            _expression_state(row),
            str(counterfactual.get("option_feasibility_state") or ""),
            _selected_expression_type(row),
            str(counterfactual.get("primary_filter_reason") or ""),
        )
        groups[key].append((row, counterfactual))

    output: list[dict[str, Any]] = []
    for (m04_state, m05_state, expression_state, feasibility_state, expression_type, filter_reason), grouped in sorted(
        groups.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        group_rows = [row for row, _counterfactual in grouped]
        group_counterfactuals = [counterfactual for _row, counterfactual in grouped]
        output.append(
            {
                "m04_state": m04_state,
                "m05_state": m05_state,
                "execution_expression_state": expression_state,
                "option_feasibility_state": feasibility_state,
                "selected_expression_type": expression_type,
                "primary_filter_reason": filter_reason,
                **_summary(group_rows),
                "positive_label_count": sum(1 for row in group_rows if str(row.get("outcome_label")) == "1"),
                "positive_underlying_return_total": _round(
                    sum(
                        _float(counterfactual.get("underlying_return"))
                        for row, counterfactual in grouped
                        if str(row.get("outcome_label")) == "1"
                    )
                ),
                "candidate_count_before_filter_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "candidate_count_before_filter",
                ),
                "candidate_count_after_filter_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "candidate_count_after_filter",
                ),
                "eligible_candidate_count_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "eligible_candidate_count",
                ),
                "top_contract_fit_score_mean": _counterfactual_metric_mean(
                    group_counterfactuals,
                    "top_contract_fit_score",
                ),
                "threshold_selection_performed": False,
                "retraining_performed": False,
                "fixed_input_only": True,
            }
        )
    return output


def _selected_expression_type(row: Mapping[str, Any]) -> str:
    for key in (
        "selected_option_expression_type",
        "decision_expression_type",
        "5_resolved_expression_type",
        "resolved_expression_type",
        "expression_type",
    ):
        value = str(row.get(key) or "").strip()
        if value == "underlying_only":
            return "underlying_only_expression"
        if value:
            return value
    return ""


def _counterfactual_metric_mean(rows: Sequence[Mapping[str, Any]], key: str) -> float | None:
    return _round(
        _mean(
            _float(row.get(key))
            for row in rows
            if row.get("expression_join_status") == "matched" and row.get(key) not in (None, "")
        )
    )


def _m04_variant_counterfactual_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    subsets = {
        "m04_open_m05_pass": tuple(
            row for row in rows if _m04_state(row) == "open_long/long" and _m05_state(row) == "alpha_passed"
        ),
        "m04_open_m05_pass_filled": tuple(
            row
            for row in rows
            if _m04_state(row) == "open_long/long"
            and _m05_state(row) == "alpha_passed"
            and row.get("fill_status") == "simulated_filled"
        ),
    }
    output: list[dict[str, Any]] = []
    variants = _m04_variant_definitions()
    for variant_name, formula in variants:
        for subset_name, subset_rows in subsets.items():
            pairs = tuple(_m04_variant_pairs(subset_rows, variant_name))
            stats = _parameter_subset_stats(pairs)
            status, reason_codes = _m04_variant_status(
                subset_input_count=len(subset_rows),
                subset_name=subset_name,
                stats=stats,
            )
            output.append(
                {
                    "variant_name": variant_name,
                    "subset_name": subset_name,
                    "formula": formula,
                    "expected_direction": "higher_is_better",
                    "diagnostic_status": status,
                    "reason_codes": ";".join(reason_codes),
                    "row_count": stats["row_count"],
                    "filled_count": sum(1 for _value, row in pairs if row.get("fill_status") == "simulated_filled"),
                    "value_mean": _round(stats["value_mean"]),
                    "label_spearman": _round(stats["label_spearman"]),
                    "return_spearman": _round(stats["return_spearman"]),
                    "high_minus_low_label_rate": _round(stats["high_minus_low_label_rate"]),
                    "high_minus_low_return_per_row": _round(stats["high_minus_low_return_per_row"]),
                    "low_bucket_fill_rate": _round(stats["low_bucket_fill_rate"]),
                    "high_bucket_fill_rate": _round(stats["high_bucket_fill_rate"]),
                    "high_minus_low_fill_rate": _round(stats["high_minus_low_fill_rate"]),
                    "threshold_selection_performed": False,
                    "retraining_performed": False,
                    "fixed_input_only": True,
                }
            )
    return output


def _m04_variant_definitions() -> tuple[tuple[str, str], ...]:
    return (
        (
            "current_horizon_rank_proxy",
            "action_confidence_score + 0.35 * materiality_adjusted_action_score - 0.25 * no_trade_probability_score",
        ),
        (
            "materiality_guarded_rank_proxy",
            "current_horizon_rank_proxy * indicator(position_gap_below_materiality is absent)",
        ),
        (
            "risk_adjusted_intensity",
            "trade_intensity_score * action_confidence_score * entry_quality_score * (1 - downside_risk_score)",
        ),
        (
            "materiality_adjusted_action_score",
            "materiality_gate(trade_intensity_score, minimum_trade_intensity) * action_confidence_score * entry_quality_score * (1 - downside_risk_score) * (1 - no_trade_probability_score)",
        ),
        (
            "expected_return_intensity_product",
            "expected_return_score * trade_intensity_score",
        ),
        (
            "trade_intensity_margin",
            "trade_intensity_score - minimum_trade_intensity",
        ),
        (
            "inverse_trade_intensity",
            "1 - trade_intensity_score",
        ),
        (
            "deemphasized_intensity_quality",
            "action_confidence_score + entry_quality_score + expected_return_score - downside_risk_score - no_trade_probability_score",
        ),
    )


def _m04_variant_pairs(rows: Sequence[Mapping[str, Any]], variant_name: str) -> Iterable[tuple[float, Mapping[str, Any]]]:
    for row in rows:
        value = _m04_variant_value(row, variant_name)
        if value is not None:
            yield value, row


def _m04_variant_value(row: Mapping[str, Any], variant_name: str) -> float | None:
    scores = _m04_component_scores(row)
    action_confidence = _finite_float(scores.get("action_confidence_score"))
    trade_intensity = _finite_float(scores.get("trade_intensity_score"))
    entry_quality = _finite_float(scores.get("entry_quality_score"))
    expected_return = _finite_float(scores.get("expected_return_score"))
    downside_risk = _finite_float(scores.get("downside_risk_score"))
    no_trade_probability = _finite_float(scores.get("no_trade_probability_score"))
    minimum_trade_intensity = _minimum_trade_intensity(row, scores)
    materiality_adjusted_action = _materiality_adjusted_action_score(
        scores,
        minimum_trade_intensity=minimum_trade_intensity,
    )
    if variant_name == "current_horizon_rank_proxy":
        if action_confidence is None or materiality_adjusted_action is None or no_trade_probability is None:
            return None
        return action_confidence + 0.35 * materiality_adjusted_action - 0.25 * no_trade_probability
    if variant_name == "materiality_guarded_rank_proxy":
        if action_confidence is None or materiality_adjusted_action is None or no_trade_probability is None:
            return None
        base = action_confidence + 0.35 * materiality_adjusted_action - 0.25 * no_trade_probability
        return 0.0 if "position_gap_below_materiality" in _m04_reason_codes(row) else base
    if variant_name == "risk_adjusted_intensity":
        if None in (trade_intensity, action_confidence, entry_quality, downside_risk):
            return None
        return trade_intensity * action_confidence * entry_quality * (1.0 - downside_risk)
    if variant_name == "materiality_adjusted_action_score":
        return materiality_adjusted_action
    if variant_name == "expected_return_intensity_product":
        if expected_return is None or trade_intensity is None:
            return None
        return expected_return * trade_intensity
    if variant_name == "trade_intensity_margin":
        if trade_intensity is None or minimum_trade_intensity is None:
            return None
        return trade_intensity - minimum_trade_intensity
    if variant_name == "inverse_trade_intensity":
        if trade_intensity is None:
            return None
        return 1.0 - trade_intensity
    if variant_name == "deemphasized_intensity_quality":
        if None in (action_confidence, entry_quality, expected_return, downside_risk, no_trade_probability):
            return None
        return action_confidence + entry_quality + expected_return - downside_risk - no_trade_probability
    return None


def _portfolio_capacity_counterfactual_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    filled_rows = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    if not filled_rows:
        return [
            _portfolio_capacity_counterfactual_row(
                variant_name="baseline_selected_all",
                ranking_metric="replay_selected_order",
                rows=[],
                selected_rows=[],
                max_positions=0,
                budget_fraction=1.0,
                budget_blocked_count=0,
                position_blocked_count=0,
            )
        ]
    variants = [
        ("baseline_selected_all", "replay_selected_order", 0, 1.0),
        ("top_5_by_replay_rank", "replay_rank_score", 5, 1.0),
        ("top_10_by_replay_rank", "replay_rank_score", 10, 1.0),
        ("budget_50pct_by_replay_rank", "replay_rank_score", 0, 0.50),
        ("budget_75pct_by_replay_rank", "replay_rank_score", 0, 0.75),
    ]
    return [
        _portfolio_capacity_counterfactual_for_variant(
            rows=filled_rows,
            variant_name=variant_name,
            ranking_metric=ranking_metric,
            max_positions=max_positions,
            budget_fraction=budget_fraction,
        )
        for variant_name, ranking_metric, max_positions, budget_fraction in variants
    ]


def _portfolio_capacity_counterfactual_for_variant(
    *,
    rows: Sequence[Mapping[str, Any]],
    variant_name: str,
    ranking_metric: str,
    max_positions: int,
    budget_fraction: float,
) -> dict[str, Any]:
    ordered = list(rows)
    if ranking_metric == "replay_rank_score":
        ordered.sort(
            key=lambda row: (
                -_portfolio_replay_rank_score(row),
                str(row.get("timestamp") or ""),
                str(row.get("target_ref") or ""),
            )
        )
    else:
        ordered.sort(key=lambda row: (str(row.get("timestamp") or ""), str(row.get("decision_id") or "")))
    budget = _portfolio_total_budget(rows) * budget_fraction
    selected: list[Mapping[str, Any]] = []
    spent = 0.0
    budget_blocked = 0
    position_blocked = 0
    for row in ordered:
        if max_positions > 0 and len(selected) >= max_positions:
            position_blocked += 1
            continue
        notional = _planned_notional(row)
        if budget_fraction < 1.0 and spent + notional > budget + 1e-9:
            budget_blocked += 1
            continue
        selected.append(row)
        spent += notional
    return _portfolio_capacity_counterfactual_row(
        variant_name=variant_name,
        ranking_metric=ranking_metric,
        rows=ordered,
        selected_rows=selected,
        max_positions=max_positions,
        budget_fraction=budget_fraction,
        budget_blocked_count=budget_blocked,
        position_blocked_count=position_blocked,
    )


def _portfolio_capacity_counterfactual_row(
    *,
    variant_name: str,
    ranking_metric: str,
    rows: Sequence[Mapping[str, Any]],
    selected_rows: Sequence[Mapping[str, Any]],
    max_positions: int,
    budget_fraction: float,
    budget_blocked_count: int,
    position_blocked_count: int,
) -> dict[str, Any]:
    selected_ids = {str(row.get("decision_id") or "") for row in selected_rows}
    excluded_rows = [row for row in rows if str(row.get("decision_id") or "") not in selected_ids]
    selected_good = sum(1 for row in selected_rows if str(row.get("outcome_label")) == "1")
    selected_bad = sum(1 for row in selected_rows if str(row.get("outcome_label")) == "0")
    excluded_good = sum(1 for row in excluded_rows if str(row.get("outcome_label")) == "1")
    excluded_bad = sum(1 for row in excluded_rows if str(row.get("outcome_label")) == "0")
    selected_return_total = sum(_float(row.get("realized_return")) for row in selected_rows)
    excluded_return_total = sum(_float(row.get("realized_return")) for row in excluded_rows)
    selected_notional = sum(_planned_notional(row) for row in selected_rows)
    total_budget = _portfolio_total_budget(rows)
    selected_count = len(selected_rows)
    excluded_count = len(excluded_rows)
    return {
        "variant_name": variant_name,
        "ranking_metric": ranking_metric,
        "max_positions": max_positions,
        "budget_fraction": _round(budget_fraction),
        "selected_count": selected_count,
        "excluded_count": excluded_count,
        "selected_good_count": selected_good,
        "selected_bad_count": selected_bad,
        "selected_hit_rate": _round(selected_good / selected_count) if selected_count else None,
        "selected_realized_return_total": _round(selected_return_total),
        "selected_return_per_row": _round(selected_return_total / selected_count) if selected_count else None,
        "excluded_good_count": excluded_good,
        "excluded_bad_count": excluded_bad,
        "excluded_realized_return_total": _round(excluded_return_total),
        "excluded_return_per_row": _round(excluded_return_total / excluded_count) if excluded_count else None,
        "selected_planned_notional_total": _round(selected_notional),
        "budget_used_fraction": _round(selected_notional / total_budget) if total_budget > 0 else None,
        "budget_blocked_count": budget_blocked_count,
        "position_blocked_count": position_blocked_count,
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _portfolio_capacity_counterfactual_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    baseline = next((row for row in rows if row.get("variant_name") == "baseline_selected_all"), None)
    variants = [row for row in rows if row.get("variant_name") != "baseline_selected_all"]
    baseline_row = baseline or {}
    baseline_return = _float(baseline_row.get("selected_realized_return_total")) if baseline else 0.0
    non_empty_variants = [row for row in variants if int(row.get("selected_count") or 0) > 0]
    best_return_variant = max(
        non_empty_variants,
        key=lambda row: _float(row.get("selected_realized_return_total")),
        default=None,
    )
    lowest_bad_rate_variant = min(
        non_empty_variants,
        key=lambda row: (
            _float(row.get("selected_bad_count")) / max(1, int(row.get("selected_count") or 0)),
            str(row.get("variant_name") or ""),
        ),
        default=None,
    )
    best_return_row = best_return_variant or {}
    lowest_bad_rate_row = lowest_bad_rate_variant or {}
    summary = {
        "contract_type": "model_group_portfolio_capacity_counterfactual_summary",
        "variant_count": len(rows),
        "baseline_selected_count": int(baseline_row.get("selected_count") or 0) if baseline else 0,
        "baseline_realized_return_total": _round(baseline_return),
        "best_return_variant": str(best_return_row.get("variant_name") or ""),
        "best_return_total": _round(_float(best_return_row.get("selected_realized_return_total")))
        if best_return_variant
        else None,
        "lowest_bad_rate_variant": str(lowest_bad_rate_row.get("variant_name") or ""),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
        "interpretation": "fixed_replay_capacity_variants_only_not_a_selected_portfolio_policy",
    }
    return {
        "contract_type": "model_group_portfolio_capacity_counterfactual_report",
        "summary": summary,
        "portfolio_capacity_counterfactual_ref": "portfolio_capacity_counterfactual.csv",
        "forbidden_uses": [
            "threshold_selection",
            "portfolio_policy_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _portfolio_replay_rank_score(row: Mapping[str, Any]) -> float:
    scores = _m04_component_scores(row)
    alpha_score = _float(row.get("prediction_score"))
    minimum_alpha = _float(row.get("entry_minimum_alpha_confidence"), default=0.5)
    trade_intensity = _float(scores.get("trade_intensity_score"))
    minimum_trade_intensity = _minimum_trade_intensity(row, scores)
    expected_return = _float(scores.get("expected_return_score"))
    action_direction = _float(scores.get("action_direction_score"))
    return (
        max(0.0, alpha_score - minimum_alpha)
        * max(0.0, trade_intensity - (minimum_trade_intensity if minimum_trade_intensity is not None else DEFAULT_MIN_TRADE_INTENSITY))
        * max(0.0, expected_return)
        * max(0.0, action_direction)
    )


def _planned_notional(row: Mapping[str, Any]) -> float:
    return _float(row.get("planned_position_notional_usd") or row.get("planned_notional_usd"))


def _portfolio_total_budget(rows: Sequence[Mapping[str, Any]]) -> float:
    for row in rows:
        budget = _float(row.get("total_portfolio_notional_usd"))
        if budget > 0:
            return budget
    total = sum(_planned_notional(row) for row in rows)
    return total if total > 0 else 1.0


def _m04_reason_codes(row: Mapping[str, Any]) -> set[str]:
    raw = _m04_diagnostics(row).get("reason_codes") or ()
    if isinstance(raw, str):
        return {item for item in raw.split(";") if item}
    if isinstance(raw, Iterable):
        return {str(item) for item in raw if str(item)}
    return set()


def _materiality_adjusted_action_score(
    scores: Mapping[str, Any],
    *,
    minimum_trade_intensity: float | None = None,
) -> float | None:
    trade_intensity = _finite_float(scores.get("trade_intensity_score"))
    action_confidence = _finite_float(scores.get("action_confidence_score"))
    entry_quality = _finite_float(scores.get("entry_quality_score"))
    downside_risk = _finite_float(scores.get("downside_risk_score"))
    no_trade_probability = _finite_float(scores.get("no_trade_probability_score"))
    if None in (trade_intensity, action_confidence, entry_quality, downside_risk, no_trade_probability):
        return None
    if minimum_trade_intensity is None:
        minimum_trade_intensity = _finite_float(scores.get("minimum_trade_intensity"))
    materiality_gate = _materiality_gate(
        trade_intensity,
        minimum_trade_intensity if minimum_trade_intensity is not None else DEFAULT_MIN_TRADE_INTENSITY,
    )
    return (
        materiality_gate
        * action_confidence
        * entry_quality
        * (1.0 - downside_risk)
        * (1.0 - no_trade_probability)
    )


def _materiality_gate(trade_intensity: float, minimum_trade_intensity: float) -> float:
    if minimum_trade_intensity <= 0.0:
        return 1.0 if trade_intensity > 0.0 else 0.0
    return max(0.0, min(1.0, trade_intensity / minimum_trade_intensity))


def _minimum_trade_intensity(row: Mapping[str, Any], scores: Mapping[str, Any]) -> float | None:
    for value in (
        scores.get("minimum_trade_intensity"),
        row.get("entry_minimum_trade_intensity"),
        row.get("minimum_trade_intensity"),
    ):
        parsed = _finite_float(value)
        if parsed is not None:
            return parsed
    return None


def _m04_variant_status(
    *,
    subset_input_count: int,
    subset_name: str,
    stats: Mapping[str, Any],
) -> tuple[str, list[str]]:
    if subset_input_count > 0 and int(stats["row_count"] or 0) == 0:
        return "missing_component_coverage", [f"{subset_name}_required_variant_inputs_missing_from_replay_rows"]
    if int(stats["row_count"] or 0) < MIN_PARAMETER_FILLED_COUNT:
        return "sample_limited", ["subset_count_below_minimum"]
    if _aligned_useful_supported(
        expected_direction=1,
        return_correlation=stats["return_spearman"],
        return_spread=stats["high_minus_low_return_per_row"],
    ):
        return "aligned_with_realized_return", [f"{subset_name}_return_correlation_and_spread_align"]
    if _aligned_inversion_supported(
        expected_direction=1,
        return_correlation=stats["return_spearman"],
        return_spread=stats["high_minus_low_return_per_row"],
    ):
        return "still_inverted_against_realized_return", [f"{subset_name}_return_correlation_and_spread_inverted"]
    return "weak_or_mixed", [f"{subset_name}_weak_or_mixed_variant_signal"]


def _m05_dte_policy_sensitivity_rows(
    rows: Sequence[Mapping[str, Any]],
    counterfactual_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    row_by_decision_id = {str(row.get("decision_id") or ""): row for row in rows}
    hard_filter_rows = [
        row
        for row in counterfactual_rows
        if row.get("intended_model_trade") is True
        and row.get("execution_expression_state") == "expression_unfilled"
        and row.get("option_feasibility_state") == "hard_filter_zero_eligible"
        and row.get("expression_join_status") == "matched"
    ]
    cases: list[tuple[str, Sequence[Mapping[str, Any]]]] = [
        ("all_hard_filter_zero_eligible", hard_filter_rows),
        (
            "dte_present_hard_filter",
            [row for row in hard_filter_rows if _filter_reason_count(row, "dte_outside_policy_range") > 0],
        ),
        (
            "dte_primary_hard_filter",
            [row for row in hard_filter_rows if row.get("primary_filter_reason") == "dte_outside_policy_range"],
        ),
        (
            "positive_dte_primary_hard_filter",
            [
                row
                for row in hard_filter_rows
                if row.get("primary_filter_reason") == "dte_outside_policy_range"
                and str(row.get("outcome_label")) == "1"
            ],
        ),
    ]
    output: list[dict[str, Any]] = []
    for case_name, case_rows in cases:
        groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
        for counterfactual in case_rows:
            decision_row = row_by_decision_id.get(str(counterfactual.get("decision_id") or ""), {})
            groups[(_selected_expression_type(decision_row), str(counterfactual.get("primary_filter_reason") or ""))].append(
                counterfactual
            )
        if not groups:
            output.append(_m05_dte_policy_sensitivity_row(case_name, "", "", []))
            continue
        for (expression_type, filter_reason), group_rows in sorted(
            groups.items(),
            key=lambda item: (-len(item[1]), item[0]),
        ):
            output.append(_m05_dte_policy_sensitivity_row(case_name, expression_type, filter_reason, group_rows))
    return output


def _m05_dte_policy_sensitivity_row(
    case_name: str,
    expression_type: str,
    filter_reason: str,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    dte_fail_counts = [_filter_reason_count(row, "dte_outside_policy_range") for row in rows]
    non_dte_fail_counts = [_non_dte_filter_count(row) for row in rows]
    before_filter_counts = [
        _float(row.get("candidate_count_before_filter"))
        for row in rows
        if row.get("candidate_count_before_filter") not in (None, "")
    ]
    status, reason_codes = _m05_dte_policy_sensitivity_status(
        rows=rows,
        dte_fail_counts=dte_fail_counts,
        non_dte_fail_counts=non_dte_fail_counts,
    )
    row_count = len(rows)
    positive_rows = [row for row in rows if str(row.get("outcome_label")) == "1"]
    dte_share_values = []
    for dte_count, non_dte_count in zip(dte_fail_counts, non_dte_fail_counts, strict=True):
        total = dte_count + non_dte_count
        if total > 0:
            dte_share_values.append(dte_count / total)
    return {
        "sensitivity_case": case_name,
        "selected_expression_type": expression_type,
        "primary_filter_reason": filter_reason,
        "diagnostic_status": status,
        "reason_codes": ";".join(reason_codes),
        "row_count": row_count,
        "positive_label_count": len(positive_rows),
        "label_rate": _round(len(positive_rows) / row_count) if row_count else None,
        "underlying_return_total": _round(sum(_float(row.get("underlying_return")) for row in rows)),
        "positive_underlying_return_total": _round(sum(_float(row.get("underlying_return")) for row in positive_rows)),
        "candidate_count_before_filter_mean": _round(_mean(before_filter_counts)),
        "candidate_count_after_filter_mean": _counterfactual_metric_mean(rows, "candidate_count_after_filter"),
        "eligible_candidate_count_mean": _counterfactual_metric_mean(rows, "eligible_candidate_count"),
        "dte_fail_count_mean": _round(_mean(float(value) for value in dte_fail_counts)),
        "non_dte_fail_count_mean": _round(_mean(float(value) for value in non_dte_fail_counts)),
        "dte_fail_share_mean": _round(_mean(dte_share_values)),
        "top_contract_fit_score_mean": _counterfactual_metric_mean(rows, "top_contract_fit_score"),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _m05_dte_policy_sensitivity_status(
    *,
    rows: Sequence[Mapping[str, Any]],
    dte_fail_counts: Sequence[int],
    non_dte_fail_counts: Sequence[int],
) -> tuple[str, list[str]]:
    if len(rows) < MIN_PARAMETER_FILLED_COUNT:
        return "sample_limited", ["subset_count_below_minimum"]
    positive_count = sum(1 for row in rows if str(row.get("outcome_label")) == "1")
    dte_present_count = sum(1 for count in dte_fail_counts if count > 0)
    if positive_count <= 0 or dte_present_count <= 0:
        return "not_dte_driven", ["no_positive_dte_filtered_rows"]
    overlapping_count = sum(1 for count in non_dte_fail_counts if count > 0)
    if overlapping_count >= len(rows) * 0.75:
        return "dte_overlaps_other_filters", ["dte_failures_mostly_overlap_other_filter_failures"]
    return "dte_policy_pressure_supported", ["positive_rows_with_dte_hard_filter_pressure"]


def _filter_reason_count(row: Mapping[str, Any], reason_code: str) -> int:
    counts = _counterfactual_filter_reason_counts(row)
    return int(counts.get(reason_code) or 0)


def _non_dte_filter_count(row: Mapping[str, Any]) -> int:
    counts = _counterfactual_filter_reason_counts(row)
    return sum(count for reason, count in counts.items() if reason != "dte_outside_policy_range")


def _counterfactual_filter_reason_counts(row: Mapping[str, Any]) -> dict[str, int]:
    raw = row.get("filter_reason_counts")
    if isinstance(raw, Mapping):
        return {str(reason): int(count) for reason, count in raw.items()}
    try:
        parsed = json.loads(str(raw or "{}"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, Mapping):
        return {}
    output: dict[str, int] = {}
    for reason, count in parsed.items():
        try:
            output[str(reason)] = int(count)
        except (TypeError, ValueError):
            continue
    return output


def _m05_hard_filter_overlap_rows(
    rows: Sequence[Mapping[str, Any]],
    counterfactual_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    row_by_decision_id = {str(row.get("decision_id") or ""): row for row in rows}
    hard_filter_rows = [
        row
        for row in counterfactual_rows
        if row.get("intended_model_trade") is True
        and row.get("execution_expression_state") == "expression_unfilled"
        and row.get("option_feasibility_state") == "hard_filter_zero_eligible"
        and row.get("expression_join_status") == "matched"
    ]
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for counterfactual in hard_filter_rows:
        decision_row = row_by_decision_id.get(str(counterfactual.get("decision_id") or ""), {})
        reason_set = tuple(sorted(_counterfactual_filter_reason_counts(counterfactual)))
        reason_set_text = ";".join(reason_set)
        key = (
            _hard_filter_overlap_group(reason_set),
            _selected_expression_type(decision_row),
            str(counterfactual.get("primary_filter_reason") or ""),
            reason_set_text,
        )
        groups[key].append(counterfactual)
    if not groups:
        return [
            _m05_hard_filter_overlap_row(
                overlap_group="no_hard_filter_zero_eligible_rows",
                expression_type="",
                primary_filter_reason="",
                filter_reason_set="",
                rows=[],
            )
        ]
    return [
        _m05_hard_filter_overlap_row(
            overlap_group=overlap_group,
            expression_type=expression_type,
            primary_filter_reason=primary_filter_reason,
            filter_reason_set=filter_reason_set,
            rows=group_rows,
        )
        for (overlap_group, expression_type, primary_filter_reason, filter_reason_set), group_rows in sorted(
            groups.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )
    ]


def _hard_filter_overlap_group(reason_set: Sequence[str]) -> str:
    reasons = set(reason_set)
    if not reasons:
        return "missing_filter_reason"
    if reasons == {"dte_outside_policy_range"}:
        return "dte_isolated"
    if "dte_outside_policy_range" in reasons:
        return "dte_overlaps_other_filters"
    if len(reasons) == 1:
        return "single_non_dte_filter"
    return "multi_non_dte_filter_overlap"


def _m05_hard_filter_overlap_row(
    *,
    overlap_group: str,
    expression_type: str,
    primary_filter_reason: str,
    filter_reason_set: str,
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    row_count = len(rows)
    positive_rows = [row for row in rows if str(row.get("outcome_label")) == "1"]
    return {
        "overlap_group": overlap_group,
        "selected_expression_type": expression_type,
        "primary_filter_reason": primary_filter_reason,
        "filter_reason_set": filter_reason_set,
        "filter_reason_count": len([reason for reason in filter_reason_set.split(";") if reason]),
        "row_count": row_count,
        "positive_label_count": len(positive_rows),
        "label_rate": _round(len(positive_rows) / row_count) if row_count else None,
        "underlying_return_total": _round(sum(_float(row.get("underlying_return")) for row in rows)),
        "positive_underlying_return_total": _round(sum(_float(row.get("underlying_return")) for row in positive_rows)),
        "candidate_count_before_filter_mean": _counterfactual_metric_mean(rows, "candidate_count_before_filter"),
        "candidate_count_after_filter_mean": _counterfactual_metric_mean(rows, "candidate_count_after_filter"),
        "eligible_candidate_count_mean": _counterfactual_metric_mean(rows, "eligible_candidate_count"),
        "top_contract_fit_score_mean": _counterfactual_metric_mean(rows, "top_contract_fit_score"),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }


def _m04_m05_mechanism_review_report(
    *,
    m04_component_rows: Sequence[Mapping[str, Any]],
    m05_selection_rows: Sequence[Mapping[str, Any]],
    m04_variant_rows: Sequence[Mapping[str, Any]],
    m05_dte_sensitivity_rows: Sequence[Mapping[str, Any]],
    m05_hard_filter_overlap_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    m04_inverted = [
        str(row.get("component_name"))
        for row in m04_component_rows
        if row.get("subset_name") == "m04_open_m05_pass_filled"
        and row.get("diagnostic_status") == "inverted_against_expected_direction"
    ]
    m05_positive_unfilled = [
        row
        for row in m05_selection_rows
        if row.get("m04_state") == "open_long/long"
        and row.get("m05_state") == "alpha_passed"
        and row.get("execution_expression_state") == "expression_unfilled"
        and int(row.get("positive_label_count") or 0) > 0
    ]
    hard_filter_positive_unfilled = [
        row for row in m05_positive_unfilled if row.get("option_feasibility_state") == "hard_filter_zero_eligible"
    ]
    aligned_variants = [
        str(row.get("variant_name"))
        for row in m04_variant_rows
        if row.get("subset_name") == "m04_open_m05_pass_filled"
        and row.get("diagnostic_status") == "aligned_with_realized_return"
    ]
    still_inverted_variants = [
        str(row.get("variant_name"))
        for row in m04_variant_rows
        if row.get("subset_name") == "m04_open_m05_pass_filled"
        and row.get("diagnostic_status") == "still_inverted_against_realized_return"
    ]
    dte_primary_rows = [
        row
        for row in m05_dte_sensitivity_rows
        if row.get("sensitivity_case") == "dte_primary_hard_filter"
        and row.get("primary_filter_reason") == "dte_outside_policy_range"
    ]
    dte_positive_label_count = sum(int(row.get("positive_label_count") or 0) for row in dte_primary_rows)
    summary = {
        "contract_type": "model_group_m04_m05_mechanism_review_summary",
        "m04_open_filled_inverted_components": sorted(set(m04_inverted)),
        "m04_open_filled_inverted_component_count": len(set(m04_inverted)),
        "m04_open_filled_aligned_variants": sorted(set(aligned_variants)),
        "m04_open_filled_aligned_variant_count": len(set(aligned_variants)),
        "m04_open_filled_still_inverted_variants": sorted(set(still_inverted_variants)),
        "m04_open_filled_still_inverted_variant_count": len(set(still_inverted_variants)),
        "m05_open_pass_positive_unfilled_group_count": len(m05_positive_unfilled),
        "m05_hard_filter_positive_unfilled_group_count": len(hard_filter_positive_unfilled),
        "m05_dte_primary_positive_label_count": dte_positive_label_count,
        "m05_hard_filter_overlap_counts": _m05_hard_filter_overlap_counts(m05_hard_filter_overlap_rows),
        "m05_dte_isolated_positive_label_count": _m05_hard_filter_overlap_positive_count(
            m05_hard_filter_overlap_rows,
            overlap_group="dte_isolated",
        ),
        "m05_dte_overlap_positive_label_count": _m05_hard_filter_overlap_positive_count(
            m05_hard_filter_overlap_rows,
            overlap_group="dte_overlaps_other_filters",
        ),
        "primary_followup": _m04_m05_primary_followup(m04_inverted, hard_filter_positive_unfilled),
        "threshold_selection_performed": False,
        "retraining_performed": False,
        "fixed_input_only": True,
    }
    return {
        "contract_type": "model_group_m04_m05_mechanism_review_report",
        "summary": summary,
        "m04_component_diagnostics_ref": "m04_component_diagnostics.csv",
        "m05_selection_mechanics_ref": "m05_selection_mechanics.csv",
        "m04_variant_counterfactual_ref": "m04_variant_counterfactual.csv",
        "m05_dte_policy_sensitivity_ref": "m05_dte_policy_sensitivity.csv",
        "m05_hard_filter_overlap_ref": "m05_hard_filter_overlap.csv",
        "review_role": "fixed_replay_m04_m05_mechanism_triage_only",
        "forbidden_uses": [
            "causal_feature_importance_claim",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
    }


def _m05_hard_filter_overlap_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts[str(row.get("overlap_group") or "unknown")] += int(row.get("row_count") or 0)
    return dict(counts)


def _m05_hard_filter_overlap_positive_count(
    rows: Sequence[Mapping[str, Any]],
    *,
    overlap_group: str,
) -> int:
    return sum(
        int(row.get("positive_label_count") or 0)
        for row in rows
        if row.get("overlap_group") == overlap_group
    )


def _m04_m05_primary_followup(
    m04_inverted_components: Sequence[str],
    hard_filter_positive_unfilled_rows: Sequence[Mapping[str, Any]],
) -> str:
    if len(set(m04_inverted_components)) >= 2 and hard_filter_positive_unfilled_rows:
        return "m04_component_and_m05_filter_joint_review"
    if len(set(m04_inverted_components)) >= 2:
        return "m04_component_weight_or_direction_review"
    if hard_filter_positive_unfilled_rows:
        return "m05_option_expression_filter_review"
    return "more_fixed_replay_evidence_required"


def _spearman(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_ranks = _ranks(left)
    right_ranks = _ranks(right)
    return _pearson(left_ranks, right_ranks)


def _ranks(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(indexed):
        end = index + 1
        while end < len(indexed) and indexed[end][1] == indexed[index][1]:
            end += 1
        average_rank = (index + end + 1) / 2
        for original_index, _value in indexed[index:end]:
            ranks[original_index] = average_rank
        index = end
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((lvalue - left_mean) * (rvalue - right_mean) for lvalue, rvalue in zip(left, right, strict=True))
    left_denominator = sum((value - left_mean) ** 2 for value in left)
    right_denominator = sum((value - right_mean) ** 2 for value in right)
    denominator = (left_denominator * right_denominator) ** 0.5
    if denominator == 0:
        return None
    return numerator / denominator


def _finite_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def _counterfactual_gate_sweep_summary(path: Path | None) -> dict[str, Any]:
    rows = _load_csv_rows(path)
    if not rows:
        return {
            "source_status": "missing",
            "row_count": 0,
            "threshold_selection_performed": False,
            "sweep_role": "fixed_diagnostic_only",
        }
    diagnostic_rows = []
    for row in rows:
        diagnostic_rows.append(
            {
                "minimum_entry_alpha_confidence": _round(_float(row.get("minimum_entry_alpha_confidence"))),
                "minimum_trade_intensity": _round(_float(row.get("minimum_trade_intensity"))),
                "m05_signal_count": _int(row.get("m05_signal_count")),
                "m05_selected_contract_count": _int(row.get("m05_selected_contract_count")),
                "m05_unfilled_count": _int(row.get("m05_unfilled_count")),
                "new_selected_vs_baseline_count": _int(row.get("new_selected_vs_baseline_count")),
                "new_selected_underlying_return_total": _round(_float(row.get("new_selected_underlying_return_total"))),
                "new_selected_underlying_return_average": _round(_float(row.get("new_selected_underlying_return_average"))),
                "new_selected_positive_label_count": _int(row.get("new_selected_positive_label_count")),
                "new_selected_negative_label_count": _int(row.get("new_selected_negative_label_count")),
            }
        )
    return {
        "source_status": "available",
        "row_count": len(rows),
        "threshold_selection_performed": False,
        "sweep_role": "fixed_diagnostic_only",
        "max_new_selected_vs_baseline_count": max(row["new_selected_vs_baseline_count"] for row in diagnostic_rows),
        "rows": diagnostic_rows,
    }


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _high_score_tail_loss_attribution_packet(
    *,
    rows: Sequence[Mapping[str, Any]],
    counterfactual_summary: Mapping[str, Any],
    decision_rows_path: Path,
    m05_unfilled_diagnostics_path: Path | None,
    output_dir: Path,
    high_score_threshold: float,
    now_utc: datetime,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    loss_rows = [
        row
        for row in filled
        if _float(row.get("prediction_score")) >= high_score_threshold and _float(row.get("realized_return")) < 0
    ]
    control_rows = [
        row
        for row in filled
        if _float(row.get("prediction_score")) >= high_score_threshold and _float(row.get("realized_return")) >= 0
    ]
    matched_rows = [_matched_tail_loss_row(loss_row, control_rows) for loss_row in loss_rows]
    matched_comparison_count = _matched_comparison_count(matched_rows)
    classification_summary = _tail_loss_classification_summary(
        filled=filled,
        loss_rows=loss_rows,
        control_rows=control_rows,
        matched_rows=matched_rows,
        counterfactual_summary=counterfactual_summary,
    )
    requires_evidence_summary = _requires_evidence_summary(classification_summary)
    packet = {
        "contract_type": "model_group_high_score_filled_tail_loss_attribution_packet",
        "generated_at_utc": now_utc.isoformat(),
        "source_scope": {
            "decision_rows_ref": str(decision_rows_path),
            "m05_unfilled_diagnostics_ref": str(m05_unfilled_diagnostics_path) if m05_unfilled_diagnostics_path else "",
            "fixed_input_only": True,
            "provider_call_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
            "sql_mutation_performed": False,
            "storage_source_mutation_performed": False,
            "model_activation_performed": False,
            "active_model_config_written": False,
        },
        "cohort_definition": {
            "high_score_threshold": high_score_threshold,
            "loss_predicate": "fill_status=simulated_filled and prediction_score>=threshold and realized_return<0",
            "control_predicate": "fill_status=simulated_filled and prediction_score>=threshold and realized_return>=0",
        },
        "headline": {
            "filled_count": len(filled),
            "high_score_filled_loss_count": len(loss_rows),
            "high_score_filled_control_count": len(control_rows),
            "filled_good_bad_score_gap": counterfactual_summary.get("filled_good_bad_score_gap"),
            "execution_connection_mismatch_count": counterfactual_summary.get("execution_connection_mismatch_count"),
            "sample_sufficiency_status": (counterfactual_summary.get("sample_sufficiency_status") or {}).get("status"),
            "matched_comparison_count": matched_comparison_count,
            "tail_loss_row_count": len(matched_rows),
        },
        "classification_summary": classification_summary,
        "requires_evidence_summary": requires_evidence_summary,
        "matched_comparison_rows_ref": str(output_dir / "high_score_filled_tail_loss_matches.csv"),
        "implementation_limits": [
            "No bid/ask, order-book depth, IV, Greeks, or venue fill-priority fields are available in replay decision rows.",
            "No point-in-time feature trace timestamps are available for feature-timing or leakage attribution.",
            "No event/regime overlay evidence is consumed by this packet; event miss classification remains replay-review event-attribution-owned.",
            "Matched controls are nearest fixed-input comparisons, not causal counterfactual trades.",
        ],
    }
    return packet, matched_rows


def _matched_tail_loss_row(loss_row: Mapping[str, Any], control_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    control_row, match_quality = _match_control_row(loss_row, control_rows)
    loss_contract = _parse_option_contract(str(loss_row.get("selected_option_contract_ref") or ""))
    control_contract = _parse_option_contract(str((control_row or {}).get("selected_option_contract_ref") or ""))
    loss_m04 = _m04_diagnostics(loss_row)
    control_m04 = _m04_diagnostics(control_row or {})
    loss_scores = loss_m04.get("dominant_horizon_scores") or {}
    control_scores = control_m04.get("dominant_horizon_scores") or {}
    loss_return = _float(loss_row.get("realized_return"))
    control_return = _float((control_row or {}).get("realized_return"))
    label_return_disagreement = _label_return_disagreement(loss_row) or (
        _label_return_disagreement(control_row or {}) if control_row else False
    )
    primary_failure_class, secondary_failure_classes, requires_evidence_codes = _tail_loss_row_classification(
        loss_row=loss_row,
        control_row=control_row,
        loss_contract=loss_contract,
        control_contract=control_contract,
        label_return_disagreement=label_return_disagreement,
    )
    return {
        "loss_decision_id": str(loss_row.get("decision_id") or ""),
        "control_decision_id": str((control_row or {}).get("decision_id") or ""),
        "loss_timestamp": str(loss_row.get("timestamp") or ""),
        "control_timestamp": str((control_row or {}).get("timestamp") or ""),
        "match_quality": match_quality,
        "loss_prediction_score": _round(_float(loss_row.get("prediction_score"))),
        "control_prediction_score": _round(_float((control_row or {}).get("prediction_score"))),
        "score_delta": _round(_float(loss_row.get("prediction_score")) - _float((control_row or {}).get("prediction_score"))),
        "loss_m05_alpha_score": _round(_float(_m05_diagnostics(loss_row).get("resolved_alpha_score"))),
        "control_m05_alpha_score": _round(_float(_m05_diagnostics(control_row or {}).get("resolved_alpha_score"))),
        "trade_intensity_delta": _round(_float(loss_scores.get("trade_intensity_score")) - _float(control_scores.get("trade_intensity_score"))),
        "loss_realized_return": _round(loss_return),
        "control_realized_return": _round(control_return),
        "return_delta": _round(loss_return - control_return),
        "loss_outcome_label": _text(loss_row.get("outcome_label")),
        "control_outcome_label": _text((control_row or {}).get("outcome_label")),
        "loss_contract_ref": str(loss_row.get("selected_option_contract_ref") or ""),
        "control_contract_ref": str((control_row or {}).get("selected_option_contract_ref") or ""),
        "loss_contract_underlying": loss_contract.get("underlying", ""),
        "loss_contract_expiry": loss_contract.get("expiry", ""),
        "loss_contract_option_side": loss_contract.get("option_side", ""),
        "loss_contract_strike": loss_contract.get("strike", ""),
        "loss_contract_dte": _contract_dte(loss_row, loss_contract),
        "control_contract_underlying": control_contract.get("underlying", ""),
        "control_contract_expiry": control_contract.get("expiry", ""),
        "control_contract_option_side": control_contract.get("option_side", ""),
        "control_contract_strike": control_contract.get("strike", ""),
        "control_contract_dte": _contract_dte(control_row or {}, control_contract),
        "same_target_ref": str(loss_row.get("target_ref") or "") == str((control_row or {}).get("target_ref") or ""),
        "same_m04_state": _m04_state(loss_row) == _m04_state(control_row or {}),
        "same_m05_state": _m05_state(loss_row) == _m05_state(control_row or {}),
        "same_contract_family": _same_contract_family(loss_contract, control_contract),
        "label_return_disagreement": label_return_disagreement,
        "primary_failure_class": primary_failure_class,
        "secondary_failure_classes": ";".join(secondary_failure_classes),
        "requires_evidence_codes": ";".join(requires_evidence_codes),
    }


def _match_control_row(
    loss_row: Mapping[str, Any],
    control_rows: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, str]:
    if not control_rows:
        return None, "unmatched"
    loss_contract = _parse_option_contract(str(loss_row.get("selected_option_contract_ref") or ""))
    loss_month = str(loss_row.get("timestamp") or "")[:7]

    def score(control_row: Mapping[str, Any]) -> tuple[int, float, int, str]:
        control_contract = _parse_option_contract(str(control_row.get("selected_option_contract_ref") or ""))
        same_target = str(loss_row.get("target_ref") or "") == str(control_row.get("target_ref") or "")
        same_m04 = _m04_state(loss_row) == _m04_state(control_row)
        same_m05 = _m05_state(loss_row) == _m05_state(control_row)
        same_score_bin = _score_bin(loss_row) == _score_bin(control_row)
        same_month = loss_month == str(control_row.get("timestamp") or "")[:7]
        same_contract_family = _same_contract_family(loss_contract, control_contract)
        quality_points = sum((same_target, same_m04, same_m05, same_score_bin, same_month, same_contract_family))
        score_distance = abs(_float(loss_row.get("prediction_score")) - _float(control_row.get("prediction_score")))
        time_distance = abs(_timestamp_sort_value(loss_row) - _timestamp_sort_value(control_row))
        return (-quality_points, score_distance, time_distance, str(control_row.get("decision_id") or ""))

    best = sorted(control_rows, key=score)[0]
    if str(loss_row.get("target_ref") or "") == str(best.get("target_ref") or "") and loss_month == str(best.get("timestamp") or "")[:7]:
        quality = "same_target_month_nearest_score"
    elif str(loss_row.get("target_ref") or "") == str(best.get("target_ref") or ""):
        quality = "same_target_nearest_score"
    elif _m04_state(loss_row) == _m04_state(best) and _m05_state(loss_row) == _m05_state(best):
        quality = "same_layer_state_only"
    else:
        quality = "weak_nearest_score"
    return best, quality


def _timestamp_sort_value(row: Mapping[str, Any]) -> int:
    text = str(row.get("timestamp") or "")
    digits = "".join(char for char in text if char.isdigit())
    try:
        return int(digits[:14])
    except ValueError:
        return 0


def _parse_option_contract(contract_ref: str) -> dict[str, str]:
    parts = contract_ref.split("_")
    if len(parts) < 4:
        return {}
    return {
        "underlying": parts[0],
        "expiry": parts[1],
        "option_side": parts[2],
        "strike": parts[3],
    }


def _contract_dte(row: Mapping[str, Any], contract: Mapping[str, str]) -> int | None:
    expiry = contract.get("expiry")
    timestamp = str(row.get("timestamp") or "")[:10]
    if not expiry or not timestamp:
        return None
    try:
        expiry_date = datetime.fromisoformat(expiry).date()
        timestamp_date = datetime.fromisoformat(timestamp).date()
    except ValueError:
        return None
    return (expiry_date - timestamp_date).days


def _same_contract_family(left: Mapping[str, str], right: Mapping[str, str]) -> bool:
    if not left or not right:
        return False
    return left.get("underlying") == right.get("underlying") and left.get("option_side") == right.get("option_side")


def _label_return_disagreement(row: Mapping[str, Any]) -> bool:
    label = _text(row.get("outcome_label"))
    realized_return = _float(row.get("realized_return"))
    return (label == "1" and realized_return < 0) or (label == "0" and realized_return > 0)


def _tail_loss_row_classification(
    *,
    loss_row: Mapping[str, Any],
    control_row: Mapping[str, Any] | None,
    loss_contract: Mapping[str, str],
    control_contract: Mapping[str, str],
    label_return_disagreement: bool,
) -> tuple[str, list[str], list[str]]:
    secondary: list[str] = ["model_overconfidence"]
    requires = [
        "feature_timing_or_leakage_requires_pit_feature_trace",
        "liquidity_spread_fill_realism_requires_bid_ask_depth_and_fill_model",
        "regime_event_miss_requires_m03_event_state_trace",
    ]
    if label_return_disagreement:
        return "label_target_definition", secondary, requires
    if _contract_dte(loss_row, loss_contract) is None:
        secondary.append("option_selection_mechanics_unknown_contract_parse")
    elif _contract_dte(loss_row, loss_contract) is not None and _contract_dte(loss_row, loss_contract) <= 7:
        secondary.append("short_dte_option_selection_mechanics")
    if control_row and _same_contract_family(loss_contract, control_contract):
        secondary.append("same_contract_family_control_available")
    return "model_overconfidence", secondary, requires


def _tail_loss_classification_summary(
    *,
    filled: Sequence[Mapping[str, Any]],
    loss_rows: Sequence[Mapping[str, Any]],
    control_rows: Sequence[Mapping[str, Any]],
    matched_rows: Sequence[Mapping[str, Any]],
    counterfactual_summary: Mapping[str, Any],
) -> dict[str, Any]:
    score_gap = counterfactual_summary.get("filled_good_bad_score_gap")
    sample_status = (counterfactual_summary.get("sample_sufficiency_status") or {}).get("status")
    execution_mismatch_count = int(counterfactual_summary.get("execution_connection_mismatch_count") or 0)
    label_disagreements = sum(1 for row in matched_rows if row.get("label_return_disagreement") is True)
    short_dte_losses = sum(
        1
        for row in matched_rows
        if row.get("loss_contract_dte") not in (None, "") and _int(row.get("loss_contract_dte")) <= 7
    )
    classification = {
        "label_target_definition": {
            "status": "supported" if label_disagreements else "not_supported_by_current_evidence",
            "evidence_count": label_disagreements,
        },
        "feature_timing_or_leakage": {
            "status": "unknown_requires_evidence",
            "requires_evidence_codes": ["pit_feature_trace", "feature_generation_clock", "leakage_check_rows"],
        },
        "data_insufficiency": {
            "status": "supported" if sample_status == "sample_limited" else "not_supported_by_current_evidence",
            "reason_codes": (counterfactual_summary.get("sample_sufficiency_status") or {}).get("reason_codes", []),
        },
        "option_selection_mechanics": {
            "status": "weakly_supported" if short_dte_losses else "unknown_requires_evidence",
            "high_score_loss_short_dte_count": short_dte_losses,
        },
        "liquidity_spread_fill_realism": {
            "status": "unknown_requires_evidence",
            "requires_evidence_codes": ["bid_ask_spread", "quote_depth", "slippage_model", "partial_fill_simulation"],
        },
        "regime_event_miss": {
            "status": "unknown_requires_evidence",
            "requires_evidence_codes": ["m03_event_state_trace", "regime_state", "co_event_controls"],
        },
        "model_overconfidence": {
            "status": "supported"
            if loss_rows and score_gap is not None and abs(float(score_gap)) < 0.02
            else "not_supported_by_current_evidence",
            "high_score_loss_count": len(loss_rows),
            "filled_good_bad_score_gap": score_gap,
        },
        "promotion_gate_weakness": {
            "status": "supported" if loss_rows and sample_status == "sample_limited" else "not_supported_by_current_evidence",
            "reason_codes": ["high_score_losses_under_sample_limited_evidence"] if loss_rows and sample_status == "sample_limited" else [],
        },
        "execution_replay_artifact": {
            "status": "supported" if execution_mismatch_count else "not_supported_by_current_evidence",
            "execution_connection_mismatch_count": execution_mismatch_count,
        },
    }
    classification["cohort_counts"] = {
        "filled_count": len(filled),
        "high_score_filled_loss_count": len(loss_rows),
        "high_score_filled_control_count": len(control_rows),
        "matched_comparison_count": _matched_comparison_count(matched_rows),
        "tail_loss_row_count": len(matched_rows),
    }
    classification["match_quality_counts"] = dict(Counter(str(row.get("match_quality") or "") for row in matched_rows))
    classification["primary_failure_class_counts"] = dict(
        Counter(str(row.get("primary_failure_class") or "") for row in matched_rows)
    )
    return classification


def _matched_comparison_count(rows: Sequence[Mapping[str, Any]]) -> int:
    return sum(1 for row in rows if row.get("match_quality") != "unmatched" and row.get("control_decision_id"))


def _requires_evidence_summary(classification_summary: Mapping[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name, item in classification_summary.items():
        if not isinstance(item, Mapping):
            continue
        if item.get("status") == "unknown_requires_evidence":
            output[name] = item.get("requires_evidence_codes", [])
    return output


def _verdict(
    *,
    rows: Sequence[Mapping[str, Any]],
    cohort_rows: Sequence[Mapping[str, Any]],
    score_bin_rows: Sequence[Mapping[str, Any]],
    counterfactual_summary: Mapping[str, Any],
) -> dict[str, Any]:
    filled = [row for row in rows if row.get("fill_status") == "simulated_filled"]
    filled_good = [row for row in filled if str(row.get("outcome_label")) == "1"]
    filled_bad = [row for row in filled if str(row.get("outcome_label")) == "0"]
    bad_score = _mean(_float(row.get("prediction_score")) for row in filled_bad)
    good_score = _mean(_float(row.get("prediction_score")) for row in filled_good)
    negative_score_bins = [
        row["score_bin"]
        for row in score_bin_rows
        if row.get("net_return_total") is not None and float(row["net_return_total"]) < 0
    ]
    return {
        "first_visible_problem_layer": "M04",
        "fault_surface": "M04/M05 boundary",
        "root_cause_status": _root_cause_status(counterfactual_summary),
        "supporting_observations": [
            "M01/M02/3 replay coverage is not contradicted by this diagnostic; the first trade-universe selection split appears at M04.",
            "M04 open_long plus M05 alpha-passed rows split between filled contracts and expression-unfilled rows.",
            "M05 alpha score does not materially separate filled good from filled bad rows.",
            "Filled score bins are non-monotonic, so alpha ranking alone is not sufficient for promotion.",
        ],
        "filled_good_mean_prediction_score": _round(good_score),
        "filled_bad_mean_prediction_score": _round(bad_score),
        "negative_filled_score_bins": negative_score_bins,
        "recommended_next_step": (
            "Run bounded counterfactual attribution over existing replay inputs: M04 materiality/intensity variants, "
            "M05 expression feasibility on M04-open/M05-alpha-passed unfilled rows, and tail-loss slices by option contract features."
        ),
    }


def _root_cause_status(counterfactual_summary: Mapping[str, Any]) -> str:
    assessment = counterfactual_summary.get("root_cause_assessment") or {}
    supported = [
        cause
        for cause in ("data_insufficiency", "execution_connection_failure", "model_mechanism_defect")
        if ((assessment.get(cause) or {}).get("status") or "") == "supported"
    ]
    if len(supported) > 1:
        return "multiple_root_causes_supported:" + ",".join(supported)
    if supported:
        return supported[0] + "_supported"
    return "not_isolated"


def _mean(values: Iterable[float]) -> float | None:
    values_tuple = tuple(values)
    if not values_tuple:
        return None
    return sum(values_tuple) / len(values_tuple)


def _median(values: Iterable[float]) -> float | None:
    values_tuple = tuple(sorted(values))
    if not values_tuple:
        return None
    midpoint = len(values_tuple) // 2
    if len(values_tuple) % 2:
        return values_tuple[midpoint]
    return (values_tuple[midpoint - 1] + values_tuple[midpoint]) / 2


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], *, fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        path.write_text("", encoding="utf-8")
        return
    output_fieldnames: list[str] = list(fieldnames or [])
    for row in rows:
        for key in row:
            if key not in output_fieldnames:
                output_fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-rows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--replay-receipt", type=Path)
    parser.add_argument("--promotion-review", type=Path)
    parser.add_argument("--m05-unfilled-diagnostics", type=Path)
    parser.add_argument("--counterfactual-gate-sweep", type=Path)
    parser.add_argument("--target-selection-universe-metrics", type=Path)
    parser.add_argument("--model-candidate-selection-trace", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--tail-row-limit", type=int, default=DEFAULT_TAIL_ROW_LIMIT)
    parser.add_argument("--high-score-threshold", type=float, default=DEFAULT_HIGH_SCORE_THRESHOLD)
    args = parser.parse_args(argv)
    report = build_model_group_layer_attribution(
        decision_rows_path=args.decision_rows,
        output_dir=args.output_dir,
        replay_receipt_path=args.replay_receipt,
        promotion_review_path=args.promotion_review,
        m05_unfilled_diagnostics_path=args.m05_unfilled_diagnostics,
        counterfactual_gate_sweep_path=args.counterfactual_gate_sweep,
        target_selection_universe_metrics_path=args.target_selection_universe_metrics,
        model_candidate_selection_trace_path=args.model_candidate_selection_trace,
        run_id=args.run_id,
        tail_row_limit=args.tail_row_limit,
        high_score_threshold=args.high_score_threshold,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

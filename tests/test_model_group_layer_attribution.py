from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.model_group_layer_attribution import build_model_group_layer_attribution


class ModelGroupLayerAttributionTests(unittest.TestCase):
    def test_builds_m04_m05_boundary_report_without_mutation_flags(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = [
                _row("r1", "accepted", "simulated_filled", 1, 0.82, 0.4, "open_long", "long", "passed", "listed_option_contract"),
                _row("r2", "accepted", "simulated_filled", 0, 0.83, -0.6, "open_long", "long", "passed", "listed_option_contract"),
                _row("r3", "suitable", "simulated_rejected", 1, 0.81, 0.0, "open_long", "long", "passed", "option_expression_unfilled"),
                _row("r4", "rejected", "simulated_rejected", 1, 0.79, 0.0, "no_trade", "none", "passed", ""),
                _row(
                    "r5",
                    "rejected",
                    "simulated_rejected",
                    0,
                    0.42,
                    0.0,
                    "no_trade",
                    "none",
                    "below_entry_threshold",
                    "",
                ),
                _row("r6", "suitable", "simulated_rejected", 1, 0.88, 0.0, "open_long", "long", "passed", "option_expression_unfilled"),
            ]
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            m05_path = tmp / "m05_unfilled.csv"
            with m05_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "timestamp",
                        "outcome_label",
                        "underlying_return",
                        "asset_expression_route",
                        "selected_contract_ref",
                        "candidate_count_before_filter",
                        "candidate_count_after_filter",
                        "eligible_candidate_count",
                        "top_contract_fit_score",
                        "plan_reason_codes",
                        "fail_reason_counts",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": "2021-01-03T16:00:00-05:00",
                        "outcome_label": "1",
                        "underlying_return": "0.02",
                        "asset_expression_route": "option_expression_unfilled",
                        "selected_contract_ref": "",
                        "candidate_count_before_filter": "4",
                        "candidate_count_after_filter": "0",
                        "eligible_candidate_count": "0",
                        "top_contract_fit_score": "0.12",
                        "plan_reason_codes": "no_contract_passed_hard_filter;dte_outside_policy_range",
                        "fail_reason_counts": "{'dte_outside_policy_range': 3, 'delta_outside_policy_range': 2}",
                    }
                )
                writer.writerow(
                    {
                        "timestamp": "2021-01-06T16:00:00-05:00",
                        "outcome_label": "1",
                        "underlying_return": "0.03",
                        "asset_expression_route": "option_expression_unfilled",
                        "selected_contract_ref": "AAPL_2021-01-08_C_130",
                        "candidate_count_before_filter": "5",
                        "candidate_count_after_filter": "1",
                        "eligible_candidate_count": "1",
                        "top_contract_fit_score": "0.72",
                        "plan_reason_codes": "point_in_time_contract_candidate_selected",
                        "fail_reason_counts": "{}",
                    }
                )
            gate_sweep_path = tmp / "counterfactual_gate_sweep.csv"
            with gate_sweep_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "minimum_entry_alpha_confidence",
                        "minimum_trade_intensity",
                        "m05_signal_count",
                        "m05_selected_contract_count",
                        "m05_unfilled_count",
                        "new_selected_vs_baseline_count",
                        "new_selected_underlying_return_total",
                        "new_selected_underlying_return_average",
                        "new_selected_positive_label_count",
                        "new_selected_negative_label_count",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "minimum_entry_alpha_confidence": "0.65",
                        "minimum_trade_intensity": "0.003",
                        "m05_signal_count": "6",
                        "m05_selected_contract_count": "3",
                        "m05_unfilled_count": "2",
                        "new_selected_vs_baseline_count": "1",
                        "new_selected_underlying_return_total": "0.02",
                        "new_selected_underlying_return_average": "0.02",
                        "new_selected_positive_label_count": "1",
                        "new_selected_negative_label_count": "0",
                    }
                )

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                m05_unfilled_diagnostics_path=m05_path,
                counterfactual_gate_sweep_path=gate_sweep_path,
                layer_review_rows=[
                    {
                        "source_decision_id": "r1",
                        "layer_id": "model_04_unified_decision",
                        "candidate_set_scope": "decision_time_entry_actions",
                        "available_action": ["open_long", "baseline_action"],
                        "chosen_action": "open_long",
                        "best_available_action_by_future_outcome": "baseline_action",
                        "chosen_action_return": -0.01,
                        "best_available_action_return": 0.0,
                        "regret_to_best_available": 0.01,
                        "correctness_class": "incorrect",
                    },
                    {
                        "source_decision_id": "r1",
                        "layer_id": "model_05_option_expression",
                        "candidate_set_scope": "decision_time_expression_candidates",
                        "available_action": ["long_call AAPL_2021-01-15_C_100", "baseline_action"],
                        "chosen_action": "long_call AAPL_2021-01-15_C_100",
                        "best_available_action_by_future_outcome": "baseline_action",
                        "chosen_action_return": -0.6,
                        "best_available_action_return": 0.0,
                        "regret_to_best_available": 0.6,
                        "correctness_class": "incorrect",
                    },
                ],
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertEqual(report["contract_type"], "model_group_layer_attribution_report")
            self.assertEqual(report["verdict"]["fault_surface"], "M04/M05 boundary")
            self.assertEqual(report["layer_status"]["m04_open_m05_pass_count"], 4)
            self.assertEqual(report["layer_status"]["m04_open_m05_pass_filled_count"], 2)
            self.assertEqual(report["layer_status"]["m04_open_m05_pass_expression_unfilled_count"], 2)
            self.assertEqual(report["layer_status"]["m05_pass_but_m04_not_open_count"], 1)
            self.assertFalse(report["side_effects"]["broker_execution_performed"])
            self.assertFalse(report["side_effects"]["sql_mutation_performed"])
            self.assertEqual(report["m05_unfilled_summary"]["filter_reason_counts"]["dte_outside_policy_range"], 3)
            self.assertEqual(report["row_counterfactual_summary"]["execution_connection_mismatch_count"], 1)
            self.assertEqual(
                report["row_counterfactual_summary"]["counterfactual_bucket_counts"]["execution_connection_failure"],
                1,
            )
            self.assertEqual(
                report["row_counterfactual_summary"]["counterfactual_bucket_counts"]["model_mechanism_defect"],
                2,
            )
            self.assertEqual(
                report["row_counterfactual_summary"]["sample_sufficiency_status"]["status"],
                "sample_limited",
            )
            self.assertEqual(report["row_counterfactual_summary"]["expression_join_status_counts"]["matched"], 2)
            self.assertFalse(report["counterfactual_gate_sweep_summary"]["threshold_selection_performed"])
            self.assertEqual(
                report["verdict"]["root_cause_status"],
                "multiple_root_causes_supported:data_insufficiency,execution_connection_failure,model_mechanism_defect",
            )
            self.assertEqual(report["high_score_filled_tail_loss_summary"]["high_score_filled_loss_count"], 1)
            self.assertEqual(report["high_score_filled_tail_loss_summary"]["high_score_filled_control_count"], 1)
            packet_path = Path(report["high_score_filled_tail_loss_attribution_packet_ref"])
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["contract_type"], "model_group_high_score_filled_tail_loss_attribution_packet")
            self.assertEqual(packet["classification_summary"]["model_overconfidence"]["status"], "supported")
            self.assertEqual(packet["classification_summary"]["data_insufficiency"]["status"], "supported")
            self.assertEqual(
                packet["classification_summary"]["feature_timing_or_leakage"]["status"],
                "unknown_requires_evidence",
            )
            self.assertEqual(
                packet["classification_summary"]["liquidity_spread_fill_realism"]["status"],
                "unknown_requires_evidence",
            )
            self.assertEqual(packet["classification_summary"]["regime_event_miss"]["status"], "unknown_requires_evidence")
            self.assertTrue((output_dir / "layer_attribution_report.json").exists())
            self.assertTrue((output_dir / "m04_m05_cohorts.csv").exists())
            self.assertTrue((output_dir / "filled_score_bins.csv").exists())
            self.assertTrue((output_dir / "tail_loss_rows.csv").exists())
            self.assertTrue((output_dir / "row_counterfactual_attribution.csv").exists())
            self.assertTrue((output_dir / "decision_surface_component_matrix.csv").exists())
            self.assertTrue((output_dir / "component_model_mapping.csv").exists())
            self.assertTrue((output_dir / "component_survival_quality_flow.csv").exists())
            self.assertTrue((output_dir / "component_survival_quality_flow_report.json").exists())
            self.assertTrue((output_dir / "component_review_packet.csv").exists())
            self.assertTrue((output_dir / "component_review_packet.json").exists())
            self.assertTrue((output_dir / "operation_review_projection_matrix.csv").exists())
            self.assertTrue((output_dir / "operation_component_flow.csv").exists())
            self.assertTrue((output_dir / "operation_component_review_packet.csv").exists())
            self.assertTrue((output_dir / "operation_component_review_packet.json").exists())
            self.assertTrue((output_dir / "operation_component_metrics.csv").exists())
            self.assertTrue((output_dir / "operation_component_metrics_report.json").exists())
            self.assertTrue((output_dir / "operation_component_action_rows.csv").exists())
            self.assertTrue((output_dir / "high_score_filled_tail_loss_matches.csv").exists())
            self.assertTrue((output_dir / "parameter_replay_review.csv").exists())
            self.assertTrue((output_dir / "parameter_replay_review_report.json").exists())
            self.assertTrue((output_dir / "parameter_bucket_metrics.csv").exists())
            self.assertTrue((output_dir / "categorical_parameter_replay_review.csv").exists())
            self.assertTrue((output_dir / "suspect_parameter_counterfactual.csv").exists())
            self.assertTrue((output_dir / "suspect_parameter_counterfactual_report.json").exists())
            self.assertTrue((output_dir / "m04_component_diagnostics.csv").exists())
            self.assertTrue((output_dir / "m05_selection_mechanics.csv").exists())
            self.assertTrue((output_dir / "m04_variant_counterfactual.csv").exists())
            self.assertTrue((output_dir / "portfolio_capacity_counterfactual.csv").exists())
            self.assertTrue((output_dir / "portfolio_capacity_counterfactual_report.json").exists())
            self.assertTrue((output_dir / "m05_dte_policy_sensitivity.csv").exists())
            self.assertTrue((output_dir / "m05_hard_filter_overlap.csv").exists())
            self.assertTrue((output_dir / "m04_m05_mechanism_review_report.json").exists())
            self.assertIn("parameter_replay_review_summary", report)
            self.assertIn("parameter_replay_review_report_ref", report)
            self.assertIn("suspect_parameter_counterfactual_summary", report)
            self.assertIn("portfolio_capacity_counterfactual_summary", report)
            self.assertIn("m04_m05_mechanism_review_summary", report)
            self.assertIn("component_survival_quality_flow_summary", report)
            self.assertIn("component_review_packet_summary", report)
            self.assertIn("operation_component_review_packet_summary", report)
            self.assertIn("operation_component_metrics_summary", report)
            self.assertIn(
                "C01_intake_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            self.assertIn(
                "C02_entry_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            self.assertEqual(
                report["operation_component_review_packet_summary"]["first_limiting_projection_counts"][
                    "settled_prediction_quality"
                ],
                2,
            )
            self.assertEqual(
                report["operation_component_review_packet_summary"]["first_limiting_projection_counts"][
                    "option_expression_selection"
                ],
                2,
            )
            self.assertEqual(
                report["decision_surface_summary"]["first_limiting_surface_counts"][
                    "C08_settled_prediction_quality_surface"
                ],
                2,
            )
            self.assertEqual(
                report["decision_surface_summary"]["first_limiting_surface_counts"][
                    "C05_option_expression_surface"
                ],
                2,
            )
            self.assertEqual(
                report["decision_surface_summary"]["first_limiting_surface_counts"][
                    "C04_underlying_decision_surface"
                ],
                2,
            )
            self.assertEqual(report["decision_surface_summary"]["settled_metric_eligible_count"], 2)
            self.assertIn(
                "C05_option_expression_surface",
                report["component_model_mapping_summary"]["first_limiting_surface_counts"],
            )
            with (output_dir / "operation_review_projection_matrix.csv").open(encoding="utf-8") as handle:
                operation_projection_rows = {
                    row["decision_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                operation_projection_rows["r1"]["operation_component_id"],
                "C07_failure_review_operation",
            )
            self.assertEqual(operation_projection_rows["r1"]["review_projection"], "settled_prediction_quality")
            self.assertEqual(
                operation_projection_rows["r3"]["operation_component_id"],
                "C04_expression_review_operation",
            )
            self.assertEqual(operation_projection_rows["r3"]["review_projection"], "option_expression_selection")
            self.assertEqual(operation_projection_rows["r4"]["operation_component_id"], "C02_entry_operation")
            self.assertEqual(operation_projection_rows["r4"]["review_projection"], "underlying_entry_decision")
            with (output_dir / "operation_component_flow.csv").open(encoding="utf-8") as handle:
                operation_flow_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                operation_flow_rows["C03_lifecycle_operation"]["applicability_status"],
                "missing_lifecycle_state_evidence",
            )
            self.assertEqual(
                operation_flow_rows["C03_lifecycle_operation"]["verdict_basis"],
                "portfolio_lifecycle_summary_missing_from_replay_receipt",
            )
            self.assertEqual(
                operation_flow_rows["C04_expression_review_operation"]["first_limiting_projections"],
                "option_expression_selection",
            )
            with (output_dir / "operation_component_review_packet.csv").open(encoding="utf-8") as handle:
                operation_packet_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertIn(
                "explicit_model_05_option_expression_ref",
                operation_packet_rows["C04_expression_review_operation"]["missing_review_outputs"],
            )
            self.assertIn(
                "component_specific_metric_data_gap",
                operation_packet_rows["C01_intake_operation"]["missing_review_outputs"],
            )
            with (output_dir / "operation_component_metrics.csv").open(encoding="utf-8") as handle:
                metric_rows = {
                    (row["operation_component_id"], row["metric_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                metric_rows[("C01_intake_operation", "visible_universe_integrity")]["availability_status"],
                "data_gap",
            )
            self.assertEqual(
                metric_rows[("C02_entry_operation", "selected_target_forward_return_rank_within_sector")][
                    "availability_status"
                ],
                "data_gap",
            )
            self.assertEqual(
                metric_rows[("C03_lifecycle_operation", "portfolio_lifecycle_state_evidence_coverage")][
                    "availability_status"
                ],
                "data_gap",
            )
            with (output_dir / "operation_component_action_rows.csv").open(encoding="utf-8") as handle:
                action_rows = list(csv.DictReader(handle))
            self.assertTrue(action_rows)
            self.assertIn("operation_action", action_rows[0])
            self.assertIn("trigger_state", action_rows[0])
            self.assertIn("pit_feasible_action_set_ref", action_rows[0])
            self.assertIn("component_objective", action_rows[0])
            self.assertIn("best_available_action_by_future_outcome", action_rows[0])
            self.assertIn("component_correctness_class", action_rows[0])
            c02_action = next(row for row in action_rows if row["operation_component_id"] == "C02_entry_operation")
            self.assertEqual(c02_action["trigger_state"], "candidate_triggered")
            self.assertEqual(c02_action["pit_feasible_action_set_ref"], "decision_time_entry_actions")
            self.assertEqual(c02_action["pit_feasible_action_set_status"], "published")
            self.assertEqual(c02_action["pit_feasible_action_count"], "2")
            self.assertEqual(c02_action["review_boundary_ref"], "decision_time_entry_actions")
            self.assertEqual(c02_action["review_boundary_status"], "received_boundary_complete")
            self.assertEqual(c02_action["upstream_decision_state_policy"], "received_upstream_state_is_fixed_review_input")
            self.assertEqual(
                c02_action["downstream_review_input_policy"],
                "judge_component_only_against_received_decision_time_inputs",
            )
            self.assertEqual(
                c02_action["upstream_error_isolation_scope"],
                "attribute_upstream_defects_to_earliest_layer_or_boundary",
            )
            self.assertEqual(
                c02_action["responsibility_assignment_policy"],
                "component_local_correctness_given_received_inputs",
            )
            self.assertEqual(c02_action["best_available_action_by_future_outcome"], "baseline_action")
            self.assertEqual(c02_action["component_correctness_class"], "incorrect")
            self.assertEqual(c02_action["regret_to_best_available"], "0.01")
            self.assertEqual(c02_action["post_replay_label_basis"], "future outcome ranks available entry actions after point-in-time gating")
            c04_action = next(row for row in action_rows if row["operation_component_id"] == "C04_expression_review_operation")
            self.assertEqual(c04_action["pit_feasible_action_set_ref"], "decision_time_expression_candidates")
            self.assertEqual(c04_action["chosen_action"], "long_call AAPL_2021-01-15_C_100")
            self.assertEqual(c04_action["best_available_action_by_future_outcome"], "baseline_action")
            self.assertEqual(c04_action["regret_to_best_available"], "0.6")
            self.assertEqual(
                {
                    "C01_intake_operation",
                    "C02_entry_operation",
                    "C03_lifecycle_operation",
                    "C04_expression_review_operation",
                    "C05_order_intent_operation",
                    "C06_execution_gate_operation",
                    "C07_failure_review_operation",
                },
                {row["operation_component_id"] for row in action_rows},
            )
            operation_packet = json.loads(
                (output_dir / "operation_component_review_packet.json").read_text(encoding="utf-8")
            )
            self.assertEqual(operation_packet["contract_type"], "model_group_operation_component_review_packet")
            self.assertIn(
                "C04_expression_review_operation",
                operation_packet["summary"]["components_with_missing_review_outputs"],
            )
            mechanism_report = json.loads((output_dir / "m04_m05_mechanism_review_report.json").read_text(encoding="utf-8"))
            self.assertEqual(mechanism_report["contract_type"], "model_group_m04_m05_mechanism_review_report")
            self.assertIn("threshold_selection", mechanism_report["forbidden_uses"])
            self.assertEqual(mechanism_report["m04_variant_counterfactual_ref"], "m04_variant_counterfactual.csv")
            self.assertEqual(mechanism_report["m05_dte_policy_sensitivity_ref"], "m05_dte_policy_sensitivity.csv")
            self.assertEqual(mechanism_report["m05_hard_filter_overlap_ref"], "m05_hard_filter_overlap.csv")
            with (output_dir / "m04_component_diagnostics.csv").open(encoding="utf-8") as handle:
                component_rows = {
                    (row["component_name"], row["subset_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                component_rows[("materiality_adjusted_action_score", "all_rows")]["diagnostic_status"],
                "missing_component_coverage",
            )
            with (output_dir / "m04_variant_counterfactual.csv").open(encoding="utf-8") as handle:
                variant_rows = {
                    (row["variant_name"], row["subset_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                variant_rows[("current_horizon_rank_proxy", "m04_open_m05_pass")]["diagnostic_status"],
                "missing_component_coverage",
            )
            self.assertIn(("materiality_guarded_rank_proxy", "m04_open_m05_pass"), variant_rows)
            capacity_report = json.loads(
                (output_dir / "portfolio_capacity_counterfactual_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                capacity_report["contract_type"],
                "model_group_portfolio_capacity_counterfactual_report",
            )
            self.assertIn("portfolio_policy_selection", capacity_report["forbidden_uses"])
            with (output_dir / "m05_hard_filter_overlap.csv").open(encoding="utf-8") as handle:
                overlap_rows = list(csv.DictReader(handle))
            self.assertTrue(
                any(
                    row["overlap_group"] == "dte_overlaps_other_filters"
                    and row["filter_reason_set"] == "delta_outside_policy_range;dte_outside_policy_range"
                    for row in overlap_rows
                )
            )
            with (output_dir / "decision_surface_component_matrix.csv").open(encoding="utf-8") as handle:
                surface_rows = {
                    row["decision_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(surface_rows["r1"]["first_limiting_surface"], "C08_settled_prediction_quality_surface")
            self.assertEqual(surface_rows["r3"]["first_limiting_surface"], "C05_option_expression_surface")
            self.assertEqual(surface_rows["r4"]["first_limiting_surface"], "C04_underlying_decision_surface")
            self.assertEqual(surface_rows["r1"]["settled_metric_eligible"], "True")
            self.assertEqual(surface_rows["r3"]["settled_metric_eligible"], "False")
            self.assertEqual(surface_rows["r1"]["model_04_score_coverage_count"], "1")
            with (output_dir / "component_model_mapping.csv").open(encoding="utf-8") as handle:
                mapping_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertFalse(any(surface.startswith("model_") for surface in mapping_rows))
            self.assertEqual(
                mapping_rows["C04_underlying_decision_surface"]["mapping_status"],
                "diagnostic_or_decision_surface_without_explicit_ref",
            )
            self.assertEqual(mapping_rows["C04_underlying_decision_surface"]["first_limiting_surface_count"], "2")
            self.assertEqual(mapping_rows["C08_settled_prediction_quality_surface"]["mapping_status"], "non_model_surface")
            self.assertEqual(mapping_rows["C08_settled_prediction_quality_surface"]["first_limiting_surface_count"], "2")
            with (output_dir / "component_survival_quality_flow.csv").open(encoding="utf-8") as handle:
                flow_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(flow_rows["C05_option_expression_surface"]["stage_verdict"], "first_observed_deterioration")
            self.assertEqual(flow_rows["C08_settled_prediction_quality_surface"]["settled_metric_eligible_count"], "2")
            self.assertEqual(flow_rows["C08_settled_prediction_quality_surface"]["tail_loss_count"], "1")
            self.assertEqual(
                flow_rows["C08_settled_prediction_quality_surface"]["stage_verdict"],
                "insufficient_evidence",
            )
            with (output_dir / "component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                packet_rows["C04_underlying_decision_surface"]["attribution_coverage_status"],
                "diagnostic_without_explicit_asset_ref",
            )
            self.assertEqual(
                packet_rows["C05_option_expression_surface"]["interpretation_status"],
                "problem_surface_with_insufficient_attribution",
            )
            self.assertIn(
                "explicit_model_05_option_expression_ref",
                packet_rows["C05_option_expression_surface"]["missing_review_outputs"],
            )
            packet = json.loads((output_dir / "component_review_packet.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["contract_type"], "model_group_component_review_packet")
            self.assertEqual(
                packet["summary"]["review_readiness_status"],
                "insufficient_attribution_for_some_problem_surfaces",
            )
            self.assertIn("C05_option_expression_surface", packet["summary"]["components_with_missing_review_outputs"])

    def test_operation_component_metrics_rank_selected_target_after_sector_bucket_selection(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            universe_path = tmp / "target_selection_universe_metrics.csv"
            row = _row(
                "r1",
                "accepted",
                "simulated_filled",
                1,
                0.72,
                0.12,
                "open_long",
                "long",
                "passed",
                "listed_option_contract",
            )
            row["target_ref"] = "MSFT"
            row["timestamp"] = "2021-01-04T16:00:00-05:00"
            rows_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with universe_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["timestamp", "target_ref", "sector_bucket_ref", "forward_return"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "target_ref": "AAPL",
                        "sector_bucket_ref": "XLK",
                        "forward_return": "0.05",
                    }
                )
                writer.writerow(
                    {
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "target_ref": "MSFT",
                        "sector_bucket_ref": "XLK",
                        "forward_return": "0.10",
                    }
                )
                writer.writerow(
                    {
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "target_ref": "NVDA",
                        "sector_bucket_ref": "XLC",
                        "forward_return": "0.20",
                    }
                )
            trace_path = tmp / "model_candidate_selection_trace.jsonl"
            trace_rows = [
                _model_candidate_trace_row("AAPL", rank=1, selected=True),
                _model_candidate_trace_row("MSFT", rank=2, selected=False),
                _model_candidate_trace_row("NVDA", rank=3, selected=False),
            ]
            trace_path.write_text("\n".join(json.dumps(row) for row in trace_rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                target_selection_universe_metrics_path=universe_path,
                model_candidate_selection_trace_path=trace_path,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertEqual(
                report["operation_component_metrics_summary"]["availability_status_counts"]["computed"],
                10,
            )
            with (output_dir / "operation_component_metrics.csv").open(encoding="utf-8") as handle:
                metric_rows = {
                    (row["operation_component_id"], row["metric_name"]): row
                    for row in csv.DictReader(handle)
                }
            sector_metric = metric_rows[("C01_intake_operation", "selected_sector_bucket_forward_return_rank")]
            self.assertEqual(sector_metric["availability_status"], "computed")
            self.assertEqual(sector_metric["universe_count_mean"], "2.0")
            self.assertEqual(sector_metric["selected_forward_return_rank_mean"], "2.0")
            self.assertEqual(sector_metric["selected_forward_return_percentile_mean"], "0.0")
            self.assertEqual(sector_metric["opportunity_cost_to_best_mean"], "0.125")
            rank_metric = metric_rows[("C02_entry_operation", "selected_target_forward_return_rank_within_sector")]
            self.assertEqual(rank_metric["availability_status"], "computed")
            self.assertEqual(rank_metric["universe_count_mean"], "2.0")
            self.assertEqual(rank_metric["selected_forward_return_rank_mean"], "1.0")
            self.assertEqual(rank_metric["selected_forward_return_percentile_mean"], "1.0")
            self.assertEqual(rank_metric["opportunity_cost_to_best_mean"], "0.0")
            self.assertEqual(
                metric_rows[("C01_intake_operation", "visible_universe_integrity")]["value"],
                "1.0",
            )
            self.assertEqual(
                metric_rows[("C01_intake_operation", "visible_candidate_model_scoring_coverage")]["value"],
                "1.0",
            )
            self.assertEqual(
                metric_rows[("C02_entry_operation", "model_ranked_candidate_selection_funnel")]["selected_forward_return_rank_mean"],
                "1.0",
            )
            self.assertTrue((output_dir / "model_candidate_selection_summary.csv").exists())
            model_candidate_summary = json.loads(
                (output_dir / "model_candidate_selection_summary_report.json").read_text(encoding="utf-8")
            )["summary"]
            self.assertEqual(model_candidate_summary["selected_candidate_rank_mean_same_timestamp"], 1.0)
            self.assertEqual(model_candidate_summary["selected_candidate_top_25_same_timestamp_count"], 1)
            self.assertTrue((output_dir / "pre_option_candidate_quality.csv").exists())
            pre_option_summary = json.loads(
                (output_dir / "pre_option_candidate_quality_report.json").read_text(encoding="utf-8")
            )["summary"]
            self.assertEqual(pre_option_summary["cohort_count"], 9)
            self.assertTrue((output_dir / "operation_mechanism_contract_packet.csv").exists())
            mechanism_contract_summary = json.loads(
                (output_dir / "operation_mechanism_contract_packet.json").read_text(encoding="utf-8")
            )["summary"]
            self.assertGreaterEqual(mechanism_contract_summary["mechanism_contract_count"], 1)
            with (output_dir / "operation_mechanism_contract_packet.csv").open(encoding="utf-8") as handle:
                mechanism_contracts = {
                    row["mechanism_contract_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertIn("mechanism_c01_sector_selection_effectiveness", mechanism_contracts)
            self.assertEqual(
                mechanism_contracts["mechanism_c01_sector_selection_effectiveness"]["breach_status"],
                "breached",
            )
            with (output_dir / "operation_component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertNotIn(
                "component_specific_metric_data_gap",
                packet_rows["C01_intake_operation"]["missing_review_outputs"],
            )
            self.assertEqual(
                packet_rows["C01_intake_operation"]["metric_effectiveness_status"],
                "weak_effectiveness_observed",
            )
            self.assertIn(
                "selected_sector_bucket_mean_percentile_below_median",
                packet_rows["C01_intake_operation"]["metric_effectiveness_flags"],
            )
            self.assertNotIn(
                "component_specific_metric_data_gap",
                packet_rows["C02_entry_operation"]["missing_review_outputs"],
            )

    def test_operation_component_metrics_use_trace_when_target_universe_is_absent(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            row = _row(
                "r1",
                "accepted",
                "simulated_filled",
                1,
                0.72,
                0.12,
                "open_long",
                "long",
                "passed",
                "listed_option_contract",
            )
            row["target_ref"] = "MSFT"
            row["timestamp"] = "2021-01-04T16:00:00-05:00"
            rows_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            trace_path = tmp / "model_candidate_selection_trace.jsonl"
            trace_rows = [
                _model_candidate_trace_row("MSFT", rank=2, selected=True),
                _model_candidate_trace_row("AAPL", rank=1, selected=False),
                _model_candidate_trace_row("NVDA", rank=3, selected=False),
            ]
            trace_path.write_text("\n".join(json.dumps(row) for row in trace_rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                model_candidate_selection_trace_path=trace_path,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertNotIn(
                "C01_intake_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            self.assertNotIn(
                "C02_entry_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            with (output_dir / "operation_component_metrics.csv").open(encoding="utf-8") as handle:
                metric_rows = {
                    (row["operation_component_id"], row["metric_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                metric_rows[("C01_intake_operation", "visible_universe_integrity")]["availability_status"],
                "computed",
            )
            self.assertEqual(
                metric_rows[("C01_intake_operation", "selected_sector_bucket_forward_return_rank")][
                    "availability_status"
                ],
                "not_applicable",
            )
            self.assertEqual(
                metric_rows[("C02_entry_operation", "selected_target_forward_return_rank_within_sector")][
                    "availability_status"
                ],
                "not_applicable",
            )
            rank_metric = metric_rows[("C02_entry_operation", "selected_target_model_rank_from_trace")]
            self.assertEqual(rank_metric["availability_status"], "computed")
            self.assertEqual(rank_metric["selected_forward_return_rank_mean"], "2.0")
            with (output_dir / "operation_component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertNotIn(
                "component_specific_metric_data_gap",
                packet_rows["C01_intake_operation"]["missing_review_outputs"],
            )
            self.assertNotIn(
                "component_specific_metric_data_gap",
                packet_rows["C02_entry_operation"]["missing_review_outputs"],
            )

    def test_operation_component_metrics_marks_partial_target_universe_as_gap(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            universe_path = tmp / "target_selection_universe_metrics.csv"
            selected_row = _row(
                "r1",
                "accepted",
                "simulated_filled",
                1,
                0.72,
                0.12,
                "open_long",
                "long",
                "passed",
                "listed_option_contract",
            )
            selected_row["target_ref"] = "MSFT"
            selected_row["timestamp"] = "2021-01-04T16:00:00-05:00"
            missing_row = dict(selected_row)
            missing_row["decision_id"] = "r2"
            missing_row["target_ref"] = "TSLA"
            rows_path.write_text(
                "\n".join(json.dumps(row) for row in (selected_row, missing_row)) + "\n",
                encoding="utf-8",
            )
            with universe_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["timestamp", "target_ref", "sector_bucket_ref", "forward_return"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "target_ref": "AAPL",
                        "sector_bucket_ref": "XLK",
                        "forward_return": "0.05",
                    }
                )
                writer.writerow(
                    {
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "target_ref": "MSFT",
                        "sector_bucket_ref": "XLK",
                        "forward_return": "0.10",
                    }
                )

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                target_selection_universe_metrics_path=universe_path,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertIn(
                "C01_intake_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            self.assertIn(
                "C02_entry_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            with (output_dir / "operation_component_metrics.csv").open(encoding="utf-8") as handle:
                metric_rows = {
                    (row["operation_component_id"], row["metric_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                metric_rows[("C01_intake_operation", "visible_universe_integrity")]["availability_status"],
                "partial",
            )
            self.assertEqual(
                metric_rows[("C02_entry_operation", "selected_target_forward_return_rank_within_sector")][
                    "availability_status"
                ],
                "partial",
            )
            with (output_dir / "operation_component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertIn(
                "component_specific_metric_data_gap",
                packet_rows["C01_intake_operation"]["missing_review_outputs"],
            )
            self.assertIn(
                "component_specific_metric_data_gap",
                packet_rows["C02_entry_operation"]["missing_review_outputs"],
            )

    def test_operation_component_metrics_separates_universe_membership_from_return_label_gap(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            universe_path = tmp / "target_selection_universe_metrics.csv"
            row = _row(
                "r1",
                "accepted",
                "simulated_filled",
                1,
                0.72,
                0.12,
                "open_long",
                "long",
                "passed",
                "listed_option_contract",
            )
            row["target_ref"] = "MSFT"
            row["timestamp"] = "2021-01-04T16:00:00-05:00"
            rows_path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            with universe_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "timestamp",
                        "target_ref",
                        "sector_bucket_ref",
                        "visible_universe_membership",
                        "forward_return",
                        "forward_return_status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "target_ref": "MSFT",
                        "sector_bucket_ref": "XLK",
                        "visible_universe_membership": "true",
                        "forward_return": "",
                        "forward_return_status": "missing_exit_bar",
                    }
                )

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                target_selection_universe_metrics_path=universe_path,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertIn(
                "C02_entry_operation",
                report["operation_component_metrics_summary"]["components_with_metric_data_gaps"],
            )
            with (output_dir / "operation_component_metrics.csv").open(encoding="utf-8") as handle:
                metric_rows = {
                    (row["operation_component_id"], row["metric_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                metric_rows[("C01_intake_operation", "visible_universe_integrity")]["availability_status"],
                "computed",
            )
            self.assertEqual(
                metric_rows[("C02_entry_operation", "selected_target_forward_return_rank_within_sector")][
                    "availability_status"
                ],
                "data_gap",
            )
            with (output_dir / "operation_component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertIn(
                "component_specific_metric_data_gap",
                packet_rows["C01_intake_operation"]["missing_review_outputs"],
            )
            self.assertIn(
                "component_specific_metric_data_gap",
                packet_rows["C02_entry_operation"]["missing_review_outputs"],
            )

    def test_tail_loss_packet_does_not_count_unmatched_loss_as_match(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = [
                _row("r1", "accepted", "simulated_filled", 0, 0.83, -0.6, "open_long", "long", "passed", "listed_option_contract"),
            ]
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            packet_path = Path(report["high_score_filled_tail_loss_attribution_packet_ref"])
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["headline"]["high_score_filled_loss_count"], 1)
            self.assertEqual(packet["headline"]["high_score_filled_control_count"], 0)
            self.assertEqual(packet["headline"]["matched_comparison_count"], 0)
            self.assertEqual(packet["headline"]["tail_loss_row_count"], 1)
            self.assertEqual(packet["classification_summary"]["cohort_counts"]["matched_comparison_count"], 0)
            self.assertEqual(packet["classification_summary"]["match_quality_counts"]["unmatched"], 1)

    def test_component_matrix_separates_path_materialization_from_model_asset_rollup(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            row = _row(
                "r1",
                "accepted",
                "simulated_rejected",
                0,
                0.61,
                0.0,
                "open_long",
                "long",
                "passed",
                "listed_option_contract",
            )
            row["selected_option_contract_ref"] = "AAPL_2021-01-08_C_130"
            row["option_contract_path_status"] = "missing"
            row["replay_rejection_reason"] = "option_contract_path_missing"
            row["model_evidence_chain"] = [
                "model_04_unified_decision",
                "model_05_option_expression",
            ]
            row["model_layer_refs"] = {"model_04_unified_decision": "udv_fixture"}
            rows_path.write_text(json.dumps(row) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            self.assertEqual(
                report["decision_surface_summary"]["first_limiting_surface_counts"][
                    "C06_selected_option_path_materialization"
                ],
                1,
            )
            self.assertEqual(report["decision_surface_summary"]["settled_metric_eligible_count"], 0)
            with (output_dir / "decision_surface_component_matrix.csv").open(encoding="utf-8") as handle:
                surface_row = next(csv.DictReader(handle))
            self.assertEqual(surface_row["first_limiting_surface"], "C06_selected_option_path_materialization")
            self.assertEqual(surface_row["model_04_unified_decision_ref_status"], "explicit_ref_and_evidence_chain")
            self.assertEqual(surface_row["model_05_option_expression_ref_status"], "evidence_chain_only")
            self.assertFalse(any(key.startswith("model_06_") for key in surface_row))
            with (output_dir / "component_model_mapping.csv").open(encoding="utf-8") as handle:
                mapping_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                mapping_rows["C06_selected_option_path_materialization"]["mapping_status"],
                "non_model_surface",
            )
            self.assertFalse(any("residual_event" in key for key in mapping_rows))
            with (output_dir / "component_survival_quality_flow.csv").open(encoding="utf-8") as handle:
                flow_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(flow_rows["C06_selected_option_path_materialization"]["stage_verdict"], "dominant_censoring_point")
            self.assertEqual(flow_rows["C06_selected_option_path_materialization"]["censored_count"], "1")
            self.assertEqual(flow_rows["C06_selected_option_path_materialization"]["settled_metric_eligible_count"], "0")
            with (output_dir / "operation_review_projection_matrix.csv").open(encoding="utf-8") as handle:
                operation_projection_row = next(csv.DictReader(handle))
            self.assertEqual(
                operation_projection_row["operation_component_id"],
                "C04_expression_review_operation",
            )
            self.assertEqual(
                operation_projection_row["review_projection"],
                "selected_contract_path_materialization",
            )
            with (output_dir / "operation_component_flow.csv").open(encoding="utf-8") as handle:
                operation_flow_rows = {
                    row["operation_component_id"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                operation_flow_rows["C04_expression_review_operation"]["stage_verdict"],
                "dominant_censoring_point",
            )
            self.assertEqual(operation_flow_rows["C04_expression_review_operation"]["censored_count"], "1")
            with (output_dir / "component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                packet_rows["C06_selected_option_path_materialization"]["interpretation_status"],
                "problem_surface_without_direct_model_asset",
            )
            flow_report = json.loads(
                (output_dir / "component_survival_quality_flow_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                flow_report["summary"]["dominant_censoring_surfaces"],
                ["C06_selected_option_path_materialization"],
            )

    def test_component_review_packet_consumes_m05_without_retired_event_surface(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = [
                _row("r1", "accepted", "simulated_filled", 1, 0.72, 0.25, "open_long", "long", "passed", "listed_option_contract"),
                _row("r2", "accepted", "simulated_filled", 0, 0.68, -0.15, "open_long", "long", "passed", "listed_option_contract"),
            ]
            for row in rows:
                row["model_layer_refs"] = {
                    "model_01_background_context": f"m01://{row['decision_id']}",
                    "model_02_target_state": f"m02://{row['decision_id']}",
                    "model_03_event_state": f"m03://{row['decision_id']}",
                    "model_04_unified_decision": f"m04://{row['decision_id']}",
                    "model_05_option_expression": f"m05://{row['decision_id']}",
                }
                row["model_layer_diagnostics"]["model_01_background_context"] = {
                    "state_quality_score": 0.91,
                    "market_risk_stress_score": 0.12,
                }
                row["model_layer_diagnostics"]["model_02_target_state"] = {
                    "target_ref": "AAPL",
                    "target_direction_score_1D": 0.62,
                }
                row["model_layer_diagnostics"]["model_03_event_state"] = {
                    "event_path_risk_score_1D": 0.18,
                    "event_entry_block_pressure_score_1D": 0.05,
                }
                row["model_layer_diagnostics"]["model_05_option_expression"] = {
                    "selection_gate_status": "passed",
                    "resolved_selection_score": row["prediction_score"],
                    "selected_contract_ref": row["selected_option_contract_ref"],
                }
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            with (output_dir / "component_review_packet.csv").open(encoding="utf-8") as handle:
                packet_rows = {
                    row["component_surface"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                packet_rows["C05_option_expression_surface"]["attribution_coverage_status"],
                "explicit_asset_and_internal_diagnostics",
            )
            for component_surface in (
                "C01_background_context_surface",
                "C02_target_state_surface",
                "C03_event_state_surface",
            ):
                self.assertEqual(
                    packet_rows[component_surface]["attribution_coverage_status"],
                    "explicit_asset_and_internal_diagnostics",
                )
                self.assertEqual(packet_rows[component_surface]["missing_review_outputs"], "")
            self.assertNotIn(
                "explicit_model_05_option_expression_ref",
                packet_rows["C05_option_expression_surface"]["missing_review_outputs"],
            )
            self.assertNotIn(
                "model_05_alpha_or_selection_score_diagnostics",
                packet_rows["C05_option_expression_surface"]["missing_review_outputs"],
            )
            self.assertEqual(packet_rows["C05_option_expression_surface"]["missing_review_outputs"], "")
            self.assertFalse(any("residual_event" in key for key in packet_rows))

    def test_tail_loss_packet_keeps_numeric_zero_label_for_disagreement(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = [
                _row("r1", "accepted", "simulated_filled", 0, 0.83, -0.6, "open_long", "long", "passed", "listed_option_contract"),
                _row("r2", "accepted", "simulated_filled", 0, 0.84, 0.4, "open_long", "long", "passed", "listed_option_contract"),
            ]
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            packet_path = Path(report["high_score_filled_tail_loss_attribution_packet_ref"])
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(packet["headline"]["matched_comparison_count"], 1)
            self.assertEqual(packet["classification_summary"]["label_target_definition"]["status"], "supported")
            self.assertEqual(packet["classification_summary"]["label_target_definition"]["evidence_count"], 1)

    def test_parameter_replay_review_classifies_useful_and_inverted_parameters(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = []
            for index in range(60):
                value = index / 59
                profitable = index >= 30
                row = _row(
                    f"p{index}",
                    "accepted",
                    "simulated_filled",
                    1 if profitable else 0,
                    0.5,
                    0.03 if profitable else -0.03,
                    "open_long",
                    "long",
                    "passed",
                    "listed_option_contract",
                )
                row["timestamp"] = f"2021-02-{(index % 28) + 1:02d}T16:00:00-05:00"
                row["feature_momentum_7d"] = value
                row["model_layer_diagnostics"]["model_05_alpha_confidence"]["resolved_alpha_score"] = 1 - value
                rows.append(row)
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            with (output_dir / "parameter_replay_review.csv").open(encoding="utf-8") as handle:
                parameter_rows = {
                    row["parameter_name"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(parameter_rows["feature_momentum_7d"]["classification"], "directionally_useful")
            self.assertEqual(
                parameter_rows["model_layer_diagnostics.model_05_alpha_confidence.resolved_alpha_score"]["classification"],
                "suspect_requires_redesign",
            )
            self.assertIn(
                "model_layer_diagnostics.model_05_alpha_confidence.resolved_alpha_score",
                report["parameter_replay_review_summary"]["suspect_requires_redesign_parameters"],
            )
            review_report = json.loads((output_dir / "parameter_replay_review_report.json").read_text(encoding="utf-8"))
            self.assertEqual(review_report["contract_type"], "model_group_parameter_replay_review_report")
            self.assertIn("threshold_selection", review_report["forbidden_uses"])

    def test_suspect_parameter_counterfactual_separates_selection_and_m04_modes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = []
            for index in range(90):
                value = index / 89
                filled = index < 60
                high_value = value >= 0.5
                profitable_fill = filled and not high_value
                row = _row(
                    f"s{index}",
                    "accepted" if filled else "suitable",
                    "simulated_filled" if filled else "simulated_rejected",
                    1 if (profitable_fill or not filled) else 0,
                    0.5,
                    0.03 if profitable_fill else -0.03 if filled else 0.0,
                    "open_long",
                    "long",
                    "passed",
                    "listed_option_contract" if filled else "option_expression_unfilled",
                )
                row["timestamp"] = f"2021-03-{(index // 24) + 1:02d}T{index % 24:02d}:00:00-05:00"
                row["feature_momentum_30d"] = value
                scores = row["model_layer_diagnostics"]["model_04_unified_decision"]["dominant_horizon_scores"]
                scores["action_direction_score"] = value
                scores["expected_return_score"] = value
                scores["trade_intensity_score"] = value
                rows.append(row)
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            m05_path = tmp / "m05_unfilled.csv"
            with m05_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "timestamp",
                        "outcome_label",
                        "underlying_return",
                        "asset_expression_route",
                        "selected_contract_ref",
                        "candidate_count_before_filter",
                        "candidate_count_after_filter",
                        "eligible_candidate_count",
                        "top_contract_fit_score",
                        "plan_reason_codes",
                        "fail_reason_counts",
                    ],
                )
                writer.writeheader()
                for row in rows[60:]:
                    writer.writerow(
                        {
                            "timestamp": row["timestamp"],
                            "outcome_label": "1",
                            "underlying_return": "0.02",
                            "asset_expression_route": "option_expression_unfilled",
                            "selected_contract_ref": "",
                            "candidate_count_before_filter": "4",
                            "candidate_count_after_filter": "0",
                            "eligible_candidate_count": "0",
                            "top_contract_fit_score": "0.18",
                            "plan_reason_codes": "no_contract_passed_hard_filter;dte_outside_policy_range",
                            "fail_reason_counts": "{'dte_outside_policy_range': 4}",
                        }
                    )

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                m05_unfilled_diagnostics_path=m05_path,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            with (output_dir / "suspect_parameter_counterfactual.csv").open(encoding="utf-8") as handle:
                counterfactual_rows = {
                    row["parameter_name"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                counterfactual_rows["feature_momentum_30d"]["primary_followup_mode"],
                "filled_subset_selection_effect",
            )
            self.assertEqual(
                counterfactual_rows[
                    "model_layer_diagnostics.model_04_unified_decision.dominant_horizon_scores.trade_intensity_score"
                ]["primary_followup_mode"],
                "m04_component_weight_or_direction_issue",
            )
            counterfactual_report = json.loads(
                (output_dir / "suspect_parameter_counterfactual_report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                counterfactual_report["contract_type"],
                "model_group_suspect_parameter_counterfactual_report",
            )
            self.assertFalse(counterfactual_report["retraining_performed"])
            self.assertIn("threshold_selection", counterfactual_report["forbidden_uses"])
            self.assertFalse(report["suspect_parameter_counterfactual_summary"]["threshold_selection_performed"])
            with (output_dir / "m04_component_diagnostics.csv").open(encoding="utf-8") as handle:
                component_rows = {
                    (row["component_name"], row["subset_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                component_rows[("trade_intensity_score", "m04_open_m05_pass_filled")]["diagnostic_status"],
                "inverted_against_expected_direction",
            )
            self.assertIn(
                "trade_intensity_score",
                report["m04_m05_mechanism_review_summary"]["m04_open_filled_inverted_components"],
            )
            with (output_dir / "m05_selection_mechanics.csv").open(encoding="utf-8") as handle:
                selection_rows = list(csv.DictReader(handle))
            self.assertTrue(
                any(
                    row["execution_expression_state"] == "expression_unfilled"
                    and row["option_feasibility_state"] == "hard_filter_zero_eligible"
                    and row["selected_expression_type"] == "underlying_only_expression"
                    for row in selection_rows
                )
            )
            with (output_dir / "m04_variant_counterfactual.csv").open(encoding="utf-8") as handle:
                variant_rows = {
                    (row["variant_name"], row["subset_name"]): row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(
                variant_rows[("inverse_trade_intensity", "m04_open_m05_pass_filled")]["diagnostic_status"],
                "aligned_with_realized_return",
            )
            self.assertIn(
                "inverse_trade_intensity",
                report["m04_m05_mechanism_review_summary"]["m04_open_filled_aligned_variants"],
            )
            with (output_dir / "m05_dte_policy_sensitivity.csv").open(encoding="utf-8") as handle:
                dte_rows = {
                    (row["sensitivity_case"], row["primary_filter_reason"]): row
                    for row in csv.DictReader(handle)
            }
            dte_primary = dte_rows[("dte_primary_hard_filter", "dte_outside_policy_range")]
            self.assertEqual(dte_primary["diagnostic_status"], "dte_policy_pressure_supported")
            self.assertEqual(dte_primary["positive_label_count"], "30")
            self.assertEqual(report["m04_m05_mechanism_review_summary"]["m05_dte_primary_positive_label_count"], 30)
            with (output_dir / "m05_hard_filter_overlap.csv").open(encoding="utf-8") as handle:
                overlap_rows = {
                    row["overlap_group"]: row
                    for row in csv.DictReader(handle)
                }
            self.assertEqual(overlap_rows["dte_isolated"]["positive_label_count"], "30")
            self.assertEqual(report["m04_m05_mechanism_review_summary"]["m05_dte_isolated_positive_label_count"], 30)
            self.assertEqual(report["m04_m05_mechanism_review_summary"]["m05_dte_overlap_positive_label_count"], 0)

    def test_portfolio_capacity_counterfactual_and_materiality_guard_are_fixed_input(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = []
            for index in range(6):
                row = _row(
                    f"c{index}",
                    "accepted",
                    "simulated_filled",
                    1 if index in {0, 1, 5} else 0,
                    0.70 + index * 0.02,
                    0.04 if index in {0, 1, 5} else -0.04,
                    "open_long",
                    "long",
                    "passed",
                    "listed_option_contract",
                )
                row["timestamp"] = f"2021-05-{index + 1:02d}T16:00:00-05:00"
                row["target_ref"] = f"T{index}"
                row["planned_position_notional_usd"] = 1000.0
                row["total_portfolio_notional_usd"] = 6000.0
                scores = row["model_layer_diagnostics"]["model_04_unified_decision"]["dominant_horizon_scores"]
                scores.update(
                    {
                        "action_confidence_score": 0.7 + index * 0.02,
                        "materiality_adjusted_action_score": 0.7 + index * 0.02,
                        "no_trade_probability_score": 0.10,
                        "trade_intensity_score": 0.02 + index * 0.01,
                        "minimum_trade_intensity": 0.01,
                        "expected_return_score": 0.02 + index * 0.01,
                        "action_direction_score": 0.55 + index * 0.05,
                        "entry_quality_score": 0.8,
                        "downside_risk_score": 0.1,
                    }
                )
                if index == 5:
                    row["model_layer_diagnostics"]["model_04_unified_decision"]["reason_codes"] = [
                        "resolved_open_long",
                        "position_gap_below_materiality",
                    ]
                rows.append(row)
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            with (output_dir / "portfolio_capacity_counterfactual.csv").open(encoding="utf-8") as handle:
                capacity_rows = {
                    row["variant_name"]: row
                    for row in csv.DictReader(handle)
                }
            top_5 = capacity_rows["top_5_by_replay_rank"]
            self.assertEqual(top_5["selected_count"], "5")
            self.assertEqual(top_5["excluded_count"], "1")
            self.assertEqual(top_5["position_blocked_count"], "1")
            self.assertEqual(top_5["budget_blocked_count"], "0")
            self.assertEqual(top_5["threshold_selection_performed"], "False")
            self.assertEqual(top_5["retraining_performed"], "False")
            self.assertEqual(top_5["fixed_input_only"], "True")
            budget_50 = capacity_rows["budget_50pct_by_replay_rank"]
            self.assertEqual(budget_50["selected_count"], "3")
            self.assertEqual(budget_50["budget_blocked_count"], "3")
            self.assertEqual(
                report["portfolio_capacity_counterfactual_summary"]["baseline_selected_count"],
                6,
            )
            self.assertFalse(report["portfolio_capacity_counterfactual_summary"]["threshold_selection_performed"])
            with (output_dir / "m04_variant_counterfactual.csv").open(encoding="utf-8") as handle:
                variant_rows = {
                    row["variant_name"]: row
                    for row in csv.DictReader(handle)
                    if row["subset_name"] == "m04_open_m05_pass_filled"
                }
            self.assertIn("materiality_guarded_rank_proxy", variant_rows)
            self.assertEqual(variant_rows["materiality_guarded_rank_proxy"]["fixed_input_only"], "True")

    def test_suspect_parameter_counterfactual_keeps_header_when_no_suspects(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            rows_path = tmp / "decision_rows.jsonl"
            output_dir = tmp / "diagnostic"
            rows = []
            for index in range(60):
                value = index / 59
                row = _row(
                    f"n{index}",
                    "accepted",
                    "simulated_filled",
                    1 if value >= 0.5 else 0,
                    value,
                    0.03 if value >= 0.5 else -0.03,
                    "open_long",
                    "long",
                    "passed",
                    "listed_option_contract",
                )
                row["timestamp"] = f"2021-04-{(index % 28) + 1:02d}T16:00:00-05:00"
                row["feature_momentum_30d"] = value
                rows.append(row)
            rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

            report = build_model_group_layer_attribution(
                decision_rows_path=rows_path,
                output_dir=output_dir,
                now_utc=datetime(2026, 6, 13, 18, 0, tzinfo=UTC),
            )

            with (output_dir / "suspect_parameter_counterfactual.csv").open(encoding="utf-8") as handle:
                header = handle.readline().strip()
            self.assertIn("parameter_name", header)
            self.assertIn("primary_followup_mode", header)
            self.assertEqual(report["suspect_parameter_counterfactual_summary"]["suspect_parameter_count"], 0)


def _row(
    decision_id: str,
    decision_status: str,
    fill_status: str,
    outcome_label: int,
    prediction_score: float,
    realized_return: float,
    m04_action: str,
    m04_side: str,
    m05_status: str,
    route: str,
) -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "timestamp": f"2021-01-0{decision_id[-1]}T16:00:00-05:00",
        "decision_status": decision_status,
        "decision_expression_type": (
            "long_call"
            if route == "listed_option_contract"
            else "underlying_only_expression" if route == "option_expression_unfilled" else "no_option_expression"
        ),
        "fill_status": fill_status,
        "outcome_label": outcome_label,
        "prediction_score": prediction_score,
        "realized_return": realized_return,
        "asset_expression_route": route,
        "selected_option_contract_ref": "AAPL_2021-01-08_C_130" if fill_status == "simulated_filled" else "",
        "option_entry_price": 1.0,
        "option_exit_price": 1.0 + realized_return,
        "model_layer_diagnostics": {
            "model_04_unified_decision": {
                "resolved_underlying_action_type": m04_action,
                "resolved_action_side": m04_side,
                "reason_codes": ["resolved_open_long"] if m04_action == "open_long" else ["resolved_no_trade"],
                "dominant_horizon_scores": {"trade_intensity_score": 0.02},
            },
            "model_05_alpha_confidence": {
                "alpha_gate_status": m05_status,
                "resolved_alpha_score": prediction_score,
            },
        },
    }


def _model_candidate_trace_row(target: str, *, rank: int, selected: bool) -> dict[str, object]:
    return {
        "contract_type": "evaluation_model_candidate_selection_trace_row",
        "replay_execution_run_id": "test_run",
        "candidate_model_ref": "storage://trading-manager/model_group/test_fold",
        "target_ref": target,
        "timestamp": "2021-01-04T16:00:00-05:00",
        "replay_time_pointer": "2021-01-04T16:00:00-05:00",
        "point_in_time_policy": "replay_time_pointer_excludes_future_decision_inputs",
        "diagnostic_only": True,
        "future_outcome_label_included": False,
        "model_score_available": True,
        "model_rank_within_timestamp": rank,
        "selected_by_replay": selected,
        "model_candidate_trace_status": "selected_by_replay" if selected else "scored_not_selected_by_portfolio",
        "m04_trade_intent": True,
        "option_expression_signal_required": True,
        "diagnostic_rank_score": 1.0 / rank,
        "alpha_score": 0.8,
        "trade_intensity_score": 0.2,
        "expected_return_score": 0.1,
        "action_direction_score": 0.9,
        "underlying_action_type": "open_long",
        "action_side": "long",
        "selected_option_contract_ref": "AAPL_2021-01-08_C_130" if selected else "",
    }


if __name__ == "__main__":
    unittest.main()

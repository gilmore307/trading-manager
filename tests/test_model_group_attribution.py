from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import trading_manager_tasks.model_group_attribution as model_group_attribution
from trading_manager_tasks.model_group_attribution import run_model_group_replay_review_if_ready
from trading_manager_tasks.model_group_residual_event_governance import _event_effect_profile, run_model_group_residual_event_governance_if_ready


class ModelGroupAttributionTests(unittest.TestCase):
    @staticmethod
    def _fake_approved_event_strategy_review(packet):
        return {
            "review_type": "event_strategy_promotion_review",
            "subject_ref": packet["subject_ref"],
            "decision": "approve",
            "pit_status": "passed",
            "control_status": "passed",
            "overlap_status": "residual_after_upstream_conditioning",
            "leakage_status": "passed",
            "allowed_model_use": ["temporal_attention_pool", "event_family_scouting"],
            "blocked_model_use": ["model_03_event_state_promotion"],
            "blocking_issues": [],
            "required_followups": ["retest before model_03_event_state_promotion"],
            "rationale": "Fixture review approves the deterministic temporal attention candidate.",
        }

    def _write_replay_dataset(self, storage_root: Path) -> Path:
        dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
        replay_run_root = dataset_root / "replay_execution_runs" / "model_group_replay_fixture"
        replay_run_root.mkdir(parents=True)
        with (dataset_root / "feed_acquisition_plan.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status"])
            writer.writeheader()
            writer.writerow({"month": "2021-01", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
            writer.writerow({"month": "2021-02", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
        (dataset_root / "replay_progress.jsonl").write_text(
            "\n".join(
                [
                    json.dumps({"stage_id": "model_group.replay", "month": "2021-01", "status": "completed"}),
                    json.dumps({"stage_id": "model_group.replay", "month": "2021-02", "status": "completed"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        decision_rows_path = replay_run_root / "decision_rows.jsonl"
        trace_rows_path = replay_run_root / "model_candidate_selection_trace.jsonl"
        decision_rows_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "decision_id": "filled_loss",
                            "fill_status": "simulated_filled",
                            "instrument_ref": "BTC-USDT",
                            "outcome_label": 0,
                            "timestamp": "2021-01-05T11:00:00-05:00",
                            "impact_exposure_time": "2021-01-05T10:10:00-05:00",
                            "future_outcome_window": "2021-01-05T11:00:00-05:00->2021-01-05T16:00:00-05:00",
                            "realized_return": -0.01,
                            "decision_intended_action": "open_long",
                            "decision_intended_side": "long",
                            "decision_expression_type": "long_call",
                            "selected_option_right": "call",
                            "underlying_return": -0.005,
                            "directional_underlying_return": -0.005,
                            "option_direction_consistency_status": "aligned",
                            "target_expected_move_abs_return": 0.02,
                        }
                    ),
                    json.dumps(
                        {
                            "decision_id": "filled_under_baseline",
                            "decision_status": "approved",
                            "outcome_label": 1,
                            "realized_return": 0.01,
                            "baseline_return": 0.02,
                            "month": "2021-01",
                            "decision_intended_action": "open_short",
                            "decision_intended_side": "short",
                            "decision_expression_type": "long_put",
                            "selected_option_right": "put",
                            "underlying_return": -0.01,
                            "directional_underlying_return": 0.01,
                            "option_direction_consistency_status": "aligned",
                            "future_outcome_window": "2021-01-06T10:00:00-05:00->2021-01-06T16:00:00-05:00",
                        }
                    ),
                    json.dumps(
                        {
                            "decision_id": "rejected_winner",
                            "decision_action": "reject_entry_thesis",
                            "decision_status": "rejected",
                            "outcome_label": 1,
                            "month": "2021-02",
                            "future_outcome_window": "2021-02-03T10:00:00-05:00->2021-02-03T16:00:00-05:00",
                            "replay_opportunity_return": 0.05,
                        }
                    ),
                    json.dumps(
                        {
                            "decision_id": "global_hindsight_winner",
                            "decision_status": "rejected",
                            "outcome_label": 1,
                            "month": "2021-02",
                            "path_conditioning_policy": "global_hindsight_oracle",
                            "candidate_set_scope": "global_candidate_universe",
                            "miss_attribution_layer": "global_hindsight_oracle",
                        }
                    ),
                    json.dumps(
                        {
                            "decision_id": "good_fill",
                            "fill_status": "simulated_filled",
                            "outcome_label": 1,
                            "realized_return": 0.04,
                            "baseline_return": 0.02,
                            "month": "2021-02",
                            "decision_intended_action": "open_short",
                            "decision_intended_side": "short",
                            "decision_expression_type": "long_put",
                            "selected_option_right": "put",
                            "underlying_return": -0.03,
                            "directional_underlying_return": 0.03,
                            "option_direction_consistency_status": "aligned",
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        trace_rows_path.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "contract_type": "model_candidate_selection_trace_row",
                            "target_ref": "AAPL",
                            "replay_time_pointer": "2021-01-05T16:00:00-05:00",
                            "model_score_available": True,
                            "selected_by_replay": True,
                            "model_candidate_trace_status": "selected_by_replay",
                            "model_rank_within_timestamp": 1,
                            "diagnostic_rank_score": 0.4,
                            "option_expression_signal_required": True,
                            "option_expression_selected_contract_available": True,
                            "portfolio_replacement_evaluation_status": "not_needed_capacity_available",
                            "portfolio_selection_action": "open_new_position",
                        }
                    ),
                    json.dumps(
                        {
                            "contract_type": "model_candidate_selection_trace_row",
                            "target_ref": "MSFT",
                            "replay_time_pointer": "2021-01-06T16:00:00-05:00",
                            "model_score_available": True,
                            "selected_by_replay": False,
                            "model_candidate_trace_status": "scored_not_selected_switch_threshold",
                            "model_rank_within_timestamp": 1,
                            "diagnostic_rank_score": 0.43,
                            "option_expression_signal_required": True,
                            "option_expression_selected_contract_available": True,
                            "portfolio_replacement_evaluation_status": "blocked_by_switch_threshold",
                            "portfolio_selection_action": "not_selected_keep_current_positions",
                            "portfolio_selection_reason": "candidate_not_significantly_better_than_weakest_held_position",
                            "portfolio_candidate_rank_score": 0.43,
                            "portfolio_worst_held_target_before": "AAPL",
                            "portfolio_worst_held_rank_score_before": 0.4,
                            "portfolio_switch_rank_score_delta": 0.03,
                            "portfolio_switch_minimum_rank_score_delta": 0.05,
                        }
                    ),
                    json.dumps(
                        {
                            "contract_type": "model_candidate_selection_trace_row",
                            "target_ref": "NVDA",
                            "replay_time_pointer": "2021-01-07T16:00:00-05:00",
                            "model_score_available": True,
                            "selected_by_replay": True,
                            "model_candidate_trace_status": "selected_by_replay_replacement",
                            "model_rank_within_timestamp": 1,
                            "diagnostic_rank_score": 0.55,
                            "option_expression_signal_required": True,
                            "option_expression_selected_contract_available": True,
                            "portfolio_replacement_evaluation_status": "triggered",
                            "portfolio_selection_action": "replace_weakest_held_position",
                            "portfolio_selection_reason": "candidate_significantly_better_than_weakest_held_position_after_switch_threshold",
                            "portfolio_candidate_rank_score": 0.55,
                            "portfolio_worst_held_target_before": "AAPL",
                            "portfolio_worst_held_rank_score_before": 0.4,
                            "portfolio_switch_rank_score_delta": 0.15,
                            "portfolio_switch_minimum_rank_score_delta": 0.05,
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (replay_run_root / "replay_execution_receipt.json").write_text(
            json.dumps(
                {
                    "contract_type": "evaluation_replay_execution_run",
                    "created_at_utc": "2026-05-28T00:00:00+00:00",
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                    },
                    "decision_rows_ref": str(decision_rows_path),
                    "model_candidate_selection_trace_ref": str(trace_rows_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return dataset_root

    def test_writes_post_replay_review_receipt_and_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_review_executed")
            receipt_paths = list((dataset_root / "post_replay_review_runs").glob("*/post_replay_review_receipt.json"))
            self.assertEqual(len(receipt_paths), 1)
            receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["contract_type"], "post_replay_review_receipt")
            self.assertEqual(receipt["reviewed_failure_count"], 3)
            self.assertEqual(receipt["residual_event_governance_status"], "not_performed")
            self.assertIs(receipt["event_evidence_consumed"], False)
            self.assertEqual(receipt["replay_review_diagnostic_summary"]["reviewed_row_count"], 3)
            self.assertIn("replay_review_performance_summary_ref", receipt)
            self.assertIn("layer_attribution_report_ref", receipt)
            performance_summary = json.loads(
                Path(receipt["replay_review_performance_summary_ref"]).read_text(encoding="utf-8")
            )
            self.assertEqual(performance_summary["contract_type"], "model_group_replay_review_performance_summary")
            self.assertEqual(performance_summary["summary"]["decision_scope"]["decision_row_count"], 5)

    def test_empty_replay_decision_rows_backoff_without_layer_attribution_error(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            decision_rows_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            decision_rows_path.write_text("", encoding="utf-8")

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_review_no_decision_rows")
            self.assertEqual(decision.execution_summary["decision_rows_ref"], str(decision_rows_path))
            self.assertEqual(
                list((dataset_root / "post_replay_review_runs").glob("*/post_replay_review_receipt.json")),
                [],
            )

    def test_scoped_empty_full_replay_writes_terminal_promotion_rejection(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            replay_root = dataset_root / "replay_execution_runs" / "model_group_replay_fixture"
            decision_rows_path = replay_root / "decision_rows.jsonl"
            decision_rows_path.write_text("", encoding="utf-8")
            receipt_path = replay_root / "replay_execution_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt.update(
                {
                    "candidate_fold_id": "fold_2016-01_2016-06",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                    "candidate_training_target": "AAPL",
                    "replay_execution_run_id": "model_group_replay_fixture",
                    "replay_completion_scope": "full_candidate_universe",
                }
            )
            receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
            (dataset_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "stage_id": "model_group.replay",
                                "month": "2021-01",
                                "status": "completed",
                                "replay_execution_run_id": "model_group_replay_fixture",
                            }
                        ),
                        json.dumps(
                            {
                                "stage_id": "model_group.replay",
                                "month": "2021-02",
                                "status": "completed",
                                "replay_execution_run_id": "model_group_replay_fixture",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_fold_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "target_symbol": "AAPL",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            dry_run_decision = run_model_group_replay_review_if_ready(storage_root=storage_root, execute=False)

            self.assertIsNotNone(dry_run_decision)
            assert dry_run_decision is not None
            self.assertEqual(dry_run_decision.decision_status, "ready")
            self.assertEqual(dry_run_decision.reason_code, "model_group_replay_no_decisions_rejection_ready")

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_no_decisions_rejected")
            rejection_path = Path(decision.execution_summary["promotion_eligibility_decision_ref"])
            rejection = json.loads(rejection_path.read_text(encoding="utf-8"))
            self.assertEqual(rejection["contract_type"], "promotion_eligibility_decision")
            self.assertEqual(rejection["decision_status"], "rejected")
            self.assertEqual(rejection["decision_reason_code"], "no_replay_decisions")
            self.assertEqual(rejection["fold_id"], "fold_2016-01_2016-06")
            self.assertEqual(rejection["candidate_model_ref"], "storage://trading-manager/model_group/aapl/2016-01_2016-06")
            self.assertEqual(rejection["source_fold_state_path"], str(state_path))
            self.assertEqual(
                list((dataset_root / "post_replay_review_runs").glob("*/post_replay_review_receipt.json")),
                [],
            )
            second = run_model_group_replay_review_if_ready(storage_root=storage_root)
            self.assertIsNone(second)
            second_dry_run = run_model_group_replay_review_if_ready(storage_root=storage_root, execute=False)
            self.assertIsNone(second_dry_run)

    def test_completed_replay_review_skips_replay_progress_scan(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_replay_dataset(storage_root)
            first = run_model_group_replay_review_if_ready(storage_root=storage_root)
            self.assertIsNotNone(first)

            with patch.object(model_group_attribution, "_ready_replay_months") as ready_months:
                second = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNone(second)
            ready_months.assert_not_called()

    def test_ready_without_execute_does_not_write_receipt(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root, execute=False)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "ready")
            self.assertEqual(decision.reason_code, "model_group_replay_review_ready")
            self.assertFalse((dataset_root / "post_replay_review_runs").exists())

    def test_missing_replay_review_outcome_data_writes_requirement_artifact(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            decision_rows_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            rows = [
                json.loads(line)
                for line in decision_rows_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            for row in rows:
                if row["decision_id"] == "rejected_winner":
                    row.pop("replay_opportunity_return", None)
                    row["realized_return"] = 0.0
                    row["selected_option_contract_ref"] = "AAPL_2021-02-05_C_140"
                    row["option_contract_path_status"] = "missing"
            decision_rows_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_review_data_required")
            summary = decision.execution_summary or {}
            self.assertEqual(summary["required_replay_review_data_count"], 1)
            self.assertIn("replay_missed_opportunity_return_materialization", summary["required_data_kinds"])
            self.assertEqual(summary["acquisition_routes"], ["model_group.replay_contract_paths"])
            requirements_path = Path(summary["requirements_artifact_ref"])
            requirements = [
                json.loads(line)
                for line in requirements_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(requirements), 1)
            self.assertEqual(requirements[0]["contract_type"], "post_replay_review_data_requirement")
            self.assertEqual(requirements[0]["source_decision_id"], "rejected_winner")
            self.assertIn("replay_opportunity_return", requirements[0]["missing_fields"])
            self.assertEqual(requirements[0]["acquisition_route"], "model_group.replay_contract_paths")
            self.assertFalse((dataset_root / "post_replay_review_runs").exists())

    def test_bounded_replay_receipt_does_not_unlock_replay_review(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            receipt_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "replay_execution_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["max_decision_rows"] = 5000
            receipt["replay_completion_scope"] = "bounded_diagnostic"
            receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNone(decision)

    def test_bounded_replay_review_receipt_does_not_lock_full_review(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)

            bounded_decision = run_model_group_replay_review_if_ready(
                storage_root=storage_root,
                max_review_rows=1,
                now_utc=datetime(2026, 6, 18, 11, 50, tzinfo=UTC),
            )

            self.assertIsNotNone(bounded_decision)
            assert bounded_decision is not None
            self.assertEqual(bounded_decision.decision_status, "executed")
            bounded_receipt_path = next((dataset_root / "post_replay_review_runs").glob("*/post_replay_review_receipt.json"))
            bounded_receipt = json.loads(bounded_receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(bounded_receipt["replay_review_completion_scope"], "bounded_diagnostic")
            self.assertEqual(bounded_receipt["max_review_rows"], 1)

            full_decision = run_model_group_replay_review_if_ready(
                storage_root=storage_root,
                now_utc=datetime(2026, 6, 18, 11, 51, tzinfo=UTC),
            )

            self.assertIsNotNone(full_decision)
            assert full_decision is not None
            self.assertEqual(full_decision.decision_status, "executed")
            receipt_paths = list((dataset_root / "post_replay_review_runs").glob("*/post_replay_review_receipt.json"))
            self.assertEqual(len(receipt_paths), 2)
            full_receipts = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in receipt_paths
                if json.loads(path.read_text(encoding="utf-8")).get("replay_review_completion_scope") == "full_replay_review"
            ]
            self.assertEqual(len(full_receipts), 1)
            self.assertEqual(full_receipts[0]["processed_review_count"], 3)

    def test_partial_replay_review_writes_diagnostic_without_unlocking_m06(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            (dataset_root / "replay_progress.jsonl").write_text(
                json.dumps({"stage_id": "model_group.replay", "month": "2021-01", "status": "completed"}) + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_review_if_ready(
                storage_root=storage_root,
                force=True,
                allow_partial_replay=True,
                now_utc=datetime(2026, 6, 18, 11, 52, tzinfo=UTC),
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            receipt_path = next((dataset_root / "post_replay_review_runs").glob("*/post_replay_review_receipt.json"))
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["replay_review_completion_scope"], "completed_replay_run_diagnostic")
            self.assertTrue(Path(receipt["replay_review_performance_summary_ref"]).exists())
            self.assertIsNone(run_model_group_residual_event_governance_if_ready(storage_root=storage_root))

    def test_newer_incompatible_replay_receipt_does_not_hide_latest_compatible_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            incompatible_root = dataset_root / "replay_execution_runs" / "newer_incompatible_replay"
            incompatible_root.mkdir(parents=True)
            compatible_rows = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            (incompatible_root / "decision_rows.jsonl").write_text(
                compatible_rows.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (incompatible_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "created_at_utc": "2026-06-18T12:30:00+00:00",
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "model_02_target_candidate_handoff",
                        "decision_rows_ref": str(incompatible_root / "decision_rows.jsonl"),
                        "replay_completion_scope": "full_candidate_universe",
                        "max_decision_rows": None,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(
                decision.execution_summary["decision_rows_ref"],
                str(compatible_rows),
            )

    def test_skips_when_attribution_receipt_already_exists(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            receipt_root = dataset_root / "post_replay_review_runs" / "existing"
            receipt_root.mkdir(parents=True)
            decision_rows_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            (receipt_root / "post_replay_review_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "post_replay_review_receipt",
                        "decision_rows_ref": str(decision_rows_path),
                        "status": "succeeded",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_review_if_ready(storage_root=storage_root)

            self.assertIsNone(decision)

    def test_writes_real_residual_event_governance_receipt_from_event_observation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            review_decision = run_model_group_replay_review_if_ready(storage_root=storage_root)
            self.assertIsNotNone(review_decision)
            observation_root = storage_root / "runtime" / "model_03_event_observation_inputs"
            observation_root.mkdir(parents=True)
            (observation_root / "2021-01_2021-02.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_03_event_observation_materialization",
                        "reviewed_event_interpretations": [
                            {
                                "contract_type": "event_interpretation",
                                "schema_version": "1",
                                "policy_version": "1",
                                "source_artifact_ref": "fixture://event/btc_liquidity_disruption",
                                "source_artifact_hash": "sha256:fixture",
                                "source_name": "fixture",
                                "source_type": "reviewed_fixture",
                                "published_time": "2021-01-05T10:00:00-05:00",
                                "available_time": "2021-01-05T10:05:00-05:00",
                                "interpreted_at": "2021-01-05T10:06:00-05:00",
                                "interpreter_agent_id": "unit",
                                "interpreter_model_id": "unit",
                                "prompt_policy_hash": "unit",
                                "normalized_event_type": "microstructure_liquidity_disruption",
                                "event_domain_tags": ["crypto", "liquidity"],
                                "affected_scope": "target",
                                "affected_entities": ["BTC"],
                                "direction_bias_score": -0.5,
                                "intensity_score": 0.8,
                                "uncertainty_score": 0.2,
                                "novelty_score": 0.7,
                                "source_quality_score": 0.8,
                                "evidence_confidence_score": 0.9,
                                "canonical_relation": {"relation_type": "canonical"},
                                "rationale_summary": "Fixture PIT event near the failed replay decision.",
                                "evidence_spans": [{"source_ref": "fixture://event/btc_liquidity_disruption"}],
                                "review_status": "reviewed",
                                "standardization_status": "standardized",
                            },
                            {
                                "contract_type": "event_interpretation",
                                "schema_version": "1",
                                "policy_version": "1",
                                "source_artifact_ref": "fixture://event/btc_liquidity_disruption_control",
                                "source_artifact_hash": "sha256:fixture-control",
                                "source_name": "fixture",
                                "source_type": "reviewed_fixture",
                                "published_time": "2021-01-20T10:00:00-05:00",
                                "available_time": "2021-01-20T10:05:00-05:00",
                                "interpreted_at": "2021-01-20T10:06:00-05:00",
                                "interpreter_agent_id": "unit",
                                "interpreter_model_id": "unit",
                                "prompt_policy_hash": "unit",
                                "normalized_event_type": "microstructure_liquidity_disruption",
                                "event_domain_tags": ["crypto", "liquidity"],
                                "affected_scope": "target",
                                "affected_entities": ["BTC"],
                                "direction_bias_score": -0.5,
                                "intensity_score": 0.7,
                                "uncertainty_score": 0.2,
                                "novelty_score": 0.7,
                                "source_quality_score": 0.8,
                                "evidence_confidence_score": 0.9,
                                "canonical_relation": {"relation_type": "canonical"},
                                "rationale_summary": "Fixture PIT same-family control occurrence without a matched replay failure.",
                                "evidence_spans": [{"source_ref": "fixture://event/btc_liquidity_disruption_control"}],
                                "review_status": "reviewed",
                                "standardization_status": "standardized",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_residual_event_governance_if_ready(
                storage_root=storage_root,
                agent_reviewer=self._fake_approved_event_strategy_review,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_residual_event_governance_executed")
            receipt_paths = list((dataset_root / "post_replay_attribution_runs").glob("*/post_replay_attribution_receipt.json"))
            self.assertEqual(len(receipt_paths), 1)
            receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["contract_type"], "post_replay_residual_event_governance_receipt")
            self.assertTrue(receipt["event_evidence_consumed"])
            self.assertEqual(receipt["event_candidate_count"], 2)
            self.assertEqual(receipt["event_observation_count"], 2)
            self.assertEqual(receipt["control_analysis_status"], "passed")
            rows = [
                json.loads(line)
                for line in Path(receipt["attribution_rows_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(rows[0]["contract_type"], "model_06_residual_event_governance_event_attribution_row")
            self.assertEqual(rows[0]["attribution_status"], "attributed")
            self.assertEqual(rows[0]["impact_exposure_time"], "2021-01-05T10:10:00-05:00")
            self.assertEqual(rows[0]["impact_onset_basis"], "source_impact_clock")
            self.assertEqual(rows[0]["impact_search_window_end"], "2021-01-05T10:10:00-05:00")
            self.assertEqual(rows[0]["impact_normalized_severity_score"], 0.5)
            self.assertEqual(receipt["event_focus_proposal_count"], 1)
            self.assertFalse(receipt["accepted_event_pool_mutation_performed"])
            self.assertTrue(receipt["temporal_attention_pool_mutation_performed"])
            self.assertEqual(receipt["temporal_attention_candidate_count"], 1)
            self.assertEqual(receipt["event_family_occurrence_scan_row_count"], 2)
            self.assertEqual(receipt["event_family_bias_association_packet_count"], 1)
            self.assertEqual(receipt["event_strategy_promotion_review_count"], 1)
            self.assertEqual(receipt["accepted_temporal_attention_pool_entry_count"], 1)
            proposals = [
                json.loads(line)
                for line in Path(receipt["event_focus_proposals_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(proposals), 1)
            self.assertEqual(proposals[0]["contract_type"], "model_06_residual_event_governance_event_focus_proposal")
            self.assertEqual(proposals[0]["stage_id"], "model_group.residual_event_governance")
            self.assertEqual(proposals[0]["proposal_status"], "watch_candidate")
            self.assertEqual(proposals[0]["event_summary"]["normalized_event_type"], "microstructure_liquidity_disruption")
            self.assertIn("Fixture PIT event", proposals[0]["event_summary"]["rationale_summary"])
            self.assertIn("BTC filled_negative_or_underperforming_outcome failures", proposals[0]["failure_attention_reason"])
            self.assertIn("requires_event_strategy_promotion_review", proposals[0]["acceptance_blockers"])
            candidates = [
                json.loads(line)
                for line in Path(receipt["temporal_attention_candidate_pool_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(candidates[0]["candidate_status"], "ready_for_agent_review")
            self.assertEqual(candidates[0]["event_temporal_form"], "instantaneous_unscheduled_event")
            self.assertEqual(candidates[0]["event_schedule_type"], "unscheduled")
            self.assertEqual(candidates[0]["event_family_prior_role"], "event_family_impact_parameterization")
            self.assertEqual(candidates[0]["model_03_event_projection_type"], "event_family_impact_state_projection")
            self.assertEqual(candidates[0]["event_family_impact_parameterization"]["severity_model"], "target_normalized_market_response")
            packets = [
                json.loads(line)
                for line in Path(receipt["event_family_bias_association_packets_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(packets[0]["deterministic_gate_status"], "passed")
            self.assertEqual(packets[0]["co_event_confounder_status"], "passed")
            self.assertEqual(packets[0]["impact_onset_status"], "passed")
            self.assertEqual(packets[0]["impact_severity_status"], "passed")
            self.assertEqual(packets[0]["impact_onset_basis_counts"], {"source_impact_clock": 1})
            self.assertEqual(packets[0]["event_temporal_form"], "instantaneous_unscheduled_event")
            self.assertEqual(packets[0]["event_temporal_form_counts"], {"instantaneous_unscheduled_event": 2})
            self.assertEqual(packets[0]["event_family_impact_parameterization"]["impact_curve_components"]["event_time_component"], "shock_onset")
            self.assertEqual(packets[0]["event_release_phase"], "post_release")
            self.assertEqual(packets[0]["event_lifecycle_stage"], "post_release_impact_state")
            self.assertEqual(packets[0]["state_signal_type"], "impact_state")
            self.assertEqual(packets[0]["model_03_event_state_overlay"], "event_post_release_impact_state")
            self.assertEqual(packets[0]["matched_occurrence_count"], 1)
            self.assertEqual(packets[0]["unmatched_occurrence_count"], 1)
            reviews = [
                json.loads(line)
                for line in Path(receipt["event_strategy_promotion_reviews_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(reviews[0]["decision"], "approve")
            accepted = [
                json.loads(line)
                for line in Path(receipt["accepted_temporal_attention_pool_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(accepted[0]["contract_type"], "model_06_residual_event_governance_temporal_attention_pool_entry")
            self.assertEqual(accepted[0]["pool_status"], "accepted")
            self.assertEqual(accepted[0]["event_temporal_form"], "instantaneous_unscheduled_event")
            self.assertEqual(accepted[0]["event_family_prior_role"], "event_family_impact_parameterization")
            self.assertEqual(accepted[0]["model_03_event_projection_type"], "event_family_impact_state_projection")
            self.assertEqual(accepted[0]["event_release_phase"], "post_release")
            self.assertEqual(accepted[0]["event_lifecycle_stage"], "post_release_impact_state")
            self.assertEqual(accepted[0]["state_signal_type"], "impact_state")
            self.assertEqual(accepted[0]["model_03_event_state_overlay"], "event_post_release_impact_state")
            self.assertFalse(receipt["model_03_event_state_promotion_performed"])

    def test_residual_event_governance_backoff_when_event_evidence_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            review_decision = run_model_group_replay_review_if_ready(storage_root=storage_root)
            self.assertIsNotNone(review_decision)

            decision = run_model_group_residual_event_governance_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_residual_event_evidence_missing")
            self.assertFalse((dataset_root / "post_replay_attribution_runs").exists())

    def test_event_effect_profile_keeps_earnings_in_pre_release_risk_stage(self):
        profile = _event_effect_profile("earnings_guidance_event_family")

        self.assertEqual(profile["event_temporal_form"], "scheduled_data_release_event")
        self.assertEqual(profile["event_schedule_type"], "scheduled_release_calendar")
        self.assertEqual(profile["event_instance_observation_role"], "scheduled_or_expected_release")
        self.assertEqual(profile["event_family_prior_role"], "event_family_impact_parameterization")
        self.assertEqual(profile["event_family_impact_parameterization"]["impact_curve_components"]["event_time_component"], "release_shock")
        self.assertEqual(profile["event_release_phase"], "pre_release")
        self.assertEqual(profile["event_lifecycle_stage"], "pre_release_risk_state")
        self.assertEqual(profile["state_signal_type"], "risk_state")
        self.assertEqual(profile["model_03_event_state_overlay"], "event_pre_release_risk_state_change")

    def test_event_effect_profile_turns_released_earnings_into_post_release_impact_stage(self):
        profile = _event_effect_profile(
            "earnings_guidance_event_family",
            information_role_type="released_result",
            text="Company reported earnings results after market close.",
        )

        self.assertEqual(profile["event_temporal_form"], "scheduled_data_release_event")
        self.assertEqual(profile["event_schedule_type"], "scheduled_release_calendar")
        self.assertEqual(profile["event_instance_observation_role"], "observed_release")
        self.assertEqual(profile["event_release_phase"], "post_release")
        self.assertEqual(profile["event_lifecycle_stage"], "post_release_impact_state")
        self.assertEqual(profile["state_signal_type"], "impact_state")
        self.assertEqual(profile["model_03_event_state_overlay"], "event_post_release_impact_state")

    def test_event_effect_profile_represents_scheduled_calendar_events(self):
        profile = _event_effect_profile("triple_witching", information_role_type="calendar", text="Known options expiration calendar event.")

        self.assertEqual(profile["event_temporal_form"], "scheduled_calendar_event")
        self.assertEqual(profile["event_schedule_type"], "scheduled_periodic_calendar")
        self.assertEqual(profile["event_instance_observation_role"], "calendar_state")
        self.assertEqual(profile["state_signal_type"], "risk_state")
        self.assertEqual(profile["event_family_impact_parameterization"]["impact_curve_components"]["event_time_component"], "session_or_expiration_mechanics")

    def test_event_effect_profile_represents_unscheduled_instant_events(self):
        profile = _event_effect_profile("breaking_news", text="Unexpected trading halt shock.")

        self.assertEqual(profile["event_temporal_form"], "instantaneous_unscheduled_event")
        self.assertEqual(profile["event_schedule_type"], "unscheduled")
        self.assertEqual(profile["event_instance_observation_role"], "observed_shock")
        self.assertEqual(profile["state_signal_type"], "impact_state")
        self.assertEqual(profile["event_family_impact_parameterization"]["impact_curve_components"]["event_time_component"], "shock_onset")


if __name__ == "__main__":
    unittest.main()

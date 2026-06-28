from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.model_group_evaluation import (
    _build_promotion_eligibility_decision,
    _build_promotion_review_packet,
    _build_settlement_run,
    _decision_variable_schema_diagnostics,
    _is_filled_trade_row,
    _scored_rows,
    _temporal_stability_diagnostics,
    run_model_group_evaluation_if_ready,
)


class ModelGroupEvaluationTests(unittest.TestCase):
    def _fake_deferred_agent_review(self, packet):
        return {
            "review_type": "promotion_evaluation_review",
            "candidate_label": packet["candidate_label"],
            "fold_id": packet["fold_id"],
            "benchmark_contract_ref": packet["benchmark_contract_ref"],
            "comparison_label": packet["comparison_label"],
            "recommendation": "deferred",
            "confidence": "medium",
            "identity_blinding_status": "insufficient_evidence",
            "integrity_status": "passed",
            "hard_guardrail_status": packet["hard_guardrail_status"],
            "comparison_status": "insufficient_evidence",
            "uncertainty_status": "insufficient_evidence",
            "shadow_readiness_status": "insufficient_evidence",
            "material_improvements": ["settlement evidence was available"],
            "material_regressions": packet["material_regressions"],
            "blocking_issues": packet["blocking_issues"],
            "required_followups": packet["required_followups"],
            "rationale": "Agent deferred because anonymous comparison, config, and first-run evidence are missing.",
        }

    def _write_completed_fold(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True)
        stages = []
        for layer in range(1, 7):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"layer_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"layer_{layer:02d}_fixture",
                        "status": "succeeded",
                        "dataset_split": {
                            "split_name": split_name,
                            "split_policy": "chronological_rolling_fold_4_1_1",
                        },
                    }
                )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_completed_fold_two(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-07_2016-12.json"
        state_path.parent.mkdir(parents=True)
        stages = []
        for layer in range(1, 7):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"layer_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"layer_{layer:02d}_fixture",
                        "status": "succeeded",
                        "dataset_split": {
                            "split_name": split_name,
                            "split_policy": "chronological_rolling_fold_4_1_1",
                        },
                    }
                )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-07",
                    "end_month": "2016-12",
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_pre_replay_complete_fold_with_pending_m06_generation(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True)
        stages = []
        for layer in range(1, 6):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"layer_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"layer_{layer:02d}_fixture",
                        "status": "succeeded",
                        "dataset_split": {
                            "split_name": split_name,
                            "split_policy": "chronological_rolling_fold_4_1_1",
                        },
                    }
                )
        for split_name, status in (("train", "ready"), ("validation", "blocked"), ("test", "blocked")):
            stages.append(
                {
                    "stage_id": f"layer_06_fixture.model_generation.{split_name}",
                    "stage_type": "model_generation",
                    "layer": 6,
                    "layer_key": "layer_06_fixture",
                    "status": status,
                    "dataset_split": {
                        "split_name": split_name,
                        "split_policy": "chronological_rolling_fold_4_1_1",
                    },
                }
            )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def test_temporal_stability_publishes_monthly_return_path_ohlc(self):
        diagnostics = _temporal_stability_diagnostics(
            [
                {"timestamp": "2021-01-02T00:00:00Z", "label": 1, "score": 0.8, "net_return": 0.10},
                {"timestamp": "2021-01-03T00:00:00Z", "label": 0, "score": 0.2, "net_return": -0.30},
                {"timestamp": "2021-01-04T00:00:00Z", "label": 1, "score": 0.7, "net_return": 0.05},
            ]
        )

        self.assertEqual(
            diagnostics["slices"][0]["net_return_path_ohlc"],
            {"open": 1.0, "high": 1.1, "low": 0.8, "close": 0.85},
        )

    def _write_ready_replay_and_attribution(self, storage_root: Path) -> Path:
        dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
        replay_run_root = dataset_root / "replay_execution_runs" / "model_group_replay_fixture"
        attribution_root = dataset_root / "post_replay_attribution_runs" / "post_replay_attribution_fixture"
        replay_run_root.mkdir(parents=True)
        attribution_root.mkdir(parents=True)
        with (dataset_root / "feed_acquisition_plan.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status"])
            writer.writeheader()
            writer.writerow({"month": "2021-01", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
        decision_rows_path = replay_run_root / "decision_rows.jsonl"
        rows = []
        for index in range(30):
            positive = index % 3 != 0
            rows.append(
                {
                    "decision_id": f"d{index}",
                    "realized_return": 0.03 if positive else -0.01,
                    "baseline_return": 0.005,
                    "cost": 0.001,
                    "outcome_label": 1 if positive else 0,
                    "prediction_score": 0.8 if positive else 0.2,
                    "action": "trade" if positive else "skip",
                    "decision_status": "approved" if positive else "rejected",
                    "fill_status": "simulated_filled" if positive else "simulated_rejected",
                    "resolved_action_side": "long" if positive else "flat",
                    "4_resolved_underlying_action_type": "open_long" if positive else "no_trade",
                    "feature_momentum_7d": 0.8 if positive else -0.3,
                    "feature_momentum_30d": 0.6 if positive else -0.2,
                    "feature_volume_rank_30d": (index % 5) / 5,
                }
            )
        decision_rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        replay_receipt_path = replay_run_root / "replay_execution_receipt.json"
        replay_receipt_path.write_text(
            json.dumps(
                {
                    "contract_type": "evaluation_replay_execution_run",
                    "created_at_utc": "2026-05-28T00:00:00+00:00",
                    "candidate_model_ref": "storage://trading-manager/model_group/2016-01_2016-06",
                    "pre_replay_target_refs": ["AAPL"],
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                    "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                    },
                    "decision_rows_ref": str(decision_rows_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        attribution_rows_path = attribution_root / "failure_attribution_rows.jsonl"
        attribution_rows_path.write_text(
            json.dumps(
                {
                    "contract_type": "model_06_residual_event_governance_event_attribution_row",
                    "attribution_id": "attr_1",
                    "event_candidate_ref": "event_candidate_fixture",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        proposal_rows_path = attribution_root / "event_focus_proposals.jsonl"
        proposal_rows_path.write_text(
            json.dumps(
                {
                    "contract_type": "model_06_residual_event_governance_event_focus_proposal",
                    "event_focus_proposal_id": "focus_1",
                    "proposal_status": "watch_candidate",
                    "event_ref": "event_candidate_fixture",
                    "supporting_failure_count": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (attribution_root / "post_replay_attribution_receipt.json").write_text(
            json.dumps(
                {
                    "contract_type": "post_replay_residual_event_governance_receipt",
                    "status": "succeeded",
                    "created_at_utc": "2026-05-28T00:00:01+00:00",
                    "decision_rows_ref": str(decision_rows_path),
                    "attribution_rows_ref": str(attribution_rows_path),
                    "event_focus_proposals_ref": str(proposal_rows_path),
                    "event_focus_proposal_count": 1,
                    "event_evidence_consumed": True,
                    "event_observation_count": 1,
                    "event_candidate_count": 1,
                    "replay_review_scope_status": "passed",
                    "control_analysis_status": "passed",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return dataset_root

    def test_ignores_replay_review_as_residual_event_governance(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_ready_replay_and_attribution(storage_root)
            self._write_completed_fold(storage_root)
            shutil.rmtree(dataset_root / "post_replay_attribution_runs")
            review_root = dataset_root / "post_replay_review_runs" / "post_replay_review_fixture"
            review_root.mkdir(parents=True)
            review_rows = review_root / "replay_review_rows.jsonl"
            review_rows.write_text(
                json.dumps({"contract_type": "post_replay_review_row", "review_status": "reviewed"}) + "\n",
                encoding="utf-8",
            )
            (review_root / "post_replay_review_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "post_replay_review_receipt",
                        "status": "succeeded",
                        "created_at_utc": "2026-05-28T00:00:01+00:00",
                        "decision_rows_ref": str(dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"),
                        "review_rows_ref": str(review_rows),
                        "residual_event_governance_status": "not_performed",
                        "event_evidence_consumed": False,
                        "event_observation_count": 0,
                        "event_candidate_count": 0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_evaluation_if_ready(
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                agent_reviewer=self._fake_deferred_agent_review,
            )

            self.assertIsNone(decision)
            self.assertFalse((dataset_root / "promotion_review_runs").exists())

    def test_writes_model_group_evaluation_and_promotion_review_artifacts(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_ready_replay_and_attribution(storage_root)
            self._write_completed_fold(storage_root)

            decision = run_model_group_evaluation_if_ready(
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                agent_reviewer=self._fake_deferred_agent_review,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.reason_code, "model_group_evaluation_executed")
            review_paths = list((dataset_root / "promotion_review_runs").glob("*/promotion_evaluation_review.json"))
            decision_paths = list((dataset_root / "promotion_review_runs").glob("*/promotion_eligibility_decision.json"))
            settlement_paths = list((dataset_root / "fold_settlement_runs").glob("*/fold_settlement_run.json"))
            receipt_paths = list((dataset_root / "promotion_review_runs").glob("*/model_group_evaluation_receipt.json"))
            self.assertEqual(len(review_paths), 1)
            self.assertEqual(len(decision_paths), 1)
            self.assertEqual(len(settlement_paths), 1)
            self.assertEqual(len(receipt_paths), 1)
            receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["ready_check_count"], 5)
            self.assertIn("residual_event_governance_event_focus_proposal", receipt["ready_checks"])
            review = json.loads(review_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(review["agent_invocation_status"], "completed")
            self.assertEqual(review["recommendation"], "deferred")
            eligibility = json.loads(decision_paths[0].read_text(encoding="utf-8"))
            settlement = json.loads(settlement_paths[0].read_text(encoding="utf-8"))
            metrics = settlement["metrics"]
            self.assertEqual(eligibility["contract_type"], "promotion_eligibility_decision")
            self.assertEqual(settlement["target_symbol"], "AAPL")
            self.assertEqual(eligibility["target_symbol"], "AAPL")
            self.assertEqual(settlement["candidate_model_ref"], "storage://trading-manager/model_group/aapl/2016-01_2016-06")
            self.assertEqual(eligibility["decision_status"], "deferred")
            self.assertEqual(eligibility["agent_review_recommendation"], "deferred")
            self.assertEqual(metrics["feature_column_count"], 3)
            self.assertEqual(metrics["feature_row_count"], 30)
            self.assertTrue(metrics["pca_available"])
            self.assertTrue(metrics["pcoa_available"])
            self.assertIsInstance(metrics["pr_auc"], float)
            self.assertIsInstance(metrics["ece"], float)
            self.assertIsInstance(metrics["profit_factor"], float)
            self.assertEqual(metrics["data_integrity_status"], "warning")
            self.assertEqual(metrics["decision_variable_schema_status"], "passed")
            self.assertEqual(metrics["decision_intended_side_unknown_count"], 0)
            self.assertEqual(metrics["decision_agency_unknown_count"], 0)
            self.assertIn("predictive_diagnostics", metrics)
            roc_curve = metrics["predictive_diagnostics"]["roc_curve"]
            self.assertGreaterEqual(len(roc_curve), 3)
            self.assertEqual(roc_curve[0]["false_positive_rate"], 0.0)
            self.assertEqual(roc_curve[0]["true_positive_rate"], 0.0)
            self.assertEqual(roc_curve[-1]["false_positive_rate"], 1.0)
            self.assertEqual(roc_curve[-1]["true_positive_rate"], 1.0)
            self.assertIn("calibration_diagnostics", metrics)
            self.assertIn("economic_diagnostics", metrics)
            self.assertIn("data_integrity_diagnostics", metrics)
            self.assertIn("decision_variable_schema_diagnostics", metrics)
            variable_diagnostics = metrics["decision_variable_schema_diagnostics"]
            self.assertEqual(variable_diagnostics["feature_namespace_leakage_status"], "passed")
            self.assertEqual(variable_diagnostics["coverage"]["decision_intended_side"]["values"]["long"], 20)
            self.assertEqual(variable_diagnostics["coverage"]["decision_intended_side"]["values"]["flat"], 10)
            self.assertEqual(variable_diagnostics["coverage"]["decision_disposition"]["values"]["accepted"], 20)
            self.assertEqual(variable_diagnostics["coverage"]["decision_disposition"]["values"]["rejected"], 10)
            self.assertIn("taken_good", variable_diagnostics["coverage"]["eval_action_class"]["values"])
            self.assertIn("positive_excess", variable_diagnostics["coverage"]["eval_economic_class"]["values"])
            self.assertIn("eval_action_class", variable_diagnostics["normalized_row_samples"][0])
            self.assertIn("scorecards", metrics)
            self.assertFalse(settlement["gate_failures"])
            self.assertEqual(metrics["high_score_tail_risk_diagnostics"]["high_score_filled_loss_count"], 0)
            self.assertFalse(metrics["evaluation_disagreement_report"]["promotion_gate_basis"]["auroc_is_hard_gate"])
            self.assertIn("score_decile_return", metrics["scorecards"]["ranking_calibration"])
            self.assertEqual(metrics["scorecards"]["selection_quality"]["taken_good_count"], 20)
            self.assertGreater(metrics["scorecards"]["economic_quality"]["excess_return_total"], 0)
            self.assertEqual(metrics["scorecards"]["slices"]["decision_intended_side"][1]["value"], "long")
            self.assertEqual(metrics["diagnostic_availability"]["feature_space"]["status"], "available")
            self.assertEqual(metrics["diagnostic_availability"]["slice_distribution"]["status"], "available")
            self.assertIn("temporal_stability_diagnostics", metrics)
            self.assertIn("baseline_comparison_diagnostics", metrics)
            self.assertIsInstance(metrics["silhouette_outcome_label"], float)
            self.assertIn("feature_diagnostics", metrics)

            second = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")
            self.assertIsNone(second)

            replay_decision_rows = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            refreshed_attribution_root = dataset_root / "post_replay_attribution_runs" / "post_replay_attribution_refreshed"
            refreshed_attribution_root.mkdir(parents=True)
            refreshed_attribution_rows = refreshed_attribution_root / "residual_event_governance_rows.jsonl"
            refreshed_attribution_rows.write_text(
                json.dumps(
                    {
                        "contract_type": "model_06_residual_event_governance_event_attribution_row",
                        "attribution_id": "attr_2",
                        "event_candidate_ref": "event_candidate_refreshed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            refreshed_proposal_rows = refreshed_attribution_root / "event_focus_proposals.jsonl"
            refreshed_proposal_rows.write_text(
                json.dumps(
                    {
                        "contract_type": "model_06_residual_event_governance_event_focus_proposal",
                        "event_focus_proposal_id": "focus_2",
                        "proposal_status": "watch_candidate",
                        "event_ref": "event_candidate_refreshed",
                        "supporting_failure_count": 1,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            refreshed_attribution_receipt = refreshed_attribution_root / "post_replay_attribution_receipt.json"
            refreshed_attribution_receipt.write_text(
                json.dumps(
                    {
                        "contract_type": "post_replay_residual_event_governance_receipt",
                        "status": "succeeded",
                        "created_at_utc": "2026-05-28T00:00:03+00:00",
                        "decision_rows_ref": str(replay_decision_rows),
                        "attribution_rows_ref": str(refreshed_attribution_rows),
                        "event_focus_proposals_ref": str(refreshed_proposal_rows),
                        "event_focus_proposal_count": 1,
                        "event_evidence_consumed": True,
                        "event_observation_count": 1,
                        "event_candidate_count": 2,
                        "replay_review_scope_status": "passed",
                        "control_analysis_status": "passed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            refreshed_attribution_decision = run_model_group_evaluation_if_ready(
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                now_utc=datetime(2026, 5, 28, 0, 0, 4, tzinfo=UTC),
                agent_reviewer=self._fake_deferred_agent_review,
            )
            self.assertIsNotNone(refreshed_attribution_decision)
            assert refreshed_attribution_decision is not None
            self.assertEqual(refreshed_attribution_decision.reason_code, "model_group_evaluation_executed")
            receipt_paths = list((dataset_root / "promotion_review_runs").glob("*/model_group_evaluation_receipt.json"))
            self.assertEqual(len(receipt_paths), 2)
            latest_receipt_path = max(receipt_paths, key=lambda path: path.stat().st_mtime)
            latest_receipt = json.loads(latest_receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(latest_receipt["residual_event_governance_receipt_ref"], str(refreshed_attribution_receipt))

            state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            newer_mtime = max(path.stat().st_mtime for path in (dataset_root / "promotion_review_runs").glob("*/promotion_eligibility_decision.json")) + 1
            os.utime(state_path, (newer_mtime, newer_mtime))

            refreshed = run_model_group_evaluation_if_ready(
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                now_utc=datetime(2026, 5, 28, 0, 0, 5, tzinfo=UTC),
                agent_reviewer=self._fake_deferred_agent_review,
            )
            self.assertIsNotNone(refreshed)
            assert refreshed is not None
            self.assertEqual(refreshed.reason_code, "model_group_evaluation_executed")
            self.assertEqual(len(list((dataset_root / "promotion_review_runs").glob("*/promotion_eligibility_decision.json"))), 3)

    def test_evaluates_pre_replay_complete_fold_with_pending_m06_generation_stages(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_ready_replay_and_attribution(storage_root)
            self._write_pre_replay_complete_fold_with_pending_m06_generation(storage_root)

            decision = run_model_group_evaluation_if_ready(
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                call_agent_review=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.reason_code, "model_group_evaluation_executed")

    def test_local_fallback_review_writes_terminal_deferred_decision(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_ready_replay_and_attribution(storage_root)
            self._write_completed_fold(storage_root)

            decision = run_model_group_evaluation_if_ready(
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                call_agent_review=False,
            )

            self.assertIsNotNone(decision)
            decision_path = next((dataset_root / "promotion_review_runs").glob("*/promotion_eligibility_decision.json"))
            review_path = next((dataset_root / "promotion_review_runs").glob("*/promotion_evaluation_review.json"))
            review = json.loads(review_path.read_text(encoding="utf-8"))
            eligibility = json.loads(decision_path.read_text(encoding="utf-8"))
            self.assertEqual(review["agent_invocation_status"], "not_invoked_local_fallback")
            self.assertEqual(review["recommendation"], "insufficient_evidence")
            self.assertEqual(eligibility["decision_status"], "deferred")
            self.assertEqual(eligibility["agent_review_recommendation"], "insufficient_evidence")

    def test_placeholder_crypto_replay_does_not_unlock_evaluation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_ready_replay_and_attribution(storage_root)
            self._write_completed_fold(storage_root)
            receipt_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "replay_execution_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["candidate_model_ref"] = "trading-model://candidate_policy_replay/current_deterministic_crypto_policy"
            receipt["target_refs"] = ["BTC", "ETH", "SOL"]
            receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

            decision = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_evaluation_replay_scope_mismatch")
            self.assertIn("deterministic crypto placeholder", decision.reason)

    def test_stale_prior_fold_replay_receipt_does_not_unlock_evaluation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_ready_replay_and_attribution(storage_root)
            self._write_completed_fold_two(storage_root)

            decision = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")

            self.assertIsNone(decision)

    def test_replay_receipt_base_context_without_training_symbol_unlocks_evaluation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_ready_replay_and_attribution(storage_root)
            self._write_completed_fold(storage_root)
            receipt_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "replay_execution_receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["target_refs"] = ["BTC", "ETH", "SOL"]
            receipt["pre_replay_target_refs"] = ["BTC", "ETH", "SOL"]
            receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

            decision = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertNotEqual(decision.reason_code, "model_group_evaluation_replay_scope_mismatch")

    def test_decision_variable_audit_does_not_infer_side_from_outcome(self):
        rows = [
            {
                "decision_id": "missing_side_positive",
                "realized_return": 0.04,
                "baseline_return": 0.01,
                "outcome_label": 1,
                "prediction_score": 0.8,
                "feature_eval_outcome_label": 1,
            }
        ]

        diagnostics = _decision_variable_schema_diagnostics(
            decision_rows=rows,
            net_returns=[0.04],
            baseline_returns=[0.01],
            costs=[0.0],
        )

        self.assertEqual(diagnostics["coverage"]["decision_intended_side"]["values"]["unknown"], 1)
        self.assertEqual(diagnostics["feature_namespace_leakage_status"], "warning")
        self.assertIn("feature_eval_outcome_label", diagnostics["feature_namespace_leakage_columns"])
        self.assertEqual(diagnostics["normalized_row_samples"][0]["eval_economic_class"], "positive_excess")

    def test_rejected_entry_thesis_rows_are_flat_not_unknown_side(self):
        rows = [
            {
                "decision_id": "rejected_entry",
                "realized_return": 0.0,
                "baseline_return": 0.0,
                "outcome_label": 0,
                "prediction_score": 0.2,
                "decision_action": "reject_entry_thesis",
                "action": "reject_entry_thesis",
                "decision_status": "rejected",
                "fill_status": "simulated_rejected",
            }
        ]

        diagnostics = _decision_variable_schema_diagnostics(
            decision_rows=rows,
            net_returns=[0.0],
            baseline_returns=[0.0],
            costs=[0.0],
        )

        self.assertEqual(diagnostics["coverage"]["decision_intended_side"]["values"]["flat"], 1)
        self.assertEqual(diagnostics["coverage"]["decision_intended_action"]["values"]["no_trade"], 1)
        self.assertEqual(diagnostics["coverage"]["decision_disposition"]["values"]["rejected"], 1)

    def test_rejected_entry_thesis_uses_market_path_for_missed_opportunity(self):
        rows = [
            {
                "decision_id": "missed_up_move",
                "realized_return": 0.0,
                "baseline_return": 0.0,
                "cost": 0.0,
                "outcome_label": 1,
                "prediction_score": 0.8,
                "decision_action": "reject_entry_thesis",
                "action": "reject_entry_thesis",
                "decision_status": "rejected",
                "fill_status": "simulated_rejected",
                "bar_close": 100.0,
                "next_bar_close": 105.0,
            },
            {
                "decision_id": "avoided_down_move",
                "realized_return": 0.0,
                "baseline_return": 0.0,
                "cost": 0.0,
                "outcome_label": 0,
                "prediction_score": 0.2,
                "decision_action": "reject_entry_thesis",
                "action": "reject_entry_thesis",
                "decision_status": "rejected",
                "fill_status": "simulated_rejected",
                "bar_close": 100.0,
                "next_bar_close": 95.0,
            },
        ]

        diagnostics = _decision_variable_schema_diagnostics(
            decision_rows=rows,
            net_returns=[0.0, 0.0],
            baseline_returns=[0.0, 0.0],
            costs=[0.0, 0.0],
        )

        self.assertEqual(diagnostics["coverage"]["eval_action_class"]["values"]["missed_good"], 1)
        self.assertEqual(diagnostics["coverage"]["eval_action_class"]["values"]["avoided_bad"], 1)
        missed_sample = diagnostics["normalized_row_samples"][0]
        self.assertEqual(missed_sample["replay_cost_adjusted_return"], 0.0)
        self.assertEqual(missed_sample["replay_excess_return"], 0.0)
        self.assertEqual(missed_sample["replay_opportunity_return"], 0.05)
        self.assertEqual(missed_sample["replay_opportunity_excess_return"], 0.05)
        self.assertEqual(missed_sample["eval_economic_class"], "positive_excess")
        self.assertEqual(missed_sample["eval_action_class"], "missed_good")
        self.assertEqual(missed_sample["miss_review_scope"], "path_conditioned_current_scope")
        self.assertEqual(missed_sample["candidate_set_scope"], "selected_path_current_decision_set")

    def test_global_hindsight_positive_is_not_scored_as_missed_good(self):
        rows = [
            {
                "decision_id": "global_hindsight_winner",
                "realized_return": 0.0,
                "baseline_return": 0.0,
                "cost": 0.0,
                "outcome_label": 1,
                "prediction_score": 0.8,
                "decision_action": "reject_entry_thesis",
                "action": "reject_entry_thesis",
                "decision_status": "rejected",
                "fill_status": "simulated_rejected",
                "bar_close": 100.0,
                "next_bar_close": 105.0,
                "path_conditioning_policy": "global_hindsight_oracle",
                "candidate_set_scope": "global_candidate_universe",
                "miss_attribution_layer": "global_hindsight_oracle",
            }
        ]

        diagnostics = _decision_variable_schema_diagnostics(
            decision_rows=rows,
            net_returns=[0.0],
            baseline_returns=[0.0],
            costs=[0.0],
        )

        self.assertEqual(diagnostics["coverage"]["eval_action_class"]["values"].get("missed_good", 0), 0)
        self.assertEqual(diagnostics["coverage"]["eval_action_class"]["values"]["unscored_global_good"], 1)
        sample = diagnostics["normalized_row_samples"][0]
        self.assertEqual(sample["miss_review_scope"], "not_path_conditioned")
        self.assertEqual(sample["eval_action_class"], "unscored_global_good")

    def test_suitable_missing_option_path_rows_are_skipped_unscored_and_unfilled(self):
        rows = [
            {
                "decision_id": "missing_option_path",
                "realized_return": 0.0,
                "baseline_return": 0.0,
                "cost": 0.0,
                "outcome_label": None,
                "prediction_score": 0.99,
                "action": "trade",
                "decision_status": "suitable",
                "fill_status": "simulated_rejected",
                "selected_option_contract_ref": "AAPL_2021-01-15_C_100",
                "option_contract_path_status": "missing",
                "4_resolved_underlying_action_type": "open_long",
            }
        ]

        diagnostics = _decision_variable_schema_diagnostics(
            decision_rows=rows,
            net_returns=[0.0],
            baseline_returns=[0.0],
            costs=[0.0],
        )

        self.assertFalse(_is_filled_trade_row(rows[0]))
        self.assertEqual(_scored_rows(rows, [0.0], [0.0], [0.0]), [])
        self.assertEqual(diagnostics["coverage"]["decision_disposition"]["values"]["skipped"], 1)
        self.assertNotIn("accepted", diagnostics["coverage"]["decision_disposition"]["values"])

    def test_high_score_tail_loss_overconfidence_blocks_promotion_settlement(self):
        rows = []
        for index in range(6):
            rows.append(
                {
                    "decision_id": f"loss{index}",
                    "timestamp": f"2021-01-0{index + 1}T16:00:00-05:00",
                    "realized_return": -0.20,
                    "baseline_return": 0.0,
                    "cost": 0.0,
                    "outcome_label": 0,
                    "prediction_score": 0.84,
                    "action": "trade",
                    "decision_status": "approved",
                    "fill_status": "simulated_filled",
                    "resolved_action_side": "long",
                    "4_resolved_underlying_action_type": "open_long",
                    "selected_option_contract_ref": "AAPL_2021-01-08_C_130",
                }
            )
        for index in range(6):
            rows.append(
                {
                    "decision_id": f"win{index}",
                    "timestamp": f"2021-02-0{index + 1}T16:00:00-05:00",
                    "realized_return": 0.25,
                    "baseline_return": 0.0,
                    "cost": 0.0,
                    "outcome_label": 1,
                    "prediction_score": 0.841,
                    "action": "trade",
                    "decision_status": "approved",
                    "fill_status": "simulated_filled",
                    "resolved_action_side": "long",
                    "4_resolved_underlying_action_type": "open_long",
                    "selected_option_contract_ref": "AAPL_2021-02-05_C_130",
                }
            )
        for index in range(12):
            rows.append(
                {
                    "decision_id": f"skip{index}",
                    "timestamp": f"2021-03-{index + 1:02d}T16:00:00-05:00",
                    "realized_return": 0.0,
                    "baseline_return": 0.0,
                    "cost": 0.0,
                    "outcome_label": 0,
                    "prediction_score": 0.2,
                    "action": "skip",
                    "decision_status": "rejected",
                    "fill_status": "simulated_rejected",
                    "resolved_action_side": "flat",
                    "4_resolved_underlying_action_type": "no_trade",
                }
            )

        settlement = _build_settlement_run(
            fold_id="fold_tail",
            target_symbol="AAPL",
            candidate_model_ref="storage://candidate/tail-risk",
            replay_contract_ref="trading-evaluation/replays/promotion_replay_candidate_policy.json",
            replay_result_ref="storage://replay/tail-risk",
            decision_rows=rows,
            created_at_utc="2026-06-13T20:00:00+00:00",
        )

        diagnostics = settlement["metrics"]["high_score_tail_risk_diagnostics"]
        self.assertIn("high_score_tail_loss_overconfidence", settlement["gate_failures"])
        self.assertIn("high_score_tail_loss_sample_limited", settlement["gate_failures"])
        self.assertEqual(diagnostics["model_overconfidence_status"], "failed")
        self.assertEqual(diagnostics["option_selection_mechanics_status"], "weakly_supported")
        self.assertEqual(diagnostics["short_dte_tail_loss_count"], 6)
        self.assertEqual(diagnostics["minimum_short_dte_tail_loss_count"], 5)
        self.assertEqual(diagnostics["sample_sufficiency_status"], "sample_limited")

        packet = _build_promotion_review_packet(
            settlement=settlement,
            settlement_ref="/tmp/fold_settlement_run.json",
            benchmark_contract_ref="trading-evaluation/replays/promotion_replay_candidate_policy.json",
            residual_event_governance_ref="/tmp/post_replay_attribution_receipt.json",
            created_at_utc="2026-06-13T20:00:00+00:00",
        )

        self.assertEqual(packet["recommendation"], "insufficient_evidence")
        self.assertIn("high_score_tail_loss_overconfidence", packet["material_regressions"])
        self.assertTrue(
            any("feature_timing_or_leakage evidence" in followup for followup in packet["required_followups"])
        )

        eligibility = _build_promotion_eligibility_decision(
            settlement=settlement,
            review=packet,
            settlement_ref="/tmp/fold_settlement_run.json",
            review_ref="/tmp/promotion_evaluation_review.json",
            replay_contract_ref="trading-evaluation/replays/promotion_replay_candidate_policy.json",
            created_at_utc="2026-06-13T20:00:00+00:00",
        )

        self.assertEqual(eligibility["guardrail_status"], "failed")
        self.assertEqual(eligibility["decision_status"], "rejected")

    def test_high_score_tail_loss_inverted_score_gap_blocks_even_with_sufficient_sample(self):
        rows = []
        for index in range(6):
            rows.append(
                {
                    "decision_id": f"inverted_loss{index}",
                    "timestamp": f"2021-04-{index + 1:02d}T16:00:00-04:00",
                    "realized_return": -0.10,
                    "baseline_return": 0.0,
                    "cost": 0.0,
                    "outcome_label": 0,
                    "prediction_score": 0.90,
                    "action": "trade",
                    "decision_status": "approved",
                    "fill_status": "simulated_filled",
                    "resolved_action_side": "long",
                    "4_resolved_underlying_action_type": "open_long",
                    "selected_option_contract_ref": "AAPL_2021-04-30_C_130",
                }
            )
        for index in range(194):
            rows.append(
                {
                    "decision_id": f"inverted_win{index}",
                    "timestamp": "2021-05-03T16:00:00-04:00",
                    "realized_return": 0.01,
                    "baseline_return": 0.0,
                    "cost": 0.0,
                    "outcome_label": 1,
                    "prediction_score": 0.70,
                    "action": "trade",
                    "decision_status": "approved",
                    "fill_status": "simulated_filled",
                    "resolved_action_side": "long",
                    "4_resolved_underlying_action_type": "open_long",
                    "selected_option_contract_ref": "AAPL_2021-05-21_C_130",
                }
            )

        settlement = _build_settlement_run(
            fold_id="fold_inverted_tail",
            target_symbol="AAPL",
            candidate_model_ref="storage://candidate/inverted-tail-risk",
            replay_contract_ref="trading-evaluation/replays/promotion_replay_candidate_policy.json",
            replay_result_ref="storage://replay/inverted-tail-risk",
            decision_rows=rows,
            created_at_utc="2026-06-13T20:00:00+00:00",
        )

        diagnostics = settlement["metrics"]["high_score_tail_risk_diagnostics"]
        self.assertIn("high_score_tail_loss_overconfidence", settlement["gate_failures"])
        self.assertNotIn("high_score_tail_loss_sample_limited", settlement["gate_failures"])
        self.assertLess(diagnostics["filled_good_bad_score_gap"], 0)
        self.assertEqual(diagnostics["filled_count"], 200)
        self.assertEqual(diagnostics["sample_sufficiency_status"], "sufficient_for_this_diagnostic")
        self.assertEqual(diagnostics["option_selection_mechanics_status"], "not_supported_by_current_evidence")


if __name__ == "__main__":
    unittest.main()

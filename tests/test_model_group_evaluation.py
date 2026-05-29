from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.model_group_evaluation import _decision_variable_schema_diagnostics, run_model_group_evaluation_if_ready


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
        for layer in range(1, 10):
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
                    "8_resolved_action_side": "long" if positive else "flat",
                    "8_resolved_underlying_action_type": "open_long" if positive else "no_trade",
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
                    "target_refs": ["AAPL"],
                    "decision_rows_ref": str(decision_rows_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        attribution_rows_path = attribution_root / "failure_attribution_rows.jsonl"
        attribution_rows_path.write_text(
            json.dumps({"contract_type": "model_10_event_risk_governor_post_replay_attribution_row", "attribution_id": "attr_1"}) + "\n",
            encoding="utf-8",
        )
        (attribution_root / "post_replay_attribution_receipt.json").write_text(
            json.dumps(
                {
                    "contract_type": "post_replay_event_attribution_receipt",
                    "status": "succeeded",
                    "created_at_utc": "2026-05-28T00:00:01+00:00",
                    "decision_rows_ref": str(decision_rows_path),
                    "attribution_rows_ref": str(attribution_rows_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return dataset_root

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
            self.assertEqual(receipt["ready_check_count"], 4)
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
            self.assertIn("eval_action_class", variable_diagnostics["normalized_row_samples"][0])
            self.assertIn("temporal_stability_diagnostics", metrics)
            self.assertIn("baseline_comparison_diagnostics", metrics)
            self.assertIsInstance(metrics["silhouette_outcome_label"], float)
            self.assertIn("feature_diagnostics", metrics)

            second = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")
            self.assertIsNone(second)

            state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            newer_mtime = max(path.stat().st_mtime for path in decision_paths) + 1
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
            self.assertEqual(len(list((dataset_root / "promotion_review_runs").glob("*/promotion_eligibility_decision.json"))), 2)

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


if __name__ == "__main__":
    unittest.main()

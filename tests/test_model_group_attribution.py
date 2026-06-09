from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_attribution import run_model_group_post_replay_attribution_if_ready
from trading_manager_tasks.model_group_layer_ten_attribution import run_model_group_layer_ten_attribution_if_ready


class ModelGroupAttributionTests(unittest.TestCase):
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
                        }
                    ),
                    json.dumps({"decision_id": "filled_under_baseline", "decision_status": "approved", "outcome_label": 1, "realized_return": 0.01, "baseline_return": 0.02, "month": "2021-01"}),
                    json.dumps({"decision_id": "rejected_winner", "decision_status": "rejected", "outcome_label": 1, "month": "2021-02"}),
                    json.dumps({"decision_id": "good_fill", "fill_status": "simulated_filled", "outcome_label": 1, "realized_return": 0.04, "baseline_return": 0.02, "month": "2021-02"}),
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
                    "decision_rows_ref": str(decision_rows_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return dataset_root

    def test_writes_post_replay_failure_triage_receipt_and_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)

            decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_post_replay_failure_triage_executed")
            receipt_paths = list((dataset_root / "post_replay_failure_triage_runs").glob("*/post_replay_failure_triage_receipt.json"))
            self.assertEqual(len(receipt_paths), 1)
            receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["contract_type"], "post_replay_failure_triage_receipt")
            self.assertEqual(receipt["triaged_failure_count"], 3)
            self.assertEqual(receipt["layer_10_event_attribution_status"], "not_performed")
            self.assertIs(receipt["event_evidence_consumed"], False)
            self.assertEqual(receipt["decision_rows_ref"], str(dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"))
            rows = [
                json.loads(line)
                for line in Path(receipt["triage_rows_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([row["source_decision_id"] for row in rows], ["filled_loss", "filled_under_baseline", "rejected_winner"])
            self.assertEqual(rows[0]["contract_type"], "post_replay_failure_triage_row")
            self.assertEqual(rows[0]["replay_month"], "2021-01")
            self.assertEqual(rows[0]["target_symbol"], "BTC")

    def test_ready_without_execute_does_not_write_receipt(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)

            decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root, execute=False)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "ready")
            self.assertEqual(decision.reason_code, "model_group_post_replay_failure_triage_ready")
            self.assertFalse((dataset_root / "post_replay_failure_triage_runs").exists())

    def test_skips_when_attribution_receipt_already_exists(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            receipt_root = dataset_root / "post_replay_failure_triage_runs" / "existing"
            receipt_root.mkdir(parents=True)
            decision_rows_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            (receipt_root / "post_replay_failure_triage_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "post_replay_failure_triage_receipt",
                        "decision_rows_ref": str(decision_rows_path),
                        "status": "succeeded",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root)

            self.assertIsNone(decision)

    def test_writes_real_layer_10_attribution_receipt_from_event_observation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            triage_decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root)
            self.assertIsNotNone(triage_decision)
            observation_root = storage_root / "runtime" / "layer_04_event_observation_inputs"
            observation_root.mkdir(parents=True)
            (observation_root / "2021-01_2021-02.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_layer_04_event_observation_materialization",
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
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_layer_ten_attribution_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_layer_10_event_attribution_executed")
            receipt_paths = list((dataset_root / "post_replay_attribution_runs").glob("*/post_replay_attribution_receipt.json"))
            self.assertEqual(len(receipt_paths), 1)
            receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["contract_type"], "post_replay_layer_10_event_attribution_receipt")
            self.assertTrue(receipt["event_evidence_consumed"])
            self.assertEqual(receipt["event_candidate_count"], 1)
            self.assertEqual(receipt["event_observation_count"], 1)
            self.assertEqual(receipt["control_analysis_status"], "passed")
            rows = [
                json.loads(line)
                for line in Path(receipt["attribution_rows_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(rows[0]["contract_type"], "model_10_event_risk_governor_event_attribution_row")
            self.assertEqual(rows[0]["attribution_status"], "attributed")
            self.assertEqual(receipt["event_focus_proposal_count"], 1)
            self.assertFalse(receipt["accepted_event_pool_mutation_performed"])
            self.assertFalse(receipt["temporal_attention_pool_mutation_performed"])
            proposals = [
                json.loads(line)
                for line in Path(receipt["event_focus_proposals_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(proposals), 1)
            self.assertEqual(proposals[0]["contract_type"], "model_10_event_risk_governor_event_focus_proposal")
            self.assertEqual(proposals[0]["stage_id"], "model_group.layer_10_event_attribution")
            self.assertEqual(proposals[0]["proposal_status"], "watch_candidate")
            self.assertEqual(proposals[0]["event_summary"]["normalized_event_type"], "microstructure_liquidity_disruption")
            self.assertIn("Fixture PIT event", proposals[0]["event_summary"]["rationale_summary"])
            self.assertIn("BTC filled_negative_or_underperforming_outcome failures", proposals[0]["failure_attention_reason"])
            self.assertIn("requires_event_strategy_promotion_review", proposals[0]["acceptance_blockers"])
            self.assertFalse(receipt["layer_4_promotion_performed"])

    def test_layer_10_backoff_when_event_evidence_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            triage_decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root)
            self.assertIsNotNone(triage_decision)

            decision = run_model_group_layer_ten_attribution_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_layer_10_event_evidence_missing")
            self.assertFalse((dataset_root / "post_replay_attribution_runs").exists())


if __name__ == "__main__":
    unittest.main()

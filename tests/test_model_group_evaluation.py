from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_evaluation import run_model_group_evaluation_if_ready


class ModelGroupEvaluationTests(unittest.TestCase):
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
                }
            )
        decision_rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        replay_receipt_path = replay_run_root / "replay_execution_receipt.json"
        replay_receipt_path.write_text(
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

            decision = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")

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
            eligibility = json.loads(decision_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(eligibility["contract_type"], "promotion_eligibility_decision")
            self.assertEqual(eligibility["decision_status"], "review_required")

            second = run_model_group_evaluation_if_ready(storage_root=storage_root, selected_target_symbol="AAPL")
            self.assertIsNone(second)


if __name__ == "__main__":
    unittest.main()

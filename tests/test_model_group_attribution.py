from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_attribution import run_model_group_post_replay_attribution_if_ready


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

    def test_writes_post_replay_attribution_receipt_and_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)

            decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root)

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_post_replay_attribution_executed")
            receipt_paths = list((dataset_root / "post_replay_attribution_runs").glob("*/post_replay_attribution_receipt.json"))
            self.assertEqual(len(receipt_paths), 1)
            receipt = json.loads(receipt_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(receipt["attributed_failure_count"], 3)
            self.assertEqual(receipt["decision_rows_ref"], str(dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"))
            rows = [
                json.loads(line)
                for line in Path(receipt["attribution_rows_ref"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([row["source_decision_id"] for row in rows], ["filled_loss", "filled_under_baseline", "rejected_winner"])
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
            self.assertEqual(decision.reason_code, "model_group_post_replay_attribution_ready")
            self.assertFalse((dataset_root / "post_replay_attribution_runs").exists())

    def test_skips_when_attribution_receipt_already_exists(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_replay_dataset(storage_root)
            receipt_root = dataset_root / "post_replay_attribution_runs" / "existing"
            receipt_root.mkdir(parents=True)
            decision_rows_path = dataset_root / "replay_execution_runs" / "model_group_replay_fixture" / "decision_rows.jsonl"
            (receipt_root / "post_replay_attribution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "post_replay_event_attribution_receipt",
                        "decision_rows_ref": str(decision_rows_path),
                        "status": "succeeded",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_post_replay_attribution_if_ready(storage_root=storage_root)

            self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()

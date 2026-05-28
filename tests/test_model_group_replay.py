from __future__ import annotations

import csv
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_replay import run_model_group_replay_if_ready


class ModelGroupReplayTests(unittest.TestCase):
    def _write_dataset(self, storage_root: Path) -> Path:
        dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
        dataset_root.mkdir(parents=True)
        plan_path = dataset_root / "feed_acquisition_plan.csv"
        with plan_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status"])
            writer.writeheader()
            writer.writerow({"month": "2021-01", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
            writer.writerow({"month": "2021-02", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
        (dataset_root / "dataset_manifest.json").write_text(
            json.dumps(
                {
                    "contract_type": "replay_dataset_preparation_manifest",
                    "freeze_status": "frozen",
                    "missing_feed_acquisition_count": 0,
                    "feed_acquisition_plan_ref": str(plan_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (dataset_root / "replay_freeze_receipt.json").write_text(
            json.dumps({"freeze_status": "frozen", "validation": {"validation_status": "passed"}}) + "\n",
            encoding="utf-8",
        )
        return dataset_root

    def _write_completed_fold(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                    "stages": [
                        {
                            "stage_id": f"layer_{layer:02d}_fixture.model_generation",
                            "stage_type": "model_generation",
                            "layer": layer,
                            "status": "succeeded",
                        }
                        for layer in range(1, 10)
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_runner(self, root: Path) -> Path:
        runner = root / "run_replay_execution.py"
        runner.write_text(
            textwrap.dedent(
                """
                import json
                import sys
                from pathlib import Path

                progress_path = Path(sys.argv[sys.argv.index("--progress-path") + 1])
                progress_path.parent.mkdir(parents=True, exist_ok=True)
                rows = [
                    {"contract_type": "evaluation_replay_progress", "stage_id": "model_group.replay", "month": "2021-01", "status": "completed"},
                    {"contract_type": "evaluation_replay_progress", "stage_id": "model_group.replay", "month": "2021-02", "status": "completed"},
                ]
                progress_path.write_text("\\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\\n", encoding="utf-8")
                print(json.dumps({"contract_type": "evaluation_replay_execution_run", "replay_execution_run_id": "test_run", "decision_row_count": 2}))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return runner

    def test_runs_replay_when_fold_and_frozen_dataset_are_ready(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            runner = self._write_runner(tmp)

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=runner,
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_executed")
            self.assertEqual(decision.provider_calls, 0)
            self.assertFalse(decision.broker_execution_performed)
            progress_rows = [json.loads(line) for line in (dataset_root / "replay_progress.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["month"] for row in progress_rows], ["2021-01", "2021-02"])

    def test_skips_replay_when_all_months_are_already_complete(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
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

            decision = run_model_group_replay_if_ready(storage_root=storage_root, runner_path=tmp / "missing.py")

            self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()

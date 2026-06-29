from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from trading_manager_tasks.task_progress import load_active_task_progress, write_task_progress_from_env, write_task_progress_node


class TaskProgressTests(unittest.TestCase):
    def test_concurrent_writes_to_same_worker_use_independent_temp_files(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            progress_root = Path(raw_tmp) / "progress"

            def write(index: int) -> None:
                write_task_progress_node(
                    progress_root=progress_root,
                    worker_id="month_ingest_worker_stage_executor",
                    task_uid=f"2016-{index + 1:02d}:model_01_market_context.feature_generation",
                    stage_id="model_01_market_context.feature_generation",
                    status="running",
                    processed_count=index,
                    expected_count=12,
                )

            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(write, range(12)))

            payloads = load_active_task_progress(progress_root)
            self.assertEqual(len(payloads), 1)
            self.assertFalse(list(progress_root.glob("*.tmp")))

    def test_stage_started_node_reports_stage_level_running_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            progress_root = Path(raw_tmp) / "progress"
            write_task_progress_node(
                progress_root=progress_root,
                worker_id="model_worker_1",
                task_uid="2016-01..2016-06:model_05_option_expression.model_generation",
                stage_id="model_05_option_expression.model_generation",
                status="running",
                unit_label="model job",
                node_id="stage_started",
                node_label="Stage process started",
            )

            payloads = load_active_task_progress(progress_root)

        progress = payloads["2016-01..2016-06:model_05_option_expression.model_generation"]
        self.assertEqual(progress["expected_count"], 1)
        self.assertEqual(progress["ready_count"], 0)
        self.assertEqual(progress["pending_count"], 1)
        self.assertEqual(progress["unit_label"], "model job")
        self.assertEqual(progress["progress_source"], "active_progress_file")

    def test_write_task_progress_from_env_uses_stage_progress_contract(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            progress_root = Path(raw_tmp) / "progress"
            env = {
                "TRADING_MANAGER_TASK_PROGRESS_ROOT": str(progress_root),
                "TRADING_MANAGER_TASK_PROGRESS_WORKER_ID": "model_worker_1",
                "TRADING_MANAGER_TASK_PROGRESS_TASK_UID": "2016-01..2016-06:model_05_option_expression.model_generation.validation",
                "TRADING_MANAGER_TASK_PROGRESS_STAGE_ID": "model_05_option_expression.model_generation.validation",
            }

            write_task_progress_from_env(processed_count=1, expected_count=1, env=env)
            payloads = load_active_task_progress(progress_root)

        progress = payloads["2016-01..2016-06:model_05_option_expression.model_generation.validation"]
        self.assertEqual(progress["unit_label"], "dataset months")
        self.assertEqual(progress["expected_count"], 1)
        self.assertEqual(progress["ready_count"], 1)
        self.assertEqual(progress["progress_source"], "active_progress_file")
        self.assertIn("train/validation/test", progress["progress_basis"])

    def test_active_progress_preserves_specific_activity_and_real_logs(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            progress_root = Path(raw_tmp) / "progress"
            log_path = Path(raw_tmp) / "stage.stdout.log"

            write_task_progress_node(
                progress_root=progress_root,
                worker_id="model_worker_1",
                task_uid="2016-01..2017-06:model_02_target_state.feature_generation",
                stage_id="model_02_target_state.feature_generation",
                unit_label="feature months",
                processed_count=8,
                expected_count=18,
                node_id="feature_window",
                node_label="Generating AAPL target-state features",
                current_activity="Generating AAPL 2016-03-01 target-state features",
                activity_details=["Window 2016-02-26 to 2016-03-04", "Rows written 143,491"],
                log_refs=[str(log_path)],
            )
            payloads = load_active_task_progress(progress_root)

        progress = payloads["2016-01..2017-06:model_02_target_state.feature_generation"]
        self.assertEqual(progress["current_activity"], "Generating AAPL 2016-03-01 target-state features")
        self.assertEqual(progress["activity_details"], ["Window 2016-02-26 to 2016-03-04", "Rows written 143,491"])
        self.assertEqual(progress["log_refs"], [str(log_path)])
        self.assertFalse((progress_root / "logs").exists())


if __name__ == "__main__":
    unittest.main()

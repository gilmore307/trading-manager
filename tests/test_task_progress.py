from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from trading_manager_tasks.task_progress import load_active_task_progress, write_task_progress_node


class TaskProgressTests(unittest.TestCase):
    def test_concurrent_writes_to_same_worker_use_independent_temp_files(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            progress_root = Path(raw_tmp) / "progress"

            def write(index: int) -> None:
                write_task_progress_node(
                    progress_root=progress_root,
                    worker_id="month_ingest_worker_stage_executor",
                    task_uid=f"2016-{index + 1:02d}:layer_01_market_regime.feature_generation",
                    stage_id="layer_01_market_regime.feature_generation",
                    status="running",
                    processed_count=index,
                    expected_count=12,
                )

            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(write, range(12)))

            payloads = load_active_task_progress(progress_root)
            self.assertEqual(len(payloads), 1)
            self.assertFalse(list(progress_root.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()

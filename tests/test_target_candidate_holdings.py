from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.target_candidate_holdings import (
    build_target_candidate_holdings_task_key,
    materialize_target_candidate_holdings,
)


class TargetCandidateHoldingsTests(unittest.TestCase):
    def test_builds_layer_two_target_candidate_holdings_task_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)

            task_key, task_key_path = build_target_candidate_holdings_task_key(
                start_month="2026-05",
                end_month="2026-05",
                output_dir=tmp / "out",
                trading_data_output_root=tmp / "td-holdings-out",
            )

            self.assertEqual(task_key["source"], "m02_sector_context_data_acquisition")
            self.assertEqual(task_key["task_id"], "layer_02_target_candidate_holdings_2026_05_2026_05")
            self.assertEqual(task_key["params"]["start"], "2026-05-01T00:00:00-05:00")
            self.assertEqual(task_key["params"]["end"], "2026-06-01T00:00:00-05:00")
            self.assertTrue(task_key["params"]["continue_on_error"])
            self.assertEqual(task_key["manager_stage_id"], "layer_02_sector_context.feature_generation")
            self.assertEqual(task_key["source_policy"], "official_issuer_holdings_fetch_with_point_in_time_window_filter")
            self.assertTrue(task_key_path.exists())

    def test_dry_run_materialization_writes_task_key_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)

            summary = materialize_target_candidate_holdings(
                start_month="2026-05",
                end_month="2026-05",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=tmp / "trading-data",
                write=False,
            )

            self.assertEqual(summary.contract_type, "manager_layer_two_target_candidate_holdings_materialization")
            self.assertEqual(summary.provider_calls, 0)
            self.assertEqual(summary.target_candidate_holdings_fetch_count, 0)
            self.assertEqual(summary.target_candidate_holdings_row_count, 0)
            self.assertTrue(Path(summary.task_key_path).exists())


if __name__ == "__main__":
    unittest.main()

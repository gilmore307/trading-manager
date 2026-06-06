from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.layer_nine_feature_stage import execute_layer_nine_feature_stage


class LayerNineFeatureStageTests(unittest.TestCase):
    def test_missing_shared_option_source_writes_failed_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch("trading_manager_tasks.layer_nine_feature_stage.option_source_row_count", return_value=0):
            tmp = Path(raw_tmp)
            summary = execute_layer_nine_feature_stage(
                start_month="2016-02",
                end_month="2016-02",
                output_root=tmp,
                trading_data_root=tmp / "trading-data",
            )

            self.assertEqual(summary.status, "failed")
            self.assertEqual(summary.mode, "option_source_coverage_missing")
            self.assertEqual(summary.provider_calls, 0)
            import json
            receipt = json.loads(Path(summary.receipt_path or "").read_text(encoding="utf-8"))
            self.assertEqual(receipt["manager_stage_id"], "layer_09_option_expression.feature_generation")
            self.assertEqual(receipt["runs"][0]["row_counts"]["option_chain_state_source_rows_available"], 0)

    def test_shared_option_source_delegates_to_trading_data_feature_generator(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch("trading_manager_tasks.layer_nine_feature_stage.option_source_row_count", return_value=2), patch("trading_manager_tasks.layer_nine_feature_stage.subprocess.run") as run:
            tmp = Path(raw_tmp)
            run.return_value.returncode = 0
            run.return_value.stdout = "generated 2 rows\n"
            run.return_value.stderr = ""

            summary = execute_layer_nine_feature_stage(
                start_month="2016-02",
                end_month="2016-02",
                output_root=tmp,
                trading_data_root=tmp / "trading-data",
            )

            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.mode, "trading_data_m09_sql_generation_from_shared_option_source")
            self.assertIn("--source-table", summary.command)
            self.assertIn("option_chain_state_source", summary.command)
            self.assertIn("--source-start", summary.command)
            self.assertIn("2016-02-01T00:00:00-05:00", summary.command)
            self.assertTrue(run.called)


if __name__ == "__main__":
    unittest.main()

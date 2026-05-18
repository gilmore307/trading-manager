from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.layer_nine_feature_stage import execute_layer_nine_feature_stage


class LayerNineFeatureStageTests(unittest.TestCase):
    def test_no_provider_gate_review_writes_feature_skip_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            review_root = tmp / "gate_review"
            review_root.mkdir(parents=True)
            review_path = review_root / "layer_09_option_expression_gate_review_2016-02.json"
            review_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_layer_09_option_expression_gate_review",
                        "stage_id": "layer_09_option_expression.data_acquisition",
                        "start_month": "2016-02",
                        "end_month": "2016-02",
                        "status": "no_provider_skip_accepted",
                        "active_request_count": 0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            summary = execute_layer_nine_feature_stage(
                start_month="2016-02",
                end_month="2016-02",
                gate_review_root=review_root,
                output_root=review_root,
                trading_data_root=tmp / "trading-data",
            )

            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.mode, "no_provider_no_option_skip")
            self.assertEqual(summary.provider_calls, 0)
            receipt = json.loads(Path(summary.receipt_path or "").read_text(encoding="utf-8"))
            self.assertEqual(receipt["manager_stage_id"], "layer_09_option_expression.feature_generation")
            self.assertEqual(receipt["runs"][0]["row_counts"]["feature_08_option_expression_rows_required"], 0)

    def test_active_gate_review_delegates_to_trading_data_feature_generator(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch("trading_manager_tasks.layer_nine_feature_stage.subprocess.run") as run:
            tmp = Path(raw_tmp)
            review_root = tmp / "gate_review"
            review_root.mkdir(parents=True)
            (review_root / "layer_09_option_expression_gate_review_2016-02.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_layer_09_option_expression_gate_review",
                        "status": "approval_required",
                        "active_request_count": 2,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            run.return_value.returncode = 0
            run.return_value.stdout = "generated 2 rows\n"
            run.return_value.stderr = ""

            summary = execute_layer_nine_feature_stage(
                start_month="2016-02",
                end_month="2016-02",
                gate_review_root=review_root,
                output_root=review_root,
                trading_data_root=tmp / "trading-data",
            )

            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.mode, "trading_data_feature_08_sql_generation")
            self.assertIn("--source-start", summary.command)
            self.assertIn("2016-02-01T00:00:00-05:00", summary.command)
            self.assertTrue(run.called)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.layer_nine_option_expression import (
    STAGE_ID,
    build_layer_nine_gate_review,
    request_previews_from_layer_8_rows,
    write_gate_review_artifacts,
)


class LayerNineOptionExpressionGateTests(unittest.TestCase):
    def test_no_trade_layer_seven_rows_accept_no_provider_skip(self) -> None:
        review = build_layer_nine_gate_review(
            start_month="2016-01",
            end_month="2016-01",
            layer_8_rows=[
                {
                    "target_candidate_id": "tcand_001",
                    "underlying": "AAPL",
                    "available_time": "2016-01-05T09:30:00-05:00",
                    "action_type": "no_trade",
                    "action_side": "none",
                },
                {
                    "target_candidate_id": "tcand_002",
                    "underlying": "MSFT",
                    "available_time": "2016-01-05T10:30:00-05:00",
                    "action_type": "maintain",
                    "action_side": "neutral",
                },
            ],
        )

        self.assertEqual(review.stage_id, STAGE_ID)
        self.assertEqual(review.status, "no_provider_skip_accepted")
        self.assertEqual(review.reviewed_decision, "accepted_skip_no_active_target_chain")
        self.assertEqual(review.total_layer_8_rows, 2)
        self.assertEqual(review.active_request_count, 0)
        self.assertEqual(review.provider_calls, 0)
        self.assertFalse(review.dispatch_performed)
        self.assertIn("no option-chain provider call", review.reason)

    def test_active_layer_seven_rows_preview_thetadata_requests(self) -> None:
        rows = [
            {
                "target_candidate_id": "tcand_active_abc123",
                "underlying": "AAPL",
                "available_time": "2016-01-05T09:30:00-05:00",
                "tradeable_time": "2016-01-05T09:31:00-05:00",
                "underlying_action_plan_ref": "uap_001",
                "action_type": "increase_long",
                "action_side": "long",
                "dominant_horizon": "390min",
                "action_confidence_score": 0.72,
            }
        ]
        previews = request_previews_from_layer_8_rows(rows, start_month="2016-01")
        review = build_layer_nine_gate_review(start_month="2016-01", end_month="2016-01", layer_8_rows=rows)

        self.assertEqual(len(previews), 1)
        self.assertTrue(previews[0].request_id.startswith("mgrreq_layer9_option_snapshot_aapl_2016_01_"))
        self.assertEqual(previews[0].provider, "thetadata")
        self.assertEqual(previews[0].target_component_id, "source_05_option_expression")
        self.assertEqual(previews[0].snapshot_time, "2016-01-05T09:31:00-05:00")
        self.assertEqual(review.status, "provider_acquisition_ready")
        self.assertEqual(review.active_request_count, 1)
        self.assertEqual(review.recommended_next_action, "prepare_option_expression_acquisition")

    def test_written_no_provider_skip_receipt_is_safe_and_stage_scoped(self) -> None:
        review = build_layer_nine_gate_review(start_month="2016-01", end_month="2016-01", layer_8_rows=[])
        with tempfile.TemporaryDirectory() as raw_tmp:
            review_path, receipt_path = write_gate_review_artifacts(review, output_root=Path(raw_tmp))
            receipt_text = receipt_path.read_text(encoding="utf-8")

            self.assertTrue(review_path.exists())
            self.assertIn('"manager_stage_id": "layer_09_option_expression.data_acquisition"', receipt_text)
            self.assertIn('"status": "succeeded"', receipt_text)
            self.assertIn('"provider_calls": 0', receipt_text)
            self.assertIn('"broker_execution_performed": false', receipt_text)
            self.assertIn('"model_activation_performed": false', receipt_text)


if __name__ == "__main__":
    unittest.main()

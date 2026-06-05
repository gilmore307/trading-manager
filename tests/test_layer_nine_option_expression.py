from __future__ import annotations

import tempfile
import unittest
import inspect
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.layer_nine_option_expression import (
    STAGE_ID,
    _runtime_task_key,
    build_layer_nine_gate_review,
    fetch_layer_8_rows,
    main,
    manager_requests_from_gate_review,
    request_previews_from_layer_8_rows,
    write_gate_review_artifacts,
)


class LayerNineOptionExpressionGateTests(unittest.TestCase):
    def test_no_trade_layer_eight_rows_still_prepare_training_snapshots(self) -> None:
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
        self.assertEqual(review.status, "provider_acquisition_ready")
        self.assertEqual(review.reviewed_decision, "dense_training_minutes_ready_for_autonomous_option_acquisition")
        self.assertEqual(review.total_layer_8_rows, 2)
        self.assertEqual(review.training_request_count, 2)
        self.assertEqual({preview.underlying for preview in review.request_previews}, {"AAPL", "MSFT"})
        self.assertEqual(review.provider_calls, 0)
        self.assertFalse(review.dispatch_performed)
        self.assertIn("dense Layer 8 minute rows", review.reason)

    def test_training_eligible_layer_eight_rows_preview_thetadata_requests(self) -> None:
        rows = [
            {
                "target_candidate_id": "tcand_active_abc123",
                "underlying": "AAPL",
                "available_time": "2016-01-05T09:30:00-05:00",
                "tradeable_time": "2016-01-05T09:31:00-05:00",
                "underlying_action_plan_ref": "uap_001",
                "action_type": "increase_long",
                "action_side": "long",
                "dominant_horizon": "1W",
                "action_confidence_score": 0.72,
            }
        ]
        previews = request_previews_from_layer_8_rows(rows, start_month="2016-01")
        review = build_layer_nine_gate_review(start_month="2016-01", end_month="2016-01", layer_8_rows=rows)

        self.assertEqual(len(previews), 1)
        self.assertTrue(previews[0].request_id.startswith("mgrreq_layer9_option_snapshot_aapl_2016_01_"))
        self.assertEqual(previews[0].provider, "thetadata")
        self.assertEqual(previews[0].target_component_id, "m09_option_expression_data_acquisition")
        self.assertEqual(previews[0].snapshot_time, "2016-01-05T09:31:00-05:00")
        self.assertEqual(previews[0].max_dte, 45)
        self.assertEqual(previews[0].strike_range, 5)
        self.assertEqual(previews[0].option_bucket_policy_ref, "LAYER_09_OPTION_BUCKET_STRIKE_POLICY")
        source_task = previews[0].summary_row()["source_task_key"]
        self.assertEqual(source_task["source"], "m09_option_expression_data_acquisition")
        self.assertEqual(source_task["params"]["strike_range"], 5)
        self.assertEqual(source_task["params"]["max_dte"], 45)
        self.assertEqual(source_task["params"]["timeout_seconds"], 120)
        self.assertEqual(review.status, "provider_acquisition_ready")
        self.assertEqual(review.training_request_count, 1)
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

    def test_written_provider_ready_receipt_is_successful_gate_completion(self) -> None:
        review = build_layer_nine_gate_review(
            start_month="2016-01",
            end_month="2016-01",
            layer_8_rows=[
                {
                    "target_candidate_id": "tcand_active_abc123",
                    "underlying": "AAPL",
                    "available_time": "2016-01-05T09:30:00-05:00",
                    "action_type": "open_long",
                    "action_side": "long",
                }
            ],
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            _review_path, receipt_path = write_gate_review_artifacts(review, output_root=Path(raw_tmp))
            receipt_text = receipt_path.read_text(encoding="utf-8")

            self.assertIn('"status": "succeeded"', receipt_text)
            self.assertIn('"layer_9_training_request_candidates": 1', receipt_text)
            self.assertIn('"provider_calls": 0', receipt_text)
            self.assertIn('"broker_execution_performed": false', receipt_text)

    def test_layer_nine_manager_requests_authorize_thetadata_option_snapshot(self) -> None:
        review = build_layer_nine_gate_review(
            start_month="2016-01",
            end_month="2016-01",
            layer_8_rows=[
                {
                    "target_candidate_id": "tcand_active_abc123",
                    "underlying": "AAPL",
                    "available_time": "2016-01-05T09:30:00-05:00",
                    "action_type": "open_long",
                    "action_side": "long",
                }
            ],
        )

        request = manager_requests_from_gate_review(review)[0]
        controls = request["_task_key"]["manager_controls"]

        self.assertEqual(controls["allowed_providers"], ["thetadata"])
        self.assertEqual(controls["allowed_endpoint_families"], ["option_selection_snapshot"])
        self.assertEqual(controls["max_requests"], 4)
        self.assertEqual(controls["max_symbols"], 1)
        self.assertEqual(controls["max_time_window"], "1d")
        self.assertEqual(controls["timeout_seconds"], 120)

    def test_runtime_task_key_repairs_existing_layer_nine_policy_envelope(self) -> None:
        runtime_key = _runtime_task_key(
            {
                "source": "m09_option_expression_data_acquisition",
                "manager_controls": {
                    "allow_live_provider_calls": True,
                    "autonomous_historical_provider_acquisition": True,
                    "stage_id": STAGE_ID,
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                },
                "params": {"underlying": "AAPL", "snapshot_time": "2016-02-23 11:19:00-05:00"},
            }
        )

        controls = runtime_key["manager_controls"]
        self.assertEqual(controls["allowed_providers"], ["thetadata"])
        self.assertEqual(controls["allowed_endpoint_families"], ["option_selection_snapshot"])
        self.assertEqual(runtime_key["params"]["timeout_seconds"], 120)
        self.assertFalse(runtime_key["params"]["manager_dry_run"])

    def test_provider_ready_main_returns_success_for_training_eligible_no_trade_row(self) -> None:
        rows = [
            {
                "target_candidate_id": "tcand_active_abc123",
                "underlying": "AAPL",
                "available_time": "2016-01-05T09:30:00-05:00",
                "action_type": "no_trade",
                "action_side": "none",
            }
        ]
        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("trading_manager_tasks.layer_nine_option_expression.fetch_layer_8_rows", return_value=rows):
                with redirect_stdout(StringIO()):
                    exit_code = main(
                        [
                            "--start-month",
                            "2016-01",
                            "--end-month",
                            "2016-01",
                            "--database-url",
                            "postgresql://redacted",
                            "--output-root",
                            raw_tmp,
                            "--write",
                        ]
                    )

        self.assertEqual(exit_code, 0)

    def test_layer_8_fetch_limits_symbol_lookup_to_fold_targets(self) -> None:
        source = inspect.getsource(fetch_layer_8_rows)

        self.assertIn("WITH l8_rows AS MATERIALIZED", source)
        self.assertIn("JOIN (SELECT DISTINCT target_candidate_id FROM l8_rows)", source)
        self.assertIn("statement_timeout", source)


if __name__ == "__main__":
    unittest.main()

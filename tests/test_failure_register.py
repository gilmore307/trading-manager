from __future__ import annotations

import unittest
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.failure_register import mark_failure_register_requests_corrected, validate_failure_register_row


class FailureRegisterTests(unittest.TestCase):
    def test_accepted_skip_requires_agent_review_ref(self):
        with self.assertRaisesRegex(TaskSystemError, "agent_review_ref"):
            validate_failure_register_row(
                {
                    "request_id": "mgrreq_backfill_alpaca_bars_bitw_2016_01",
                    "stage_id": "layer_01_market_regime.data_acquisition",
                    "target_component_id": "01_feed_alpaca_bars",
                    "failure_status": "accepted_skip",
                    "failure_kind": "no_data_not_yet_listed",
                    "skip_future_matching": True,
                }
            )

    def test_corrected_requires_agent_review_ref(self):
        with self.assertRaisesRegex(TaskSystemError, "agent_review_ref"):
            validate_failure_register_row(
                {
                    "request_id": "mgrreq_backfill_alpaca_bars_bitw_2016_01",
                    "stage_id": "layer_01_market_regime.data_acquisition",
                    "target_component_id": "01_feed_alpaca_bars",
                    "failure_status": "corrected",
                    "failure_kind": "provider_schema_shape",
                    "correction_ref": "commit://fix",
                }
            )

    def test_valid_accepted_skip_preserves_skip_disposition(self):
        row = validate_failure_register_row(
            {
                "request_id": "mgrreq_backfill_alpaca_bars_bitw_2016_01",
                "stage_id": "layer_01_market_regime.data_acquisition",
                "target_component_id": "01_feed_alpaca_bars",
                "source_id": "alpaca_bars",
                "symbol": "bitw",
                "start_month": "2016-01",
                "end_month": "2016-01",
                "failure_status": "accepted_skip",
                "failure_kind": "no_data_not_yet_listed",
                "agent_review_ref": "storage://review.json",
                "skip_future_matching": True,
            }
        )

        self.assertEqual(row["contract_type"], "manager_failure_register")
        self.assertEqual(row["symbol"], "BITW")
        self.assertEqual(row["failure_status"], "accepted_skip")
        self.assertTrue(row["skip_future_matching"])

    def test_mark_failure_register_requests_corrected_updates_mutable_rows(self):
        existing = [
            {
                "failure_id": "fail_a",
                "request_id": "request_a",
                "run_id": "run_failed",
                "stage_id": "layer_09_option_expression.data_acquisition",
                "target_component_id": "m09_option_expression_data_acquisition",
                "source_id": "m09_option_expression_data_acquisition",
                "symbol": "AAPL",
                "start_month": "2016-01",
                "end_month": "2016-06",
                "failure_status": "agent_review_required",
                "failure_kind": "provider_service_unavailable",
                "observed_status": "failed",
                "error_summary": "connection refused",
                "evidence_refs": ["storage://old-receipt.json"],
            },
            {
                "failure_id": "fail_b",
                "request_id": "request_b",
                "run_id": "run_failed",
                "stage_id": "layer_09_option_expression.data_acquisition",
                "target_component_id": "m09_option_expression_data_acquisition",
                "failure_status": "accepted_skip",
                "failure_kind": "no_data",
                "agent_review_ref": "review://skip",
                "skip_future_matching": True,
            },
        ]
        with patch("trading_manager_tasks.failure_register.fetch_failure_register_rows", return_value=existing), patch(
            "trading_manager_tasks.failure_register.persist_failure_register_rows"
        ) as persist_mock:
            count = mark_failure_register_requests_corrected(
                stage_id="layer_09_option_expression.data_acquisition",
                start_month="2016-01",
                end_month="2016-06",
                corrected_request_refs={"request_a": "storage://new-success.json", "request_b": "storage://new-success.json"},
            )

        self.assertEqual(count, 1)
        persisted = persist_mock.call_args.args[0]
        self.assertEqual(persisted[0]["failure_status"], "corrected")
        self.assertEqual(persisted[0]["agent_review_ref"], "manager_provider_stage_reconcile:latest_receipt_succeeded")
        self.assertEqual(persisted[0]["correction_ref"], "storage://new-success.json")
        self.assertIn("storage://new-success.json", persisted[0]["evidence_refs"])


if __name__ == "__main__":
    unittest.main()

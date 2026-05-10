from __future__ import annotations

import unittest

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.failure_register import validate_failure_register_row


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

        self.assertEqual(row["contract_type"], "manager_failure_register_v1")
        self.assertEqual(row["symbol"], "BITW")
        self.assertEqual(row["failure_status"], "accepted_skip")
        self.assertTrue(row["skip_future_matching"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from trading_manager_tasks.historical_training import prepare_layer_one_historical_training_batch
from trading_manager_tasks.provider_dispatch import dispatch_layer_one_provider_acquisition


class ProviderDispatchTests(unittest.TestCase):
    def test_layer_one_dispatch_validates_approval_without_provider_calls_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_test",
                        "decision_status": "approved",
                        "approved_by": "unit-test",
                        "approved_at_utc": datetime.now(UTC).isoformat(),
                        "expires_at_utc": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
                        "request_ids": [request["request_id"] for request in requests],
                        "approval_scope": "provider_data_acquisition_only",
                        "broker_execution_allowed": False,
                        "allowed_providers": ["alpaca"],
                        "max_requests": summary.request_count,
                        "max_window_days": 31,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                approval_path=approval,
                execute_approved_provider_calls=False,
            )
        self.assertEqual(dispatch.contract_type, "manager_provider_dispatch_summary_v1")
        self.assertEqual(dispatch.stage_id, "layer_01_market_regime.data_acquisition")
        self.assertEqual(dispatch.request_count, 22)
        self.assertEqual(dispatch.validation_count, 22)
        self.assertEqual(dispatch.dispatch_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertFalse(dispatch.dispatch_performed)
        self.assertEqual(dispatch.items[0].status, "validated_not_dispatched")
        self.assertIn("data_feed.01_feed_alpaca_bars", dispatch.items[0].command)


if __name__ == "__main__":
    unittest.main()

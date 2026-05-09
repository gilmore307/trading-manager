from __future__ import annotations

import unittest
from datetime import UTC, datetime

from trading_manager_tasks.live_call_gate import validate_live_call_approval
from trading_manager_tasks.monthly_backfill import plan_monthly_backfill_requests


class LiveCallGateTests(unittest.TestCase):
    def _live_request(self):
        request = dict(plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")[0])
        request["dry_run"] = False
        request["policy_refs"] = ["monthly_backfill_v1", "live_call_policy_required", "live_call_approval_gate_v1"]
        return request

    def _approval(self, request_id: str):
        return {
            "contract_type": "live_call_approval_v1",
            "approval_id": "liveapp_test_001",
            "decision_status": "approve",
            "approved_by": "reviewer-agent",
            "approved_at_utc": "2026-05-09T10:00:00Z",
            "expires_at_utc": "2026-05-10T10:00:00Z",
            "request_ids": [request_id],
            "approval_scope": "provider_data_acquisition_only",
            "allowed_providers": ["alpaca"],
            "max_requests": 10,
            "max_window_days": 31,
            "broker_execution_allowed": False,
        }

    def test_approves_bounded_non_dry_run_provider_request(self):
        request = self._live_request()
        result = validate_live_call_approval(
            request,
            self._approval(request["request_id"]),
            now_utc=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(result.request_id, request["request_id"])
        self.assertEqual(result.target_repo_id, "trading-data")
        self.assertIn("alpaca", result.allowed_providers)
        self.assertEqual(result.max_requests, 10)
        self.assertEqual(result.max_window_days, 31)
        self.assertFalse(result.dispatch_performed)
        self.assertEqual(result.provider_calls, 0)

    def test_rejects_dry_run_request(self):
        request = self._live_request()
        request["dry_run"] = True

        with self.assertRaisesRegex(ValueError, "non-dry-run"):
            validate_live_call_approval(
                request,
                self._approval(request["request_id"]),
                now_utc=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            )

    def test_rejects_missing_gate_policy(self):
        request = self._live_request()
        request["policy_refs"] = ["monthly_backfill_v1", "live_call_policy_required"]

        with self.assertRaisesRegex(ValueError, "live_call_approval_gate_v1"):
            validate_live_call_approval(
                request,
                self._approval(request["request_id"]),
                now_utc=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            )

    def test_rejects_wrong_provider_scope(self):
        request = self._live_request()
        approval = self._approval(request["request_id"])
        approval["allowed_providers"] = ["okx"]

        with self.assertRaisesRegex(ValueError, "allowed_providers"):
            validate_live_call_approval(
                request,
                approval,
                now_utc=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            )

    def test_rejects_window_beyond_approval(self):
        request = self._live_request()
        approval = self._approval(request["request_id"])
        approval["max_window_days"] = 10

        with self.assertRaisesRegex(ValueError, "max_window_days"):
            validate_live_call_approval(
                request,
                approval,
                now_utc=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            )

    def test_rejects_broker_execution_approval(self):
        request = self._live_request()
        approval = self._approval(request["request_id"])
        approval["broker_execution_allowed"] = True

        with self.assertRaisesRegex(ValueError, "broker_execution_allowed"):
            validate_live_call_approval(
                request,
                approval,
                now_utc=datetime(2026, 5, 9, 12, 0, tzinfo=UTC),
            )


if __name__ == "__main__":
    unittest.main()

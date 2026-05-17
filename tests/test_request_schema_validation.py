from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from trading_manager_tasks.control_plane import validate_manager_request
from trading_manager_tasks.model_promotion import build_model_promotion_review_request
from trading_manager_tasks.monthly_backfill import plan_monthly_backfill_requests


REPO_ROOT = Path(__file__).resolve().parents[1]
MANAGER_REQUEST_SCHEMA = json.loads((REPO_ROOT / "schemas/manager_request.schema.json").read_text(encoding="utf-8"))
PLANNER_PREVIEW_SCHEMA = json.loads((REPO_ROOT / "schemas/manager_request_planner_preview.schema.json").read_text(encoding="utf-8"))


def _assert_valid(testcase: unittest.TestCase, payload: dict[str, object], schema: dict[str, object]) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda error: list(error.path))
    testcase.assertEqual(errors, [], "; ".join(error.message for error in errors))


class RequestSchemaValidationTests(unittest.TestCase):
    def test_monthly_backfill_preview_validates_and_normalizes_to_manager_request(self) -> None:
        request = next(
            row
            for row in plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")
            if row["target_component_id"] == "01_feed_alpaca_bars" and row.get("symbol") == "SPY"
        )

        _assert_valid(self, request, PLANNER_PREVIEW_SCHEMA)
        _assert_valid(self, validate_manager_request(request), MANAGER_REQUEST_SCHEMA)

    def test_model_promotion_preview_validates_and_normalizes_to_manager_request(self) -> None:
        request = build_model_promotion_review_request(
            model="model_04_event_failure_risk",
            candidate_ref="trading-model://promotion-candidates/mpcand_event_failure",
            evaluation_run_refs=["trading-model://eval-runs/mdevrun_event_failure"],
            evidence_refs=["storage://trading-model/evidence/event_failure.json"],
            priority="high",
        )

        _assert_valid(self, request, PLANNER_PREVIEW_SCHEMA)
        _assert_valid(self, validate_manager_request(request), MANAGER_REQUEST_SCHEMA)


if __name__ == "__main__":
    unittest.main()

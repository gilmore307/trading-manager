from __future__ import annotations

import io
import json
import unittest

from trading_manager_tasks.monthly_backfill import (
    DEFAULT_SOURCES,
    LAYER_ONE_MODEL_LAYER,
    iter_monthly_windows,
    load_market_regime_universe,
    plan_monthly_backfill_requests,
    write_requests,
)


class MonthlyBackfillPlannerTests(unittest.TestCase):
    def test_iter_monthly_windows_uses_inclusive_months_and_exclusive_end_dates(self):
        windows = list(iter_monthly_windows("2016-01", "2016-03"))

        self.assertEqual([window.month for window in windows], ["2016-01", "2016-02", "2016-03"])
        self.assertEqual(windows[0].start_date, "2016-01-01")
        self.assertEqual(windows[0].end_date_exclusive, "2016-02-01")
        self.assertEqual(windows[-1].end_date_exclusive, "2016-04-01")

    def test_common_start_includes_historical_sources_at_2016_01(self):
        requests = plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")
        by_component = {request["target_component_id"]: request for request in requests}
        layer_one_bars = [request for request in requests if request["target_component_id"] == "01_feed_alpaca_bars"]

        self.assertEqual(len(layer_one_bars), len(load_market_regime_universe()))
        self.assertIn("SPY", {request["symbol"] for request in layer_one_bars})
        self.assertTrue(all(request["model_layer"] == LAYER_ONE_MODEL_LAYER for request in layer_one_bars))

        for component_id in {
            "01_feed_alpaca_bars",
            "02_feed_alpaca_liquidity",
            "03_feed_alpaca_news",
            "05_feed_gdelt_news",
            "08_feed_sec_company_financials",
            "10_feed_thetadata_option_primary_tracking",
            "11_feed_thetadata_option_event_timeline",
        }:
            self.assertIn(component_id, by_component)
            self.assertEqual(by_component[component_id]["month"], "2016-01")
            self.assertEqual(by_component[component_id]["contract_type"], "manager_request_v1")
            self.assertEqual(by_component[component_id]["priority"], "normal")
            self.assertTrue(by_component[component_id]["dry_run"])

    def test_crypto_joins_later_than_common_start(self):
        requests_2016 = plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-12")
        self.assertNotIn("04_feed_okx_crypto_market_data", {row["target_component_id"] for row in requests_2016})

        requests_2018 = plan_monthly_backfill_requests(start_month="2016-01", end_month="2018-01")
        okx = [row for row in requests_2018 if row["target_component_id"] == "04_feed_okx_crypto_market_data"]
        self.assertEqual(len(okx), 1)
        self.assertEqual(okx[0]["month"], "2018-01")

    def test_current_only_sources_are_not_historical_backfill_requests(self):
        planned_components = {
            row["target_component_id"]
            for row in plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")
        }

        self.assertNotIn("06_feed_etf_holdings", planned_components)
        self.assertNotIn("07_feed_trading_economics_calendar_web", planned_components)
        self.assertNotIn("09_feed_thetadata_option_selection_snapshot", planned_components)
        self.assertTrue(
            any(
                source.target_component_id == "06_feed_etf_holdings"
                and not source.historical_backfill_supported
                for source in DEFAULT_SOURCES
            )
        )

    def test_write_jsonl_keeps_expected_manager_request_shape(self):
        request = next(
            row
            for row in plan_monthly_backfill_requests(start_month="2016-01", end_month="2016-01")
            if row["target_component_id"] == "01_feed_alpaca_bars" and row.get("symbol") == "SPY"
        )
        buffer = io.StringIO()

        write_requests([request], output=buffer, output_format="jsonl")

        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["contract_type"], "manager_request_v1")
        self.assertEqual(payload["status"], "requested")
        self.assertIn("monthly_backfill_v1", payload["policy_refs"])
        self.assertTrue(payload["parameter_ref"].endswith("/task_key.json"))


if __name__ == "__main__":
    unittest.main()

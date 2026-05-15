import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.event_feed_backfill import (
    REQUIRED_EVENT_FEED_IDS,
    plan_event_feed_requests,
    prepare_event_feed_backfill,
)


class EventFeedBackfillTests(unittest.TestCase):
    def test_plans_required_event_feeds_for_each_month(self):
        requests = plan_event_feed_requests(start_month="2016-01", end_month="2016-02", target_symbol="AAPL")
        self.assertEqual(len(requests), 2 * len(REQUIRED_EVENT_FEED_IDS))
        self.assertEqual({row["target_component_id"] for row in requests}, set(REQUIRED_EVENT_FEED_IDS))
        self.assertEqual({row["dry_run"] for row in requests}, {True})
        self.assertTrue(all("monthly_backfill" in str(row["parameter_ref"]) for row in requests))

    def test_writes_enriched_event_feed_task_keys_without_provider_calls(self):
        with tempfile.TemporaryDirectory() as td:
            summary = prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                target_cik="320193",
                storage_root=Path(td),
                write_files=True,
            )
            self.assertEqual(summary.task_key_count, 4)
            self.assertTrue(summary.write_performed)
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertFalse(summary.broker_execution_performed)
            by_feed = {}
            for item in summary.task_keys:
                payload = json.loads(Path(item.local_path).read_text())
                by_feed[payload["feed"]] = payload
                self.assertEqual(payload["manager_controls"]["allow_live_provider_calls"], False)
            self.assertEqual(by_feed["03_feed_alpaca_news"]["params"]["symbols"], ["AAPL"])
            self.assertEqual(by_feed["05_feed_gdelt_news"]["params"]["dry_run"], True)
            self.assertEqual(by_feed["07_feed_trading_economics_calendar_web"]["params"]["allow_live_fetch"], False)
            self.assertEqual(by_feed["07_feed_trading_economics_calendar_web"]["params"]["start_date"], "2016-01-01")
            self.assertEqual(by_feed["07_feed_trading_economics_calendar_web"]["params"]["end_date"], "2016-02-01")
            self.assertEqual(by_feed["08_feed_sec_company_financials"]["params"]["cik"], "0000320193")
            self.assertNotIn("tag", by_feed["08_feed_sec_company_financials"]["params"])


if __name__ == "__main__":
    unittest.main()

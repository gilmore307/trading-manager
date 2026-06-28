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
        self.assertEqual(len(requests), 66)
        self.assertEqual({row["target_component_id"] for row in requests}, set(REQUIRED_EVENT_FEED_IDS))
        self.assertEqual({row["dry_run"] for row in requests}, {True})
        self.assertTrue(all("monthly_backfill" in str(row["parameter_ref"]) for row in requests))
        self.assertEqual(
            len([row for row in requests if row["target_component_id"] == "12_feed_official_calendar_discovery"]),
            60,
        )

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
            self.assertEqual(summary.task_key_count, 34)
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
            self.assertNotIn("07_feed_trading_economics_calendar_web", by_feed)
            self.assertEqual(by_feed["08_feed_sec_company_financials"]["params"]["cik"], "0000320193")
            self.assertNotIn("tag", by_feed["08_feed_sec_company_financials"]["params"])
            self.assertEqual(by_feed["12_feed_official_calendar_discovery"]["params"]["data_kind"], "nasdaq_earnings_calendar")
            self.assertEqual(by_feed["12_feed_official_calendar_discovery"]["params"]["symbols"], ["AAPL"])
            calendar_payloads = [
                json.loads(Path(item.local_path).read_text())
                for item in summary.task_keys
                if item.feed_id == "12_feed_official_calendar_discovery"
            ]
            self.assertTrue(all(payload["params"]["date"] == payload["window"]["start_date"] for payload in calendar_payloads))
            self.assertTrue(
                all("/task_keys/aapl/" in payload["manager_controls"]["parameter_ref"] for payload in by_feed.values())
            )

    def test_task_keys_are_isolated_by_target_symbol(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            aapl = prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                write_files=True,
            )
            msft = prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="MSFT",
                storage_root=root,
                write_files=True,
            )

            aapl_paths = {item.local_path for item in aapl.task_keys}
            msft_paths = {item.local_path for item in msft.task_keys}
            self.assertFalse(aapl_paths & msft_paths)
            self.assertTrue(all("/task_keys/aapl/" in path for path in aapl_paths))
            self.assertTrue(all("/task_keys/msft/" in path for path in msft_paths))


if __name__ == "__main__":
    unittest.main()

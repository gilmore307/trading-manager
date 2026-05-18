import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.event_feed_backfill import prepare_event_feed_backfill
from trading_manager_tasks.event_feed_dispatch import dispatch_event_feed_backfill


class EventFeedDispatchTests(unittest.TestCase):
    def test_validates_prepared_event_feed_task_keys_without_provider_calls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                write_files=True,
            )
            summary = dispatch_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                trading_data_root=Path("/tmp/trading-data"),
                feed_ids=["07_feed_trading_economics_calendar_web"],
                execute_provider_calls=False,
            )
            self.assertFalse(summary.dispatch_performed)
            self.assertEqual(summary.provider_calls, 0)
            self.assertEqual(summary.validation_count, 1)
            self.assertEqual(summary.items[0].status, "validated_not_dispatched")
            self.assertIn("data_feed.07_feed_trading_economics_calendar_web", summary.items[0].command)

    def test_runtime_key_enables_only_selected_live_feed_controls(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                write_files=True,
            )

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            with patch("trading_manager_tasks.event_feed_dispatch.subprocess.run", return_value=Result()) as run_mock:
                summary = dispatch_event_feed_backfill(
                    start_month="2016-01",
                    end_month="2016-01",
                    target_symbol="AAPL",
                    storage_root=root,
                    trading_data_root=Path("/tmp/trading-data"),
                    feed_ids=["05_feed_gdelt_news", "07_feed_trading_economics_calendar_web"],
                    execute_provider_calls=True,
                    dynamic_workers=False,
                )
            self.assertTrue(summary.dispatch_performed)
            self.assertEqual(summary.provider_calls, 2)
            self.assertEqual(run_mock.call_count, 2)
            by_feed = {}
            for item in summary.items:
                payload = json.loads(Path(item.runtime_task_key_path).read_text())
                by_feed[payload["feed"]] = payload
                self.assertFalse(payload["dry_run"])
                self.assertTrue(payload["manager_controls"]["allow_live_provider_calls"])
                self.assertTrue(payload["manager_controls"]["autonomous_historical_provider_acquisition"])
            self.assertFalse(by_feed["05_feed_gdelt_news"]["params"]["dry_run"])
            self.assertEqual(by_feed["05_feed_gdelt_news"]["manager_controls"]["allowed_providers"], ["gdelt_bigquery"])
            self.assertEqual(by_feed["05_feed_gdelt_news"]["manager_controls"]["allowed_endpoint_families"], ["news_query"])
            self.assertTrue(by_feed["07_feed_trading_economics_calendar_web"]["params"]["allow_live_fetch"])
            self.assertEqual(by_feed["07_feed_trading_economics_calendar_web"]["manager_controls"]["allowed_providers"], ["trading_economics"])
            self.assertEqual(by_feed["07_feed_trading_economics_calendar_web"]["manager_controls"]["allowed_endpoint_families"], ["calendar_web"])
            self.assertEqual(by_feed["07_feed_trading_economics_calendar_web"]["manager_controls"]["max_time_window"], "45d")


if __name__ == "__main__":
    unittest.main()

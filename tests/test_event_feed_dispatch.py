import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.event_feed_backfill import prepare_event_feed_backfill
from trading_manager_tasks.event_feed_dispatch import DEFAULT_TRADING_DATA_ROOT, dispatch_event_feed_backfill


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
                feed_ids=["05_feed_gdelt_news"],
                execute_provider_calls=False,
            )
            self.assertFalse(summary.dispatch_performed)
            self.assertEqual(summary.provider_calls, 0)
            self.assertEqual(summary.validation_count, 1)
            self.assertEqual(summary.items[0].status, "validated_not_dispatched")
            self.assertEqual(summary.items[0].command[0], sys.executable)
            self.assertIn("data_feed.05_feed_gdelt_news", summary.items[0].command)

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

            captured_payloads = []

            def fake_run(command, **_kwargs):
                captured_payloads.append(json.loads(Path(command[3]).read_text()))
                return Result()

            with patch("trading_manager_tasks.event_feed_dispatch.subprocess.run", side_effect=fake_run) as run_mock:
                summary = dispatch_event_feed_backfill(
                    start_month="2016-01",
                    end_month="2016-01",
                    target_symbol="AAPL",
                    storage_root=root,
                    trading_data_root=Path("/tmp/trading-data"),
                    feed_ids=["05_feed_gdelt_news", "08_feed_sec_company_financials"],
                    execute_provider_calls=True,
                    dynamic_workers=False,
                )
            self.assertTrue(summary.dispatch_performed)
            self.assertEqual(summary.provider_calls, 2)
            self.assertEqual(run_mock.call_count, 2)
            by_feed = {}
            self.assertFalse(list((root / "runtime" / "event_feed_task_keys").glob("*/task_key.json")))
            for item, payload in zip(summary.items, captured_payloads):
                self.assertIsNone(item.runtime_task_key_path)
                self.assertFalse(item.runtime_task_key_retained)
                by_feed[payload["feed"]] = payload
                self.assertFalse(payload["dry_run"])
                self.assertTrue(payload["manager_controls"]["allow_live_provider_calls"])
                self.assertTrue(payload["manager_controls"]["autonomous_historical_provider_acquisition"])
            self.assertFalse(by_feed["05_feed_gdelt_news"]["params"]["dry_run"])
            self.assertEqual(by_feed["05_feed_gdelt_news"]["manager_controls"]["allowed_providers"], ["gdelt_bigquery"])
            self.assertEqual(by_feed["05_feed_gdelt_news"]["manager_controls"]["allowed_endpoint_families"], ["news_query"])
            self.assertEqual(by_feed["08_feed_sec_company_financials"]["manager_controls"]["allowed_providers"], ["sec_edgar"])
            self.assertEqual(by_feed["08_feed_sec_company_financials"]["manager_controls"]["allowed_endpoint_families"], ["company_financials"])

    def test_dispatch_skips_already_successful_requests_before_applying_limit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            trading_data_root = root / "trading-data"
            prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                write_files=True,
            )
            receipt = trading_data_root / "storage" / "monthly_backfill" / "alpaca_news" / "2016-01" / "completion_receipt.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps(
                    {
                        "runs": [
                            {
                                "run_id": "mgrreq_event_backfill_alpaca_news_aapl_2016_01_event_feed_20160101T000000Z",
                                "status": "succeeded",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            captured_payloads = []

            def fake_run(command, **_kwargs):
                captured_payloads.append(json.loads(Path(command[3]).read_text()))
                return Result()

            with patch("trading_manager_tasks.event_feed_dispatch.subprocess.run", side_effect=fake_run):
                summary = dispatch_event_feed_backfill(
                    start_month="2016-01",
                    end_month="2016-01",
                    target_symbol="AAPL",
                    storage_root=root,
                    trading_data_root=trading_data_root,
                    limit=1,
                    execute_provider_calls=True,
                    dynamic_workers=False,
                )

        self.assertEqual(summary.items[0].status, "already_succeeded")
        self.assertEqual(summary.provider_calls, 1)
        self.assertEqual(captured_payloads[0]["feed"], "05_feed_gdelt_news")

    def test_default_dispatch_receipts_resolve_to_source_data_storage_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source_storage_root = root / "trading-storage" / "storage" / "01_source_data"
            prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                write_files=True,
            )
            receipt = source_storage_root / "monthly_backfill" / "alpaca_news" / "2016-01" / "completion_receipt.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps(
                    {
                        "runs": [
                            {
                                "run_id": "mgrreq_event_backfill_alpaca_news_aapl_2016_01_event_feed_20160101T000000Z",
                                "status": "succeeded",
                                "row_counts": {"equity_news": 1},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with patch("trading_manager_tasks.event_feed_dispatch.data_storage_root", return_value=source_storage_root):
                summary = dispatch_event_feed_backfill(
                    start_month="2016-01",
                    end_month="2016-01",
                    target_symbol="AAPL",
                    storage_root=root,
                    trading_data_root=DEFAULT_TRADING_DATA_ROOT,
                    feed_ids=["03_feed_alpaca_news"],
                    execute_provider_calls=True,
                    dynamic_workers=False,
                )

        self.assertEqual(summary.provider_calls, 0)
        self.assertEqual(summary.items[0].status, "already_succeeded")
        self.assertEqual(Path(summary.items[0].receipt_path), receipt.resolve())

    def test_trading_economics_feed_is_not_dispatchable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prepare_event_feed_backfill(
                start_month="2016-01",
                end_month="2016-01",
                target_symbol="AAPL",
                storage_root=root,
                write_files=True,
            )

            with self.assertRaisesRegex(Exception, "unsupported event feed ids"):
                dispatch_event_feed_backfill(
                    start_month="2016-01",
                    end_month="2016-01",
                    target_symbol="AAPL",
                    storage_root=root,
                    trading_data_root=Path("/tmp/trading-data"),
                    feed_ids=["07_feed_trading_economics_calendar_web"],
                    execute_provider_calls=True,
                )


if __name__ == "__main__":
    unittest.main()

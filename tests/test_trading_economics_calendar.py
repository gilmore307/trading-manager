import csv
import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.trading_economics_calendar import plan_historical_seed, plan_recent_poll


class TradingEconomicsCalendarPlanningTests(unittest.TestCase):
    def test_historical_seed_inventory_is_retired_without_m06_source_task(self):
        with tempfile.TemporaryDirectory() as td:
            data_root = Path(td) / "trading-data"
            month_root = data_root / "storage" / "monthly_backfill" / "trading_economics_calendar_web" / "2016-01" / "runs"
            old_saved = month_root / "old" / "saved"
            new_saved = month_root / "new" / "saved"
            wrong_window_saved = month_root / "wrong-window" / "saved"
            old_saved.mkdir(parents=True)
            new_saved.mkdir(parents=True)
            wrong_window_saved.mkdir(parents=True)
            for path, event_time, event in [
                (old_saved / "trading_economics_calendar_event.csv", "2016-01-08T08:30:00-05:00", "Old"),
                (new_saved / "trading_economics_calendar_event.csv", "2016-01-08T08:30:00-05:00", "New"),
                (wrong_window_saved / "trading_economics_calendar_event.csv", "2026-05-18T08:30:00-04:00", "Wrong Window"),
            ]:
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["event_time", "event"])
                    writer.writeheader()
                    writer.writerow({"event_time": event_time, "event": event})
            # Ensure the wrong-window file is newest; in-month filtering should still reject it.
            (wrong_window_saved / "trading_economics_calendar_event.csv").touch()
            summary = plan_historical_seed(start_month="2016-01", end_month="2016-01", trading_data_root=data_root, storage_root=Path(td) / "manager", write_files=True)
            self.assertEqual(summary.contract_type, "te_calendar_historical_seed_retired")
            self.assertEqual(summary.covered_month_count, 1)
            self.assertEqual(summary.missing_months, ())
            self.assertIsNone(summary.task_key_path)
            self.assertIsNone(summary.task_key_hash)
            self.assertFalse(summary.write_performed)
            self.assertIn("M06 materialization consumes reviewed TE storage artifacts directly", summary.retired_reason or "")
            self.assertFalse(summary.database_writes_performed)
            self.assertEqual(summary.provider_calls, 0)

    def test_recent_poll_writes_storage_source_task_key(self):
        with tempfile.TemporaryDirectory() as td:
            summary = plan_recent_poll(as_of_date=__import__("datetime").date(2026, 5, 18), storage_root=Path(td), write_files=True)
            self.assertEqual(summary.contract_type, "te_calendar_recent_poll_plan")
            self.assertEqual(summary.date_range_mode, "recent")
            self.assertFalse(summary.use_authenticated_cookies)
            self.assertIsNotNone(summary.task_key_path)
            self.assertIsNotNone(summary.task_key_hash)
            self.assertTrue(summary.write_performed)
            self.assertIsNone(summary.retired_reason)
            self.assertEqual(summary.provider_calls, 0)
            task_key = json.loads(Path(summary.task_key_path or "").read_text(encoding="utf-8"))
            self.assertEqual(task_key["params"]["source_materialization_role"], "append_to_trading_economics_monthly_backfill")
            self.assertTrue(task_key["params"]["allow_live_fetch"])
            self.assertFalse(task_key["manager_controls"]["database_writes_performed"])
            self.assertFalse(task_key["manager_controls"]["website_url_persistence"])


if __name__ == "__main__":
    unittest.main()

import csv
import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.trading_economics_calendar import plan_historical_seed, plan_recent_poll


class TradingEconomicsCalendarPlanningTests(unittest.TestCase):
    def test_historical_seed_selects_latest_nonempty_artifact_per_month(self):
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
            self.assertEqual(summary.covered_month_count, 1)
            self.assertEqual(summary.missing_months, ())
            self.assertTrue(summary.task_key_path)
            payload = json.loads(Path(summary.task_key_path).read_text())
            self.assertEqual(payload["source"], "source_09_event_risk_governor")
            self.assertEqual(payload["params"]["source_materialization_role"], "historical_seed_to_event_risk_governor_source")
            self.assertEqual(len(payload["params"]["feed_artifact_paths"]), 1)
            self.assertIn("/filtered_artifacts/2016-01/", payload["params"]["feed_artifact_paths"][0])
            filtered_path = Path(payload["params"]["feed_artifact_paths"][0])
            manifest = json.loads((filtered_path.parent / "manifest.json").read_text())
            self.assertEqual(manifest["row_count"], 2)
            self.assertTrue(any("/new/saved/" in path for path in manifest["source_artifact_paths"]))
            self.assertTrue(any("/old/saved/" in path for path in manifest["source_artifact_paths"]))
            self.assertFalse(any("/wrong-window/saved/" in path for path in manifest["source_artifact_paths"]))
            with filtered_path.open(newline="", encoding="utf-8") as handle:
                self.assertEqual({row["event"] for row in csv.DictReader(handle)}, {"Old", "New"})
            self.assertFalse(manifest["raw_original_deleted"])
            self.assertFalse(summary.database_writes_performed)
            self.assertEqual(summary.provider_calls, 0)

    def test_recent_poll_plans_logged_out_recent_feed_task(self):
        with tempfile.TemporaryDirectory() as td:
            summary = plan_recent_poll(as_of_date=__import__("datetime").date(2026, 5, 18), storage_root=Path(td), write_files=True)
            self.assertEqual(summary.date_range_mode, "recent")
            self.assertFalse(summary.use_authenticated_cookies)
            payload = json.loads(Path(summary.task_key_path).read_text())
            self.assertEqual(payload["feed"], "07_feed_trading_economics_calendar_web")
            self.assertEqual(payload["params"]["date_range_mode"], "recent")
            self.assertFalse(payload["params"]["use_authenticated_cookies"])
            self.assertEqual(payload["manager_controls"]["allowed_endpoint_families"], ["calendar_web"])
            self.assertTrue(payload["manager_controls"]["realtime_provider_maintenance"])
            self.assertEqual(payload["manager_controls"]["max_requests"], 2)
            self.assertEqual(payload["manager_controls"]["retry_policy_ref"], "te_recent_release_fetch_retry_after_10s_once")
            self.assertIn("retry_after_10s_once_on_fetch_failure", payload["policy_refs"])
            self.assertEqual(payload["params"]["end_date"], "2026-07-02")
            self.assertEqual(summary.provider_calls, 0)


if __name__ == "__main__":
    unittest.main()

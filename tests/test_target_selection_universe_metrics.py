from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.target_selection_universe_metrics import build_target_selection_universe_metrics


class TargetSelectionUniverseMetricsTests(unittest.TestCase):
    def test_materializes_selected_target_effectiveness_against_visible_universe(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision_rows = tmp / "decision_rows.jsonl"
            candidate_universe = tmp / "historical_candidate_universe.csv"
            output_path = tmp / "target_selection_universe_metrics.csv"
            decision_rows.write_text(
                json.dumps(
                    {
                        "decision_id": "r1",
                        "timestamp": "2021-02-02T16:00:00-05:00",
                        "next_timestamp": "2021-02-03T16:00:00-05:00",
                        "target_ref": "MSFT",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with candidate_universe.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["symbol", "target_ref", "asset_class", "replay_candidate_status"],
                )
                writer.writeheader()
                writer.writerow(
                    {"symbol": "AAPL", "target_ref": "AAPL", "asset_class": "us_equity", "replay_candidate_status": "active"}
                )
                writer.writerow(
                    {"symbol": "MSFT", "target_ref": "MSFT", "asset_class": "us_equity", "replay_candidate_status": "active"}
                )
                writer.writerow(
                    {"symbol": "NVDA", "target_ref": "NVDA", "asset_class": "us_equity", "replay_candidate_status": "active"}
                )
            report = build_target_selection_universe_metrics(
                decision_rows_path=decision_rows,
                candidate_universe_path=candidate_universe,
                output_path=output_path,
                bar_rows=[
                    {"symbol": "AAPL", "timestamp": datetime(2021, 2, 2, tzinfo=UTC), "bar_close": 100.0},
                    {"symbol": "AAPL", "timestamp": datetime(2021, 2, 3, tzinfo=UTC), "bar_close": 105.0},
                    {"symbol": "MSFT", "timestamp": datetime(2021, 2, 2, tzinfo=UTC), "bar_close": 100.0},
                    {"symbol": "MSFT", "timestamp": datetime(2021, 2, 3, tzinfo=UTC), "bar_close": 110.0},
                    {"symbol": "NVDA", "timestamp": datetime(2021, 2, 2, tzinfo=UTC), "bar_close": 100.0},
                    {"symbol": "NVDA", "timestamp": datetime(2021, 2, 3, tzinfo=UTC), "bar_close": 120.0},
                ],
                now_utc=datetime(2026, 6, 21, 16, 0, tzinfo=UTC),
            )

            self.assertEqual(report["summary"]["row_count"], 3)
            self.assertEqual(report["summary"]["selected_row_count"], 1)
            self.assertEqual(report["summary"]["forward_return_status_counts"]["computed"], 3)
            self.assertFalse(report["side_effects"]["provider_call_performed"])
            self.assertTrue(output_path.with_suffix(".report.json").exists())
            with output_path.open(encoding="utf-8") as handle:
                rows = {row["target_ref"]: row for row in csv.DictReader(handle)}
            self.assertEqual(rows["MSFT"]["selected_by_replay"], "True")
            self.assertEqual(rows["MSFT"]["forward_return"], "0.1")
            self.assertEqual(rows["MSFT"]["forward_return_rank"], "2")
            self.assertEqual(rows["MSFT"]["forward_return_percentile"], "0.5")
            self.assertEqual(rows["MSFT"]["opportunity_cost_to_best"], "0.1")
            self.assertEqual(rows["NVDA"]["top_quartile_candidate"], "True")

    def test_missing_exit_bar_keeps_universe_visible_but_marks_return_gap(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision_rows = tmp / "decision_rows.jsonl"
            candidate_universe = tmp / "historical_candidate_universe.csv"
            output_path = tmp / "target_selection_universe_metrics.csv"
            decision_rows.write_text(
                json.dumps(
                    {
                        "timestamp": "2021-02-02T16:00:00-05:00",
                        "next_timestamp": "2021-02-03T16:00:00-05:00",
                        "target_ref": "MSFT",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with candidate_universe.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["symbol", "target_ref", "asset_class", "replay_candidate_status"],
                )
                writer.writeheader()
                writer.writerow(
                    {"symbol": "MSFT", "target_ref": "MSFT", "asset_class": "us_equity", "replay_candidate_status": "active"}
                )

            report = build_target_selection_universe_metrics(
                decision_rows_path=decision_rows,
                candidate_universe_path=candidate_universe,
                output_path=output_path,
                bar_rows=[
                    {"symbol": "MSFT", "timestamp": datetime(2021, 2, 2, tzinfo=UTC), "bar_close": 100.0},
                ],
                now_utc=datetime(2026, 6, 21, 16, 0, tzinfo=UTC),
            )

            self.assertEqual(report["summary"]["forward_return_status_counts"]["missing_exit_bar"], 1)
            with output_path.open(encoding="utf-8") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["visible_universe_membership"], "True")
            self.assertEqual(row["selected_by_replay"], "True")
            self.assertEqual(row["forward_return_status"], "missing_exit_bar")
            self.assertEqual(row["forward_return"], "")


if __name__ == "__main__":
    unittest.main()

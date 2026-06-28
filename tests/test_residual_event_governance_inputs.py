from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.event_feed_coverage import discover_event_feed_artifacts
from trading_manager_tasks.residual_event_governance_inputs import materialize_residual_event_governance_inputs_inputs


def _write_layer_two_bar_receipt(storage_root: Path, symbol: str, month: str, row_count: int = 1) -> None:
    receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": "run_001",
                        "status": "succeeded",
                        "outputs": ["trading_data.model_01_market_regime_data_acquisition"],
                        "row_counts": {"equity_bar": row_count},
                        "steps": {"save": {"references": ["trading_data.model_01_market_regime_data_acquisition"]}},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class ResidualEventGovernanceInputTests(unittest.TestCase):
    def test_dry_run_prepares_detector_and_source_task_keys_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")

            summary = materialize_residual_event_governance_inputs_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

            self.assertEqual(summary.contract_type, "manager_residual_event_governance_input_materialization")
            self.assertEqual(summary.detector_run_count, 1)
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertTrue(Path(summary.source_task_key_path).exists())
            self.assertTrue(Path(summary.source_task_key_path).is_relative_to(tmp / "manager-storage"))
            source_task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))
            self.assertTrue(Path(source_task_key["output_root"]).is_relative_to(tmp / "manager-storage"))
            detector_task_key = json.loads(Path(summary.detector_runs[0].task_key_path).read_text(encoding="utf-8"))
            self.assertTrue(Path(detector_task_key["output_root"]).is_relative_to(tmp / "manager-storage"))
            self.assertIn("bars_sql_source", detector_task_key["params"])
            self.assertNotIn("bars_csv_path", detector_task_key["params"])

    def test_zero_row_feed_receipts_are_skipped_before_detector_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-02", row_count=0)

            summary = materialize_residual_event_governance_inputs_inputs(
                start_month="2016-02",
                end_month="2016-02",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

            self.assertEqual(summary.detector_run_count, 1)
            self.assertEqual(summary.detector_runs[0].status, "skipped_zero_bar_rows")
            self.assertEqual(summary.detector_event_count, 0)
            self.assertEqual(summary.provider_calls, 0)

    def test_fold_materialization_prepares_detector_per_symbol_month(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            for month in ("2016-01", "2016-02"):
                _write_layer_two_bar_receipt(storage_root, "XLF", month)

            summary = materialize_residual_event_governance_inputs_inputs(
                start_month="2016-01",
                end_month="2016-02",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))

            self.assertEqual(summary.detector_run_count, 2)
            self.assertEqual({run.month for run in summary.detector_runs}, {"2016-01", "2016-02"})
            self.assertEqual(Path(summary.source_task_key_path).name, "m06_residual_event_governance_data_acquisition_task_key.json")
            self.assertEqual(task_key["params"]["start"], "2016-01-01T00:00:00-05:00")
            self.assertEqual(task_key["params"]["end"], "2016-03-01T00:00:00-05:00")
            self.assertTrue(all(Path(run.task_key_path).exists() for run in summary.detector_runs))

    def test_dry_run_includes_reviewed_news_and_sec_artifacts_in_source_task_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")
            feed_root = trading_data_root / "storage" / "monthly_backfill"
            artifacts = {
                "alpaca_news": ("equity_news.csv", "id,timeline_headline,created_at,updated_at,symbols,summary,event_link_url\nn1,Headline,2016-01-04T10:00:00-05:00,2016-01-04T10:01:00-05:00,XLF,Summary,https://example.com/news\n"),
                "gdelt_news": ("gdelt_article.csv", "article_id,seen_at,source_domain,event_link_url,title,source_theme_tags,organizations,tone,impact_scope\ng1,2016-01-04T09:00:00-05:00,reuters.com,https://example.com/gdelt,Fed news,ECON,Federal Reserve,-1,market\n"),
                "sec_company_financials": ("sec_company_fact.csv", "cik,entity_name,taxonomy,tag,label,description,unit,fy,fp,form,filed,frame,end,value,accession_number,symbol\n1,Test Inc,us-gaap,Revenues,Revenue,,USD,2016,Q1,10-Q,2016-01-05,,2015-12-31,1,a1,XLF\n"),
                "release_calendar": ("release_calendar.csv", "event_id,calendar_source,event_name,release_time,event_date,timezone,source_url,raw_summary,symbol\nc1,nasdaq_earnings_calendar,XLF earnings,2016-01-20T16:05:00-05:00,2016-01-20,America/New_York,https://example.com/calendar,,XLF\n"),
            }
            for source_id, (filename, content) in artifacts.items():
                path = feed_root / source_id / "2016-01" / "runs" / "run_001" / "saved" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            summary = materialize_residual_event_governance_inputs_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))

            self.assertEqual(set(summary.event_feed_coverage), set(artifacts))
            self.assertTrue(all(count == 1 for count in summary.event_feed_coverage.values()))
            self.assertGreaterEqual(summary.event_feed_row_coverage["alpaca_news"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["gdelt_news"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["sec_company_financials"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["release_calendar"], 1)
            self.assertNotIn("trading_economics_calendar_web", summary.event_feed_coverage)
            self.assertEqual(len(task_key["params"]["event_artifact_paths"]), 4)
            self.assertEqual(summary.provider_calls, 0)

    def test_uses_latest_reviewed_feed_artifact_per_source_month(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            feed_root = trading_data_root / "storage" / "monthly_backfill" / "gdelt_news" / "2016-01" / "runs"
            old_path = feed_root / "run_old" / "saved" / "gdelt_article.csv"
            new_path = feed_root / "run_new" / "saved" / "gdelt_article.csv"
            old_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.write_text("old\n", encoding="utf-8")
            new_path.write_text("new\n", encoding="utf-8")
            os.utime(old_path, (1, 1))
            os.utime(new_path, (2, 2))

            paths, coverage = discover_event_feed_artifacts(trading_data_root=trading_data_root, start_month="2016-01", end_month="2016-01")

            self.assertEqual(coverage["gdelt_news"], 1)
            self.assertEqual(paths, [str(new_path)])

    def test_release_calendar_sql_receipt_is_included_as_m06_event_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")
            for source_id, row_counts in {
                "alpaca_news": {"equity_news": 1},
                "gdelt_news": {"gdelt_article": 1},
                "sec_company_financials": {"sec_company_fact": 1},
                "release_calendar": {"release_calendar": 1},
            }.items():
                receipt = storage_root / "monthly_backfill" / source_id / "2016-01" / "completion_receipt.json"
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({"runs": [{"status": "succeeded", "row_counts": row_counts}]}), encoding="utf-8")

            summary = materialize_residual_event_governance_inputs_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))

        self.assertEqual(summary.event_feed_coverage["release_calendar"], 1)
        self.assertEqual(summary.event_feed_row_coverage["release_calendar"], 1)
        self.assertTrue(any(item["table"] == "feed_12_release_calendar" for item in task_key["params"]["event_sql_inputs"]))

    def test_event_feed_sql_row_coverage_sums_all_successful_runs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")
            for source_id, row_counts in {
                "alpaca_news": {"equity_news": 1},
                "gdelt_news": {"gdelt_article": 1},
                "sec_company_financials": {"sec_company_fact": 1},
            }.items():
                receipt = storage_root / "monthly_backfill" / source_id / "2016-01" / "completion_receipt.json"
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({"runs": [{"status": "succeeded", "row_counts": row_counts}]}), encoding="utf-8")
            calendar_receipt = storage_root / "monthly_backfill" / "release_calendar" / "2016-01" / "completion_receipt.json"
            calendar_receipt.parent.mkdir(parents=True, exist_ok=True)
            calendar_receipt.write_text(
                json.dumps(
                    {
                        "runs": [
                            {"status": "succeeded", "row_counts": {"release_calendar": 2}},
                            {"status": "succeeded", "row_counts": {"release_calendar": 0}},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = materialize_residual_event_governance_inputs_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

        self.assertEqual(summary.event_feed_coverage["release_calendar"], 1)
        self.assertEqual(summary.event_feed_row_coverage["release_calendar"], 2)

    def test_write_allows_missing_optional_release_calendar_when_sec_release_evidence_exists(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01", row_count=0)
            for source_id, row_counts in {
                "alpaca_news": {"equity_news": 1},
                "gdelt_news": {"gdelt_article": 1},
                "sec_company_financials": {"sec_company_fact": 1},
            }.items():
                receipt = storage_root / "monthly_backfill" / source_id / "2016-01" / "completion_receipt.json"
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({"runs": [{"status": "succeeded", "row_counts": row_counts}]}), encoding="utf-8")

            class Result:
                returncode = 0
                stdout = json.dumps({"references": [], "row_counts": {"m06_residual_event_governance_data_acquisition": 0}})
                stderr = ""

            with patch("trading_manager_tasks.residual_event_governance_inputs.subprocess.run", return_value=Result()):
                summary = materialize_residual_event_governance_inputs_inputs(
                    start_month="2016-01",
                    end_month="2016-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=trading_data_root,
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    write=True,
                )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))

        self.assertEqual(summary.event_feed_row_coverage["release_calendar"], 0)
        self.assertNotIn("release_calendar", {item["kind"] for item in task_key["params"]["event_sql_inputs"]})
        self.assertIn("sec_company_financials", {item["kind"] for item in task_key["params"]["event_sql_inputs"]})

    def test_write_blocks_when_reviewed_event_feed_artifacts_have_zero_in_window_rows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")
            feed_root = trading_data_root / "storage" / "monthly_backfill"
            artifacts = {
                "alpaca_news": ("equity_news.csv", "id,timeline_headline,created_at,updated_at,symbols,summary,event_link_url\nn1,Headline,2016-01-04T10:00:00-05:00,2016-01-04T10:01:00-05:00,XLF,Summary,https://example.com/news\n"),
                "gdelt_news": ("gdelt_article.csv", "article_id,seen_at,source_domain,event_link_url,title,source_theme_tags,organizations,tone,impact_scope\ng1,2016-02-04T09:00:00-05:00,reuters.com,https://example.com/gdelt,Fed news,ECON,Federal Reserve,-1,market\n"),
                "sec_company_financials": ("sec_company_fact.csv", "cik,entity_name,taxonomy,tag,label,description,unit,fy,fp,form,filed,frame,end,value,accession_number,symbol\n1,Test Inc,us-gaap,Revenues,Revenue,,USD,2016,Q1,10-Q,2016-01-05,,2015-12-31,1,a1,XLF\n"),
                "release_calendar": ("release_calendar.csv", "event_id,calendar_source,event_name,release_time,event_date,timezone,source_url,raw_summary,symbol\nc1,nasdaq_earnings_calendar,XLF earnings,2016-01-20T16:05:00-05:00,2016-01-20,America/New_York,https://example.com/calendar,,XLF\n"),
            }
            for source_id, (filename, content) in artifacts.items():
                path = feed_root / source_id / "2016-01" / "runs" / "run_001" / "saved" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(TaskSystemError, "zero in-window rows.*gdelt_news"):
                materialize_residual_event_governance_inputs_inputs(
                    start_month="2016-01",
                    end_month="2016-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=trading_data_root,
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    write=True,
                )

    def test_write_blocks_when_required_event_feed_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")

            with self.assertRaisesRegex(TaskSystemError, "event-risk coverage is incomplete"):
                materialize_residual_event_governance_inputs_inputs(
                    start_month="2016-01",
                    end_month="2016-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=trading_data_root,
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    write=True,
                )


if __name__ == "__main__":
    unittest.main()

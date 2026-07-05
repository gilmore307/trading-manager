from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.event_feed_coverage import discover_event_feed_artifacts, successful_feed_runs
from trading_manager_tasks.model_03_event_impact_inputs import materialize_model_03_event_impact_inputs


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

            summary = materialize_model_03_event_impact_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

            self.assertEqual(summary.contract_type, "manager_model_03_event_impact_input_materialization")
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
            source_task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))
            self.assertIn("market_session_calendar", summary.event_feed_coverage)
            self.assertGreater(summary.event_feed_row_coverage["market_session_calendar"], 0)
            self.assertTrue(any(event["event_category_type"] == "market_structure" for event in source_task_key["params"]["events"]))

    def test_zero_row_feed_receipts_are_skipped_before_detector_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-02", row_count=0)

            summary = materialize_model_03_event_impact_inputs(
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

    def test_market_session_calendar_includes_expiry_and_rebalance_windows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2021-03")

            summary = materialize_model_03_event_impact_inputs(
                start_month="2021-03",
                end_month="2021-03",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))
            market_events = [event for event in task_key["params"]["events"] if event["event_category_type"] == "market_structure"]
            summaries = "\n".join(event["summary"] for event in market_events)

            self.assertIn("market_structure_type=monthly_option_expiration", summaries)
            self.assertIn("market_structure_type=triple_witching", summaries)
            self.assertIn("market_structure_type=quarterly_etf_index_rebalance_window", summaries)
            self.assertIn("market_structure_type=month_end_rebalance_window", summaries)
            self.assertEqual(summary.event_feed_coverage["market_session_calendar"], 1)

    def test_fold_materialization_prepares_detector_per_symbol_month(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            for month in ("2016-01", "2016-02"):
                _write_layer_two_bar_receipt(storage_root, "XLF", month)

            summary = materialize_model_03_event_impact_inputs(
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
            self.assertEqual(Path(summary.source_task_key_path).name, "model_03_event_impact_data_acquisition_task_key.json")
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
                "trading_economics_calendar_web": ("trading_economics_calendar_event.csv", "event_time,country,event,source_event_type,reference,actual,previous,consensus,te_forecast,revised,importance,symbol\n2016-01-08T08:30:00-05:00,United States,Non Farm Payrolls,employment,te:nfp,200K,180K,190K,,,3,\n"),
                "release_calendar": ("release_calendar.csv", "event_id,calendar_source,event_name,release_time,event_date,timezone,source_url,raw_summary,symbol\nc1,nasdaq_earnings_calendar,XLF earnings,2016-01-20T16:05:00-05:00,2016-01-20,America/New_York,https://example.com/calendar,,XLF\n"),
            }
            for source_id, (filename, content) in artifacts.items():
                path = feed_root / source_id / "2016-01" / "runs" / "run_001" / "saved" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            summary = materialize_model_03_event_impact_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))

            self.assertEqual(set(summary.event_feed_coverage), {*artifacts, "market_session_calendar"})
            for source_id in artifacts:
                self.assertEqual(summary.event_feed_coverage[source_id], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["alpaca_news"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["gdelt_news"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["sec_company_financials"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["market_session_calendar"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["trading_economics_calendar_web"], 1)
            self.assertGreaterEqual(summary.event_feed_row_coverage["release_calendar"], 1)
            self.assertEqual(len(task_key["params"]["event_artifact_paths"]), 5)
            self.assertTrue(any(event["source_name"] == "manager_market_session_calendar" for event in task_key["params"]["events"]))
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

    def test_successful_feed_runs_falls_back_to_saved_artifact_after_receipt_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            artifact = storage_root / "monthly_backfill" / "release_calendar" / "2016-01" / "runs" / "run_001" / "saved" / "release_calendar.csv"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(
                "event_id,calendar_source,event_name,release_time,event_date,timezone,source_url,raw_summary,symbol\n"
                "c1,nasdaq_earnings_calendar,XLF earnings,2016-01-20T16:05:00-05:00,2016-01-20,America/New_York,https://example.com/calendar,,XLF\n"
                "c2,nasdaq_earnings_calendar,SPY earnings,2016-01-21T16:05:00-05:00,2016-01-21,America/New_York,https://example.com/calendar,,SPY\n",
                encoding="utf-8",
            )

            runs = successful_feed_runs(storage_root / "monthly_backfill" / "release_calendar" / "2016-01" / "completion_receipt.json")

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "succeeded")
        self.assertEqual(runs[0]["run_id"], "run_001")
        self.assertEqual(runs[0]["row_counts"], {"release_calendar": 2})
        self.assertEqual(runs[0]["receipt_reconstruction"], "saved_artifact_fallback")

    def test_successful_feed_runs_keeps_failed_receipt_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            month_dir = storage_root / "monthly_backfill" / "release_calendar" / "2016-01"
            artifact = month_dir / "runs" / "run_001" / "saved" / "release_calendar.csv"
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(
                "event_id,calendar_source,event_name,release_time,event_date,timezone,source_url,raw_summary,symbol\n"
                "c1,nasdaq_earnings_calendar,XLF earnings,2016-01-20T16:05:00-05:00,2016-01-20,America/New_York,https://example.com/calendar,,XLF\n",
                encoding="utf-8",
            )
            receipt = month_dir / "completion_receipt.json"
            receipt.write_text(json.dumps({"runs": [{"status": "failed", "row_counts": {"release_calendar": 1}}]}), encoding="utf-8")

            runs = successful_feed_runs(receipt)

        self.assertEqual(runs, ())

    def test_successful_feed_runs_reads_compact_receipt_manifest_after_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            manifest = storage_root / "90_lifecycle" / "maintenance" / "compact_contracts" / "event_feed_monthly_receipt_compaction_manifest.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(
                json.dumps(
                    {
                        "contract_type": "storage_event_feed_monthly_receipt_compaction_manifest",
                        "source_month_summaries": [
                            {
                                "source_id": "alpaca_news",
                                "month": "2016-01",
                                "row_counts": {"equity_news": 405},
                                "receipt_ref": "storage/01_source_data/monthly_backfill/alpaca_news/2016-01/completion_receipt.json",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            runs = successful_feed_runs(storage_root / "01_source_data" / "monthly_backfill" / "alpaca_news" / "2016-01" / "completion_receipt.json")

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "succeeded")
        self.assertEqual(runs[0]["row_counts"], {"equity_news": 405})
        self.assertEqual(runs[0]["receipt_reconstruction"], "compact_provenance_manifest")

    def test_release_calendar_sql_receipt_is_included_as_m03_event_input(self) -> None:
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
                "trading_economics_calendar_web": {"trading_economics_calendar_event": 1},
                "release_calendar": {"release_calendar": 1},
            }.items():
                receipt = storage_root / "monthly_backfill" / source_id / "2016-01" / "completion_receipt.json"
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(json.dumps({"runs": [{"status": "succeeded", "row_counts": row_counts}]}), encoding="utf-8")

            summary = materialize_model_03_event_impact_inputs(
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
            te_artifact = storage_root / "monthly_backfill" / "trading_economics_calendar_web" / "2016-01" / "runs" / "run_001" / "saved" / "trading_economics_calendar_event.csv"
            te_artifact.parent.mkdir(parents=True, exist_ok=True)
            te_artifact.write_text(
                "event_time,country,event,source_event_type,reference,actual,previous,consensus,te_forecast,revised,importance,symbol\n"
                "2016-01-08T08:30:00-05:00,United States,Non Farm Payrolls,employment,te:nfp,200K,180K,190K,,,3,\n",
                encoding="utf-8",
            )
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

            summary = materialize_model_03_event_impact_inputs(
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
            te_artifact = storage_root / "monthly_backfill" / "trading_economics_calendar_web" / "2016-01" / "runs" / "run_001" / "saved" / "trading_economics_calendar_event.csv"
            te_artifact.parent.mkdir(parents=True, exist_ok=True)
            te_artifact.write_text(
                "event_time,country,event,source_event_type,reference,actual,previous,consensus,te_forecast,revised,importance,symbol\n"
                "2016-01-08T08:30:00-05:00,United States,Non Farm Payrolls,employment,te:nfp,200K,180K,190K,,,3,\n",
                encoding="utf-8",
            )

            class Result:
                returncode = 0
                stdout = json.dumps({"references": [], "row_counts": {"m03_event_state_data_acquisition": 0}})
                stderr = ""

            with patch("trading_manager_tasks.model_03_event_impact_inputs.subprocess.run", return_value=Result()):
                summary = materialize_model_03_event_impact_inputs(
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
        self.assertGreater(summary.event_feed_row_coverage["market_session_calendar"], 0)
        self.assertNotIn("release_calendar", {item["kind"] for item in task_key["params"]["event_sql_inputs"]})
        self.assertIn("sec_company_financials", {item["kind"] for item in task_key["params"]["event_sql_inputs"]})
        self.assertTrue(any(event["event_category_type"] == "market_structure" for event in task_key["params"]["events"]))

    def test_write_records_zero_row_reviewed_event_feeds_without_blocking_m03(self) -> None:
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
                "trading_economics_calendar_web": ("trading_economics_calendar_event.csv", "event_time,country,event,source_event_type,reference,actual,previous,consensus,te_forecast,revised,importance,symbol\n2016-01-08T08:30:00-05:00,United States,Non Farm Payrolls,employment,te:nfp,200K,180K,190K,,,3,\n"),
                "release_calendar": ("release_calendar.csv", "event_id,calendar_source,event_name,release_time,event_date,timezone,source_url,raw_summary,symbol\nc1,nasdaq_earnings_calendar,XLF earnings,2016-01-20T16:05:00-05:00,2016-01-20,America/New_York,https://example.com/calendar,,XLF\n"),
            }
            for source_id, (filename, content) in artifacts.items():
                path = feed_root / source_id / "2016-01" / "runs" / "run_001" / "saved" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            class Result:
                returncode = 0
                stdout = json.dumps({"references": [], "row_counts": {"m03_event_state_data_acquisition": 0}})
                stderr = ""

            with patch("trading_manager_tasks.model_03_event_impact_inputs.subprocess.run", return_value=Result()):
                summary = materialize_model_03_event_impact_inputs(
                    start_month="2016-01",
                    end_month="2016-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=trading_data_root,
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    write=True,
                )

        self.assertEqual(summary.event_feed_row_coverage["gdelt_news"], 0)
        self.assertGreater(summary.event_feed_row_coverage["market_session_calendar"], 0)

    def test_write_records_missing_event_feeds_without_blocking_m03(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_receipt(storage_root, "XLF", "2016-01")

            class Result:
                returncode = 0
                stdout = json.dumps({"references": [], "row_counts": {"m03_event_state_data_acquisition": 0}})
                stderr = ""

            with patch("trading_manager_tasks.model_03_event_impact_inputs.subprocess.run", return_value=Result()):
                summary = materialize_model_03_event_impact_inputs(
                    start_month="2016-01",
                    end_month="2016-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=trading_data_root,
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    write=True,
                )
            task_key = json.loads(Path(summary.source_task_key_path).read_text(encoding="utf-8"))

        self.assertEqual(summary.event_feed_coverage["alpaca_news"], 0)
        self.assertEqual(summary.event_feed_row_coverage["alpaca_news"], 0)
        self.assertGreater(summary.event_feed_row_coverage["market_session_calendar"], 0)
        self.assertTrue(any(event["event_category_type"] == "market_structure" for event in task_key["params"]["events"]))

    def test_write_blocks_when_no_event_inputs_or_market_context_exist(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,model_01_sector_context\n", encoding="utf-8")

            with self.assertRaisesRegex(TaskSystemError, "no successful M02 feed artifacts"):
                materialize_model_03_event_impact_inputs(
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

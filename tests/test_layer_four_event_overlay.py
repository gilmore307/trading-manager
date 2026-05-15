from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.layer_four_event_overlay import materialize_layer_four_event_overlay_inputs


def _write_layer_two_bar_artifact(storage_root: Path, symbol: str, month: str, row_count: int = 1) -> None:
    run_dir = storage_root / "monthly_backfill" / "alpaca_bars" / symbol / month / "runs" / "run_001"
    (run_dir / "cleaned").mkdir(parents=True)
    (run_dir / "saved").mkdir(parents=True)
    (run_dir / "cleaned" / "equity_bar.jsonl").write_text(
        "" if row_count <= 0 else f'{{"symbol":"{symbol}","timestamp":"{month}-04T09:30:00-05:00"}}\n',
        encoding="utf-8",
    )
    (run_dir / "saved" / "equity_bar.csv").write_text(
        "symbol,timestamp,bar_open,bar_high,bar_low,bar_close,bar_volume,timeframe\n"
        + ("" if row_count <= 0 else f"{symbol},{month}-04T09:30:00-05:00,1,2,1,2,100,30Min\n"),
        encoding="utf-8",
    )
    receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": "run_001",
                        "status": "succeeded",
                        "row_counts": {"equity_bar": row_count},
                        "steps": {"clean": {"references": [f"storage/monthly_backfill/alpaca_bars/{symbol}/{month}/runs/run_001/cleaned/equity_bar.jsonl"]}},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class LayerFourEventOverlayTests(unittest.TestCase):
    def test_dry_run_prepares_detector_and_source_task_keys_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,layer_02_sector_context\n", encoding="utf-8")
            run_dir = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / "2016-01" / "runs" / "run_001"
            (run_dir / "cleaned").mkdir(parents=True)
            (run_dir / "saved").mkdir(parents=True)
            (run_dir / "cleaned" / "equity_bar.jsonl").write_text('{"symbol":"XLF","timestamp":"2016-01-04T09:30:00-05:00"}\n', encoding="utf-8")
            (run_dir / "saved" / "equity_bar.csv").write_text("symbol,timestamp,bar_open,bar_high,bar_low,bar_close,bar_volume,timeframe\nXLF,2016-01-04T09:30:00-05:00,1,2,1,2,100,30Min\n", encoding="utf-8")
            receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / "2016-01" / "completion_receipt.json"
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(
                    {
                        "runs": [
                            {
                                "run_id": "run_001",
                                "status": "succeeded",
                                "row_counts": {"equity_bar": 1},
                                "steps": {"clean": {"references": ["storage/monthly_backfill/alpaca_bars/XLF/2016-01/runs/run_001/cleaned/equity_bar.jsonl"]}},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = materialize_layer_four_event_overlay_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

            self.assertEqual(summary.contract_type, "manager_layer_four_event_overlay_input_materialization")
            self.assertEqual(summary.detector_run_count, 1)
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertTrue(Path(summary.source_task_key_path).exists())

    def test_zero_row_feed_artifacts_are_skipped_before_detector_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nARKF,layer_02_sector_context\n", encoding="utf-8")
            run_dir = storage_root / "monthly_backfill" / "alpaca_bars" / "ARKF" / "2016-02" / "runs" / "run_001"
            (run_dir / "cleaned").mkdir(parents=True)
            (run_dir / "saved").mkdir(parents=True)
            (run_dir / "cleaned" / "equity_bar.jsonl").write_text("", encoding="utf-8")
            (run_dir / "saved" / "equity_bar.csv").write_text("symbol,timestamp,bar_open,bar_high,bar_low,bar_close,bar_volume,timeframe\n", encoding="utf-8")
            receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / "ARKF" / "2016-02" / "completion_receipt.json"
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(
                json.dumps(
                    {
                        "runs": [
                            {
                                "run_id": "run_001",
                                "status": "succeeded",
                                "row_counts": {"equity_bar": 0},
                                "steps": {"clean": {"references": ["storage/monthly_backfill/alpaca_bars/ARKF/2016-02/runs/run_001/cleaned/equity_bar.jsonl"]}},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            summary = materialize_layer_four_event_overlay_inputs(
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
            universe_path.write_text("symbol,model_layer\nXLF,layer_02_sector_context\n", encoding="utf-8")
            for month in ("2016-01", "2016-02"):
                run_dir = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / month / "runs" / "run_001"
                (run_dir / "cleaned").mkdir(parents=True)
                (run_dir / "saved").mkdir(parents=True)
                (run_dir / "cleaned" / "equity_bar.jsonl").write_text(f'{{"symbol":"XLF","timestamp":"{month}-04T09:30:00-05:00"}}\n', encoding="utf-8")
                (run_dir / "saved" / "equity_bar.csv").write_text("symbol,timestamp,bar_open,bar_high,bar_low,bar_close,bar_volume,timeframe\nXLF,2016-01-04T09:30:00-05:00,1,2,1,2,100,30Min\n", encoding="utf-8")
                receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / month / "completion_receipt.json"
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(
                    json.dumps(
                        {
                            "runs": [
                                {
                                    "run_id": "run_001",
                                    "status": "succeeded",
                                    "row_counts": {"equity_bar": 1},
                                    "steps": {"clean": {"references": [f"storage/monthly_backfill/alpaca_bars/XLF/{month}/runs/run_001/cleaned/equity_bar.jsonl"]}},
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

            summary = materialize_layer_four_event_overlay_inputs(
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
            self.assertEqual(task_key["params"]["start"], "2016-01-01T00:00:00-05:00")
            self.assertEqual(task_key["params"]["end"], "2016-03-01T00:00:00-05:00")
            self.assertTrue(all(Path(run.task_key_path).exists() for run in summary.detector_runs))

    def test_dry_run_includes_reviewed_news_sec_macro_artifacts_in_source_task_key(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,layer_02_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_artifact(storage_root, "XLF", "2016-01")
            feed_root = trading_data_root / "storage" / "monthly_backfill"
            artifacts = {
                "alpaca_news": ("equity_news.csv", "id,timeline_headline,created_at,updated_at,symbols,summary,event_link_url\nn1,Headline,2016-01-04T10:00:00-05:00,2016-01-04T10:01:00-05:00,XLF,Summary,https://example.com/news\n"),
                "gdelt_news": ("gdelt_article.csv", "article_id,seen_at,source_domain,event_link_url,title,source_theme_tags,organizations,tone,impact_scope\ng1,2016-01-04T09:00:00-05:00,reuters.com,https://example.com/gdelt,Fed news,ECON,Federal Reserve,-1,market\n"),
                "sec_company_financials": ("sec_company_fact.csv", "cik,entity_name,taxonomy,tag,label,description,unit,fy,fp,form,filed,frame,end,value,accession_number,symbol\n1,Test Inc,us-gaap,Revenues,Revenue,,USD,2016,Q1,10-Q,2016-01-05,,2015-12-31,1,a1,XLF\n"),
                "trading_economics_calendar_web": ("trading_economics_calendar_event.csv", "event_time,country,event,source_event_type,reference,actual,previous,consensus,te_forecast,revised,importance,symbol,source_url\n2016-01-08T08:30:00-05:00,United States,Payrolls,Labour,Dec,200K,180K,190K,,,3,,https://tradingeconomics.com/united-states/calendar\n"),
            }
            for source_id, (filename, content) in artifacts.items():
                path = feed_root / source_id / "2016-01" / "runs" / "run_001" / "saved" / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            summary = materialize_layer_four_event_overlay_inputs(
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
            self.assertEqual(len(task_key["params"]["event_artifact_paths"]), 4)
            self.assertEqual(summary.provider_calls, 0)

    def test_write_blocks_when_required_event_feed_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,layer_02_sector_context\n", encoding="utf-8")
            _write_layer_two_bar_artifact(storage_root, "XLF", "2016-01")

            with self.assertRaisesRegex(TaskSystemError, "event-overlay coverage is incomplete"):
                materialize_layer_four_event_overlay_inputs(
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

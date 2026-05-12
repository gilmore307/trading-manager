from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.layer_four_event_overlay import materialize_layer_four_event_overlay_inputs


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


if __name__ == "__main__":
    unittest.main()

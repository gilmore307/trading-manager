from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.layer_three_target_state import (
    build_source_task_key,
    discover_layer_two_feed_artifacts,
    materialize_layer_three_target_state_inputs,
)


class LayerThreeTargetStateTests(unittest.TestCase):
    def test_discovers_successful_layer_two_feed_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,layer_02_sector_context\nSPY,layer_01_market_regime\n", encoding="utf-8")
            run_dir = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / "2016-01" / "runs" / "run_001"
            (run_dir / "cleaned").mkdir(parents=True)
            (run_dir / "cleaned" / "equity_bar.jsonl").write_text('{"symbol":"XLF","timestamp":"2016-01-04T09:30:00-05:00"}\n', encoding="utf-8")
            receipt = {
                "runs": [
                    {
                        "run_id": "run_001",
                        "status": "succeeded",
                        "row_counts": {"equity_bar": 1},
                        "steps": {"clean": {"references": ["storage/monthly_backfill/alpaca_bars/XLF/2016-01/runs/run_001/cleaned/equity_bar.jsonl"]}},
                    }
                ]
            }
            receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / "2016-01" / "completion_receipt.json"
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

            refs = discover_layer_two_feed_artifacts(
                start_month="2016-01",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
            )

            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0].symbol, "XLF")
            self.assertEqual(refs[0].row_count, 1)

    def test_builds_source_task_key_without_embedding_bar_rows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            bar_path = tmp / "XLF.jsonl"
            bar_path.write_text('{"symbol":"XLF","timestamp":"2016-01-04T09:30:00-05:00","bar_close":1}\n', encoding="utf-8")
            refs = [
                type("Ref", (), {"symbol": "XLF", "cleaned_bar_path": str(bar_path), "row_count": 1})(),
            ]

            task_key, task_key_path, candidate_path, merged_bar_path, bar_count = build_source_task_key(
                start_month="2016-01",
                end_month="2016-01",
                output_dir=tmp / "out",
                trading_data_output_root=tmp / "td-out",
                refs=refs,  # type: ignore[arg-type]
            )

            self.assertEqual(task_key["source"], "source_03_target_state")
            self.assertEqual(bar_count, 1)
            self.assertTrue(task_key_path.exists())
            self.assertTrue(candidate_path.exists())
            self.assertTrue(merged_bar_path.exists())
            self.assertIn("bar_rows_path", task_key["params"])
            self.assertNotIn("bar_rows", task_key["params"])

    def test_dry_run_writes_task_evidence_but_does_not_call_provider(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            trading_data_root = tmp / "trading-data"
            storage_root = trading_data_root / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,model_layer\nXLF,layer_02_sector_context\n", encoding="utf-8")
            run_dir = storage_root / "monthly_backfill" / "alpaca_bars" / "XLF" / "2016-01" / "runs" / "run_001"
            (run_dir / "cleaned").mkdir(parents=True)
            (run_dir / "cleaned" / "equity_bar.jsonl").write_text('{"symbol":"XLF","timestamp":"2016-01-04T09:30:00-05:00"}\n', encoding="utf-8")
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

            summary = materialize_layer_three_target_state_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=trading_data_root,
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

            self.assertEqual(summary.contract_type, "manager_layer_three_target_state_input_materialization")
            self.assertEqual(summary.feed_artifact_count, 1)
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertTrue(Path(summary.task_key_path).exists())


if __name__ == "__main__":
    unittest.main()

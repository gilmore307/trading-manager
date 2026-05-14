from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.historical_training import (
    LAYER_ONE_PHASE,
    LAYER_TWO_PHASE,
    prepare_layer_one_historical_training_batch,
    prepare_layer_two_historical_training_batch,
)


class HistoricalTrainingPreparationTests(unittest.TestCase):
    def _fake_data_src(self, tmp: Path) -> Path:
        src = tmp / "trading-data-src"
        package = src / "data_feed" / "01_feed_alpaca_bars"
        package.mkdir(parents=True)
        (src / "data_feed" / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "pipeline.py").write_text(
            textwrap.dedent(
                """
                from dataclasses import dataclass
                from pathlib import Path

                @dataclass(frozen=True)
                class Context:
                    run_dir: Path

                def build_context(task_key, run_id):
                    if task_key.get('feed') != '01_feed_alpaca_bars':
                        raise ValueError('wrong feed')
                    if not task_key.get('params', {}).get('symbol'):
                        raise ValueError('missing symbol')
                    return Context(Path(task_key['output_root']) / 'runs' / run_id)
                """
            ),
            encoding="utf-8",
        )
        return src

    def test_layer_one_batch_preparation_writes_payloads_and_validates_handoffs(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, payloads, validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp / "manager-storage",
                component_src_root=self._fake_data_src(tmp),
                write=True,
            )

        self.assertEqual(summary.phase, LAYER_ONE_PHASE)
        self.assertEqual(summary.model_layer, "layer_01_market_regime")
        self.assertEqual(summary.request_count, 19)
        self.assertEqual(summary.payload_count, 19)
        self.assertEqual(summary.handoff_validation_count, 19)
        self.assertIn("SPY", summary.symbols)
        self.assertTrue(all(row["target_component_id"] == "01_feed_alpaca_bars" for row in requests))
        self.assertTrue(all("/alpaca_bars/" in row["parameter_ref"] for row in requests))
        self.assertTrue(all(row["schema_ref"] == "manager_request_parameter_payload" for row in payloads))
        self.assertTrue(all(row["provider_calls"] == 0 for row in validations))
        self.assertFalse(summary.dispatch_performed)
        self.assertFalse(summary.model_activation_performed)
        self.assertFalse(summary.broker_execution_performed)

    def test_layer_two_batch_preparation_uses_sector_context_universe(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, payloads, validations = prepare_layer_two_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp / "manager-storage",
                component_src_root=self._fake_data_src(tmp),
                write=True,
            )

        self.assertEqual(summary.phase, LAYER_TWO_PHASE)
        self.assertEqual(summary.model_layer, "layer_02_sector_context")
        self.assertEqual(summary.request_count, 25)
        self.assertEqual(summary.payload_count, 25)
        self.assertEqual(summary.handoff_validation_count, 25)
        self.assertIn("XLK", summary.symbols)
        self.assertNotIn("SPY", summary.symbols)
        self.assertTrue(all(row["model_layer"] == "layer_02_sector_context" for row in requests))
        self.assertTrue(any(row["symbol"] == "XLB" and row["timeframe"] == "30Min" for row in requests))
        self.assertTrue(any(row["symbol"] == "AIQ" and row["timeframe"] == "1Day" for row in requests))
        self.assertTrue(all(row["provider_calls"] == 0 for row in validations))

    def test_default_preview_does_not_write_or_validate_handoff(self):
        summary, _requests, payloads, validations = prepare_layer_one_historical_training_batch(
            start_month="2016-01",
            end_month="2016-01",
            write=False,
        )

        self.assertEqual(summary.request_count, 19)
        self.assertEqual(summary.payload_count, 19)
        self.assertEqual(summary.handoff_validation_count, 0)
        self.assertFalse(summary.wrote_manager_sql)
        self.assertFalse(summary.wrote_payload_files)
        self.assertFalse(summary.persisted_input_bindings)
        self.assertEqual(len(payloads), 19)
        self.assertEqual(validations, [])


if __name__ == "__main__":
    unittest.main()

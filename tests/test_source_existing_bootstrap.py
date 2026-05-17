from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_state import workflow_state_path_for_month
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe
from trading_manager_tasks.source_existing_bootstrap import build_source_coverages_from_counts, run_source_existing_bootstrap


def _symbols(model_layer: str) -> tuple[str, ...]:
    return tuple(member.symbol.upper() for member in load_market_regime_universe(model_layers=(model_layer,)))


class SourceExistingBootstrapTests(unittest.TestCase):
    def test_builds_ready_stage_coverage_from_existing_source_rows(self) -> None:
        layer_one = _symbols(LAYER_ONE_MODEL_LAYER)
        layer_two = _symbols(LAYER_TWO_MODEL_LAYER)
        source_01 = {"2016-01": {symbol: 10 for symbol in (*layer_one, *layer_two)}}
        source_03 = {"2016-01": {"AAPL": 20}}
        source_09 = {"2016-01": 3}

        stage_coverages, event_coverages, warnings = build_source_coverages_from_counts(
            months=("2016-01",),
            source_01_counts=source_01,
            source_03_counts=source_03,
            source_09_counts=source_09,
            selected_target_symbol="AAPL",
        )

        self.assertFalse(warnings)
        self.assertEqual({coverage.stage_id for coverage in stage_coverages}, {
            "layer_01_market_regime.data_acquisition",
            "layer_02_sector_context.data_acquisition",
            "layer_03_target_state_vector.data_acquisition",
        })
        self.assertTrue(all(coverage.ready for coverage in stage_coverages))
        self.assertTrue(event_coverages[0].ready)
        self.assertEqual(event_coverages[0].row_count, 3)

    def test_write_bootstrap_seeds_acquisition_state_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            layer_one = _symbols(LAYER_ONE_MODEL_LAYER)
            layer_two = _symbols(LAYER_TWO_MODEL_LAYER)
            source_01 = {"2016-01": {symbol: 10 for symbol in (*layer_one, *layer_two)}}
            source_03 = {"2016-01": {"AAPL": 20}}
            summary = run_source_existing_bootstrap(
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
                storage_root=storage_root,
                source_01_counts=source_01,
                source_03_counts=source_03,
                source_09_counts={"2016-01": 0},
                write=True,
            )
            state_path = workflow_state_path_for_month("2016-01", root=storage_root / "runtime")
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            by_stage = {stage["stage_id"]: stage for stage in payload["stages"]}

        self.assertEqual(summary.provider_calls, 0)
        self.assertEqual(summary.bootstrapped_months, ("2016-01",))
        self.assertEqual(by_stage["layer_01_market_regime.data_acquisition"]["status"], "succeeded")
        self.assertEqual(by_stage["layer_02_sector_context.data_acquisition"]["status"], "succeeded")
        self.assertEqual(by_stage["layer_03_target_state_vector.data_acquisition"]["status"], "succeeded")
        self.assertEqual(by_stage["layer_01_market_regime.feature_generation"]["status"], "ready")
        self.assertFalse(payload["model_activation_performed"])
        self.assertFalse(payload["broker_execution_performed"])

    def test_partial_source_coverage_does_not_seed_workflow_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            source_01 = {"2016-01": {_symbols(LAYER_ONE_MODEL_LAYER)[0]: 10}}
            summary = run_source_existing_bootstrap(
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
                storage_root=storage_root,
                source_01_counts=source_01,
                source_03_counts={},
                source_09_counts={},
                write=True,
            )
            state_path = workflow_state_path_for_month("2016-01", root=storage_root / "runtime")

        self.assertEqual(summary.bootstrapped_months, ())
        self.assertFalse(state_path.exists())


if __name__ == "__main__":
    unittest.main()

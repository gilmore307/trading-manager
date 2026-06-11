from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.model_training_workflow import (
    BASE_STACK_LAYER_COUNT,
    FOUNDATION_CATCH_UP_LAYERS,
    LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS,
    MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER,
    MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID,
    MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER,
    MULTI_TARGET_SYMBOL_BLOCKER,
    build_model_training_workflow_plan,
)
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        path = root / "monthly_backfill" / "alpaca_bars" / member.symbol / month / "task_key.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")


def _write_target_feed_artifact(root: Path, *, symbol: str = "AAPL", month: str = "2016-01") -> None:
    receipt_path = root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": "run_001",
                        "status": "succeeded",
                        "outputs": ["trading_data.m03_target_state_vector_data_acquisition"],
                        "row_counts": {"equity_bar": 1},
                        "steps": {"save": {"references": ["trading_data.m03_target_state_vector_data_acquisition"]}},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


class ModelTrainingWorkflowTests(unittest.TestCase):
    def test_six_model_workflow_plan_shape_after_foundation_catch_up(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        self.assertEqual(plan.layer_count, BASE_STACK_LAYER_COUNT)
        self.assertEqual(
            [layer.layer_key for layer in plan.layers],
            [
                "model_01_background_context",
                "model_02_target_state",
                "model_03_event_state",
                "model_04_unified_decision",
                "model_05_option_expression",
                "model_06_residual_event_governance",
            ],
        )
        self.assertEqual(
            [layer.model_name for layer in plan.layers],
            [
                "BackgroundContextModel",
                "TargetStateModel",
                "EventStateModel",
                "UnifiedDecisionModel",
                "OptionExpressionModel",
                "ResidualEventGovernanceModel",
            ],
        )
        current_layer_keys = {layer.layer_key for layer in plan.layers}
        self.assertTrue(
            all(
                any(stage.stage_id.startswith(f"{layer_key}.") for layer_key in current_layer_keys)
                for layer in plan.layers
                for stage in layer.stages
            )
        )

    def test_foundation_catch_up_only_exposes_m01_and_m03_input_stages(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
            )

        self.assertTrue(plan.foundation_catch_up_only)
        self.assertEqual(plan.foundation_catch_up_layers, FOUNDATION_CATCH_UP_LAYERS)
        self.assertEqual([stage.stage_type for stage in plan.layers[0].stages], ["data_acquisition", "feature_generation"])
        self.assertEqual([stage.stage_type for stage in plan.layers[2].stages], ["data_acquisition"])
        for layer in (plan.layers[1], plan.layers[3], plan.layers[4], plan.layers[5]):
            self.assertEqual(layer.stages, ())

    def test_m01_acquisition_waits_for_task_key_preparation_then_auto_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            plan = build_model_training_workflow_plan(storage_root=root, trading_storage_root=root, start_month="2016-01", end_month="2016-01")
            acquisition = plan.layers[0].stages[0]
            self.assertEqual(acquisition.stage_id, "model_01_background_context.data_acquisition")
            self.assertEqual(acquisition.status, "blocked")
            self.assertIn("layer_01_task_key_preparation", acquisition.blockers)

            _write_task_keys(root, model_layer=LAYER_ONE_MODEL_LAYER)
            plan = build_model_training_workflow_plan(storage_root=root, trading_storage_root=root, start_month="2016-01", end_month="2016-01")
            acquisition = plan.layers[0].stages[0]

        self.assertEqual(plan.layer_one_task_key_count, LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS)
        self.assertEqual(acquisition.status, "ready")
        self.assertEqual(acquisition.blockers, ())
        self.assertTrue(acquisition.provider_calls_allowed)
        self.assertIn("scripts/tasks/dispatch_and_reconcile_provider_stage.py", acquisition.command)

    def test_m02_target_state_uses_target_local_materializer_without_provider_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            _write_target_feed_artifact(root, symbol="AAPL", month="2016-01")
            plan = build_model_training_workflow_plan(
                storage_root=root,
                trading_storage_root=root,
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stage = {stage.stage_id: stage for stage in plan.layers[1].stages}["model_02_target_state.data_acquisition"]
        self.assertEqual(stage.status, "ready")
        self.assertFalse(stage.provider_calls_allowed)
        self.assertTrue(stage.safe_without_provider_calls)
        self.assertIn("scripts/tasks/materialize_layer_three_target_state_inputs.py", stage.command)
        self.assertIn("--target-symbol", stage.command)

    def test_m02_target_state_blocks_without_target_local_feed_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stage = {stage.stage_id: stage for stage in plan.layers[1].stages}["model_02_target_state.data_acquisition"]
        self.assertEqual(stage.status, "blocked")
        self.assertEqual(stage.blockers, (MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER,))

    def test_m03_event_state_input_waits_for_m01_foundation(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stage = {stage.stage_id: stage for stage in plan.layers[2].stages}["model_03_event_state.data_acquisition"]
        self.assertEqual(stage.blockers, ("model_01_background_context.feature_or_input_ready",))
        self.assertIn("scripts/tasks/materialize_layer_four_event_observation_inputs.py", stage.command)

    def test_m05_option_expression_owns_option_source_when_options_apply(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stages = {stage.stage_id: stage for stage in plan.layers[4].stages}
        self.assertIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID, stages)
        self.assertIn("scripts/tasks/prepare_option_chain_source_acquisition.py", stages[MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID].command)
        self.assertIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER, stages["model_05_option_expression.feature_generation"].blockers)
        self.assertIn("model_05_option_expression.feature_or_input_ready", stages["model_05_option_expression.model_generation.train"].blockers)

    def test_m05_no_option_target_skips_option_source_but_keeps_model_generation(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            pool_path = tmp / "main" / "shared" / "equity_total_symbol_pool.csv"
            pool_path.parent.mkdir(parents=True, exist_ok=True)
            pool_path.write_text(
                "symbol,name,sector,optionable_underlying_status,pool_membership_status,pool_membership_reason\n"
                "XYZ,No Options Inc.,Industrials,confirmed_no_listed_options,inactive,inactive_confirmed_no_listed_options\n",
                encoding="utf-8",
            )
            plan = build_model_training_workflow_plan(
                storage_root=tmp,
                trading_storage_root=tmp,
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="XYZ",
                foundation_catch_up_only=False,
            )

        stage_ids = [stage.stage_id for stage in plan.layers[4].stages]
        self.assertNotIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID, stage_ids)
        self.assertEqual(stage_ids, [
            "model_05_option_expression.model_generation.train",
            "model_05_option_expression.model_generation.validation",
            "model_05_option_expression.model_generation.test",
        ])

    def test_model_generation_uses_chronological_train_validation_test_split_stages(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        split_stages = [stage for stage in plan.layers[3].stages if stage.stage_type == "model_generation"]
        self.assertEqual([stage.stage_id for stage in split_stages], [
            "model_04_unified_decision.model_generation.train",
            "model_04_unified_decision.model_generation.validation",
            "model_04_unified_decision.model_generation.test",
        ])
        self.assertEqual([stage.dataset_split["split_name"] for stage in split_stages], ["train", "validation", "test"])
        self.assertEqual([stage.dataset_split["split_months"] for stage in split_stages], [4, 1, 1])
        self.assertEqual(split_stages[1].blockers, ("model_04_unified_decision.model_generation.train_complete",))
        self.assertEqual(split_stages[2].blockers, ("model_04_unified_decision.model_generation.validation_complete",))

    def test_dataset_units_are_model_aware_and_target_visible(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="aapl",
                foundation_catch_up_only=False,
            )

        self.assertEqual(plan.selected_target_symbol, "AAPL")
        self.assertEqual(plan.layers[0].dataset_unit.unit_kind, "six_month_panel")
        self.assertFalse(plan.layers[0].dataset_unit.target_required)
        self.assertEqual(plan.layers[2].stages[0].dataset_unit.unit_kind, "event_observation_fold_panel")
        for layer in (plan.layers[1], plan.layers[3], plan.layers[4], plan.layers[5]):
            self.assertEqual(layer.dataset_unit.unit_kind, "target_symbol_six_month")
            self.assertEqual(layer.dataset_unit.target_symbol, "AAPL")
            self.assertTrue(layer.dataset_unit.target_required)

    def test_multi_target_symbol_requires_separate_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            with self.assertRaisesRegex(ValueError, MULTI_TARGET_SYMBOL_BLOCKER):
                build_model_training_workflow_plan(
                    storage_root=Path(raw_tmp),
                    trading_storage_root=Path(raw_tmp),
                    start_month="2016-01",
                    end_month="2016-06",
                    selected_target_symbol="AAPL,MSFT",
                    foundation_catch_up_only=False,
                )

    def test_m02_plus_model_generation_requires_selected_target_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                foundation_catch_up_only=False,
            )

        self.assertIsNone(plan.selected_target_symbol)
        m02_generation = next(stage for stage in plan.layers[1].stages if stage.stage_type == "model_generation")
        self.assertIn("selected_target_symbol_required", m02_generation.blockers)
        self.assertTrue(m02_generation.dataset_unit.target_required)


if __name__ == "__main__":
    unittest.main()

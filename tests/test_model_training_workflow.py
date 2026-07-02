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
    MODEL_GROUP_CUMULATIVE_CHECKPOINT_STAGE_ID,
    MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER,
    MULTI_TARGET_SYMBOL_BLOCKER,
    build_model_training_workflow_plan,
    model_script,
)
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_readiness=(model_layer,)):
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
                        "outputs": ["trading_data.model_03_target_state_vector_data_acquisition"],
                        "row_counts": {"equity_bar": 1},
                        "steps": {"save": {"references": ["trading_data.model_03_target_state_vector_data_acquisition"]}},
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
                end_month="2017-06",
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
            ],
        )
        current_layer_keys = {layer.layer_key for layer in plan.layers}
        self.assertTrue(
            all(
                any(stage.stage_id.startswith(f"{layer_key}.") for layer_key in current_layer_keys)
                or stage.stage_id == MODEL_GROUP_CUMULATIVE_CHECKPOINT_STAGE_ID
                for layer in plan.layers
                for stage in layer.stages
            )
        )

    def test_foundation_catch_up_only_exposes_m01_input_stages(self) -> None:
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
        for layer in (plan.layers[1], plan.layers[2], plan.layers[3], plan.layers[4]):
            self.assertEqual(layer.stages, ())

    def test_m01_acquisition_waits_for_task_key_preparation_then_auto_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            plan = build_model_training_workflow_plan(storage_root=root, trading_storage_root=root, start_month="2016-01", end_month="2016-01")
            acquisition = plan.layers[0].stages[0]
            self.assertEqual(acquisition.stage_id, "model_01_background_context.data_acquisition")
            self.assertEqual(acquisition.status, "blocked")
            self.assertIn("model_01_task_key_preparation", acquisition.blockers)

            _write_task_keys(root, model_layer=LAYER_ONE_MODEL_LAYER)
            plan = build_model_training_workflow_plan(storage_root=root, trading_storage_root=root, start_month="2016-01", end_month="2016-01")
            acquisition = plan.layers[0].stages[0]

        self.assertEqual(plan.layer_one_task_key_count, LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS)
        self.assertEqual(acquisition.status, "ready")
        self.assertEqual(acquisition.blockers, ())
        self.assertTrue(acquisition.provider_calls_allowed)
        self.assertIn("scripts/tasks/dispatch_and_reconcile_provider_stage.py", acquisition.command)

    def test_m02_target_state_waits_for_m01_even_with_target_local_feed(self) -> None:
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
        self.assertEqual(stage.status, "blocked")
        self.assertEqual(stage.blockers, ("upstream_model_01_model_generation_complete",))
        self.assertFalse(stage.provider_calls_allowed)
        self.assertTrue(stage.safe_without_provider_calls)
        self.assertIn("scripts/tasks/materialize_layer_three_target_state_inputs.py", stage.command)
        self.assertIn("--target-symbol", stage.command)

    def test_monthly_target_input_plan_does_not_emit_fold_model_generation_blockers(self) -> None:
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

        stages = [stage for layer in plan.layers for stage in layer.stages]
        self.assertNotIn("model_02_target_state.feature_generation", {stage.stage_id for stage in stages})
        self.assertNotIn("model_05_option_expression.feature_generation", {stage.stage_id for stage in stages})
        self.assertFalse(any(stage.stage_type == "model_generation" for stage in stages))
        self.assertFalse(any("rolling_fold_12_3_3_split_required" in stage.blockers for stage in stages))

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
        self.assertEqual(
            stage.blockers,
            ("upstream_model_01_model_generation_complete", MODEL_TWO_TARGET_LOCAL_FEED_ARTIFACTS_BLOCKER),
        )

    def test_m03_event_state_input_waits_for_upstream_models(self) -> None:
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
        self.assertEqual(
            stage.blockers,
            (
                "upstream_model_01_model_generation_complete",
                "upstream_model_02_model_generation_complete",
                "model_01_background_context.feature_or_input_ready",
            ),
        )
        self.assertIn("scripts/tasks/materialize_layer_four_event_observation_inputs.py", stage.command)

    def test_m05_option_expression_owns_option_source_when_options_apply(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2017-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stages = {stage.stage_id: stage for stage in plan.layers[4].stages}
        self.assertIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID, stages)
        self.assertIn("scripts/tasks/prepare_option_chain_source_acquisition.py", stages[MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID].command)
        self.assertIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER, stages["model_05_option_expression.feature_generation"].blockers)
        self.assertIn("--target-symbol", stages["model_05_option_expression.feature_generation"].command)
        self.assertIn("AAPL", stages["model_05_option_expression.feature_generation"].command)
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
                end_month="2017-06",
                selected_target_symbol="XYZ",
                foundation_catch_up_only=False,
            )

        stage_ids = [stage.stage_id for stage in plan.layers[4].stages]
        self.assertNotIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID, stage_ids)
        self.assertEqual(stage_ids, [
            "model_05_option_expression.model_generation.train",
            "model_05_option_expression.model_generation.validation",
            "model_05_option_expression.model_generation.test",
            MODEL_GROUP_CUMULATIVE_CHECKPOINT_STAGE_ID,
        ])

    def test_m05_crypto_target_skips_option_source_but_keeps_model_generation(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            universe_path = tmp / "main" / "shared" / "historical_candidate_universe.csv"
            universe_path.parent.mkdir(parents=True, exist_ok=True)
            universe_path.write_text(
                "symbol,asset_class,instrument_type,optionable_underlying_status,replay_candidate_status\n"
                "BTC,crypto_spot,spot_crypto_underlying,not_applicable,active\n",
                encoding="utf-8",
            )
            plan = build_model_training_workflow_plan(
                storage_root=tmp,
                trading_storage_root=tmp,
                start_month="2016-01",
                end_month="2017-06",
                selected_target_symbol="BTC",
                foundation_catch_up_only=False,
            )

        stage_ids = [stage.stage_id for stage in plan.layers[4].stages]
        self.assertNotIn(MODEL_FIVE_OPTION_CHAIN_SOURCE_STAGE_ID, stage_ids)
        self.assertEqual(stage_ids, [
            "model_05_option_expression.model_generation.train",
            "model_05_option_expression.model_generation.validation",
            "model_05_option_expression.model_generation.test",
            MODEL_GROUP_CUMULATIVE_CHECKPOINT_STAGE_ID,
        ])
        self.assertTrue(
            all(MODEL_FIVE_OPTION_CHAIN_SOURCE_BLOCKER not in stage.blockers for stage in plan.layers[4].stages)
        )

    def test_m06_does_not_expose_pre_replay_input_or_feature_stages(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2017-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stage_ids = {stage.stage_id for layer in plan.layers for stage in layer.stages}
        self.assertNotIn("model_06_residual_event_governance.data_acquisition", stage_ids)
        self.assertNotIn("model_06_residual_event_governance.feature_generation", stage_ids)
        self.assertFalse(any(stage_id.startswith("model_06_residual_event_governance.model_generation") for stage_id in stage_ids))

    def test_model_generation_uses_chronological_train_validation_test_split_stages(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2017-06",
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
        self.assertEqual([stage.dataset_split["split_months"] for stage in split_stages], [12, 3, 3])
        self.assertEqual(split_stages[1].blockers, ("model_04_unified_decision.model_generation.train_complete",))
        self.assertEqual(split_stages[2].blockers, ("model_04_unified_decision.model_generation.validation_complete",))

    def test_model_group_fold_includes_cumulative_checkpoint_stage(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp) / "storage" / "02_control_plane"
            plan = build_model_training_workflow_plan(
                storage_root=root,
                trading_storage_root=Path(raw_tmp),
                start_month="2017-01",
                end_month="2018-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stage = next(stage for layer in plan.layers for stage in layer.stages if stage.stage_id == MODEL_GROUP_CUMULATIVE_CHECKPOINT_STAGE_ID)
        self.assertEqual(stage.stage_type, "model_generation")
        self.assertEqual(stage.layer_key, "model_05_alpha_confidence")
        self.assertEqual(stage.blockers, ("model_05_option_expression.model_generation.test_complete",))
        self.assertTrue(any(token.endswith("train_model_05_alpha_confidence.py") for token in stage.command))
        self.assertIn("--parent-checkpoint-ref", stage.command)
        self.assertTrue(any(token.endswith("after_cost_alpha_model_2016-01_2017-06.json") for token in stage.command))
        self.assertTrue(any(token.endswith("after_cost_alpha_model_2017-01_2018-06.json") for token in stage.command))
        self.assertIn("--source-end", stage.command)
        self.assertIn("2018-01-01T00:00:00-05:00", stage.command)

    def test_dataset_units_are_model_aware_and_target_visible(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2017-06",
                selected_target_symbol="aapl",
                foundation_catch_up_only=False,
            )

        self.assertEqual(plan.selected_target_symbol, "AAPL")
        self.assertEqual(plan.layers[0].dataset_unit.unit_kind, "walk_forward_12_3_3_panel")
        self.assertFalse(plan.layers[0].dataset_unit.target_required)
        self.assertEqual(plan.layers[2].stages[0].dataset_unit.unit_kind, "event_observation_fold_panel")
        for layer in (plan.layers[1], plan.layers[3], plan.layers[4]):
            self.assertEqual(layer.dataset_unit.unit_kind, "target_symbol_walk_forward_12_3_3")
            self.assertEqual(layer.dataset_unit.target_symbol, "AAPL")
            self.assertTrue(layer.dataset_unit.target_required)

    def test_multi_target_symbol_requires_separate_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            with self.assertRaisesRegex(ValueError, MULTI_TARGET_SYMBOL_BLOCKER):
                build_model_training_workflow_plan(
                    storage_root=Path(raw_tmp),
                    trading_storage_root=Path(raw_tmp),
                    start_month="2016-01",
                    end_month="2017-06",
                    selected_target_symbol="AAPL,MSFT",
                    foundation_catch_up_only=False,
                )

    def test_m02_plus_model_generation_requires_selected_target_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                trading_storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2017-06",
                foundation_catch_up_only=False,
            )

        self.assertIsNone(plan.selected_target_symbol)
        m02_generation = next(stage for stage in plan.layers[1].stages if stage.stage_type == "model_generation")
        self.assertIn("selected_target_symbol_required", m02_generation.blockers)
        self.assertTrue(m02_generation.dataset_unit.target_required)

    def test_m02_model_generation_uses_database_backed_current_route(self) -> None:
        command = model_script(2, "target_state", "generate")

        self.assertIn("--from-database", command)
        self.assertIn("--source-start", command)
        self.assertIn("--source-end", command)

    def test_m06_model_generation_uses_database_backed_current_route(self) -> None:
        command = model_script(6, "residual_event_governance", "generate")

        self.assertIn("--from-database", command)
        self.assertIn("--source-start", command)
        self.assertIn("--source-end", command)


if __name__ == "__main__":
    unittest.main()

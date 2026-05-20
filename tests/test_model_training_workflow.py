from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_workflow import (
    BASE_STACK_LAYER_COUNT,
    FOLD_STACK_PROMOTION_BLOCKER,
    FOUNDATION_CATCH_UP_BLOCKER,
    MULTI_TARGET_SYMBOL_BLOCKER,
    MONTHLY_SUBSTRATE_LAYERS,
    POST_MODEL_GENERATION_REBUILD_BLOCKER,
    LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS,
    LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS,
    build_model_training_workflow_plan,
)
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        path = root / "monthly_backfill" / "alpaca_bars" / member.symbol / month / "task_key.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")


class ModelTrainingWorkflowTests(unittest.TestCase):
    def test_base_stack_plan_covers_all_nine_layers_and_stage_types_after_foundation_catch_up(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        self.assertEqual(plan.contract_type, "manager_model_training_workflow_plan")
        self.assertEqual(plan.layer_count, BASE_STACK_LAYER_COUNT)
        self.assertEqual([layer.layer for layer in plan.layers], list(range(1, 10)))
        for layer in plan.layers:
            expected_stage_types = [
                "data_acquisition",
                "feature_generation",
                "model_generation",
                "model_evaluation",
                "promotion_review",
                "maintenance",
            ]
            if layer.layer in {4, 5, 6, 7}:
                expected_stage_types = ["model_generation", "model_evaluation", "promotion_review", "maintenance"]
            self.assertEqual([stage.stage_type for stage in layer.stages], expected_stage_types)
            self.assertIn("model_", " ".join(layer.model_generate_command))
            self.assertIn("model_", " ".join(layer.model_evaluate_command))
            self.assertTrue(layer.progression_mode)
            self.assertTrue(layer.candidate_axis)
            self.assertTrue(layer.candidate_progression_policy)

    def test_foundation_catch_up_months_do_not_expose_model_or_promotion_review_stages(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
            )

        self.assertTrue(plan.foundation_catch_up_only)
        for layer in plan.layers:
            expected_stage_types = ["data_acquisition", "feature_generation"] if layer.layer in MONTHLY_SUBSTRATE_LAYERS else []
            self.assertEqual([stage.stage_type for stage in layer.stages], expected_stage_types)
            self.assertNotIn("model_generation", {stage.stage_type for stage in layer.stages})
            self.assertNotIn("model_evaluation", {stage.stage_type for stage in layer.stages})
            self.assertNotIn("promotion_review", {stage.stage_type for stage in layer.stages})

    def test_layer_one_acquisition_waits_for_task_key_preparation_then_auto_dispatch(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            plan = build_model_training_workflow_plan(storage_root=root, start_month="2016-01", end_month="2016-01")
            layer_one_acquisition = plan.layers[0].stages[0]
            self.assertEqual(layer_one_acquisition.status, "blocked")
            self.assertIn("layer_01_task_key_preparation", layer_one_acquisition.blockers)
            self.assertIsNone(layer_one_acquisition.approval_gate_required)

            _write_task_keys(root, model_layer=LAYER_ONE_MODEL_LAYER)
            plan = build_model_training_workflow_plan(storage_root=root, start_month="2016-01", end_month="2016-01")
            layer_one_acquisition = plan.layers[0].stages[0]
            self.assertEqual(plan.layer_one_task_key_count, LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS)
            self.assertEqual(layer_one_acquisition.status, "ready")
            self.assertIsNone(layer_one_acquisition.approval_gate_required)
            self.assertEqual(layer_one_acquisition.blockers, ())
            self.assertTrue(layer_one_acquisition.provider_calls_allowed)
            self.assertIn("scripts/tasks/dispatch_and_reconcile_provider_stage.py", layer_one_acquisition.command)
            self.assertIn("--reject-terminal-coverage", layer_one_acquisition.command)
            self.assertEqual(plan.next_stage, layer_one_acquisition)

    def test_layer_two_acquisition_waits_for_own_task_key_preparation_then_auto_dispatch(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            _write_task_keys(root, model_layer=LAYER_ONE_MODEL_LAYER)
            plan = build_model_training_workflow_plan(storage_root=root, start_month="2016-01", end_month="2016-01")
            layer_two_acquisition = plan.layers[1].stages[0]
            self.assertEqual(layer_two_acquisition.status, "blocked")
            self.assertIn("layer_02_task_key_preparation", layer_two_acquisition.blockers)
            self.assertIsNone(layer_two_acquisition.approval_gate_required)

            _write_task_keys(root, model_layer=LAYER_TWO_MODEL_LAYER)
            plan = build_model_training_workflow_plan(storage_root=root, start_month="2016-01", end_month="2016-01")
            layer_two_acquisition = plan.layers[1].stages[0]
            self.assertEqual(plan.layer_two_task_key_count, LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS)
            self.assertEqual(layer_two_acquisition.status, "ready")
            self.assertIsNone(layer_two_acquisition.approval_gate_required)
            self.assertEqual(layer_two_acquisition.blockers, ())
            self.assertTrue(layer_two_acquisition.provider_calls_allowed)
            self.assertIn("--model-layer", layer_two_acquisition.command)
            self.assertIn("layer_02_sector_context", layer_two_acquisition.command)
            self.assertIn("--skip-registered-failures", layer_two_acquisition.command)
            self.assertIn("--reject-terminal-coverage", layer_two_acquisition.command)
            self.assertIn("scripts/tasks/dispatch_and_reconcile_provider_stage.py", layer_two_acquisition.command)

    def test_layer_three_data_acquisition_uses_local_materializer_without_provider_dispatch(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        command = plan.layers[2].stages[0].command
        self.assertIn("scripts/tasks/materialize_layer_three_target_state_inputs.py", command)
        self.assertIn("--write", command)
        self.assertIsNone(plan.layers[2].stages[0].approval_gate_required)
        self.assertFalse(plan.layers[2].stages[0].provider_calls_allowed)
        self.assertTrue(plan.layers[2].stages[0].safe_without_provider_calls)

    def test_foundation_catch_up_omits_monthly_post_feature_model_stages(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
            )

        self.assertTrue(plan.foundation_catch_up_only)
        self.assertEqual(plan.foundation_catch_up_layers, MONTHLY_SUBSTRATE_LAYERS)
        self.assertEqual(plan.reusable_substrate_stage_types, ("data_acquisition", "feature_generation"))
        for layer in plan.layers:
            expected_stage_types = ["data_acquisition", "feature_generation"] if layer.layer in MONTHLY_SUBSTRATE_LAYERS else []
            self.assertEqual(
                [stage.stage_type for stage in layer.stages],
                expected_stage_types,
            )
        layer_three_acquisition = plan.layers[2].stages[0]
        self.assertNotIn(FOUNDATION_CATCH_UP_BLOCKER, layer_three_acquisition.blockers)

    def test_monthly_substrate_stages_stay_month_scoped_while_model_stages_are_fold_scoped(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            monthly_plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-07",
                end_month="2016-07",
                selected_target_symbol="AAPL",
            )
            fold_plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-07",
                end_month="2016-12",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        self.assertEqual(monthly_plan.layers[2].stages[0].command[monthly_plan.layers[2].stages[0].command.index("--end-month") + 1], "${END_MONTH}")
        self.assertEqual(monthly_plan.end_month, "2016-07")
        self.assertEqual(fold_plan.layers[2].stages[2].stage_type, "model_generation")
        self.assertEqual(fold_plan.end_month, "2016-12")
        self.assertIn("${END_MONTH_EXCLUSIVE_START_ET}", fold_plan.layers[2].stages[2].command)

    def test_post_foundation_model_stages_can_be_reenabled_after_catch_up_acceptance(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-01",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        self.assertFalse(plan.foundation_catch_up_only)
        self.assertNotIn(POST_MODEL_GENERATION_REBUILD_BLOCKER, plan.layers[0].stages[2].blockers)
        self.assertNotIn(FOUNDATION_CATCH_UP_BLOCKER, plan.layers[2].stages[0].blockers)

    def test_layer_one_and_two_model_evaluation_read_database_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        for index, script_name in ((0, "evaluate_model_01_market_regime.py"), (1, "evaluate_model_02_sector_context.py")):
            command = plan.layers[index].model_evaluate_command
            self.assertIn(script_name, " ".join(command))
            self.assertIn("--from-database", command)
            self.assertIn("--output-json", command)
            self.assertTrue(any("evaluation_summary_${START_MONTH}.json" in item for item in command))

    def test_layer_one_and_two_promotion_review_use_evaluation_summary_artifact(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        for index, script_name in ((0, "review_market_regime_promotion.py"), (1, "review_sector_context_promotion.py")):
            command = plan.layers[index].promotion_review_command
            self.assertIn(script_name, " ".join(command))
            self.assertIn("--evaluation-summary-json", command)
            self.assertIn("--local-fallback-review", command)

    def test_layer_one_feature_generation_materializes_feed_artifacts_first(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        command = plan.layers[0].feature_command

        self.assertIn("data_feature.feature_01_market_regime.from_feed_artifacts", command)
        self.assertIn("--month", command)
        self.assertIn("${START_MONTH}", command)

    def test_layer_two_feature_generation_materializes_features_and_source_two(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        stage = plan.layers[1].stages[1]
        command = plan.layers[1].feature_command

        self.assertIn("scripts/tasks/execute_layer_two_feature_generation.py", command)
        self.assertIn("--month", command)
        self.assertIn("${START_MONTH}", command)
        self.assertIn("--write", command)
        self.assertTrue(stage.provider_calls_allowed)
        self.assertFalse(stage.safe_without_provider_calls)

    def test_layer_eight_option_expression_feature_generation_uses_option_adapter_with_no_provider_skip_support(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        command = plan.layers[7].feature_command

        self.assertIn("scripts/tasks/execute_layer_eight_option_feature_generation.py", command)
        self.assertIn("--start-month", command)
        self.assertIn("${START_MONTH}", command)
        self.assertIn("--end-month", command)

    def test_layer_eight_option_expression_data_acquisition_runs_gate_review_without_provider_approval(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        stage = plan.layers[7].stages[0]

        self.assertIsNone(stage.approval_gate_required)
        self.assertIn("scripts/tasks/review_layer_eight_option_expression_gate.py", stage.command)
        self.assertIn("--write", stage.command)

    def test_layer_three_feature_generation_reads_month_scoped_source_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        command = plan.layers[2].feature_command

        self.assertIn("data_feature.feature_03_target_state_vector", command)
        self.assertIn("--source-start", command)
        self.assertIn("${START_MONTH_START_ET}", command)
        self.assertIn("--source-end", command)
        self.assertIn("${END_MONTH_EXCLUSIVE_START_ET}", command)

    def test_layer_three_model_commands_use_database_rows_and_evaluation_summary(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        layer = plan.layers[2]
        self.assertIn("--from-database", layer.model_generate_command)
        self.assertIn("--source-end", layer.model_generate_command)
        self.assertIn("--output", layer.model_generate_command)
        self.assertIn("--from-database", layer.model_evaluate_command)
        self.assertIn("--output-json", layer.model_evaluate_command)
        self.assertIn("--evaluation-summary-json", layer.promotion_review_command)
        self.assertIn("real_database_evaluation", layer.promotion_review_command)

    def test_alpha_confidence_has_no_event_risk_materializer_or_event_source_blocker(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        layer = plan.layers[4]
        self.assertEqual(layer.layer_key, "layer_05_alpha_confidence")
        self.assertEqual([stage.stage_type for stage in layer.stages], ["model_generation", "model_evaluation", "promotion_review", "maintenance"])
        self.assertNotIn("materialize_layer_nine_event_risk_governor_inputs.py", " ".join(token for stage in layer.stages for token in stage.command))
        self.assertIn("generate_model_05_alpha_confidence.py", " ".join(layer.model_generate_command))
        self.assertIn("--from-database", layer.model_generate_command)
        self.assertIn("--output-jsonl", layer.model_generate_command)
        self.assertIn("database_rows_fixture_outcomes", layer.model_evaluate_command)
        self.assertIn("--evaluation-summary-json", layer.promotion_review_command)

    def test_base_layers_four_to_nine_use_current_physical_model_rows_and_conservative_review(self):
        expected_scripts = {
            3: "generate_model_04_event_failure_risk.py",
            4: "generate_model_05_alpha_confidence.py",
            5: "generate_model_06_position_projection.py",
            6: "generate_model_07_underlying_action.py",
            7: "generate_model_08_option_expression.py",
            8: "generate_model_09_event_risk_governor.py",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        for index, script_name in expected_scripts.items():
            layer = plan.layers[index]
            self.assertIn(script_name, " ".join(layer.model_generate_command))
            self.assertIn("--from-database", layer.model_generate_command)
            self.assertIn("--output-jsonl", layer.model_generate_command)
            self.assertIn("--from-database", layer.model_evaluate_command)
            self.assertIn("database_rows_fixture_outcomes", layer.model_evaluate_command)
            self.assertIn("--evaluation-summary-json", layer.promotion_review_command)
            self.assertIn("--output-json", layer.promotion_review_command)

    def test_progression_modes_encode_background_panels_target_chain_and_base_guidance_gate(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        self.assertEqual(plan.layers[0].progression_mode, "background_panel_continuous")
        self.assertEqual(plan.layers[1].progression_mode, "sector_panel_continuous")
        self.assertTrue(all(plan.layers[index].progression_mode == "target_major_serial_chain" for index in range(2, 7)))
        self.assertEqual(plan.layers[7].progression_mode, "optional_trading_guidance_after_underlying_action")
        self.assertEqual(plan.layers[7].depends_on_layers, (7,))
        self.assertIn("crypto/direct-underlying-only routes do not require option refs", plan.layers[7].candidate_progression_policy)
        self.assertIn("upstream_layer_07_model_evaluation_complete", plan.layers[7].stages[0].blockers)
        self.assertEqual(plan.layers[8].progression_mode, "event_risk_governance_over_underlying_thesis")
        self.assertEqual(plan.layers[8].depends_on_layers, (7,))
        self.assertIn("Layer 8 guidance/expression context is optional", plan.layers[8].candidate_progression_policy)
        self.assertIn("upstream_layer_07_model_evaluation_complete", plan.layers[8].stages[0].blockers)

    def test_promotion_review_waits_for_full_fold_stack_evaluation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )

        for layer in plan.layers:
            promotion_stage = next(stage for stage in layer.stages if stage.stage_type == "promotion_review")
            self.assertEqual(promotion_stage.blockers, (FOLD_STACK_PROMOTION_BLOCKER,))
            self.assertIn("Layer 1-9 model evaluation", promotion_stage.description)
            self.assertIn("pinned Layer 1-9 bundle", promotion_stage.description)

    def test_layers_without_dedicated_data_features_do_not_create_nonexistent_tasks(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
        for layer_number in (4, 5, 6, 7):
            layer = plan.layers[layer_number - 1]
            stage_types = [stage.stage_type for stage in layer.stages]
            self.assertNotIn("data_acquisition", stage_types)
            self.assertNotIn("feature_generation", stage_types)
            self.assertEqual(stage_types, ["model_generation", "model_evaluation", "promotion_review", "maintenance"])
            self.assertIn("no-dedicated-trading-data-feature-stage", " ".join(layer.feature_command))

    def test_dataset_units_are_layer_aware_and_target_visible(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(
                storage_root=Path(raw_tmp),
                start_month="2016-01",
                end_month="2016-06",
                selected_target_symbol="aapl",
                foundation_catch_up_only=False,
            )

        self.assertEqual(plan.selected_target_symbol, "AAPL")
        self.assertEqual(plan.layers[0].dataset_unit.unit_kind, "six_month_panel")
        self.assertEqual(plan.layers[0].dataset_unit.unit_months, 6)
        self.assertIsNone(plan.layers[0].dataset_unit.target_symbol)
        self.assertFalse(plan.layers[0].dataset_unit.target_required)
        self.assertEqual(plan.layers[1].dataset_unit.unit_kind, "six_month_panel")
        for layer in plan.layers[2:]:
            self.assertEqual(layer.dataset_unit.unit_kind, "target_symbol_six_month")
            self.assertEqual(layer.dataset_unit.unit_months, 6)
            self.assertEqual(layer.dataset_unit.target_symbol, "AAPL")
            self.assertTrue(layer.dataset_unit.target_required)
            self.assertEqual(layer.stages[0].dataset_unit.target_symbol, "AAPL")

    def test_multi_target_symbol_requires_separate_workflows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            with self.assertRaisesRegex(ValueError, MULTI_TARGET_SYMBOL_BLOCKER):
                build_model_training_workflow_plan(
                    storage_root=Path(raw_tmp),
                    start_month="2016-01",
                    end_month="2016-06",
                    selected_target_symbol="AAPL,MSFT",
                    foundation_catch_up_only=False,
                )

    def test_later_layers_block_when_task_intro_omits_target_symbol(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-06")

        self.assertIsNone(plan.selected_target_symbol)
        layer_three_acquisition = plan.layers[2].stages[0]
        self.assertIn("selected_target_symbol_required", layer_three_acquisition.blockers)
        self.assertTrue(layer_three_acquisition.dataset_unit.target_required)
        self.assertIsNone(layer_three_acquisition.dataset_unit.target_symbol)


if __name__ == "__main__":
    unittest.main()

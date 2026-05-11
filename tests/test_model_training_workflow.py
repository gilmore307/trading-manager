from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_workflow import (
    FULL_LAYER_COUNT,
    LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS,
    LAYER_TWO_REQUIRED_ALPACA_BAR_REQUESTS,
    build_model_training_workflow_plan,
)
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        path = root / "monthly_backfill_v1" / "alpaca_bars" / member.symbol / month / "task_key.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")


class ModelTrainingWorkflowTests(unittest.TestCase):
    def test_full_stack_plan_covers_all_eight_layers_and_stage_types(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        self.assertEqual(plan.contract_type, "manager_model_training_workflow_plan_v1")
        self.assertEqual(plan.layer_count, FULL_LAYER_COUNT)
        self.assertEqual([layer.layer for layer in plan.layers], list(range(1, 9)))
        for layer in plan.layers:
            self.assertEqual(
                [stage.stage_type for stage in layer.stages],
                [
                    "data_acquisition",
                    "feature_generation",
                    "model_generation",
                    "model_evaluation",
                    "promotion_review_preparation",
                    "maintenance",
                ],
            )
            self.assertIn(f"model_{layer.layer:02d}_", " ".join(layer.model_generate_command))
            self.assertIn(f"model_{layer.layer:02d}_", " ".join(layer.model_evaluate_command))
            self.assertTrue(layer.progression_mode)
            self.assertTrue(layer.candidate_axis)
            self.assertTrue(layer.candidate_progression_policy)

    def test_layer_one_acquisition_waits_for_task_key_preparation_then_approval(self):
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
            self.assertEqual(layer_one_acquisition.approval_gate_required, "live_call_approval_v1")
            self.assertIn("live_call_approval_v1", layer_one_acquisition.blockers)
            self.assertEqual(plan.next_stage, layer_one_acquisition)

    def test_layer_two_acquisition_waits_for_own_task_key_preparation_then_approval(self):
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
            self.assertEqual(layer_two_acquisition.approval_gate_required, "live_call_approval_v1")
            self.assertIn("live_call_approval_v1", layer_two_acquisition.blockers)
            self.assertIn("--model-layer", layer_two_acquisition.command)
            self.assertIn("layer_02_sector_context", layer_two_acquisition.command)
            self.assertIn("--skip-registered-failures", layer_two_acquisition.command)
            self.assertNotIn("--execute-approved-provider-calls", layer_two_acquisition.command)

    def test_layer_three_data_acquisition_uses_local_materializer_without_provider_dispatch(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        command = plan.layers[2].stages[0].command
        self.assertIn("scripts/tasks/materialize_layer_three_target_state_inputs.py", command)
        self.assertIn("--write", command)
        self.assertIsNone(plan.layers[2].stages[0].approval_gate_required)
        self.assertFalse(plan.layers[2].stages[0].provider_calls_allowed)

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

    def test_layer_two_feature_generation_materializes_feed_artifacts_first(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        command = plan.layers[1].feature_command

        self.assertIn("data_feature.feature_02_sector_context.from_feed_artifacts", command)
        self.assertIn("--month", command)
        self.assertIn("${START_MONTH}", command)

    def test_layer_eight_feature_generation_uses_manager_adapter_with_no_provider_skip_support(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        command = plan.layers[7].feature_command

        self.assertIn("scripts/tasks/execute_layer_eight_option_feature_generation.py", command)
        self.assertIn("--start-month", command)
        self.assertIn("${START_MONTH}", command)
        self.assertIn("--end-month", command)

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

    def test_layer_four_uses_local_event_materializer_and_database_model_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        layer = plan.layers[3]
        self.assertIn("scripts/tasks/materialize_layer_four_event_overlay_inputs.py", layer.stages[0].command)
        self.assertIsNone(layer.stages[0].approval_gate_required)
        self.assertIn("--source-start", layer.feature_command)
        self.assertIn("--from-database", layer.model_generate_command)
        self.assertIn("--output-jsonl", layer.model_generate_command)
        self.assertIn("database_rows_fixture_outcomes", layer.model_evaluate_command)
        self.assertIn("--evaluation-summary-json", layer.promotion_review_command)

    def test_layers_five_to_eight_use_database_model_rows_and_conservative_review(self):
        expected_scripts = {
            4: "generate_model_05_alpha_confidence.py",
            5: "generate_model_06_position_projection.py",
            6: "generate_model_07_underlying_action.py",
            7: "generate_model_08_option_expression.py",
        }
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        for index, script_name in expected_scripts.items():
            layer = plan.layers[index]
            self.assertIn(script_name, " ".join(layer.model_generate_command))
            self.assertIn("--from-database", layer.model_generate_command)
            self.assertIn("--output-jsonl", layer.model_generate_command)
            self.assertIn("--from-database", layer.model_evaluate_command)
            self.assertIn("database_rows_fixture_outcomes", layer.model_evaluate_command)
            self.assertIn("--evaluation-summary-json", layer.promotion_review_command)
            self.assertIn("--output-json", layer.promotion_review_command)

    def test_progression_modes_encode_background_panels_target_chain_and_option_gate(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        self.assertEqual(plan.layers[0].progression_mode, "background_panel_continuous")
        self.assertEqual(plan.layers[1].progression_mode, "sector_panel_continuous")
        self.assertTrue(all(plan.layers[index].progression_mode == "target_major_serial_chain" for index in range(2, 7)))
        self.assertEqual(plan.layers[7].progression_mode, "option_expression_after_target_chain_complete")
        self.assertEqual(plan.layers[7].depends_on_layers, (1, 2, 3, 4, 5, 6, 7))
        self.assertIn("near-to-far", plan.layers[7].candidate_progression_policy)
        self.assertIn("three listed strike levels", plan.layers[7].candidate_progression_policy)
        self.assertIn("without prefiltering", plan.layers[7].candidate_progression_policy)
        self.assertIn("single-leg", plan.layers[7].candidate_progression_policy)
        self.assertIn("active_target_chain_complete", plan.layers[7].stages[0].blockers)

    def test_layers_without_dedicated_data_features_are_explicit_not_applicable(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")
        for layer_number in (5, 6, 7):
            layer = plan.layers[layer_number - 1]
            self.assertEqual(layer.stages[0].status, "not_applicable")
            self.assertEqual(layer.stages[1].status, "not_applicable")
            self.assertIn("no-dedicated-trading-data-feature-stage", " ".join(layer.feature_command))


if __name__ == "__main__":
    unittest.main()

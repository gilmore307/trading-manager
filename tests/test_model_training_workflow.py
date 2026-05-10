from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_workflow import (
    FULL_LAYER_COUNT,
    LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS,
    build_model_training_workflow_plan,
)


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

            for index in range(LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS):
                path = root / "monthly_backfill_v1" / "alpaca_bars" / f"SYM{index:02d}" / "2016-01" / "task_key.json"
                path.parent.mkdir(parents=True)
                path.write_text("{}\n", encoding="utf-8")
            plan = build_model_training_workflow_plan(storage_root=root, start_month="2016-01", end_month="2016-01")
            layer_one_acquisition = plan.layers[0].stages[0]
            self.assertEqual(plan.layer_one_task_key_count, LAYER_ONE_REQUIRED_ALPACA_BAR_REQUESTS)
            self.assertEqual(layer_one_acquisition.approval_gate_required, "live_call_approval_v1")
            self.assertIn("live_call_approval_v1", layer_one_acquisition.blockers)
            self.assertEqual(plan.next_stage, layer_one_acquisition)

    def test_progression_modes_encode_background_panels_target_chain_and_option_gate(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")

        self.assertEqual(plan.layers[0].progression_mode, "background_panel_continuous")
        self.assertEqual(plan.layers[1].progression_mode, "sector_panel_continuous")
        self.assertTrue(all(plan.layers[index].progression_mode == "target_major_serial_chain" for index in range(2, 7)))
        self.assertEqual(plan.layers[7].progression_mode, "option_expression_after_target_chain_complete")
        self.assertEqual(plan.layers[7].depends_on_layers, (1, 2, 3, 4, 5, 6, 7))
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

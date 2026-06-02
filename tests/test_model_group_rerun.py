from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from trading_manager_tasks.model_group_rerun import execute_model_group_rerun_reset
from trading_manager_tasks.model_training_state import advance_workflow_state
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan


class ModelGroupRerunTests(unittest.TestCase):
    def test_dry_run_builds_schema_valid_plan_without_mutating_state(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-07_2016-12.json"
            plan = build_model_training_workflow_plan(
                start_month="2016-07",
                end_month="2016-12",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            completed = [
                stage.stage_id
                for layer in plan.layers
                for stage in layer.stages
                if stage.layer <= 4
            ]
            advance_workflow_state(
                start_month="2016-07",
                end_month="2016-12",
                storage_root=storage_root,
                state_path=state_path,
                completed_stage_ids=completed,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )
            before = state_path.read_text(encoding="utf-8")

            result = execute_model_group_rerun_reset(
                storage_root=storage_root,
                start_month="2016-07",
                end_month="2016-12",
                target_symbol="AAPL",
                layer_id=3,
                stage="data_acquisition",
                reason="Layer 3 target-local acquisition route changed.",
                write=False,
            )
            schema = json.loads(Path("schemas/model_group_rerun_plan.schema.json").read_text(encoding="utf-8"))
            errors = sorted(Draft202012Validator(schema).iter_errors(result.plan), key=lambda error: list(error.path))
            after = state_path.read_text(encoding="utf-8")

        self.assertEqual(errors, [])
        self.assertFalse(result.write_performed)
        self.assertEqual(before, after)
        self.assertEqual(result.cutpoint_stage_id, "layer_03_target_state_vector.data_acquisition")
        self.assertFalse(result.source_data_delete_required)
        protected_refs = {row["ref"] for row in result.plan["protected_set"]}
        self.assertIn("storage://01_source_data/monthly_backfill/trading_economics_calendar_web/", protected_refs)

    def test_execute_resets_cutpoint_and_downstream_state_for_scheduler_reentry(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-07_2016-12.json"
            plan = build_model_training_workflow_plan(
                start_month="2016-07",
                end_month="2016-12",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            completed = [
                stage.stage_id
                for layer in plan.layers
                for stage in layer.stages
                if stage.layer <= 4
            ]
            advance_workflow_state(
                start_month="2016-07",
                end_month="2016-12",
                storage_root=storage_root,
                state_path=state_path,
                completed_stage_ids=completed,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )

            result = execute_model_group_rerun_reset(
                storage_root=storage_root,
                start_month="2016-07",
                end_month="2016-12",
                target_symbol="AAPL",
                layer_id=3,
                stage="data_acquisition",
                reason="Layer 3 target-local acquisition route changed.",
                write=True,
            )
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            by_stage = {stage["stage_id"]: stage for stage in payload["stages"]}

        self.assertTrue(result.write_performed)
        self.assertEqual(by_stage["layer_01_market_regime.data_acquisition"]["status"], "succeeded")
        self.assertEqual(by_stage["layer_02_sector_context.data_acquisition"]["status"], "succeeded")
        self.assertEqual(by_stage["layer_03_target_state_vector.data_acquisition"]["status"], "blocked")
        self.assertEqual(
            by_stage["layer_03_target_state_vector.data_acquisition"]["last_reason"],
            "waiting for layer_03_target_local_feed_artifacts_ready",
        )
        self.assertEqual(by_stage["layer_03_target_state_vector.feature_generation"]["status"], "blocked")
        self.assertEqual(by_stage["layer_04_event_failure_risk.model_generation.train"]["status"], "blocked")
        self.assertEqual(by_stage["layer_03_target_state_vector.data_acquisition"].get("artifact_refs") or [], [])
        self.assertEqual(
            by_stage["layer_03_target_state_vector.feature_generation"]["last_reason"],
            "waiting for layer_03_target_state_vector.data_acquisition_complete",
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.fold_cleanup import build_fold_cleanup_plan
from trading_manager_tasks.model_training_state import advance_workflow_state
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.scheduler_daemon import model_worker_fold_state_path


class FoldCleanupTests(unittest.TestCase):
    def _write_fold_state(self, *, storage_root: Path, completed_stage_ids: list[str]) -> Path:
        state_path = model_worker_fold_state_path("2016-01", "2016-06", root=storage_root / "runtime")
        advance_workflow_state(
            start_month="2016-01",
            end_month="2016-06",
            storage_root=storage_root,
            state_path=state_path,
            completed_stage_ids=completed_stage_ids,
            selected_target_symbol="AAPL",
            foundation_catch_up_only=False,
            write=True,
        )
        return state_path

    def test_complete_fold_requires_one_logical_backup_before_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage"
            plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            state_path = self._write_fold_state(storage_root=storage_root, completed_stage_ids=stage_ids)

            cleanup = build_fold_cleanup_plan(
                state_path=state_path,
                generated_at_utc="2026-05-19T12:00:00Z",
            )

        self.assertTrue(cleanup.cleanup_ready)
        self.assertEqual(cleanup.cleanup_granularity, "fold_all_models_all_tasks_once")
        self.assertEqual(cleanup.completed_model_layers, tuple(range(1, 10)))
        self.assertEqual(cleanup.required_model_stage_count, 36)
        self.assertEqual(cleanup.completed_model_stage_count, 36)
        self.assertTrue(cleanup.logical_backup_required)
        self.assertEqual(cleanup.logical_backup_plan["backup_mode"], "logical_pg_dump_custom")
        self.assertEqual(cleanup.logical_backup_plan["backup_command"][0], "pg_dump")
        self.assertIn("-Fc", cleanup.logical_backup_plan["backup_command"])
        self.assertIn("$DATABASE_URL", cleanup.logical_backup_plan["backup_command"])
        self.assertEqual(cleanup.logical_backup_plan["backup_must_complete_before_cleanup"], True)
        self.assertEqual(cleanup.logical_backup_plan["globals_backup_command"][0], "pg_dumpall")
        self.assertIn("fold_2016-01_2016-06", cleanup.logical_backup_plan["output_path"])
        self.assertEqual(cleanup.cleanup_action_status, "not_performed_plan_only")
        self.assertFalse(cleanup.storage_lifecycle_mutation_performed)
        self.assertFalse(cleanup.database_mutation_performed)

    def test_incomplete_fold_blocks_cleanup_and_backup_gate_progression(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage"
            state_path = self._write_fold_state(
                storage_root=storage_root,
                completed_stage_ids=["layer_01_market_regime.model_generation"],
            )

            cleanup = build_fold_cleanup_plan(
                state_path=state_path,
                generated_at_utc="2026-05-19T12:00:00Z",
            )

        self.assertFalse(cleanup.cleanup_ready)
        self.assertIn("fold_has_open_or_failed_stages", cleanup.blocked_reasons)
        self.assertIn("not_all_model_layers_completed", cleanup.blocked_reasons)
        self.assertEqual(cleanup.required_model_stage_count, 36)
        self.assertLess(cleanup.completed_model_stage_count, cleanup.required_model_stage_count)
        self.assertIn("layer_02_sector_context.model_generation", cleanup.open_stage_ids)
        self.assertTrue(cleanup.logical_backup_required)
        self.assertEqual(cleanup.cleanup_action_status, "not_performed_plan_only")


if __name__ == "__main__":
    unittest.main()

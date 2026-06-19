from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from trading_manager_tasks.model_group_rerun import execute_model_group_rerun_reset, write_reset_batch_receipt
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
                layer_id=2,
                stage="data_acquisition",
                reason="M02 target-local acquisition route changed.",
                write=False,
            )
            schema = json.loads(Path("schemas/model_group_rerun_plan.schema.json").read_text(encoding="utf-8"))
            errors = sorted(Draft202012Validator(schema).iter_errors(result.plan), key=lambda error: list(error.path))
            after = state_path.read_text(encoding="utf-8")

        self.assertEqual(errors, [])
        self.assertFalse(result.write_performed)
        self.assertFalse(result.reset_receipt_written)
        self.assertIsNone(result.reset_receipt_path)
        self.assertEqual(before, after)
        self.assertEqual(result.cutpoint_stage_id, "model_02_target_state.data_acquisition")
        self.assertFalse(result.source_data_delete_required)
        protected_refs = {row["ref"] for row in result.plan["protected_set"]}
        self.assertIn("storage://01_source_data/monthly_backfill/trading_economics_calendar_web/", protected_refs)
        retained_refs = {row["ref"] for row in result.plan["retained_set"]}
        self.assertIn("storage://01_source_data/monthly_backfill/trading_economics_calendar_web/", retained_refs)
        root_classes = {row["root_class"] for row in result.plan["controlled_artifact_roots"]}
        self.assertIn("rerun_reset_receipts", root_classes)
        self.assertIn("protected_source_data", root_classes)
        lifecycle_request = result.plan["storage_lifecycle_request"]
        self.assertEqual(lifecycle_request["contract_type"], "storage_lifecycle_request")
        self.assertEqual(lifecycle_request["request_origin"], "model_group_rerun_plan")
        self.assertEqual(lifecycle_request["origin_rerun_id"], result.rerun_id)
        self.assertFalse(lifecycle_request["mutation_allowed_by_request"])
        self.assertFalse(lifecycle_request["storage_lifecycle_mutation_performed"])
        self.assertTrue(lifecycle_request["requires_storage_lifecycle_review"])
        self.assertTrue(lifecycle_request["requires_artifact_index"])
        self.assertTrue(lifecycle_request["requires_protected_set_clearance"])
        self.assertTrue(lifecycle_request["requires_quarantine_recheck_before_delete"])
        self.assertEqual(
            set(lifecycle_request["protected_refs"]),
            protected_refs,
        )
        self.assertEqual(
            set(lifecycle_request["retained_refs"]),
            retained_refs,
        )

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
                layer_id=2,
                stage="data_acquisition",
                reason="M02 target-local acquisition route changed.",
                write=True,
            )
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            by_stage = {stage["stage_id"]: stage for stage in payload["stages"]}
            receipt_payload = json.loads(Path(result.reset_receipt_path or "").read_text(encoding="utf-8"))

        self.assertTrue(result.write_performed)
        self.assertTrue(result.reset_receipt_written)
        self.assertIsNotNone(result.reset_receipt_path)
        self.assertEqual(receipt_payload["contract_type"], "manager_model_group_rerun_reset_receipt")
        self.assertEqual(receipt_payload["rerun_id"], result.rerun_id)
        self.assertEqual(receipt_payload["cutpoint_stage_id"], "model_02_target_state.data_acquisition")
        receipt_root_classes = {row["root_class"] for row in receipt_payload["controlled_artifact_roots"]}
        self.assertIn("rerun_reset_receipts", receipt_root_classes)
        self.assertIn("protected_source_data", receipt_root_classes)
        self.assertEqual(by_stage["model_01_background_context.data_acquisition"]["status"], "succeeded")
        self.assertEqual(by_stage["model_02_target_state.data_acquisition"]["status"], "blocked")
        self.assertEqual(
            by_stage["model_02_target_state.data_acquisition"]["last_reason"],
            "waiting for model_02_target_local_feed_artifacts_ready",
        )
        self.assertEqual(by_stage["model_02_target_state.feature_generation"]["status"], "blocked")
        self.assertEqual(by_stage["model_04_unified_decision.model_generation.train"]["status"], "blocked")
        self.assertEqual(by_stage["model_02_target_state.data_acquisition"].get("artifact_refs") or [], [])
        self.assertEqual(
            by_stage["model_02_target_state.feature_generation"]["last_reason"],
            "waiting for model_02_target_state.data_acquisition_complete",
        )

    def test_execute_resets_model_training_cutpoint(self):
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
                if stage.layer <= 5
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
                layer_id=5,
                stage="model_generation",
                reason="M05 option-expression generation environment changed.",
                write=True,
            )
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            by_stage = {stage["stage_id"]: stage for stage in payload["stages"]}

        self.assertEqual(result.cutpoint_stage_id, "model_05_option_expression.model_generation.train")
        self.assertEqual(by_stage["model_04_unified_decision.model_generation.test"]["status"], "succeeded")
        self.assertEqual(by_stage["model_05_option_expression.feature_generation"]["status"], "succeeded")
        self.assertEqual(by_stage["model_05_option_expression.model_generation.train"]["status"], "ready")
        self.assertEqual(by_stage["model_06_residual_event_governance.model_generation.train"]["status"], "blocked")

    def test_batch_receipt_summarizes_per_state_reset_receipts(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            receipt_paths = []
            for month in ("2016-07", "2016-08"):
                state_path = storage_root / "runtime" / f"model_training_workflow_state_{month}.json"
                plan = build_model_training_workflow_plan(
                    start_month=month,
                    end_month=month,
                    storage_root=storage_root,
                    selected_target_symbol=None,
                    foundation_catch_up_only=False,
                )
                completed = [
                    stage.stage_id
                    for layer in plan.layers
                    for stage in layer.stages
                    if stage.layer <= 3
                ]
                advance_workflow_state(
                    start_month=month,
                    end_month=month,
                    storage_root=storage_root,
                    state_path=state_path,
                    completed_stage_ids=completed,
                    selected_target_symbol=None,
                    foundation_catch_up_only=False,
                    write=True,
                )
                result = execute_model_group_rerun_reset(
                    storage_root=storage_root,
                    state_path=state_path,
                    start_month=month,
                    end_month=month,
                    target_symbol=None,
                    layer_id=1,
                    stage="data_acquisition",
                    reason="M01 source contract changed.",
                    write=True,
                )
                receipt_paths.append(Path(result.reset_receipt_path or ""))

            batch_path = write_reset_batch_receipt(
                storage_root=storage_root,
                batch_id="layer2_reset_test",
                receipt_paths=receipt_paths,
                reason="M02 contract changed.",
                created_at_utc="2026-06-05T08:00:00+00:00",
            )
            batch_payload = json.loads(Path(batch_path).read_text(encoding="utf-8"))

        self.assertEqual(batch_payload["contract_type"], "manager_model_group_rerun_reset_batch_receipt")
        self.assertEqual(batch_payload["receipt_count"], 2)
        self.assertEqual(batch_payload["state_count"], 2)
        self.assertEqual(batch_payload["scope"]["start_month"], "2016-07")
        self.assertEqual(batch_payload["scope"]["end_month"], "2016-08")
        self.assertEqual(batch_payload["scope"]["cutpoint_stage_ids"], ["model_01_background_context.data_acquisition"])
        self.assertFalse(batch_payload["source_data_delete_required"])
        self.assertIn("operator_entrypoint", batch_payload)
        self.assertEqual(len(batch_payload["reset_receipts"]), 2)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.model_training_state import (
    advance_workflow_state,
    first_blocked_stage,
    initial_workflow_state,
    mark_stage_started,
    mark_stage_succeeded,
    next_ready_or_blocked_stage,
    write_workflow_state,
    workflow_state_path_for_month,
)
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        task_key = root / "monthly_backfill" / "alpaca_bars" / member.symbol / month / "task_key.json"
        task_key.parent.mkdir(parents=True, exist_ok=True)
        task_key.write_text("{}\n", encoding="utf-8")


class ModelTrainingWorkflowStateTests(unittest.TestCase):
    def test_initial_state_blocks_until_layer_one_task_keys_exist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")
            state = initial_workflow_state(plan)
        stage = state.stages[0]
        self.assertEqual(state.contract_type, "manager_model_training_workflow_state")
        self.assertEqual(stage.stage_id, "model_01_background_context.data_acquisition")
        self.assertEqual(stage.status, "blocked")
        self.assertIn("layer_01_task_key_preparation", stage.last_reason or "")
        self.assertIsNone(next_ready_or_blocked_stage(state))
        self.assertEqual(first_blocked_stage(state).stage_id, "model_01_background_context.data_acquisition")

    def test_approval_then_receipt_progresses_layer_one_to_feature_generation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)

            state_path = tmp / "workflow_state.json"
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=state_path,
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                write=True,
            )
            next_stage = next_ready_or_blocked_stage(state)
            self.assertIsNotNone(next_stage)
            self.assertEqual(next_stage.stage_id, "model_01_background_context.data_acquisition")
            self.assertEqual(next_stage.status, "ready")

            receipt = tmp / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "manager_stage_id": "model_01_background_context.data_acquisition",
                        "run_id": "run_layer_01_acq",
                        "status": "succeeded",
                        "started_at": "2026-05-10T00:00:00+00:00",
                        "completed_at": "2026-05-10T00:01:00+00:00",
                        "output_refs": ["storage://bars/layer1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=state_path,
                receipt_paths=[receipt],
                write=True,
            )
            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stage_by_id["model_01_background_context.data_acquisition"].status, "succeeded")
            self.assertIn("storage://bars/layer1", stage_by_id["model_01_background_context.data_acquisition"].artifact_refs)
            self.assertEqual(stage_by_id["model_01_background_context.feature_generation"].status, "ready")
            self.assertEqual(next_ready_or_blocked_stage(state).stage_id, "model_01_background_context.feature_generation")

    def test_stage_receipts_attach_partial_evidence_without_unlocking_downstream(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)
            receipts = []
            for index in range(3):
                receipt = tmp / f"receipt_{index}.json"
                receipt.write_text(
                    json.dumps(
                        {
                            "task_id": f"mgrreq_{index}",
                            "feed": "01_feed_alpaca_bars",
                            "runs": [
                                {
                                    "run_id": f"run_{index}",
                                    "status": "succeeded",
                                    "started_at": "2026-05-10T00:00:00+00:00",
                                    "completed_at": "2026-05-10T00:01:00+00:00",
                                    "outputs": [f"storage://bars/{index}.csv"],
                                }
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                receipts.append(receipt)

            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=tmp / "workflow_state.json",
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                stage_receipts=[("model_01_background_context.data_acquisition", receipt) for receipt in receipts],
                write=False,
            )

            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            acquisition = stage_by_id["model_01_background_context.data_acquisition"]
            self.assertEqual(acquisition.status, "ready")
            self.assertEqual(len(acquisition.receipt_refs), 3)
            self.assertIn("partial component receipt coverage 3/19", acquisition.last_reason)
            self.assertEqual(stage_by_id["model_01_background_context.feature_generation"].status, "blocked")
            self.assertIn("model_01_background_context.data_acquisition_complete", stage_by_id["model_01_background_context.feature_generation"].last_reason)

    def test_stage_receipts_complete_stage_after_expected_coverage(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            receipts = []
            for index in range(2):
                receipt = tmp / f"receipt_{index}.json"
                receipt.write_text(
                    json.dumps(
                        {
                            "runs": [
                                {
                                    "run_id": f"run_{index}",
                                    "status": "succeeded",
                                    "started_at": "2026-05-10T00:00:00+00:00",
                                    "completed_at": "2026-05-10T00:01:00+00:00",
                                    "outputs": [f"storage://bars/{index}.csv"],
                                }
                            ]
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                receipts.append(receipt)

            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                state_path=tmp / "workflow_state.json",
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                stage_receipts=[("model_01_background_context.data_acquisition", receipt) for receipt in receipts],
                expected_receipt_counts={"model_01_background_context.data_acquisition": 2},
                write=False,
            )

            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            acquisition = stage_by_id["model_01_background_context.data_acquisition"]
            self.assertEqual(acquisition.status, "succeeded")
            self.assertEqual(len(acquisition.receipt_refs), 2)
            self.assertIn("storage://bars/0.csv", acquisition.artifact_refs)
            self.assertEqual(stage_by_id["model_01_background_context.feature_generation"].status, "ready")

    def test_lifecycle_timestamps_are_recorded_on_creation_start_and_terminal_transition(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=tmp / "workflow_state.json",
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                write=False,
            )
            stage_id = "model_01_background_context.data_acquisition"
            stage = {stage.stage_id: stage for stage in state.stages}[stage_id]
            self.assertIsNotNone(stage.created_at_utc)
            self.assertIsNotNone(stage.status_updated_at_utc)
            self.assertIsNone(stage.started_at_utc)
            self.assertIsNone(stage.ended_at_utc)

            state = mark_stage_started(state, stage_id=stage_id, started_at="2026-05-13T10:00:00+00:00")
            state = mark_stage_succeeded(state, stage_id=stage_id, ended_at="2026-05-13T10:05:00+00:00")
            stage = {stage.stage_id: stage for stage in state.stages}[stage_id]
            self.assertEqual(stage.started_at_utc, "2026-05-13T10:00:00+00:00")
            self.assertEqual(stage.ended_at_utc, "2026-05-13T10:05:00+00:00")
            self.assertEqual(stage.status_updated_at_utc, "2026-05-13T10:05:00+00:00")

    def test_ready_refresh_clears_legacy_started_timestamp_unless_stage_is_running(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)
            state_path = tmp / "workflow_state.json"
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=state_path,
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                write=False,
            )
            stage = {stage.stage_id: stage for stage in state.stages}["model_01_background_context.data_acquisition"]
            legacy_payload = state.summary_row()
            legacy_payload["stages"][0]["started_at_utc"] = "2026-05-13T10:00:00+00:00"
            state_path.write_text(json.dumps(legacy_payload) + "\n", encoding="utf-8")

            refreshed = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=state_path,
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                write=False,
            )

            refreshed_stage = {item.stage_id: item for item in refreshed.stages}[stage.stage_id]
            self.assertEqual(refreshed_stage.status, "ready")
            self.assertIsNone(refreshed_stage.started_at_utc)

            running_payload = refreshed.summary_row()
            running_payload["stages"][0]["started_at_utc"] = "2026-05-13T10:00:00+00:00"
            running_payload["stages"][0]["last_reason"] = "stage execution started by manager stage executor"
            state_path.write_text(json.dumps(running_payload) + "\n", encoding="utf-8")

            running = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=state_path,
                write=False,
            )
            running_stage = {item.stage_id: item for item in running.stages}[stage.stage_id]
            self.assertEqual(running_stage.started_at_utc, "2026-05-13T10:00:00+00:00")

    def test_terminal_stage_without_lifecycle_is_not_backfilled_when_reobserved(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "updated_utc": "2026-05-12T00:00:00+00:00",
                        "stages": [
                            {
                                "stage_id": "model_01_background_context.data_acquisition",
                                "status": "succeeded",
                                "updated_utc": "2026-05-12T00:00:00+00:00",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=["model_01_background_context.data_acquisition"],
                write=False,
            )

            stage = {stage.stage_id: stage for stage in state.stages}["model_01_background_context.data_acquisition"]
            self.assertEqual(stage.status, "succeeded")
            self.assertIsNone(stage.created_at_utc)
            self.assertIsNone(stage.started_at_utc)
            self.assertIsNone(stage.ended_at_utc)
            self.assertIsNone(stage.status_updated_at_utc)

    def test_default_checkpoint_path_is_month_scoped(self):
        path = workflow_state_path_for_month("2016-02", root=Path("02_control_plane/runtime"))

        self.assertEqual(path, Path("02_control_plane/runtime/model_training_workflow_state_2016-02.json"))

    def test_advance_default_checkpoint_path_follows_storage_root(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state = advance_workflow_state(
                start_month="2016-03",
                end_month="2016-03",
                storage_root=tmp,
                write=True,
            )

            self.assertEqual(state.start_month, "2016-03")
            self.assertTrue((tmp / "runtime" / "model_training_workflow_state_2016-03.json").exists())

    def test_provider_calls_observed_is_recorded_separately_from_offline_provider_calls(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            receipt = tmp / "provider_receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "manager_stage_id": "model_01_background_context.data_acquisition",
                        "status": "succeeded",
                        "provider_calls": 2,
                        "output_refs": ["storage://bars/layer1"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                state_path=state_path,
                receipt_paths=[receipt],
                write=True,
            )
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                state_path=state_path,
                receipt_paths=[receipt],
                write=False,
            )

            self.assertEqual(state.provider_calls, 0)
            self.assertEqual(state.provider_calls_observed, 2)
            self.assertEqual(state.summary_row()["provider_calls_observed"], 2)

    def test_m05_option_feature_generation_is_ready_after_shared_option_source_and_m04_generation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            completions = [
                "model_04_unified_decision.model_generation.train",
                "model_04_unified_decision.model_generation.validation",
                "model_04_unified_decision.model_generation.test",
            ]
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions + ["model_05_option_expression.option_chain_data_acquisition"],
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            m05_feature = {stage.stage_id: stage for stage in state.stages}["model_05_option_expression.feature_generation"]
            self.assertEqual(m05_feature.status, "ready")
            self.assertIsNone(m05_feature.approval_gate_required)
            self.assertTrue(any(token.endswith("execute_layer_nine_option_feature_generation.py") for token in m05_feature.command))

    def test_layer_workflow_state_has_no_layer_local_post_generation_stages(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=tmp,
                state_path=state_path,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            stage_types = {stage.stage_type for stage in state.stages}
            self.assertIn("model_generation", stage_types)
            self.assertNotIn("model_evaluation", stage_types)
            self.assertNotIn("promotion_review", stage_types)
            self.assertNotIn("maintenance", stage_types)

    def test_m04_unified_decision_can_progress_from_upstream_model_generation_completion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            completions = [
                f"model_{layer:02d}_{slug}.model_generation.{split}"
                for layer, slug in ((1, "background_context"), (2, "target_state"), (3, "event_state"))
                for split in ("train", "validation", "test")
            ]
            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            self.assertNotIn("model_04_unified_decision.data_acquisition", stage_by_id)
            self.assertNotIn("model_04_unified_decision.feature_generation", stage_by_id)
            self.assertEqual(stage_by_id["model_04_unified_decision.model_generation.train"].status, "ready")

    def test_workflow_state_write_triggers_dashboard_refresh_when_enabled(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            plan = build_model_training_workflow_plan(storage_root=tmp / "storage" / "02_control_plane", start_month="2016-01", end_month="2016-01")
            state = initial_workflow_state(plan)
            state_path = tmp / "workflow_state.json"

            with patch("trading_manager_tasks.model_training_state.trigger_dashboard_refresh_from_workflow_state_write") as trigger:
                write_workflow_state(state_path, state)

        trigger.assert_called_once_with(state_path=state_path)


if __name__ == "__main__":
    unittest.main()

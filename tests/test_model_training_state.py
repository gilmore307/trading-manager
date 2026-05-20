from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.model_training_state import (
    advance_workflow_state,
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
        self.assertEqual(stage.stage_id, "layer_01_market_regime.data_acquisition")
        self.assertEqual(stage.status, "blocked")
        self.assertIn("layer_01_task_key_preparation", stage.last_reason or "")
        self.assertIsNone(next_ready_or_blocked_stage(state))

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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                write=True,
            )
            next_stage = next_ready_or_blocked_stage(state)
            self.assertIsNotNone(next_stage)
            self.assertEqual(next_stage.stage_id, "layer_01_market_regime.data_acquisition")
            self.assertEqual(next_stage.status, "ready")

            receipt = tmp / "receipt.json"
            receipt.write_text(
                json.dumps(
                    {
                        "manager_stage_id": "layer_01_market_regime.data_acquisition",
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
            self.assertEqual(stage_by_id["layer_01_market_regime.data_acquisition"].status, "succeeded")
            self.assertIn("storage://bars/layer1", stage_by_id["layer_01_market_regime.data_acquisition"].artifact_refs)
            self.assertEqual(stage_by_id["layer_01_market_regime.feature_generation"].status, "ready")
            self.assertEqual(next_ready_or_blocked_stage(state).stage_id, "layer_01_market_regime.feature_generation")

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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_receipts=[("layer_01_market_regime.data_acquisition", receipt) for receipt in receipts],
                write=False,
            )

            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            acquisition = stage_by_id["layer_01_market_regime.data_acquisition"]
            self.assertEqual(acquisition.status, "ready")
            self.assertEqual(len(acquisition.receipt_refs), 3)
            self.assertIn("partial component receipt coverage 3/19", acquisition.last_reason)
            self.assertEqual(stage_by_id["layer_01_market_regime.feature_generation"].status, "blocked")
            self.assertIn("layer_01_market_regime.data_acquisition_complete", stage_by_id["layer_01_market_regime.feature_generation"].last_reason)

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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_receipts=[("layer_01_market_regime.data_acquisition", receipt) for receipt in receipts],
                expected_receipt_counts={"layer_01_market_regime.data_acquisition": 2},
                write=False,
            )

            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            acquisition = stage_by_id["layer_01_market_regime.data_acquisition"]
            self.assertEqual(acquisition.status, "succeeded")
            self.assertEqual(len(acquisition.receipt_refs), 2)
            self.assertIn("storage://bars/0.csv", acquisition.artifact_refs)
            self.assertEqual(stage_by_id["layer_01_market_regime.feature_generation"].status, "ready")

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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                write=False,
            )
            stage_id = "layer_01_market_regime.data_acquisition"
            stage = {stage.stage_id: stage for stage in state.stages}[stage_id]
            self.assertIsNotNone(stage.created_at_utc)
            self.assertIsNotNone(stage.status_updated_at_utc)
            self.assertIsNotNone(stage.started_at_utc)
            self.assertIsNone(stage.ended_at_utc)
            started_when_current = stage.started_at_utc

            state = mark_stage_started(state, stage_id=stage_id, started_at="2026-05-13T10:00:00+00:00")
            state = mark_stage_succeeded(state, stage_id=stage_id, ended_at="2026-05-13T10:05:00+00:00")
            stage = {stage.stage_id: stage for stage in state.stages}[stage_id]
            self.assertEqual(stage.started_at_utc, started_when_current)
            self.assertEqual(stage.ended_at_utc, "2026-05-13T10:05:00+00:00")
            self.assertEqual(stage.status_updated_at_utc, "2026-05-13T10:05:00+00:00")

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
                                "stage_id": "layer_01_market_regime.data_acquisition",
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
                completed_stage_ids=["layer_01_market_regime.data_acquisition"],
                write=False,
            )

            stage = {stage.stage_id: stage for stage in state.stages}["layer_01_market_regime.data_acquisition"]
            self.assertEqual(stage.status, "succeeded")
            self.assertIsNone(stage.created_at_utc)
            self.assertIsNone(stage.started_at_utc)
            self.assertIsNone(stage.ended_at_utc)
            self.assertIsNone(stage.status_updated_at_utc)

    def test_default_checkpoint_path_is_month_scoped(self):
        path = workflow_state_path_for_month("2016-02", root=Path("storage/runtime"))

        self.assertEqual(path, Path("storage/runtime/model_training_workflow_state_2016-02.json"))

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
                        "manager_stage_id": "layer_01_market_regime.data_acquisition",
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

    def test_layer_nine_option_expression_gate_review_is_ready_after_complete_upstream_base_chain(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            completions = []
            layer_slugs = {
                1: "market_regime",
                2: "sector_context",
                3: "target_state_vector",
                4: "event_failure_risk",
                5: "alpha_confidence",
                6: "dynamic_risk_policy",
                7: "position_projection",
                8: "underlying_action",
            }
            for layer, key in layer_slugs.items():
                prefix = f"layer_{layer:02d}_{key}"
                stage_types = ["model_generation", "model_evaluation", "promotion_review", "maintenance"]
                if layer not in {4, 5, 6, 7, 8}:
                    stage_types = ["data_acquisition", "feature_generation", *stage_types]
                completions.extend(f"{prefix}.{stage_type}" for stage_type in stage_types)
            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            layer_nine_acquisition = {stage.stage_id: stage for stage in state.stages}["layer_09_option_expression.data_acquisition"]
            self.assertEqual(layer_nine_acquisition.status, "ready")
            self.assertIsNone(layer_nine_acquisition.approval_gate_required)
            self.assertTrue(any(token.endswith("review_layer_nine_option_expression_gate.py") for token in layer_nine_acquisition.command))

    def test_promotion_review_waits_until_all_layer_evaluations_complete(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            layer_slugs = {
                1: "market_regime",
                2: "sector_context",
                3: "target_state_vector",
                4: "event_failure_risk",
                5: "alpha_confidence",
                6: "dynamic_risk_policy",
                7: "position_projection",
                8: "underlying_action",
                9: "option_expression",
                10: "event_risk_governor",
            }
            incomplete = [f"layer_{layer:02d}_{slug}.model_evaluation" for layer, slug in layer_slugs.items() if layer < 10]
            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=incomplete,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stage_by_id["layer_01_market_regime.promotion_review"].status, "blocked")
            self.assertIn("fold_layers_01_10_model_evaluation_complete", stage_by_id["layer_01_market_regime.promotion_review"].last_reason or "")

            complete = [f"layer_{layer:02d}_{slug}.model_evaluation" for layer, slug in layer_slugs.items()]
            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=complete,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stage_by_id["layer_01_market_regime.promotion_review"].status, "ready")
            self.assertEqual(stage_by_id["layer_10_event_risk_governor.promotion_review"].status, "ready")

    def test_layers_without_input_tasks_can_progress_from_upstream_completion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            completions = []
            for layer in range(1, 4):
                key = [
                    "market_regime",
                    "sector_context",
                    "target_state_vector",
                ][layer - 1]
                prefix = f"layer_{layer:02d}_{key}"
                completions.extend(
                    [
                        f"{prefix}.data_acquisition",
                        f"{prefix}.feature_generation",
                        f"{prefix}.model_generation",
                        f"{prefix}.model_evaluation",
                        f"{prefix}.promotion_review",
                        f"{prefix}.maintenance",
                    ]
                )
            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=False,
            )
            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            self.assertNotIn("layer_05_alpha_confidence.data_acquisition", stage_by_id)
            self.assertNotIn("layer_05_alpha_confidence.feature_generation", stage_by_id)
            self.assertEqual(stage_by_id["layer_04_event_failure_risk.model_generation"].status, "ready")

    def test_workflow_state_write_triggers_dashboard_refresh_when_enabled(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            plan = build_model_training_workflow_plan(storage_root=tmp / "storage", start_month="2016-01", end_month="2016-01")
            state = initial_workflow_state(plan)
            state_path = tmp / "workflow_state.json"

            with patch("trading_manager_tasks.model_training_state.trigger_dashboard_refresh_from_workflow_state_write") as trigger:
                write_workflow_state(state_path, state)

        trigger.assert_called_once_with(state_path=state_path)


if __name__ == "__main__":
    unittest.main()

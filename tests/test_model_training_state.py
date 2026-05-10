from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_state import (
    advance_workflow_state,
    initial_workflow_state,
    next_ready_or_blocked_stage,
)
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        task_key = root / "monthly_backfill_v1" / "alpaca_bars" / member.symbol / month / "task_key.json"
        task_key.parent.mkdir(parents=True, exist_ok=True)
        task_key.write_text("{}\n", encoding="utf-8")


class ModelTrainingWorkflowStateTests(unittest.TestCase):
    def test_initial_state_blocks_until_layer_one_task_keys_exist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            plan = build_model_training_workflow_plan(storage_root=Path(raw_tmp), start_month="2016-01", end_month="2016-01")
            state = initial_workflow_state(plan)
        stage = state.stages[0]
        self.assertEqual(state.contract_type, "manager_model_training_workflow_state_v1")
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
            self.assertIn("partial component receipt coverage 3/22", acquisition.last_reason)
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

    def test_layer_eight_waits_for_complete_upstream_target_chain_and_approval(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            completions = []
            layer_slugs = {
                1: "market_regime",
                2: "sector_context",
                3: "target_state_vector",
                4: "event_overlay",
                5: "alpha_confidence",
                6: "position_projection",
                7: "underlying_action",
            }
            for layer, key in layer_slugs.items():
                prefix = f"layer_{layer:02d}_{key}"
                completions.extend(
                    [
                        f"{prefix}.data_acquisition",
                        f"{prefix}.feature_generation",
                        f"{prefix}.model_generation",
                        f"{prefix}.model_evaluation",
                        f"{prefix}.promotion_review_preparation",
                        f"{prefix}.maintenance",
                    ]
                )
            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions,
                write=False,
            )
            layer_eight_acquisition = {stage.stage_id: stage for stage in state.stages}["layer_08_option_expression.data_acquisition"]
            self.assertEqual(layer_eight_acquisition.status, "blocked")
            self.assertEqual(layer_eight_acquisition.last_reason, "waiting for live_call_approval_v1")

            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions,
                approved_stage_refs=["layer_08_option_expression.data_acquisition=approval://layer8"],
                write=False,
            )
            layer_eight_acquisition = {stage.stage_id: stage for stage in state.stages}["layer_08_option_expression.data_acquisition"]
            self.assertEqual(layer_eight_acquisition.status, "ready")

    def test_not_applicable_layers_can_progress_from_upstream_completion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "workflow_state.json"
            completions = []
            for layer in range(1, 5):
                key = [
                    "market_regime",
                    "sector_context",
                    "target_state_vector",
                    "event_overlay",
                ][layer - 1]
                prefix = f"layer_{layer:02d}_{key}"
                completions.extend(
                    [
                        f"{prefix}.data_acquisition",
                        f"{prefix}.feature_generation",
                        f"{prefix}.model_generation",
                        f"{prefix}.model_evaluation",
                        f"{prefix}.promotion_review_preparation",
                        f"{prefix}.maintenance",
                    ]
                )
            state = advance_workflow_state(
                storage_root=tmp,
                state_path=state_path,
                completed_stage_ids=completions,
                write=False,
            )
            stage_by_id = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stage_by_id["layer_05_alpha_confidence.data_acquisition"].status, "not_applicable")
            self.assertEqual(stage_by_id["layer_05_alpha_confidence.feature_generation"].status, "not_applicable")
            self.assertEqual(stage_by_id["layer_05_alpha_confidence.model_generation"].status, "ready")


if __name__ == "__main__":
    unittest.main()

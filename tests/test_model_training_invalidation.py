from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_invalidation import invalidate_layer_downstream_outputs


class ModelTrainingInvalidationTests(unittest.TestCase):
    def test_invalidates_residual_event_governance_outputs_while_preserving_layers_one_three(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            runtime = tmp / "runtime"
            runtime.mkdir()
            state_path = runtime / "model_training_fold_state_2016-01_2016-06.json"
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "updated_utc": "old",
                        "stages": [
                            {"stage_id": "layer_03_target_state_vector.model_generation", "layer": 3, "status": "succeeded", "artifact_refs": []},
                            {"stage_id": "model_05_option_expression.model_evaluation", "layer": 5, "status": "ready", "artifact_refs": []},
                            {"stage_id": "model_06_residual_event_governance.model_generation", "layer": 6, "status": "succeeded", "artifact_refs": ["old"]},
                        ],
                    }
                ),
                encoding="utf-8",
            )

            summary = invalidate_layer_downstream_outputs(runtime_root=runtime, write=True)
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            by_stage = {stage["stage_id"]: stage for stage in payload["stages"]}

            self.assertEqual(summary.invalidated_stage_count, 1)
            self.assertEqual(by_stage["layer_03_target_state_vector.model_generation"]["status"], "succeeded")
            self.assertEqual(by_stage["model_05_option_expression.model_evaluation"]["status"], "ready")
            self.assertEqual(by_stage["model_06_residual_event_governance.model_generation"]["status"], "failed")
            self.assertIn("rebuild_from_residual_event_governance_required", by_stage["model_06_residual_event_governance.model_generation"]["last_reason"])
            self.assertIn("manager://stale_downstream_from_m06_residual_event_source_rebuild_required", by_stage["model_06_residual_event_governance.model_generation"]["artifact_refs"])

    def test_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            runtime = tmp / "runtime"
            runtime.mkdir()
            state_path = runtime / "model_training_fold_state_2016-01_2016-06.json"
            original = {"stages": [{"stage_id": "model_06_residual_event_governance.data_acquisition", "layer": 6, "status": "succeeded", "artifact_refs": []}]}
            state_path.write_text(json.dumps(original), encoding="utf-8")

            summary = invalidate_layer_downstream_outputs(runtime_root=runtime, write=False)

            self.assertFalse(summary.write_performed)
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), original)


if __name__ == "__main__":
    unittest.main()

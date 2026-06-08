from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.layer_nine_feature_stage import LayerNineFeatureStageSummary
from trading_manager_tasks.model_group_replay_option_features import (
    ReplayOptionFeatureRequirement,
    run_model_group_replay_option_features_if_required,
)


class ModelGroupReplayOptionFeaturesTests(unittest.TestCase):
    def _write_completed_fold(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        stages = []
        for layer in range(1, 10):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"layer_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"layer_{layer:02d}_fixture",
                        "status": "succeeded",
                        "dataset_split": {
                            "split_name": split_name,
                            "split_policy": "chronological_rolling_fold_4_1_1",
                        },
                    }
                )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                    "target_symbol": "AAPL",
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        artifact_path = (
            storage_root.parent
            / "03_model_artifacts"
            / "runtime"
            / "model_05_alpha_confidence"
            / "after_cost_alpha_model_aapl_2016-01_2016-06.json"
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text('{"artifacts_by_horizon": {}}\n', encoding="utf-8")

    def _write_frozen_dataset(self, storage_root: Path) -> Path:
        dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
        dataset_root.mkdir(parents=True, exist_ok=True)
        plan_path = dataset_root / "feed_acquisition_plan.csv"
        plan_path.write_text(
            "month,source_id,coverage_status,target_ref,start_date,end_date_exclusive\n"
            "2021-01,alpaca_bars,available,AAPL,2021-01-01,2021-02-01\n",
            encoding="utf-8",
        )
        (dataset_root / "dataset_manifest.json").write_text(
            json.dumps(
                {
                    "contract_type": "replay_dataset_preparation_manifest",
                    "freeze_status": "frozen",
                    "missing_feed_acquisition_count": 0,
                    "feed_acquisition_plan_ref": str(plan_path),
                    "pre_replay_target_refs": ["AAPL"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (dataset_root / "replay_freeze_receipt.json").write_text(
            json.dumps({"freeze_status": "frozen", "validation": {"validation_status": "passed"}}) + "\n",
            encoding="utf-8",
        )
        return dataset_root

    def test_generates_layer_nine_features_when_source_rows_are_ready(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._missing_option_feature_requirements", return_value=(requirement,)),
                patch("trading_manager_tasks.model_group_replay_option_features._source_rows_available", return_value=True),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.execute_layer_nine_feature_stage",
                    return_value=LayerNineFeatureStageSummary(
                        contract_type="manager_layer_09_option_expression_feature_generation_stage",
                        stage_id="layer_09_option_expression.feature_generation",
                        start_month="2021-01",
                        end_month="2021-01",
                        status="succeeded",
                        mode="test",
                        receipt_path=None,
                    ),
                ) as generate,
            ):
                decision = run_model_group_replay_option_features_if_required(
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=False,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "model_group_replay_option_feature_preparation_executed")
        self.assertEqual(decision.provider_calls, 0)
        generate.assert_called_once_with(start_month="2021-01", end_month="2021-01")

    def test_requires_provider_gate_when_source_rows_are_missing(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._missing_option_feature_requirements", return_value=(requirement,)),
                patch("trading_manager_tasks.model_group_replay_option_features._source_rows_available", return_value=False),
            ):
                decision = run_model_group_replay_option_features_if_required(
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=False,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_acquisition_required")
        self.assertEqual(decision.execution_summary["blocked_stage_id"], "layer_03_target_state_vector.option_chain_data_acquisition")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

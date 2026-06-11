from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.m05_option_expression_feature_stage import M05OptionExpressionFeatureStageSummary
from trading_manager_tasks.model_group_replay_option_features import (
    ReplayOptionFeatureRequirement,
    replay_option_feature_requirements_from_replay_decision,
    run_model_group_replay_option_features_for_replay_backoff,
)
from trading_manager_tasks.scheduler import SchedulerDecision


class ModelGroupReplayOptionFeaturesTests(unittest.TestCase):
    def _replay_backoff(self, requirement: ReplayOptionFeatureRequirement) -> SchedulerDecision:
        payload = {
            "missing_count": 1,
            "sample": [
                {
                    "target_ref": requirement.target_ref,
                    "timestamp": requirement.timestamp,
                    "maximum_permitted_source_end": requirement.timestamp,
                    "signal_source": "model_04_unified_decision.handoff_to_model_05",
                }
            ],
        }
        reason = "ValueError: replay_option_feature_acquisition_required: " + json.dumps(payload, sort_keys=True)
        return SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-01-01T00:00:00+00:00",
            now_et="2025-12-31T19:00:00-05:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_feature_acquisition_required",
            reason=reason,
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay",
            command=[],
            execution_summary={"runner_stderr": reason},
        )

    def _write_completed_fold(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        stages = []
        for layer in range(1, 7):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"model_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"model_{layer:02d}_fixture",
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
                patch("trading_manager_tasks.model_group_replay_option_features._source_rows_available", return_value=True),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.execute_m05_option_expression_feature_stage",
                    return_value=M05OptionExpressionFeatureStageSummary(
                        contract_type="manager_model_05_option_expression_feature_generation_stage",
                        stage_id="model_05_option_expression.feature_generation",
                        start_month="2021-01",
                        end_month="2021-01",
                        status="succeeded",
                        mode="test",
                        receipt_path=None,
                    ),
                ) as generate,
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    self._replay_backoff(requirement),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=False,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "model_group_replay_option_feature_repair_executed")
        self.assertEqual(decision.provider_calls, 0)
        generate.assert_called_once_with(start_month="2021-01", end_month="2021-01", target_symbol="AAPL")

    def test_extracts_requirements_from_replay_backoff_sample(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01")
        parsed = replay_option_feature_requirements_from_replay_decision(self._replay_backoff(requirement))
        self.assertEqual(parsed, (requirement,))

    def test_requires_provider_gate_when_source_rows_are_missing(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._source_rows_available", return_value=False),
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    self._replay_backoff(requirement),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=False,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_acquisition_required")
        self.assertEqual(decision.execution_summary["blocked_stage_id"], "model_05_option_expression.option_chain_data_acquisition")

    def test_provider_failure_returns_repair_failure_decision(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-03-05T16:00:00-05:00", "2021-03")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._source_rows_available", return_value=False),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_replay_option_source_requests",
                    return_value={"2021-03": ["mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930"]},
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.dispatch_option_chain_source_acquisition",
                    side_effect=RuntimeError("ThetaData INTERNAL"),
                ),
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    self._replay_backoff(requirement),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=True,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_acquisition_failed")
        self.assertTrue(decision.dispatch_performed)
        self.assertIn("ThetaData INTERNAL", decision.execution_summary["provider_acquisition_error"])
        self.assertEqual(
            decision.execution_summary["source_request_ids_by_month"],
            {"2021-03": ["mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930"]},
        )

    def test_provider_unavailable_records_replay_sentinel(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-03-05T16:00:00-05:00", "2021-03")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._source_rows_available", return_value=False),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_replay_option_source_requests",
                    return_value={"2021-03": ["mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930"]},
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.dispatch_option_chain_source_acquisition",
                    side_effect=RuntimeError("ThetaData Terminal REST HTTP 478"),
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_option_source_unavailable_markers",
                    return_value=1,
                ) as persist_unavailable,
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    self._replay_backoff(requirement),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=True,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_unavailable_recorded")
        self.assertTrue(decision.dispatch_performed)
        self.assertEqual(decision.execution_summary["option_source_unavailable_count"], 1)
        persist_unavailable.assert_called_once()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

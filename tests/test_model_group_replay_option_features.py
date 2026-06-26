from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from trading_manager_tasks.m05_option_expression_feature_stage import M05OptionExpressionFeatureStageSummary
from trading_manager_tasks.model_group_replay_option_features import (
    ReplayOptionFeatureRequirement,
    latest_replay_option_feature_requirements_artifact,
    replay_option_feature_backoff_for_requirements_artifact,
    replay_option_feature_payload_from_text,
    replay_option_feature_requirements_from_replay_decision,
    run_model_group_replay_option_features_for_replay_backoff,
)
from trading_manager_tasks.scheduler import SchedulerDecision


class ModelGroupReplayOptionFeaturesTests(unittest.TestCase):
    def _requirements_artifact_row(
        self,
        *,
        target_ref: str = "AAPL",
        timestamp: str = "2021-01-04T16:00:00-05:00",
    ) -> dict[str, str]:
        return {
            "target_ref": target_ref,
            "timestamp": timestamp,
            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
            "max_positions": "5",
            "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
            "switch_minimum_rank_score_delta": "1e-05",
        }

    def test_extracts_option_feature_payload_from_runner_text(self) -> None:
        payload = {
            "missing_count": 2,
            "requirements_artifact_ref": "/tmp/requirements.jsonl",
            "sample": [{"target_ref": "AAPL", "timestamp": "2021-01-04T16:00:00-05:00"}],
        }
        text = "ValueError: replay_option_feature_acquisition_required: " + json.dumps(payload, sort_keys=True)

        self.assertEqual(replay_option_feature_payload_from_text(text), payload)

    def test_option_feature_payload_returns_empty_for_unrelated_text(self) -> None:
        self.assertEqual(replay_option_feature_payload_from_text("ValueError: unrelated"), {})

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
        requirement = ReplayOptionFeatureRequirement("MSFT", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", side_effect=((requirement,), ())),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=(requirement,)),
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
        generate.assert_called_once_with(start_month="2021-01", end_month="2021-01", target_symbol="MSFT")

    def test_feature_repair_limit_is_independent_from_provider_limit(self) -> None:
        requirement = ReplayOptionFeatureRequirement("MSFT", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", return_value=()) as missing,
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    self._replay_backoff(requirement),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=True,
                    provider_acquisition_limit=1,
                    feature_repair_limit=250,
                )

        self.assertIsNotNone(decision)
        self.assertEqual(missing.call_args.kwargs["limit"], 250)

    def test_generates_source_ready_features_before_provider_backoff(self) -> None:
        ready = ReplayOptionFeatureRequirement("MSFT", "2021-01-04T16:00:00-05:00", "2021-01")
        missing_source = ReplayOptionFeatureRequirement("TSLA", "2021-01-05T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements",
                    side_effect=((ready, missing_source), (missing_source,)),
                ),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=(ready,)),
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
                    self._replay_backoff(ready),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=False,
                    feature_repair_limit=2,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_option_feature_repair_incomplete")
        self.assertEqual(decision.execution_summary["source_missing_count"], 1)
        self.assertEqual(decision.execution_summary["post_repair_missing_count"], 1)
        generate.assert_called_once_with(start_month="2021-01", end_month="2021-01", target_symbol="MSFT")

    def test_feature_generation_success_requires_post_repair_feature_rows(self) -> None:
        requirement = ReplayOptionFeatureRequirement("MSFT", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements",
                    side_effect=((requirement,), (requirement,)),
                ),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=(requirement,)),
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
                ),
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
        self.assertEqual(decision.reason_code, "model_group_replay_option_feature_repair_incomplete")
        self.assertEqual(decision.execution_summary["post_repair_missing_count"], 1)

    def test_extracts_requirements_from_replay_backoff_sample(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01")
        parsed = replay_option_feature_requirements_from_replay_decision(self._replay_backoff(requirement))
        self.assertEqual(parsed, (requirement,))

    def test_extracts_requirements_from_replay_backoff_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "option_feature_requirements.jsonl"
            artifact.write_text(
                "\n".join(
                    [
                        json.dumps({"target_ref": "AAPL", "timestamp": "2021-01-04T16:00:00-05:00"}),
                        json.dumps({"target_ref": "MSFT", "timestamp": "2021-02-05T16:00:00-05:00"}),
                        json.dumps({"target_ref": "AAPL", "timestamp": "2021-01-04T16:00:00-05:00"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            payload = {
                "missing_count": 3,
                "requirements_artifact_ref": str(artifact),
                "sample": [{"target_ref": "TSLA", "timestamp": "2021-03-01T16:00:00-05:00"}],
            }
            reason = "ValueError: replay_option_feature_acquisition_required: " + json.dumps(payload, sort_keys=True)
            decision = SchedulerDecision(
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

            parsed = replay_option_feature_requirements_from_replay_decision(decision)

        self.assertEqual(
            parsed,
            (
                ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01"),
                ReplayOptionFeatureRequirement("MSFT", "2021-02-05T16:00:00-05:00", "2021-02"),
            ),
        )

    def test_latest_requirements_artifact_ignores_completed_replay_runs(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            old_run = dataset_root / "replay_execution_runs" / "old_run"
            new_run = dataset_root / "replay_execution_runs" / "new_run"
            old_run.mkdir(parents=True)
            new_run.mkdir(parents=True)
            old_artifact = old_run / "option_feature_requirements.jsonl"
            new_artifact = new_run / "option_feature_requirements.jsonl"
            old_artifact.write_text(json.dumps(self._requirements_artifact_row()) + "\n", encoding="utf-8")
            new_artifact.write_text(json.dumps(self._requirements_artifact_row()) + "\n", encoding="utf-8")
            (new_run / "replay_execution_receipt.json").write_text("{}\n", encoding="utf-8")

            selected = latest_replay_option_feature_requirements_artifact(storage_root=storage_root)

        self.assertEqual(selected, old_artifact)

    def test_latest_requirements_artifact_ignores_stale_portfolio_capacity_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            stale_run = dataset_root / "replay_execution_runs" / "stale_run"
            current_run = dataset_root / "replay_execution_runs" / "current_run"
            stale_run.mkdir(parents=True)
            current_run.mkdir(parents=True)
            stale_artifact = stale_run / "option_feature_requirements.jsonl"
            current_artifact = current_run / "option_feature_requirements.jsonl"
            stale_artifact.write_text(
                json.dumps({"target_ref": "AAPL", "timestamp": "2021-01-04T16:00:00-05:00"}) + "\n",
                encoding="utf-8",
            )
            current_artifact.write_text(
                json.dumps(self._requirements_artifact_row(target_ref="MSFT")) + "\n",
                encoding="utf-8",
            )

            selected = latest_replay_option_feature_requirements_artifact(storage_root=storage_root)

        self.assertEqual(selected, current_artifact)

    def test_latest_requirements_artifact_ignores_stale_switch_threshold_contract(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            stale_run = dataset_root / "replay_execution_runs" / "stale_run"
            current_run = dataset_root / "replay_execution_runs" / "current_run"
            stale_run.mkdir(parents=True)
            current_run.mkdir(parents=True)
            stale_artifact = stale_run / "option_feature_requirements.jsonl"
            current_artifact = current_run / "option_feature_requirements.jsonl"
            stale_row = self._requirements_artifact_row(target_ref="AAPL")
            stale_row.pop("switch_threshold_policy")
            stale_artifact.write_text(json.dumps(stale_row) + "\n", encoding="utf-8")
            current_artifact.write_text(
                json.dumps(self._requirements_artifact_row(target_ref="MSFT")) + "\n",
                encoding="utf-8",
            )

            selected = latest_replay_option_feature_requirements_artifact(storage_root=storage_root)

        self.assertEqual(selected, current_artifact)

    def test_synthetic_backoff_from_requirements_artifact_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "option_feature_requirements.jsonl"
            artifact.write_text(
                json.dumps({"target_ref": "AAPL", "timestamp": "2021-01-04T16:00:00-05:00"}) + "\n",
                encoding="utf-8",
            )

            decision = replay_option_feature_backoff_for_requirements_artifact(artifact)
            parsed = replay_option_feature_requirements_from_replay_decision(decision)

        self.assertEqual(parsed, (ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01"),))

    def test_requires_provider_gate_when_source_rows_are_missing(self) -> None:
        requirement = ReplayOptionFeatureRequirement("AAPL", "2021-01-04T16:00:00-05:00", "2021-01")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", side_effect=((requirement,), ())),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=()),
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
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", side_effect=((requirement,), ())),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=()),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_replay_option_source_requests",
                    return_value={"2021-03": ["mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930"]},
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.dispatch_option_chain_source_acquisition",
                    side_effect=RuntimeError("ThetaData INTERNAL"),
                ) as dispatch,
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    self._replay_backoff(requirement),
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=True,
                    provider_max_workers=4,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_acquisition_failed")
        self.assertEqual(dispatch.call_args.kwargs["max_workers"], 4)
        self.assertTrue(decision.dispatch_performed)
        self.assertIn("ThetaData INTERNAL", decision.execution_summary["provider_acquisition_error"])
        self.assertEqual(
            decision.execution_summary["source_request_ids_by_month"],
            {"2021-03": ["mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930"]},
        )

    def test_provider_read_timeout_returns_retryable_source_backoff(self) -> None:
        requirement = ReplayOptionFeatureRequirement("TMHC", "2021-03-08T16:00:00-05:00", "2021-03")
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", side_effect=((requirement,), ())),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=()),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_replay_option_source_requests",
                    return_value={"2021-03": ["mgrreq_replay_option_chain_window_tmhc_2021_03_2021_03_08_1600"]},
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.dispatch_option_chain_source_acquisition",
                    side_effect=RuntimeError('"error": {"message": "The read operation timed out", "type": "ReadTimeout"}'),
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
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_acquisition_required")
        self.assertTrue(decision.dispatch_performed)
        self.assertIn("ReadTimeout", decision.execution_summary["provider_acquisition_error"])
        self.assertEqual(
            decision.execution_summary["required_next_step"],
            "continue bounded replay option source acquisition",
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
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", side_effect=((requirement,), ())),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", return_value=()),
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

    def test_provider_success_without_source_rows_records_replay_sentinel(self) -> None:
        requirement = ReplayOptionFeatureRequirement("ALAB", "2024-03-21T16:00:00-04:00", "2024-03")
        dispatch_summary = SimpleNamespace(
            provider_calls=1,
            summary_row=lambda: {
                "contract_type": "manager_provider_dispatch_summary",
                "provider_calls": 1,
                "dispatch_count": 1,
            },
        )
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", side_effect=((requirement,), ())),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", side_effect=((), ())),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_replay_option_source_requests",
                    return_value={"2024-03": ["mgrreq_option_chain_window_alab_2024_03_2024_03_21_0930"]},
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.dispatch_option_chain_source_acquisition",
                    return_value=dispatch_summary,
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_option_source_unavailable_markers",
                    return_value=1,
                ) as persist_unavailable,
                patch("trading_manager_tasks.model_group_replay_option_features.execute_m05_option_expression_feature_stage") as generate,
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
        self.assertEqual(decision.provider_calls, 1)
        self.assertEqual(decision.execution_summary["option_source_unavailable_count"], 1)
        persist_unavailable.assert_called_once()
        generate.assert_not_called()

    def test_provider_success_without_source_rows_with_deferred_work_reports_progress(self) -> None:
        first = ReplayOptionFeatureRequirement("TKO", "2021-01-05T16:00:00-05:00", "2021-01")
        deferred = ReplayOptionFeatureRequirement("CLS", "2021-01-05T16:00:00-05:00", "2021-01")
        dispatch_summary = SimpleNamespace(
            provider_calls=1,
            summary_row=lambda: {
                "contract_type": "manager_provider_dispatch_summary",
                "provider_calls": 1,
                "dispatch_count": 1,
            },
        )
        payload = {
            "missing_count": 2,
            "sample": [
                {
                    "target_ref": first.target_ref,
                    "timestamp": first.timestamp,
                    "maximum_permitted_source_end": first.timestamp,
                    "signal_source": "model_04_unified_decision.handoff_to_model_05",
                },
                {
                    "target_ref": deferred.target_ref,
                    "timestamp": deferred.timestamp,
                    "maximum_permitted_source_end": deferred.timestamp,
                    "signal_source": "model_04_unified_decision.handoff_to_model_05",
                },
            ],
        }
        reason = "ValueError: replay_option_feature_acquisition_required: " + json.dumps(payload, sort_keys=True)
        replay_backoff = SchedulerDecision(
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
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True, exist_ok=True)
            self._write_completed_fold(storage_root)
            self._write_frozen_dataset(storage_root)

            with (
                patch("trading_manager_tasks.model_group_replay_option_features._database_url", return_value="postgres://test"),
                patch("trading_manager_tasks.model_group_replay_option_features._feature_missing_requirements", return_value=(first, deferred)),
                patch("trading_manager_tasks.model_group_replay_option_features._source_ready_requirements", side_effect=((), ())),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_replay_option_source_requests",
                    return_value={"2021-01": ["mgrreq_replay_option_chain_window_tko_2021_01_2021_01_05_1600"]},
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features.dispatch_option_chain_source_acquisition",
                    return_value=dispatch_summary,
                ),
                patch(
                    "trading_manager_tasks.model_group_replay_option_features._persist_option_source_unavailable_markers",
                    return_value=1,
                ) as persist_unavailable,
                patch("trading_manager_tasks.model_group_replay_option_features.execute_m05_option_expression_feature_stage") as generate,
            ):
                decision = run_model_group_replay_option_features_for_replay_backoff(
                    replay_backoff,
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    execute=True,
                    execute_provider_acquisition=True,
                    provider_acquisition_limit=1,
                )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "model_group_replay_option_source_unavailable_recorded")
        self.assertEqual(decision.provider_calls, 1)
        self.assertEqual(decision.execution_summary["option_source_unavailable_count"], 1)
        self.assertEqual(
            decision.execution_summary["required_next_step"],
            "continue replay option feature drain before retrying model_group.replay",
        )
        persist_unavailable.assert_called_once_with(
            [first],
            database_url="postgres://test",
            provider_error="provider acquisition completed without option_chain_state_source rows",
        )
        generate.assert_not_called()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

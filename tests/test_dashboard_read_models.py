from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.dashboard_read_models import build_historical_task_progress_summary
from trading_manager_tasks.scheduler_status import collect_historical_scheduler_status
from trading_manager_tasks.task_progress import write_task_progress_node


class DashboardReadModelProducerTests(unittest.TestCase):
    def _write_service_files(self, root: Path) -> tuple[Path, Path, Path]:
        service = root / "deploy" / "systemd" / "trading-manager-historical-scheduler.service"
        env = root / "deploy" / "systemd" / "trading-manager-historical-scheduler.env"
        wrapper = root / "scripts" / "tasks" / "run_automation_scheduler_daemon.py"
        service.parent.mkdir(parents=True, exist_ok=True)
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        service.write_text(
            "ExecStart=python3 scripts/tasks/run_automation_scheduler_daemon.py "
            "--execute-safe-preparation --execute-safe-offline-stages "
            "--execute-autonomous-provider-stages --auto-select-next-work --advance-month-on-complete\n",
            encoding="utf-8",
        )
        env.write_text("TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\n", encoding="utf-8")
        wrapper.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        return service, env, wrapper

    def test_builds_historical_task_progress_summary_payload(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            decision_log.parent.mkdir(parents=True, exist_ok=True)
            workflow_state = tmp / "storage" / "02_control_plane" / "runtime" / "model_training_workflow_state_2019-05.json"
            workflow_state.parent.mkdir(parents=True, exist_ok=True)
            receipt_path = tmp / "storage" / "02_control_plane" / "runtime" / "example_stage_receipt.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "layer_01_market_regime.data_acquisition",
                        "started_at": "2026-05-12T09:00:00Z",
                        "completed_at": "2026-05-12T09:30:00Z",
                        "status": "succeeded",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            workflow_state.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2019-05",
                        "end_month": "2019-05",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                                "updated_utc": "2026-05-12T10:00:00Z",
                                "last_reason": "stage coverage complete",
                                "receipt_refs": ["02_control_plane/runtime/example_stage_receipt.json"],
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "blocked",
                                "updated_utc": "2026-05-12T11:00:00Z",
                                "last_reason": "waiting for source rows",
                                "blockers": ["layer_02_sector_context.model_evaluation_complete"],
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "blocked",
                                "updated_utc": "2026-05-12T11:05:00Z",
                                "last_reason": "waiting for data acquisition",
                                "blockers": ["layer_03_target_state_vector.data_acquisition_complete"],
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision_log.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_decision",
                        "decision_status": "executed",
                        "selected_work": "layer_03_target_state_vector.data_acquisition",
                        "start_month": "2019-05",
                        "execution_summary": {
                            "stage_execution": {
                                "contract_type": "manager_stage_execution_summary",
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "status": "failed",
                                "reason": "no successful Layer 2 feed artifacts are available for Layer 3 target-state materialization",
                                "return_code": 1,
                                "stdout_path": "02_control_plane/runtime/model_training_stage_logs/example.stdout.log",
                                "stderr_path": "02_control_plane/runtime/model_training_stage_logs/example.stderr.log",
                                "receipt_path": "02_control_plane/runtime/model_training_stage_receipts/example.receipt.json",
                                "provider_calls": 0,
                                "model_activation_performed": False,
                                "broker_execution_performed": False,
                            }
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(
                status,
                stage_coverage={
                    "contract_type": "manager_stage_coverage",
                    "stage_id": "layer_01_market_regime.data_acquisition",
                    "status": "partial_ready",
                    "expected_count": 19,
                    "ready_count": 3,
                    "pending_count": 16,
                    "failed_count": 0,
                    "accepted_failed_count": 0,
                    "can_unlock_downstream": False,
                },
                generated_at_utc="2026-05-12T12:00:00Z",
            )

        self.assertEqual(payload["contract_type"], "historical_task_progress_summary")
        self.assertEqual(payload["source_system"], "trading-manager")
        self.assertEqual(payload["generated_at_utc"], "2026-05-12T12:00:00Z")
        self.assertEqual(payload["schema_ref"], "storage/06_dashboard_cache/schemas/historical_task_progress_summary.schema.json")
        self.assertEqual(payload["status"], "action_required")
        self.assertIn("last execution failed", payload["summary"])
        self.assertEqual(payload["chart_payload"]["stage_coverage"]["expected_count"], 19)
        self.assertFalse(payload["chart_payload"]["stage_coverage"]["can_unlock_downstream"])
        self.assertEqual(payload["chart_payload"]["last_stage_execution"]["status"], "failed")
        self.assertEqual(payload["chart_payload"]["last_stage_execution"]["return_code"], 1)
        task_timeline = payload["chart_payload"]["task_timeline"]
        self.assertEqual([task["task_state"] for task in task_timeline], ["completed", "failed", "future"])
        self.assertEqual(task_timeline[1]["task_label"], "Data Acquisition")
        self.assertEqual(task_timeline[1]["month"], "2019-fold1")
        self.assertEqual(task_timeline[1]["detail"]["child_partitions"], ["2019-01", "2019-02", "2019-03", "2019-04", "2019-05", "2019-06"])
        self.assertEqual(task_timeline[1]["detail"]["last_execution"]["return_code"], 1)
        self.assertEqual(task_timeline[0]["worker_id"], "model_worker_1")
        self.assertEqual(task_timeline[0]["detail"]["worker"]["worker_label"], "Model Worker 1")
        self.assertEqual(task_timeline[2]["stage_type"], "feature_generation")
        self.assertEqual(task_timeline[2]["worker_label"], "Model Worker 1")
        self.assertIsNone(task_timeline[0]["created_at_utc"])
        self.assertEqual(task_timeline[0]["started_at_utc"], "2026-05-12T09:00:00Z")
        self.assertEqual(task_timeline[0]["ended_at_utc"], "2026-05-12T09:30:00Z")
        self.assertEqual(task_timeline[0]["status_updated_at_utc"], "2026-05-12T10:00:00Z")
        self.assertEqual(task_timeline[0]["detail"]["progress"]["ready_count"], 3)
        self.assertIsNone(task_timeline[1]["detail"]["progress"])
        self.assertIsNone(task_timeline[2]["detail"]["progress"])
        self.assertIn("Layer 2 feed artifacts", payload["chart_payload"]["last_stage_execution"]["failure_detail"])
        self.assertTrue(any(ref.get("issue_type") == "historical_stage_execution_failed" for ref in payload["issue_refs"]))
        self.assertTrue(any(ref.get("ref_type") == "manager_stage_execution_summary" for ref in payload["diagnostic_refs"]))
        self.assertIn("profile_refs", payload)
        self.assertIn("lineage_refs", payload)
        self.assertIn(payload["severity"], {"critical", "high", "medium", "low", "info"})

    def test_task_timeline_shows_started_ready_stage_as_running_without_static_blockers(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2020-07.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2020-07",
                        "end_month": "2020-07",
                        "stages": [
                            {
                                "stage_id": "layer_09_option_expression.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 9,
                                "layer_key": "layer_09_option_expression",
                                "status": "ready",
                                "blockers": ["upstream_layer_08_model_evaluation_complete"],
                                "last_reason": "stage execution started by manager stage executor",
                                "started_at_utc": "2026-05-22T12:48:38Z",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            write_task_progress_node(
                progress_root=runtime / "task_progress",
                worker_id="month_ingest_worker_1",
                task_uid="2020-07:layer_09_option_expression.data_acquisition",
                stage_id="layer_09_option_expression.data_acquisition",
                node_id="stage_started",
                node_label="Stage process started",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T13:00:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_09_option_expression.data_acquisition")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["blocker_count"], 0)
        self.assertEqual(task["detail"]["blockers"], [])
        self.assertIsNone(task["detail"]["progress"])

    def test_task_timeline_reports_only_unresolved_blockers_from_waiting_reason(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2020-07.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2020-07",
                        "end_month": "2020-07",
                        "stages": [
                            {
                                "stage_id": "layer_09_option_expression.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 9,
                                "layer_key": "layer_09_option_expression",
                                "status": "blocked",
                                "blockers": ["upstream_layer_08_model_evaluation_complete", "other_static_dependency"],
                                "last_reason": "waiting for upstream_layer_08_model_evaluation_complete",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T13:00:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_09_option_expression.data_acquisition")
        self.assertEqual(task["status"], "blocked")
        self.assertEqual(task["blocker_count"], 1)
        self.assertEqual(task["detail"]["blockers"], ["upstream_layer_08_model_evaluation_complete"])

    def test_layer_model_evaluation_is_hidden_from_public_timeline(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            workflow_state = tmp / "storage" / "02_control_plane" / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            workflow_state.parent.mkdir(parents=True, exist_ok=True)
            workflow_state.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.model_evaluation",
                                "stage_type": "model_evaluation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T12:00:00Z")

        task_ids = [task["task_id"] for task in payload["chart_payload"]["task_timeline"]]
        self.assertNotIn("layer_03_target_state_vector.model_evaluation", task_ids)
        self.assertNotIn("model_group.model_evaluation", task_ids)
        self.assertIsNone(payload["chart_payload"]["active_stage"])
        self.assertIn("internal_active_stage", payload["chart_payload"])


    def test_non_owner_operational_items_are_ready_not_action_required(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["severity"], "info")
        self.assertIn("stopped and ready to start", payload["summary"])
        self.assertTrue(payload["issue_refs"])
        self.assertTrue(all(ref["owner_action_required"] is False for ref in payload["issue_refs"]))

    def test_task_timeline_uses_model_group_lifecycle_for_replay_and_promotion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "preparation_status": "prepared_candidate_policy_replay_acquisition_bundle",
                        "prepared_at_utc": "2026-05-21T02:34:48Z",
                        "freeze_status": "not_frozen",
                        "feed_acquisition_count": 360,
                        "available_feed_acquisition_count": 0,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 360,
                        "source_contract_ref": "trading-evaluation/replays/promotion_replay_candidate_policy.json",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "coverage_summary.csv").write_text(
                "contract_id,source_id,required_acquisition_count,available_acquisition_count,deferred_acquisition_count,missing_acquisition_count,coverage_status,notes\n"
                "promotion_replay_candidate_policy,alpaca_bars,60,0,0,60,incomplete,missing\n",
                encoding="utf-8",
            )
            (replay_root / "replay_window_manifest.csv").write_text(
                "contract_id,replay_mode,start_date,end_date,min_trading_days,candidate_policy_ref,replay_route_ref,market_condition_tags,selection_metric_refs\n"
                "promotion_replay_candidate_policy,candidate_policy_replay,2021-01-01,2026-01-01,1255,candidate,route,tags,metrics\n",
                encoding="utf-8",
            )
            fold_state = tmp / "storage" / "02_control_plane" / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            fold_state.parent.mkdir(parents=True, exist_ok=True)
            fold_state.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "six_month_target_fold",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T09:20:00Z")

        evaluation_tasks = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if str(task["task_id"]).startswith("model_group.")
        ]
        self.assertEqual(
            [task["task_id"] for task in evaluation_tasks],
            [
                "model_group.data_acquisition",
                "model_group.replay",
                "model_group.promotion_review",
                "model_group.maintenance",
            ],
        )
        self.assertEqual(
            [task["stage_type"] for task in evaluation_tasks],
            ["data_acquisition", "model_evaluation", "promotion_review", "maintenance"],
        )
        self.assertTrue(all(task["worker_id"] == "evaluation_worker_1" for task in evaluation_tasks))
        self.assertTrue(all(task["layer_key"] == "model_group" for task in evaluation_tasks))
        self.assertTrue(all(task["month"] == "2016-fold1" for task in evaluation_tasks))
        self.assertTrue(all(task["dataset_unit_kind"] == "model_group_training_fold" for task in evaluation_tasks))
        self.assertTrue(all(task["dataset_unit_months"] == 6 for task in evaluation_tasks))
        self.assertEqual(evaluation_tasks[1]["detail"]["dataset_unit"]["start_month"], "2016-01")
        self.assertEqual(evaluation_tasks[1]["detail"]["dataset_unit"]["end_month"], "2016-06")
        self.assertEqual(evaluation_tasks[1]["detail"]["dataset_unit"]["unit_months"], 6)
        self.assertEqual(evaluation_tasks[1]["detail"]["replay_window"]["start_month"], "2021-01")
        self.assertEqual(evaluation_tasks[1]["detail"]["replay_window"]["end_month"], "2026-01")
        self.assertEqual(evaluation_tasks[1]["detail"]["replay_window"]["unit_months"], 60)
        self.assertEqual(evaluation_tasks[0]["task_label"], "Data Acquisition")
        self.assertEqual(evaluation_tasks[0]["task_state"], "current")
        self.assertEqual(evaluation_tasks[0]["status"], "blocked")
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["expected_count"], 360)
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["pending_count"], 360)
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["unit_label"], "source-months")
        self.assertEqual(evaluation_tasks[1]["task_label"], "Model Evaluation")
        self.assertEqual(evaluation_tasks[1]["task_state"], "future")
        self.assertEqual(evaluation_tasks[1]["detail"]["progress"]["expected_count"], 60)
        self.assertEqual(evaluation_tasks[1]["detail"]["progress"]["pending_count"], 60)
        self.assertEqual(evaluation_tasks[1]["detail"]["progress"]["unit_label"], "months")
        self.assertIn("frozen replay contract", evaluation_tasks[1]["reason"])
        self.assertEqual(evaluation_tasks[2]["task_label"], "Promotion Review")
        self.assertEqual(evaluation_tasks[2]["detail"]["progress"]["expected_count"], 1)
        self.assertEqual(evaluation_tasks[2]["detail"]["progress"]["pending_count"], 1)
        self.assertEqual(evaluation_tasks[2]["detail"]["progress"]["unit_label"], "review-decision")
        self.assertIn("promotion-evaluation-review", evaluation_tasks[2]["detail"]["blockers"])
        self.assertEqual(evaluation_tasks[3]["task_label"], "Maintenance")
        self.assertEqual(evaluation_tasks[3]["detail"]["blockers"], ["model_group.promotion_review"])
        self.assertEqual(evaluation_tasks[3]["detail"]["progress"]["expected_count"], 1)
        self.assertEqual(evaluation_tasks[3]["detail"]["progress"]["unit_label"], "maintenance-step")
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.data_acquisition")
        self.assertEqual(payload["chart_payload"]["current_month"], "2016-fold1")
        self.assertEqual(payload["chart_payload"]["active_task"]["worker_id"], "evaluation_worker_1")
        self.assertNotEqual(payload["chart_payload"]["internal_active_stage"], payload["chart_payload"]["active_stage"])

    def test_ready_model_group_replay_does_not_override_active_scheduler_work(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "preparation_status": "prepared_candidate_policy_replay_acquisition_bundle",
                        "prepared_at_utc": "2026-05-21T02:34:48Z",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 60,
                        "available_feed_acquisition_count": 60,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 0,
                        "source_contract_ref": "trading-evaluation/replays/promotion_replay_candidate_policy.json",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "replay_window_manifest.csv").write_text(
                "contract_id,replay_mode,start_date,end_date,min_trading_days,candidate_policy_ref,replay_route_ref,market_condition_tags,selection_metric_refs\n"
                "promotion_replay_candidate_policy,candidate_policy_replay,2021-01-01,2026-01-01,1255,candidate,route,tags,metrics\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "six_month_target_fold",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_symbol": "AAPL",
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_workflow_state_2020-07.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2020-07",
                        "end_month": "2020-07",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "updated_utc": "2026-05-22T12:20:59Z",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({"current_month": "2020-07", "start_month": "2020-07"}) + "\n", encoding="utf-8")
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:21:00Z")

        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        self.assertEqual(replay_task["status"], "ready")
        self.assertEqual(replay_task["task_state"], "future")
        self.assertEqual(payload["chart_payload"]["active_stage"], "layer_03_target_state_vector.data_acquisition")
        self.assertEqual(payload["chart_payload"]["current_month"], "2020-fold2")

    def test_model_group_promotion_review_uses_review_artifact(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            review_root = replay_root / "promotion_review_runs" / "model_group_replay_fixture"
            review_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 2,
                        "available_feed_acquisition_count": 2,
                        "missing_feed_acquisition_count": 0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "feed_acquisition_plan.csv").write_text(
                "month\n2021-01\n2021-02\n",
                encoding="utf-8",
            )
            (replay_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (review_root / "promotion_evaluation_review.json").write_text(
                json.dumps(
                    {
                        "recommendation": "insufficient_evidence",
                        "blocking_issues": ["missing anonymous comparison", "auroc_below_minimum"],
                        "created_at_utc": "2026-05-22T12:50:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (review_root / "promotion_eligibility_decision.json").write_text(
                json.dumps(
                    {
                        "contract_type": "promotion_eligibility_decision",
                        "decision_status": "review_required",
                        "decision_reason": "AUROC below minimum; missing comparison evidence",
                        "created_at_utc": "2026-05-22T12:50:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            fold_state = tmp / "storage" / "02_control_plane" / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            fold_state.parent.mkdir(parents=True, exist_ok=True)
            fold_state.write_text(
                json.dumps(
                    {
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [{"stage_id": "layer_03_target_state_vector.model_generation", "stage_type": "model_generation", "status": "succeeded"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:51:00Z")

        promotion_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.promotion_review")
        maintenance_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.maintenance")
        self.assertEqual(promotion_task["status"], "review_required")
        self.assertEqual(promotion_task["task_state"], "current")
        self.assertEqual(promotion_task["detail"]["progress"]["ready_count"], 1)
        self.assertEqual(promotion_task["detail"]["progress"]["pending_count"], 0)
        self.assertFalse(promotion_task["detail"]["progress"]["can_unlock_downstream"])
        self.assertEqual(promotion_task["detail"]["blockers"], ["missing anonymous comparison", "auroc_below_minimum"])
        self.assertEqual(maintenance_task["status"], "blocked")
        self.assertEqual(maintenance_task["detail"]["blockers"], ["model_group.promotion_review"])

    def test_model_group_maintenance_completes_from_readiness_record(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            review_root = replay_root / "promotion_review_runs" / "model_group_replay_fixture"
            readiness_root = replay_root / "promotion_readiness_runs" / "model_group_replay_fixture"
            review_root.mkdir(parents=True, exist_ok=True)
            readiness_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 2,
                        "available_feed_acquisition_count": 2,
                        "missing_feed_acquisition_count": 0,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "feed_acquisition_plan.csv").write_text("month\n2021-01\n2021-02\n", encoding="utf-8")
            (replay_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (review_root / "promotion_evaluation_review.json").write_text(
                json.dumps({"recommendation": "eligible_for_shadow", "created_at_utc": "2026-05-22T12:50:00Z"}) + "\n",
                encoding="utf-8",
            )
            (review_root / "promotion_eligibility_decision.json").write_text(
                json.dumps(
                    {
                        "contract_type": "promotion_eligibility_decision",
                        "decision_status": "eligible",
                        "decision_reason": "first model bootstrap",
                        "created_at_utc": "2026-05-22T12:50:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (readiness_root / "promotion_readiness_record.json").write_text(
                json.dumps(
                    {
                        "contract_type": "promotion_readiness_record",
                        "promotion_readiness_record_id": "promready_fixture",
                        "created_at_utc": "2026-05-22T12:55:00Z",
                        "model_activation_performed": False,
                        "active_model_config_written": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:56:00Z")

        maintenance_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.maintenance")
        self.assertEqual(maintenance_task["status"], "succeeded")
        self.assertEqual(maintenance_task["task_state"], "completed")
        self.assertEqual(maintenance_task["receipt_count"], 1)
        self.assertEqual(maintenance_task["detail"]["progress"]["ready_count"], 1)
        self.assertEqual(maintenance_task["detail"]["progress"]["pending_count"], 0)
        self.assertTrue(maintenance_task["detail"]["progress"]["can_unlock_downstream"])

    def test_agent_error_summary_marks_repaired_smoke_closed(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            agent_root = tmp / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            request_root = agent_root / "erragent_smoke"
            request_root.mkdir(parents=True, exist_ok=True)
            diagnosis_path = request_root / "agent_error_diagnosis.json"
            diagnosis_path.write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_smoke",
                        "request_ref": "erragent_smoke",
                        "agent_ref": "trader",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps(
                            {
                                "result": {
                                    "payloads": [
                                        {
                                            "text": json.dumps(
                                                {
                                                    "diagnosis_status": "repaired",
                                                    "root_cause": "synthetic state was broken",
                                                    "repair_attempted": True,
                                                    "files_changed": ["02_control_plane/runtime/smoke/state.json"],
                                                    "verification": {"command": "python3 check_state.py", "exit_code": 0},
                                                    "retry_recommendation": "retry is safe",
                                                    "blockers": [],
                                                }
                                            )
                                        }
                                    ]
                                }
                            }
                        ),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T11:07:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 3,
                        "error_ref": "ERR-000003",
                        "error_fingerprint": "errfp_smoke",
                        "request_id": "erragent_smoke",
                        "request_path": "02_control_plane/runtime/agent_error_handling/erragent_smoke/server_error_agent_request.json",
                        "diagnosis_path": "02_control_plane/runtime/agent_error_handling/erragent_smoke/agent_error_diagnosis.json",
                        "source_component": "synthetic.agent_error_live_repair_smoke",
                        "source_repo": "trading-manager",
                        "error_scope": "server.synthetic_repair_smoke",
                        "error_kind": "synthetic_repair_required",
                        "severity": "warning",
                        "summary": "Synthetic auto-repair smoke",
                        "exit_code": 42,
                        "occurred_at_utc": "2026-05-18T11:06:37Z",
                        "created_at_utc": "2026-05-18T11:06:37Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T11:10:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(len(agent_errors), 1)
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000003")
        self.assertEqual(agent_errors[0]["diagnosis_status"], "completed")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
        self.assertEqual(agent_errors[0]["root_cause"], "synthetic state was broken")

    def test_agent_error_summary_parses_openclaw_agent_final_json(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            agent_root = tmp / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            request_root = agent_root / "erragent_openclaw"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "repaired_verified",
                "root_cause": {"summary": "type mismatch was repaired"},
                "repair_attempted": {"attempted": True},
                "files_changed": ["/repo/file.py"],
                "verification": [{"command": "tests", "exit_code": 0}],
                "retry_recommendation": "retry",
                "blockers": [],
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_openclaw",
                        "request_ref": "erragent_openclaw",
                        "agent_ref": "trader",
                        "runner_command": "openclaw_agent",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps({"result": {"meta": {"finalAssistantRawText": json.dumps(final_report)}}}),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T13:29:52Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 4,
                        "error_ref": "ERR-000004",
                        "error_fingerprint": "errfp_openclaw",
                        "request_id": "erragent_openclaw",
                        "request_path": "storage/runtime/agent_error_handling/erragent_openclaw/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_openclaw/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "stage failed",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T13:27:32Z",
                        "created_at_utc": "2026-05-18T13:27:32Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T13:30:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["runner_command"], "openclaw_agent")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "awaiting_retry")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "warning")
        self.assertEqual(agent_errors[0]["root_cause"], "type mismatch was repaired")

    def test_agent_error_summary_recovers_truncated_openclaw_stdout_and_closes_manual_review_repair(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_truncated"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "review_type": "server_error_repair",
                "error_ref": "ERR-000006",
                "diagnosis_status": "repaired_verified",
                "root_cause": "planner exposed layer_10_event_risk_governor.data_acquisition before event-feed coverage",
                "repair": {"repair_status": "repaired", "files_changed": ["/repo/planner.py"]},
                "retry_recommendation": "manual_review",
                "blockers": ["reviewed event-feed artifacts are still missing"],
            }
            truncated_stdout = 'truncated prefix "finalAssistantRawText": ' + json.dumps(json.dumps(final_report)) + ', "tail": true}'
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_truncated",
                        "request_ref": "erragent_truncated",
                        "agent_ref": "trader",
                        "runner_command": "openclaw_agent",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": truncated_stdout,
                        "stderr": "",
                        "completed_at_utc": "2026-05-21T12:30:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 6,
                        "error_ref": "ERR-000006",
                        "error_fingerprint": "errfp_truncated",
                        "request_id": "erragent_truncated",
                        "request_path": "storage/runtime/agent_error_handling/erragent_truncated/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_truncated/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage layer_10_event_risk_governor.data_acquisition command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-21T12:01:49Z",
                        "created_at_utc": "2026-05-21T12:01:49Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T12:31:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000006")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
        self.assertIn("event-feed coverage", agent_errors[0]["root_cause"])

    def test_agent_error_summary_closes_repaired_stage_after_successful_retry_receipt(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_retry_closed"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "repaired_awaiting_retry",
                "root_cause": "stage bug was repaired",
                "repair": {"repair_status": "repaired", "files_changed": ["/repo/file.py"]},
                "retry_recommendation": "wait for scheduler",
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_retry_closed",
                        "request_ref": "erragent_retry_closed",
                        "agent_ref": "trader",
                        "runner_command": "openclaw_agent",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps({"result": {"meta": {"finalAssistantRawText": json.dumps(final_report)}}}),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T13:29:52Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_dir = runtime / "model_training_stage_receipts" / "layer_04_event_failure_risk__model_generation"
            receipt_dir.mkdir(parents=True, exist_ok=True)
            (receipt_dir / "2026-05-21T112022.000000+0000.receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "layer_04_event_failure_risk.model_generation",
                        "status": "succeeded",
                        "completed_at": "2026-05-21T11:20:22Z",
                        "runs": [{"status": "succeeded", "return_code": 0}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 4,
                        "error_ref": "ERR-000004",
                        "error_fingerprint": "errfp_retry_closed",
                        "request_id": "erragent_retry_closed",
                        "request_path": "storage/runtime/agent_error_handling/erragent_retry_closed/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_retry_closed/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage layer_04_event_failure_risk.model_generation command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T13:27:32Z",
                        "created_at_utc": "2026-05-18T13:27:32Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T11:21:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
        self.assertIn("retry completed successfully", agent_errors[0]["retry_recommendation"])

    def test_supersedes_layer_nine_event_risk_error(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_10_event_risk_governor.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 10,
                                "layer_key": "layer_10_event_risk_governor",
                                "status": "blocked",
                                "last_reason": "waiting for upstream_layer_08_model_evaluation_complete",
                                "updated_utc": "2026-05-21T10:00:00Z",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_old_layer_nine"
            request_root.mkdir(parents=True, exist_ok=True)
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_old_layer_nine",
                        "request_ref": "erragent_old_layer_nine",
                        "agent_ref": "trader",
                        "runner_command": "safe_error_repair",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps(
                            {
                                "diagnosis_status": "completed",
                                "repair": {"repair_status": "not_supported"},
                                "root_cause": "model training stage layer_09_event_risk_governor.data_acquisition command returned non-zero status",
                                "retry_recommendation": "manual review",
                            }
                        ),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T10:41:07Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 1,
                        "error_ref": "ERR-000001",
                        "error_fingerprint": "errfp_old_layer_nine",
                        "request_id": "erragent_old_layer_nine",
                        "request_path": "storage/runtime/agent_error_handling/erragent_old_layer_nine/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_old_layer_nine/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage layer_09_event_risk_governor.data_acquisition command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T10:41:07Z",
                        "created_at_utc": "2026-05-18T10:41:07Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T10:00:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000001")
        self.assertEqual(agent_errors[0]["repair_status"], "superseded")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
        self.assertIn("layer_10_event_risk_governor", agent_errors[0]["retry_recommendation"])

    def test_active_scheduler_no_executable_backoff_is_running_not_error(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2021-10.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2021-10",
                        "end_month": "2021-10",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "updated_utc": "2026-05-18T10:46:52Z",
                                "last_reason": "stage execution started by manager stage executor",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps({"current_month": "2021-10", "start_month": "2021-10", "end_month": "2021-10"}) + "\n",
                encoding="utf-8",
            )
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            decision_log.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_decision",
                        "decision_status": "backoff",
                        "start_month": "2021-10",
                        "selected_work": "layer_03_target_state_vector.feature_generation",
                        "reason": "no executable scheduler-owned workflow stage is currently available",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T10:47:42Z")

        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["severity"], "info")
        self.assertIn("Historical scheduler is running", payload["summary"])
        self.assertFalse(any(ref.get("issue_type") == "historical_workflow_blocked" for ref in payload["issue_refs"]))


    def test_terminal_task_without_recorded_timing_is_not_backfilled_from_status_update(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2019-04.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2019-04",
                        "end_month": "2019-04",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                                "updated_utc": "2026-05-12T10:00:00Z",
                                "receipt_refs": ["02_control_plane/runtime/stage_coverage/example.json"],
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps({"current_month": "2019-05", "last_completed_months": ["2019-04"]}) + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2019-fold1")
        self.assertEqual(task["task_state"], "completed")
        self.assertIsNone(task["created_at_utc"])
        self.assertIsNone(task["started_at_utc"])
        self.assertIsNone(task["ended_at_utc"])
        self.assertEqual(task["status_updated_at_utc"], "2026-05-12T10:00:00Z")

    def test_task_timeline_includes_completed_month_groups_before_current_month(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2019-04.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2019-04",
                        "end_month": "2019-04",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_workflow_state_2019-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2019-06",
                        "end_month": "2019-06",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2019-06",
                        "end_month": "2019-06",
                        "last_completed_months": ["2019-04", "2019-05"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        task_timeline = payload["chart_payload"]["task_timeline"]
        self.assertEqual([task["month"] for task in task_timeline], ["2019-fold1"])
        self.assertEqual([task["task_state"] for task in task_timeline], ["completed"])

    def test_task_timeline_uses_durable_month_inventory_and_continuous_numbers(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2018-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2018-01",
                        "end_month": "2018-01",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2019-01",
                        "end_month": "2019-01",
                        "current_month": "2019-01",
                        "last_completed_months": ["2017-12"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        tasks = payload["chart_payload"]["task_timeline"]
        durable_task = next(task for task in tasks if task["month"] == "2018-fold1")
        self.assertEqual(durable_task["task_number"], durable_task["sequence"])
        self.assertEqual(durable_task["task_number"], 1)
        self.assertEqual(durable_task["task_uid"], "2018-01..2018-06:layer_01_market_regime.data_acquisition")

    def test_task_timeline_shows_fold_target_chain_prep_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_01_market_regime.model_generation",
                                "stage_type": "model_generation",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_02_sector_context.model_generation",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "layer_02_sector_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_workflow_state_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-06",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2016-07",
                        "end_month": "2016-07",
                        "current_month": "2016-07",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            write_task_progress_node(
                progress_root=runtime / "task_progress",
                worker_id="model_worker_1",
                task_uid="2016-01..2016-06:layer_03_target_state_vector.data_acquisition",
                stage_id="layer_03_target_state_vector.data_acquisition",
                unit_label="rows",
                processed_count=40,
                expected_count=100,
                node_id="materialize_rows",
                node_label="Materializing source rows",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        fold_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-fold1"]
        self.assertEqual([task["stage_type"] for task in fold_tasks], ["data_acquisition", "model_generation", "model_generation", "data_acquisition"])
        self.assertEqual([task["task_number"] for task in fold_tasks], [1, 2, 3, 4])
        self.assertEqual([task["sequence"] for task in fold_tasks], [1, 2, 3, 4])
        self.assertEqual(fold_tasks[0]["task_uid"], "2016-01..2016-06:layer_01_market_regime.data_acquisition")
        self.assertEqual(fold_tasks[0]["detail"]["child_partitions"], ["2016-01", "2016-02", "2016-03", "2016-04", "2016-05", "2016-06"])
        self.assertIsNone(fold_tasks[1]["detail"]["progress"])
        self.assertIsNone(fold_tasks[2]["detail"]["progress"])
        fold_prep_tasks = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["task_id"] == "layer_03_target_state_vector.data_acquisition"
        ]
        self.assertEqual([task["month"] for task in fold_prep_tasks], ["2016-fold1"])
        timeline_months = [task["month"] for task in payload["chart_payload"]["task_timeline"]]
        self.assertIn("2016-fold1", timeline_months)
        self.assertEqual(fold_prep_tasks[0]["worker_label"], "Model Worker 1")
        self.assertEqual(fold_prep_tasks[0]["dataset_unit_months"], None)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["ready_count"], 40)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["expected_count"], 100)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["unit_label"], "rows")

    def test_task_timeline_prefers_selected_target_fold_over_stale_untargeted_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "blocked",
                                "last_reason": "waiting for selected_target_symbol_required",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "last_reason": "stage completed by manager stage executor",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({"current_month": "2016-07", "start_month": "2016-07"}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-27T07:40:00Z")

        task = next(
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["month"] == "2016-fold1" and task["task_id"] == "layer_03_target_state_vector.feature_generation"
        )
        self.assertEqual(task["status"], "succeeded")
        self.assertEqual(task["target_symbol"], "AAPL")

    def test_task_timeline_places_fold_after_ending_month(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            for month in ("2016-06", "2016-12"):
                (runtime / f"model_training_workflow_state_{month}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_model_training_workflow_state",
                            "start_month": month,
                            "end_month": month,
                            "stages": [
                                {
                                    "stage_id": "layer_01_market_regime.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 1,
                                    "layer_key": "layer_01_market_regime",
                                    "status": "succeeded",
                                }
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            for start, end in (("2016-01", "2016-06"), ("2016-07", "2016-12")):
                (runtime / f"model_training_fold_state_{start}_{end}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_model_training_workflow_state",
                            "start_month": start,
                            "end_month": end,
                            "stages": [
                                {
                                    "stage_id": "layer_01_market_regime.model_generation",
                                    "stage_type": "model_generation",
                                    "layer": 1,
                                    "layer_key": "layer_01_market_regime",
                                    "status": "succeeded",
                                }
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2017-01",
                        "end_month": "2017-01",
                        "current_month": "2017-01",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        ordered_months = [task["month"] for task in payload["chart_payload"]["task_timeline"]]
        self.assertLess(ordered_months.index("2016-fold1"), ordered_months.index("2016-fold2"))

    def test_current_incomplete_fold_is_not_exposed_as_ready_task(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2026-05.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2026-05",
                        "end_month": "2026-05",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2026-05",
                        "end_month": "2026-05",
                        "current_month": "2026-05",
                        "last_completed_months": ["2026-05"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            with patch(
                "trading_manager_tasks.dashboard_read_models.completed_historical_month_cutoff",
                return_value="2026-04",
            ):
                payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-14T12:00:00Z")

        task_timeline = payload["chart_payload"]["task_timeline"]
        self.assertFalse(any(task["month"] == "2026-05" for task in task_timeline))
        self.assertFalse(any(task["month"] == "2026-fold1" for task in task_timeline))
        self.assertIsNone(payload["chart_payload"]["current_month"])

    def test_task_timeline_omits_nonexistent_no_feature_layer_input_tasks(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2019-04.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2019-04",
                        "end_month": "2019-04",
                        "stages": [
                            {
                                "stage_id": "layer_05_alpha_confidence.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 5,
                                "layer_key": "layer_05_alpha_confidence",
                                "status": "not_applicable",
                            },
                            {
                                "stage_id": "layer_05_alpha_confidence.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 5,
                                "layer_key": "layer_05_alpha_confidence",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_05_alpha_confidence.model_generation",
                                "stage_type": "model_generation",
                                "layer": 5,
                                "layer_key": "layer_05_alpha_confidence",
                                "status": "blocked",
                            },
                            {
                                "stage_id": "layer_09_option_expression.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 8,
                                "layer_key": "layer_09_option_expression",
                                "status": "not_applicable",
                                "last_reason": "no active Layer 8 target chain ready for option-expression expansion",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({"current_month": "2019-04", "last_completed_months": ["2019-04"]}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        task_timeline = payload["chart_payload"]["task_timeline"]
        self.assertFalse(
            any(task["layer"] == 5 and task["stage_type"] in {"data_acquisition", "feature_generation"} for task in task_timeline)
        )
        self.assertTrue(any(task["layer"] == 5 and task["stage_type"] == "model_generation" for task in task_timeline))
        real_skip = next(task for task in task_timeline if task["task_id"] == "layer_09_option_expression.data_acquisition")
        self.assertEqual(real_skip["task_state"], "skipped")
        self.assertIn("no active Layer 8", real_skip["reason"])

    def test_planned_task_timeline_uses_service_target_symbol(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\n"
                "TRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2019-05",
                        "end_month": "2019-05",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        self.assertFalse(any(task["layer"] == 3 for task in payload["chart_payload"]["task_timeline"]))

    def test_task_timeline_marks_three_month_ingest_lane_heads_current(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            for month in ("2017-01", "2017-02", "2017-03", "2017-04"):
                (runtime / f"model_training_workflow_state_{month}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_model_training_workflow_state",
                            "start_month": month,
                            "end_month": month,
                            "stages": [
                                {
                                    "stage_id": "layer_01_market_regime.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 1,
                                    "layer_key": "layer_01_market_regime",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "layer_01_market_regime.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 1,
                                    "layer_key": "layer_01_market_regime",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "layer_02_sector_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 2,
                                    "layer_key": "layer_02_sector_context",
                                    "status": "ready",
                                },
                                {
                                    "stage_id": "layer_02_sector_context.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 2,
                                    "layer_key": "layer_02_sector_context",
                                    "status": "blocked",
                                },
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2017-01",
                        "end_month": "2017-01",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        current_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["task_state"] == "current"]
        self.assertEqual([task["month"] for task in current_tasks], ["2017-fold1"])
        self.assertEqual([task["worker_id"] for task in current_tasks], ["model_worker_1"])
        self.assertTrue(all(task["task_id"] == "layer_02_sector_context.data_acquisition" for task in current_tasks))

    def test_task_timeline_advances_after_completed_foundation_months(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            for month in ("2020-09", "2020-10", "2020-11", "2020-12"):
                (runtime / f"model_training_workflow_state_{month}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_model_training_workflow_state",
                            "start_month": month,
                            "end_month": month,
                            "stages": [
                                {
                                    "stage_id": "layer_01_market_regime.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 1,
                                    "layer_key": "layer_01_market_regime",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "layer_01_market_regime.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 1,
                                    "layer_key": "layer_01_market_regime",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "layer_02_sector_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 2,
                                    "layer_key": "layer_02_sector_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "layer_02_sector_context.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 2,
                                    "layer_key": "layer_02_sector_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "layer_03_target_state_vector.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 3,
                                    "layer_key": "layer_03_target_state_vector",
                                    "status": "ready",
                                },
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_daemon_state",
                        "start_month": "2020-09",
                        "end_month": "2020-09",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-14T12:00:00Z")

        current_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["task_state"] == "current"]
        self.assertEqual(current_tasks, [])

    def test_task_timeline_marks_ready_model_fold_current_not_blocked_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_2016-07_2016-12.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-07",
                        "end_month": "2016-12",
                        "stages": [
                            {
                                "stage_id": "layer_10_event_risk_governor.model_generation",
                                "stage_type": "model_generation",
                                "layer": 9,
                                "layer_key": "layer_10_event_risk_governor",
                                "status": "blocked",
                                "last_reason": "waiting for layer_10_event_risk_governor.feature_or_input_ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_2017-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.model_generation",
                                "stage_type": "model_generation",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T12:00:00Z")

        current_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["task_state"] == "current"]
        self.assertIn(("2017-fold1", "layer_01_market_regime.model_generation"), [(task["month"], task["task_id"]) for task in current_tasks])
        blocked_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-fold2")
        self.assertEqual(blocked_task["task_state"], "future")

    def test_task_timeline_exposes_missing_start_month_gap_before_later_work(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_workflow_state_2016-02.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-02",
                        "end_month": "2016-02",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_01_market_regime.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_02_sector_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "layer_02_sector_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_02_sector_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "layer_02_sector_context",
                                "status": "succeeded",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T12:00:00Z")

        current_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["task_state"] == "current"]
        self.assertEqual(current_tasks, [])

    def test_task_timeline_uses_latest_model_worker_fold_for_current_task(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_01_market_regime.model_evaluation",
                                "stage_type": "model_evaluation",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aaoi_2016-07_2016-12.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-07",
                        "end_month": "2016-12",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAOI",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-07_2016-12.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-07",
                        "end_month": "2016-12",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            decision_log.parent.mkdir(parents=True, exist_ok=True)
            decision_log.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_decision",
                        "decision_status": "executed",
                        "selected_work": "layer_03_target_state_vector.data_acquisition",
                        "execution_summary": {
                            "workflow_plan": {
                                "start_month": "2016-07",
                                "end_month": "2016-12",
                                "selected_target_symbol": "AAPL",
                            },
                            "stage_execution": {
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "status": "succeeded",
                                "return_code": 0,
                            }
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T11:34:00Z")

        current_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["task_state"] == "current"]
        self.assertIn(
            ("2016-fold2", "layer_03_target_state_vector.feature_generation", "AAPL", "Model Worker 1"),
            [(task["month"], task["task_id"], task["target_symbol"], task["worker_label"]) for task in current_tasks],
        )
        self.assertNotIn(
            ("2016-fold1", "layer_01_market_regime.model_evaluation"),
            [(task["month"], task["task_id"]) for task in current_tasks],
        )

    def test_task_timeline_does_not_fallback_to_older_fold_when_latest_fold_has_no_ready_head(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "layer_09_option_expression.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 9,
                                "layer_key": "layer_09_option_expression",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-07_2016-12.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-07",
                        "end_month": "2016-12",
                        "stages": [
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "blocked",
                                "last_reason": "stage command is currently running outside checkpoint state",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            decision_log.parent.mkdir(parents=True, exist_ok=True)
            decision_log.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_scheduler_decision",
                        "decision_status": "executed",
                        "selected_work": "layer_03_target_state_vector.feature_generation",
                        "execution_summary": {
                            "workflow_plan": {
                                "start_month": "2016-07",
                                "end_month": "2016-12",
                                "selected_target_symbol": "AAPL",
                            },
                            "stage_execution": {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "status": "succeeded",
                                "return_code": 0,
                            },
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-21T11:45:00Z")

        current_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["task_state"] == "current"]
        self.assertNotIn(
            ("2016-fold1", "layer_09_option_expression.feature_generation"),
            [(task["month"], task["task_id"]) for task in current_tasks],
        )

    def test_cli_builds_payload(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)

            from scripts.tasks.build_historical_task_progress_summary import main

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(
                    [
                        "--storage-root",
                        str(tmp / "storage"),
                        "--state-path",
                        str(tmp / "runtime" / "historical_scheduler_state.json"),
                        "--lock-path",
                        str(tmp / "runtime" / "historical_scheduler.lock"),
                        "--decision-log-path",
                        str(tmp / "runtime" / "historical_scheduler_decisions.jsonl"),
                        "--service-template-path",
                        str(service),
                        "--service-env-path",
                        str(env),
                        "--daemon-wrapper-path",
                        str(wrapper),
                    ]
                )

        self.assertEqual(result, 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["contract_type"], "historical_task_progress_summary")
        self.assertIn("chart_payload", payload)


if __name__ == "__main__":
    unittest.main()

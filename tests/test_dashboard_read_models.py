from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.dashboard_read_models import (
    _agent_errors_for_task,
    _attach_task_error_context,
    _task_error_intervention_status,
    build_historical_task_progress_summary,
)
from trading_manager_tasks.scheduler_status import collect_historical_scheduler_status
from trading_manager_tasks.task_progress import write_task_progress_node


class DashboardReadModelProducerTests(unittest.TestCase):
    def test_task_error_intervention_prioritizes_open_diagnosis_over_awaiting_retry(self):
        status = _task_error_intervention_status(
            task={},
            failure_rows=[],
            agent_errors=[
                {"handling_status": "awaiting_retry", "repair_status": "repaired"},
                {"handling_status": "open", "repair_status": "unknown"},
            ],
        )

        self.assertEqual(status, "agent_diagnosis_open")

    def test_task_agent_errors_sort_open_before_awaiting_retry(self):
        rows = [
            {
                "error_number": 3,
                "handling_status": "awaiting_retry",
                "repair_status": "repaired",
                "summary": "model training stage layer_09_option_expression.data_acquisition command returned non-zero status",
            },
            {
                "error_number": 6,
                "handling_status": "open",
                "repair_status": "unknown",
                "summary": "provider stage layer_09_option_expression.data_acquisition has failed requests requiring agent review",
            },
        ]
        task = {"task_id": "layer_09_option_expression", "detail": {"active_stage_id": "layer_09_option_expression.data_acquisition"}}

        ordered = _agent_errors_for_task(rows, task)

        self.assertEqual([row["error_number"] for row in ordered], [6, 3])

    def test_task_error_context_closes_nonblocking_awaiting_retry(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            task = {
                "task_id": "layer_09_option_expression",
                "task_state": "current",
                "status": "ready",
                "detail": {
                    "active_stage_id": "layer_09_option_expression.data_acquisition",
                    "progress": {"failed_count": 0, "accepted_failed_count": 0},
                },
            }
            rows = [
                {
                    "error_number": 3,
                    "error_ref": "ERR-000003",
                    "handling_status": "awaiting_retry",
                    "repair_status": "repaired",
                    "summary": "model training stage layer_09_option_expression.data_acquisition command returned non-zero status",
                }
            ]

            updated = _attach_task_error_context([task], storage_root=Path(raw_tmp), agent_errors=rows)

        detail = updated[0]["detail"]
        self.assertEqual(detail["agent_error_summary"][0]["handling_status"], "closed")
        self.assertEqual(detail["agent_error_summary"][0]["dashboard_severity"], "notice")
        self.assertNotIn("repair_intervention_status", detail)
        self.assertEqual(detail.get("blockers", []), [])

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

    def _write_post_replay_attribution_receipt(self, replay_root: Path) -> None:
        receipt_root = replay_root / "post_replay_attribution_runs" / "fixture"
        receipt_root.mkdir(parents=True, exist_ok=True)
        (receipt_root / "post_replay_attribution_receipt.json").write_text(
            json.dumps(
                {
                    "contract_type": "post_replay_event_attribution_receipt",
                    "status": "succeeded",
                    "created_at_utc": "2026-05-22T12:49:00Z",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_completed_pre_replay_fold(self, runtime: Path, *, symbol: str = "AAPL") -> Path:
        fold_state = runtime / f"model_training_fold_state_{symbol.lower()}_2016-01_2016-06.json"
        fold_state.parent.mkdir(parents=True, exist_ok=True)
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
                        "dataset_unit": {
                            "unit_kind": "six_month_target_fold",
                            "unit_months": 6,
                            "start_month": "2016-01",
                            "end_month": "2016-06",
                            "target_required": layer >= 3,
                            "target_symbol": symbol if layer >= 3 else None,
                        },
                    }
                )
        fold_state.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return fold_state

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
        model_tasks = [task for task in task_timeline if task["stage_type"] == "model_task"]
        lifecycle_tasks = [task for task in task_timeline if str(task["task_id"]).startswith("model_group.")]
        self.assertEqual([task["task_state"] for task in model_tasks], ["completed", "failed"])
        self.assertEqual(lifecycle_tasks, [])
        self.assertEqual(task_timeline[1]["task_label"], "Layer 3 Target State Vector Model")
        self.assertEqual(task_timeline[1]["month"], "2019-fold1")
        self.assertEqual(task_timeline[1]["detail"]["child_partitions"], ["2019-01", "2019-02", "2019-03", "2019-04", "2019-05", "2019-06"])
        self.assertEqual(task_timeline[1]["detail"]["last_execution"]["return_code"], 1)
        self.assertEqual(task_timeline[0]["worker_id"], "model_worker_1")
        self.assertEqual(task_timeline[0]["detail"]["worker"]["worker_label"], "Model Worker 1")
        self.assertEqual(task_timeline[1]["stage_type"], "model_task")
        self.assertEqual(task_timeline[1]["detail"]["active_stage_id"], "layer_03_target_state_vector.data_acquisition")
        self.assertIsNone(task_timeline[0]["created_at_utc"])
        self.assertEqual(task_timeline[0]["started_at_utc"], "2026-05-12T09:00:00Z")
        self.assertEqual(task_timeline[0]["ended_at_utc"], "2026-05-12T09:30:00Z")
        self.assertEqual(task_timeline[0]["status_updated_at_utc"], "2026-05-12T10:00:00Z")
        self.assertEqual(task_timeline[0]["detail"]["progress"]["ready_count"], 3)
        self.assertEqual(task_timeline[1]["detail"]["progress"]["unit_label"], "source-month requests")
        self.assertEqual(task_timeline[1]["detail"]["progress"]["expected_count"], 6)
        self.assertEqual(task_timeline[1]["detail"]["progress"]["pending_count"], 6)
        self.assertIn("Layer 2 feed artifacts", payload["chart_payload"]["last_stage_execution"]["failure_detail"])
        self.assertTrue(any(ref.get("issue_type") == "historical_stage_execution_failed" for ref in payload["issue_refs"]))
        self.assertTrue(any(ref.get("ref_type") == "manager_stage_execution_summary" for ref in payload["diagnostic_refs"]))
        self.assertIn("profile_refs", payload)
        self.assertIn("lineage_refs", payload)
        self.assertIn(payload["severity"], {"critical", "high", "medium", "low", "info"})

    def test_task_timeline_attaches_status_level_progress_when_no_finer_counter_exists(self):
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
                                "stage_id": "scheduler_control.maintenance",
                                "stage_type": "maintenance",
                                "status": "ready",
                                "last_reason": "ready for maintenance handoff",
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

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "scheduler_control.maintenance")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "stage_status")
        self.assertEqual(progress["expected_count"], 1)
        self.assertEqual(progress["ready_count"], 0)
        self.assertEqual(progress["pending_count"], 1)
        self.assertEqual(progress["unit_label"], "task")

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
                task_uid="2020-07..2020-12:layer_09_option_expression.data_acquisition",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_09_option_expression")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["blocker_count"], 0)
        self.assertEqual(task["detail"]["blockers"], [])
        self.assertEqual(task["detail"]["progress"]["expected_count"], 1)
        self.assertEqual(task["detail"]["progress"]["ready_count"], 0)
        self.assertEqual(task["detail"]["progress"]["pending_count"], 1)
        self.assertEqual(task["detail"]["progress"]["unit_label"], "option gate")

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

        self.assertFalse(
            any(task["task_id"] == "layer_09_option_expression" for task in payload["chart_payload"]["task_timeline"])
        )

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
        self.assertIsNone(payload["chart_payload"]["active_stage"])
        self.assertIn("internal_active_stage", payload["chart_payload"])
        self.assertIn("runtime_active_work", payload["chart_payload"])


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
                        "feed_acquisition_count": 300,
                        "available_feed_acquisition_count": 120,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 180,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "source_contract_ref": "trading-evaluation/replays/promotion_replay_candidate_policy.json",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "coverage_summary.csv").write_text(
                "contract_id,source_id,required_acquisition_count,available_acquisition_count,deferred_acquisition_count,missing_acquisition_count,coverage_status,notes\n"
                "promotion_replay_candidate_policy,alpaca_bars,60,0,0,60,incomplete,missing\n"
                "promotion_replay_candidate_policy,alpaca_liquidity,60,0,0,60,incomplete,missing\n"
                "promotion_replay_candidate_policy,alpaca_news,60,0,0,60,incomplete,missing\n"
                "promotion_replay_candidate_policy,gdelt_news,60,60,0,0,complete,available\n"
                "promotion_replay_candidate_policy,trading_economics_calendar_web,60,60,0,0,complete,available\n",
                encoding="utf-8",
            )
            (replay_root / "replay_window_manifest.csv").write_text(
                "contract_id,replay_mode,start_date,end_date,min_trading_days,candidate_policy_ref,replay_route_ref,market_condition_tags,selection_metric_refs\n"
                "promotion_replay_candidate_policy,candidate_policy_replay,2021-01-01,2026-01-01,1255,candidate,route,tags,metrics\n",
                encoding="utf-8",
            )
            feed_fields = [
                "acquisition_id",
                "contract_id",
                "source_id",
                "feed",
                "target_ref",
                "asset_class",
                "instrument_type",
                "month",
                "start_date",
                "end_date_exclusive",
                "timeframe",
                "acquisition_mode",
                "output_root",
                "expected_output_ref",
                "coverage_status",
                "coverage_receipt_path",
                "params_json",
                "notes",
            ]
            source_rows = [
                ("alpaca_bars", "01_feed_alpaca_bars", "AAPL", "missing"),
                ("alpaca_liquidity", "02_feed_alpaca_liquidity", "AAPL", "missing"),
                ("alpaca_news", "03_feed_alpaca_news", "AAPL", "missing"),
                ("gdelt_news", "05_feed_gdelt_news", "", "available"),
                ("trading_economics_calendar_web", "07_feed_trading_economics_calendar_web", "", "available"),
            ]
            feed_rows = [",".join(feed_fields)]
            for offset in range(60):
                year = 2021 + offset // 12
                month_number = 1 + offset % 12
                month = f"{year}-{month_number:02d}"
                next_year = year + (1 if month_number == 12 else 0)
                next_month_number = 1 if month_number == 12 else month_number + 1
                start_date = f"{month}-01"
                end_date = f"{next_year}-{next_month_number:02d}-01"
                for source_id, feed, target_ref, coverage_status in source_rows:
                    acquisition_id = f"acq_{source_id}_{month.replace('-', '_')}"
                    output_root = f"/tmp/replay/{source_id}/{month}"
                    receipt_path = f"{output_root}/completion_receipt.json"
                    feed_rows.append(
                        ",".join(
                            [
                                acquisition_id,
                                "promotion_replay_candidate_policy",
                                source_id,
                                feed,
                                target_ref,
                                "equity",
                                "stock",
                                month,
                                start_date,
                                end_date,
                                "1Min",
                                "monthly_replay_source_acquisition",
                                output_root,
                                "",
                                coverage_status,
                                receipt_path,
                                "{}",
                                "",
                            ]
                        )
                    )
            (replay_root / "feed_acquisition_plan.csv").write_text("\n".join(feed_rows) + "\n", encoding="utf-8")
            self._write_completed_pre_replay_fold(tmp / "storage" / "02_control_plane" / "runtime", symbol="AAPL")
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
        self.assertEqual([task["task_id"] for task in evaluation_tasks], ["model_group.replay"])
        self.assertEqual([task["stage_type"] for task in evaluation_tasks], ["replay"])
        self.assertTrue(all(task["worker_id"] == "evaluation_worker_1" for task in evaluation_tasks))
        self.assertTrue(all(task["layer_key"] == "model_group" for task in evaluation_tasks))
        self.assertTrue(all(task["month"] == "2016-fold1" for task in evaluation_tasks))
        self.assertTrue(all(task["dataset_unit_kind"] == "model_group_training_fold" for task in evaluation_tasks))
        self.assertTrue(all(task["dataset_unit_months"] == 6 for task in evaluation_tasks))
        self.assertEqual(evaluation_tasks[0]["detail"]["dataset_unit"]["start_month"], "2016-01")
        self.assertEqual(evaluation_tasks[0]["detail"]["dataset_unit"]["end_month"], "2016-06")
        self.assertEqual(evaluation_tasks[0]["detail"]["dataset_unit"]["unit_months"], 6)
        self.assertEqual(evaluation_tasks[0]["detail"]["replay_window"]["start_month"], "2021-01")
        self.assertEqual(evaluation_tasks[0]["detail"]["replay_window"]["end_month"], "2026-01")
        self.assertEqual(evaluation_tasks[0]["detail"]["replay_window"]["unit_months"], 60)
        self.assertEqual(evaluation_tasks[0]["task_label"], "Model Replay")
        self.assertEqual(evaluation_tasks[0]["task_state"], "current")
        self.assertEqual(evaluation_tasks[0]["status"], "blocked")
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["expected_count"], 60)
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["pending_count"], 60)
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["unit_label"], "replay months")
        self.assertEqual(evaluation_tasks[0]["detail"]["progress"]["progress_source"], "replay_dataset_month_operations")
        self.assertEqual(evaluation_tasks[0]["detail"]["blockers"], ["replay_month_operation_complete"])
        self.assertIn("Replay month 2021-01 is incomplete", evaluation_tasks[0]["reason"])
        self.assertEqual(evaluation_tasks[0]["detail"]["replay_month_operation"]["month"], "2021-01")
        self.assertEqual(evaluation_tasks[0]["detail"]["replay_month_operation"]["source_count"], 5)
        self.assertEqual(
            evaluation_tasks[0]["detail"]["replay_month_operation"]["missing_source_ids"],
            ["alpaca_bars", "alpaca_liquidity", "alpaca_news"],
        )
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.replay")
        self.assertEqual(payload["chart_payload"]["current_month"], "2016-fold1")
        self.assertEqual(payload["chart_payload"]["active_task"]["worker_id"], "evaluation_worker_1")
        self.assertEqual(payload["chart_payload"]["internal_active_stage"], payload["chart_payload"]["active_stage"])

    def test_task_timeline_shows_model_group_lifecycle_after_layer_nine_completes_before_replay_manifest(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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

        model_group_tasks = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if str(task["task_id"]).startswith("model_group.")
        ]
        self.assertEqual([task["task_id"] for task in model_group_tasks], ["model_group.replay"])
        self.assertEqual(model_group_tasks[0]["task_state"], "current")
        self.assertEqual(model_group_tasks[0]["status"], "blocked")
        self.assertEqual(model_group_tasks[0]["detail"]["blockers"], ["replay_dataset_preparation_manifest"])
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.replay")

    def test_task_timeline_shows_fixed_model_group_lifecycle_for_first_open_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
            fold2 = runtime / "model_training_fold_state_aapl_2016-07_2016-12.json"
            fold2.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-07",
                        "end_month": "2016-12",
                        "stages": [
                            {
                                "stage_id": f"layer_{layer:02d}_fixture.model_generation",
                                "stage_type": "model_generation",
                                "layer": layer,
                                "layer_key": f"layer_{layer:02d}_fixture",
                                "status": "succeeded" if layer <= 2 else "blocked",
                                "last_reason": "waiting for pre-replay input" if layer > 2 else "stage complete",
                                "dataset_unit": {
                                    "unit_kind": "six_month_target_fold",
                                    "unit_months": 6,
                                    "start_month": "2016-07",
                                    "end_month": "2016-12",
                                    "target_required": layer >= 3,
                                    "target_symbol": "AAPL" if layer >= 3 else None,
                                },
                            }
                            for layer in range(1, 10)
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

        fold1_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-fold1"]
        fold2_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-fold2"]
        self.assertEqual(len(fold1_tasks), 10)
        self.assertEqual(fold2_tasks, [])
        self.assertEqual(fold1_tasks[-1]["task_id"], "model_group.replay")
        self.assertEqual(fold1_tasks[-1]["task_state"], "current")
        self.assertEqual(fold1_tasks[-1]["detail"]["blockers"], ["replay_dataset_preparation_manifest"])

    def test_ready_model_group_replay_becomes_active_after_pre_replay_fold(self):
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
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
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
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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
        self.assertEqual(replay_task["task_state"], "current")
        self.assertEqual(replay_task["detail"]["blockers"], [])
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.replay")
        self.assertEqual(payload["chart_payload"]["current_month"], "2016-fold1")

    def test_wrong_fold_replay_dataset_does_not_unlock_model_group_replay(self):
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
                        "candidate_fold_id": "2016-fold2",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 60,
                        "available_feed_acquisition_count": 60,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 0,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
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
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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
        self.assertEqual(replay_task["status"], "blocked")
        self.assertEqual(replay_task["detail"]["blockers"], ["replay_dataset_scope_matches_training_fold"])
        self.assertIn("does not match completed training fold", replay_task["reason"])

    def test_replay_completion_surfaces_layer_ten_ready_despite_internal_lifecycle_hold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 2,
                        "available_feed_acquisition_count": 2,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 0,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "feed_acquisition_plan.csv").write_text("month\n2021-01\n2021-02\n", encoding="utf-8")
            (replay_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "fixture", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "fixture", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            replay_run = replay_root / "replay_execution_runs" / "fixture"
            replay_run.mkdir(parents=True)
            decision_rows_path = replay_run / "decision_rows.jsonl"
            decision_rows_path.write_text(
                "\n".join(
                    [
                        json.dumps({"decision_status": "rejected", "fill_status": "simulated_rejected", "outcome_label": 1}),
                        json.dumps(
                            {
                                "decision_status": "approved",
                                "fill_status": "simulated_filled",
                                "outcome_label": 0,
                                "realized_return": -0.02,
                                "baseline_return": 0.0,
                            }
                        ),
                        json.dumps({"decision_status": "rejected", "fill_status": "simulated_rejected", "outcome_label": 0}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_run / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "fixture",
                        "candidate_model_ref": "storage://trading-manager/model_group/2016-01_2016-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "validation_status": "passed",
                        "generated_at_utc": "2026-05-22T12:30:00Z",
                        "decision_rows_ref": str(decision_rows_path),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:31:00Z")

        self.assertEqual(status.current_stage, "model_group.replay")
        self.assertEqual(status.blocked_reason, "waiting_for_model_group_lifecycle_tasks")
        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        layer_ten_task = next(
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["task_id"] == "model_group.model_10_event_risk_governor"
        )
        self.assertEqual(replay_task["status"], "succeeded")
        self.assertEqual(replay_task["task_state"], "completed")
        self.assertEqual(layer_ten_task["status"], "ready")
        self.assertEqual(layer_ten_task["task_state"], "current")
        self.assertEqual(layer_ten_task["detail"]["progress"]["unit_label"], "failure attributions")
        self.assertEqual(layer_ten_task["detail"]["progress"]["expected_count"], 2)
        self.assertEqual(layer_ten_task["detail"]["progress"]["ready_count"], 0)
        self.assertEqual(layer_ten_task["detail"]["progress"]["pending_count"], 2)
        self.assertEqual(layer_ten_task["detail"]["progress"]["progress_source"], "replay_failure_attribution_units")
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.model_10_event_risk_governor")
        self.assertEqual(payload["chart_payload"]["blocker_category"], None)
        self.assertEqual(payload["status"], "running")
        self.assertIn("Layer 10 Event Risk Governor", payload["summary"])
        self.assertNotIn("blocked at model_group.replay", payload["summary"])
        self.assertFalse(
            any(ref.get("issue_id") == "model_group.replay" and ref.get("summary") == "waiting_for_model_group_lifecycle_tasks" for ref in payload["issue_refs"])
        )

    def test_legacy_unsplit_fold_hides_stale_replay_lifecycle_artifacts(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 2,
                        "available_feed_acquisition_count": 2,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 0,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
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
            self._write_post_replay_attribution_receipt(replay_root)
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
                                "stage_id": f"layer_{layer:02d}_fixture.model_generation",
                                "stage_type": "model_generation",
                                "layer": layer,
                                "layer_key": f"layer_{layer:02d}_fixture",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "six_month_target_fold",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_symbol": "AAPL" if layer >= 3 else None,
                                },
                            }
                            for layer in range(1, 10)
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:32:00Z")

        task_ids = {task["task_id"] for task in payload["chart_payload"]["task_timeline"]}
        self.assertNotIn("model_group.replay", task_ids)
        self.assertNotIn("model_group.model_10_event_risk_governor", task_ids)
        self.assertNotEqual(payload["chart_payload"]["active_stage"], "model_group.model_10_event_risk_governor")

    def test_data_acquisition_progress_aggregates_fold_source_month_requests(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            fold_state = runtime / "model_training_fold_state_aapl_2016-01_2016-06.json"
            fold_state.write_text(
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
                                "status": "ready",
                                "dataset_unit": {
                                    "unit_kind": "six_month_panel",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": False,
                                },
                            },
                            {
                                "stage_id": "layer_01_market_regime.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "blocked",
                                "blockers": ["layer_01_market_regime.data_acquisition_complete"],
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            coverage_root = runtime / "stage_coverage"
            coverage_root.mkdir(parents=True)
            for month, ready_count in [("2016-01", 3), ("2016-02", 5), ("2016-03", 0)]:
                (coverage_root / f"layer_01_market_regime_data_acquisition_{month}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_stage_coverage",
                            "stage_id": "layer_01_market_regime.data_acquisition",
                            "start_month": month,
                            "end_month": month,
                            "expected_count": 10,
                            "ready_count": ready_count,
                            "pending_count": 10 - ready_count,
                            "failed_count": 0,
                            "accepted_failed_count": 0,
                            "status": "partial_ready",
                            "can_unlock_downstream": False,
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps({"current_month": "2016-01", "start_month": "2016-01"}) + "\n", encoding="utf-8")
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:35:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_01_market_regime")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "fold_stage_coverage")
        self.assertEqual(progress["unit_label"], "source-month requests")
        self.assertEqual(progress["expected_count"], 30)
        self.assertEqual(progress["ready_count"], 8)
        self.assertEqual(progress["pending_count"], 22)
        self.assertEqual(progress["covered_partition_count"], 3)
        self.assertEqual(progress["expected_partition_count"], 6)

    def test_feature_generation_progress_uses_fold_month_partitions(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
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
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
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
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:35:30Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_03_target_state_vector")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "fold_feature_generation_partitions")
        self.assertEqual(progress["unit_label"], "feature months")
        self.assertEqual(progress["expected_count"], 6)
        self.assertEqual(progress["ready_count"], 0)
        self.assertEqual(progress["pending_count"], 6)
        self.assertIn("six-month fold", progress["progress_basis"])

    def test_reset_fold_waits_for_monthly_foundation_instead_of_showing_ready(self):
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
                                "stage_id": "layer_02_sector_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "layer_02_sector_context",
                                "status": "ready",
                                "last_reason": (
                                    "rerun reset from layer_02.data_acquisition: Layer 2 sector-context "
                                    "contract changed; reset AAPL fold Layer 2 and downstream generated workflow state."
                                ),
                                "dataset_unit": {
                                    "unit_kind": "six_month_panel",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": False,
                                },
                            },
                            {
                                "stage_id": "layer_02_sector_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "layer_02_sector_context",
                                "status": "blocked",
                                "blockers": ["layer_02_sector_context.data_acquisition_complete"],
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-05T09:15:00Z")

        self.assertFalse(
            any(
                task["month"] == "2016-fold1"
                and task["task_id"] == "layer_02_sector_context"
                and task["task_state"] == "future"
                for task in payload["chart_payload"]["task_timeline"]
            )
        )

    def test_task_timeline_exposes_target_and_instrument_scope(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_target_queue.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_target_queue",
                        "queue_policy": "ordered_first_open_fold",
                        "rotation_boundary": "layer_03_plus_model_worker",
                        "targets": [{"symbol": "AAPL"}, {"symbol": "NVDA"}],
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
                                "stage_id": "layer_01_market_regime.model_task",
                                "stage_type": "model_task",
                                "layer": 1,
                                "layer_key": "layer_01_market_regime",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "six_month_panel",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": False,
                                    "target_symbol": None,
                                },
                            },
                            {
                                "stage_id": "layer_08_underlying_action.model_task",
                                "stage_type": "model_task",
                                "layer": 8,
                                "layer_key": "layer_08_underlying_action",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "layer_09_option_expression.model_task",
                                "stage_type": "model_task",
                                "layer": 9,
                                "layer_key": "layer_09_option_expression",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:35:40Z")

        tasks = payload["chart_payload"]["task_timeline"]
        layer_one = next(task for task in tasks if task["layer"] == 1)
        layer_eight = next(task for task in tasks if task["layer"] == 8)
        layer_nine = next(task for task in tasks if task["layer"] == 9)
        self.assertEqual(layer_one["target_scope"], "market_context_panel")
        self.assertEqual(layer_one["instrument_scope"], "market_context_proxy_panel")
        self.assertEqual(layer_eight["target_scope"], "target_symbol")
        self.assertEqual(layer_eight["instrument_scope"], "underlying_action_plan")
        self.assertEqual(layer_nine["instrument_scope"], "option_expression_or_underlying_fallback")
        self.assertEqual(payload["chart_payload"]["target_queue"]["enabled_targets"], ["AAPL", "NVDA"])

    def test_model_generation_progress_uses_dataset_splits_without_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
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
                                "stage_id": "layer_03_target_state_vector.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "dataset_split": {"split_name": "validation"},
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "blocked",
                                "blockers": ["layer_03_target_state_vector.model_generation.validation_complete"],
                                "dataset_split": {"split_name": "test"},
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:35:45Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_03_target_state_vector")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "model_generation_dataset_splits")
        self.assertEqual(progress["unit_label"], "dataset months")
        self.assertEqual(progress["expected_count"], 6)
        self.assertEqual(progress["ready_count"], 4)
        self.assertEqual(progress["pending_count"], 2)
        self.assertIn("train=4 months", progress["progress_basis"])
        self.assertEqual(task["detail"]["active_stage_id"], "layer_03_target_state_vector.model_generation.validation")

    def test_active_model_generation_progress_preserves_split_total(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
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
                                "stage_id": "layer_03_target_state_vector.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "ready",
                                "dataset_split": {"split_name": "validation"},
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "blocked",
                                "blockers": ["layer_03_target_state_vector.model_generation.validation_complete"],
                                "dataset_split": {"split_name": "test"},
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            write_task_progress_node(
                progress_root=runtime / "task_progress",
                worker_id="model_worker_1",
                task_uid="2016-01..2016-06:layer_03_target_state_vector.model_generation.validation",
                stage_id="layer_03_target_state_vector.model_generation.validation",
                unit_label="model rows",
                expected_count=1,
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:35:50Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_03_target_state_vector")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["status"], "running")
        self.assertEqual(progress["progress_source"], "model_generation_dataset_splits")
        self.assertEqual(progress["unit_label"], "dataset months")
        self.assertEqual(progress["expected_count"], 6)
        self.assertEqual(progress["ready_count"], 4)
        self.assertEqual(progress["pending_count"], 2)
        self.assertEqual(progress["stage_id"], "layer_03_target_state_vector.model_generation.validation")
        self.assertEqual(progress["nodes"][0]["node_id"], "stage_started")

    def test_completed_model_task_ignores_model_row_count_for_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
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
                                "stage_id": "layer_03_target_state_vector.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
                                    "unit_months": 6,
                                    "start_month": "2016-01",
                                    "end_month": "2016-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "validation"},
                            },
                            {
                                "stage_id": "layer_03_target_state_vector.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "layer_03_target_state_vector",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "test"},
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_six_month",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:36:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_03_target_state_vector")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "model_generation_dataset_splits")
        self.assertEqual(progress["unit_label"], "dataset months")
        self.assertEqual(progress["expected_count"], 6)
        self.assertEqual(progress["ready_count"], 6)
        self.assertEqual(progress["pending_count"], 0)
        self.assertNotIn("artifact_count", progress)

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
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "feed_acquisition_plan.csv").write_text(
                "month\n2021-01\n2021-02\n",
                encoding="utf-8",
            )
            replay_run = replay_root / "replay_execution_runs" / "model_group_replay_fixture"
            replay_run.mkdir(parents=True, exist_ok=True)
            (replay_run / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "model_group_replay_fixture",
                        "candidate_model_ref": "storage://trading-manager/model_group/2016-01_2016-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "validation_status": "passed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "model_group_replay_fixture", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "model_group_replay_fixture", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self._write_post_replay_attribution_receipt(replay_root)
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
            self._write_completed_pre_replay_fold(tmp / "storage" / "02_control_plane" / "runtime", symbol="AAPL")
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

        promotion_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.promotion")
        maintenance_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.maintenance")
        self.assertEqual(promotion_task["status"], "review_required")
        self.assertEqual(promotion_task["task_state"], "completed")
        self.assertEqual(promotion_task["detail"]["progress"]["ready_count"], 5)
        self.assertEqual(promotion_task["detail"]["progress"]["pending_count"], 0)
        self.assertFalse(promotion_task["detail"]["progress"]["can_unlock_downstream"])
        self.assertEqual(promotion_task["detail"]["blockers"], ["missing anonymous comparison", "auroc_below_minimum"])
        self.assertEqual(payload["status"], "action_required")
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.promotion")
        self.assertEqual(payload["chart_payload"]["blocker_category"], "missing anonymous comparison")
        self.assertIn("requires review at Model Promotion", payload["summary"])
        self.assertNotIn("blocked at model_group.replay", payload["summary"])
        self.assertEqual(maintenance_task["status"], "not_applicable")
        self.assertEqual(maintenance_task["task_state"], "skipped")
        self.assertEqual(maintenance_task["detail"]["blockers"], [])
        self.assertEqual(maintenance_task["detail"]["progress"]["ready_count"], 4)

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
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "feed_acquisition_plan.csv").write_text("month\n2021-01\n2021-02\n", encoding="utf-8")
            replay_run = replay_root / "replay_execution_runs" / "model_group_replay_fixture"
            replay_run.mkdir(parents=True, exist_ok=True)
            (replay_run / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "model_group_replay_fixture",
                        "candidate_model_ref": "storage://trading-manager/model_group/2016-01_2016-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "validation_status": "passed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "model_group_replay_fixture", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "model_group_replay_fixture", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self._write_post_replay_attribution_receipt(replay_root)
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
            self._write_completed_pre_replay_fold(tmp / "storage" / "02_control_plane" / "runtime", symbol="AAPL")
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
        self.assertEqual(maintenance_task["detail"]["progress"]["expected_count"], 4)
        self.assertEqual(maintenance_task["detail"]["progress"]["ready_count"], 4)
        self.assertEqual(maintenance_task["detail"]["progress"]["pending_count"], 0)
        self.assertEqual(maintenance_task["detail"]["progress"]["unit_label"], "data types")
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

    def test_task_detail_surfaces_failure_register_and_agent_intervention(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\n"
                "TRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
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
                                "stage_id": "layer_09_option_expression.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 9,
                                "layer_key": "layer_09_option_expression",
                                "status": "ready",
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
            coverage_root = runtime / "stage_coverage"
            coverage_root.mkdir(parents=True, exist_ok=True)
            (coverage_root / "layer_09_option_expression_data_acquisition_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "layer_09_option_expression.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "status": "partial_ready",
                        "expected_count": 10,
                        "ready_count": 0,
                        "pending_count": 10,
                        "failed_count": 0,
                        "accepted_failed_count": 0,
                        "can_unlock_downstream": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (coverage_root / "layer_09_option_expression_data_acquisition_2016-01_failure_register_proposals.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_failure_register",
                        "failure_id": "fail_layer9_provider_policy",
                        "request_id": "mgrreq_layer9_option_snapshot_aapl_2016_01",
                        "run_id": "run_layer9_provider_policy",
                        "stage_id": "layer_09_option_expression.data_acquisition",
                        "target_component_id": "m09_option_expression_data_acquisition",
                        "source_id": "m09_option_expression_data_acquisition",
                        "symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "failure_status": "agent_review_required",
                        "failure_kind": "unclassified_provider_failure",
                        "observed_status": "failed",
                        "error_summary": "ProviderPolicyError: provider not allowed: thetadata",
                        "skip_future_matching": False,
                        "evidence_refs": ["storage://trading-data/layer_09/receipt.json"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_layer9_provider_policy"
            request_root.mkdir(parents=True, exist_ok=True)
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_layer9_provider_policy",
                        "request_ref": "erragent_layer9_provider_policy",
                        "agent_ref": "trader",
                        "status": "queued",
                        "return_code": None,
                        "stdout": "",
                        "stderr": "",
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
                        "error_number": 9,
                        "error_ref": "ERR-000009",
                        "error_fingerprint": "errfp_layer9_provider_policy",
                        "request_id": "erragent_layer9_provider_policy",
                        "request_path": "storage/runtime/agent_error_handling/erragent_layer9_provider_policy/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_layer9_provider_policy/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_reconcile",
                        "source_repo": "trading-manager",
                        "error_scope": "server.provider_stage_failure_register",
                        "error_kind": "provider_stage_requests_failed",
                        "severity": "warning",
                        "summary": "provider stage layer_09_option_expression.data_acquisition has failed requests requiring agent review",
                        "occurred_at_utc": "2026-06-05T10:33:32Z",
                        "created_at_utc": "2026-06-05T10:33:32Z",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-05T10:40:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_09_option_expression")
        self.assertEqual(task["status"], "review_required")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["detail"]["progress"]["failed_count"], 0)
        self.assertEqual(task["detail"]["failure_register"]["agent_review_required_count"], 1)
        self.assertEqual(task["detail"]["agent_error_summary"][0]["error_ref"], "ERR-000009")
        self.assertEqual(task["detail"]["repair_intervention_status"], "agent_diagnosis_queued")

    def test_task_detail_surfaces_retry_required_provider_failures_without_review_required_status(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\n"
                "TRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
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
                                "stage_id": "layer_09_option_expression.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 9,
                                "layer_key": "layer_09_option_expression",
                                "status": "ready",
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
            coverage_root = runtime / "stage_coverage"
            coverage_root.mkdir(parents=True, exist_ok=True)
            (coverage_root / "layer_09_option_expression_data_acquisition_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "layer_09_option_expression.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "status": "partial_ready",
                        "expected_count": 10,
                        "ready_count": 1,
                        "pending_count": 9,
                        "failed_count": 0,
                        "accepted_failed_count": 0,
                        "can_unlock_downstream": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (coverage_root / "layer_09_option_expression_data_acquisition_2016-01_failure_register_proposals.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_failure_register",
                        "failure_id": "fail_layer9_thetadata_connection_refused",
                        "request_id": "mgrreq_layer9_option_snapshot_aapl_2016_01",
                        "run_id": "run_layer9_thetadata_connection_refused",
                        "stage_id": "layer_09_option_expression.data_acquisition",
                        "target_component_id": "m09_option_expression_data_acquisition",
                        "source_id": "m09_option_expression_data_acquisition",
                        "symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "failure_status": "retry_required",
                        "failure_kind": "provider_service_unavailable",
                        "observed_status": "failed",
                        "error_summary": "ThetaDataOptionSelectionSnapshotError: request failed before HTTP response: URLError: <urlopen error [Errno 111] Connection refused>",
                        "skip_future_matching": False,
                        "evidence_refs": ["storage://trading-data/layer_09/receipt.json"],
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-05T10:40:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "layer_09_option_expression")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["detail"]["failure_register"]["retry_required_count"], 1)
        self.assertEqual(task["detail"]["failure_register"]["agent_review_required_count"], 0)
        self.assertEqual(task["detail"]["repair_intervention_status"], "provider_retry_required")
        self.assertIn("automatic retry", task["reason"])

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

    def test_agent_error_summary_closes_repaired_stage_when_retry_is_not_applicable(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            agent_root = tmp / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            request_root = agent_root / "erragent_do_not_retry"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "repaired_verified",
                "root_cause": "workflow now blocks missing target-local feed artifacts before execution",
                "repair": {"repair_status": "repaired", "files_changed": ["/repo/workflow.py"]},
                "retry_recommendation": "do_not_retry",
                "blockers": ["target-local feed artifacts are unavailable"],
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_do_not_retry",
                        "request_ref": "erragent_do_not_retry",
                        "agent_ref": "trader",
                        "runner_command": "openclaw_agent",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps({"result": {"meta": {"finalAssistantRawText": json.dumps(final_report)}}}),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T13:40:00Z",
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
                        "error_number": 15,
                        "error_ref": "ERR-000015",
                        "error_fingerprint": "errfp_do_not_retry",
                        "request_id": "erragent_do_not_retry",
                        "request_path": "storage/runtime/agent_error_handling/erragent_do_not_retry/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_do_not_retry/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage layer_03_target_state_vector.data_acquisition command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T13:35:00Z",
                        "created_at_utc": "2026-05-18T13:35:00Z",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T13:41:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000015")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")

    def test_agent_error_summary_closes_repaired_with_blockers_when_exact_retry_is_forbidden(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            agent_root = tmp / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            request_root = agent_root / "erragent_repaired_with_blockers"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "repaired_with_blockers",
                "root_cause": {"summary": "stale bootstrap target was removed from the executable route"},
                "repair_attempted": {"attempted": True},
                "files_changed": ["/repo/queue.py"],
                "verification": [{"command": "workflow check", "status": "passed"}],
                "retry_recommendation": "Do not retry the exact failed materialization command; use normal scheduler selection.",
                "blockers": ["direct materialization remains blocked by missing target-local artifacts"],
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_repaired_with_blockers",
                        "request_ref": "erragent_repaired_with_blockers",
                        "agent_ref": "trader",
                        "runner_command": "codex_cli",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps(final_report),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T13:50:00Z",
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
                        "error_number": 14,
                        "error_ref": "ERR-000014",
                        "error_fingerprint": "errfp_repaired_with_blockers",
                        "request_id": "erragent_repaired_with_blockers",
                        "request_path": "storage/runtime/agent_error_handling/erragent_repaired_with_blockers/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_repaired_with_blockers/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage layer_03_target_state_vector.data_acquisition command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T13:45:00Z",
                        "created_at_utc": "2026-05-18T13:45:00Z",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T13:51:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000014")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")

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
        self.assertEqual(payload["chart_payload"]["runtime_active_work"]["status"], "running")
        self.assertEqual(
            payload["chart_payload"]["runtime_active_work"]["stage_id"],
            "layer_03_target_state_vector.feature_generation",
        )


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
        self.assertEqual({task["month"] for task in task_timeline}, {"2019-fold1"})
        model_tasks = [task for task in task_timeline if task["stage_type"] == "model_task"]
        self.assertEqual([task["task_state"] for task in model_tasks], ["completed"])
        self.assertEqual(len([task for task in task_timeline if str(task["task_id"]).startswith("model_group.")]), 0)

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
        self.assertEqual(durable_task["task_uid"], "2018-01..2018-06:layer_01_market_regime")

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
        model_tasks = [task for task in fold_tasks if task["stage_type"] == "model_task"]
        lifecycle_tasks = [task for task in fold_tasks if str(task["task_id"]).startswith("model_group.")]
        self.assertEqual([task["stage_type"] for task in model_tasks], ["model_task", "model_task", "model_task"])
        self.assertEqual([task["task_number"] for task in model_tasks], [1, 2, 3])
        self.assertEqual([task["sequence"] for task in model_tasks], [1, 2, 3])
        self.assertEqual(model_tasks[0]["task_uid"], "2016-01..2016-06:layer_01_market_regime")
        self.assertEqual(model_tasks[0]["detail"]["child_partitions"], ["2016-01", "2016-02", "2016-03", "2016-04", "2016-05", "2016-06"])
        self.assertEqual(model_tasks[0]["task_label"], "Layer 1 Market Regime Model")
        self.assertEqual(model_tasks[1]["task_label"], "Layer 2 Sector Context Model")
        self.assertEqual(model_tasks[2]["task_label"], "Layer 3 Target State Vector Model")
        self.assertEqual(len(lifecycle_tasks), 0)
        fold_prep_tasks = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["task_id"] == "layer_03_target_state_vector"
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
            if task["month"] == "2016-fold1" and task["task_id"] == "layer_03_target_state_vector"
        )
        self.assertEqual(task["status"], "succeeded")
        self.assertEqual(task["target_symbol"], "AAPL")

    def test_task_timeline_hides_later_fold_after_first_open_fold(self):
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
        self.assertIn("2016-fold1", ordered_months)
        self.assertNotIn("2016-fold2", ordered_months)

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
        self.assertFalse(any(task["layer"] == 5 and task["stage_type"] == "model_task" for task in task_timeline))
        real_skip = next(task for task in task_timeline if task["task_id"] == "layer_09_option_expression")
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
        self.assertTrue(all(task["task_id"] == "layer_02_sector_context" for task in current_tasks))

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
        self.assertEqual([(task["month"], task["task_id"]) for task in current_tasks], [("2020-fold2", "layer_03_target_state_vector")])

    def test_task_timeline_hides_later_fold_until_earliest_open_fold_closes(self):
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

        self.assertNotIn("2017-fold1", {task["month"] for task in payload["chart_payload"]["task_timeline"]})
        self.assertNotIn("2016-fold2", {task["month"] for task in payload["chart_payload"]["task_timeline"]})

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
            ("2016-fold2", "layer_03_target_state_vector", "AAPL", "Model Worker 1"),
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

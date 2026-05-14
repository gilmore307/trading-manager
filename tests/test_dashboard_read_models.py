from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.dashboard_read_models import build_historical_task_progress_summary
from trading_manager_tasks.scheduler_status import collect_historical_scheduler_status


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
            workflow_state = tmp / "storage" / "runtime" / "model_training_workflow_state_2019-05.json"
            workflow_state.parent.mkdir(parents=True, exist_ok=True)
            receipt_path = tmp / "storage" / "runtime" / "example_stage_receipt.json"
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
                                "receipt_refs": ["storage/runtime/example_stage_receipt.json"],
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
                                "stdout_path": "storage/runtime/model_training_stage_logs/example.stdout.log",
                                "stderr_path": "storage/runtime/model_training_stage_logs/example.stderr.log",
                                "receipt_path": "storage/runtime/model_training_stage_receipts/example.receipt.json",
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
                storage_root=tmp / "storage",
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
        self.assertEqual(payload["schema_ref"], "storage/dashboard/schemas/historical_task_progress_summary.schema.json")
        self.assertEqual(payload["status"], "action_required")
        self.assertIn("last execution failed", payload["summary"])
        self.assertEqual(payload["chart_payload"]["stage_coverage"]["expected_count"], 19)
        self.assertFalse(payload["chart_payload"]["stage_coverage"]["can_unlock_downstream"])
        self.assertEqual(payload["chart_payload"]["last_stage_execution"]["status"], "failed")
        self.assertEqual(payload["chart_payload"]["last_stage_execution"]["return_code"], 1)
        task_timeline = payload["chart_payload"]["task_timeline"]
        self.assertEqual([task["task_state"] for task in task_timeline], ["completed", "failed", "future"])
        self.assertEqual(task_timeline[1]["task_label"], "Data Acquisition")
        self.assertEqual(task_timeline[1]["month"], "2019-05")
        self.assertEqual(task_timeline[1]["detail"]["last_execution"]["return_code"], 1)
        self.assertEqual(task_timeline[2]["stage_type"], "feature_generation")
        self.assertIsNone(task_timeline[0]["created_at_utc"])
        self.assertEqual(task_timeline[0]["started_at_utc"], "2026-05-12T09:00:00Z")
        self.assertEqual(task_timeline[0]["ended_at_utc"], "2026-05-12T09:30:00Z")
        self.assertEqual(task_timeline[0]["status_updated_at_utc"], "2026-05-12T10:00:00Z")
        self.assertEqual(task_timeline[0]["detail"]["progress"]["ready_count"], 3)
        self.assertIn("Layer 2 feed artifacts", payload["chart_payload"]["last_stage_execution"]["failure_detail"])
        self.assertTrue(any(ref.get("issue_type") == "historical_stage_execution_failed" for ref in payload["issue_refs"]))
        self.assertTrue(any(ref.get("ref_type") == "manager_stage_execution_summary" for ref in payload["diagnostic_refs"]))
        self.assertIn("profile_refs", payload)
        self.assertIn("lineage_refs", payload)
        self.assertIn(payload["severity"], {"critical", "high", "medium", "low", "info"})


    def test_terminal_task_without_recorded_timing_is_not_backfilled_from_status_update(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "runtime"
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
                                "receipt_refs": ["storage/runtime/stage_coverage/example.json"],
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
                storage_root=tmp / "storage",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        task = payload["chart_payload"]["task_timeline"][0]
        self.assertEqual(task["task_state"], "completed")
        self.assertIsNone(task["created_at_utc"])
        self.assertIsNone(task["started_at_utc"])
        self.assertIsNone(task["ended_at_utc"])
        self.assertEqual(task["status_updated_at_utc"], "2026-05-12T10:00:00Z")

    def test_task_timeline_includes_completed_month_groups_before_current_month(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "runtime"
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
                        "contract_type": "manager_scheduler_daemon_state_v1",
                        "start_month": "2019-06",
                        "end_month": "2019-06",
                        "last_completed_months": ["2019-04", "2019-05"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        task_timeline = payload["chart_payload"]["task_timeline"]
        self.assertEqual([task["month"] for task in task_timeline], ["2019-04", "2019-06"])
        self.assertEqual([task["task_state"] for task in task_timeline], ["completed", "current"])

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
                        "contract_type": "manager_scheduler_daemon_state_v1",
                        "start_month": "2019-05",
                        "end_month": "2019-05",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage",
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-12T12:00:00Z")

        layer_three_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["layer"] == 3)
        self.assertEqual(layer_three_task["dataset_unit_kind"], "target_symbol_six_month")
        self.assertEqual(layer_three_task["target_symbol"], "AAPL")
        self.assertTrue(layer_three_task["target_required"])
        self.assertEqual(layer_three_task["detail"]["dataset_unit"]["target_symbol"], "AAPL")

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

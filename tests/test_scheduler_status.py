from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_state import advance_workflow_state, workflow_state_path_for_month
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.scheduler_status import collect_historical_scheduler_status


class SchedulerStatusTests(unittest.TestCase):
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

    def test_status_auto_selects_next_month_and_reports_runtime_readiness(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            service, env, wrapper = self._write_service_files(tmp)
            for month in ("2016-02", "2016-03"):
                plan = build_model_training_workflow_plan(start_month=month, end_month=month, storage_root=storage_root)
                all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
                advance_workflow_state(
                    start_month=month,
                    end_month=month,
                    storage_root=storage_root,
                    state_path=workflow_state_path_for_month(month, root=storage_root / "runtime"),
                    completed_stage_ids=all_stage_ids,
                    write=True,
                )

            status = collect_historical_scheduler_status(
                storage_root=storage_root,
                state_path=tmp / "runtime" / "historical_scheduler_state.json",
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=tmp / "runtime" / "historical_scheduler_decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

        row = status.summary_row()
        self.assertTrue(row["service_runtime_ready"])
        self.assertEqual(row["auto_work_selection"]["start_month"], "2016-04")
        self.assertEqual(row["current_month"], "2016-04")
        self.assertEqual(row["current_stage"], "prepare_layer_one_historical_training_batch")
        self.assertEqual(row["missing_service_flags"], [])
        self.assertIn("start_service_or_run_one_shot_smoke_to_create_daemon_state", row["open_operational_items"])
        self.assertEqual(row["gated_scope_status"]["model_activation"]["status"], "agent_promotion_decision_required_not_owner_approval")

    def test_status_reports_latest_decision_and_provider_gate(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            service, env, wrapper = self._write_service_files(tmp)
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps({
                    "contract_type": "manager_scheduler_daemon_state",
                    "daemon_id": "manager_historical_training_scheduler",
                    "resume_supported": True,
                    "start_month": "2016-04",
                    "end_month": "2016-04",
                    "total_ticks": 1,
                    "successful_ticks": 0,
                    "backoff_ticks": 1,
                    "failed_ticks": 0,
                    "consecutive_errors": 0,
                    "last_decision_status": "backoff",
                    "last_reason_code": "workflow_stage_ready",
                    "last_next_internal_stage": "autonomous_historical_provider_acquisition",
                    "service_managed": True,
                    "service_manager": "systemd",
                    "last_completed_months": ["2016-02", "2016-03"],
                    "last_open_months": [],
                }) + "\n",
                encoding="utf-8",
            )
            decision_log.write_text(
                json.dumps({
                    "contract_type": "manager_scheduler_decision",
                    "decision_status": "ready",
                    "reason_code": "workflow_stage_ready",
                    "reason": "provider stage ready for autonomous dispatch",
                    "selected_work": "layer_01_market_regime.data_acquisition",
                    "next_internal_stage": "autonomous_historical_provider_acquisition",
                    "provider_calls": 0,
                    "dispatch_performed": False,
                }) + "\n",
                encoding="utf-8",
            )

            status = collect_historical_scheduler_status(
                storage_root=storage_root,
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

        row = status.summary_row()
        self.assertEqual(row["current_month"], "2016-04")
        self.assertEqual(row["current_stage"], "layer_01_market_regime.data_acquisition")
        self.assertEqual(row["provider_status"]["status"], "provider_stage_autonomous_ready")
        self.assertIsNone(row["blocked_reason"])
        self.assertEqual(row["latest_decision"]["decision_log_row_count"], 1)
        self.assertEqual(row["lock_plan"]["contract_type"], "scheduler_lock_plan_v1")
        self.assertEqual(
            row["lock_plan"]["required_lock_scopes"],
            ["daemon", "month_stage", "reconcile", "provider_partition"],
        )

    def test_status_ignores_stale_completed_previous_decision(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            service, env, wrapper = self._write_service_files(tmp)
            plan = build_model_training_workflow_plan(start_month="2019-01", end_month="2019-01", storage_root=storage_root)
            all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2019-01",
                end_month="2019-01",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2019-01", root=storage_root / "runtime"),
                completed_stage_ids=all_stage_ids,
                write=True,
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps({
                    "contract_type": "manager_scheduler_daemon_state",
                    "start_month": "2019-01",
                    "end_month": "2019-01",
                    "last_next_internal_stage": "old_provider_gate",
                }) + "\n",
                encoding="utf-8",
            )
            decision_log.write_text(
                json.dumps({
                    "contract_type": "manager_scheduler_decision",
                    "decision_status": "executed",
                    "start_month": "2019-01",
                    "selected_work": "old_stage",
                    "approval_gate_required": "retired_gate",
                }) + "\n",
                encoding="utf-8",
            )

            status = collect_historical_scheduler_status(
                storage_root=storage_root,
                state_path=state_path,
                lock_path=tmp / "runtime" / "historical_scheduler.lock",
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

        row = status.summary_row()
        self.assertEqual(row["auto_work_selection"]["start_month"], "2019-02")
        self.assertEqual(row["current_month"], "2019-02")
        self.assertIsNone(row["blocked_reason"])
        self.assertIsNone(row["latest_decision"])
        self.assertEqual(row["provider_status"]["status"], "no_provider_work_selected")
        self.assertNotIn("last_next_internal_stage", row["daemon_state"])

    def test_status_flags_missing_service_flags(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service = tmp / "service.service"
            env = tmp / "service.env"
            wrapper = tmp / "daemon.py"
            service.write_text("ExecStart=python3 scripts/tasks/run_automation_scheduler_daemon.py\n", encoding="utf-8")
            env.write_text("\n", encoding="utf-8")
            wrapper.write_text("\n", encoding="utf-8")

            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage",
                state_path=tmp / "state.json",
                lock_path=tmp / "lock.json",
                decision_log_path=tmp / "decisions.jsonl",
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

        row = status.summary_row()
        self.assertFalse(row["recommended_service_flags_present"])
        self.assertIn("--auto-select-next-work", row["missing_service_flags"])
        self.assertIn("review_systemd_template_flags", row["open_operational_items"])
        self.assertFalse(row["service_runtime_ready"])


if __name__ == "__main__":
    unittest.main()

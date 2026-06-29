from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from trading_manager_tasks.dashboard_read_models import (
    _agent_errors_for_task,
    _apply_agent_repair_closure_receipt,
    _attach_task_error_context,
    _close_global_nonblocking_agent_errors,
    _agent_error_summary,
    _compatible_replay_run_ids,
    _mark_active_task_running,
    _mark_superseded_agent_errors,
    _model_group_replay_timeline_tasks,
    _runtime_activity_decision,
    _scheduler_decision_runtime_activity,
    _stage_id_from_error_row,
    _task_error_intervention_status,
    build_historical_task_progress_summary,
)
from trading_manager_tasks.scheduler_status import collect_historical_scheduler_status
from trading_manager_tasks.task_progress import write_task_progress_node


class DashboardReadModelProducerTests(unittest.TestCase):
    def test_scheduler_backoff_runtime_activity_blocks_ready_task_instead_of_running(self):
        status = SimpleNamespace(
            lock=SimpleNamespace(status="active"),
            blocked_reason="after-cost alpha artifact is a no-supervised-fit policy bundle",
        )
        task = {
            "task_id": "model_group.replay",
            "task_label": "Model Replay",
            "month": "2017-01..2018-06",
            "status": "ready",
            "task_state": "current",
            "stage_type": "replay",
            "layer_key": "model_group",
            "worker_id": "evaluation_worker_1",
            "target_symbol": None,
            "detail": {
                "progress": {
                    "stage_id": "model_group.replay",
                    "status": "ready",
                    "expected_count": 60,
                    "ready_count": 0,
                }
            },
        }
        runtime_activity = {
            "activity_type": "scheduler_decision",
            "decision_status": "backoff",
            "selected_work": "model_group.replay",
            "reason_code": "model_group_replay_after_cost_alpha_model_not_trained",
            "reason": "after-cost alpha artifact is a no-supervised-fit policy bundle",
            "updated_at_utc": "2026-06-29T04:20:32Z",
        }

        timeline, active = _mark_active_task_running(
            status,
            [task],
            dict(task),
            {"runtime_activity": runtime_activity},
        )

        self.assertIsNotNone(active)
        assert active is not None
        self.assertEqual(active["status"], "blocked")
        self.assertEqual(active["reason"], runtime_activity["reason"])
        self.assertEqual(active["detail"]["progress"]["status"], "blocked")
        self.assertEqual(active["detail"]["runtime_activity"]["reason_code"], runtime_activity["reason_code"])
        self.assertEqual(timeline[0]["status"], "blocked")

    def test_scheduler_decision_runtime_activity_describes_m06_missing_event_inputs(self):
        activity = _scheduler_decision_runtime_activity(
            {
                "decision_status": "backoff",
                "reason_code": "model_group_residual_event_evidence_missing",
                "reason": "replay review is ready, but M06 has no local point-in-time event observations or candidates to attribute",
                "selected_work": "model_group.residual_event_governance",
                "next_internal_stage": "residual_event_governance",
                "now_utc": "2026-06-28T13:30:21.213306+00:00",
                "execution_summary": {
                    "event_source_summary": {
                        "checked_paths": ["/tmp/model_03_event_observation_inputs.json", "/tmp/source_06_task_key.json"],
                        "raw_event_count": 0,
                        "standardized_event_candidate_count": 0,
                    },
                    "fold_scope": {"start_month": "2021-01", "end_month": "2025-12"},
                    "required_next_action": "materialize reviewed PIT event observations/candidates before M06 attribution can complete",
                },
            }
        )

        self.assertIsNotNone(activity)
        assert activity is not None
        self.assertEqual(activity["activity_label"], "M06 Event Risk Governor")
        self.assertIn("waiting for PIT event observations/candidates", activity["activity_summary"])
        self.assertIn("2021-01 to 2025-12", activity["activity_summary"])
        self.assertIn("raw events 0", activity["activity_summary"])
        self.assertIn("candidates 0", activity["activity_summary"])
        self.assertEqual(activity["reason_code"], "model_group_residual_event_evidence_missing")
        self.assertEqual(
            activity["required_next_step"],
            "materialize reviewed PIT event observations/candidates before M06 attribution can complete",
        )
        self.assertIn("Checked 2 event input paths", activity["activity_details"])

    def test_runtime_activity_decision_falls_back_to_decision_log_tail(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            decision_log_path = Path(raw_tmp) / "historical_scheduler_decisions.jsonl"
            decision_log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"selected_work": "model_group.replay", "now_utc": "2026-06-28T13:00:00+00:00"}),
                        json.dumps(
                            {
                                "selected_work": "model_group.residual_event_governance",
                                "reason_code": "model_group_residual_event_evidence_missing",
                                "now_utc": "2026-06-28T13:30:00+00:00",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            status = SimpleNamespace(
                latest_workflow_transition=None,
                latest_decision=None,
                decision_log_file=SimpleNamespace(path=str(decision_log_path)),
            )

            decision = _runtime_activity_decision(status)

        self.assertEqual(decision["selected_work"], "model_group.residual_event_governance")
        self.assertEqual(decision["reason_code"], "model_group_residual_event_evidence_missing")

    def test_runtime_activity_decision_prefers_workflow_transition_ledger(self):
        status = SimpleNamespace(
            latest_workflow_transition={
                "contract_type": "manager_historical_workflow_transition",
                "selected_work": "model_02_target_state.data_acquisition",
                "reason_code": "target_local_provider_stage_executed",
                "task_status": "completed",
            },
            latest_decision={
                "selected_work": "model_group.promotion",
                "reason_code": "stale_promotion_decision",
            },
            decision_log_file=SimpleNamespace(path=""),
        )

        decision = _runtime_activity_decision(status)

        self.assertEqual(decision["selected_work"], "model_02_target_state.data_acquisition")
        self.assertEqual(decision["reason_code"], "target_local_provider_stage_executed")

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
                "summary": "model training stage model_02_target_state.option_chain_data_acquisition command returned non-zero status",
            },
            {
                "error_number": 6,
                "handling_status": "open",
                "repair_status": "unknown",
                "summary": "provider stage model_02_target_state.option_chain_data_acquisition has failed requests requiring automatic repair",
            },
        ]
        task = {"task_id": "model_02_target_state", "detail": {"active_stage_id": "model_02_target_state.option_chain_data_acquisition"}}

        ordered = _agent_errors_for_task(rows, task)

        self.assertEqual([row["error_number"] for row in ordered], [6, 3])

    def test_task_error_context_closes_nonblocking_awaiting_retry(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            task = {
                "task_id": "model_02_target_state",
                "task_state": "current",
                "status": "ready",
                "detail": {
                    "active_stage_id": "model_02_target_state.option_chain_data_acquisition",
                    "progress": {"failed_count": 0, "accepted_failed_count": 0},
                },
            }
            rows = [
                {
                    "error_number": 3,
                    "error_ref": "ERR-000003",
                    "handling_status": "awaiting_retry",
                    "repair_status": "repaired",
                    "summary": "model training stage model_02_target_state.option_chain_data_acquisition command returned non-zero status",
                }
            ]

            updated = _attach_task_error_context([task], storage_root=Path(raw_tmp), agent_errors=rows)

        detail = updated[0]["detail"]
        self.assertEqual(detail["agent_error_summary"][0]["handling_status"], "closed")
        self.assertEqual(detail["agent_error_summary"][0]["dashboard_severity"], "notice")
        self.assertNotIn("repair_intervention_status", detail)
        self.assertEqual(detail.get("blockers", []), [])

    def test_global_agent_errors_close_nonblocking_awaiting_retry(self):
        agent_errors = [
            {
                "error_number": 3,
                "error_ref": "ERR-000003",
                "handling_status": "awaiting_retry",
                "repair_status": "repaired",
            },
            {
                "error_number": 4,
                "error_ref": "ERR-000004",
                "handling_status": "open",
                "repair_status": "unknown",
            },
        ]
        task_timeline = [
            {
                "detail": {
                    "agent_error_summary": [
                        {
                            "error_ref": "ERR-000004",
                            "handling_status": "open",
                        }
                    ]
                }
            }
        ]

        updated = _close_global_nonblocking_agent_errors(agent_errors, task_timeline)

        by_ref = {row["error_ref"]: row for row in updated}
        self.assertEqual(by_ref["ERR-000003"]["handling_status"], "closed")
        self.assertEqual(by_ref["ERR-000003"]["dashboard_severity"], "notice")
        self.assertEqual(by_ref["ERR-000004"]["handling_status"], "open")

    def test_stage_id_from_error_row_accepts_current_stage_wording(self):
        command_row = {
            "summary": "model training stage model_05_option_expression.feature_generation stage command returned non-zero status",
            "error_scope": "server.model_training_stage",
        }
        stalled_row = {
            "summary": "model training stage model_02_target_state.feature_generation stage progress stalled for timeout_seconds=600",
            "error_scope": "server.model_training_stage",
        }

        self.assertEqual(_stage_id_from_error_row(command_row), "model_05_option_expression.feature_generation")
        self.assertEqual(_stage_id_from_error_row(stalled_row), "model_02_target_state.feature_generation")

    def test_blocked_closure_does_not_reopen_already_closed_repair(self):
        repair_status, handling_status = _apply_agent_repair_closure_receipt(
            "repaired",
            "closed",
            {"closure_status": "blocked", "blockers": ["exact retry is not applicable"]},
        )

        self.assertEqual(repair_status, "repaired")
        self.assertEqual(handling_status, "closed")

    def test_supersedes_legacy_layer_nine_option_expression_errors(self):
        rows = [
            {
                "error_ref": "ERR-000003",
                "repair_status": "unknown",
                "handling_status": "open",
                "dashboard_severity": "error",
                "summary": "model training stage model_05_option_expression.data_acquisition command returned non-zero status",
            }
        ]
        tasks = [{"task_id": "model_05_option_expression"}]

        updated = _mark_superseded_agent_errors(rows, tasks)

        self.assertEqual(updated[0]["repair_status"], "superseded")
        self.assertEqual(updated[0]["handling_status"], "closed")
        self.assertEqual(updated[0]["dashboard_severity"], "notice")

    def test_supersedes_python_library_replay_option_source_errors(self):
        rows = [
            {
                "error_ref": "ERR-000021",
                "error_kind": "model_group_replay_option_source_acquisition_failed",
                "repair_status": "blocked",
                "handling_status": "open",
                "dashboard_severity": "error",
                "root_cause": "option-chain source default still selected the Python-library transport; accepted contract requires Terminal REST",
            }
        ]

        updated = _mark_superseded_agent_errors(rows, [])

        self.assertEqual(updated[0]["repair_status"], "superseded")
        self.assertEqual(updated[0]["handling_status"], "closed")
        self.assertEqual(updated[0]["dashboard_severity"], "notice")

    def test_closes_scheduler_lock_conflict_when_managed_daemon_is_active(self):
        rows = [
            {
                "error_ref": "ERR-000039",
                "error_kind": "RuntimeError",
                "source_component": "trading-manager.historical_scheduler_daemon",
                "repair_status": "blocked",
                "handling_status": "open",
                "dashboard_severity": "error",
                "root_cause": (
                    "The failed one-shot scheduler invocation attempted to acquire historical_scheduler.lock while an "
                    "existing historical scheduler daemon was already running. The lock file records pid 123, and process "
                    "inspection confirmed that pid is an active run_automation_scheduler_daemon.py process."
                ),
                "summary": "historical scheduler daemon failed: scheduler daemon lock is active",
            }
        ]

        updated = _mark_superseded_agent_errors(rows, [])

        self.assertEqual(updated[0]["repair_status"], "no_action_needed")
        self.assertEqual(updated[0]["handling_status"], "closed")
        self.assertEqual(updated[0]["dashboard_severity"], "notice")

    def test_agent_error_summary_filters_foreign_absolute_artifact_paths(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            agent_root = storage_root / "runtime" / "agent_error_handling"
            agent_root.mkdir(parents=True, exist_ok=True)
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 26,
                        "error_ref": "ERR-000026",
                        "error_fingerprint": "errfp_foreign_tmp",
                        "request_id": "erragent_foreign_tmp",
                        "request_path": "/tmp/tm-storage/runtime/agent_error_handling/erragent_foreign_tmp/server_error_agent_request.json",
                        "diagnosis_path": "/tmp/tm-storage/runtime/agent_error_handling/erragent_foreign_tmp/agent_error_diagnosis.json",
                        "source_component": "trading-manager.scheduler_daemon",
                        "source_repo": "trading-manager",
                        "error_scope": "server.scheduler_progress",
                        "error_kind": "scheduler_progress_stalled",
                        "severity": "warning",
                        "summary": "historical scheduler made no progress",
                        "occurred_at_utc": "2026-06-11T06:10:58Z",
                        "created_at_utc": "2026-06-11T06:10:58Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            rows = _agent_error_summary(storage_root)

        self.assertEqual(rows, [])

    def test_agent_error_summary_filters_missing_diagnosis_artifacts(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            agent_root = storage_root / "runtime" / "agent_error_handling"
            agent_root.mkdir(parents=True, exist_ok=True)
            (agent_root / "server_error_catalog.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_catalog_entry",
                        "schema_version": "1",
                        "error_number": 27,
                        "error_ref": "ERR-000027",
                        "error_fingerprint": "errfp_missing_diagnosis",
                        "request_id": "erragent_missing_diagnosis",
                        "request_path": "02_control_plane/runtime/agent_error_handling/erragent_missing_diagnosis/server_error_agent_request.json",
                        "diagnosis_path": "02_control_plane/runtime/agent_error_handling/erragent_missing_diagnosis/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.provider_stage_failure_register",
                        "error_kind": "provider_stage_requests_failed",
                        "severity": "warning",
                        "summary": "stale provider stage error",
                        "occurred_at_utc": "2026-06-11T06:10:58Z",
                        "created_at_utc": "2026-06-11T06:10:58Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            rows = _agent_error_summary(storage_root)

        self.assertEqual(rows, [])

    def test_agent_error_summary_filters_targets_outside_current_training_queue(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            self._write_target_queue(runtime, ["AAPL"])
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_aaoi_stale"
            request_root.mkdir(parents=True, exist_ok=True)
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_aaoi_stale",
                        "request_ref": "erragent_aaoi_stale",
                        "agent_ref": "trader",
                        "status": "completed",
                        "root_cause": "For AAOI 2016-01..2017-06, stale model worker provider keys were generated.",
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
                        "error_number": 17,
                        "error_ref": "ERR-000017",
                        "error_fingerprint": "errfp_aaoi_stale",
                        "request_id": "erragent_aaoi_stale",
                        "request_path": "storage/runtime/agent_error_handling/erragent_aaoi_stale/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_aaoi_stale/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_reconcile",
                        "source_repo": "trading-manager",
                        "error_scope": "server.provider_stage_failure_register",
                        "error_kind": "provider_stage_requests_failed",
                        "severity": "warning",
                        "summary": "For AAOI 2016-01..2017-06, provider stage generated stale task locks.",
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

        self.assertEqual(payload["chart_payload"]["target_queue"]["enabled_targets"], ["AAPL"])
        self.assertEqual(payload["chart_payload"]["agent_error_summary"], [])
        self.assertNotIn("AAOI", json.dumps(payload["chart_payload"], sort_keys=True))

    def test_supersedes_retired_m05_option_data_acquisition_errors(self):
        rows = [
            {
                "error_ref": "ERR-000005",
                "repair_status": "blocked",
                "handling_status": "open",
                "dashboard_severity": "warning",
                "summary": "provider stage model_05_option_expression.data_acquisition has failed requests",
                "root_cause": "old model_05_option_expression.data_acquisition route failed before current shared source route",
            },
            {
                "error_ref": "ERR-000006",
                "repair_status": "repaired",
                "handling_status": "closed",
                "dashboard_severity": "notice",
                "summary": "provider stage model_05_option_expression.data_acquisition was already closed",
                "root_cause": "old model_05_option_expression.data_acquisition route already has a closure receipt",
            }
        ]
        task_timeline = [
            {"task_id": "model_02_target_state.option_chain_data_acquisition"},
            {"task_id": "model_05_option_expression.feature_generation"},
        ]

        updated = _mark_superseded_agent_errors(rows, task_timeline)

        self.assertEqual(updated[0]["repair_status"], "superseded")
        self.assertEqual(updated[0]["handling_status"], "closed")
        self.assertEqual(updated[0]["dashboard_severity"], "notice")
        self.assertIn("option_chain_state_source", updated[0]["retry_recommendation"])
        self.assertEqual(updated[1]["repair_status"], "repaired")
        self.assertEqual(updated[1]["handling_status"], "closed")

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

    def test_dashboard_replay_run_filter_requires_canonical_full_universe_receipts(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            dataset_root = Path(raw_tmp) / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root = dataset_root / "replay_execution_runs"
            replay_root.mkdir(parents=True)
            for run_id, receipt in {
                "legacy": {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": "legacy",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "validation_status": "passed",
                },
                "bounded": {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": "bounded",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "replay_completion_scope": "bounded_diagnostic",
                    "max_decision_rows": 5000,
                    "validation_status": "passed",
                },
                "canonical": {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": "canonical",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                    "target_refs": ["AAPL", "MSFT"],
                    "asset_class_counts": {"us_equity": 2},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                    },
                    "replay_completion_scope": "full_candidate_universe",
                    "max_decision_rows": None,
                    "validation_status": "passed",
                },
                "layer2_handoff": {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": "layer2_handoff",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "model_02_target_candidate_handoff",
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                    },
                    "replay_completion_scope": "full_candidate_universe",
                    "max_decision_rows": None,
                    "validation_status": "passed",
                },
            }.items():
                run_root = replay_root / run_id
                run_root.mkdir()
                (run_root / "replay_execution_receipt.json").write_text(json.dumps(receipt) + "\n", encoding="utf-8")

            self.assertEqual(_compatible_replay_run_ids(dataset_root=dataset_root), {"canonical", "layer2_handoff"})

    def _write_post_replay_attribution_receipt(self, replay_root: Path) -> Path:
        receipt_root = replay_root / "post_replay_attribution_runs" / "fixture"
        receipt_root.mkdir(parents=True, exist_ok=True)
        proposals_path = receipt_root / "event_focus_proposals.jsonl"
        proposals_path.write_text(
            json.dumps(
                {
                    "contract_type": "model_06_residual_event_governance_event_focus_proposal",
                    "event_focus_proposal_id": "focus_fixture",
                    "proposal_status": "watch_candidate",
                    "event_ref": "event_fixture",
                    "supporting_failure_count": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        receipt_path = receipt_root / "post_replay_attribution_receipt.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "contract_type": "post_replay_residual_event_governance_receipt",
                    "status": "succeeded",
                    "created_at_utc": "2026-05-22T12:49:00Z",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                    "candidate_fold_id": "fold_aapl_2016",
                    "event_evidence_consumed": True,
                    "event_observation_count": 1,
                    "event_candidate_count": 1,
                    "event_focus_proposals_ref": str(proposals_path),
                    "event_focus_proposal_count": 1,
                    "replay_review_scope_status": "passed",
                    "control_analysis_status": "passed",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return receipt_path

    def _write_post_replay_review_receipt(self, replay_root: Path, *, decision_rows_ref: str = "") -> Path:
        receipt_root = replay_root / "post_replay_review_runs" / "fixture"
        receipt_root.mkdir(parents=True, exist_ok=True)
        review_rows_path = receipt_root / "replay_review_rows.jsonl"
        review_rows_path.write_text(
            json.dumps(
                {
                    "contract_type": "post_replay_review_row",
                    "review_id": "review_fixture",
                    "review_status": "reviewed",
                    "source_decision_id": "decision_fixture",
                    "replay_month": "2021-01",
                    "target_symbol": "AAPL",
                    "best_available_action_by_future_outcome": "path_conditioned_take_opportunity",
                    "regret_to_best_available": 0.04,
                    "first_gap_component": "model_05_option_expression",
                    "first_gap_mechanism": "gate",
                    "miss_attribution_layer": "model_05_option_expression",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        receipt_path = receipt_root / "post_replay_review_receipt.json"
        receipt_path.write_text(
            json.dumps(
                {
                    "contract_type": "post_replay_review_receipt",
                    "status": "succeeded",
                    "stage_id": "model_group.replay_review",
                    "created_at_utc": "2026-05-22T12:45:00Z",
                    "completed_at_utc": "2026-05-22T12:45:00Z",
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                    "candidate_fold_id": "fold_aapl_2016",
                    "decision_rows_ref": decision_rows_ref,
                    "review_rows_ref": str(review_rows_path),
                    "expected_review_count": 1,
                    "reviewed_failure_count": 1,
                    "processed_review_count": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return receipt_path

    def _write_completed_pre_replay_fold(self, runtime: Path, *, symbol: str = "AAPL") -> Path:
        fold_state = runtime / f"model_training_fold_state_{symbol.lower()}_2016-01_2017-06.json"
        fold_state.parent.mkdir(parents=True, exist_ok=True)
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
                            "split_policy": "chronological_rolling_fold_8_2_2",
                        },
                        "dataset_unit": {
                            "unit_kind": "twelve_month_target_fold",
                            "unit_months": 18,
                            "start_month": "2016-01",
                            "end_month": "2017-06",
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
                        "end_month": "2017-06",
                        "target_symbol": symbol,
                        "stages": stages,
                    }
                )
            + "\n",
            encoding="utf-8",
        )
        return fold_state

    def _write_target_queue(self, runtime: Path, symbols: list[str] | None = None) -> Path:
        queue_path = runtime / "model_training_target_queue.json"
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_target_queue",
                    "targets": [{"symbol": symbol} for symbol in (symbols or ["AAPL"])],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return queue_path

    def test_builds_historical_task_progress_summary_payload(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            decision_log = tmp / "runtime" / "historical_scheduler_decisions.jsonl"
            decision_log.parent.mkdir(parents=True, exist_ok=True)
            workflow_state = tmp / "storage" / "02_control_plane" / "runtime" / "model_training_fold_state_aapl_2019-01_2020-06.json"
            workflow_state.parent.mkdir(parents=True, exist_ok=True)
            receipt_path = tmp / "storage" / "02_control_plane" / "runtime" / "example_stage_receipt.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "model_01_background_context.data_acquisition",
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
                        "start_month": "2019-01",
                        "end_month": "2020-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": "model_01_background_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_background_context",
                                "status": "succeeded",
                                "updated_utc": "2026-05-12T10:00:00Z",
                                "last_reason": "stage coverage complete",
                                "receipt_refs": ["02_control_plane/runtime/example_stage_receipt.json"],
                            },
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "updated_utc": "2026-05-12T11:00:00Z",
                                "last_reason": "waiting for source rows",
                                "blockers": ["upstream_model_01_model_generation_complete"],
                            },
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "updated_utc": "2026-05-12T11:05:00Z",
                                "last_reason": "waiting for data acquisition",
                                "blockers": ["model_02_target_state.data_acquisition_complete"],
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
                        "selected_work": "model_02_target_state.data_acquisition",
                        "start_month": "2019-01",
                        "end_month": "2020-06",
                        "execution_summary": {
                            "stage_execution": {
                                "contract_type": "manager_stage_execution_summary",
                                "stage_id": "model_02_target_state.data_acquisition",
                                "status": "failed",
                                "reason": "no successful M02 feed artifacts are available for M02 target-state materialization",
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
                    "stage_id": "model_01_background_context.data_acquisition",
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
        self.assertEqual([task["task_state"] for task in model_tasks], ["completed", "blocked"])
        self.assertTrue(lifecycle_tasks)
        self.assertTrue(all(task["task_state"] == "blocked" for task in lifecycle_tasks))
        self.assertEqual(task_timeline[1]["task_label"], "M02 Target State Vector Model")
        self.assertEqual(task_timeline[1]["month"], "2019-01..2020-06")
        self.assertEqual(
            task_timeline[1]["detail"]["child_partitions"],
            [
                "2019-01",
                "2019-02",
                "2019-03",
                "2019-04",
                "2019-05",
                "2019-06",
                "2019-07",
                "2019-08",
                "2019-09",
                "2019-10",
                "2019-11",
                "2019-12",
                "2020-01",
                "2020-02",
                "2020-03",
                "2020-04",
                "2020-05",
                "2020-06",
            ],
        )
        self.assertEqual(task_timeline[1]["detail"]["last_execution"]["return_code"], 1)
        self.assertEqual(task_timeline[0]["worker_id"], "model_worker_1")
        self.assertEqual(task_timeline[0]["detail"]["worker"]["worker_label"], "Model Worker 1")
        self.assertEqual(task_timeline[1]["stage_type"], "model_task")
        self.assertEqual(task_timeline[1]["detail"]["active_stage_id"], "model_02_target_state.data_acquisition")
        self.assertIsNone(task_timeline[0]["created_at_utc"])
        self.assertEqual(task_timeline[0]["started_at_utc"], "2026-05-12T09:00:00Z")
        self.assertEqual(task_timeline[0]["ended_at_utc"], "2026-05-12T09:30:00Z")
        self.assertEqual(task_timeline[0]["status_updated_at_utc"], "2026-05-12T10:00:00Z")
        self.assertEqual(task_timeline[0]["detail"]["progress"]["ready_count"], 18)
        self.assertEqual(task_timeline[1]["detail"]["progress"]["unit_label"], "task units")
        self.assertEqual(task_timeline[1]["detail"]["progress"]["expected_count"], 2)
        self.assertEqual(task_timeline[1]["detail"]["progress"]["pending_count"], 2)
        self.assertIn("M02 feed artifacts", payload["chart_payload"]["last_stage_execution"]["failure_detail"])
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
                                "stage_id": "model_05_option_expression.option_chain_data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 5,
                                "layer_key": "model_05_option_expression",
                                "status": "ready",
                                "blockers": ["upstream_model_04_model_generation_complete"],
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
                task_uid="2020-07..2020-12:model_05_option_expression.option_chain_data_acquisition",
                stage_id="model_05_option_expression.option_chain_data_acquisition",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_05_option_expression")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["blocker_count"], 0)
        self.assertEqual(task["detail"]["blockers"], [])
        self.assertEqual(task["detail"]["progress"]["expected_count"], 18)
        self.assertEqual(task["detail"]["progress"]["ready_count"], 0)
        self.assertEqual(task["detail"]["progress"]["unit_label"], "source-month requests")

    def test_model_task_aggregate_shows_started_internal_stage_as_running(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            receipt = runtime / "model_training_stage_receipts" / "model_02_target_state__data_acquisition" / "completion_receipt.json"
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt.write_text(
                json.dumps(
                    {
                        "started_at_utc": "2026-06-28T06:14:07Z",
                        "ended_at_utc": "2026-06-28T06:14:12Z",
                        "status": "succeeded",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "ended_at_utc": "2026-06-28T06:14:12Z",
                                "receipt_refs": [str(receipt)],
                            },
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "started_at_utc": "2026-06-28T06:14:12Z",
                                "last_reason": "stage execution started by manager stage executor",
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_split": {"split_name": "train"},
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "dataset_split": {"split_name": "validation"},
                                "last_reason": "waiting for model_02_target_state.model_generation.train_complete",
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "dataset_split": {"split_name": "test"},
                                "last_reason": "waiting for model_02_target_state.model_generation.validation_complete",
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
                task_uid="2016-01..2017-06:model_02_target_state.feature_generation",
                stage_id="model_02_target_state.feature_generation",
                unit_label="feature months",
                processed_count=8,
                expected_count=26,
                node_id="feature_generation_window_started",
                node_label="Generating feature window 9 of 26",
                current_activity="Generating AAPL 2016-03-01 target-state features",
                activity_details=["Using target-local source rows"],
                extra={
                    "window_start": "2016-02-25T00:00:00-05:00",
                    "window_end": "2016-03-03T00:00:00-05:00",
                    "candidate_symbol_count": 50,
                    "sample_targets": ["AAPL", "BTC", "MSFT", "NVDA"],
                },
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

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-28T06:15:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["detail"]["active_stage_id"], "model_02_target_state.feature_generation")
        self.assertEqual(task["started_at_utc"], "2026-06-28T06:14:12Z")
        self.assertIsNone(task["ended_at_utc"])
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "active_progress_file")
        self.assertEqual(progress["progress_scope"], "active_stage")
        self.assertEqual(progress["unit_label"], "feature months")
        self.assertEqual(progress["ready_count"], 8)
        self.assertEqual(progress["expected_count"], 26)
        self.assertEqual(progress["parent_task_progress"]["progress_source"], "model_task_internal_stages")
        self.assertEqual(progress["parent_task_progress"]["expected_count"], 20)
        live_activity = task["detail"]["runtime_activity"]
        self.assertEqual(
            live_activity["activity_summary"],
            "Generating AAPL 2016-03-01 target-state features · 2016-02-25 to 2016-03-03 · targets AAPL, BTC, MSFT, NVDA",
        )
        self.assertEqual(live_activity["progress_label"], "8/26 feature months")
        self.assertEqual(live_activity["sample_targets"], ["AAPL", "BTC", "MSFT", "NVDA"])
        self.assertIn("Candidate symbols 50", live_activity["activity_details"])
        self.assertIn("Using target-local source rows", live_activity["activity_details"])

    def test_completed_model_task_runtime_spans_internal_stage_receipts(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            receipt_root = runtime / "model_training_stage_receipts"
            receipts: dict[str, Path] = {}
            for stage_name, started_at, completed_at in (
                ("data_acquisition", "2026-06-28T06:14:07Z", "2026-06-28T06:14:12Z"),
                ("feature_generation", "2026-06-28T06:14:12Z", "2026-06-28T07:19:52Z"),
                ("model_generation__train", "2026-06-28T07:19:58Z", "2026-06-28T07:25:03Z"),
                ("model_generation__validation", "2026-06-28T07:25:08Z", "2026-06-28T07:26:28Z"),
                ("model_generation__test", "2026-06-28T07:26:28Z", "2026-06-28T07:27:48Z"),
            ):
                receipt = receipt_root / f"model_02_target_state__{stage_name}" / "completion_receipt.json"
                receipt.parent.mkdir(parents=True, exist_ok=True)
                receipt.write_text(
                    json.dumps(
                        {
                            "started_at": started_at,
                            "completed_at": completed_at,
                            "status": "succeeded",
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
                receipts[stage_name] = receipt
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "receipt_refs": [str(receipts["data_acquisition"])],
                            },
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "receipt_refs": [str(receipts["feature_generation"])],
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                                "receipt_refs": [str(receipts["model_generation__train"])],
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "validation"},
                                "receipt_refs": [str(receipts["model_generation__validation"])],
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "test"},
                                "started_at_utc": "2026-06-28T07:26:28Z",
                                "ended_at_utc": "2026-06-28T07:27:48Z",
                                "receipt_refs": [str(receipts["model_generation__test"])],
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

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-28T07:28:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        self.assertEqual(task["status"], "succeeded")
        self.assertEqual(task["started_at_utc"], "2026-06-28T06:14:07Z")
        self.assertEqual(task["ended_at_utc"], "2026-06-28T07:27:48Z")
        self.assertEqual(task["receipt_count"], 5)

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
                                "stage_id": "model_02_target_state.option_chain_data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "blockers": ["upstream_model_04_evaluation_complete", "other_static_dependency"],
                                "last_reason": "waiting for upstream_model_04_evaluation_complete",
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
            any(task["task_id"] == "model_02_target_state" for task in payload["chart_payload"]["task_timeline"])
        )

    def test_layer_model_evaluation_is_hidden_from_public_timeline(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            workflow_state = tmp / "storage" / "02_control_plane" / "runtime" / "model_training_fold_state_aapl_2016-01_2017-06.json"
            workflow_state.parent.mkdir(parents=True, exist_ok=True)
            workflow_state.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.model_evaluation",
                                "stage_type": "model_evaluation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
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
        self.assertNotIn("model_02_target_state.model_evaluation", task_ids)
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
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
            self._write_target_queue(runtime, ["AAPL"])
            (runtime / "historical_workflow_transition_latest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_historical_workflow_transition",
                        "transition_id": "hwf-replay-waiting",
                        "task_status": "waiting",
                        "event_type": "task_waiting",
                        "selected_work": "model_group.replay",
                        "next_internal_stage": "model_group_replay",
                        "target_symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "reason_code": "waiting_for_model_group_lifecycle_tasks",
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
                "model_group.replay",
                "model_group.replay_review",
                "model_group.model_06_event_risk_governor",
                "model_group.evaluation",
                "model_group.promotion",
                "model_group.maintenance",
            ],
        )
        self.assertEqual(
            [task["stage_type"] for task in evaluation_tasks],
            ["replay", "replay_review", "model_06_event_risk_governor", "model_evaluation", "promotion_review", "maintenance"],
        )
        self.assertTrue(all(task["worker_id"] == "evaluation_worker_1" for task in evaluation_tasks))
        self.assertTrue(all(task["layer_key"] == "model_group" for task in evaluation_tasks))
        self.assertTrue(all(task["month"] == "2016-01..2017-06" for task in evaluation_tasks))
        self.assertTrue(all(task["dataset_unit_kind"] == "model_group_training_fold" for task in evaluation_tasks))
        self.assertTrue(all(task["dataset_unit_months"] == 18 for task in evaluation_tasks))
        self.assertEqual(evaluation_tasks[0]["detail"]["dataset_unit"]["start_month"], "2016-01")
        self.assertEqual(evaluation_tasks[0]["detail"]["dataset_unit"]["end_month"], "2017-06")
        self.assertEqual(evaluation_tasks[0]["detail"]["dataset_unit"]["unit_months"], 18)
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
        self.assertEqual(payload["chart_payload"]["current_month"], "2016-01..2017-06")
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
            self._write_target_queue(runtime, ["AAPL"])
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
        self.assertEqual(
            [task["task_id"] for task in model_group_tasks],
            [
                "model_group.replay",
                "model_group.replay_review",
                "model_group.model_06_event_risk_governor",
                "model_group.evaluation",
                "model_group.promotion",
                "model_group.maintenance",
            ],
        )
        self.assertEqual(model_group_tasks[0]["task_state"], "current")
        self.assertEqual(model_group_tasks[0]["status"], "blocked")
        self.assertEqual(model_group_tasks[0]["detail"]["blockers"], ["replay_dataset_preparation_manifest"])
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.replay")

    def test_replay_attempt_artifact_marks_replay_started_before_first_month_completes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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
            earlier_replay_run = replay_root / "replay_execution_runs" / "model_group_replay_20260624T150000Z"
            earlier_replay_run.mkdir(parents=True, exist_ok=True)
            (earlier_replay_run / "option_feature_requirements.jsonl").write_text(
                json.dumps(
                    {
                        "requirement_kind": "same_row_option_snapshot",
                        "target_ref": "AAPL",
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "month": "2021-01",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            replay_run = replay_root / "replay_execution_runs" / "model_group_replay_fixture"
            replay_run.mkdir(parents=True, exist_ok=True)
            (replay_run / "option_feature_requirements.jsonl").write_text(
                json.dumps(
                    {
                        "requirement_kind": "same_row_option_snapshot",
                        "target_ref": "AAPL",
                        "timestamp": "2021-01-05T16:00:00-05:00",
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

        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        self.assertEqual(replay_task["task_state"], "current")
        self.assertEqual(replay_task["status"], "ready")
        self.assertEqual(replay_task["started_at_utc"], "2026-06-24T15:00:00Z")
        self.assertEqual(replay_task["detail"]["progress"]["ready_count"], 0)
        self.assertEqual(replay_task["detail"]["progress"]["expected_count"], 2)
        self.assertIn("started and completed 0/2 replay months", replay_task["reason"])

    def test_running_replay_option_feature_drain_updates_live_cursor_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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
            earlier_replay_run = replay_root / "replay_execution_runs" / "model_group_replay_20260624T150000Z"
            earlier_replay_run.mkdir(parents=True, exist_ok=True)
            (earlier_replay_run / "option_feature_requirements.jsonl").write_text(
                json.dumps(
                    {
                        "requirement_kind": "same_row_option_snapshot",
                        "target_ref": "AAPL",
                        "timestamp": "2021-01-04T16:00:00-05:00",
                        "month": "2021-01",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            replay_run = replay_root / "replay_execution_runs" / "model_group_replay_fixture"
            replay_run.mkdir(parents=True, exist_ok=True)
            requirements_path = replay_run / "option_feature_requirements.jsonl"
            requirements_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "requirement_kind": "same_row_option_snapshot",
                                "target_ref": "AAPL",
                                "timestamp": "2021-02-01T16:00:00-05:00",
                                "month": "2021-02",
                            }
                        ),
                        json.dumps(
                            {
                                "requirement_kind": "same_row_option_snapshot",
                                "target_ref": "MSFT",
                                "timestamp": "2021-02-01T16:00:00-05:00",
                                "month": "2021-02",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            trace_path = replay_run / "replay_runtime_trace.jsonl"
            trace_path.write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_runtime_trace_row",
                        "trace_event_type": "replay_option_feature_requirements_blocked",
                        "replay_execution_run_id": "model_group_replay_fixture",
                        "replay_time_pointer": "2021-02-01T16:00:00-05:00",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            drain_status_path = tmp / "storage" / "02_control_plane" / "runtime" / "replay_option_feature_drain_latest.json"
            drain_status_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_replay_option_feature_drain_status",
                        "decision_status": "repair_incomplete",
                        "reason_code": "model_group_replay_option_feature_repair_incomplete",
                        "replay_time_pointer": "2021-02-01T16:00:00-05:00",
                        "source_missing_count": 42,
                        "source_ready_count": 18,
                        "provider_calls": 12,
                        "batch_index": 2,
                        "batch_size": 12,
                        "batch_count": 4,
                        "option_source_unavailable_count": 3,
                        "elapsed_seconds": 3,
                        "drain_started_at_utc": "2026-06-25T15:00:00Z",
                        "required_next_step": "continue_option_feature_repair",
                        "requirements_artifact_ref": str(requirements_path),
                        "emitted_at_utc": "2026-06-25T15:41:00Z",
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
                        "decision_status": "backoff",
                        "start_month": "2021-01",
                        "selected_work": "model_group.replay_option_features",
                        "next_internal_stage": "model_group.replay_option_features",
                        "reason_code": "model_group_replay_option_feature_repair_incomplete",
                        "reason": "replay option feature repair is still draining source gaps",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.write_text(json.dumps({"current_month": "2020-07", "start_month": "2020-07"}) + "\n", encoding="utf-8")
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-25T15:41:00Z")

        runtime_activity = payload["chart_payload"]["runtime_active_work"]["runtime_activity"]
        self.assertEqual(runtime_activity["activity_type"], "replay_option_feature_drain")
        self.assertEqual(runtime_activity["source_missing_count"], 42)
        self.assertEqual(runtime_activity["source_ready_count"], 18)
        self.assertEqual(runtime_activity["provider_calls"], 12)
        self.assertEqual(runtime_activity["sample_targets"], ["AAPL", "MSFT"])
        self.assertEqual(runtime_activity["started_at_utc"], "2026-06-25T15:00:00Z")
        self.assertEqual(runtime_activity["elapsed_seconds"], 3)
        self.assertEqual(runtime_activity["replay_runtime_trace_ref"], str(trace_path))
        self.assertEqual(runtime_activity["requirement_count"], 2)
        self.assertIn("2 total frontier requirements", runtime_activity["activity_summary"])
        self.assertIn("42 source-gap candidates in current repair slice", runtime_activity["activity_summary"])
        self.assertIn("targets AAPL, MSFT", runtime_activity["activity_summary"])
        self.assertNotIn("source gaps remain", runtime_activity["activity_summary"])
        self.assertNotIn("sample AAPL", runtime_activity["activity_summary"])
        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        self.assertEqual(replay_task["status"], "running")
        self.assertEqual(replay_task["started_at_utc"], "2026-06-24T15:00:00Z")
        self.assertEqual(replay_task["updated_at_utc"], "2026-06-25T15:41:00Z")
        self.assertEqual(replay_task["detail"]["runtime_activity"]["source_missing_count"], 42)
        self.assertEqual(replay_task["detail"]["progress"]["expected_count"], 2)
        self.assertEqual(replay_task["detail"]["progress"]["ready_count"], 0)
        self.assertEqual(replay_task["detail"]["progress"]["active_count"], 2)
        self.assertEqual(replay_task["detail"]["progress"]["active_month"], "2021-02")
        self.assertEqual(
            replay_task["detail"]["progress"]["active_time_pointer"],
            "2021-02-01T16:00:00-05:00",
        )

    def test_replay_option_feature_activity_ready_status_does_not_show_stale_requirements(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            service = tmp / "service"
            env = tmp / "env"
            wrapper = tmp / "wrapper"
            for path in (service, env, wrapper):
                path.write_text("", encoding="utf-8")
            replay_run = (
                tmp
                / "storage"
                / "05_replay_datasets"
                / "promotion_replay_candidate_policy"
                / "replay_execution_runs"
                / "model_group_replay_fixture"
            )
            replay_run.mkdir(parents=True, exist_ok=True)
            (replay_run / "option_feature_requirements.jsonl").write_text(
                json.dumps(
                    {
                        "requirement_kind": "same_row_option_snapshot",
                        "target_ref": "AAPL",
                        "timestamp": "2021-02-01T16:00:00-05:00",
                        "month": "2021-02",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            drain_status_path = tmp / "storage" / "02_control_plane" / "runtime" / "replay_option_feature_drain_latest.json"
            drain_status_path.parent.mkdir(parents=True, exist_ok=True)
            drain_status_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_replay_option_feature_drain_status",
                        "decision_status": "executed",
                        "reason_code": "model_group_replay_option_features_already_ready",
                        "source_missing_count": 0,
                        "source_ready_count": 0,
                        "provider_calls": 0,
                        "batch_index": 2,
                        "batch_size": 12,
                        "batch_count": 0,
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
                        "selected_work": "model_group.replay_option_features",
                        "next_internal_stage": "model_group.replay_option_features",
                        "reason_code": "model_group_replay_option_features_already_ready",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.write_text(json.dumps({"current_month": "2020-07", "start_month": "2020-07"}) + "\n", encoding="utf-8")
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-25T15:41:00Z")

        runtime_activity = payload["chart_payload"]["runtime_active_work"]["runtime_activity"]
        self.assertEqual(runtime_activity["source_missing_count"], 0)
        self.assertIsNone(runtime_activity["requirements_artifact_ref"])
        self.assertIsNone(runtime_activity["requirement_count"])
        self.assertEqual(runtime_activity["sample_targets"], [])
        self.assertIn("0 source-gap candidates in current repair slice", runtime_activity["activity_summary"])
        self.assertNotIn("AAPL", runtime_activity["activity_summary"])

    def test_running_replay_execution_trace_updates_live_cursor_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
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
            replay_run = replay_root / "replay_execution_runs" / "model_group_replay_20260625T150000Z"
            replay_run.mkdir(parents=True, exist_ok=True)
            trace_path = replay_run / "replay_runtime_trace.jsonl"
            trace_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "contract_type": "evaluation_replay_runtime_trace_row",
                                "trace_event_type": "replay_clock_processed",
                                "replay_execution_run_id": "model_group_replay_20260625T150000Z",
                                "replay_month": "2021-01",
                                "replay_time_pointer": "2021-01-04T16:00:00-05:00",
                                "generated_at_utc": "2026-06-25T15:00:01Z",
                                "cumulative_summary": {"timestamp_count": 1},
                            }
                        ),
                        json.dumps(
                            {
                                "contract_type": "evaluation_replay_runtime_trace_row",
                                "trace_event_type": "replay_clock_processed",
                                "replay_execution_run_id": "model_group_replay_20260625T150000Z",
                                "replay_month": "2021-02",
                                "replay_time_pointer": "2021-02-03T16:00:00-05:00",
                                "generated_at_utc": "2026-06-25T15:01:00Z",
                                "selected_targets": ["MSFT"],
                                "cumulative_summary": {"timestamp_count": 21},
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            drain_status_path = runtime / "replay_option_feature_drain_latest.json"
            drain_status_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_replay_option_feature_drain_status",
                        "decision_status": "executed",
                        "reason_code": "model_group_replay_option_features_already_ready",
                        "source_missing_count": 0,
                        "source_ready_count": 0,
                        "provider_calls": 0,
                        "emitted_at_utc": "2026-06-25T14:59:00Z",
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
                        "selected_work": "model_group.replay_option_features",
                        "next_internal_stage": "model_group.replay_option_features",
                        "reason_code": "model_group_replay_option_features_already_ready",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.write_text(json.dumps({"current_month": "2020-07", "start_month": "2020-07"}) + "\n", encoding="utf-8")
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-25T15:01:05Z")

        runtime_activity = payload["chart_payload"]["runtime_active_work"]["runtime_activity"]
        self.assertEqual(runtime_activity["activity_type"], "replay_execution")
        self.assertEqual(runtime_activity["replay_time_pointer"], "2021-02-03T16:00:00-05:00")
        self.assertIn("21 replay timestamps processed", runtime_activity["activity_summary"])
        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        progress = replay_task["detail"]["progress"]
        self.assertEqual(progress["active_month"], "2021-02")
        self.assertEqual(progress["active_time_pointer"], "2021-02-03T16:00:00-05:00")
        self.assertEqual(progress["current_count"], 2)

    def test_replay_progress_uses_high_water_when_drain_status_has_no_cursor(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 3,
                        "available_feed_acquisition_count": 3,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 0,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (replay_root / "feed_acquisition_plan.csv").write_text(
                "month\n2021-01\n2021-02\n2021-03\n",
                encoding="utf-8",
            )
            replay_run = replay_root / "replay_execution_runs" / "model_group_replay_frontier"
            replay_run.mkdir(parents=True)
            trace_path = replay_run / "replay_runtime_trace.jsonl"
            trace_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "contract_type": "evaluation_replay_runtime_trace_row",
                                "trace_event_type": "replay_clock_processed",
                                "replay_execution_run_id": replay_run.name,
                                "replay_month": "2021-01",
                                "replay_time_pointer": "2021-01-04T16:00:00-05:00",
                                "generated_at_utc": "2026-06-25T15:00:00Z",
                                "cumulative_summary": {"timestamp_count": 1},
                            }
                        ),
                        json.dumps(
                            {
                                "contract_type": "evaluation_replay_runtime_trace_row",
                                "trace_event_type": "replay_option_feature_requirements_blocked",
                                "replay_execution_run_id": replay_run.name,
                                "replay_month": "2021-02",
                                "replay_time_pointer": "2021-02-03T16:00:00-05:00",
                                "generated_at_utc": "2026-06-25T15:01:00Z",
                                "missing_option_feature_requirement_count": 7,
                                "cumulative_summary": {
                                    "timestamp_count": 21,
                                    "missing_option_feature_requirement_count": 7,
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            drain_status_path = runtime / "replay_option_feature_drain_latest.json"
            drain_status_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_replay_option_feature_drain_status",
                        "decision_status": "backoff",
                        "reason_code": "model_group_replay_option_feature_repair_incomplete",
                        "source_missing_count": 0,
                        "source_ready_count": 0,
                        "provider_calls": 0,
                        "batch_index": 2,
                        "required_next_step": "retry model_group.replay",
                        "emitted_at_utc": "2026-06-25T15:02:00Z",
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
                        "decision_status": "backoff",
                        "selected_work": "model_group.replay_option_features",
                        "next_internal_stage": "model_group.replay_option_features",
                        "reason_code": "model_group_replay_option_feature_repair_incomplete",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.write_text(json.dumps({"current_month": "2020-07", "start_month": "2020-07"}) + "\n", encoding="utf-8")
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-25T15:02:05Z")

        runtime_activity = payload["chart_payload"]["runtime_active_work"]["runtime_activity"]
        self.assertEqual(runtime_activity["activity_type"], "replay_option_feature_drain")
        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        progress = replay_task["detail"]["progress"]
        self.assertEqual(progress["active_month"], "2021-02")
        self.assertEqual(progress["active_time_pointer"], "2021-02-03T16:00:00-05:00")
        self.assertEqual(progress["current_count"], 2)
        self.assertIn("has reached 2/3 replay months", replay_task["reason"])
        self.assertIn("0/3 months have closed with terminal replay receipts", replay_task["reason"])

    def test_running_replay_retry_keeps_frontier_high_water_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 16,
                        "available_feed_acquisition_count": 16,
                        "deferred_feed_acquisition_count": 0,
                        "missing_feed_acquisition_count": 0,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            months = [f"2021-{month:02d}" for month in range(1, 13)] + [f"2022-{month:02d}" for month in range(1, 5)]
            (replay_root / "feed_acquisition_plan.csv").write_text(
                "month\n" + "\n".join(months) + "\n",
                encoding="utf-8",
            )
            runs_root = replay_root / "replay_execution_runs"
            bad_run = runs_root / "model_group_replay_bad_future_gap"
            good_run = runs_root / "model_group_replay_frontier_high_water"
            retry_run = runs_root / "model_group_replay_retry_from_start"
            for run in (bad_run, good_run, retry_run):
                run.mkdir(parents=True, exist_ok=True)
            (bad_run / "replay_runtime_trace.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_runtime_trace_row",
                        "trace_event_type": "replay_option_feature_requirements_blocked",
                        "replay_execution_run_id": bad_run.name,
                        "replay_month": "2025-12",
                        "replay_time_pointer": "2025-12-30T16:00:00-05:00",
                        "missing_option_feature_requirement_count": 188,
                        "cumulative_summary": {
                            "timestamp_count": 244,
                            "missing_option_feature_requirement_count": 174236,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (good_run / "replay_runtime_trace.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_runtime_trace_row",
                        "trace_event_type": "replay_option_feature_requirements_blocked",
                        "replay_execution_run_id": good_run.name,
                        "replay_month": "2022-04",
                        "replay_time_pointer": "2022-04-25T16:00:00-04:00",
                        "missing_option_feature_requirement_count": 91,
                        "generated_at_utc": "2026-06-25T15:50:00Z",
                        "cumulative_summary": {
                            "timestamp_count": 329,
                            "missing_option_feature_requirement_count": 91,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (retry_run / "replay_runtime_trace.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_runtime_trace_row",
                        "trace_event_type": "replay_clock_processed",
                        "replay_execution_run_id": retry_run.name,
                        "replay_month": "2021-02",
                        "replay_time_pointer": "2021-02-17T16:00:00-05:00",
                        "generated_at_utc": "2026-06-25T15:55:00Z",
                        "cumulative_summary": {"timestamp_count": 31},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            os.utime(bad_run / "replay_runtime_trace.jsonl", (1000, 1000))
            os.utime(good_run / "replay_runtime_trace.jsonl", (2000, 2000))
            os.utime(retry_run / "replay_runtime_trace.jsonl", (3000, 3000))
            drain_status_path = runtime / "replay_option_feature_drain_latest.json"
            drain_status_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_replay_option_feature_drain_status",
                        "decision_status": "executed",
                        "reason_code": "model_group_replay_option_features_already_ready",
                        "source_missing_count": 0,
                        "source_ready_count": 0,
                        "provider_calls": 0,
                        "emitted_at_utc": "2026-06-25T15:51:00Z",
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
                        "selected_work": "model_group.replay_option_features",
                        "next_internal_stage": "model_group.replay_option_features",
                        "reason_code": "model_group_replay_option_features_already_ready",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_path = tmp / "runtime" / "historical_scheduler_state.json"
            state_path.write_text(json.dumps({"current_month": "2020-07", "start_month": "2020-07"}) + "\n", encoding="utf-8")
            lock_path = tmp / "runtime" / "historical_scheduler.lock"
            lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")
            status = collect_historical_scheduler_status(
                storage_root=tmp / "storage" / "02_control_plane",
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                service_template_path=service,
                service_env_path=env,
                daemon_wrapper_path=wrapper,
            )

            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-25T15:55:05Z")

        runtime_activity = payload["chart_payload"]["runtime_active_work"]["runtime_activity"]
        self.assertEqual(runtime_activity["activity_type"], "replay_execution")
        self.assertTrue(runtime_activity["retrying_from_earlier_clock"])
        self.assertEqual(runtime_activity["replay_time_pointer"], "2021-02-17T16:00:00-05:00")
        self.assertEqual(runtime_activity["furthest_replay_time_pointer"], "2022-04-25T16:00:00-04:00")
        self.assertIn("current run 2021-02-17T16:00:00-05:00", runtime_activity["activity_summary"])
        self.assertIn("furthest reached 2022-04-25T16:00:00-04:00", runtime_activity["activity_summary"])
        self.assertNotIn("2025-12", runtime_activity["activity_summary"])
        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        progress = replay_task["detail"]["progress"]
        self.assertEqual(progress["active_month"], "2022-04")
        self.assertEqual(progress["active_time_pointer"], "2022-04-25T16:00:00-04:00")
        self.assertEqual(progress["current_run_month"], "2021-02")
        self.assertEqual(progress["current_run_time_pointer"], "2021-02-17T16:00:00-05:00")
        self.assertEqual(progress["current_count"], 16)

    def test_task_timeline_shows_fixed_model_group_lifecycle_for_later_fold_blocked_by_lane(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            self._write_completed_pre_replay_fold(runtime, symbol="AAPL")
            fold2 = runtime / "model_training_fold_state_aapl_2017-01_2018-06.json"
            fold2.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2018-06",
                        "stages": [
                            {
                                "stage_id": f"model_{layer:02d}_fixture.model_generation",
                                "stage_type": "model_generation",
                                "layer": layer,
                                "layer_key": f"model_{layer:02d}_fixture",
                                "status": "succeeded" if layer <= 2 else "blocked",
                                "last_reason": "waiting for pre-replay input" if layer > 2 else "stage complete",
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_target_fold",
                                    "unit_months": 18,
                                    "start_month": "2017-01",
                                    "end_month": "2018-06",
                                    "target_required": layer >= 3,
                                    "target_symbol": "AAPL" if layer >= 3 else None,
                                },
                            }
                            for layer in range(1, 7)
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

        fold1_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-01..2017-06"]
        fold2_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2017-01..2018-06"]
        self.assertEqual(len(fold1_tasks), 11)
        self.assertEqual(
            [task["task_label"] for task in fold1_tasks],
            [
                "Model 01 Fixture",
                "Model 02 Fixture",
                "Model 03 Fixture",
                "Model 04 Fixture",
                "Model 05 Fixture",
                "Model Replay",
                "Replay Review",
                "M06 Event Risk Governor",
                "Model Evaluation",
                "Model Promotion",
                "Model Maintenance",
            ],
        )
        self.assertTrue(fold2_tasks)
        blocked_fold2_tasks = [task for task in fold2_tasks if task["task_state"] == "blocked"]
        self.assertTrue(blocked_fold2_tasks)
        self.assertEqual(blocked_fold2_tasks[0]["status"], "blocked")
        self.assertIn("previous_fold_complete:2016-01..2017-06", blocked_fold2_tasks[0]["detail"]["blockers"])
        self.assertTrue(blocked_fold2_tasks[0]["detail"]["single_fold_lane_blocked"])
        replay_task = next(task for task in fold1_tasks if task["task_id"] == "model_group.replay")
        self.assertEqual(replay_task["task_state"], "current")
        self.assertEqual(replay_task["detail"]["blockers"], ["replay_dataset_preparation_manifest"])

    def test_task_timeline_attaches_lifecycle_rows_for_each_completed_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)

            def write_completed_fold(start: str, end: str) -> None:
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
                                "dataset_split": {"split_name": split_name},
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_target_fold",
                                    "unit_months": 18,
                                    "start_month": start,
                                    "end_month": end,
                                    "target_required": layer >= 3,
                                    "target_symbol": "AAPL" if layer >= 3 else None,
                                },
                            }
                        )
                (runtime / f"model_training_fold_state_aapl_{start}_{end}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_model_training_workflow_state",
                            "start_month": start,
                            "end_month": end,
                            "stages": stages,
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )

            write_completed_fold("2016-01", "2017-06")
            write_completed_fold("2017-01", "2018-06")
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "candidate_fold_id": "fold_aapl_2017",
                        "fold_id": "fold_aapl_2017",
                        "freeze_status": "not_frozen",
                        "feed_acquisition_count": 1,
                        "available_feed_acquisition_count": 1,
                        "missing_feed_acquisition_count": 0,
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
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

        fold1_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-01..2017-06"]
        fold1_lifecycle_tasks = [task for task in fold1_tasks if str(task["task_id"]).startswith("model_group.")]
        self.assertEqual(
            [task["task_id"] for task in fold1_lifecycle_tasks],
            [
                "model_group.replay",
                "model_group.replay_review",
                "model_group.model_06_event_risk_governor",
                "model_group.evaluation",
                "model_group.promotion",
                "model_group.maintenance",
            ],
        )
        self.assertFalse(any(task["task_state"] == "skipped" for task in fold1_lifecycle_tasks))
        self.assertFalse(any(task["status"] == "not_applicable" for task in fold1_lifecycle_tasks))
        self.assertFalse(any("historical_lifecycle_scope_status" in task["detail"] for task in fold1_lifecycle_tasks))
        self.assertTrue(
            any(
                task["month"] == "2017-01..2018-06" and task["task_id"] == "model_group.replay" and task["status"] != "not_applicable"
                for task in payload["chart_payload"]["task_timeline"]
            )
        )

    def test_model_group_replay_does_not_attach_stale_dataset_operations_to_later_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            replay_root = tmp / "storage" / "05_replay_datasets" / "promotion_replay_candidate_policy"
            replay_root.mkdir(parents=True, exist_ok=True)
            (replay_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "candidate_fold_id": "fold_aapl_2016",
                        "fold_id": "fold_aapl_2016",
                        "freeze_status": "frozen",
                        "feed_acquisition_count": 180,
                        "available_feed_acquisition_count": 180,
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
            (replay_root / "feed_acquisition_plan.csv").write_text(
                "contract_id,source_id,month,coverage_status\n"
                "promotion_replay_candidate_policy,alpaca_bars,2025-12,available\n"
                "promotion_replay_candidate_policy,gdelt_news,2025-12,available\n"
                "promotion_replay_candidate_policy,trading_economics_calendar_web,2025-12,available\n",
                encoding="utf-8",
            )
            stale_run = replay_root / "replay_execution_runs" / "model_group_replay_20260611T154500Z"
            stale_run.mkdir(parents=True, exist_ok=True)
            (stale_run / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_execution_receipt",
                        "replay_execution_run_id": stale_run.name,
                        "started_at_utc": "2026-06-11T15:45:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            tasks = _model_group_replay_timeline_tasks(
                storage_root=tmp / "storage" / "02_control_plane",
                generated_at_utc="2026-06-11T15:45:00Z",
                starting_sequence=0,
                selected_target_symbol="AAPL",
                training_start_month="2017-01",
                training_end_month="2018-06",
                pre_replay_complete=False,
                use_lifecycle_artifacts=False,
            )

        replay_task = next(task for task in tasks if task["task_id"] == "model_group.replay")
        self.assertEqual(replay_task["task_state"], "future")
        self.assertEqual(replay_task["status"], "blocked")
        self.assertEqual(replay_task["detail"]["blockers"], ["fold_models_01_05_model_generation_complete"])
        self.assertIsNone(replay_task.get("started_at_utc"))
        self.assertNotIn("replay_month_operation", replay_task["detail"])
        self.assertNotIn("Replay month 2025-12 is incomplete", replay_task["reason"])
        self.assertIn("Waiting for pre-replay M01-M05 model generation", replay_task["reason"])

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
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
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
        self.assertEqual(replay_task["status"], "running")
        self.assertEqual(replay_task["task_state"], "current")
        self.assertEqual(replay_task["detail"]["blockers"], [])
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.replay")
        self.assertEqual(payload["chart_payload"]["current_month"], "2016-01..2017-06")

    def test_replay_dataset_manifest_fold_id_does_not_block_model_group_replay(self):
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
                        "candidate_fold_id": "2017-01..2018-06",
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
            self._write_target_queue(runtime, ["AAPL"])
            (runtime / "historical_workflow_transition_latest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_historical_workflow_transition",
                        "transition_id": "hwf-replay-complete",
                        "task_status": "waiting",
                        "event_type": "task_waiting",
                        "selected_work": "model_group.replay",
                        "next_internal_stage": "model_group_replay",
                        "target_symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "reason_code": "waiting_for_model_group_lifecycle_tasks",
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
        self.assertEqual(replay_task["status"], "running")
        self.assertNotIn("replay_dataset_scope_matches_training_fold", replay_task["detail"]["blockers"])
        self.assertNotIn("does not match completed training fold", replay_task["reason"])

    def test_replay_completion_surfaces_residual_event_governance_ready_despite_internal_lifecycle_hold(self):
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
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        },
                        "replay_completion_scope": "full_candidate_universe",
                        "completed_replay_month_count": 2,
                        "max_decision_rows": None,
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
            self._write_target_queue(runtime, ["AAPL"])
            (runtime / "historical_workflow_transition_latest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_historical_workflow_transition",
                        "transition_id": "hwf-replay-complete",
                        "task_status": "waiting",
                        "event_type": "task_waiting",
                        "selected_work": "model_group.replay",
                        "next_internal_stage": "model_group_replay",
                        "target_symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "reason_code": "waiting_for_model_group_lifecycle_tasks",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-22T12:31:00Z")

        self.assertEqual(status.current_stage, "model_group.replay")
        self.assertEqual(status.blocked_reason, "waiting_for_model_group_lifecycle_tasks")
        replay_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay")
        replay_review_task = next(
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["task_id"] == "model_group.replay_review"
        )
        self.assertEqual(replay_task["status"], "succeeded")
        self.assertEqual(replay_task["task_state"], "completed")
        self.assertEqual(replay_review_task["status"], "running")
        self.assertEqual(replay_review_task["task_state"], "current")
        self.assertEqual(replay_review_task["detail"]["progress"]["unit_label"], "review rows")
        self.assertEqual(replay_review_task["detail"]["progress"]["expected_count"], 2)
        self.assertEqual(replay_review_task["detail"]["progress"]["ready_count"], 0)
        self.assertEqual(replay_review_task["detail"]["progress"]["pending_count"], 2)
        self.assertEqual(replay_review_task["detail"]["progress"]["progress_source"], "post_replay_review_rows")
        self.assertEqual(payload["chart_payload"]["active_stage"], "model_group.replay_review")
        self.assertEqual(payload["chart_payload"]["blocker_category"], None)
        self.assertEqual(payload["status"], "running")
        self.assertIn("Replay Review", payload["summary"])
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
            self._write_post_replay_review_receipt(replay_root)
            self._write_post_replay_attribution_receipt(replay_root)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": f"model_{layer:02d}_fixture.model_generation",
                                "stage_type": "model_generation",
                                "layer": layer,
                                "layer_key": f"model_{layer:02d}_fixture",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_target_fold",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_symbol": "AAPL" if layer >= 3 else None,
                                },
                            }
                            for layer in range(1, 7)
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

        lifecycle_tasks = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if str(task["task_id"]).startswith("model_group.")
        ]
        self.assertEqual(
            [task["task_id"] for task in lifecycle_tasks],
            [
                "model_group.replay",
                "model_group.replay_review",
                "model_group.model_06_event_risk_governor",
                "model_group.evaluation",
                "model_group.promotion",
                "model_group.maintenance",
            ],
        )
        self.assertEqual(lifecycle_tasks[0]["status"], "blocked")
        self.assertIn("model_group.replay", {task["task_id"] for task in lifecycle_tasks})
        self.assertNotEqual(payload["chart_payload"]["active_stage"], "model_group.model_06_event_risk_governor")

    def test_data_acquisition_progress_aggregates_fold_source_month_requests(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            fold_state = runtime / "model_training_fold_state_aapl_2016-01_2017-06.json"
            fold_state.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "ready",
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_panel",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_required": False,
                                },
                            },
                            {
                                "stage_id": "model_01_market_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "blocked",
                                "blockers": ["model_01_market_context.data_acquisition_complete"],
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
                (coverage_root / f"model_01_market_context_data_acquisition_{month}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_stage_coverage",
                            "stage_id": "model_01_market_context.data_acquisition",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_01_market_context")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "fold_stage_coverage")
        self.assertEqual(progress["unit_label"], "source-month requests")
        self.assertEqual(progress["expected_count"], 30)
        self.assertEqual(progress["ready_count"], 8)
        self.assertEqual(progress["pending_count"], 22)
        self.assertEqual(progress["covered_partition_count"], 3)
        self.assertEqual(progress["expected_partition_count"], 18)

    def test_feature_generation_progress_uses_fold_month_partitions(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "fold_feature_generation_partitions")
        self.assertEqual(progress["unit_label"], "feature months")
        self.assertEqual(progress["expected_count"], 18)
        self.assertEqual(progress["ready_count"], 0)
        self.assertEqual(progress["pending_count"], 18)
        self.assertIn("12+3+3 walk-forward fold", progress["progress_basis"])

    def test_task_timeline_ignores_stale_non_eighteen_month_fold_state_for_live_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            env.write_text(
                "TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS=300\nTRADING_MANAGER_SELECTED_TARGET_SYMBOL=AAPL\n",
                encoding="utf-8",
            )
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            stale_payload = {
                "contract_type": "manager_model_training_workflow_state",
                "start_month": "2016-01",
                "end_month": "2016-12",
                "stages": [
                    {
                        "stage_id": "model_02_target_state.feature_generation",
                        "stage_type": "feature_generation",
                        "layer": 3,
                        "layer_key": "model_02_target_state",
                        "status": "ready",
                    }
                ],
            }
            current_payload = {
                "contract_type": "manager_model_training_workflow_state",
                "start_month": "2016-01",
                "end_month": "2017-06",
                "stages": [
                    {
                        "stage_id": "model_02_target_state.data_acquisition",
                        "stage_type": "data_acquisition",
                        "layer": 3,
                        "layer_key": "model_02_target_state",
                        "status": "succeeded",
                    },
                    {
                        "stage_id": "model_02_target_state.feature_generation",
                        "stage_type": "feature_generation",
                        "layer": 3,
                        "layer_key": "model_02_target_state",
                        "status": "ready",
                    },
                ],
            }
            (runtime / "model_training_fold_state_aapl_2016-01_2016-12.json").write_text(
                json.dumps(stale_payload) + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(current_payload) + "\n",
                encoding="utf-8",
            )
            write_task_progress_node(
                progress_root=runtime / "task_progress",
                worker_id="model_worker_1",
                task_uid="2016-01..2017-06:model_02_target_state.feature_generation",
                stage_id="model_02_target_state.feature_generation",
                unit_label="feature months",
                processed_count=4,
                expected_count=18,
                node_id="feature_generation_window_started",
                node_label="Feature generation running",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-29T19:59:30Z")

        timeline = payload["chart_payload"]["task_timeline"]
        self.assertFalse(any(task["month"] == "2016-01..2016-12" for task in timeline))
        task = next(task for task in timeline if task["task_id"] == "model_02_target_state")
        self.assertEqual(task["month"], "2016-01..2017-06")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["detail"]["progress"]["status"], "running")
        self.assertEqual(task["detail"]["progress"]["stage_id"], "model_02_target_state.feature_generation")
        self.assertEqual(task["detail"]["runtime_activity"]["progress_label"], "4/18 feature months")

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
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_01_sector_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "ready",
                                "last_reason": (
                                    "rerun reset from model_01_sector_context.data_acquisition: M02 sector-context "
                                    "contract changed; reset AAPL fold M02 and downstream generated workflow state."
                                ),
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_panel",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_required": False,
                                },
                            },
                            {
                                "stage_id": "model_01_sector_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "blocked",
                                "blockers": ["model_01_sector_context.data_acquisition_complete"],
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
                task["month"] == "2016-01..2017-06"
                and task["task_id"] == "model_01_sector_context"
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
                        "rotation_boundary": "model_02_plus_model_worker",
                        "targets": [{"symbol": "AAPL"}, {"symbol": "NVDA"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.model_task",
                                "stage_type": "model_task",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_panel",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_required": False,
                                    "target_symbol": None,
                                },
                            },
                            {
                                "stage_id": "model_06_residual_event_governance.model_task",
                                "stage_type": "model_task",
                                "layer": 6,
                                "layer_key": "model_06_residual_event_governance",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "model_05_option_expression.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 5,
                                "layer_key": "model_05_option_expression",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
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
        model_six = next(task for task in tasks if task["layer"] == 6)
        model_five = next(task for task in tasks if task["task_id"] == "model_05_option_expression")
        self.assertEqual(layer_one["target_scope"], "market_context_panel")
        self.assertEqual(layer_one["instrument_scope"], "market_context_proxy_panel")
        self.assertEqual(model_six["target_scope"], "target_symbol")
        self.assertEqual(model_six["instrument_scope"], "residual_event_governance")
        self.assertEqual(model_five["instrument_scope"], "option_expression_or_underlying_fallback")
        self.assertEqual(payload["chart_payload"]["target_queue"]["enabled_targets"], ["AAPL", "NVDA"])

    def test_model_generation_progress_uses_dataset_splits_without_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_split": {"split_name": "validation"},
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "blockers": ["model_02_target_state.model_generation.validation_complete"],
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "model_task_internal_stages")
        self.assertEqual(progress["unit_label"], "task units")
        self.assertEqual(progress["expected_count"], 20)
        self.assertEqual(progress["ready_count"], 14)
        self.assertEqual(progress["active_count"], 14)
        self.assertEqual(progress["pending_count"], 6)
        self.assertIn("all layer-internal", progress["progress_basis"])
        self.assertEqual(task["detail"]["active_stage_id"], "model_02_target_state.model_generation.validation")
        internal_stages = {stage["stage_id"]: stage for stage in task["detail"]["internal_stages"]}
        self.assertEqual(internal_stages["model_02_target_state.data_acquisition"]["progress"]["ready_count"], 1)
        self.assertEqual(internal_stages["model_02_target_state.feature_generation"]["progress"]["ready_count"], 1)
        self.assertEqual(
            internal_stages["model_02_target_state.model_generation.train"]["progress"]["ready_count"],
            12,
        )
        self.assertEqual(
            internal_stages["model_02_target_state.model_generation.validation"]["progress"]["expected_count"],
            3,
        )
        self.assertEqual(
            internal_stages["model_02_target_state.model_generation.test"]["progress"]["status"],
            "blocked",
        )

    def test_stage_started_model_generation_uses_parent_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_split": {"split_name": "validation"},
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "blockers": ["model_02_target_state.model_generation.validation_complete"],
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
                task_uid="2016-01..2017-06:model_02_target_state.model_generation.validation",
                stage_id="model_02_target_state.model_generation.validation",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "model_task_internal_stages")
        self.assertEqual(progress["unit_label"], "task units")
        self.assertEqual(progress["expected_count"], 18)
        self.assertEqual(progress["ready_count"], 12)
        live_activity = task["detail"]["runtime_activity"]
        self.assertEqual(live_activity["activity_summary"], "Stage process started")
        self.assertEqual(live_activity["progress_label"], "12/18 task units")
        self.assertFalse(any("Worker completed" in line for line in live_activity["activity_details"]))
        internal_stages = {stage["stage_id"]: stage for stage in task["detail"]["internal_stages"]}
        validation_stage = internal_stages["model_02_target_state.model_generation.validation"]
        self.assertEqual(validation_stage["progress"]["progress_source"], "internal_stage_progress")
        self.assertEqual(validation_stage["progress"]["expected_count"], 3)
        self.assertEqual(validation_stage["progress"]["unit_label"], "dataset months")
        self.assertEqual(validation_stage["runtime_activity"]["activity_summary"], "Stage process started")
        self.assertEqual(validation_stage["runtime_activity"]["progress_label"], "0/3 dataset months")

    def test_completed_model_task_ignores_model_row_count_for_progress(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "train"},
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.validation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "validation"},
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_split": {"split_name": "test"},
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        progress = task["detail"]["progress"]
        self.assertEqual(progress["progress_source"], "model_task_internal_stages")
        self.assertEqual(progress["unit_label"], "task units")
        self.assertEqual(progress["expected_count"], 18)
        self.assertEqual(progress["ready_count"], 18)
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
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "model_02_target_candidate_handoff",
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        },
                        "replay_completion_scope": "full_candidate_universe",
                        "max_decision_rows": None,
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
            self._write_post_replay_review_receipt(replay_root)
            attribution_receipt_path = self._write_post_replay_attribution_receipt(replay_root)
            event_focus_proposals_path = attribution_receipt_path.parent / "event_focus_proposals.jsonl"
            (review_root / "model_group_evaluation_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "model_group_evaluation_receipt",
                        "status": "succeeded",
                        "created_at_utc": "2026-05-22T12:50:00Z",
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "candidate_fold_id": "fold_aapl_2016",
                        "replay_execution_receipt_ref": str(replay_run / "replay_execution_receipt.json"),
                        "residual_event_governance_receipt_ref": str(attribution_receipt_path),
                        "residual_event_governance_event_focus_proposals_ref": str(event_focus_proposals_path),
                    }
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

    def test_model_group_promotion_rejected_is_public_terminal_task(self):
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
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        },
                        "replay_completion_scope": "full_candidate_universe",
                        "max_decision_rows": None,
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
            (review_root / "model_group_evaluation_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "model_group_evaluation_receipt",
                        "status": "succeeded",
                        "created_at_utc": "2026-05-22T12:50:00Z",
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "candidate_fold_id": "fold_aapl_2016",
                        "replay_execution_receipt_ref": str(replay_run / "replay_execution_receipt.json"),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (review_root / "promotion_evaluation_review.json").write_text(
                json.dumps(
                    {
                        "recommendation": "failed",
                        "blocking_issues": ["settlement gate failure: drawdown_too_severe"],
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
                        "decision_status": "rejected",
                        "decision_reason": "Candidate failed drawdown guardrail.",
                        "replay_validation_ref": str(replay_run / "replay_execution_receipt.json"),
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
        self.assertEqual(promotion_task["status"], "rejected")
        self.assertEqual(promotion_task["task_state"], "completed")
        self.assertEqual(promotion_task["started_at_utc"], "2026-05-22T12:50:00Z")
        self.assertEqual(promotion_task["ended_at_utc"], "2026-05-22T12:50:00Z")
        self.assertEqual(promotion_task["detail"]["blockers"], ["settlement gate failure: drawdown_too_severe"])
        self.assertEqual(payload["status"], "complete")
        self.assertIsNone(payload["chart_payload"]["active_stage"])
        self.assertIsNone(payload["chart_payload"]["active_task"])
        self.assertIn("Model Evaluation completed; Model Promotion is rejected", payload["summary"])
        self.assertNotIn("current public task is Model Replay", payload["summary"])
        self.assertEqual(maintenance_task["status"], "not_applicable")
        self.assertEqual(maintenance_task["task_state"], "skipped")

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
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "pre_replay_target_refs": ["AAPL"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        },
                        "replay_completion_scope": "full_candidate_universe",
                        "max_decision_rows": None,
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
            self._write_post_replay_review_receipt(replay_root)
            attribution_receipt_path = self._write_post_replay_attribution_receipt(replay_root)
            event_focus_proposals_path = attribution_receipt_path.parent / "event_focus_proposals.jsonl"
            (review_root / "model_group_evaluation_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "model_group_evaluation_receipt",
                        "status": "succeeded",
                        "created_at_utc": "2026-05-22T12:50:00Z",
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "candidate_fold_id": "fold_aapl_2016",
                        "replay_execution_receipt_ref": str(replay_run / "replay_execution_receipt.json"),
                        "residual_event_governance_receipt_ref": str(attribution_receipt_path),
                        "residual_event_governance_event_focus_proposals_ref": str(event_focus_proposals_path),
                    }
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
        replay_review_task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_group.replay_review")
        replay_review_summary = replay_review_task["detail"]["replay_review_diagnostic_summary"]
        self.assertEqual(replay_review_summary["reviewed_row_count"], 1)
        self.assertEqual(replay_review_summary["total_regret_to_best_available"], 0.04)
        self.assertEqual(replay_review_summary["first_gap_component_counts"], {"model_05_option_expression": 1})
        self.assertEqual(replay_review_summary["top_regret_rows"][0]["source_decision_id"], "decision_fixture")
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
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.option_chain_data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_target_fold",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
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
            (coverage_root / "model_02_target_state_option_chain_data_acquisition_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "model_02_target_state.option_chain_data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
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
            (coverage_root / "model_02_target_state_option_chain_data_acquisition_2016-01_failure_register_proposals.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_failure_register",
                        "failure_id": "fail_option_chain_provider_policy",
                        "request_id": "mgrreq_option_chain_window_aapl_2016_01_2016_01_05_0930",
                        "run_id": "run_option_chain_provider_policy",
                        "stage_id": "model_02_target_state.option_chain_data_acquisition",
                        "target_component_id": "option_chain_state_source",
                        "source_id": "option_chain_state_source",
                        "symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "failure_status": "auto_repair_required",
                        "failure_kind": "unclassified_provider_failure",
                        "observed_status": "failed",
                        "error_summary": "ProviderPolicyError: provider not allowed: thetadata",
                        "skip_future_matching": False,
                        "evidence_refs": ["storage://trading-data/option_chain_state_source/receipt.json"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_option_chain_provider_policy"
            request_root.mkdir(parents=True, exist_ok=True)
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_option_chain_provider_policy",
                        "request_ref": "erragent_option_chain_provider_policy",
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
                        "error_fingerprint": "errfp_option_chain_provider_policy",
                        "request_id": "erragent_option_chain_provider_policy",
                        "request_path": "storage/runtime/agent_error_handling/erragent_option_chain_provider_policy/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_option_chain_provider_policy/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_reconcile",
                        "source_repo": "trading-manager",
                        "error_scope": "server.provider_stage_failure_register",
                        "error_kind": "provider_stage_requests_failed",
                        "severity": "warning",
                        "summary": "provider stage model_02_target_state.option_chain_data_acquisition has failed requests requiring automatic repair",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["detail"]["progress"]["failed_count"], 0)
        self.assertEqual(task["detail"]["failure_register"]["auto_repair_required_count"], 1)
        self.assertEqual(task["detail"]["failure_register"]["agent_review_required_count"], 0)
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
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.option_chain_data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "unit_kind": "twelve_month_target_fold",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
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
            (coverage_root / "model_02_target_state_option_chain_data_acquisition_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "model_02_target_state.option_chain_data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
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
            (coverage_root / "model_02_target_state_option_chain_data_acquisition_2016-01_failure_register_proposals.jsonl").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_failure_register",
                        "failure_id": "fail_option_chain_thetadata_connection_refused",
                        "request_id": "mgrreq_option_chain_window_aapl_2016_01_2016_01_05_0930",
                        "run_id": "run_option_chain_thetadata_connection_refused",
                        "stage_id": "model_02_target_state.option_chain_data_acquisition",
                        "target_component_id": "option_chain_state_source",
                        "source_id": "option_chain_state_source",
                        "symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "failure_status": "retry_required",
                        "failure_kind": "provider_service_unavailable",
                        "observed_status": "failed",
                        "error_summary": "ThetaDataOptionSelectionSnapshotError: request failed before HTTP response: URLError: <urlopen error [Errno 111] Connection refused>",
                        "skip_future_matching": False,
                        "evidence_refs": ["storage://trading-data/option_chain_state_source/receipt.json"],
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["detail"]["failure_register"]["retry_required_count"], 1)
        self.assertEqual(task["detail"]["failure_register"]["agent_review_required_count"], 0)
        self.assertEqual(task["detail"]["repair_intervention_status"], "provider_retry_required")
        self.assertIn("automatic retry", task["reason"])

    def test_fold_model_task_remains_visible_while_month_lane_has_open_head(self):
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
            (runtime / "model_training_workflow_state_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_market_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_sector_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_sector_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_05_option_expression.model_generation.test",
                                "stage_type": "model_generation",
                                "layer": 5,
                                "layer_key": "model_05_option_expression",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
                                    "target_required": True,
                                    "target_symbol": "AAPL",
                                },
                            },
                            {
                                "stage_id": "model_02_target_state.option_chain_data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                    "start_month": "2016-01",
                                    "end_month": "2017-06",
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
            coverage_root = runtime / "stage_coverage"
            coverage_root.mkdir(parents=True, exist_ok=True)
            (coverage_root / "model_02_target_state_option_chain_data_acquisition_2016-01.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "model_02_target_state.option_chain_data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "status": "partial_ready",
                        "expected_count": 77837,
                        "ready_count": 12,
                        "pending_count": 77825,
                        "failed_count": 0,
                        "accepted_failed_count": 0,
                        "can_unlock_downstream": False,
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-06-05T16:55:00Z")

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["task_id"] == "model_02_target_state")
        self.assertEqual(task["task_state"], "current")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["detail"]["progress"]["progress_source"], "fold_stage_coverage")
        self.assertEqual(task["detail"]["progress"]["expected_count"], 77837)
        self.assertEqual(task["detail"]["progress"]["ready_count"], 12)

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
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
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
                "retry_recommendation": "do_not_retry: retired direct materialization route",
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
                        "summary": "model training stage model_02_target_state.data_acquisition command returned non-zero status",
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

    def test_agent_error_summary_closure_receipt_closes_diagnosed_repair(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            agent_root = tmp / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            request_root = agent_root / "erragent_closure_closed"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "completed",
                "root_cause": "stage command contract was repaired locally",
                "retry_recommendation": "retry stage after repair",
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_closure_closed",
                        "request_ref": "erragent_closure_closed",
                        "agent_ref": "trader",
                        "runner_command": "codex_cli",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps(final_report),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T13:55:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (request_root / "agent_repair_closure_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "schema_version": "1",
                        "error_ref": "ERR-000016",
                        "closure_status": "closed",
                        "actions": [{"action": "dashboard_refresh", "status": "completed"}],
                        "blockers": [],
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
                        "error_number": 16,
                        "error_ref": "ERR-000016",
                        "error_fingerprint": "errfp_closure_closed",
                        "request_id": "erragent_closure_closed",
                        "request_path": "storage/runtime/agent_error_handling/erragent_closure_closed/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_closure_closed/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage model_02_target_state.data_acquisition command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T13:52:00Z",
                        "created_at_utc": "2026-05-18T13:52:00Z",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T13:56:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000016")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
        self.assertEqual(agent_errors[0]["closure_receipt"]["closure_status"], "closed")
        self.assertEqual(agent_errors[0]["retry_recommendation"], "agent repair closure receipt recorded closed")

    def test_agent_error_summary_closure_receipt_blocks_attempted_repair(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            agent_root = tmp / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            request_root = agent_root / "erragent_closure_blocked"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "repaired_with_push_blocked",
                "root_cause": "provider route was changed but remote durability was incomplete",
                "repair_attempted": True,
                "retry_recommendation": "retry after push",
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_closure_blocked",
                        "request_ref": "erragent_closure_blocked",
                        "agent_ref": "trader",
                        "runner_command": "codex_cli",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps(final_report),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T14:05:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (request_root / "agent_repair_closure_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "schema_version": "1",
                        "error_ref": "ERR-000017",
                        "closure_status": "blocked",
                        "blockers": ["remote durability is incomplete"],
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
                        "error_number": 17,
                        "error_ref": "ERR-000017",
                        "error_fingerprint": "errfp_closure_blocked",
                        "request_id": "erragent_closure_blocked",
                        "request_path": "storage/runtime/agent_error_handling/erragent_closure_blocked/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_closure_blocked/agent_error_diagnosis.json",
                        "source_component": "trading-manager.model_group_replay_option_features",
                        "source_repo": "trading-manager",
                        "error_scope": "server.replay_option_feature_repair",
                        "error_kind": "model_group_replay_option_source_acquisition_failed",
                        "severity": "error",
                        "summary": "replay option source/feature repair failed for emitted signal AAPL",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T14:02:00Z",
                        "created_at_utc": "2026-05-18T14:02:00Z",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T14:06:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000017")
        self.assertEqual(agent_errors[0]["repair_status"], "blocked")
        self.assertEqual(agent_errors[0]["handling_status"], "open")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "error")
        self.assertIn("remote durability", agent_errors[0]["retry_recommendation"])

    def test_agent_error_summary_successful_retry_closes_stale_blocked_closure(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            agent_root = runtime / "agent_error_handling"
            request_root = agent_root / "erragent_blocked_then_retry_closed"
            request_root.mkdir(parents=True, exist_ok=True)
            final_report = {
                "diagnosis_status": "repaired_with_push_blocked",
                "root_cause": "stage repair was initially blocked before retry evidence arrived",
                "repair_attempted": True,
                "retry_recommendation": "retry stage after repair",
            }
            (request_root / "agent_error_diagnosis.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_error_diagnosis",
                        "schema_version": "1",
                        "diagnosis_id": "errdiag_blocked_then_retry_closed",
                        "request_ref": "erragent_blocked_then_retry_closed",
                        "agent_ref": "trader",
                        "runner_command": "codex_cli",
                        "status": "completed",
                        "return_code": 0,
                        "stdout": json.dumps(final_report),
                        "stderr": "",
                        "completed_at_utc": "2026-05-18T14:05:00Z",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (request_root / "agent_repair_closure_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "schema_version": "1",
                        "error_ref": "ERR-000018",
                        "closure_status": "blocked",
                        "blockers": ["stale closure blocker"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_dir = runtime / "model_training_stage_receipts" / "model_05_option_expression__model_generation__train"
            receipt_dir.mkdir(parents=True, exist_ok=True)
            (receipt_dir / "2026-05-18T141000.000000+0000.receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "model_05_option_expression.model_generation.train",
                        "status": "succeeded",
                        "completed_at": "2026-05-18T14:10:00Z",
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
                        "error_number": 18,
                        "error_ref": "ERR-000018",
                        "error_fingerprint": "errfp_blocked_then_retry_closed",
                        "request_id": "erragent_blocked_then_retry_closed",
                        "request_path": "storage/runtime/agent_error_handling/erragent_blocked_then_retry_closed/server_error_agent_request.json",
                        "diagnosis_path": "storage/runtime/agent_error_handling/erragent_blocked_then_retry_closed/agent_error_diagnosis.json",
                        "source_component": "trading-manager.stage_executor",
                        "source_repo": "trading-manager",
                        "error_scope": "server.model_training_stage",
                        "error_kind": "stage_command_failed",
                        "severity": "error",
                        "summary": "model training stage model_05_option_expression.model_generation.train command returned non-zero status",
                        "exit_code": 1,
                        "occurred_at_utc": "2026-05-18T14:02:00Z",
                        "created_at_utc": "2026-05-18T14:02:00Z",
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
            payload = build_historical_task_progress_summary(status, generated_at_utc="2026-05-18T14:11:00Z")

        agent_errors = payload["chart_payload"]["agent_error_summary"]
        self.assertEqual(agent_errors[0]["error_ref"], "ERR-000018")
        self.assertEqual(agent_errors[0]["repair_status"], "repaired")
        self.assertEqual(agent_errors[0]["handling_status"], "closed")
        self.assertEqual(agent_errors[0]["dashboard_severity"], "notice")
        self.assertIn("retry completed successfully", agent_errors[0]["retry_recommendation"])

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
                        "summary": "model training stage model_02_target_state.data_acquisition command returned non-zero status",
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
                "root_cause": "planner exposed model_06_residual_event_governance.data_acquisition before event-feed coverage",
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
                        "summary": "model training stage model_06_residual_event_governance.data_acquisition command returned non-zero status",
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
            receipt_dir = runtime / "model_training_stage_receipts" / "model_03_event_state__model_generation"
            receipt_dir.mkdir(parents=True, exist_ok=True)
            (receipt_dir / "2026-05-21T112022.000000+0000.receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "model_03_event_state.model_generation",
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
                        "summary": "model training stage model_03_event_state.model_generation command returned non-zero status",
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
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_06_residual_event_governance.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 10,
                                "layer_key": "model_06_residual_event_governance",
                                "status": "blocked",
                                "last_reason": "waiting for upstream_model_04_evaluation_complete",
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
                                "root_cause": "model training stage m06_residual_event_governance.data_acquisition command returned non-zero status",
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
                        "summary": "model training stage m06_residual_event_governance.data_acquisition command returned non-zero status",
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
        self.assertIn("model_06_residual_event_governance", agent_errors[0]["retry_recommendation"])

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
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
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
                        "selected_work": "model_02_target_state.feature_generation",
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
            "model_02_target_state.feature_generation",
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
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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

        task = next(task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2019-01..2020-06")
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
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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
        self.assertEqual({task["month"] for task in task_timeline}, {"2019-01..2020-06"})
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
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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
        durable_task = next(task for task in tasks if task["month"] == "2018-01..2019-06")
        self.assertEqual(durable_task["task_number"], durable_task["sequence"])
        self.assertEqual(durable_task["task_number"], 1)
        self.assertEqual(durable_task["task_uid"], "2018-01..2019-06:model_01_market_context")

    def test_task_timeline_shows_fold_target_chain_prep_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            self._write_target_queue(runtime, ["AAPL"])
            (runtime / "model_training_fold_state_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_market_context.model_generation",
                                "stage_type": "model_generation",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_sector_context.model_generation",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
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
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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
                task_uid="2016-01..2017-06:model_02_target_state.data_acquisition",
                stage_id="model_02_target_state.data_acquisition",
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

        fold_tasks = [task for task in payload["chart_payload"]["task_timeline"] if task["month"] == "2016-01..2017-06"]
        model_tasks = [task for task in fold_tasks if task["stage_type"] == "model_task"]
        lifecycle_tasks = [task for task in fold_tasks if str(task["task_id"]).startswith("model_group.")]
        self.assertEqual([task["stage_type"] for task in model_tasks], ["model_task", "model_task", "model_task"])
        self.assertEqual([task["task_number"] for task in model_tasks], [1, 2, 3])
        self.assertEqual([task["sequence"] for task in model_tasks], [1, 2, 3])
        self.assertEqual(model_tasks[0]["task_uid"], "2016-01..2017-06:model_01_market_context")
        self.assertEqual(
            model_tasks[0]["detail"]["child_partitions"],
            [
                "2016-01",
                "2016-02",
                "2016-03",
                "2016-04",
                "2016-05",
                "2016-06",
                "2016-07",
                "2016-08",
                "2016-09",
                "2016-10",
                "2016-11",
                "2016-12",
                "2017-01",
                "2017-02",
                "2017-03",
                "2017-04",
                "2017-05",
                "2017-06",
            ],
        )
        self.assertEqual(model_tasks[0]["task_label"], "M01 Market Regime Model")
        self.assertEqual(model_tasks[1]["task_label"], "M01 Sector Context Model")
        self.assertEqual(model_tasks[2]["task_label"], "M02 Target State Vector Model")
        self.assertEqual(
            [task["task_id"] for task in lifecycle_tasks],
            [
                "model_group.replay",
                "model_group.replay_review",
                "model_group.model_06_event_risk_governor",
                "model_group.evaluation",
                "model_group.promotion",
                "model_group.maintenance",
            ],
        )
        self.assertTrue(all(task["task_state"] == "blocked" for task in lifecycle_tasks))
        self.assertEqual(lifecycle_tasks[0]["detail"]["blockers"], ["fold_models_01_05_model_generation_complete"])
        fold_prep_tasks = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["task_id"] == "model_02_target_state"
        ]
        self.assertEqual([task["month"] for task in fold_prep_tasks], ["2016-01..2017-06"])
        timeline_months = [task["month"] for task in payload["chart_payload"]["task_timeline"]]
        self.assertIn("2016-01..2017-06", timeline_months)
        self.assertEqual(fold_prep_tasks[0]["worker_label"], "Model Worker 1")
        self.assertEqual(fold_prep_tasks[0]["dataset_unit_months"], None)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["ready_count"], 40)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["expected_count"], 100)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["unit_label"], "rows")
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["progress_source"], "active_progress_file")
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["nodes"][0]["processed_count"], 40)
        self.assertEqual(fold_prep_tasks[0]["detail"]["progress"]["nodes"][0]["expected_count"], 100)

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
            self._write_target_queue(runtime, ["AAPL"])
            (runtime / "model_training_fold_state_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2018-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "last_reason": "waiting for selected_target_symbol_required",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "last_reason": "stage completed by manager stage executor",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
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
            state_path.write_text(json.dumps({"current_month": "2016-07", "start_month": "2017-01"}) + "\n", encoding="utf-8")
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
            if task["month"] == "2016-01..2017-06" and task["task_id"] == "model_02_target_state"
        )
        self.assertEqual(task["status"], "succeeded")
        self.assertEqual(task["target_symbol"], "AAPL")

    def test_task_timeline_blocks_later_fold_after_first_open_fold(self):
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
                                    "stage_id": "model_01_market_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 1,
                                    "layer_key": "model_01_market_context",
                                    "status": "succeeded",
                                }
                            ],
                        }
                    )
                    + "\n",
                    encoding="utf-8",
                )
            for start, end in (("2016-01", "2017-06"), ("2017-01", "2018-06")):
                (runtime / f"model_training_fold_state_{start}_{end}.json").write_text(
                    json.dumps(
                        {
                            "contract_type": "manager_model_training_workflow_state",
                            "start_month": start,
                            "end_month": end,
                            "stages": [
                                {
                                    "stage_id": "model_01_market_context.model_generation",
                                    "stage_type": "model_generation",
                                    "layer": 1,
                                    "layer_key": "model_01_market_context",
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
        self.assertIn("2016-01..2017-06", ordered_months)
        self.assertIn("2017-01..2018-06", ordered_months)
        fold2_blocked = [
            task
            for task in payload["chart_payload"]["task_timeline"]
            if task["month"] == "2017-01..2018-06" and task["task_state"] == "blocked"
        ]
        self.assertTrue(fold2_blocked)
        self.assertIn("previous_fold_complete:2016-01..2017-06", fold2_blocked[0]["detail"]["blockers"])

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
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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
                                "stage_id": "model_06_residual_event_governance.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 6,
                                "layer_key": "model_06_residual_event_governance",
                                "status": "not_applicable",
                            },
                            {
                                "stage_id": "model_06_residual_event_governance.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 6,
                                "layer_key": "model_06_residual_event_governance",
                                "status": "not_applicable",
                            },
                            {
                                "stage_id": "model_06_residual_event_governance.model_generation",
                                "stage_type": "model_generation",
                                "layer": 6,
                                "layer_key": "model_06_residual_event_governance",
                                "status": "blocked",
                            },
                            {
                                "stage_id": "model_02_target_state.option_chain_data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 5,
                                "layer_key": "model_02_target_state",
                                "status": "not_applicable",
                                "last_reason": "no M05 training-eligible underlying minutes ready for option-expression acquisition",
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
            any(task["layer"] == 6 and task["stage_type"] in {"data_acquisition", "feature_generation"} for task in task_timeline)
        )
        self.assertFalse(any(task["layer"] == 6 and task["stage_type"] == "model_task" for task in task_timeline))
        real_skip = next(task for task in task_timeline if task["task_id"] == "model_02_target_state")
        self.assertEqual(real_skip["task_state"], "skipped")
        self.assertIn("no M05 training-eligible", real_skip["reason"])

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
                                    "stage_id": "model_01_market_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 1,
                                    "layer_key": "model_01_market_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "model_01_market_context.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 1,
                                    "layer_key": "model_01_market_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "model_01_sector_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 2,
                                    "layer_key": "model_01_sector_context",
                                    "status": "ready",
                                },
                                {
                                    "stage_id": "model_01_sector_context.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 2,
                                    "layer_key": "model_01_sector_context",
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
        self.assertEqual([task["month"] for task in current_tasks], ["2017-01..2018-06"])
        self.assertEqual([task["worker_id"] for task in current_tasks], ["model_worker_1"])
        self.assertTrue(all(task["task_id"] == "model_01_sector_context" for task in current_tasks))

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
                                    "stage_id": "model_01_market_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 1,
                                    "layer_key": "model_01_market_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "model_01_market_context.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 1,
                                    "layer_key": "model_01_market_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "model_01_sector_context.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 2,
                                    "layer_key": "model_01_sector_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "model_01_sector_context.feature_generation",
                                    "stage_type": "feature_generation",
                                    "layer": 2,
                                    "layer_key": "model_01_sector_context",
                                    "status": "succeeded",
                                },
                                {
                                    "stage_id": "model_02_target_state.data_acquisition",
                                    "stage_type": "data_acquisition",
                                    "layer": 3,
                                    "layer_key": "model_02_target_state",
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
        self.assertEqual([(task["month"], task["task_id"]) for task in current_tasks], [("2020-01..2021-06", "model_02_target_state")])

    def test_task_timeline_blocks_later_fold_until_earliest_open_fold_closes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            service, env, wrapper = self._write_service_files(tmp)
            runtime = tmp / "storage" / "02_control_plane" / "runtime"
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "model_training_fold_state_2017-01_2018-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2018-06",
                        "target_symbol": "AAOI",
                        "stages": [
                            {
                                "stage_id": "model_06_residual_event_governance.model_generation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_06_residual_event_governance",
                                "status": "blocked",
                                "last_reason": "waiting for model_06_residual_event_governance.feature_or_input_ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_2017-01_2018-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2018-06",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.model_generation",
                                "stage_type": "model_generation",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
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

        timeline = payload["chart_payload"]["task_timeline"]
        self.assertIn("2017-01..2018-06", {task["month"] for task in timeline})
        self.assertIn("2017-01..2018-06", {task["month"] for task in timeline})
        fold_2017_blocked = [
            task
            for task in timeline
            if task["month"] == "2017-01..2018-06" and task["task_state"] == "blocked"
        ]
        self.assertTrue(fold_2017_blocked)
        self.assertIn("fold_models_01_05_model_generation_complete", fold_2017_blocked[0]["detail"]["blockers"])

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
                                "stage_id": "model_01_market_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_market_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_sector_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "succeeded",
                            },
                            {
                                "stage_id": "model_01_sector_context.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
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
            self._write_target_queue(runtime, ["AAPL"])
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.model_evaluation",
                                "stage_type": "model_evaluation",
                                "layer": 1,
                                "layer_key": "model_01_market_context",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aaoi_2017-01_2018-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2018-06",
                        "target_symbol": "AAPL",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAOI",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2017-01_2018-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2018-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "succeeded",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                },
                            },
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
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
                        "selected_work": "model_02_target_state.data_acquisition",
                        "execution_summary": {
                            "workflow_plan": {
                                "start_month": "2017-01",
                                "end_month": "2018-06",
                                "selected_target_symbol": "AAPL",
                            },
                            "stage_execution": {
                                "stage_id": "model_02_target_state.data_acquisition",
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
            ("2017-01..2018-06", "model_02_target_state", "AAPL", "Model Worker 1"),
            [(task["month"], task["task_id"], task["target_symbol"], task["worker_label"]) for task in current_tasks],
        )
        self.assertNotIn(
            ("2016-01..2017-06", "model_01_market_context.model_evaluation"),
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
            (runtime / "model_training_fold_state_aapl_2016-01_2017-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.feature_generation",
                                "stage_type": "feature_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
                                },
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime / "model_training_fold_state_aapl_2017-01_2018-06.json").write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2017-01",
                        "end_month": "2018-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.model_generation",
                                "stage_type": "model_generation",
                                "layer": 3,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "last_reason": "stage command is currently running outside checkpoint state",
                                "dataset_unit": {
                                    "target_symbol": "AAPL",
                                    "unit_kind": "target_symbol_walk_forward_12_3_3",
                                    "unit_months": 18,
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
                        "selected_work": "model_02_target_state.feature_generation",
                        "execution_summary": {
                            "workflow_plan": {
                                "start_month": "2017-01",
                                "end_month": "2018-06",
                                "selected_target_symbol": "AAPL",
                            },
                            "stage_execution": {
                                "stage_id": "model_02_target_state.feature_generation",
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
            ("2016-01..2017-06", "model_02_target_state.feature_generation"),
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

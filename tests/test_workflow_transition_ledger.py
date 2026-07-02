from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.workflow_transition_ledger import (
    append_transition,
    append_work_selection_transition,
    transition_from_decision_row,
    transition_from_work_selection,
)


class WorkflowTransitionLedgerTests(unittest.TestCase):
    def test_transition_extracts_scope_and_status_from_scheduler_decision(self) -> None:
        transition = transition_from_decision_row(
            {
                "decision_status": "executed",
                "reason_code": "target_local_provider_stage_executed",
                "reason": "executed one ready workflow stage",
                "selected_work": "model_02_target_state.data_acquisition",
                "next_internal_stage": "autonomous_target_local_provider_acquisition",
                "worker_id": "model_worker_1",
                "selected_target_symbol": "btc",
                "fold_id": "fold_aapl_2016",
                "execution_summary": {
                    "workflow_plan": {"start_month": "2016-01", "end_month": "2016-06"},
                },
            },
            recorded_at_utc="2026-06-29T01:00:00+00:00",
        )

        self.assertEqual(transition["contract_type"], "manager_historical_workflow_transition")
        self.assertEqual(transition["event_type"], "task_step_completed")
        self.assertEqual(transition["task_status"], "completed")
        self.assertEqual(transition["selected_work"], "model_02_target_state.data_acquisition")
        self.assertEqual(transition["target_symbol"], "BTC")
        self.assertEqual(transition["start_month"], "2016-01")
        self.assertEqual(transition["end_month"], "2016-06")
        self.assertEqual(transition["fold_id"], "fold_aapl_2016")
        self.assertEqual(transition["task_id"], "model_02_target_state")
        self.assertEqual(transition["created_at"], "2026-06-29T01:00:00+00:00")
        self.assertEqual(transition["started_at"], "2026-06-29T01:00:00+00:00")
        self.assertEqual(transition["ended_at"], "2026-06-29T01:00:00+00:00")
        self.assertEqual(transition["status_updated_at"], "2026-06-29T01:00:00+00:00")

    def test_transition_extracts_model_group_training_fold_scope(self) -> None:
        transition = transition_from_decision_row(
            {
                "decision_status": "backoff",
                "reason_code": "model_group_replay_after_cost_alpha_training_labels_missing",
                "reason": "recent after-cost alpha supervised training label rejection is active",
                "selected_work": "model_group.replay",
                "next_internal_stage": "model_group_replay",
                "execution_summary": {
                    "training_fold": {
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "target_symbol": "AAPL",
                        "start_month": "2016-01",
                        "end_month": "2017-06",
                        "fold_id": "fold_aapl_2016",
                    },
                    "replay_execution_run_id": "model_group_replay_2016_fold2_complete",
                    "required_next_step": "repair or populate fold-scoped labels",
                },
            },
            recorded_at_utc="2026-06-29T01:02:00+00:00",
        )

        self.assertEqual(transition["event_type"], "task_waiting")
        self.assertEqual(transition["task_status"], "waiting")
        self.assertEqual(transition["task_id"], "model_group.replay")
        self.assertEqual(transition["target_symbol"], "AAPL")
        self.assertEqual(transition["start_month"], "2016-01")
        self.assertEqual(transition["end_month"], "2017-06")
        self.assertEqual(transition["fold_id"], "fold_aapl_2016")
        self.assertEqual(transition["candidate_model_ref"], "storage://trading-manager/model_group/aapl/2016-01_2017-06")
        self.assertEqual(transition["candidate_fold_id"], "fold_aapl_2016")
        self.assertEqual(transition["candidate_training_target"], "AAPL")
        self.assertEqual(transition["replay_execution_run_id"], "model_group_replay_2016_fold2_complete")

    def test_transition_falls_back_to_evaluation_receipt_scope(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            receipt_path = Path(raw_tmp) / "model_group_evaluation_receipt.json"
            receipt_path.write_text(
                json.dumps(
                    {
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2017-06",
                        "candidate_fold_id": "fold_aapl_2016",
                        "candidate_training_target": "AAPL",
                        "replay_execution_run_id": "model_group_replay_2016_fold2_complete",
                        "target_symbol": "AAPL",
                        "fold_id": "fold_aapl_2016",
                    }
                ),
                encoding="utf-8",
            )
            transition = transition_from_decision_row(
                {
                    "decision_status": "executed",
                    "reason_code": "model_group_evaluation_executed",
                    "selected_work": "model_group.evaluation",
                    "execution_summary": {
                        "model_group_evaluation_receipt": str(receipt_path),
                    },
                },
                recorded_at_utc="2026-06-29T01:03:00+00:00",
            )

        self.assertEqual(transition["candidate_model_ref"], "storage://trading-manager/model_group/aapl/2016-01_2017-06")
        self.assertEqual(transition["fold_id"], "fold_aapl_2016")
        self.assertEqual(transition["target_symbol"], "AAPL")
        self.assertEqual(transition["candidate_fold_id"], "fold_aapl_2016")
        self.assertEqual(transition["candidate_training_target"], "AAPL")
        self.assertEqual(transition["replay_execution_run_id"], "model_group_replay_2016_fold2_complete")

    def test_append_transition_writes_log_and_latest(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            log_path = tmp / "historical_workflow_transitions.jsonl"
            latest_path = tmp / "historical_workflow_transition_latest.json"

            transition = append_transition(
                {
                    "decision_status": "backoff",
                    "reason_code": "model_group_m03_event_impact_inputs_required",
                    "reason": "prepare event inputs before attribution",
                    "selected_work": "model_group.m03_event_impact_inputs",
                    "start_month": "2021-01",
                    "end_month": "2025-12",
                },
                log_path=log_path,
                latest_path=latest_path,
                recorded_at_utc="2026-06-29T01:05:00+00:00",
            )

            rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        self.assertEqual(rows, [transition])
        self.assertEqual(latest["transition_id"], transition["transition_id"])
        self.assertEqual(latest["task_status"], "waiting")

    def test_error_decision_becomes_failed_transition(self) -> None:
        transition = transition_from_decision_row(
            {
                "decision_status": "error",
                "reason_code": "scheduler_progress_stalled",
                "reason": "scheduler made no progress",
                "selected_work": "model_group.promotion",
            },
            recorded_at_utc="2026-06-29T01:20:00+00:00",
        )

        self.assertEqual(transition["event_type"], "task_failed")
        self.assertEqual(transition["task_status"], "failed")

    def test_work_selection_transition_records_lane_owner(self) -> None:
        transition = transition_from_work_selection(
            {
                "reason_code": "resume_open_model_worker_fold",
                "start_month": "2016-01",
                "end_month": "2017-06",
            },
            selected_target_symbol="AAPL",
            recorded_at_utc="2026-06-29T02:00:00+00:00",
        )

        self.assertEqual(transition["source"], "historical_work_selection")
        self.assertEqual(transition["event_type"], "task_selected")
        self.assertEqual(transition["task_status"], "selected")
        self.assertEqual(transition["selected_work"], "model_worker.fold")
        self.assertEqual(transition["next_internal_stage"], "model_worker_1")
        self.assertEqual(transition["target_symbol"], "AAPL")
        self.assertEqual(transition["fold_id"], "fold_aapl_2016")
        self.assertEqual(transition["task_id"], "model_worker")
        self.assertEqual(transition["created_at"], "2026-06-29T02:00:00+00:00")
        self.assertEqual(transition["started_at"], "2026-06-29T02:00:00+00:00")
        self.assertIsNone(transition["ended_at"])
        self.assertEqual(transition["status_updated_at"], "2026-06-29T02:00:00+00:00")

    def test_append_work_selection_transition_writes_log_and_latest(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            log_path = tmp / "historical_workflow_transitions.jsonl"
            latest_path = tmp / "historical_workflow_transition_latest.json"

            transition = append_work_selection_transition(
                {
                    "reason_code": "blocked_model_worker_fold_holds_target_lane",
                    "start_month": "2016-07",
                    "end_month": "2016-12",
                    "blocked_target_symbol": "AAPL",
                },
                log_path=log_path,
                latest_path=latest_path,
                recorded_at_utc="2026-06-29T02:05:00+00:00",
            )

            rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            latest = json.loads(latest_path.read_text(encoding="utf-8"))

        self.assertEqual(rows, [transition])
        self.assertEqual(latest["task_status"], "waiting")
        self.assertEqual(latest["target_symbol"], "AAPL")


if __name__ == "__main__":
    unittest.main()

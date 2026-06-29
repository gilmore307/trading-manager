from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.workflow_transition_ledger import append_transition, transition_from_decision_row


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
                "fold_id": "fold_2016-01_2016-06",
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
        self.assertEqual(transition["fold_id"], "fold_2016-01_2016-06")

    def test_append_transition_writes_log_and_latest(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            log_path = tmp / "historical_workflow_transitions.jsonl"
            latest_path = tmp / "historical_workflow_transition_latest.json"

            transition = append_transition(
                {
                    "decision_status": "backoff",
                    "reason_code": "model_group_m06_event_inputs_required",
                    "reason": "prepare event inputs before attribution",
                    "selected_work": "model_group.m06_event_inputs",
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


if __name__ == "__main__":
    unittest.main()

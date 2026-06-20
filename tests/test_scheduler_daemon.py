from __future__ import annotations

import json
import os
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from trading_manager_tasks.scheduler import ResourceSnapshot, SchedulerConfig, SchedulerDecision
from trading_manager_tasks.model_training_state import advance_workflow_state, workflow_state_path_for_month
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.scheduler_daemon import (
    ModelWorkerFoldSelection,
    SchedulerDaemonState,
    acquire_daemon_lock,
    apply_auto_work_selection,
    compact_decision_log_tail,
    completed_historical_fold_cutoff,
    completed_historical_fold_cutoff_month,
    completed_historical_month_cutoff,
    load_model_worker_target_queue,
    load_daemon_state,
    handle_scheduler_progress_stall,
    handle_replay_option_feature_failure,
    model_worker_fold_state_path,
    next_month,
    refresh_dashboard_read_models,
    release_daemon_lock,
    rolling_fold_months,
    run_daemon_loop,
    seed_model_worker_fold_state,
    select_model_worker_fold,
    select_model_worker_target,
    select_month_ingest_worker_months,
    select_next_historical_work,
    update_state_from_error,
    write_daemon_state,
    _run_model_worker_decision,
    _run_replay_review_data_requirement_handoff,
)



class SchedulerDaemonTests(unittest.TestCase):

    def test_decision_log_compaction_keeps_valid_bounded_jsonl_tail(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "runtime" / "historical_scheduler_decisions.jsonl"
            path.parent.mkdir(parents=True)
            with path.open("a", encoding="utf-8") as handle:
                for index in range(20):
                    handle.write(
                        json.dumps(
                            {
                                "contract_type": "manager_scheduler_decision",
                                "sequence": index,
                                "reason": "x" * 512,
                            },
                            sort_keys=True,
                        )
                        + "\n"
                    )

            compact_decision_log_tail(path, max_bytes=2048)
            compacted_size = path.stat().st_size
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertLessEqual(compacted_size, 2048)
        self.assertGreater(len(rows), 0)
        self.assertEqual(rows[-1]["sequence"], 19)
        self.assertGreater(rows[0]["sequence"], 0)

    def _complete_monthly_substrate(self, *, storage_root: Path, month: str) -> None:
        plan = build_model_training_workflow_plan(
            start_month=month,
            end_month=month,
            storage_root=storage_root,
            selected_target_symbol="AAPL",
        )
        substrate_stage_ids = [
            stage.stage_id
            for layer in plan.layers
            for stage in layer.stages
            if stage.stage_type in {"data_acquisition", "feature_generation"}
        ]
        advance_workflow_state(
            start_month=month,
            end_month=month,
            storage_root=storage_root,
            state_path=workflow_state_path_for_month(month, root=storage_root / "runtime"),
            completed_stage_ids=substrate_stage_ids,
            selected_target_symbol="AAPL",
            write=True,
        )

    def _write_promotion_readiness_after(
        self,
        *,
        storage_root: Path,
        state_path: Path,
        source_fold_state_path: Path | None = None,
    ) -> Path:
        source_path = source_fold_state_path or state_path
        readiness_path = (
            storage_root.parent
            / "05_replay_datasets"
            / "promotion_replay_candidate_policy"
            / "promotion_readiness_runs"
            / f"ready_after_{source_path.stem}"
            / "promotion_readiness_record.json"
        )
        readiness_path.parent.mkdir(parents=True, exist_ok=True)
        readiness_path.write_text(
            json.dumps(
                {
                    "contract_type": "promotion_readiness_record",
                    "created_at_utc": "2026-05-28T00:00:00Z",
                    "source_fold_state_path": str(source_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        state_mtime = state_path.stat().st_mtime
        os.utime(readiness_path, (state_mtime + 10, state_mtime + 10))
        return readiness_path

    def _write_terminal_promotion_decision_after(self, *, storage_root: Path, state_path: Path, status: str = "deferred") -> Path:
        state_payload = json.loads(state_path.read_text(encoding="utf-8"))
        fold_id = f"fold_{state_payload['start_month']}_{state_payload['end_month']}"
        model_ref = f"storage://trading-manager/model_group/{state_payload['start_month']}_{state_payload['end_month']}"
        replay_receipt_path = (
            storage_root.parent
            / "05_replay_datasets"
            / "promotion_replay_candidate_policy"
            / "replay_execution_runs"
            / f"replay_after_{state_path.stem}"
            / "replay_execution_receipt.json"
        )
        replay_receipt_path.parent.mkdir(parents=True, exist_ok=True)
        replay_receipt_path.write_text(
            json.dumps(
                {
                    "contract_type": "evaluation_replay_execution_run",
                    "candidate_model_ref": model_ref,
                    "pre_replay_target_refs": ["AAPL"],
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "candidate_fold_id": fold_id,
                    "validation_status": "passed",
                    "created_at_utc": "2026-05-28T00:00:00Z",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        decision_path = (
            storage_root.parent
            / "05_replay_datasets"
            / "promotion_replay_candidate_policy"
            / "promotion_review_runs"
            / f"review_after_{state_path.stem}"
            / "promotion_eligibility_decision.json"
        )
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(
            json.dumps(
                {
                    "contract_type": "promotion_eligibility_decision",
                    "fold_id": fold_id,
                    "decision_status": status,
                    "created_at_utc": "2026-05-28T00:00:00Z",
                    "replay_validation_ref": str(replay_receipt_path),
                    "source_fold_state_path": str(state_path),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        state_mtime = state_path.stat().st_mtime
        os.utime(decision_path, (state_mtime + 10, state_mtime + 10))
        return decision_path

    def _fake_data_src(self, tmp: Path) -> Path:
        src = tmp / "trading-data-src"
        package = src / "data_feed" / "01_feed_alpaca_bars"
        package.mkdir(parents=True)
        (src / "data_feed" / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "pipeline.py").write_text(
            textwrap.dedent(
                """
                from dataclasses import dataclass
                from pathlib import Path

                @dataclass(frozen=True)
                class Context:
                    run_dir: Path

                def build_context(task_key, run_id):
                    if task_key.get('feed') != '01_feed_alpaca_bars':
                        raise ValueError('wrong feed')
                    if not task_key.get('params', {}).get('symbol'):
                        raise ValueError('missing symbol')
                    return Context(Path(task_key['output_root']) / 'runs' / run_id)
                """
            ),
            encoding="utf-8",
        )
        return src

    def test_state_checkpoint_round_trips_and_resumes_month_scope(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "state.json"
            state = SchedulerDaemonState(start_month="2016-01", end_month="2016-01", total_ticks=3)
            write_daemon_state(path, state)

            loaded = load_daemon_state(path, start_month="2016-01", end_month="2016-01")
            self.assertEqual(loaded.total_ticks, 3)
            self.assertTrue(loaded.resume_supported)

            changed_scope = load_daemon_state(path, start_month="2016-02", end_month="2016-02")
            self.assertEqual(changed_scope.total_ticks, 3)
            self.assertEqual(changed_scope.start_month, "2016-02")
            self.assertEqual(changed_scope.end_month, "2016-02")

            resumed_cursor = load_daemon_state(path, start_month="2015-12", end_month="2015-12", resume_month_cursor=True)
            self.assertEqual(resumed_cursor.total_ticks, 3)
            self.assertEqual(resumed_cursor.start_month, "2016-01")
            self.assertEqual(resumed_cursor.end_month, "2016-01")

    def test_scheduler_progress_stall_opens_agent_error_once_per_window(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state = SchedulerDaemonState(
                start_month="2016-01",
                end_month="2016-01",
                last_decision_status="backoff",
                last_reason_code="workflow_stage_blocked",
                last_progress_utc="2026-01-01T00:00:00+00:00",
            )
            with patch("trading_manager_tasks.scheduler_daemon.handle_server_error") as handler:
                handler.return_value = {"error_ref": "ERR-STALL"}
                updated = handle_scheduler_progress_stall(
                    state,
                    storage_root=tmp / "storage",
                    state_path=tmp / "runtime" / "state.json",
                    decision_log_path=tmp / "runtime" / "decisions.jsonl",
                    stall_seconds=600,
                )
                repeated = handle_scheduler_progress_stall(
                    updated,
                    storage_root=tmp / "storage",
                    state_path=tmp / "runtime" / "state.json",
                    decision_log_path=tmp / "runtime" / "decisions.jsonl",
                    stall_seconds=600,
                )

        self.assertEqual(handler.call_count, 1)
        self.assertEqual(updated.last_stall_agent_error_ref, "ERR-STALL")
        self.assertEqual(repeated.last_stall_agent_error_ref, "ERR-STALL")
        call = handler.call_args.kwargs
        self.assertEqual(call["error_kind"], "scheduler_progress_stalled")
        self.assertIn("historical scheduler made no progress", call["summary"])

    def test_scheduler_progress_stall_ignores_future_fold_wait(self):
        state = SchedulerDaemonState(
            start_month="2026-06",
            end_month="2026-06",
            last_work_selection_reason="waiting_for_next_training_fold_to_complete",
            last_progress_utc="2026-01-01T00:00:00+00:00",
        )
        with tempfile.TemporaryDirectory() as raw_tmp, patch("trading_manager_tasks.scheduler_daemon.handle_server_error") as handler:
            tmp = Path(raw_tmp)
            updated = handle_scheduler_progress_stall(
                state,
                storage_root=tmp / "storage",
                state_path=tmp / "runtime" / "state.json",
                decision_log_path=tmp / "runtime" / "decisions.jsonl",
                stall_seconds=600,
            )

        self.assertIsNone(updated.last_stall_agent_error_ref)
        handler.assert_not_called()

    def test_scheduler_progress_stall_ignores_model_group_lifecycle_hold(self):
        state = SchedulerDaemonState(
            start_month="2016-01",
            end_month="2016-06",
            last_work_selection_reason="model_group_lifecycle_holds_fold_lane",
            last_progress_utc="2026-01-01T00:00:00+00:00",
        )
        with tempfile.TemporaryDirectory() as raw_tmp, patch("trading_manager_tasks.scheduler_daemon.handle_server_error") as handler:
            tmp = Path(raw_tmp)
            updated = handle_scheduler_progress_stall(
                state,
                storage_root=tmp / "storage",
                state_path=tmp / "runtime" / "state.json",
                decision_log_path=tmp / "runtime" / "decisions.jsonl",
                stall_seconds=600,
            )

        self.assertIsNone(updated.last_stall_agent_error_ref)
        handler.assert_not_called()

    def test_scheduler_progress_stall_ignores_event_evidence_waits(self):
        for reason_code in (
            "model_group_m06_event_evidence_missing",
            "model_group_residual_event_evidence_missing",
            "model_group_m06_event_evidence_missing",
        ):
            with self.subTest(reason_code=reason_code):
                state = SchedulerDaemonState(
                    start_month="2021-01",
                    end_month="2025-12",
                    last_decision_status="backoff",
                    last_reason_code=reason_code,
                    last_work_selection_reason="model_group_replay_review_ready",
                    last_progress_utc="2026-01-01T00:00:00+00:00",
                )
                with tempfile.TemporaryDirectory() as raw_tmp, patch(
                    "trading_manager_tasks.scheduler_daemon.handle_server_error"
                ) as handler:
                    tmp = Path(raw_tmp)
                    updated = handle_scheduler_progress_stall(
                        state,
                        storage_root=tmp / "storage",
                        state_path=tmp / "runtime" / "state.json",
                        decision_log_path=tmp / "runtime" / "decisions.jsonl",
                        stall_seconds=600,
                    )

                self.assertIsNone(updated.last_stall_agent_error_ref)
                handler.assert_not_called()

    def test_scheduler_progress_stall_ignores_completed_model_group_evaluation(self):
        for reason_code, work_selection_reason in (
            ("model_group_evaluation_executed", "model_group_evaluation_ready"),
            (None, "model_group_evaluation_complete"),
        ):
            with self.subTest(reason_code=reason_code, work_selection_reason=work_selection_reason):
                state = SchedulerDaemonState(
                    start_month="2025-12",
                    end_month="2025-12",
                    last_decision_status="executed",
                    last_reason_code=reason_code,
                    last_work_selection_reason=work_selection_reason,
                    last_progress_utc="2026-01-01T00:00:00+00:00",
                )
                with tempfile.TemporaryDirectory() as raw_tmp, patch(
                    "trading_manager_tasks.scheduler_daemon.handle_server_error"
                ) as handler:
                    tmp = Path(raw_tmp)
                    updated = handle_scheduler_progress_stall(
                        state,
                        storage_root=tmp / "storage",
                        state_path=tmp / "runtime" / "state.json",
                        decision_log_path=tmp / "runtime" / "decisions.jsonl",
                        stall_seconds=600,
                    )

                self.assertIsNone(updated.last_stall_agent_error_ref)
                handler.assert_not_called()

    def test_replay_option_feature_failure_routes_server_error_agent(self):
        decision = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-06-08T07:34:00+00:00",
            now_et="2026-06-08T03:34:00-04:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_source_acquisition_failed",
            reason="RuntimeError: ThetaData INTERNAL",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay_option_features",
            command=[],
            execution_summary={
                "batch": [{"target_ref": "AAPL", "timestamp": "2021-03-05T16:00:00-05:00"}],
                "source_request_ids_by_month": {
                    "2021-03": ["mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930"]
                },
            },
        )
        with tempfile.TemporaryDirectory() as raw_tmp, patch("trading_manager_tasks.scheduler_daemon.handle_server_error") as handler:
            tmp = Path(raw_tmp)
            handler.return_value = {"error_ref": "ERR-REPLAY"}
            result = handle_replay_option_feature_failure(
                decision,
                storage_root=tmp / "storage",
                decision_log_path=tmp / "runtime" / "decisions.jsonl",
            )

        self.assertEqual(result, {"error_ref": "ERR-REPLAY"})
        call = handler.call_args.kwargs
        self.assertEqual(call["error_kind"], "model_group_replay_option_source_acquisition_failed")
        self.assertEqual(
            call["summary"],
            "replay option source/feature repair failed for emitted signal AAPL 2021-03-05T16:00:00-05:00",
        )
        self.assertIn("manager_request:mgrreq_option_chain_window_aapl_2021_03_2021_03_05_0930", call["evidence_refs"])

    def test_replay_review_data_requirement_routes_selected_contract_paths(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            decision_rows = root / "decision_rows.jsonl"
            decision_rows.write_text(
                json.dumps(
                    {
                        "decision_id": "ed_1",
                        "target_ref": "AAPL",
                        "selected_option_contract_ref": "AAPL_2021-07-09_C_142",
                        "option_contract_path_status": "missing",
                        "replay_time_pointer": "2021-07-06T16:00:00-04:00",
                        "next_timestamp": "2021-07-07T16:00:00-04:00",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            review_decision = SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc="2026-06-18T00:00:00+00:00",
                now_et="2026-06-17T20:00:00-04:00",
                decision_status="backoff",
                reason_code="model_group_replay_review_data_required",
                reason="missing replay review data",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work="model_group.replay_review",
                command=[],
                next_internal_stage="replay_review",
                execution_summary={
                    "decision_rows_ref": str(decision_rows),
                    "acquisition_routes": ["model_group.replay_contract_paths"],
                },
            )

            decision = _run_replay_review_data_requirement_handoff(
                review_decision,
                storage_root=root / "storage" / "02_control_plane",
                execute=True,
                execute_provider_acquisition=False,
                limit=None,
            )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_contract_path_provider_required")
        self.assertEqual(decision.selected_work, "model_group.replay_contract_paths")
        self.assertEqual(decision.provider_calls, 0)
        self.assertEqual((decision.execution_summary or {})["resume_stage_id"], "model_group.replay")

    def test_lock_prevents_duplicate_daemon_instance(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            lock_path = Path(raw_tmp) / "scheduler.lock"
            acquire_daemon_lock(lock_path)
            try:
                with self.assertRaises(RuntimeError):
                    acquire_daemon_lock(lock_path)
            finally:
                release_daemon_lock(lock_path)
            self.assertFalse(lock_path.exists())

    def test_lock_replaces_dead_pid_without_waiting_for_age_threshold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            lock_path = Path(raw_tmp) / "scheduler.lock"
            lock_path.write_text('{"pid": 999999999, "created_utc": "2026-05-13T00:00:00+00:00"}\n', encoding="utf-8")

            acquire_daemon_lock(lock_path)
            try:
                payload = json.loads(lock_path.read_text(encoding="utf-8"))
                self.assertNotEqual(payload["pid"], 999999999)
            finally:
                release_daemon_lock(lock_path)

    def test_lock_keeps_recent_malformed_lock_until_stale_threshold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            lock_path = Path(raw_tmp) / "scheduler.lock"
            lock_path.write_text('{"created_utc": "2026-05-13T00:00:00+00:00"}\n', encoding="utf-8")

            with self.assertRaises(RuntimeError):
                acquire_daemon_lock(lock_path, stale_after_seconds=3600)


    def test_error_update_records_resume_safe_failure(self):
        state = update_state_from_error(
            SchedulerDaemonState(),
            started_utc="2026-05-10T00:00:00+00:00",
            completed_utc="2026-05-10T00:00:01+00:00",
            error=ValueError("boom"),
        )
        self.assertEqual(state.failed_ticks, 1)
        self.assertEqual(state.consecutive_errors, 1)
        self.assertEqual(state.last_reason_code, "scheduler_iteration_error")
        self.assertIn("boom", state.last_error or "")

    def test_next_month_rolls_year_boundary(self):
        self.assertEqual(next_month("2016-01"), "2016-02")
        self.assertEqual(next_month("2016-12"), "2017-01")

    def test_completed_historical_month_cutoff_excludes_current_incomplete_month(self):
        self.assertEqual(
            completed_historical_month_cutoff(datetime(2026, 5, 14, 10, 9, tzinfo=ZoneInfo("America/New_York"))),
            "2026-04",
        )
        self.assertEqual(
            completed_historical_month_cutoff(datetime(2026, 6, 1, 0, 1, tzinfo=ZoneInfo("America/New_York"))),
            "2026-05",
        )

    def test_completed_historical_fold_cutoff_excludes_incomplete_six_month_fold(self):
        self.assertEqual(completed_historical_fold_cutoff_month("2026-05"), "2025-12")
        self.assertEqual(completed_historical_fold_cutoff_month("2026-06"), "2026-06")
        self.assertEqual(completed_historical_fold_cutoff_month("2026-11"), "2026-06")
        self.assertEqual(completed_historical_fold_cutoff_month("2026-12"), "2026-12")
        self.assertEqual(
            completed_historical_fold_cutoff(datetime(2026, 6, 30, 23, 59, tzinfo=ZoneInfo("America/New_York"))),
            "2025-12",
        )
        self.assertEqual(
            completed_historical_fold_cutoff(datetime(2026, 7, 1, 0, 1, tzinfo=ZoneInfo("America/New_York"))),
            "2026-06",
        )

    def test_select_next_historical_work_advances_after_latest_completed_month(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in ("2016-01", "2016-02", "2016-03"):
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

            selection = select_next_historical_work(storage_root=storage_root, default_start_month="2016-01", default_end_month="2016-01")

        self.assertEqual(selection.start_month, "2016-04")
        self.assertEqual(selection.end_month, "2016-04")
        self.assertEqual(selection.reason_code, "advance_after_latest_completed_workflow_state")
        self.assertEqual(selection.completed_months, ("2016-01", "2016-02", "2016-03"))
        self.assertEqual(selection.open_months, ())

    def test_select_next_historical_work_fills_missing_start_month_gap(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
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

            selection = select_next_historical_work(storage_root=storage_root, default_start_month="2016-01", default_end_month="2016-01")

        self.assertEqual(selection.start_month, "2016-01")
        self.assertEqual(selection.end_month, "2016-01")
        self.assertEqual(selection.reason_code, "fill_missing_workflow_state_gap")
        self.assertEqual(selection.completed_months, ("2016-02", "2016-03"))
        self.assertEqual(selection.open_months, ())

    def test_select_next_historical_work_waits_for_complete_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            plan = build_model_training_workflow_plan(start_month="2026-04", end_month="2026-04", storage_root=storage_root)
            all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2026-04",
                end_month="2026-04",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2026-04", root=storage_root / "runtime"),
                completed_stage_ids=all_stage_ids,
                write=True,
            )

            selection = select_next_historical_work(
                storage_root=storage_root,
                default_start_month="2026-04",
                default_end_month="2026-04",
                max_month="2026-04",
            )

        self.assertEqual(selection.start_month, "2025-12")
        self.assertEqual(selection.end_month, "2025-12")
        self.assertEqual(selection.reason_code, "waiting_for_next_training_fold_to_complete")

    def test_select_next_historical_work_ignores_open_month_after_cutoff(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            plan = build_model_training_workflow_plan(start_month="2026-04", end_month="2026-04", storage_root=storage_root)
            all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2026-04",
                end_month="2026-04",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2026-04", root=storage_root / "runtime"),
                completed_stage_ids=all_stage_ids,
                write=True,
            )
            open_path = workflow_state_path_for_month("2026-05", root=storage_root / "runtime")
            open_path.parent.mkdir(parents=True, exist_ok=True)
            open_path.write_text(
                json.dumps({"start_month": "2026-05", "end_month": "2026-05", "stages": [{"status": "pending"}]}) + "\n",
                encoding="utf-8",
            )

            selection = select_next_historical_work(
                storage_root=storage_root,
                default_start_month="2026-04",
                default_end_month="2026-04",
                max_month="2026-04",
            )

        self.assertEqual(selection.start_month, "2025-12")
        self.assertEqual(selection.reason_code, "waiting_for_next_training_fold_to_complete")
        self.assertEqual(selection.open_months, ("2026-05",))

    def test_select_next_historical_work_advances_after_foundation_substrate_month(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            month = "2016-01"
            self._complete_monthly_substrate(storage_root=storage_root, month=month)

            selection = select_next_historical_work(storage_root=storage_root, default_start_month=month, default_end_month=month)

        self.assertEqual(selection.start_month, "2016-02")
        self.assertEqual(selection.reason_code, "advance_after_latest_completed_workflow_state")
        self.assertEqual(selection.completed_months, ("2016-01",))
        self.assertEqual(selection.open_months, ())

    def test_select_next_historical_work_resumes_earliest_open_month(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            complete_plan = build_model_training_workflow_plan(start_month="2016-01", end_month="2016-01", storage_root=storage_root)
            all_stage_ids = [stage.stage_id for layer in complete_plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2016-01", root=storage_root / "runtime"),
                completed_stage_ids=all_stage_ids,
                write=True,
            )
            open_path = workflow_state_path_for_month("2016-02", root=storage_root / "runtime")
            open_path.parent.mkdir(parents=True, exist_ok=True)
            open_path.write_text(
                json.dumps({"start_month": "2016-02", "end_month": "2016-02", "stages": [{"status": "pending"}]}) + "\n",
                encoding="utf-8",
            )

            selection = select_next_historical_work(storage_root=storage_root, default_start_month="2016-01", default_end_month="2016-01")

        self.assertEqual(selection.start_month, "2016-02")
        self.assertEqual(selection.reason_code, "resume_earliest_open_workflow_state")
        self.assertEqual(selection.completed_months, ("2016-01",))
        self.assertEqual(selection.open_months, ("2016-02",))

    def test_month_ingest_worker_selection_uses_single_month_after_completed_months(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in ("2016-01", "2016-02"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            advance_workflow_state(
                start_month="2016-03",
                end_month="2016-03",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2016-03", root=storage_root / "runtime"),
                write=True,
            )

            selected = select_month_ingest_worker_months(storage_root=storage_root, default_start_month="2016-01", worker_count=3)
            capped = select_month_ingest_worker_months(storage_root=storage_root, default_start_month="2016-01", worker_count=3, max_month="2016-06")
            before_fold_end = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2016-01",
                worker_count=3,
                max_month="2016-04",
            )

        self.assertEqual(selected, ("2016-03",))
        self.assertEqual(capped, ("2016-03",))
        self.assertEqual(before_fold_end, ())

    def test_month_ingest_worker_selection_ignores_open_month_after_cutoff(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            self._complete_monthly_substrate(storage_root=storage_root, month="2026-04")
            open_path = workflow_state_path_for_month("2026-05", root=storage_root / "runtime")
            open_path.parent.mkdir(parents=True, exist_ok=True)
            open_path.write_text(
                json.dumps({"start_month": "2026-05", "end_month": "2026-05", "stages": [{"status": "ready"}]}) + "\n",
                encoding="utf-8",
            )

            selected = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2026-04",
                worker_count=3,
                max_month="2026-04",
            )

        self.assertEqual(selected, ())


    def test_model_worker_selects_first_complete_six_month_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-06")
            self.assertIsNotNone(selection)
            assert selection is not None
            self.assertEqual(selection.fold_id, "fold_2016-01_2016-06")
            self.assertEqual(selection.reason_code, "complete_foundation_fold_ready")
            self.assertEqual(selection.fold_months, ("2016-01", "2016-02", "2016-03", "2016-04", "2016-05", "2016-06"))

            state_path = seed_model_worker_fold_state(storage_root=storage_root, selection=selection, selected_target_symbol="AAPL")
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            ready = [stage["stage_id"] for stage in payload["stages"] if stage["status"] == "ready"]

        self.assertEqual(state_path.name, "model_training_fold_state_aapl_2016-01_2016-06.json")
        self.assertIn("model_01_background_context.model_generation.train", ready)

    def test_seed_model_worker_fold_state_refreshes_existing_monthly_foundation_stages(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-06", selected_target_symbol="AAPL")
            self.assertIsNotNone(selection)
            assert selection is not None
            state_path = model_worker_fold_state_path(
                selection.start_month,
                selection.end_month,
                root=storage_root / "runtime",
                selected_target_symbol="AAPL",
            )
            plan = build_model_training_workflow_plan(
                start_month=selection.start_month,
                end_month=selection.end_month,
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            layer_one_foundation = [
                stage.stage_id
                for layer in plan.layers
                if layer.layer == 1
                for stage in layer.stages
                if stage.stage_type in {"data_acquisition", "feature_generation"}
            ]
            advance_workflow_state(
                start_month=selection.start_month,
                end_month=selection.end_month,
                storage_root=storage_root,
                state_path=state_path,
                completed_stage_ids=layer_one_foundation,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )

            seeded_path = seed_model_worker_fold_state(storage_root=storage_root, selection=selection, selected_target_symbol="AAPL")
            payload = json.loads(seeded_path.read_text(encoding="utf-8"))
            statuses = {stage["stage_id"]: stage["status"] for stage in payload["stages"]}

        self.assertEqual(seeded_path, state_path)
        self.assertEqual(statuses["model_03_event_state.data_acquisition"], "succeeded")
        self.assertEqual(statuses["model_01_background_context.feature_generation"], "succeeded")
        self.assertEqual(payload["next_stage"]["stage_id"], "model_01_background_context.model_generation.train")

    def test_target_scoped_fold_state_path_prevents_cross_target_collision(self):
        path = model_worker_fold_state_path(
            "2016-01",
            "2016-06",
            root=Path("/tmp/runtime"),
            selected_target_symbol="BRK.B",
        )

        self.assertEqual(path.name, "model_training_fold_state_brk_b_2016-01_2016-06.json")

    def test_model_worker_target_queue_skips_completed_target_and_restarts_next_target(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            for start_month in ("2016-01", "2016-07"):
                end_month = rolling_fold_months(start_month)[-1]
                selection = select_model_worker_fold(
                    storage_root=storage_root,
                    default_start_month="2016-01",
                    max_month="2016-12",
                    selected_target_symbol="AAPL",
                )
                self.assertIsNotNone(selection)
                assert selection is not None
                state_path = seed_model_worker_fold_state(
                    storage_root=storage_root,
                    selection=selection,
                    selected_target_symbol="AAPL",
                )
                plan = build_model_training_workflow_plan(
                    start_month=start_month,
                    end_month=end_month,
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    foundation_catch_up_only=False,
                )
                advance_workflow_state(
                    start_month=start_month,
                    end_month=end_month,
                    storage_root=storage_root,
                    state_path=state_path,
                    completed_stage_ids=[stage.stage_id for layer in plan.layers for stage in layer.stages],
                    selected_target_symbol="AAPL",
                    foundation_catch_up_only=False,
                    write=True,
                )
                self._write_promotion_readiness_after(storage_root=storage_root, state_path=state_path)

            queue_path = storage_root / "runtime" / "model_training_target_queue.json"
            queue_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_target_queue",
                        "targets": [{"symbol": "AAPL"}, {"symbol": "MSFT"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            loaded_queue = load_model_worker_target_queue(queue_path)
            target_selection = select_model_worker_target(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                target_queue_path=queue_path,
            )

        self.assertEqual(loaded_queue, ("AAPL", "MSFT"))
        self.assertIsNotNone(target_selection)
        assert target_selection is not None
        self.assertEqual(target_selection.selected_target_symbol, "MSFT")
        self.assertEqual(target_selection.reason_code, "selected_target_has_open_model_worker_fold")
        self.assertIsNotNone(target_selection.fold_selection)
        assert target_selection.fold_selection is not None
        self.assertEqual(target_selection.fold_selection.start_month, "2016-01")
        self.assertEqual(Path(target_selection.fold_selection.state_path or "").name, "model_training_fold_state_msft_2016-01_2016-06.json")

    def test_model_worker_selects_foundation_fold_without_target_queue(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            queue_path = storage_root / "runtime" / "model_training_target_queue.json"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            target_selection = select_model_worker_target(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-06",
                target_queue_path=queue_path,
            )

        self.assertIsNotNone(target_selection)
        assert target_selection is not None
        self.assertIsNone(target_selection.selected_target_symbol)
        self.assertEqual(target_selection.reason_code, "foundation_fold_has_open_model_worker_stage")
        self.assertIsNotNone(target_selection.fold_selection)
        assert target_selection.fold_selection is not None
        self.assertEqual(target_selection.fold_selection.fold_id, "fold_2016-01_2016-06")

    def test_model_worker_executes_foundation_fold_without_selected_target(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "manager-storage"
            queue_path = storage_root / "runtime" / "model_training_target_queue.json"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            decision = SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc="2026-05-27T04:00:00+00:00",
                now_et="2026-05-27T00:00:00-04:00",
                decision_status="executed",
                reason_code="workflow_stage_executed",
                reason="executed model generation",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work="model_01_market_context.model_generation",
                command=[],
                next_internal_stage="model_generation",
            )

            with patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=decision) as run_once:
                result = _run_model_worker_decision(
                    storage_root=storage_root,
                    component_src_root=tmp,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                    execute_safe_offline_stages=True,
                    execute_autonomous_provider_stages=True,
                    provider_stage_next_limit=12,
                    provider_stage_max_workers=3,
                    selected_target_symbol=None,
                    target_queue_path=queue_path,
                )

        self.assertIsNotNone(result)
        assert result is not None
        target_selection, model_decision = result
        self.assertIsNone(target_selection.selected_target_symbol)
        self.assertEqual(target_selection.fold_selection.fold_id, "fold_2016-01_2016-06")
        self.assertEqual(model_decision.selected_work, "model_01_market_context.model_generation")
        self.assertIsNone(run_once.call_args.kwargs["selected_target_symbol"])
        self.assertTrue(run_once.call_args.kwargs["execute_autonomous_provider_stages"])
        self.assertEqual(run_once.call_args.kwargs["provider_stage_next_limit"], 12)
        self.assertEqual(run_once.call_args.kwargs["provider_stage_max_workers"], 3)

    def test_model_worker_does_not_select_until_validation_and_test_months_ready(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in ("2016-01", "2016-02", "2016-03", "2016-04"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-06")

        self.assertIsNone(selection)

    def test_model_worker_uses_non_overlapping_six_month_folds(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            first_selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            self.assertIsNotNone(first_selection)
            assert first_selection is not None
            first_state_path = seed_model_worker_fold_state(storage_root=storage_root, selection=first_selection, selected_target_symbol="AAPL")
            first_plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            all_first_stage_ids = [stage.stage_id for layer in first_plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=first_state_path,
                completed_stage_ids=all_first_stage_ids,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )

            overlapping_selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-07",
                selected_target_symbol="AAPL",
            )

            for month in rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            next_selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            self._write_promotion_readiness_after(storage_root=storage_root, state_path=first_state_path)
            next_selection_after_lifecycle = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(overlapping_selection)
        self.assertIsNone(next_selection)
        self.assertIsNotNone(next_selection_after_lifecycle)
        assert next_selection_after_lifecycle is not None
        self.assertEqual(next_selection_after_lifecycle.fold_id, "fold_2016-07_2016-12")
        self.assertEqual(next_selection_after_lifecycle.fold_months, ("2016-07", "2016-08", "2016-09", "2016-10", "2016-11", "2016-12"))

    def test_model_worker_does_not_leapfrog_missing_foundation_month_gap(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            state_path = model_worker_fold_state_path("2016-07", "2016-12", root=storage_root / "runtime")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-07",
                        "end_month": "2016-12",
                        "stages": [
                            {
                                "stage_id": "model_01_market_context.model_generation",
                                "stage_type": "model_generation",
                                "layer": 1,
                                "status": "ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-12")

        self.assertIsNone(selection)

    def test_model_worker_reopens_legacy_unsplit_completed_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            state_path = model_worker_fold_state_path(
                "2016-01",
                "2016-06",
                root=storage_root / "runtime",
                selected_target_symbol="AAPL",
            )
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
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
                            }
                            for layer in range(1, 10)
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.fold_id, "fold_2016-01_2016-06")
        self.assertEqual(selection.reason_code, "resume_open_model_worker_fold")

    def test_completed_model_generation_splits_close_fold_even_with_failed_prep_stage(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            state_path = model_worker_fold_state_path(
                "2016-01",
                "2016-06",
                root=storage_root / "runtime",
                selected_target_symbol="AAPL",
            )
            state_path.parent.mkdir(parents=True, exist_ok=True)
            plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=state_path,
                completed_stage_ids=all_stage_ids,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            for stage in payload["stages"]:
                if stage["stage_id"] == "model_02_target_state.feature_generation":
                    stage["status"] = "failed"
                    stage["last_reason"] = "stage progress stalled for timeout_seconds=600"
                    break
            state_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

            selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            blocked = select_next_historical_work(
                storage_root=storage_root,
                default_start_month="2016-01",
                default_end_month="2016-01",
                max_month="2016-12",
            )

        self.assertIsNone(selection)
        self.assertEqual(blocked.reason_code, "model_group_lifecycle_holds_fold_lane")
        self.assertEqual(blocked.blocked_fold_state_path, str(state_path))

    def test_model_worker_open_fold_waits_for_monthly_foundation_after_layer_two_reset(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01")[:-1]:
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            state_path = model_worker_fold_state_path(
                "2016-01",
                "2016-06",
                root=storage_root / "runtime",
                selected_target_symbol="AAPL",
            )
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "model_01_sector_context.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_01_sector_context",
                                "status": "ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            has_open_fold = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2016-01",
                worker_count=3,
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(selection)
        self.assertEqual(has_open_fold[:1], ("2016-06",))
        self.assertGreater(len(has_open_fold), 0)

    def test_model_worker_holds_blocked_fold_instead_of_selecting_next_ready_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            blocked_state_path = model_worker_fold_state_path("2016-01", "2016-06", root=storage_root / "runtime")
            blocked_state_path.parent.mkdir(parents=True, exist_ok=True)
            blocked_state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "model_05_option_expression.model_generation",
                                "stage_type": "model_generation",
                                "layer": 5,
                                "layer_key": "model_05_option_expression",
                                "status": "blocked",
                                "last_reason": "waiting for model_05_option_expression.feature_or_input_ready",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-12")

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.fold_id, "fold_2016-01_2016-06")
        self.assertEqual(selection.reason_code, "blocked_model_worker_fold_holds_target_lane")

    def test_completed_pre_replay_fold_holds_next_fold_until_model_group_lifecycle_completes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            first_selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            self.assertIsNotNone(first_selection)
            assert first_selection is not None
            first_state_path = seed_model_worker_fold_state(
                storage_root=storage_root,
                selection=first_selection,
                selected_target_symbol="AAPL",
            )
            first_plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=first_state_path,
                completed_stage_ids=[stage.stage_id for layer in first_plan.layers for stage in layer.stages],
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )

            blocked_next_fold = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            blocked_month_ingest = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2016-01",
                worker_count=3,
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            self._write_promotion_readiness_after(storage_root=storage_root, state_path=first_state_path)
            unblocked_next_fold = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(blocked_next_fold)
        self.assertEqual(blocked_month_ingest, ())
        self.assertIsNotNone(unblocked_next_fold)
        assert unblocked_next_fold is not None
        self.assertEqual(unblocked_next_fold.fold_id, "fold_2016-07_2016-12")

    def test_other_fold_promotion_readiness_does_not_unblock_current_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            first_plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            first_state_path = model_worker_fold_state_path("2016-01", "2016-06", root=storage_root / "runtime", selected_target_symbol="AAPL")
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=first_state_path,
                completed_stage_ids=[stage.stage_id for layer in first_plan.layers for stage in layer.stages],
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )
            other_state_path = model_worker_fold_state_path(
                "2016-07",
                "2016-12",
                root=storage_root / "runtime",
                selected_target_symbol="AAPL",
            )

            self._write_promotion_readiness_after(
                storage_root=storage_root,
                state_path=first_state_path,
                source_fold_state_path=other_state_path,
            )
            blocked_next_fold = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(blocked_next_fold)

    def test_incomplete_lifecycle_fold_blocks_later_open_fold_resume(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07") + rolling_fold_months("2017-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            for start_month, end_month in (("2016-01", "2016-06"), ("2016-07", "2016-12")):
                plan = build_model_training_workflow_plan(
                    start_month=start_month,
                    end_month=end_month,
                    storage_root=storage_root,
                    selected_target_symbol="AAPL",
                    foundation_catch_up_only=False,
                )
                state_path = model_worker_fold_state_path(
                    start_month,
                    end_month,
                    root=storage_root / "runtime",
                    selected_target_symbol="AAPL",
                )
                advance_workflow_state(
                    start_month=start_month,
                    end_month=end_month,
                    storage_root=storage_root,
                    state_path=state_path,
                    completed_stage_ids=[stage.stage_id for layer in plan.layers for stage in layer.stages],
                    selected_target_symbol="AAPL",
                    foundation_catch_up_only=False,
                    write=True,
                )
                if start_month == "2016-01":
                    self._write_promotion_readiness_after(storage_root=storage_root, state_path=state_path)
            third_selection = ModelWorkerFoldSelection(
                fold_id="fold_2017-01_2017-06",
                start_month="2017-01",
                end_month="2017-06",
                fold_months=rolling_fold_months("2017-01"),
                reason_code="complete_foundation_fold_ready",
                state_path=str(
                    model_worker_fold_state_path(
                        "2017-01",
                        "2017-06",
                        root=storage_root / "runtime",
                        selected_target_symbol="AAPL",
                    )
                ),
            )
            seed_model_worker_fold_state(
                storage_root=storage_root,
                selection=third_selection,
                selected_target_symbol="AAPL",
            )

            blocked_open_fold = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2017-06",
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(blocked_open_fold)

    def test_non_eligible_promotion_decision_unblocks_next_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            first_plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            first_state_path = model_worker_fold_state_path("2016-01", "2016-06", root=storage_root / "runtime", selected_target_symbol="AAPL")
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=first_state_path,
                completed_stage_ids=[stage.stage_id for layer in first_plan.layers for stage in layer.stages],
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )

            blocked_next_fold = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            self._write_terminal_promotion_decision_after(storage_root=storage_root, state_path=first_state_path)
            unblocked_next_fold = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(blocked_next_fold)
        self.assertIsNotNone(unblocked_next_fold)
        assert unblocked_next_fold is not None
        self.assertEqual(unblocked_next_fold.fold_id, "fold_2016-07_2016-12")

    def test_next_historical_work_pauses_on_incomplete_model_group_lifecycle(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                plan = build_model_training_workflow_plan(start_month=month, end_month=month, storage_root=storage_root)
                monthly_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
                advance_workflow_state(
                    start_month=month,
                    end_month=month,
                    storage_root=storage_root,
                    state_path=workflow_state_path_for_month(month, root=storage_root / "runtime"),
                    completed_stage_ids=monthly_stage_ids,
                    write=True,
                )
            fold_selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )
            self.assertIsNotNone(fold_selection)
            assert fold_selection is not None
            fold_state_path = seed_model_worker_fold_state(
                storage_root=storage_root,
                selection=fold_selection,
                selected_target_symbol="AAPL",
            )
            fold_plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=fold_state_path,
                completed_stage_ids=[stage.stage_id for layer in fold_plan.layers for stage in layer.stages],
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )

            blocked = select_next_historical_work(
                storage_root=storage_root,
                default_start_month="2016-01",
                default_end_month="2016-01",
                max_month="2016-12",
            )
            state = apply_auto_work_selection(
                SchedulerDaemonState(
                    start_month="2016-07",
                    end_month="2016-07",
                    last_work_selection_reason="advance_after_latest_completed_workflow_state",
                ),
                storage_root=storage_root,
                default_start_month="2016-01",
                default_end_month="2016-01",
            )
            self._write_promotion_readiness_after(storage_root=storage_root, state_path=fold_state_path)
            unblocked = select_next_historical_work(
                storage_root=storage_root,
                default_start_month="2016-01",
                default_end_month="2016-01",
                max_month="2017-06",
            )

        self.assertEqual(blocked.reason_code, "model_group_lifecycle_holds_fold_lane")
        self.assertEqual(blocked.start_month, "2016-01")
        self.assertEqual(blocked.end_month, "2016-06")
        self.assertEqual(blocked.blocked_fold_state_path, str(fold_state_path))
        self.assertEqual(state.start_month, "2016-01")
        self.assertEqual(state.end_month, "2016-06")
        self.assertEqual(state.last_work_selection_reason, "model_group_lifecycle_holds_fold_lane")
        self.assertEqual(unblocked.reason_code, "advance_after_latest_completed_workflow_state")
        self.assertEqual(unblocked.start_month, "2017-01")

    def test_daemon_records_model_group_lifecycle_hold_without_stall_handoff(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "manager-storage"
            state_path = tmp / "runtime" / "state.json"
            lock_path = tmp / "runtime" / "scheduler.lock"
            decision_log = tmp / "runtime" / "decisions.jsonl"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            fold_selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-06",
                selected_target_symbol="AAPL",
            )
            self.assertIsNotNone(fold_selection)
            assert fold_selection is not None
            fold_state_path = seed_model_worker_fold_state(
                storage_root=storage_root,
                selection=fold_selection,
                selected_target_symbol="AAPL",
            )
            fold_plan = build_model_training_workflow_plan(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
            )
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-06",
                storage_root=storage_root,
                state_path=fold_state_path,
                completed_stage_ids=[stage.stage_id for layer in fold_plan.layers for stage in layer.stages],
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                write=True,
            )
            stale_state = SchedulerDaemonState(
                start_month="2016-01",
                end_month="2016-06",
                last_progress_utc="2026-01-01T00:00:00+00:00",
            )
            write_daemon_state(state_path, stale_state)

            with patch("trading_manager_tasks.scheduler_daemon.handle_server_error") as handler:
                state = run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-06",
                    storage_root=storage_root,
                    component_src_root=self._fake_data_src(tmp),
                    state_path=state_path,
                    lock_path=lock_path,
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=1,
                    auto_select_next_work=True,
                    source_existing_bootstrap=False,
                    progress_stall_seconds=600,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

        self.assertEqual(state.last_work_selection_reason, "model_group_replay_dataset_ready")
        self.assertEqual(state.last_next_internal_stage, "model_group_replay_dataset")
        self.assertEqual(state.start_month, "2016-01")
        self.assertEqual(state.end_month, "2016-06")
        handler.assert_not_called()

    def test_month_ingest_workers_pause_when_target_has_open_model_worker_fold(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            selection = select_model_worker_fold(
                storage_root=storage_root,
                default_start_month="2016-01",
                max_month="2016-06",
                selected_target_symbol="AAPL",
            )
            self.assertIsNotNone(selection)
            assert selection is not None
            seed_model_worker_fold_state(storage_root=storage_root, selection=selection, selected_target_symbol="AAPL")

            months = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2016-01",
                worker_count=3,
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertEqual(months, ())

    def test_month_ingest_workers_pause_when_model_worker_fold_is_ready(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)

            months = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2016-01",
                worker_count=3,
                max_month="2016-12",
                selected_target_symbol="AAPL",
            )

        self.assertEqual(months, ())

    def test_month_ingest_worker_selection_fills_missing_start_month_gap(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            self._complete_monthly_substrate(storage_root=storage_root, month="2016-02")
            self._complete_monthly_substrate(storage_root=storage_root, month="2016-03")

            months = select_month_ingest_worker_months(
                storage_root=storage_root,
                default_start_month="2016-01",
                worker_count=3,
                max_month="2016-06",
            )

        self.assertEqual(months, ("2016-01",))

    def test_model_worker_selects_fold_with_ready_target_chain_preparation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in rolling_fold_months("2016-01") + rolling_fold_months("2016-07"):
                self._complete_monthly_substrate(storage_root=storage_root, month=month)
            state_path = model_worker_fold_state_path("2016-01", "2016-06", root=storage_root / "runtime")
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": "model_02_target_state.data_acquisition",
                                "stage_type": "data_acquisition",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "ready",
                            },
                            {
                                "stage_id": "model_02_target_state.model_generation.train",
                                "stage_type": "model_generation",
                                "layer": 2,
                                "layer_key": "model_02_target_state",
                                "status": "blocked",
                                "last_reason": "waiting for model_02_target_state.feature_or_input_ready",
                            },
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-12")

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.fold_id, "fold_2016-01_2016-06")
        self.assertEqual(selection.reason_code, "resume_open_model_worker_fold")

    def test_auto_work_selection_jumps_past_externally_completed_months(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "manager-storage"
            for month in ("2016-10", "2016-11", "2016-12"):
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

            state = apply_auto_work_selection(
                SchedulerDaemonState(
                    start_month="2016-10",
                    end_month="2016-10",
                    last_work_selection_reason="advance_after_latest_completed_workflow_state",
                    last_completed_months=("2016-09",),
                ),
                storage_root=storage_root,
                default_start_month="2016-10",
                default_end_month="2016-10",
            )

        self.assertEqual(state.start_month, "2017-01")
        self.assertEqual(state.end_month, "2017-01")
        self.assertEqual(state.last_next_internal_stage, "historical_work_selected")
        self.assertEqual(state.last_work_selection_reason, "advance_after_latest_completed_workflow_state")
        self.assertEqual(state.last_completed_months, ("2016-10", "2016-11", "2016-12"))


    def test_daemon_auto_selects_next_work_without_user_month_instruction(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "manager-storage"
            plan = build_model_training_workflow_plan(start_month="2016-01", end_month="2016-01", storage_root=storage_root)
            all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2016-01", root=storage_root / "runtime"),
                completed_stage_ids=all_stage_ids,
                write=True,
            )
            state = run_daemon_loop(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage_root,
                component_src_root=self._fake_data_src(tmp),
                state_path=tmp / "runtime" / "state.json",
                lock_path=tmp / "runtime" / "scheduler.lock",
                decision_log_path=tmp / "runtime" / "decisions.jsonl",
                interval_seconds=0,
                max_iterations=1,
                execute_safe_preparation=True,
                auto_select_next_work=True,
                source_existing_bootstrap=False,
                config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
            )

        self.assertEqual(state.start_month, "2016-02")
        self.assertEqual(state.end_month, "2016-02")
        self.assertEqual(state.last_work_selection_reason, "advance_after_latest_completed_workflow_state")
        self.assertEqual(state.last_completed_months, ("2016-01",))

    def test_daemon_advances_month_cursor_after_completed_workflow(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "manager-storage"
            plan = build_model_training_workflow_plan(start_month="2016-01", end_month="2016-01", storage_root=storage_root)
            all_stage_ids = [stage.stage_id for layer in plan.layers for stage in layer.stages]
            advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage_root,
                state_path=workflow_state_path_for_month("2016-01", root=storage_root / "runtime"),
                completed_stage_ids=all_stage_ids,
                write=True,
            )
            state = run_daemon_loop(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage_root,
                component_src_root=self._fake_data_src(tmp),
                state_path=tmp / "runtime" / "state.json",
                lock_path=tmp / "runtime" / "scheduler.lock",
                decision_log_path=tmp / "runtime" / "decisions.jsonl",
                interval_seconds=0,
                max_iterations=1,
                advance_month_on_complete=True,
                source_existing_bootstrap=False,
                config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
            )

        self.assertEqual(state.start_month, "2016-02")
        self.assertEqual(state.end_month, "2016-02")
        self.assertEqual(state.last_reason_code, "month_workflow_complete")
        self.assertEqual(state.last_next_internal_stage, "chronological_month_advanced")
        self.assertTrue(state.service_managed)


    def test_daemon_runs_source_existing_bootstrap_on_start_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            with patch("trading_manager_tasks.scheduler_daemon.run_source_existing_bootstrap") as bootstrap:
                run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=tmp / "runtime" / "state.json",
                    lock_path=tmp / "runtime" / "scheduler.lock",
                    decision_log_path=tmp / "runtime" / "decisions.jsonl",
                    interval_seconds=0,
                    max_iterations=1,
                    execute_safe_preparation=True,
                    selected_target_symbol="AAPL",
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

        bootstrap.assert_called_once()
        _, kwargs = bootstrap.call_args
        self.assertEqual(kwargs["start_month"], "2016-01")
        self.assertEqual(kwargs["end_month"], "2016-01")
        self.assertEqual(kwargs["selected_target_symbol"], "AAPL")
        self.assertTrue(kwargs["write"])

    def test_daemon_loop_persists_state_and_decision_log(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "runtime" / "state.json"
            lock_path = tmp / "runtime" / "scheduler.lock"
            decision_log = tmp / "runtime" / "decisions.jsonl"
            state = run_daemon_loop(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp / "manager-storage",
                component_src_root=self._fake_data_src(tmp),
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                interval_seconds=0,
                max_iterations=1,
                execute_safe_preparation=True,
                source_existing_bootstrap=False,
                config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
            )

            self.assertEqual(state.total_ticks, 1)
            self.assertEqual(state.successful_ticks, 1)
            self.assertEqual(state.last_next_internal_stage, "autonomous_historical_provider_acquisition")
            self.assertFalse(lock_path.exists())
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["contract_type"], "manager_scheduler_daemon_state")
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(log_rows), 1)
            self.assertEqual(log_rows[0]["provider_calls"], 0)

    def test_daemon_dispatches_replay_review_after_scheduler_tick(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "runtime" / "state.json"
            lock_path = tmp / "runtime" / "scheduler.lock"
            decision_log = tmp / "runtime" / "decisions.jsonl"
            scheduler_decision = SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc="2026-05-28T00:00:00+00:00",
                now_et="2026-05-27T20:00:00-04:00",
                decision_status="ready",
                reason_code="no_month_stage_ready",
                reason="no month stage ready",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work=None,
                command=[],
                next_internal_stage="historical_training_work_loop",
            )
            replay_review_decision = SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc="2026-05-28T00:00:01+00:00",
                now_et="2026-05-27T20:00:01-04:00",
                decision_status="executed",
                reason_code="model_group_replay_review_executed",
                reason="executed replay review",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work="model_group.replay_review",
                command=[],
                next_internal_stage="replay_review",
            )

            with patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=scheduler_decision), patch(
                "trading_manager_tasks.scheduler_daemon.run_model_group_replay_if_ready", return_value=None
            ), patch(
                "trading_manager_tasks.scheduler_daemon.run_model_group_replay_review_if_ready",
                return_value=replay_review_decision,
            ) as replay_review:
                state = run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=state_path,
                    lock_path=lock_path,
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=2,
                    execute_safe_preparation=True,
                    source_existing_bootstrap=False,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

            replay_review.assert_called()
            self.assertEqual(state.last_next_internal_stage, "replay_review")
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["reason_code"] for row in log_rows], ["no_month_stage_ready", "model_group_replay_review_executed"])

    def test_daemon_dispatches_model_group_evaluation_after_attribution(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "runtime" / "state.json"
            lock_path = tmp / "runtime" / "scheduler.lock"
            decision_log = tmp / "runtime" / "decisions.jsonl"
            scheduler_decision = SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc="2026-05-28T00:00:00+00:00",
                now_et="2026-05-27T20:00:00-04:00",
                decision_status="ready",
                reason_code="no_month_stage_ready",
                reason="no month stage ready",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work=None,
                command=[],
                next_internal_stage="historical_training_work_loop",
            )
            evaluation_decision = SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc="2026-05-28T00:00:01+00:00",
                now_et="2026-05-27T20:00:01-04:00",
                decision_status="executed",
                reason_code="model_group_evaluation_executed",
                reason="executed model-group evaluation",
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work="model_group.evaluation",
                command=[],
                next_internal_stage="model_group_evaluation",
            )

            with patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=scheduler_decision), patch(
                "trading_manager_tasks.scheduler_daemon.run_model_group_replay_if_ready", return_value=None
            ), patch(
                "trading_manager_tasks.scheduler_daemon.run_model_group_replay_review_if_ready", return_value=None
            ), patch(
                "trading_manager_tasks.scheduler_daemon.run_model_group_evaluation_if_ready",
                return_value=evaluation_decision,
            ) as evaluation:
                state = run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=state_path,
                    lock_path=lock_path,
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=2,
                    execute_safe_preparation=True,
                    source_existing_bootstrap=False,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

            evaluation.assert_called()
            self.assertEqual(state.last_next_internal_stage, "model_group_evaluation")
            self.assertEqual(state.last_work_selection_reason, "model_group_evaluation_complete")
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["reason_code"] for row in log_rows], ["no_month_stage_ready", "model_group_evaluation_executed"])

    def test_daemon_drain_continues_until_next_non_executed_decision(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            state_path = tmp / "runtime" / "state.json"
            lock_path = tmp / "runtime" / "scheduler.lock"
            decision_log = tmp / "runtime" / "decisions.jsonl"
            state = run_daemon_loop(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp / "manager-storage",
                component_src_root=self._fake_data_src(tmp),
                state_path=state_path,
                lock_path=lock_path,
                decision_log_path=decision_log,
                interval_seconds=0,
                max_iterations=2,
                execute_safe_preparation=True,
                drain_ready_stages=True,
                source_existing_bootstrap=False,
                config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
            )

            self.assertEqual(state.total_ticks, 2)
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["reason_code"] for row in log_rows], ["safe_offline_preparation_executed", "autonomous_provider_stage_ready"])

    def test_daemon_drains_replay_option_features_before_next_replay_retry(self):
        replay_backoff = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_feature_acquisition_required",
            reason="replay_option_feature_acquisition_required",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay",
            command=[],
            next_internal_stage="model_group.replay",
        )
        option_decisions = [
            SchedulerDecision(
                contract_type="manager_scheduler_decision",
                now_utc=f"2026-05-28T00:00:0{index}+00:00",
                now_et=f"2026-05-27T20:00:0{index}-04:00",
                decision_status="executed",
                reason_code=reason,
                reason=reason,
                market_protection_active=False,
                resource_pressure_active=False,
                selected_work="model_group.replay_option_features",
                command=[],
                next_internal_stage="model_group.replay_option_features",
            )
            for index, reason in enumerate(
                [
                    "model_group_replay_option_feature_repair_executed",
                    "model_group_replay_option_feature_repair_executed",
                    "model_group_replay_option_features_already_ready",
                ],
                start=1,
            )
        ]
        no_month = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="ready",
            reason_code="no_month_stage_ready",
            reason="no month stage ready",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=None,
            command=[],
            next_internal_stage="historical_training_work_loop",
        )

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision_log = tmp / "runtime" / "decisions.jsonl"
            with (
                patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=no_month),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_dataset_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_if_ready", return_value=replay_backoff) as replay,
                patch(
                    "trading_manager_tasks.scheduler_daemon.run_model_group_replay_option_features_for_replay_backoff",
                    side_effect=option_decisions,
                ) as repair,
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_review_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_residual_event_governance_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_evaluation_if_ready", return_value=None),
            ):
                run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=tmp / "runtime" / "state.json",
                    lock_path=tmp / "runtime" / "scheduler.lock",
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=1,
                    execute_safe_preparation=True,
                    execute_model_group_replay=True,
                    replay_option_feature_repair_limit=123,
                    source_existing_bootstrap=False,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

            replay.assert_called_once()
            self.assertEqual(repair.call_count, 3)
            self.assertTrue(all(call.kwargs["feature_repair_limit"] == 123 for call in repair.call_args_list))
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(
            [row["reason_code"] for row in log_rows],
            [
                "no_month_stage_ready",
                "model_group_replay_option_feature_acquisition_required",
                "model_group_replay_option_feature_repair_executed",
                "model_group_replay_option_feature_repair_executed",
                "model_group_replay_option_features_already_ready",
            ],
        )

    def test_daemon_drains_pending_replay_option_requirements_before_replay(self):
        pending_backoff = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_feature_acquisition_required",
            reason="replay_option_feature_acquisition_required",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay",
            command=[],
            next_internal_stage="model_group.replay",
        )
        option_backoff = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:01+00:00",
            now_et="2026-05-27T20:00:01-04:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_source_acquisition_required",
            reason="source missing",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay_option_features",
            command=[],
            next_internal_stage="model_group.replay_option_features",
        )
        no_month = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="ready",
            reason_code="no_month_stage_ready",
            reason="no month stage ready",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=None,
            command=[],
            next_internal_stage="historical_training_work_loop",
        )

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision_log = tmp / "runtime" / "decisions.jsonl"
            with (
                patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=no_month),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_dataset_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon._pending_replay_option_feature_backoff_decision", return_value=pending_backoff),
                patch(
                    "trading_manager_tasks.scheduler_daemon.run_model_group_replay_option_features_for_replay_backoff",
                    return_value=option_backoff,
                ) as repair,
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_if_ready") as replay,
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_review_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_residual_event_governance_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_evaluation_if_ready", return_value=None),
            ):
                run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=tmp / "runtime" / "state.json",
                    lock_path=tmp / "runtime" / "scheduler.lock",
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=1,
                    execute_safe_preparation=True,
                    execute_model_group_replay=True,
                    replay_option_feature_repair_limit=123,
                    source_existing_bootstrap=False,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

            repair.assert_called_once()
            replay.assert_not_called()
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]
            status_jsonl = decision_log.parent / "replay_option_feature_drain_status.jsonl"
            latest_status_json = decision_log.parent / "replay_option_feature_drain_latest.json"
            status_rows = [json.loads(line) for line in status_jsonl.read_text(encoding="utf-8").splitlines()]
            latest_status = json.loads(latest_status_json.read_text(encoding="utf-8"))

        self.assertEqual(
            [row["reason_code"] for row in log_rows],
            ["no_month_stage_ready", "model_group_replay_option_source_acquisition_required"],
        )
        self.assertEqual(len(status_rows), 1)
        self.assertEqual(status_rows[0]["event"], "batch_complete")
        self.assertEqual(status_rows[0]["reason_code"], "model_group_replay_option_source_acquisition_required")
        self.assertEqual(latest_status["reason_code"], "model_group_replay_option_source_acquisition_required")

    def test_daemon_retries_replay_after_pending_option_feature_repair_executes(self):
        pending_backoff = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_feature_acquisition_required",
            reason="replay_option_feature_acquisition_required",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay",
            command=[],
            next_internal_stage="model_group.replay",
        )
        option_executed = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:01+00:00",
            now_et="2026-05-27T20:00:01-04:00",
            decision_status="executed",
            reason_code="model_group_replay_option_feature_repair_executed",
            reason="prepared replay option source/features",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay_option_features",
            command=[],
            next_internal_stage="model_group.replay_option_features",
            execution_summary={"required_next_step": None},
        )
        replay_completed = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:02+00:00",
            now_et="2026-05-27T20:00:02-04:00",
            decision_status="executed",
            reason_code="model_group_replay_executed",
            reason="replay completed",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay",
            command=[],
            next_internal_stage="model_group.replay",
        )
        no_month = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="ready",
            reason_code="no_month_stage_ready",
            reason="no month stage ready",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=None,
            command=[],
            next_internal_stage="historical_training_work_loop",
        )

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision_log = tmp / "runtime" / "decisions.jsonl"

            def repair_once(replay_decision, **_kwargs):
                if replay_decision.reason_code == "model_group_replay_option_feature_acquisition_required":
                    return option_executed
                return None

            with (
                patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=no_month),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_dataset_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon._pending_replay_option_feature_backoff_decision", return_value=pending_backoff),
                patch(
                    "trading_manager_tasks.scheduler_daemon.run_model_group_replay_option_features_for_replay_backoff",
                    side_effect=repair_once,
                ),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_if_ready", return_value=replay_completed) as replay,
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_review_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_residual_event_governance_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_evaluation_if_ready", return_value=None),
            ):
                run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=tmp / "runtime" / "state.json",
                    lock_path=tmp / "runtime" / "scheduler.lock",
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=1,
                    execute_safe_preparation=True,
                    execute_model_group_replay=True,
                    drain_max_steps=1,
                    source_existing_bootstrap=False,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

            replay.assert_called_once()
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(
            [row["reason_code"] for row in log_rows],
            ["no_month_stage_ready", "model_group_replay_option_feature_repair_executed", "model_group_replay_executed"],
        )

    def test_daemon_does_not_retry_replay_when_pending_option_feature_repair_needs_more_drain(self):
        pending_backoff = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="backoff",
            reason_code="model_group_replay_option_feature_acquisition_required",
            reason="replay_option_feature_acquisition_required",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay",
            command=[],
            next_internal_stage="model_group.replay",
        )
        option_executed = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:01+00:00",
            now_et="2026-05-27T20:00:01-04:00",
            decision_status="executed",
            reason_code="model_group_replay_option_feature_repair_executed",
            reason="prepared replay option source/features",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work="model_group.replay_option_features",
            command=[],
            next_internal_stage="model_group.replay_option_features",
            execution_summary={"required_next_step": "continue replay option feature drain before retrying model_group.replay"},
        )
        no_month = SchedulerDecision(
            contract_type="manager_scheduler_decision",
            now_utc="2026-05-28T00:00:00+00:00",
            now_et="2026-05-27T20:00:00-04:00",
            decision_status="ready",
            reason_code="no_month_stage_ready",
            reason="no month stage ready",
            market_protection_active=False,
            resource_pressure_active=False,
            selected_work=None,
            command=[],
            next_internal_stage="historical_training_work_loop",
        )

        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision_log = tmp / "runtime" / "decisions.jsonl"

            def repair_once(replay_decision, **_kwargs):
                if replay_decision.reason_code == "model_group_replay_option_feature_acquisition_required":
                    return option_executed
                return None

            with (
                patch("trading_manager_tasks.scheduler_daemon.run_scheduler_once", return_value=no_month),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_dataset_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon._pending_replay_option_feature_backoff_decision", return_value=pending_backoff),
                patch(
                    "trading_manager_tasks.scheduler_daemon.run_model_group_replay_option_features_for_replay_backoff",
                    side_effect=repair_once,
                ),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_if_ready") as replay,
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_replay_review_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_residual_event_governance_if_ready", return_value=None),
                patch("trading_manager_tasks.scheduler_daemon.run_model_group_evaluation_if_ready", return_value=None),
            ):
                run_daemon_loop(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp / "manager-storage",
                    component_src_root=self._fake_data_src(tmp),
                    state_path=tmp / "runtime" / "state.json",
                    lock_path=tmp / "runtime" / "scheduler.lock",
                    decision_log_path=decision_log,
                    interval_seconds=0,
                    max_iterations=1,
                    execute_safe_preparation=True,
                    execute_model_group_replay=True,
                    drain_max_steps=1,
                    source_existing_bootstrap=False,
                    config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
                )

            replay.assert_not_called()

    def test_daemon_can_trigger_event_dashboard_refresh_after_executed_decision(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            marker = tmp / "dashboard_refresh_marker.txt"
            run_daemon_loop(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp / "manager-storage",
                component_src_root=self._fake_data_src(tmp),
                state_path=tmp / "runtime" / "state.json",
                lock_path=tmp / "runtime" / "scheduler.lock",
                decision_log_path=tmp / "runtime" / "decisions.jsonl",
                interval_seconds=0,
                max_iterations=1,
                execute_safe_preparation=True,
                refresh_dashboard_on_decision=True,
                dashboard_refresh_command=(sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).write_text('refreshed')"),
                source_existing_bootstrap=False,
                config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
            )

            self.assertEqual(marker.read_text(encoding="utf-8"), "refreshed")

    def test_dashboard_refresh_no_block_uses_systemctl_no_block(self):
        with patch.dict(os.environ, {"TRADING_MANAGER_DASHBOARD_REFRESH_NO_BLOCK": "true"}), patch(
            "trading_manager_tasks.scheduler_daemon.subprocess.run"
        ) as run:
            run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")

            result = refresh_dashboard_read_models(enabled=True, service_unit="refresh.service")

        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(run.call_args.args[0], ("systemctl", "start", "--no-block", "refresh.service"))


if __name__ == "__main__":
    unittest.main()

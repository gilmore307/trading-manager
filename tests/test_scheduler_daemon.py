from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from trading_manager_tasks.scheduler import ResourceSnapshot, SchedulerConfig
from trading_manager_tasks.model_training_state import advance_workflow_state, workflow_state_path_for_month
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.scheduler_daemon import (
    SchedulerDaemonState,
    acquire_daemon_lock,
    apply_auto_work_selection,
    completed_historical_month_cutoff,
    load_model_worker_target_queue,
    load_daemon_state,
    model_worker_fold_state_path,
    next_month,
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
)



class SchedulerDaemonTests(unittest.TestCase):

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

    def test_select_next_historical_work_advances_after_latest_completed_month(self):
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

        self.assertEqual(selection.start_month, "2016-04")
        self.assertEqual(selection.end_month, "2016-04")
        self.assertEqual(selection.reason_code, "advance_after_latest_completed_workflow_state")
        self.assertEqual(selection.completed_months, ("2016-02", "2016-03"))
        self.assertEqual(selection.open_months, ())

    def test_select_next_historical_work_does_not_publish_incomplete_calendar_month(self):
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

        self.assertEqual(selection.start_month, "2026-04")
        self.assertEqual(selection.end_month, "2026-04")
        self.assertEqual(selection.reason_code, "waiting_for_next_calendar_month_to_complete")

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

        self.assertEqual(selection.start_month, "2026-04")
        self.assertEqual(selection.reason_code, "waiting_for_next_calendar_month_to_complete")
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

    def test_month_ingest_worker_selection_fills_three_lanes_after_completed_months(self):
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
            capped = select_month_ingest_worker_months(storage_root=storage_root, default_start_month="2016-01", worker_count=3, max_month="2016-04")

        self.assertEqual(selected, ("2016-03", "2016-04", "2016-05"))
        self.assertEqual(capped, ("2016-03", "2016-04"))


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
        self.assertIn("layer_01_market_regime.model_generation", ready)

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

        self.assertIsNone(overlapping_selection)
        self.assertIsNotNone(next_selection)
        assert next_selection is not None
        self.assertEqual(next_selection.fold_id, "fold_2016-07_2016-12")
        self.assertEqual(next_selection.fold_months, ("2016-07", "2016-08", "2016-09", "2016-10", "2016-11", "2016-12"))

    def test_model_worker_skips_blocked_fold_and_selects_next_ready_fold(self):
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

            selection = select_model_worker_fold(storage_root=storage_root, default_start_month="2016-01", max_month="2016-12")

        self.assertIsNotNone(selection)
        assert selection is not None
        self.assertEqual(selection.fold_id, "fold_2016-07_2016-12")
        self.assertEqual(selection.reason_code, "complete_foundation_fold_ready")

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


if __name__ == "__main__":
    unittest.main()

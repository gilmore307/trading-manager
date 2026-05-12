from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.scheduler import ResourceSnapshot, SchedulerConfig
from trading_manager_tasks.model_training_state import advance_workflow_state, workflow_state_path_for_month
from trading_manager_tasks.model_training_workflow import build_model_training_workflow_plan
from trading_manager_tasks.scheduler_daemon import (
    SchedulerDaemonState,
    acquire_daemon_lock,
    apply_auto_work_selection,
    load_daemon_state,
    next_month,
    release_daemon_lock,
    run_daemon_loop,
    select_next_historical_work,
    update_state_from_error,
    write_daemon_state,
)



class SchedulerDaemonTests(unittest.TestCase):
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
                config=SchedulerConfig(min_free_disk_gb=0, protected_start_et="00:00", protected_end_et="00:00"),
            )

        self.assertEqual(state.start_month, "2016-02")
        self.assertEqual(state.end_month, "2016-02")
        self.assertEqual(state.last_reason_code, "month_workflow_complete")
        self.assertEqual(state.last_next_internal_stage, "chronological_month_advanced")
        self.assertTrue(state.service_managed)

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


if __name__ == "__main__":
    unittest.main()

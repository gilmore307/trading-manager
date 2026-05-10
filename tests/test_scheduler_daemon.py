from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.scheduler import ResourceSnapshot, SchedulerConfig
from trading_manager_tasks.scheduler_daemon import (
    SchedulerDaemonState,
    acquire_daemon_lock,
    load_daemon_state,
    release_daemon_lock,
    run_daemon_loop,
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
                config=SchedulerConfig(min_free_disk_gb=0),
            )

            self.assertEqual(state.total_ticks, 1)
            self.assertEqual(state.successful_ticks, 1)
            self.assertEqual(state.last_next_internal_stage, "approval_gated_provider_acquisition")
            self.assertFalse(lock_path.exists())
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["contract_type"], "manager_scheduler_daemon_state_v1")
            log_rows = [json.loads(line) for line in decision_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(log_rows), 1)
            self.assertEqual(log_rows[0]["provider_calls"], 0)


if __name__ == "__main__":
    unittest.main()

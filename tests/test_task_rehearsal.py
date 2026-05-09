from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from trading_manager_tasks.task_rehearsal import rehearse_monthly_backfill_task_system

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "tasks" / "rehearse_task_system.py"


class TaskSystemRehearsalTests(unittest.TestCase):
    def test_mixed_rehearsal_exercises_ready_partial_failed_paths(self) -> None:
        rehearsal = rehearse_monthly_backfill_task_system(end_month="2016-01", limit=3, scenario="mixed")

        self.assertEqual(rehearsal["contract_type"], "manager_task_system_rehearsal_v1")
        self.assertTrue(rehearsal["rehearsal_only"])
        self.assertEqual(rehearsal["request_count"], 3)
        statuses = [row["task_status"] for row in rehearsal["task_summary"]]
        self.assertEqual(statuses, ["ready", "partial", "failed"])
        partial = next(row for row in rehearsal["task_summary"] if row["task_status"] == "partial")
        failed = next(row for row in rehearsal["task_summary"] if row["task_status"] == "failed")
        self.assertTrue(partial["latest_ready_signal_review_required"])
        self.assertIn("simulated provider failure", failed["latest_ready_signal_blocking_reason"])
        self.assertGreater(partial["artifact_count"], failed["artifact_count"])

    def test_success_rehearsal_keeps_all_tasks_ready(self) -> None:
        rehearsal = rehearse_monthly_backfill_task_system(end_month="2016-01", limit=2, scenario="success")

        self.assertEqual([row["task_status"] for row in rehearsal["task_summary"]], ["ready", "ready"])
        self.assertTrue(all(not row["latest_ready_signal_review_required"] for row in rehearsal["task_summary"]))

    def test_rehearsal_cli_emits_task_summary_rows(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--end-month", "2016-01", "--limit", "2", "--scenario", "success", "--format", "jsonl"],
            cwd=REPO_ROOT,
            env={"PYTHONPATH": "src"},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len([row for row in rows if row["section"] == "manager_request"]), 2)
        self.assertEqual(len([row for row in rows if row["section"] == "task_summary"]), 2)
        self.assertTrue(all(row["task_status"] == "ready" for row in rows if row["section"] == "task_summary"))


if __name__ == "__main__":
    unittest.main()

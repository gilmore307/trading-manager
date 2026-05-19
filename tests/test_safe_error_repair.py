from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.agent_error_handler import build_server_error_agent_request, register_error_in_catalog
from trading_manager_tasks.safe_error_repair import build_diagnosis


class SafeErrorRepairTests(unittest.TestCase):
    def test_repairs_scheduler_dead_pid_lock_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            lock = tmp / "storage/runtime/historical_scheduler.lock"
            lock.parent.mkdir(parents=True)
            lock.write_text('{"pid": 999999999, "created_utc": "2026-05-13T00:00:00Z"}\n', encoding="utf-8")
            request = build_server_error_agent_request(
                source_component="trading-manager.historical_scheduler_daemon",
                source_repo="trading-manager",
                error_scope="server_service",
                error_kind="RuntimeError",
                summary="historical scheduler daemon failed: scheduler daemon lock is active: storage/runtime/historical_scheduler.lock",
                working_directory=str(tmp),
            )
            request, _ = register_error_in_catalog(request, output_root=tmp / "agent_errors", catalog_storage="jsonl")

            diagnosis = build_diagnosis(request)
            report = json.loads(diagnosis["stdout"])

            self.assertEqual(diagnosis["status"], "completed")
            self.assertEqual(report["repair"]["repair_status"], "repaired")
            self.assertFalse(lock.exists())

    def test_unknown_error_is_not_modified(self) -> None:
        request = build_server_error_agent_request(source_component="server.unknown", summary="unknown failure")
        diagnosis = build_diagnosis(request)
        report = json.loads(diagnosis["stdout"])
        self.assertEqual(report["repair"]["repair_status"], "not_supported")
        self.assertFalse(report["repair_attempted"])


if __name__ == "__main__":
    unittest.main()

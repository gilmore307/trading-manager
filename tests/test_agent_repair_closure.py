from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.agent_repair_closure import (
    ClosureCandidate,
    close_agent_repair,
    close_pending_agent_repairs,
    discover_closure_candidates,
)


class AgentRepairClosureTests(unittest.TestCase):
    def _write_candidate(
        self,
        root: Path,
        *,
        request_overrides: dict[str, object] | None = None,
        stdout_payload: dict[str, object] | None = None,
    ) -> ClosureCandidate:
        request_dir = root / "erragent_fixture"
        request_dir.mkdir(parents=True)
        request = {
            "contract_type": "server_error_agent_request",
            "schema_version": "1",
            "request_id": "erragent_fixture",
            "error_ref": "ERR-000001",
            "source_component": "trading-manager.scheduler_daemon",
            "error_scope": "server.scheduler_progress",
            "error_kind": "scheduler_progress_stalled",
            "summary": "scheduler stalled",
        }
        request.update(request_overrides or {})
        payload = stdout_payload or {
            "diagnosis_status": "repaired_with_runtime_restart_pending",
            "root_cause": "scheduler code was repaired",
            "repair_attempted": True,
            "files_changed": ["/repo/trading-manager/src/trading_manager_tasks/scheduler_daemon.py"],
            "retry_recommendation": "restart service and retry scheduler selection",
            "blockers": [],
        }
        diagnosis = {
            "contract_type": "agent_error_diagnosis",
            "schema_version": "1",
            "diagnosis_id": "errdiag_fixture",
            "request_ref": "erragent_fixture",
            "agent_ref": "codex_cli_gpt_5_5",
            "runner_command": "codex",
            "status": "completed",
            "return_code": 0,
            "stdout": json.dumps(payload),
            "stderr": "",
            "completed_at_utc": "2026-06-08T05:00:00Z",
        }
        request_path = request_dir / "server_error_agent_request.json"
        diagnosis_path = request_dir / "agent_error_diagnosis.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
        return ClosureCandidate(
            request_dir=request_dir,
            request_path=request_path,
            diagnosis_path=diagnosis_path,
            receipt_path=request_dir / "agent_repair_closure_receipt.json",
        )

    def test_repaired_scheduler_error_pushes_and_restarts_internal_services(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            repo = tmp / "trading-manager"
            repo.mkdir()
            candidate = self._write_candidate(
                tmp / "agent",
                stdout_payload={
                    "diagnosis_status": "repaired_with_runtime_restart_pending",
                    "files_changed": [str(repo / "src" / "trading_manager_tasks" / "scheduler_daemon.py")],
                    "retry_recommendation": "service restart required, then retry scheduler selection",
                    "blockers": [],
                },
            )
            calls: list[tuple[str, ...]] = []

            def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(tuple(argv))
                if argv[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="main\n", stderr="")
                if argv[:2] == ["git", "status"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                if argv[:3] == ["git", "rev-list", "--count"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="1\n", stderr="")
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            receipt = close_agent_repair(candidate, runner=fake_run, repo_roots=(repo,))

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertIn(("git", "push", "origin", "main"), calls)
        self.assertIn(("systemctl", "restart", "trading-manager-historical-scheduler.service"), calls)
        self.assertIn(("systemctl", "start", "trading-storage-dashboard-read-model-refresh.service"), calls)
        self.assertFalse(receipt["safety"]["broker_account_order_position_mutation_performed"])

    def test_broker_boundary_blocks_automatic_closure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            candidate = self._write_candidate(
                Path(raw_tmp),
                request_overrides={
                    "source_component": "trading-execution.broker",
                    "error_scope": "broker_order_submission",
                    "summary": "order submission failed",
                },
            )
            receipt = close_agent_repair(candidate, runner=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, "", ""))

        self.assertEqual(receipt["closure_status"], "blocked")
        self.assertIn("broker/account/order", receipt["blockers"][0])

    def test_discovery_skips_requests_with_existing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            candidate.receipt_path.write_text(json.dumps({"closure_status": "closed"}), encoding="utf-8")

            self.assertEqual(discover_closure_candidates(root), ())
            self.assertEqual(close_pending_agent_repairs(output_root=root), [])

    def test_plan_only_does_not_write_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            receipts = close_pending_agent_repairs(
                output_root=root,
                execute_actions=False,
                repo_roots=(Path("/repo/trading-manager"),),
            )

            self.assertEqual(len(receipts), 1)
            self.assertTrue(receipts[0]["dry_run"])
            self.assertFalse(candidate.receipt_path.exists())

    def test_incomplete_diagnosis_remains_pending_without_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")

            receipt = close_agent_repair(candidate)

            self.assertEqual(receipt["closure_status"], "pending")
            self.assertFalse(candidate.receipt_path.exists())


if __name__ == "__main__":
    unittest.main()

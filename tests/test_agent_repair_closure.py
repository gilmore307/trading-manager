from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.agent_repair_closure import (
    ClosureCandidate,
    close_agent_repair,
    close_pending_agent_repairs,
    discover_agent_diagnosis_candidates,
    discover_closure_candidates,
    run_pending_agent_diagnoses,
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
            "agent_ref": "codex_cli_gpt_5_5",
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

    def test_push_blocked_diagnosis_blocks_automatic_closure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            candidate = self._write_candidate(
                Path(raw_tmp),
                stdout_payload={
                    "diagnosis_status": "repaired_with_push_blocked",
                    "files_changed": ["/repo/trading-manager/src/trading_manager_tasks/option_chain_source_acquisition.py"],
                    "retry_recommendation": "manual_review",
                    "blockers": ["push blocked"],
                },
            )
            receipt = close_agent_repair(candidate, runner=lambda argv, **kwargs: subprocess.CompletedProcess(argv, 0, "", ""))

        self.assertEqual(receipt["closure_status"], "blocked")
        self.assertIn("automatic retry", receipt["blockers"][0])

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

    def test_plan_only_does_not_run_agent_diagnosis_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")

            with unittest.mock.patch("trading_manager_tasks.agent_repair_closure.call_agent_runner") as runner:
                receipts = close_pending_agent_repairs(output_root=root, execute_actions=False)

        self.assertEqual(len(receipts), 1)
        self.assertFalse(runner.called)
        self.assertEqual(receipts[0]["closure_status"], "pending")

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

    def test_incomplete_diagnosis_closes_when_retry_receipt_succeeded(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            control_root = Path(raw_tmp) / "storage" / "02_control_plane"
            root = control_root / "runtime" / "agent_error_handling"
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "error_scope": "server.model_training_stage",
                    "summary": "model training stage model_05_option_expression.feature_generation stage command returned non-zero status",
                },
            )
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            diagnosis["stderr"] = "agent call not requested"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
            receipt_dir = control_root / "runtime" / "model_training_stage_receipts" / "model_05_option_expression__feature_generation"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "2026-06-11T124916.000000+0000.receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "model_05_option_expression.feature_generation",
                        "status": "succeeded",
                        "completed_at": "2026-06-11T12:49:16Z",
                        "runs": [{"status": "succeeded", "return_code": 0}],
                    }
                ),
                encoding="utf-8",
            )

            receipt = close_agent_repair(candidate)

            self.assertEqual(receipt["closure_status"], "closed")
            self.assertTrue(candidate.receipt_path.exists())
            self.assertEqual(receipt["actions"][0]["action"], "retry_receipt_observed")

    def test_blocked_completed_diagnosis_closes_when_retry_receipt_succeeded(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            control_root = Path(raw_tmp) / "storage" / "02_control_plane"
            root = control_root / "runtime" / "agent_error_handling"
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "error_scope": "server.model_training_stage",
                    "summary": "model training stage model_02_target_state.feature_generation stage command exceeded timeout_seconds=1800",
                },
                stdout_payload={
                    "diagnosis_status": "fixed_pending_retry",
                    "root_cause": "stage timeout issue, not a broker/account/order/fill/position problem",
                    "files_changed": [],
                    "retry_recommendation": "retry_original_stage_command",
                    "blockers": ["original stage had not rerun yet"],
                },
            )
            candidate.receipt_path.write_text(
                json.dumps({"contract_type": "agent_repair_closure_receipt", "closure_status": "blocked"}),
                encoding="utf-8",
            )
            receipt_dir = control_root / "runtime" / "model_training_stage_receipts" / "model_02_target_state__feature_generation"
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "2026-06-22T155411.926989+0000.receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": "model_02_target_state.feature_generation",
                        "status": "succeeded",
                        "completed_at": "2026-06-22T16:37:07Z",
                        "runs": [{"status": "succeeded", "return_code": 0}],
                    }
                ),
                encoding="utf-8",
            )

            candidates = discover_closure_candidates(root)
            receipt = close_pending_agent_repairs(output_root=root, recover_agent_diagnoses=False)[0]

            self.assertEqual(len(candidates), 1)
            self.assertEqual(receipt["closure_status"], "closed")
            self.assertEqual(receipt["actions"][0]["action"], "retry_receipt_observed")
            self.assertEqual(receipt["blockers"], [])

    def test_incomplete_provider_diagnosis_closes_when_failure_register_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp) / "storage" / "02_control_plane" / "runtime" / "agent_error_handling"
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "error_scope": "server.provider_stage_failure_register",
                    "error_kind": "provider_stage_requests_failed",
                    "summary": "provider stage model_02_target_state.option_chain_data_acquisition has 10 failed request(s) requiring automatic repair",
                },
            )
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            diagnosis["stderr"] = "agent call not requested"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
            resolved_rows = [
                {
                    "stage_id": "model_02_target_state.option_chain_data_acquisition",
                    "failure_status": "corrected",
                }
            ]

            with unittest.mock.patch(
                "trading_manager_tasks.agent_repair_closure.fetch_failure_register_rows",
                return_value=resolved_rows,
            ):
                receipt = close_agent_repair(candidate)

            self.assertEqual(receipt["closure_status"], "closed")
            self.assertTrue(candidate.receipt_path.exists())
            self.assertEqual(receipt["actions"][0]["action"], "failure_register_resolved")

    def test_discovers_request_without_diagnosis_for_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            request_dir = root / "erragent_missing_diagnosis"
            request_dir.mkdir()
            (request_dir / "server_error_agent_request.json").write_text(
                json.dumps(
                    {
                        "contract_type": "server_error_agent_request",
                        "schema_version": "1",
                        "request_id": "erragent_missing_diagnosis",
                        "agent_ref": "codex_cli_gpt_5_5",
                    }
                ),
                encoding="utf-8",
            )

            candidates = discover_agent_diagnosis_candidates(root)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].request_dir.name, "erragent_missing_diagnosis")

    def test_recovery_runs_agent_for_queued_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            diagnosis["stderr"] = "agent runner call pending"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")

            with unittest.mock.patch(
                "trading_manager_tasks.agent_repair_closure.call_agent_runner",
                return_value={
                    "contract_type": "agent_error_diagnosis",
                    "schema_version": "1",
                    "diagnosis_id": "errdiag_recovered",
                    "request_ref": "erragent_fixture",
                    "agent_ref": "codex_cli_gpt_5_5",
                    "runner_command": "codex",
                    "status": "completed",
                    "return_code": 0,
                    "stdout": json.dumps(
                        {
                            "diagnosis_status": "repaired_verified",
                            "repair": {"repair_status": "repaired", "files_changed": []},
                            "retry_recommendation": "retry",
                            "blockers": [],
                        }
                    ),
                    "stderr": "",
                    "completed_at_utc": "2026-06-08T05:10:00Z",
                },
            ) as runner, unittest.mock.patch.dict(
                "os.environ",
                {"MANAGER_AGENT_ERROR_RUNNER_COMMAND": "codex repair"},
                clear=False,
            ):
                diagnoses = run_pending_agent_diagnoses(output_root=root)

            recovered = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))

        self.assertEqual(len(diagnoses), 1)
        self.assertEqual(recovered["status"], "completed")
        self.assertEqual(recovered["diagnosis_id"], "errdiag_recovered")
        self.assertEqual(runner.call_args.kwargs["runner_command"], "codex repair")

    def test_runner_not_configured_queue_is_not_auto_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            diagnosis["stderr"] = "agent runner not configured for closure recovery"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")

            candidates = discover_agent_diagnosis_candidates(root)

        self.assertEqual(candidates, ())

    def test_stale_recovery_candidate_is_not_auto_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            candidate = self._write_candidate(root)
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "queued"
            diagnosis["stderr"] = "agent runner recovery call pending"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
            stale_time = 1_700_000_000
            os.utime(candidate.request_path, (stale_time, stale_time))

            candidates = discover_agent_diagnosis_candidates(root)

        self.assertEqual(candidates, ())


if __name__ == "__main__":
    unittest.main()

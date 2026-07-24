from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
import unittest.mock
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

    def test_github_https_push_uses_askpass_token_without_command_exposure(self) -> None:
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
            push_envs: list[dict[str, str]] = []
            calls: list[tuple[str, ...]] = []

            def fake_run(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
                calls.append(tuple(argv))
                if argv[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="main\n", stderr="")
                if argv[:2] == ["git", "status"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                if argv[:3] == ["git", "rev-list", "--count"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="1\n", stderr="")
                if argv[:3] == ["git", "remote", "get-url"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="https://github.com/gilmore307/trading-manager.git\n", stderr="")
                if argv[:3] == ["git", "push", "origin"]:
                    push_envs.append(dict(kwargs.get("env") or {}))
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            with unittest.mock.patch.dict(os.environ, {"MANAGER_AGENT_REPAIR_GITHUB_TOKEN": "fixture-token"}):
                receipt = close_agent_repair(candidate, runner=fake_run, repo_roots=(repo,))

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertIn(("git", "push", "origin", "main"), calls)
        self.assertEqual(len(push_envs), 1)
        self.assertEqual(push_envs[0]["GIT_ASKPASS_TOKEN"], "fixture-token")
        self.assertEqual(push_envs[0]["GIT_TERMINAL_PROMPT"], "0")
        self.assertTrue(push_envs[0]["GIT_ASKPASS"].endswith("askpass.sh"))
        self.assertFalse(any("fixture-token" in " ".join(call) for call in calls))

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

    def test_broker_safety_statement_does_not_block_repaired_internal_closure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            repo = tmp / "trading-manager"
            changed_file = repo / "src" / "trading_manager_tasks" / "model_group_replay_option_features.py"
            changed_file.parent.mkdir(parents=True)
            changed_file.write_text("# fixture\n", encoding="utf-8")
            candidate = self._write_candidate(
                tmp / "agent",
                request_overrides={
                    "source_component": "trading-manager.model_group_replay_option_features",
                    "error_scope": "server.replay_option_feature_repair",
                    "error_kind": "model_group_replay_option_source_acquisition_failed",
                    "summary": "replay option source/feature repair failed for emitted signal CSX",
                },
                stdout_payload={
                    "diagnosis_status": "repaired_verified_push_blocked",
                    "files_changed": ["src/trading_manager_tasks/model_group_replay_option_features.py"],
                    "retry_recommendation": "retry_or_continue_model_group_replay_option_features_drain",
                    "blockers": [
                        "Push blocked before closure retry",
                        "No broker, account, order, fill, position, buying-power, or funds state was mutated.",
                    ],
                },
            )

            def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                if argv[:3] == ["git", "rev-parse", "--abbrev-ref"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="main\n", stderr="")
                if argv[:2] == ["git", "status"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
                if argv[:3] == ["git", "rev-list", "--count"]:
                    return subprocess.CompletedProcess(argv, 0, stdout="0\n", stderr="")
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            receipt = close_agent_repair(candidate, runner=fake_run, repo_roots=(repo,))

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertEqual(receipt["blockers"], [])

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

    def test_push_blocked_diagnosis_closes_after_repo_is_pushed_and_drain_can_continue(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            repo = tmp / "trading-manager"
            changed_file = repo / "src" / "trading_manager_tasks" / "option_chain_source_acquisition.py"
            changed_file.parent.mkdir(parents=True)
            changed_file.write_text("# fixture\n", encoding="utf-8")
            candidate = self._write_candidate(
                tmp / "agent",
                stdout_payload={
                    "diagnosis_status": "repaired_verified_push_blocked",
                    "files_changed": ["src/trading_manager_tasks/option_chain_source_acquisition.py"],
                    "retry_recommendation": "retry_or_continue_model_group_replay_option_features_drain",
                    "blockers": [
                        "git push origin main failed before closure retry",
                        "The full replay option-feature artifact is not yet drained",
                    ],
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
                    return subprocess.CompletedProcess(argv, 0, stdout="0\n", stderr="")
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            receipt = close_agent_repair(candidate, runner=fake_run, repo_roots=(repo,))

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertEqual(receipt["blockers"], [])
        self.assertIn(("git", "rev-list", "--count", "origin/main..HEAD"), calls)
        self.assertEqual(receipt["actions"][0]["action"], "git_push")
        self.assertEqual(receipt["actions"][0]["status"], "not_needed")

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

    def test_manager_stage_evidence_ref_closes_memory_guard_after_retry_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            control_root = Path(raw_tmp) / "storage" / "02_control_plane"
            root = control_root / "runtime" / "agent_error_handling"
            stage_id = "model_05_option_expression.model_generation.train"
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "error_scope": "server.model_training_stage",
                    "summary": f"model training stage {stage_id} stage memory guard exceeded max_rss_mb=16384",
                    "evidence_refs": [f"manager_stage:{stage_id}"],
                },
                stdout_payload={
                    "diagnosis_status": "repaired_verified_push_blocked",
                    "root_cause": "M05 generation exceeded memory guard before streaming repair.",
                    "files_changed": ["scripts/models/model_05_option_expression/generate_model_05_option_expression.py"],
                    "retry_recommendation": "retry original stage command",
                    "blockers": ["git push failed before closure retry"],
                },
            )
            candidate.receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "closure_status": "blocked",
                        "actions": [{"action": "git_push", "status": "failed"}],
                        "blockers": ["existing blocked closure requires new successful retry evidence"],
                    }
                ),
                encoding="utf-8",
            )
            receipt_dir = control_root / "runtime" / "model_training_stage_receipts" / stage_id.replace(".", "__")
            receipt_dir.mkdir(parents=True)
            (receipt_dir / "2026-07-07T111516.497372+0000.receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "component_completion_receipt",
                        "manager_stage_id": stage_id,
                        "status": "succeeded",
                        "completed_at": "2026-07-07T11:25:51Z",
                        "runs": [{"status": "succeeded", "return_code": 0}],
                    }
                ),
                encoding="utf-8",
            )

            receipt = close_agent_repair(candidate)

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertEqual(receipt["actions"][0]["action"], "retry_receipt_observed")
        self.assertEqual(receipt["actions"][0]["stage_id"], stage_id)
        self.assertEqual(receipt["blockers"], [])

    def test_blocked_replay_source_error_closes_when_source_requests_succeeded(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            control_root = Path(raw_tmp) / "storage" / "02_control_plane"
            root = control_root / "runtime" / "agent_error_handling"
            source_root = (
                control_root.parent
                / "01_source_data"
                / "model_05_option_expression"
                / "option_chain_state_source"
                / "2021-03"
            )
            request_ids = (
                "mgrreq_replay_option_chain_window_mnst_2021_03_2021_03_11_1600",
                "mgrreq_replay_option_chain_window_nem_2021_03_2021_03_11_1600",
            )
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "source_component": "trading-manager.model_group_replay_option_features",
                    "error_scope": "server.replay_option_feature_repair",
                    "error_kind": "model_group_replay_option_source_acquisition_failed",
                    "summary": "replay option source/feature repair failed for emitted signal MNST 2021-03-11T16:00:00-05:00",
                    "evidence_refs": [f"manager_request:{request_id}" for request_id in request_ids],
                },
                stdout_payload={
                    "diagnosis_status": "repaired_with_push_blocked",
                    "files_changed": ["src/trading_manager_tasks/model_group_replay_option_features.py"],
                    "retry_recommendation": "retry model_group.replay_option_features",
                    "blockers": ["original source request needed retry evidence"],
                },
            )
            candidate.receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "closure_status": "blocked",
                        "actions": [{"action": "git_push", "status": "failed"}],
                        "blockers": ["existing blocked closure requires new successful retry evidence"],
                    }
                ),
                encoding="utf-8",
            )
            for request_id in request_ids:
                receipt_path = source_root / request_id / "completion_receipt.json"
                receipt_path.parent.mkdir(parents=True)
                receipt_path.write_text(
                    json.dumps(
                        {
                            "task_id": request_id,
                            "source": "option_chain_state_source",
                            "runs": [
                                {
                                    "run_id": f"{request_id}_provider_20260626T053229Z",
                                    "status": "succeeded",
                                    "completed_at": "2026-06-26T05:32:33Z",
                                    "row_counts": {"option_chain_state_source": 36},
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

            receipt = close_agent_repair(candidate)

            self.assertEqual(receipt["closure_status"], "closed")
            self.assertEqual(receipt["blockers"], [])
            self.assertEqual(receipt["actions"][0]["action"], "source_request_receipts_observed")
            self.assertEqual(receipt["actions"][0]["receipt_count"], 2)
            self.assertTrue(candidate.receipt_path.exists())

    def test_blocked_replay_option_feature_error_closes_when_later_replay_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            control_root = Path(raw_tmp) / "storage" / "02_control_plane"
            root = control_root / "runtime" / "agent_error_handling"
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "created_at_utc": "2026-06-27T20:18:45Z",
                    "occurred_at_utc": "2026-06-27T20:18:45Z",
                    "source_component": "trading-manager.model_group_replay_option_features",
                    "error_scope": "server.replay_option_feature_repair",
                    "error_kind": "model_group_replay_option_feature_generation_failed",
                    "summary": "replay option source/feature repair failed for emitted signal SNOW 2022-09-14T16:00:00-04:00",
                    "evidence_refs": [str(control_root / "runtime" / "historical_scheduler_decisions.jsonl")],
                },
                stdout_payload={
                    "diagnosis_status": "repaired_verified_push_blocked",
                    "files_changed": ["src/data_feature/m05_option_expression_feature_generation/generator.py"],
                    "retry_recommendation": "retry_or_continue_model_group_replay_option_features_drain",
                    "blockers": ["git push failed before closure retry"],
                },
            )
            candidate.receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "closure_status": "blocked",
                        "actions": [{"action": "git_push", "status": "failed"}],
                        "blockers": ["existing blocked closure requires new successful retry evidence"],
                    }
                ),
                encoding="utf-8",
            )
            decisions_path = control_root / "runtime" / "historical_scheduler_decisions.jsonl"
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            decisions_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "now_utc": "2026-06-27T20:00:00+00:00",
                                "reason_code": "model_group_replay_executed",
                                "execution_summary": {
                                    "replay_execution_receipt": {
                                        "replay_execution_run_id": "too_old",
                                        "validation_status": "passed",
                                        "portfolio_selection_summary": {"missing_option_feature_requirement_count": 0},
                                        "option_replay_coverage": {
                                            "coverage_status": "complete",
                                            "feature_snapshot_count": 10,
                                            "expected_option_signal_snapshot_count": 10,
                                        },
                                    }
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "now_utc": "2026-06-28T05:50:41+00:00",
                                "reason_code": "model_group_replay_executed",
                                "execution_summary": {
                                    "replay_execution_receipt": {
                                        "replay_execution_run_id": "model_group_replay_20260628T055041Z_complete",
                                        "completed_replay_month_count": 52,
                                        "validation_status": "passed",
                                        "portfolio_selection_summary": {"missing_option_feature_requirement_count": 0},
                                        "option_replay_coverage": {
                                            "coverage_status": "complete",
                                            "feature_snapshot_count": 134,
                                            "expected_option_signal_snapshot_count": 134,
                                        },
                                    }
                                },
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            receipt = close_agent_repair(candidate)

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertEqual(receipt["blockers"], [])
        self.assertEqual(receipt["actions"][0]["action"], "replay_option_feature_run_observed")
        self.assertEqual(
            receipt["actions"][0]["receipt"]["replay_execution_run_id"],
            "model_group_replay_20260628T055041Z_complete",
        )

    def test_scheduler_progress_stalled_closes_when_later_scheduler_work_executes(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            control_root = Path(raw_tmp) / "storage" / "02_control_plane"
            root = control_root / "runtime" / "agent_error_handling"
            candidate = self._write_candidate(
                root,
                request_overrides={
                    "created_at_utc": "2026-06-23T14:38:38Z",
                    "occurred_at_utc": "2026-06-23T14:38:38Z",
                    "error_kind": "scheduler_progress_stalled",
                    "error_scope": "server.scheduler_progress",
                    "source_component": "trading-manager.scheduler_daemon",
                    "summary": "historical scheduler made no progress for 729 seconds",
                },
                stdout_payload={
                    "diagnosis_status": "repaired_verified",
                    "files_changed": [],
                    "retry_recommendation": "continue scheduler",
                    "blockers": [],
                },
            )
            diagnosis = json.loads(candidate.diagnosis_path.read_text(encoding="utf-8"))
            diagnosis["status"] = "agent_call_failed"
            candidate.diagnosis_path.write_text(json.dumps(diagnosis), encoding="utf-8")
            decisions_path = control_root / "runtime" / "historical_scheduler_decisions.jsonl"
            decisions_path.parent.mkdir(parents=True, exist_ok=True)
            decisions_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "now_utc": "2026-06-23T14:37:00+00:00",
                                "decision_status": "executed",
                                "reason_code": "too_old",
                                "selected_work": "model_group.replay",
                            }
                        ),
                        json.dumps(
                            {
                                "now_utc": "2026-06-28T05:53:27+00:00",
                                "decision_status": "executed",
                                "reason_code": "model_group_replay_executed",
                                "selected_work": "model_group.replay",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            receipt = close_agent_repair(candidate)

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertEqual(receipt["blockers"], [])
        self.assertEqual(receipt["actions"][0]["action"], "scheduler_progress_observed")
        self.assertEqual(receipt["actions"][0]["receipt"]["reason_code"], "model_group_replay_executed")

    def test_blocked_closure_does_not_repeat_scheduler_restart(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            repo = tmp / "trading-manager"
            changed_file = repo / "src" / "trading_manager_tasks" / "scheduler_daemon.py"
            changed_file.parent.mkdir(parents=True)
            changed_file.write_text("# fixture\n", encoding="utf-8")
            candidate = self._write_candidate(
                tmp / "agent",
                request_overrides={
                    "source_component": "trading-manager.historical_scheduler_daemon",
                    "error_scope": "server_service",
                    "error_kind": "scheduler_progress_stalled",
                },
                stdout_payload={
                    "diagnosis_status": "repaired_with_runtime_restart_pending",
                    "files_changed": [str(changed_file)],
                    "retry_recommendation": "service restart required, then retry scheduler selection",
                    "blockers": [],
                },
            )
            candidate.receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "closure_status": "blocked",
                        "actions": [
                            {
                                "action": "systemctl_restart",
                                "service": "trading-manager-historical-scheduler.service",
                                "status": "completed",
                            }
                        ],
                        "blockers": ["git push failed before closure retry"],
                    }
                ),
                encoding="utf-8",
            )
            calls: list[tuple[str, ...]] = []

            def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(tuple(argv))
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            receipt = close_agent_repair(candidate, runner=fake_run, repo_roots=(repo,))

        self.assertEqual(receipt["closure_status"], "blocked")
        self.assertEqual(calls, [])
        self.assertEqual(receipt["actions"][-1]["action"], "blocked_closure_recheck")

    def test_scheduler_lock_conflict_closes_as_no_action_after_blocked_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            candidate = self._write_candidate(
                Path(raw_tmp),
                request_overrides={
                    "source_component": "trading-manager.historical_scheduler_daemon",
                    "error_scope": "server_service",
                    "error_kind": "RuntimeError",
                    "summary": "historical scheduler daemon failed: scheduler daemon lock is active",
                },
                stdout_payload={
                    "diagnosis_status": "completed",
                    "root_cause": (
                        "operator-boundary/concurrency: scheduler daemon lock is active. "
                        "The single-daemon guard correctly rejected a duplicate startup because "
                        "the lock was already held by a running scheduler process. Current service status "
                        "is active/running with service_runtime_ready=true and lock.status=active."
                    ),
                    "verification": [
                        {
                            "command": "ps -p 897353 -o pid,ppid,stat,etime,cmd",
                            "status": "passed",
                            "evidence": "Confirmed PID 897353 is a live run_automation_scheduler_daemon.py process.",
                        }
                    ],
                    "repair_attempted": False,
                    "files_changed": [],
                    "retry_recommendation": "close_without_retry_of_the_same_command_while_the_service_is_running",
                    "blockers": [],
                },
            )
            candidate.receipt_path.write_text(
                json.dumps(
                    {
                        "contract_type": "agent_repair_closure_receipt",
                        "closure_status": "blocked",
                        "actions": [
                            {
                                "action": "blocked_closure_recheck",
                                "status": "skipped",
                                "reason": "existing blocked closure is not retried automatically without successful retry evidence",
                            }
                        ],
                        "blockers": ["agent diagnosis did not report a repaired/fixed status"],
                    }
                ),
                encoding="utf-8",
            )
            calls: list[tuple[str, ...]] = []

            def fake_run(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                calls.append(tuple(argv))
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

            receipt = close_agent_repair(candidate, runner=fake_run)

        self.assertEqual(receipt["closure_status"], "closed")
        self.assertEqual(receipt["blockers"], [])
        self.assertEqual(calls, [])
        self.assertEqual(receipt["actions"][0]["action"], "no_action_needed")

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

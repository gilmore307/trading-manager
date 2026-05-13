from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.agent_error_handler import (
    build_server_error_agent_request,
    handle_server_error,
    validate_agent_error_diagnosis,
    validate_server_error_agent_request,
)
from trading_manager_tasks.control_plane import TaskSystemError


class AgentErrorHandlerTests(unittest.TestCase):
    def test_builds_server_wide_error_request_with_safety_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stderr = tmp / "failure.stderr.log"
            stderr.write_text("Traceback\nTaskSystemError: missing artifact\n", encoding="utf-8")

            request = build_server_error_agent_request(
                source_component="trading-manager.stage_executor",
                source_repo="trading-manager",
                error_scope="server.model_training_stage",
                error_kind="stage_command_failed",
                severity="error",
                summary="stage failed",
                command=["python3", "script.py"],
                exit_code=1,
                stderr_path=str(stderr),
                evidence_refs=["manager_stage:layer_03_target_state_vector.data_acquisition"],
                occurred_at_utc="2026-05-13T12:06:38Z",
            )

            normalized = validate_server_error_agent_request(request)
            self.assertEqual(normalized["contract_type"], "server_error_agent_request")
            self.assertEqual(normalized["schema_version"], "1")
            self.assertIn("TaskSystemError", normalized["stderr_excerpt"])
            self.assertTrue(any("do not submit broker orders" in item for item in normalized["forbidden_actions"]))
            self.assertIn("Error request:", normalized["agent_prompt"])

    def test_rejects_invalid_severity(self) -> None:
        with self.assertRaisesRegex(TaskSystemError, "severity"):
            build_server_error_agent_request(source_component="component", summary="bad", severity="urgent")

    def test_handle_server_error_writes_request_and_queued_diagnosis_without_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            result = handle_server_error(
                source_component="systemd.trading-manager",
                source_repo="trading-manager",
                summary="service command failed",
                command=["systemctl", "status", "service"],
                output_root=tmp,
                call_agent=False,
            )

            self.assertEqual(result["contract_type"], "agent_error_handling_result")
            request_path = Path(result["request_path"])
            diagnosis_path = Path(result["diagnosis_path"])
            self.assertTrue(request_path.exists())
            self.assertTrue(diagnosis_path.exists())
            diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_agent_error_diagnosis(diagnosis)["status"], "queued")

    def test_handle_server_error_calls_configured_runner_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            runner = tmp / "runner.py"
            runner.write_text(
                "import json, sys\n"
                "request=json.load(sys.stdin)\n"
                "print(json.dumps({'diagnosis_status':'ok','request_id':request['request_id']}))\n",
                encoding="utf-8",
            )

            result = handle_server_error(
                source_component="server.test",
                summary="failure",
                output_root=tmp / "out",
                call_agent=True,
                runner_command=f"python3 {runner}",
            )

            diagnosis = json.loads(Path(result["diagnosis_path"]).read_text(encoding="utf-8"))
            self.assertEqual(diagnosis["status"], "completed")
            self.assertIn("diagnosis_status", diagnosis["stdout"])


if __name__ == "__main__":
    unittest.main()

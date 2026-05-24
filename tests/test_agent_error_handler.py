from __future__ import annotations

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from trading_manager_tasks.agent_error_handler import (
    build_server_error_agent_request,
    handle_server_error,
    notify_discord_for_error,
    register_error_in_catalog,
    validate_agent_error_diagnosis,
    validate_server_error_catalog_entry,
    validate_server_error_agent_request,
)
from trading_manager_tasks.agent_error_agent_runner import run_codex_cli_for_error
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
            self.assertIn("server-error-diagnosis", normalized["agent_prompt"])

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
                catalog_storage="jsonl",
            )

            self.assertEqual(result["contract_type"], "agent_error_handling_result")
            request_path = Path(result["request_path"])
            diagnosis_path = Path(result["diagnosis_path"])
            self.assertTrue(request_path.exists())
            self.assertTrue(diagnosis_path.exists())
            diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_agent_error_diagnosis(diagnosis)["status"], "queued")
            self.assertEqual(diagnosis["discord_notification"]["status"], "skipped")
            self.assertEqual(result["error_ref"], "ERR-000001")
            catalog_path = tmp / "server_error_catalog.jsonl"
            rows = [json.loads(line) for line in catalog_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(validate_server_error_catalog_entry(rows[0])["error_ref"], "ERR-000001")
            request = json.loads(request_path.read_text(encoding="utf-8"))
            self.assertEqual(request["error_ref"], "ERR-000001")
            self.assertIn("Error number: ERR-000001", request["agent_prompt"])

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
                catalog_storage="jsonl",
            )

            diagnosis = json.loads(Path(result["diagnosis_path"]).read_text(encoding="utf-8"))
            self.assertEqual(diagnosis["status"], "completed")
            self.assertIn("diagnosis_status", diagnosis["stdout"])
            self.assertEqual(diagnosis["discord_notification"]["status"], "skipped")

    def test_false_autocall_env_does_not_call_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_AUTOCALL": "false", "MANAGER_AGENT_ERROR_RUNNER_COMMAND": "python3 should_not_run.py"}, clear=False):
                result = handle_server_error(
                    source_component="server.env",
                    summary="failure",
                    output_root=tmp,
                    call_agent=False,
                    catalog_storage="jsonl",
                )

            diagnosis = json.loads(Path(result["diagnosis_path"]).read_text(encoding="utf-8"))
            self.assertEqual(diagnosis["status"], "queued")
            self.assertEqual(diagnosis["stderr"], "agent call not requested")


    def test_catalog_assigns_monotonic_error_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            first = handle_server_error(source_component="server.one", summary="first", output_root=tmp, catalog_storage="jsonl")
            second = handle_server_error(source_component="server.two", summary="second", output_root=tmp, catalog_storage="jsonl")

            self.assertEqual(first["error_ref"], "ERR-000001")
            self.assertEqual(second["error_ref"], "ERR-000002")
            rows = [json.loads(line) for line in (tmp / "server_error_catalog.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["error_ref"] for row in rows], ["ERR-000001", "ERR-000002"])

    def test_catalog_uses_sql_store_by_default(self) -> None:
        request = build_server_error_agent_request(
            source_component="server.sql",
            summary="sql-backed failure",
            request_id="erragent_sql",
        )
        stored_rows: list[dict[str, object]] = []

        def fake_fetch(**_: object) -> list[dict[str, object]]:
            return list(stored_rows)

        def fake_persist(rows: list[dict[str, object]], **_: object) -> None:
            stored_rows.extend(rows)

        with tempfile.TemporaryDirectory() as raw_tmp:
            with patch("trading_manager_tasks.agent_error_handler.fetch_server_error_catalog_rows", side_effect=fake_fetch), patch(
                "trading_manager_tasks.agent_error_handler.persist_server_error_catalog_rows",
                side_effect=fake_persist,
            ):
                numbered_request, row = register_error_in_catalog(
                    request,
                    output_root=Path(raw_tmp),
                    database_url="postgresql://example/catalog",
                )

        self.assertEqual(numbered_request["error_ref"], "ERR-000001")
        self.assertEqual(numbered_request["error_catalog_path"], "trading_manager.server_error_catalog")
        self.assertEqual(row["catalog_row_id"], stored_rows[0]["catalog_row_id"])
        self.assertEqual(stored_rows[0]["contract_type"], "server_error_catalog_entry")

    def test_duplicate_errors_reuse_number_and_suppress_notification(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            first = handle_server_error(
                source_component="server.same",
                summary="repeat failure",
                command=["cmd"],
                exit_code=1,
                output_root=tmp,
                notify_discord=False,
                occurred_at_utc="2026-05-13T13:00:00Z",
                catalog_storage="jsonl",
            )
            second = handle_server_error(
                source_component="server.same",
                summary="repeat failure",
                command=["cmd"],
                exit_code=1,
                output_root=tmp,
                notify_discord=True,
                occurred_at_utc="2026-05-13T13:00:30Z",
                catalog_storage="jsonl",
            )

            self.assertEqual(first["error_ref"], "ERR-000001")
            self.assertEqual(second["error_ref"], "ERR-000001")
            self.assertTrue(second["error_deduplicated"])
            self.assertEqual(second["discord_notification"]["status"], "deduplicated")
            rows = [json.loads(line) for line in (tmp / "server_error_catalog.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["contract_type"] for row in rows], ["server_error_catalog_entry", "server_error_catalog_occurrence"])


    def test_catalog_reuses_existing_number_for_same_request_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            request = build_server_error_agent_request(
                source_component="server.test",
                summary="same failure",
                request_id="erragent_fixed",
            )
            first_request, first_row = register_error_in_catalog(request, output_root=tmp, catalog_storage="jsonl")
            second_request, second_row = register_error_in_catalog(request, output_root=tmp, catalog_storage="jsonl")

            self.assertEqual(first_request["error_ref"], "ERR-000001")
            self.assertEqual(second_request["error_ref"], "ERR-000001")
            self.assertEqual(first_row["error_ref"], second_row["error_ref"])
            self.assertEqual(len((tmp / "server_error_catalog.jsonl").read_text(encoding="utf-8").splitlines()), 1)


    def test_discord_notification_uses_openclaw_message_cli_target(self) -> None:
        request = build_server_error_agent_request(
            source_component="server.test",
            source_repo="trading-manager",
            summary="failure",
            exit_code=1,
        )
        diagnosis = {
            "contract_type": "agent_error_diagnosis",
            "schema_version": "1",
            "diagnosis_id": "errdiag_test",
            "request_ref": request["request_id"],
            "agent_ref": request["agent_ref"],
            "status": "queued",
            "completed_at_utc": "2026-05-13T12:00:00Z",
        }

        with tempfile.TemporaryDirectory() as raw_tmp:
            request, _ = register_error_in_catalog(request, output_root=Path(raw_tmp), catalog_storage="jsonl")

        with patch("trading_manager_tasks.agent_error_handler.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = "sent"
            run.return_value.stderr = ""
            result = notify_discord_for_error(request, diagnosis)

        self.assertEqual(result["status"], "sent")
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:4], ["openclaw", "message", "send", "--channel"])
        self.assertIn("discord", cmd)
        self.assertIn("channel:1504100135200620665", cmd)
        self.assertIn("--message", cmd)
        self.assertIn("Error No: ERR-000001", cmd[cmd.index("--message") + 1])
        self.assertIn("Occurred:", cmd[cmd.index("--message") + 1])
        self.assertIn("Recorded:", cmd[cmd.index("--message") + 1])
        self.assertIn("Deduplicated: no", cmd[cmd.index("--message") + 1])

    def test_codex_cli_runner_calls_repair_skill(self) -> None:
        request = build_server_error_agent_request(
            source_component="server.test",
            source_repo="trading-manager",
            summary="failure",
            request_id="erragent_test",
        )

        with patch.dict(
            "os.environ",
            {
                "MANAGER_AGENT_ERROR_CODEX_MODEL": "gpt-5.5",
                "MANAGER_AGENT_ERROR_CODEX_TIMEOUT_SECONDS": "60",
            },
            clear=False,
        ), patch("trading_manager_tasks.agent_error_agent_runner.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stdout = '{"diagnosis_status":"repaired_verified","root_cause":"fixed"}'
            run.return_value.stderr = ""
            diagnosis = run_codex_cli_for_error(request)

        self.assertEqual(diagnosis["contract_type"], "agent_error_diagnosis")
        self.assertEqual(diagnosis["status"], "completed")
        self.assertEqual(diagnosis["runner_command"], "codex_cli")
        cmd = run.call_args.args[0]
        self.assertEqual(cmd[:4], ["codex", "exec", "--ephemeral", "--ignore-rules"])
        self.assertIn("-m", cmd)
        self.assertEqual(cmd[cmd.index("-m") + 1], "gpt-5.5")
        self.assertIn("--output-last-message", cmd)
        self.assertIn("--add-dir", cmd)
        message = cmd[-1]
        self.assertIn("server-error-repair", message)
        self.assertIn("server_error_agent_request", message)
        self.assertIn("Return ONLY strict JSON", message)
        self.assertIn("provider/source calls", message)
        self.assertIn("Never mutate broker/account/order/fill/position state", message)
        self.assertIn("Never print, copy, or persist secrets", message)


if __name__ == "__main__":
    unittest.main()

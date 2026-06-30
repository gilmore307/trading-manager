from __future__ import annotations

import json
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.model_training_state import StageProgress
from trading_manager_tasks.stage_executor import (
    DEFAULT_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS,
    _cwd_for_stage,
    _resolve_command_placeholders,
    _stage_progress_worker_id,
    _stage_timeout_seconds,
    execute_stage_process,
)


class StageExecutorTests(unittest.TestCase):
    def test_executes_ready_safe_offline_stage_and_writes_receipt(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=[
                    "python3",
                    "-c",
                    "import os, pathlib; p=pathlib.Path(os.environ['TRADING_MANAGER_TASK_PROGRESS_PATH']); print('offline ok', p.exists(), os.environ['TRADING_MANAGER_TASK_PROGRESS_TASK_UID'])",
                ],
                blockers=(),
            )
            progress_root = tmp / "progress"
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_AUTOCALL": "false", "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                    progress_root=progress_root,
                    task_uid="2016-01:model_01_background_context.feature_generation",
                    worker_id="month_ingest_worker_1",
                )
            self.assertEqual(summary.contract_type, "manager_stage_execution_summary")
            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertFalse(summary.broker_execution_performed)
            self.assertTrue(Path(summary.receipt_path or "").exists())
            stdout = Path(summary.stdout_path or "").read_text(encoding="utf-8")
            self.assertIn("offline ok True 2016-01:model_01_background_context.feature_generation", stdout)
            self.assertFalse(list(progress_root.glob("*.json")))

    def test_executes_python_stage_with_manager_interpreter(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import sys; print(sys.executable)"],
                blockers=(),
            )
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_AUTOCALL": "false", "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.command[0], sys.executable)
            stdout = Path(summary.stdout_path or "").read_text(encoding="utf-8").strip()
            self.assertEqual(stdout, sys.executable)

    def test_stage_process_timeout_fails_and_writes_diagnostics(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import time; time.sleep(2)"],
                blockers=(),
            )
            with patch.dict(
                "os.environ",
                {
                    "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
                    "MANAGER_AGENT_ERROR_AUTOCALL": "false",
                    "TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "1",
                },
                clear=False,
            ):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "failed")
            self.assertIsNone(summary.return_code)
            self.assertIn("timeout_seconds=1", summary.reason or "")
            self.assertIn("timeout_seconds=1", Path(summary.stderr_path or "").read_text(encoding="utf-8"))

    def test_stage_process_stall_triggers_agent_error_before_total_timeout(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import time; time.sleep(2)"],
                blockers=(),
            )
            with patch.dict(
                "os.environ",
                {
                    "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
                    "MANAGER_AGENT_ERROR_AUTOCALL": "false",
                    "TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "5",
                    "TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS": "0.2",
                    "TRADING_MANAGER_STAGE_PROGRESS_POLL_SECONDS": "0.05",
                },
                clear=False,
            ):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "failed")
            self.assertIsNone(summary.return_code)
            self.assertIn("progress stalled", summary.reason or "")
            self.assertTrue(Path(summary.agent_error_request_path or "").exists())
            self.assertTrue(Path(summary.agent_error_diagnosis_path or "").exists())
            self.assertIn("progress stalled", Path(summary.stderr_path or "").read_text(encoding="utf-8"))

    def test_stage_process_memory_guard_stops_runaway_child(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import time; time.sleep(5)"],
                blockers=(),
            )
            with patch.dict(
                "os.environ",
                {
                    "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
                    "MANAGER_AGENT_ERROR_AUTOCALL": "false",
                    "TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "10",
                    "TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS": "10",
                    "TRADING_MANAGER_STAGE_PROGRESS_POLL_SECONDS": "0.05",
                    "TRADING_MANAGER_STAGE_MAX_RSS_MB": "64",
                    "TRADING_MANAGER_STAGE_MIN_AVAILABLE_MEMORY_MB": "0",
                },
                clear=False,
            ), patch("trading_manager_tasks.stage_executor._process_tree_rss_mb", return_value=65):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "failed")
            self.assertIsNone(summary.return_code)
            self.assertIn("memory guard", summary.reason or "")
            self.assertIn("observed_rss_mb=65", Path(summary.stderr_path or "").read_text(encoding="utf-8"))

    def test_stage_process_host_memory_guard_stops_before_machine_starves(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import time; time.sleep(5)"],
                blockers=(),
            )
            with patch.dict(
                "os.environ",
                {
                    "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
                    "MANAGER_AGENT_ERROR_AUTOCALL": "false",
                    "TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "10",
                    "TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS": "10",
                    "TRADING_MANAGER_STAGE_PROGRESS_POLL_SECONDS": "0.05",
                    "TRADING_MANAGER_STAGE_MAX_RSS_MB": "0",
                    "TRADING_MANAGER_STAGE_MIN_AVAILABLE_MEMORY_MB": "4096",
                },
                clear=False,
            ), patch("trading_manager_tasks.stage_executor._read_available_memory_mb", return_value=2048):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "failed")
            self.assertIsNone(summary.return_code)
            self.assertIn("host memory guard", summary.reason or "")
            self.assertIn("observed_available_memory_mb=2048", Path(summary.stderr_path or "").read_text(encoding="utf-8"))

    def test_long_database_feature_generation_uses_total_timeout_not_progress_stall(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            for stage_id, layer, layer_key in (
                ("model_02_target_state.feature_generation", 2, "model_02_target_state"),
                ("model_05_option_expression.feature_generation", 5, "model_05_option_expression"),
            ):
                stage = StageProgress(
                    stage_id=stage_id,
                    layer=layer,
                    layer_key=layer_key,
                    stage_type="feature_generation",
                    status="ready",
                    command=["python3", "-c", "import time; time.sleep(0.4); print('long sql complete')"],
                    blockers=(),
                )
                with patch.dict(
                    "os.environ",
                    {
                        "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
                        "MANAGER_AGENT_ERROR_AUTOCALL": "false",
                        "TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "5",
                        "TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS": "0.1",
                        "TRADING_MANAGER_STAGE_PROGRESS_POLL_SECONDS": "0.05",
                    },
                    clear=False,
                ):
                    summary = execute_stage_process(
                        stage,
                        manager_root=tmp,
                        trading_data_root=tmp,
                        trading_model_root=tmp,
                        receipt_root=tmp / "receipts",
                        log_root=tmp / "logs",
                    )

                self.assertEqual(summary.status, "succeeded")
                self.assertEqual(summary.return_code, 0)
                self.assertIn("long sql complete", Path(summary.stdout_path or "").read_text(encoding="utf-8"))

    def test_long_database_feature_generation_uses_dedicated_timeout(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_02_target_state.feature_generation",
                layer=2,
                layer_key="model_02_target_state",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import time; time.sleep(0.3); print('dedicated timeout complete')"],
                blockers=(),
            )
            with patch.dict(
                "os.environ",
                {
                    "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
                    "MANAGER_AGENT_ERROR_AUTOCALL": "false",
                    "TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "0",
                    "TRADING_MANAGER_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS": "2",
                    "TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS": "0.1",
                    "TRADING_MANAGER_STAGE_PROGRESS_POLL_SECONDS": "0.05",
                },
                clear=False,
            ):
                self.assertEqual(_stage_timeout_seconds(stage), 2)
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.return_code, 0)
            self.assertIn("dedicated timeout complete", Path(summary.stdout_path or "").read_text(encoding="utf-8"))

    def test_long_database_feature_generation_default_timeout_exceeds_global_stage_timeout(self):
        stage = StageProgress(
            stage_id="model_02_target_state.feature_generation",
            layer=2,
            layer_key="model_02_target_state",
            stage_type="feature_generation",
            status="ready",
            command=["python3", "-c", "print('ok')"],
            blockers=(),
        )
        with patch.dict("os.environ", {"TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "1800"}, clear=True):
            self.assertEqual(_stage_timeout_seconds(stage), DEFAULT_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS)
        with patch.dict("os.environ", {"TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS": "18000"}, clear=True):
            self.assertEqual(_stage_timeout_seconds(stage), 18000)

    def test_long_database_feature_generation_default_timeout_covers_fold_scope(self):
        self.assertEqual(DEFAULT_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS, 60 * 60 * 4)

    def test_stage_process_retries_once_after_completed_agent_repair(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            marker = tmp / "first_failed"
            diagnosis_path = tmp / "agent" / "agent_error_diagnosis.json"
            request_path = tmp / "agent" / "server_error_agent_request.json"
            command = (
                "import pathlib, sys; "
                f"marker=pathlib.Path({str(marker)!r}); "
                "print('retry ok') if marker.exists() else (marker.write_text('1'), sys.exit(1))"
            )
            stage = StageProgress(
                stage_id="model_01_background_context.feature_generation",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", command],
                blockers=(),
            )

            def fake_handle_server_error(**_: object) -> dict[str, object]:
                diagnosis_path.parent.mkdir(parents=True, exist_ok=True)
                diagnosis_path.write_text(
                    json.dumps(
                        {
                            "contract_type": "agent_error_diagnosis",
                            "schema_version": "1",
                            "diagnosis_id": "errdiag_test",
                            "request_ref": "erragent_test",
                            "agent_ref": "codex_cli_gpt_5_5",
                            "runner_command": "codex_cli",
                            "status": "completed",
                            "return_code": 0,
                            "stdout": json.dumps(
                                {
                                    "diagnosis_status": "repaired_verified",
                                    "retry_recommendation": "retry_original_stage",
                                }
                            ),
                            "stderr": "",
                            "started_at_utc": "2026-06-08T00:00:00Z",
                            "completed_at_utc": "2026-06-08T00:01:00Z",
                        }
                    ),
                    encoding="utf-8",
                )
                request_path.write_text("{}", encoding="utf-8")
                return {
                    "request_path": str(request_path),
                    "diagnosis_path": str(diagnosis_path),
                    "error_number": 99,
                    "error_ref": "ERR-000099",
                }

            with patch("trading_manager_tasks.stage_executor.handle_server_error", side_effect=fake_handle_server_error) as error_mock:
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )

            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.reason, "stage completed after automatic repair retry")
            self.assertEqual(summary.agent_error_ref, "ERR-000099")
            self.assertIn("retry ok", Path(summary.stdout_path or "").read_text(encoding="utf-8"))
            self.assertEqual(error_mock.call_count, 1)

    def test_resolves_runtime_month_placeholders_before_execution(self):
        command = _resolve_command_placeholders(["runner", "--month", "${START_MONTH}", "--path", "summary_${END_MONTH}.json"], start_month="2016-01", end_month="2016-02")

        self.assertEqual(command, ["runner", "--month", "2016-01", "--path", "summary_2016-02.json"])

    def test_rejects_deprecated_runtime_model_rows_output(self):
        stage = StageProgress(
            stage_id="model_03_event_state.model_generation.train",
            layer=4,
            layer_key="model_03_event_state",
            stage_type="model_generation",
            status="ready",
            command=[
                "python3",
                "/root/projects/trading-model/scripts/models/model_04_event_failure_risk/generate_model_04_event_failure_risk.py",
                "--from-database",
                "--output-jsonl",
                "/root/projects/trading-storage/storage/03_model_artifacts/runtime/model_04_event_failure_risk/model_rows_aapl_2016-01_train.jsonl",
            ],
            blockers=(),
        )

        with self.assertRaisesRegex(TaskSystemError, "deprecated runtime model_rows"):
            execute_stage_process(stage, manager_root=Path("/manager"), trading_data_root=Path("/data"), trading_model_root=Path("/model"))

    def test_stage_progress_worker_id_is_unique_for_month_scoped_execution(self):
        self.assertEqual(
            _stage_progress_worker_id(start_month="2016-01", end_month="2016-01"),
            "month_ingest_worker_stage_executor_2016_01",
        )
        self.assertEqual(_stage_progress_worker_id(start_month="2016-01", end_month="2016-06"), "model_worker_1")

    def test_manager_task_scripts_run_from_manager_root_even_with_trading_model_refs(self):
        stage = StageProgress(
            stage_id="model_01_market_context.maintenance",
            layer=1,
            layer_key="model_01_market_context",
            stage_type="maintenance",
            status="ready",
            command=["PYTHONPATH=src", "python3", "scripts/tasks/plan_model_promotion_review.py", "--candidate-ref", "storage://trading-model/example.json"],
            blockers=(),
        )

        cwd = _cwd_for_stage(stage, manager_root=Path("/manager"), trading_data_root=Path("/data"), trading_model_root=Path("/model"))

        self.assertEqual(cwd, Path("/manager"))

    def test_executes_approved_local_data_acquisition_command(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_02_target_state.data_acquisition",
                layer=3,
                layer_key="model_02_target_state",
                stage_type="data_acquisition",
                status="ready",
                command=["python3", "materialize_layer_three_target_state_inputs.py"],
                blockers=(),
            )
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_AUTOCALL": "false", "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )
            self.assertEqual(summary.status, "failed")
            self.assertEqual(summary.provider_calls, 0)
            self.assertTrue(Path(summary.agent_error_request_path or "").exists())
            self.assertTrue(Path(summary.agent_error_diagnosis_path or "").exists())

    def test_executes_approved_layer_four_event_observation_local_data_acquisition_command(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="model_03_event_state.data_acquisition",
                layer=4,
                layer_key="model_03_event_state",
                stage_type="data_acquisition",
                status="ready",
                command=["python3", "materialize_layer_four_event_observation_inputs.py"],
                blockers=(),
            )
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_AUTOCALL": "false", "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                )
            self.assertEqual(summary.status, "failed")
            self.assertEqual(summary.provider_calls, 0)

    def test_refuses_provider_dispatch_data_acquisition_command(self):
        for script in ("dispatch_and_reconcile_provider_stage.py", "dispatch_event_feed_backfill.py"):
            stage = StageProgress(
                stage_id="model_01_background_context.data_acquisition",
                layer=1,
                layer_key="model_01_market_context",
                stage_type="data_acquisition",
                status="ready",
                command=["python3", f"scripts/tasks/{script}"],
                blockers=(),
            )
            with self.subTest(script=script):
                with self.assertRaises(TaskSystemError):
                    execute_stage_process(stage)

    def test_refuses_option_chain_source_preparation_as_safe_offline_stage(self):
        stage = StageProgress(
            stage_id="model_05_option_expression.option_chain_data_acquisition",
            layer=3,
            layer_key="model_02_target_state",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "scripts/tasks/prepare_option_chain_source_acquisition.py", "--write", "--persist-sql"],
            blockers=(),
        )

        with self.assertRaisesRegex(TaskSystemError, "not an allowed materialization/review command"):
            execute_stage_process(stage)

    def test_refuses_unapproved_local_data_acquisition_command(self):
        stage = StageProgress(
            stage_id="model_02_target_state.data_acquisition",
            layer=3,
            layer_key="model_02_target_state",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "-c", "print('not approved')"],
            blockers=(),
        )
        with self.assertRaises(TaskSystemError):
            execute_stage_process(stage)

    def test_refuses_approval_gated_stage(self):
        stage = StageProgress(
            stage_id="model_01_background_context.data_acquisition",
            layer=1,
            layer_key="model_01_market_context",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "-c", "print('no')"],
            blockers=("manual_provider_gate",),
            approval_gate_required="manual_provider_gate",
        )
        with self.assertRaises(TaskSystemError):
            execute_stage_process(stage)


if __name__ == "__main__":
    unittest.main()

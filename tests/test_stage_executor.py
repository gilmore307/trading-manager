from __future__ import annotations

import json
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.model_training_state import StageProgress
from trading_manager_tasks.stage_executor import _cwd_for_stage, _resolve_command_placeholders, _stage_progress_worker_id, execute_stage_process


class StageExecutorTests(unittest.TestCase):
    def test_executes_ready_safe_offline_stage_and_writes_receipt(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="layer_01_market_regime.feature_generation",
                layer=1,
                layer_key="layer_01_market_regime",
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
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
                summary = execute_stage_process(
                    stage,
                    manager_root=tmp,
                    trading_data_root=tmp,
                    trading_model_root=tmp,
                    receipt_root=tmp / "receipts",
                    log_root=tmp / "logs",
                    progress_root=progress_root,
                    task_uid="2016-01:layer_01_market_regime.feature_generation",
                    worker_id="month_ingest_worker_1",
                )
            self.assertEqual(summary.contract_type, "manager_stage_execution_summary")
            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertFalse(summary.broker_execution_performed)
            self.assertTrue(Path(summary.receipt_path or "").exists())
            stdout = Path(summary.stdout_path or "").read_text(encoding="utf-8")
            self.assertIn("offline ok True 2016-01:layer_01_market_regime.feature_generation", stdout)
            self.assertFalse(list(progress_root.glob("*.json")))

    def test_executes_python_stage_with_manager_interpreter(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="layer_01_market_regime.feature_generation",
                layer=1,
                layer_key="layer_01_market_regime",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import sys; print(sys.executable)"],
                blockers=(),
            )
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
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
                stage_id="layer_01_market_regime.feature_generation",
                layer=1,
                layer_key="layer_01_market_regime",
                stage_type="feature_generation",
                status="ready",
                command=["python3", "-c", "import time; time.sleep(2)"],
                blockers=(),
            )
            with patch.dict(
                "os.environ",
                {
                    "MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl",
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
                stage_id="layer_01_market_regime.feature_generation",
                layer=1,
                layer_key="layer_01_market_regime",
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
            stage_id="layer_04_event_failure_risk.model_generation.train",
            layer=4,
            layer_key="layer_04_event_failure_risk",
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
            stage_id="layer_01_market_regime.maintenance",
            layer=1,
            layer_key="layer_01_market_regime",
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
                stage_id="layer_03_target_state_vector.data_acquisition",
                layer=3,
                layer_key="layer_03_target_state_vector",
                stage_type="data_acquisition",
                status="ready",
                command=["python3", "materialize_layer_three_target_state_inputs.py"],
                blockers=(),
            )
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
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
                stage_id="layer_04_event_failure_risk.data_acquisition",
                layer=4,
                layer_key="layer_04_event_failure_risk",
                stage_type="data_acquisition",
                status="ready",
                command=["python3", "materialize_layer_four_event_observation_inputs.py"],
                blockers=(),
            )
            with patch.dict("os.environ", {"MANAGER_AGENT_ERROR_CATALOG_STORAGE": "jsonl"}, clear=False):
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
                stage_id="layer_01_market_regime.data_acquisition",
                layer=1,
                layer_key="layer_01_market_regime",
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
            stage_id="layer_03_target_state_vector.option_chain_data_acquisition",
            layer=3,
            layer_key="layer_03_target_state_vector",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "scripts/tasks/prepare_option_chain_source_acquisition.py", "--write", "--persist-sql"],
            blockers=(),
        )

        with self.assertRaisesRegex(TaskSystemError, "not an allowed materialization/review command"):
            execute_stage_process(stage)

    def test_refuses_unapproved_local_data_acquisition_command(self):
        stage = StageProgress(
            stage_id="layer_03_target_state_vector.data_acquisition",
            layer=3,
            layer_key="layer_03_target_state_vector",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "-c", "print('not approved')"],
            blockers=(),
        )
        with self.assertRaises(TaskSystemError):
            execute_stage_process(stage)

    def test_refuses_approval_gated_stage(self):
        stage = StageProgress(
            stage_id="layer_01_market_regime.data_acquisition",
            layer=1,
            layer_key="layer_01_market_regime",
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

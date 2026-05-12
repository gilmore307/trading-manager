from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.model_training_state import StageProgress
from trading_manager_tasks.stage_executor import _cwd_for_stage, _resolve_command_placeholders, execute_stage_process


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
                command=["python3", "-c", "print('offline ok')"],
                blockers=(),
            )
            summary = execute_stage_process(
                stage,
                manager_root=tmp,
                trading_data_root=tmp,
                trading_model_root=tmp,
                receipt_root=tmp / "receipts",
                log_root=tmp / "logs",
            )
            self.assertEqual(summary.contract_type, "manager_stage_execution_summary")
            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertFalse(summary.broker_execution_performed)
            self.assertTrue(Path(summary.receipt_path or "").exists())
            self.assertIn("offline ok", Path(summary.stdout_path or "").read_text(encoding="utf-8"))


    def test_resolves_runtime_month_placeholders_before_execution(self):
        command = _resolve_command_placeholders(["runner", "--month", "${START_MONTH}", "--path", "summary_${END_MONTH}.json"], start_month="2016-01", end_month="2016-02")

        self.assertEqual(command, ["runner", "--month", "2016-01", "--path", "summary_2016-02.json"])

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

    def test_executes_approved_layer_four_local_data_acquisition_command(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            stage = StageProgress(
                stage_id="layer_04_event_overlay.data_acquisition",
                layer=4,
                layer_key="layer_04_event_overlay",
                stage_type="data_acquisition",
                status="ready",
                command=["python3", "materialize_layer_four_event_overlay_inputs.py"],
                blockers=(),
            )
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
        stage = StageProgress(
            stage_id="layer_01_market_regime.data_acquisition",
            layer=1,
            layer_key="layer_01_market_regime",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "scripts/tasks/dispatch_and_reconcile_provider_stage.py"],
            blockers=(),
        )
        with self.assertRaises(TaskSystemError):
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

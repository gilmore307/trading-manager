from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.model_training_state import StageProgress
from trading_manager_tasks.stage_executor import execute_stage_process


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
            self.assertEqual(summary.contract_type, "manager_stage_execution_summary_v1")
            self.assertEqual(summary.status, "succeeded")
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertFalse(summary.broker_execution_performed)
            self.assertTrue(Path(summary.receipt_path or "").exists())
            self.assertIn("offline ok", Path(summary.stdout_path or "").read_text(encoding="utf-8"))

    def test_refuses_approval_gated_stage(self):
        stage = StageProgress(
            stage_id="layer_01_market_regime.data_acquisition",
            layer=1,
            layer_key="layer_01_market_regime",
            stage_type="data_acquisition",
            status="ready",
            command=["python3", "-c", "print('no')"],
            blockers=("live_call_approval_v1",),
            approval_gate_required="live_call_approval_v1",
        )
        with self.assertRaises(TaskSystemError):
            execute_stage_process(stage)


if __name__ == "__main__":
    unittest.main()

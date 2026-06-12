from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.model_group_replay_contract_paths import (
    replay_contract_path_requirements_from_decision_rows,
    run_model_group_replay_contract_paths,
)


class ModelGroupReplayContractPathsTests(unittest.TestCase):
    def _write_decision_rows(self, path: Path) -> None:
        rows = [
            {
                "decision_id": "ed_1",
                "target_ref": "AAPL",
                "selected_option_contract_ref": "AAPL_2021-07-09_C_142",
                "option_contract_path_status": "missing",
                "replay_time_pointer": "2021-07-06T16:00:00-04:00",
                "next_timestamp": "2021-07-07T16:00:00-04:00",
            },
            {
                "decision_id": "ed_2",
                "target_ref": "AAPL",
                "selected_option_contract_ref": "AAPL_2021-07-09_C_142",
                "option_contract_path_status": "missing",
                "replay_time_pointer": "2021-07-06T16:00:00-04:00",
                "next_timestamp": "2021-07-07T16:00:00-04:00",
            },
            {
                "decision_id": "ed_3",
                "target_ref": "AAPL",
                "selected_option_contract_ref": "AAPL_2021-07-09_P_140",
                "option_contract_path_status": "available",
                "replay_time_pointer": "2021-07-06T16:00:00-04:00",
                "next_timestamp": "2021-07-07T16:00:00-04:00",
            },
        ]
        path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")

    def test_extracts_missing_selected_contract_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            decision_rows = Path(raw_tmp) / "decision_rows.jsonl"
            self._write_decision_rows(decision_rows)

            requirements = replay_contract_path_requirements_from_decision_rows(decision_rows)

        self.assertEqual(len(requirements), 1)
        requirement = requirements[0]
        self.assertEqual(requirement.underlying, "AAPL")
        self.assertEqual(requirement.option_symbol, "AAPL_2021-07-09_C_142")
        self.assertEqual(requirement.expiration, "2021-07-09")
        self.assertEqual(requirement.option_right_type, "CALL")
        self.assertEqual(requirement.strike, 142.0)
        self.assertEqual(requirement.entry_time, "2021-07-06T16:00:00-04:00")
        self.assertEqual(requirement.exit_time, "2021-07-07T16:00:00-04:00")

    def test_execute_without_provider_writes_task_key_and_backs_off(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            decision_rows = root / "decision_rows.jsonl"
            storage_root = root / "storage" / "02_control_plane"
            self._write_decision_rows(decision_rows)

            decision = run_model_group_replay_contract_paths(
                decision_rows_ref=decision_rows,
                storage_root=storage_root,
                execute=True,
                execute_provider_acquisition=False,
            )

            summary = decision.execution_summary or {}
            task_key_path = Path(str(summary["task_key_path"]))
            task_key = json.loads(task_key_path.read_text(encoding="utf-8"))

        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "model_group_replay_contract_path_provider_required")
        self.assertEqual(decision.provider_calls, 0)
        self.assertEqual(task_key["source"], "m05_option_expression_data_acquisition_contract_path")
        self.assertEqual(len(task_key["params"]["selected_contracts"]), 1)
        self.assertTrue(task_key["manager_controls"]["allow_live_provider_calls"])
        self.assertTrue(task_key["manager_controls"]["autonomous_historical_provider_acquisition"])
        self.assertEqual(task_key["manager_controls"]["allowed_endpoint_families"], ["option_primary_tracking"])
        self.assertFalse(task_key["manager_controls"]["broker_execution_performed"])
        self.assertFalse(task_key["manager_controls"]["model_activation_performed"])

    def test_execute_provider_runs_trading_data_source(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            decision_rows = root / "decision_rows.jsonl"
            storage_root = root / "storage" / "02_control_plane"
            self._write_decision_rows(decision_rows)

            with patch("trading_manager_tasks.model_group_replay_contract_paths.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = '{"status": "succeeded"}'
                run.return_value.stderr = ""
                decision = run_model_group_replay_contract_paths(
                    decision_rows_ref=decision_rows,
                    storage_root=storage_root,
                    execute=True,
                    execute_provider_acquisition=True,
                )

        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "model_group_replay_contract_paths_executed")
        self.assertEqual(decision.provider_calls, 1)
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()

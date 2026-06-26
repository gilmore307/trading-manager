from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from trading_manager_tasks.option_chain_source_acquisition import (
    DEFAULT_PYTHON_EXECUTABLE,
    _runtime_task_key,
    _provider_python_executable,
    build_option_chain_source_review,
    dispatch_option_chain_source_acquisition,
    is_current_option_chain_request,
    manager_requests_from_review,
    request_previews_for_replay_decision_times,
    request_previews_for_fold,
)


class OptionChainSourceAcquisitionTests(unittest.TestCase):
    def test_prepares_regular_session_day_windows_before_layer_three(self) -> None:
        previews = request_previews_for_fold(start_month="2016-01", end_month="2016-01", target_symbol="AAPL")

        self.assertEqual(len(previews), 19)
        self.assertEqual(previews[0].request_id, "mgrreq_option_chain_window_aapl_2016_01_2016_01_04_0930")
        self.assertEqual(previews[0].snapshot_time, "2016-01-04T09:30:00-05:00")
        self.assertEqual(previews[0].window_start, "2016-01-04T09:30:00-05:00")
        self.assertEqual(previews[0].window_end, "2016-01-04T16:00:00-05:00")
        self.assertEqual(previews[0].max_dte, 180)
        self.assertEqual(previews[0].strike_range, 5)
        self.assertEqual(previews[-1].request_id, "mgrreq_option_chain_window_aapl_2016_01_2016_01_29_0930")
        self.assertEqual(previews[-1].window_end, "2016-01-29T16:00:00-05:00")

    def test_preparation_excludes_ad_hoc_us_equity_closures(self) -> None:
        previews = request_previews_for_fold(start_month="2018-12", end_month="2018-12", target_symbol="AAPL")

        request_ids = {preview.request_id for preview in previews}
        self.assertNotIn("mgrreq_option_chain_window_aapl_2018_12_2018_12_05_0930", request_ids)

    def test_manager_controls_use_provider_supported_time_window(self) -> None:
        review = build_option_chain_source_review(start_month="2016-01", end_month="2016-01", target_symbol="AAPL")
        request = manager_requests_from_review(review)[0]

        self.assertEqual(request["_task_key"]["manager_controls"]["max_time_window"], "1d")
        self.assertEqual(request["_task_key"]["manager_controls"]["rate_limit_policy_ref"], "thetadata_terminal_rest_account_concurrency")
        self.assertEqual(request["_task_key"]["params"]["thetadata_transport"], "terminal_rest_selected_contracts")
        self.assertEqual(request["_task_key"]["params"]["terminal_rest_exact_max_workers"], 1)
        self.assertEqual(request["_task_key"]["params"]["max_dte"], 180)
        self.assertEqual(request["_task_key"]["params"]["strike_range"], 5)

    def test_runtime_task_key_repairs_stale_time_window_controls(self) -> None:
        task_key = {
            "manager_controls": {
                "allow_live_provider_calls": True,
                "autonomous_historical_provider_acquisition": True,
                "max_time_window": "30m",
            },
            "params": {},
        }

        runtime_key = _runtime_task_key(task_key)

        self.assertEqual(runtime_key["manager_controls"]["max_time_window"], "1d")
        self.assertEqual(runtime_key["manager_controls"]["rate_limit_policy_ref"], "thetadata_terminal_rest_account_concurrency")
        self.assertEqual(runtime_key["params"]["thetadata_transport"], "terminal_rest_selected_contracts")
        self.assertEqual(runtime_key["params"]["terminal_rest_exact_max_workers"], 1)

    def test_provider_command_uses_project_virtualenv_when_available(self) -> None:
        if DEFAULT_PYTHON_EXECUTABLE.exists():
            self.assertEqual(_provider_python_executable(), str(DEFAULT_PYTHON_EXECUTABLE))
        else:
            self.assertTrue(_provider_python_executable())

    def test_current_request_matching_uses_fold_start_month_not_end_month(self) -> None:
        current = {
            "request_id": "mgrreq_option_chain_window_aapl_2021_01_2021_06_01_0930",
            "request_kind": "option_chain_snapshot",
            "target_component_id": "option_chain_state_source",
            "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-01/mgrreq_option_chain_window_aapl_2021_01_2021_06_01_0930/task_key.json",
        }
        stale_end_month = {
            **current,
            "request_id": "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700",
            "parameter_ref": "storage://trading-manager/runtime/model_02_target_state/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700/task_key.json",
        }

        self.assertTrue(is_current_option_chain_request(current, start_month="2021-01", end_month="2021-06"))
        self.assertFalse(is_current_option_chain_request(stale_end_month, start_month="2021-01", end_month="2021-06"))

    def test_current_request_matching_excludes_intraday_or_after_close_windows(self) -> None:
        current = {
            "request_id": "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_0930",
            "request_kind": "option_chain_snapshot",
            "target_component_id": "option_chain_state_source",
            "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_0930/task_key.json",
        }
        stale_intraday = {
            **current,
            "request_id": "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1600",
            "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1600/task_key.json",
        }
        stale_after_close = {
            **current,
            "request_id": "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700",
            "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700/task_key.json",
        }

        self.assertTrue(is_current_option_chain_request(current, start_month="2021-01", end_month="2021-06"))
        self.assertFalse(is_current_option_chain_request(stale_intraday, start_month="2021-01", end_month="2021-06"))
        self.assertFalse(is_current_option_chain_request(stale_after_close, start_month="2021-01", end_month="2021-06"))

    def test_replay_decision_requests_same_row_asof_window(self) -> None:
        previews = request_previews_for_replay_decision_times(
            target_symbol="AAPL",
            decision_timestamps=["2021-01-04T16:00:00-05:00"],
        )

        self.assertEqual(len(previews), 1)
        self.assertEqual(previews[0].request_id, "mgrreq_replay_option_chain_window_aapl_2021_01_2021_01_04_1600")
        self.assertEqual(previews[0].snapshot_time, "2021-01-04T16:00:00-05:00")
        self.assertEqual(previews[0].window_start, "2021-01-04T15:59:00-05:00")
        self.assertEqual(previews[0].window_end, "2021-01-04T16:00:00-05:00")

    def test_replay_decision_request_matching_allows_replay_intraday_window(self) -> None:
        replay = {
            "request_id": "mgrreq_replay_option_chain_window_aapl_2021_06_2021_06_01_1600",
            "request_kind": "option_chain_snapshot",
            "target_component_id": "option_chain_state_source",
            "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-06/mgrreq_replay_option_chain_window_aapl_2021_06_2021_06_01_1600/task_key.json",
        }

        self.assertTrue(is_current_option_chain_request(replay, start_month="2021-06", end_month="2021-06"))

    def test_execute_dispatch_can_use_multiple_option_chain_workers(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            storage_root = Path(raw_tmp) / "storage"
            task_root = storage_root / "runtime" / "model_05_option_expression" / "option_chain_state_source" / "2021-03"
            rows = []
            for index, symbol in enumerate(("AAPL", "MSFT", "NVDA", "AMD"), start=1):
                request_id = f"mgrreq_replay_option_chain_window_{symbol.lower()}_2021_03_2021_03_11_1600"
                task_path = task_root / request_id / "task_key.json"
                task_path.parent.mkdir(parents=True, exist_ok=True)
                task_path.write_text(
                    json.dumps({"output_root": str(task_path.parent / "runs" / f"run_{index}"), "params": {}}),
                    encoding="utf-8",
                )
                rows.append(
                    {
                        "request_id": request_id,
                        "parameter_ref": "storage://trading-manager/" + str(task_path.relative_to(storage_root)),
                    }
                )

            with (
                patch("trading_manager_tasks.option_chain_source_acquisition.request_rows", return_value=rows),
                patch(
                    "trading_manager_tasks.option_chain_source_acquisition.subprocess.run",
                    return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
                ) as run_mock,
            ):
                dispatch = dispatch_option_chain_source_acquisition(
                    start_month="2021-03",
                    end_month="2021-03",
                    storage_root=storage_root,
                    trading_data_root=Path(raw_tmp),
                    execute_provider_calls=True,
                    dynamic_workers=False,
                    max_workers=4,
                )

        self.assertEqual(dispatch.worker_selection.selected_worker_count, 4)
        self.assertEqual(dispatch.dispatch_count, 4)
        self.assertEqual(run_mock.call_count, 4)
        self.assertEqual({item.worker_slot for item in dispatch.items}, {1, 2, 3, 4})


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

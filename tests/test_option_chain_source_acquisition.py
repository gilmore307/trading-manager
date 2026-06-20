from __future__ import annotations

import unittest

from trading_manager_tasks.option_chain_source_acquisition import (
    _runtime_task_key,
    build_option_chain_source_review,
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
        self.assertEqual(request["_task_key"]["manager_controls"]["rate_limit_policy_ref"], "thetadata_python_library_serial_session")
        self.assertEqual(request["_task_key"]["params"]["thetadata_transport"], "python_library")
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
        self.assertEqual(runtime_key["manager_controls"]["rate_limit_policy_ref"], "thetadata_python_library_serial_session")
        self.assertEqual(runtime_key["params"]["thetadata_transport"], "python_library")

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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

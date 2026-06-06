from __future__ import annotations

import unittest

from trading_manager_tasks.option_chain_source_acquisition import request_previews_for_fold


class OptionChainSourceAcquisitionTests(unittest.TestCase):
    def test_prepares_regular_session_thirty_minute_windows_before_layer_three(self) -> None:
        previews = request_previews_for_fold(start_month="2016-01", end_month="2016-01", target_symbol="AAPL")

        self.assertEqual(len(previews), 247)
        self.assertEqual(previews[0].request_id, "mgrreq_option_chain_window_aapl_2016_01_2016_01_04_0930")
        self.assertEqual(previews[0].snapshot_time, "2016-01-04T09:30:00-05:00")
        self.assertEqual(previews[0].window_start, "2016-01-04T09:30:00-05:00")
        self.assertEqual(previews[0].window_end, "2016-01-04T10:00:00-05:00")
        self.assertEqual(previews[-1].request_id, "mgrreq_option_chain_window_aapl_2016_01_2016_01_29_1530")
        self.assertEqual(previews[-1].window_end, "2016-01-29T16:00:00-05:00")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

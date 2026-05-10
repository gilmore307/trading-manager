from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_state import advance_workflow_state
from trading_manager_tasks.stage_coverage import summarize_stage_coverage_from_rows


def _summary_row(symbol: str, *, ready: bool = False, failed: bool = False) -> dict[str, object]:
    request_id = f"mgrreq_backfill_alpaca_bars_{symbol.lower()}_2016_01"
    if failed:
        return {
            "request_id": request_id,
            "request_kind": "data_backfill_month_v1",
            "target_component_id": "01_feed_alpaca_bars",
            "parameter_ref": f"storage://trading-manager/monthly_backfill_v1/alpaca_bars/{symbol}/2016-01/task_key.json",
            "expected_outputs": [f"storage://trading-data/monthly_backfill_v1/alpaca_bars/{symbol}/2016-01/"],
            "task_status": "failed",
            "latest_run_status": "failed",
            "latest_ready_signal_status": None,
        }
    return {
        "request_id": request_id,
        "request_kind": "data_backfill_month_v1",
        "target_component_id": "01_feed_alpaca_bars",
        "parameter_ref": f"storage://trading-manager/monthly_backfill_v1/alpaca_bars/{symbol}/2016-01/task_key.json",
        "expected_outputs": [f"storage://trading-data/monthly_backfill_v1/alpaca_bars/{symbol}/2016-01/"],
        "task_status": "ready" if ready else "requested",
        "latest_run_status": "succeeded" if ready else None,
        "latest_ready_signal_status": "ready" if ready else None,
    }


class StageCoverageTests(unittest.TestCase):
    def test_three_ready_of_twenty_two_is_partial_and_cannot_unlock(self):
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in ("QQQ", "SPY", "TLT")],
            *[_summary_row(f"SYM{index:02d}") for index in range(19)],
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_01_market_regime.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=22,
        )

        self.assertEqual(report.status, "partial_ready")
        self.assertEqual(report.ready_count, 3)
        self.assertEqual(report.pending_count, 19)
        self.assertFalse(report.can_unlock_downstream)
        self.assertIn("3/22", report.reason)

    def test_full_coverage_can_unlock_downstream(self):
        rows = [_summary_row(f"SYM{index:02d}", ready=True) for index in range(22)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_01_market_regime.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=22,
        )

        self.assertEqual(report.status, "ready")
        self.assertEqual(report.ready_count, 22)
        self.assertTrue(report.can_unlock_downstream)

    def test_failed_coverage_blocks_downstream_unlock(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("QQQ", failed=True)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_01_market_regime.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=2,
        )

        self.assertEqual(report.status, "failed")
        self.assertEqual(report.ready_count, 1)
        self.assertEqual(report.failed_count, 1)
        self.assertFalse(report.can_unlock_downstream)

    def test_partial_coverage_report_does_not_complete_workflow_stage(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            for index in range(22):
                task_key = storage / "monthly_backfill_v1" / "alpaca_bars" / f"SYM{index:02d}" / "2016-01" / "task_key.json"
                task_key.parent.mkdir(parents=True)
                task_key.write_text("{}\n", encoding="utf-8")
            report_path = tmp / "coverage.json"
            report_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage_v1",
                        "stage_id": "layer_01_market_regime.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "expected_count": 22,
                        "observed_count": 22,
                        "ready_count": 3,
                        "failed_count": 0,
                        "pending_count": 19,
                        "status": "partial_ready",
                        "can_unlock_downstream": False,
                        "ready_request_ids": ["mgrreq_backfill_alpaca_bars_spy_2016_01"],
                        "failed_request_ids": [],
                        "pending_request_ids": [],
                        "reason": "stage coverage partial 3/22; downstream remains blocked",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=tmp / "workflow_state.json",
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["layer_01_market_regime.data_acquisition"].status, "ready")
            self.assertIn("3/22", stages["layer_01_market_regime.data_acquisition"].last_reason or "")
            self.assertEqual(stages["layer_01_market_regime.feature_generation"].status, "blocked")

    def test_complete_coverage_report_completes_stage_and_unlocks_feature_generation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            for index in range(22):
                task_key = storage / "monthly_backfill_v1" / "alpaca_bars" / f"SYM{index:02d}" / "2016-01" / "task_key.json"
                task_key.parent.mkdir(parents=True)
                task_key.write_text("{}\n", encoding="utf-8")
            report_path = tmp / "coverage.json"
            report_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage_v1",
                        "stage_id": "layer_01_market_regime.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "expected_count": 22,
                        "observed_count": 22,
                        "ready_count": 22,
                        "failed_count": 0,
                        "pending_count": 0,
                        "status": "ready",
                        "can_unlock_downstream": True,
                        "ready_request_ids": [],
                        "failed_request_ids": [],
                        "pending_request_ids": [],
                        "reason": "stage coverage complete 22/22; downstream may unlock",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            state = advance_workflow_state(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=storage,
                state_path=tmp / "workflow_state.json",
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["layer_01_market_regime.data_acquisition"].status, "succeeded")
            self.assertEqual(stages["layer_01_market_regime.feature_generation"].status, "ready")


if __name__ == "__main__":
    unittest.main()

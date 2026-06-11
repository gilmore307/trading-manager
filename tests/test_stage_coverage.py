from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_state import advance_workflow_state
from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe
from trading_manager_tasks.stage_coverage import summarize_stage_coverage_from_rows


def _write_task_keys(root: Path, *, model_layer: str, month: str = "2016-01") -> None:
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        task_key = root / "monthly_backfill" / "alpaca_bars" / member.symbol / month / "task_key.json"
        task_key.parent.mkdir(parents=True, exist_ok=True)
        task_key.write_text("{}\n", encoding="utf-8")


def _symbols(model_layer: str) -> list[str]:
    return [member.symbol for member in load_market_regime_universe(model_layers=(model_layer,))]


def _summary_row(symbol: str, *, ready: bool = False, failed: bool = False) -> dict[str, object]:
    request_id = f"mgrreq_backfill_alpaca_bars_{symbol.lower()}_2016_01"
    if failed:
        return {
            "request_id": request_id,
            "request_kind": "data_backfill_month",
            "target_component_id": "01_feed_alpaca_bars",
            "parameter_ref": f"storage://trading-manager/monthly_backfill/alpaca_bars/{symbol}/2016-01/task_key.json",
            "expected_outputs": [f"storage://trading-data/monthly_backfill/alpaca_bars/{symbol}/2016-01/"],
            "task_status": "failed",
            "latest_run_status": "failed",
            "latest_ready_signal_status": None,
        }
    return {
        "request_id": request_id,
        "request_kind": "data_backfill_month",
        "target_component_id": "01_feed_alpaca_bars",
        "parameter_ref": f"storage://trading-manager/monthly_backfill/alpaca_bars/{symbol}/2016-01/task_key.json",
        "expected_outputs": [f"storage://trading-data/monthly_backfill/alpaca_bars/{symbol}/2016-01/"],
        "task_status": "ready" if ready else "requested",
        "latest_run_status": "succeeded" if ready else None,
        "latest_ready_signal_status": "ready" if ready else None,
    }


def _option_chain_summary_row(request_id: str, *, ready: bool = False, failed: bool = False) -> dict[str, object]:
    status = "failed" if failed else ("ready" if ready else "requested")
    return {
        "request_id": request_id,
        "request_kind": "option_chain_snapshot",
        "target_component_id": "option_chain_state_source",
        "parameter_ref": f"storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2016-01/{request_id}/task_key.json",
        "expected_outputs": ["trading_data.option_chain_state_source"],
        "task_status": status,
        "latest_run_status": "failed" if failed else ("succeeded" if ready else None),
        "latest_ready_signal_status": "ready" if ready else None,
    }


class StageCoverageTests(unittest.TestCase):
    def test_three_ready_of_nineteen_is_partial_and_cannot_unlock(self):
        layer_one_symbols = _symbols(LAYER_ONE_MODEL_LAYER)
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in ("QQQ", "SPY", "TLT")],
            *[_summary_row(symbol) for symbol in layer_one_symbols if symbol not in {"QQQ", "SPY", "TLT"}],
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=19,
        )

        self.assertEqual(report.status, "partial_ready")
        self.assertEqual(report.ready_count, 3)
        self.assertEqual(report.pending_count, 16)
        self.assertFalse(report.can_unlock_downstream)
        self.assertIn("3 ready", report.reason)

    def test_full_coverage_can_unlock_downstream(self):
        rows = [_summary_row(symbol, ready=True) for symbol in _symbols(LAYER_ONE_MODEL_LAYER)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=19,
        )

        self.assertEqual(report.status, "ready")
        self.assertEqual(report.ready_count, 19)
        self.assertTrue(report.can_unlock_downstream)

    def test_stage_coverage_ignores_rows_outside_m01_request_universe(self):
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in _symbols(LAYER_ONE_MODEL_LAYER)],
            _summary_row("XLK"),
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=19,
        )

        self.assertEqual(report.observed_count, 19)
        self.assertEqual(report.ready_count, 19)
        self.assertEqual(report.pending_count, 0)

    def test_m01_stage_coverage_uses_background_context_universe(self):
        layer_one_symbols = _symbols(LAYER_ONE_MODEL_LAYER)
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in layer_one_symbols[:2]],
            *[_summary_row(symbol) for symbol in layer_one_symbols[2:]],
            _summary_row("XLK", ready=True),
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=len(layer_one_symbols),
        )

        self.assertEqual(report.observed_count, len(layer_one_symbols))
        self.assertEqual(report.ready_count, 2)
        self.assertEqual(report.pending_count, len(layer_one_symbols) - 2)
        self.assertEqual(report.status, "partial_ready")

    def test_failed_coverage_blocks_downstream_unlock(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("QQQ", failed=True)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=2,
        )

        self.assertEqual(report.status, "failed")
        self.assertEqual(report.ready_count, 1)
        self.assertEqual(report.failed_count, 1)
        self.assertFalse(report.can_unlock_downstream)

    def test_accepted_failed_requests_require_agent_review_ref(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("BITW", failed=True)]

        with self.assertRaisesRegex(TaskSystemError, "agent failure review"):
            summarize_stage_coverage_from_rows(
                rows,
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                expected_count=2,
                accepted_failure_request_ids=["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
            )

    def test_stale_reviewed_failures_outside_current_stage_requests_are_ignored(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("BITW", ready=True)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=2,
            accepted_failure_request_ids=["mgrreq_backfill_alpaca_bars_ibit_2016_01"],
        )

        self.assertEqual(report.status, "ready")
        self.assertEqual(report.accepted_failed_count, 0)
        self.assertEqual(report.accepted_failed_request_ids, ())

    def test_reviewed_failed_requests_preserve_failed_count_but_allow_unlock(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("BITW", failed=True)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=2,
            accepted_failure_request_ids=["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
            accepted_failure_refs=["review://not-yet-listed"],
        )

        self.assertEqual(report.status, "ready")
        self.assertEqual(report.ready_count, 1)
        self.assertEqual(report.failed_count, 1)
        self.assertEqual(report.accepted_failed_count, 1)
        self.assertEqual(report.accepted_failed_request_ids, ("mgrreq_backfill_alpaca_bars_bitw_2016_01",))
        self.assertTrue(report.can_unlock_downstream)
        self.assertIn("1 ready + 1 reviewed failed/skip / 2", report.reason)

    def test_reviewed_preflight_skip_counts_as_terminal_without_rewriting_ready(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("BITW")]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=2,
            accepted_failure_request_ids=["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
            accepted_failure_refs=["review://not-yet-listed"],
        )

        self.assertEqual(report.status, "ready")
        self.assertEqual(report.ready_count, 1)
        self.assertEqual(report.failed_count, 0)
        self.assertEqual(report.accepted_failed_count, 1)
        self.assertEqual(report.pending_count, 0)
        self.assertEqual(report.accepted_failed_request_ids, ("mgrreq_backfill_alpaca_bars_bitw_2016_01",))
        self.assertIn("reviewed failed/skip", report.reason)

    def test_only_reviewed_preflight_skips_are_partial_without_unlock(self):
        rows = [_summary_row("BITW")]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_01_background_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=2,
            accepted_failure_request_ids=["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
            accepted_failure_refs=["review://not-yet-listed"],
        )

        self.assertEqual(report.status, "partial_ready")
        self.assertEqual(report.ready_count, 0)
        self.assertEqual(report.accepted_failed_count, 1)
        self.assertEqual(report.pending_count, 1)
        self.assertFalse(report.can_unlock_downstream)
        self.assertIn("0 ready + 1 reviewed failed/skip / 2", report.reason)

    def test_option_chain_coverage_uses_shared_window_requests_not_stale_layer_nine_snapshots(self):
        window_request = "mgrreq_option_chain_window_aapl_2016_01_2016_01_05_0930"
        stale_snapshot = "mgrreq_m05_option_snapshot_aapl_2016_01_2016_01_05_09_30_00_05_00_old"
        stale_day_request = "mgrreq_option_chain_day_aapl_2016_01_2016_01_05"
        rows = [
            _option_chain_summary_row(window_request, ready=True),
            _option_chain_summary_row(stale_snapshot, ready=True),
            _option_chain_summary_row(stale_day_request, ready=True),
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_05_option_expression.option_chain_data_acquisition",
            start_month="2016-01",
            end_month="2016-06",
            expected_count=1,
        )

        self.assertEqual(report.observed_count, 1)
        self.assertEqual(report.ready_request_ids, (window_request,))
        self.assertEqual(report.status, "ready")

    def test_option_chain_coverage_excludes_stale_end_month_layer_three_requests(self):
        current_request = "mgrreq_option_chain_window_aapl_2021_01_2021_06_01_0930"
        stale_end_month_request = "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700"
        rows = [
            {
                **_option_chain_summary_row(current_request, ready=True),
                "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-01/mgrreq_option_chain_window_aapl_2021_01_2021_06_01_0930/task_key.json",
            },
            {
                **_option_chain_summary_row(stale_end_month_request, failed=True),
                "parameter_ref": "storage://trading-manager/runtime/layer_03_target_state_vector/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700/task_key.json",
            },
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_05_option_expression.option_chain_data_acquisition",
            start_month="2021-01",
            end_month="2021-06",
            expected_count=1,
        )

        self.assertEqual(report.observed_count, 1)
        self.assertEqual(report.failed_request_ids, ())
        self.assertEqual(report.ready_request_ids, (current_request,))

    def test_option_chain_coverage_excludes_stale_non_day_window_times(self):
        current_request = "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_0930"
        stale_after_close = "mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700"
        rows = [
            {
                **_option_chain_summary_row(current_request, ready=True),
                "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_0930/task_key.json",
            },
            {
                **_option_chain_summary_row(stale_after_close, failed=True),
                "parameter_ref": "storage://trading-manager/runtime/model_05_option_expression/option_chain_state_source/2021-06/mgrreq_option_chain_window_aapl_2021_06_2021_06_01_1700/task_key.json",
            },
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="model_05_option_expression.option_chain_data_acquisition",
            start_month="2021-01",
            end_month="2021-06",
            expected_count=1,
        )

        self.assertEqual(report.observed_count, 1)
        self.assertEqual(report.failed_request_ids, ())
        self.assertEqual(report.ready_request_ids, (current_request,))

    def test_partial_coverage_report_does_not_complete_workflow_stage(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)
            report_path = tmp / "coverage.json"
            report_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "model_01_background_context.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "expected_count": 19,
                        "observed_count": 19,
                        "ready_count": 3,
                        "failed_count": 0,
                        "pending_count": 16,
                        "status": "partial_ready",
                        "can_unlock_downstream": False,
                        "ready_request_ids": ["mgrreq_backfill_alpaca_bars_spy_2016_01"],
                        "failed_request_ids": [],
                        "pending_request_ids": [],
                        "reason": "stage coverage partial 3/19; downstream remains blocked",
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
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["model_01_background_context.data_acquisition"].status, "ready")
            self.assertIn("3/19", stages["model_01_background_context.data_acquisition"].last_reason or "")
            self.assertEqual(stages["model_01_background_context.feature_generation"].status, "blocked")

    def test_accepted_failure_coverage_report_completes_stage_and_unlocks_feature_generation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)
            report_path = tmp / "coverage.json"
            report_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "model_01_background_context.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "expected_count": 19,
                        "observed_count": 19,
                        "ready_count": 15,
                        "failed_count": 4,
                        "accepted_failed_count": 4,
                        "pending_count": 0,
                        "status": "ready",
                        "can_unlock_downstream": True,
                        "ready_request_ids": [],
                        "failed_request_ids": ["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
                        "accepted_failed_request_ids": ["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
                        "pending_request_ids": [],
                        "accepted_failure_refs": ["review://not-yet-listed"],
                        "reason": "stage coverage accepted 15 ready + 4 reviewed failed / 19; downstream may unlock",
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
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["model_01_background_context.data_acquisition"].status, "succeeded")
            self.assertIn("reviewed failed", stages["model_01_background_context.data_acquisition"].last_reason or "")
            self.assertEqual(stages["model_01_background_context.feature_generation"].status, "ready")

    def test_complete_coverage_report_completes_stage_and_unlocks_feature_generation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage = tmp / "storage"
            _write_task_keys(storage, model_layer=LAYER_ONE_MODEL_LAYER)
            report_path = tmp / "coverage.json"
            report_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_stage_coverage",
                        "stage_id": "model_01_background_context.data_acquisition",
                        "start_month": "2016-01",
                        "end_month": "2016-01",
                        "expected_count": 19,
                        "observed_count": 19,
                        "ready_count": 19,
                        "failed_count": 0,
                        "pending_count": 0,
                        "status": "ready",
                        "can_unlock_downstream": True,
                        "ready_request_ids": [],
                        "failed_request_ids": [],
                        "pending_request_ids": [],
                        "reason": "stage coverage complete 19/19; downstream may unlock",
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
                approved_stage_refs=["model_01_background_context.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["model_01_background_context.data_acquisition"].status, "succeeded")
            self.assertEqual(stages["model_01_background_context.feature_generation"].status, "ready")


if __name__ == "__main__":
    unittest.main()

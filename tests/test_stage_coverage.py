from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.model_training_state import advance_workflow_state
from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe
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


class StageCoverageTests(unittest.TestCase):
    def test_three_ready_of_nineteen_is_partial_and_cannot_unlock(self):
        layer_one_symbols = _symbols(LAYER_ONE_MODEL_LAYER)
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in ("QQQ", "SPY", "TLT")],
            *[_summary_row(symbol) for symbol in layer_one_symbols if symbol not in {"QQQ", "SPY", "TLT"}],
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_01_market_regime.data_acquisition",
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
            stage_id="layer_01_market_regime.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=19,
        )

        self.assertEqual(report.status, "ready")
        self.assertEqual(report.ready_count, 19)
        self.assertTrue(report.can_unlock_downstream)

    def test_layer_one_stage_coverage_ignores_layer_two_rows_for_same_month(self):
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in _symbols(LAYER_ONE_MODEL_LAYER)],
            *[_summary_row(symbol) for symbol in _symbols(LAYER_TWO_MODEL_LAYER)],
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_01_market_regime.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=19,
        )

        self.assertEqual(report.observed_count, 19)
        self.assertEqual(report.ready_count, 19)
        self.assertEqual(report.pending_count, 0)

    def test_layer_two_stage_coverage_uses_sector_context_universe(self):
        layer_two_symbols = _symbols(LAYER_TWO_MODEL_LAYER)
        rows = [
            *[_summary_row(symbol, ready=True) for symbol in layer_two_symbols[:2]],
            *[_summary_row(symbol) for symbol in layer_two_symbols[2:]],
            _summary_row("SPY", ready=True),
        ]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_02_sector_context.data_acquisition",
            start_month="2016-01",
            end_month="2016-01",
            expected_count=len(layer_two_symbols),
        )

        self.assertEqual(report.observed_count, len(layer_two_symbols))
        self.assertEqual(report.ready_count, 2)
        self.assertEqual(report.pending_count, len(layer_two_symbols) - 2)
        self.assertEqual(report.status, "partial_ready")

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

    def test_accepted_failed_requests_require_agent_review_ref(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("BITW", failed=True)]

        with self.assertRaisesRegex(TaskSystemError, "agent failure review"):
            summarize_stage_coverage_from_rows(
                rows,
                stage_id="layer_01_market_regime.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                expected_count=2,
                accepted_failure_request_ids=["mgrreq_backfill_alpaca_bars_bitw_2016_01"],
            )

    def test_stale_reviewed_failures_outside_current_stage_requests_are_ignored(self):
        rows = [_summary_row("SPY", ready=True), _summary_row("BITW", ready=True)]

        report = summarize_stage_coverage_from_rows(
            rows,
            stage_id="layer_01_market_regime.data_acquisition",
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
            stage_id="layer_01_market_regime.data_acquisition",
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
            stage_id="layer_01_market_regime.data_acquisition",
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
            stage_id="layer_01_market_regime.data_acquisition",
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
                        "stage_id": "layer_01_market_regime.data_acquisition",
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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["layer_01_market_regime.data_acquisition"].status, "ready")
            self.assertIn("3/19", stages["layer_01_market_regime.data_acquisition"].last_reason or "")
            self.assertEqual(stages["layer_01_market_regime.feature_generation"].status, "blocked")

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
                        "stage_id": "layer_01_market_regime.data_acquisition",
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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["layer_01_market_regime.data_acquisition"].status, "succeeded")
            self.assertIn("reviewed failed", stages["layer_01_market_regime.data_acquisition"].last_reason or "")
            self.assertEqual(stages["layer_01_market_regime.feature_generation"].status, "ready")

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
                        "stage_id": "layer_01_market_regime.data_acquisition",
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
                approved_stage_refs=["layer_01_market_regime.data_acquisition=approval://layer1"],
                stage_coverage_reports=[report_path],
                write=False,
            )

            stages = {stage.stage_id: stage for stage in state.stages}
            self.assertEqual(stages["layer_01_market_regime.data_acquisition"].status, "succeeded")
            self.assertEqual(stages["layer_01_market_regime.feature_generation"].status, "ready")


if __name__ == "__main__":
    unittest.main()

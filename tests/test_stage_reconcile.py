from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.stage_coverage import StageCoverageReport
from trading_manager_tasks.stage_reconcile import discover_stage_receipts, reconcile_provider_stage


def _write_receipt(root: Path, *, symbol: str = "XLK", month: str = "2016-01") -> Path:
    path = root / "monthly_backfill_v1" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": f"run_{symbol.lower()}_{month.replace('-', '_')}",
                        "status": "succeeded",
                        "started_at": "2026-05-10T00:00:00Z",
                        "completed_at": "2026-05-10T00:00:01Z",
                        "outputs": [f"storage/monthly_backfill_v1/alpaca_bars/{symbol}/{month}/runs/run_1/saved/equity_bar.csv"],
                        "row_counts": {"equity_bar": 10},
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _coverage() -> StageCoverageReport:
    return StageCoverageReport(
        contract_type="manager_stage_coverage_v1",
        stage_id="layer_02_sector_context.data_acquisition",
        start_month="2016-01",
        end_month="2016-01",
        expected_count=25,
        observed_count=6,
        ready_count=1,
        failed_count=0,
        pending_count=19,
        accepted_failed_count=5,
        status="partial_ready",
        can_unlock_downstream=False,
        ready_request_ids=("mgrreq_backfill_alpaca_bars_xlk_2016_01",),
        failed_request_ids=(),
        accepted_failed_request_ids=(
            "mgrreq_backfill_alpaca_bars_aiq_2016_01",
            "mgrreq_backfill_alpaca_bars_arkf_2016_01",
            "mgrreq_backfill_alpaca_bars_arkx_2016_01",
            "mgrreq_backfill_alpaca_bars_bkch_2016_01",
            "mgrreq_backfill_alpaca_bars_xlc_2016_01",
        ),
        pending_request_ids=(),
        accepted_failure_refs=("review://layer2-preflight",),
        reason="stage coverage partial 1 ready + 5 reviewed failed/skip / 25; downstream remains blocked",
    )


class StageReconcileTests(unittest.TestCase):
    def test_discovers_layer_two_receipts_by_reviewed_universe(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            receipt = _write_receipt(root, symbol="XLK")
            refs = discover_stage_receipts(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
            )

        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].symbol, "XLK")
        self.assertEqual(refs[0].request_id, "mgrreq_backfill_alpaca_bars_xlk_2016_01")
        self.assertEqual(refs[0].receipt_path, receipt)
        self.assertEqual(refs[0].receipt_uri, "storage://trading-data/monthly_backfill_v1/alpaca_bars/XLK/2016-01/completion_receipt.json")

    def test_reconcile_normalizes_receipts_without_provider_calls_or_writes_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(),
        ) as collect_mock, patch(
            "trading_manager_tasks.stage_reconcile.persist_completion_rows",
        ) as persist_mock:
            root = Path(raw_tmp)
            _write_receipt(root, symbol="XLK")
            summary = reconcile_provider_stage(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
            )

        self.assertEqual(summary.contract_type, "manager_provider_stage_reconcile_v1")
        self.assertEqual(summary.discovered_receipt_count, 1)
        self.assertEqual(summary.normalized_run_manifest_count, 1)
        self.assertGreaterEqual(summary.normalized_artifact_ref_count, 2)
        self.assertEqual(summary.normalized_ready_signal_count, 1)
        self.assertFalse(summary.persisted_control_plane)
        self.assertEqual(summary.coverage_status, "partial_ready")
        self.assertEqual(summary.provider_calls, 0)
        self.assertFalse(summary.dispatch_performed)
        self.assertFalse(summary.model_activation_performed)
        self.assertFalse(summary.broker_execution_performed)
        self.assertFalse(summary.storage_lifecycle_mutation_performed)
        persist_mock.assert_not_called()
        collect_mock.assert_called_once()

    def test_reconcile_can_write_coverage_and_advance_workflow_only_from_written_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(),
        ), patch("trading_manager_tasks.stage_reconcile.persist_completion_rows") as persist_mock, patch(
            "trading_manager_tasks.stage_reconcile.advance_workflow_state",
        ) as advance_mock:
            root = Path(raw_tmp)
            _write_receipt(root, symbol="XLK")
            coverage_path = root / "coverage.json"
            summary = reconcile_provider_stage(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
                persist_control_plane=True,
                coverage_report_path=coverage_path,
                write_coverage_report=True,
                advance_workflow=True,
                workflow_state_path=root / "workflow.json",
                write_workflow_state=True,
            )

            self.assertTrue(summary.persisted_control_plane)
            self.assertEqual(summary.coverage_report_path, str(coverage_path))
            self.assertTrue(coverage_path.exists())
            self.assertTrue(summary.workflow_advanced)
            persist_mock.assert_called_once()
            advance_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()

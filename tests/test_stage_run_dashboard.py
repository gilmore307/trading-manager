from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.live_call_packet import create_live_call_approval_packet
from trading_manager_tasks.monthly_backfill import LAYER_TWO_MODEL_LAYER
from trading_manager_tasks.stage_coverage import StageCoverageReport
from trading_manager_tasks.stage_run_dashboard import build_stage_run_dashboard, collect_packet_summaries, default_dashboard_path


def _coverage(*, status: str = "partial_ready") -> StageCoverageReport:
    return StageCoverageReport(
        contract_type="manager_stage_coverage_v1",
        stage_id="layer_02_sector_context.data_acquisition",
        start_month="2016-01",
        end_month="2016-01",
        expected_count=25,
        observed_count=8,
        ready_count=3,
        failed_count=0 if status != "failed" else 1,
        pending_count=17,
        accepted_failed_count=5,
        status=status,
        can_unlock_downstream=status == "ready",
        ready_request_ids=(
            "mgrreq_backfill_alpaca_bars_xlb_2016_01",
            "mgrreq_backfill_alpaca_bars_xle_2016_01",
            "mgrreq_backfill_alpaca_bars_xlk_2016_01",
        ),
        failed_request_ids=("mgrreq_backfill_alpaca_bars_xop_2016_01",) if status == "failed" else (),
        accepted_failed_request_ids=(
            "mgrreq_backfill_alpaca_bars_aiq_2016_01",
            "mgrreq_backfill_alpaca_bars_arkf_2016_01",
            "mgrreq_backfill_alpaca_bars_arkx_2016_01",
            "mgrreq_backfill_alpaca_bars_bkch_2016_01",
            "mgrreq_backfill_alpaca_bars_xlc_2016_01",
        ),
        pending_request_ids=("mgrreq_backfill_alpaca_bars_arkg_2016_01",),
        accepted_failure_refs=("review://layer2-preflight",),
        reason="stage coverage partial 3 ready + 5 reviewed failed/skip / 25; downstream remains blocked",
    )


class StageRunDashboardTests(unittest.TestCase):
    def test_collect_packet_summaries_reads_packet_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=((), ()),
        ):
            root = Path(raw_tmp)
            packet = create_live_call_approval_packet(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=root / "manager_storage",
                packet_root=root / "packets",
                symbols=("XLK",),
                write=True,
            )
            rows = collect_packet_summaries(
                model_layer=LAYER_TWO_MODEL_LAYER,
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_root=root / "packets",
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].packet_id, packet.packet_id)
        self.assertEqual(rows[0].status, "template_pending_review")
        self.assertEqual(rows[0].provider_calls, 0)

    def test_dashboard_is_single_receipt_with_coverage_packets_and_next_pending_packet(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=((), ()),
        ), patch(
            "trading_manager_tasks.live_call_planning.collect_stage_coverage",
            return_value=_coverage(),
        ), patch(
            "trading_manager_tasks.stage_run_dashboard.collect_stage_coverage",
            return_value=_coverage(),
        ):
            root = Path(raw_tmp)
            create_live_call_approval_packet(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=root / "manager_storage",
                packet_root=root / "packets",
                symbols=("XLK",),
                write=True,
            )
            dashboard = build_stage_run_dashboard(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_root=root / "packets",
                packet_storage_root=root / "manager_storage",
                next_limit=1,
            )

        self.assertEqual(dashboard.contract_type, "manager_stage_run_dashboard_v1")
        self.assertEqual(dashboard.coverage["ready_count"], 3)
        self.assertEqual(dashboard.coverage["pending_count"], 17)
        self.assertEqual(dashboard.packet_count, 1)
        self.assertTrue(dashboard.next_recommended_packet.available)
        self.assertEqual(dashboard.next_recommended_packet.request_count, 1)
        self.assertEqual(dashboard.next_recommended_packet.request_ids, ("mgrreq_backfill_alpaca_bars_arkg_2016_01",))
        self.assertEqual(dashboard.next_action, "review_existing_pending_packet")
        self.assertFalse(dashboard.broker_execution_performed)

    def test_dashboard_prioritizes_failed_coverage_over_next_packet(self) -> None:
        with patch("trading_manager_tasks.stage_run_dashboard.collect_stage_coverage", return_value=_coverage(status="failed")), patch(
            "trading_manager_tasks.stage_run_dashboard.preview_next_pending_packet"
        ) as preview_mock:
            preview_mock.return_value.available = True
            preview_mock.return_value.request_count = 1
            preview_mock.return_value.reason = "pending"
            dashboard = build_stage_run_dashboard(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_root=Path("/tmp/does-not-exist"),
                packet_storage_root=Path("/tmp/does-not-exist"),
                next_limit=1,
            )

        self.assertEqual(dashboard.next_action, "review_stage_failures")
        self.assertIn("downstream remains blocked", dashboard.blocking_reason)

    def test_default_dashboard_path_is_stable(self) -> None:
        self.assertEqual(
            default_dashboard_path(stage_id="layer_02_sector_context.data_acquisition", start_month="2016-01"),
            Path("storage/runtime/stage_run_dashboard/layer_02_sector_context_data_acquisition_2016-01.json"),
        )


if __name__ == "__main__":
    unittest.main()

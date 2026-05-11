from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.stage_run_controller import run_stage_controller_step
from trading_manager_tasks.stage_run_dashboard import StageRunDashboard, StageRunNextPacket
from trading_manager_tasks.stage_coverage import StageCoverageReport


def _coverage() -> dict:
    return {
        "contract_type": "manager_stage_coverage_v1",
        "status": "partial_ready",
        "expected_count": 25,
        "observed_count": 8,
        "ready_count": 3,
        "failed_count": 0,
        "accepted_failed_count": 5,
        "pending_count": 17,
        "can_unlock_downstream": False,
        "ready_request_ids": [],
        "failed_request_ids": [],
        "accepted_failed_request_ids": [],
        "pending_request_ids": [],
        "accepted_failure_refs": [],
        "reason": "partial",
    }


def _dashboard(next_action: str) -> StageRunDashboard:
    return StageRunDashboard(
        contract_type="manager_stage_run_dashboard_v1",
        stage_id="layer_02_sector_context.data_acquisition",
        model_layer="layer_02_sector_context",
        start_month="2016-01",
        end_month="2016-01",
        coverage=_coverage(),
        packet_count=0,
        packets=(),
        latest_packet_status=None,
        next_recommended_packet=StageRunNextPacket(
            available=True,
            reason="pending",
            request_count=1,
            request_ids=("mgrreq_backfill_alpaca_bars_arkg_2016_01",),
            skipped_registered_request_ids=(),
            skipped_terminal_request_ids=(),
            create_packet_command=("create",),
        ),
        blocking_reason="partial",
        next_action=next_action,
        evidence_refs=(),
        provider_calls_observed=0,
        dispatch_performed_observed=False,
    )


class StageRunControllerTests(unittest.TestCase):
    def test_controller_creates_pending_packet_when_dashboard_requests_it(self) -> None:
        after_dashboard = _dashboard("review_existing_pending_packet")
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("create_or_review_next_pending_only_packet"), after_dashboard],
        ), patch("trading_manager_tasks.stage_run_controller.create_live_call_approval_packet") as create_mock:
            create_mock.return_value.packet_dir = str(Path(raw_tmp) / "packet")
            create_mock.return_value.packet_id = "packet_1"
            dashboard_path = Path(raw_tmp) / "dashboard.json"
            receipt, dashboard = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_root=Path(raw_tmp) / "packets",
                packet_storage_root=Path(raw_tmp) / "storage",
                dashboard_path=dashboard_path,
            )
            dashboard_exists = dashboard_path.exists()

        self.assertEqual(receipt.contract_type, "manager_stage_run_controller_receipt_v1")
        self.assertEqual(receipt.action_taken, "create_pending_only_packet")
        self.assertEqual(receipt.action_status, "completed")
        self.assertEqual(receipt.created_packet_id, "packet_1")
        self.assertEqual(receipt.dashboard_next_action_before, "create_or_review_next_pending_only_packet")
        self.assertEqual(receipt.dashboard_next_action_after, "review_existing_pending_packet")
        self.assertEqual(receipt.provider_calls, 0)
        self.assertFalse(receipt.dispatch_performed)
        self.assertEqual(dashboard.next_action, "review_existing_pending_packet")
        create_mock.assert_called_once()
        self.assertTrue(dashboard_exists)

    def test_controller_stops_at_provider_execution_gate(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("review_execute_or_defer_ready_packet"), _dashboard("review_execute_or_defer_ready_packet")],
        ), patch("trading_manager_tasks.stage_run_controller.create_live_call_approval_packet") as create_mock:
            receipt, _dashboard_row = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                dashboard_path=Path(raw_tmp) / "dashboard.json",
            )

        self.assertEqual(receipt.action_taken, "provider_execution_review_required")
        self.assertEqual(receipt.action_status, "external_call_gate")
        self.assertEqual(receipt.provider_calls, 0)
        create_mock.assert_not_called()

    def test_controller_can_run_dry_without_creating_packet(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("create_or_review_next_pending_only_packet"), _dashboard("create_or_review_next_pending_only_packet")],
        ), patch("trading_manager_tasks.stage_run_controller.create_live_call_approval_packet") as create_mock:
            receipt, _dashboard_row = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                auto_create_packet=False,
                dashboard_path=Path(raw_tmp) / "dashboard.json",
            )

        self.assertEqual(receipt.action_taken, "create_pending_only_packet")
        self.assertEqual(receipt.action_status, "dry_run_no_write")
        create_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()

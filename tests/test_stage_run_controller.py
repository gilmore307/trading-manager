from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.stage_run_controller import run_stage_controller_step
from trading_manager_tasks.stage_run_dashboard import StageRunDashboard, StageRunProviderDispatchPreview


def _coverage() -> dict:
    return {
        "contract_type": "manager_stage_coverage",
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
        "pending_request_ids": ["mgrreq_backfill_alpaca_bars_arkg_2016_01"],
        "accepted_failure_refs": [],
        "reason": "partial",
    }


def _preview() -> StageRunProviderDispatchPreview:
    return StageRunProviderDispatchPreview(
        available=True,
        reason="autonomous provider dispatch preview available",
        request_count=1,
        request_ids=("mgrreq_backfill_alpaca_bars_arkg_2016_01",),
        skipped_registered_request_ids=(),
        command_preview=(("python3", "-m", "data_feed.01_feed_alpaca_bars", "task_key.json"),),
        execute_command_template=("PYTHONPATH=src", "python3", "scripts/tasks/dispatch_and_reconcile_provider_stage.py"),
    )


def _dashboard(next_action: str) -> StageRunDashboard:
    return StageRunDashboard(
        contract_type="manager_stage_run_dashboard",
        stage_id="layer_02_sector_context.data_acquisition",
        model_layer="layer_02_sector_context",
        start_month="2016-01",
        end_month="2016-01",
        coverage=_coverage(),
        next_provider_dispatch=_preview(),
        blocking_reason="partial",
        next_action=next_action,
        evidence_refs=(),
        provider_calls_observed=0,
        dispatch_performed_observed=False,
    )


class StageRunControllerTests(unittest.TestCase):
    def test_controller_executes_autonomous_provider_dispatch_when_ready(self) -> None:
        after_dashboard = _dashboard("no_action_until_blocker_resolved")
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("autonomous_provider_dispatch_ready"), after_dashboard],
        ), patch("trading_manager_tasks.stage_run_controller.dispatch_layer_provider_acquisition") as dispatch_mock:
            dispatch_mock.return_value.provider_calls = 1
            dispatch_mock.return_value.dispatch_performed = True
            dashboard_path = Path(raw_tmp) / "dashboard.json"
            receipt, dashboard = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_storage_root=Path(raw_tmp) / "storage",
                dashboard_path=dashboard_path,
            )
            dashboard_exists = dashboard_path.exists()

        self.assertEqual(receipt.contract_type, "manager_stage_run_controller_receipt")
        self.assertEqual(receipt.action_taken, "execute_autonomous_provider_dispatch")
        self.assertEqual(receipt.action_status, "completed")
        self.assertEqual(receipt.dispatch_request_ids, ("mgrreq_backfill_alpaca_bars_arkg_2016_01",))
        self.assertEqual(receipt.provider_calls, 1)
        self.assertTrue(receipt.dispatch_performed)
        self.assertFalse(receipt.broker_execution_performed)
        self.assertFalse(receipt.model_activation_performed)
        self.assertEqual(dashboard.next_action, "no_action_until_blocker_resolved")
        dispatch_mock.assert_called_once()
        self.assertTrue(dashboard_exists)

    def test_controller_can_plan_without_provider_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("autonomous_provider_dispatch_ready"), _dashboard("autonomous_provider_dispatch_ready")],
        ), patch("trading_manager_tasks.stage_run_controller.dispatch_layer_provider_acquisition") as dispatch_mock:
            receipt, _dashboard_row = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                auto_execute_provider_calls=False,
                dashboard_path=Path(raw_tmp) / "dashboard.json",
            )

        self.assertEqual(receipt.action_taken, "execute_autonomous_provider_dispatch")
        self.assertEqual(receipt.action_status, "dry_run_no_provider_calls")
        self.assertEqual(receipt.provider_calls, 0)
        dispatch_mock.assert_not_called()

    def test_controller_surfaces_failed_stage_auto_repair(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("automatic_repair_required"), _dashboard("automatic_repair_required")],
        ), patch("trading_manager_tasks.stage_run_controller.dispatch_layer_provider_acquisition") as dispatch_mock:
            receipt, _dashboard_row = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                dashboard_path=Path(raw_tmp) / "dashboard.json",
            )

        self.assertEqual(receipt.action_taken, "automatic_repair_required")
        self.assertEqual(receipt.action_status, "automatic_repair_pending")
        self.assertEqual(receipt.provider_calls, 0)
        dispatch_mock.assert_not_called()

    def test_controller_retries_retryable_provider_policy_failures(self) -> None:
        after_dashboard = _dashboard("no_action_until_blocker_resolved")
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_run_controller.build_stage_run_dashboard",
            side_effect=[_dashboard("autonomous_provider_failure_retry_ready"), after_dashboard],
        ), patch("trading_manager_tasks.stage_run_controller.dispatch_layer_provider_acquisition") as dispatch_mock:
            dispatch_mock.return_value.provider_calls = 1
            dispatch_mock.return_value.dispatch_performed = True
            receipt, _dashboard_row = run_stage_controller_step(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_storage_root=Path(raw_tmp) / "storage",
                dashboard_path=Path(raw_tmp) / "dashboard.json",
            )

        self.assertEqual(receipt.action_taken, "retry_failed_provider_policy_requests")
        self.assertEqual(receipt.action_status, "completed")
        self.assertEqual(receipt.provider_calls, 1)
        self.assertFalse(dispatch_mock.call_args.kwargs["reject_terminal_coverage"])


if __name__ == "__main__":
    unittest.main()

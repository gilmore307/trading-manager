from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.stage_coverage import StageCoverageReport
from trading_manager_tasks.stage_run_dashboard import (
    DEFAULT_STAGE_RUN_DASHBOARD_ROOT,
    StageRunProviderDispatchPreview,
    build_stage_run_dashboard,
    default_dashboard_path,
)


def _coverage(*, status: str = "partial_ready") -> StageCoverageReport:
    return StageCoverageReport(
        contract_type="manager_stage_coverage",
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


def _preview(*, available: bool = True) -> StageRunProviderDispatchPreview:
    return StageRunProviderDispatchPreview(
        available=available,
        reason="autonomous provider dispatch preview available" if available else "no pending request ids available",
        request_count=1 if available else 0,
        request_ids=("mgrreq_backfill_alpaca_bars_arkg_2016_01",) if available else (),
        skipped_registered_request_ids=(),
        command_preview=(("python3", "-m", "data_feed.01_feed_alpaca_bars", "task_key.json"),) if available else (),
        worker_preview=(
            {
                "request_id": "mgrreq_backfill_alpaca_bars_arkg_2016_01",
                "worker_id": "provider-worker-1",
                "worker_slot": 1,
                "status": "validated_not_dispatched",
            },
        ) if available else (),
        execute_command_template=("PYTHONPATH=src", "python3", "scripts/tasks/dispatch_and_reconcile_provider_stage.py"),
    )


class StageRunDashboardTests(unittest.TestCase):
    def test_dashboard_is_single_receipt_with_coverage_and_next_provider_dispatch(self) -> None:
        with patch("trading_manager_tasks.stage_run_dashboard.collect_stage_coverage", return_value=_coverage()), patch(
            "trading_manager_tasks.stage_run_dashboard.preview_next_provider_dispatch",
            return_value=_preview(),
        ):
            dashboard = build_stage_run_dashboard(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_storage_root=Path("/tmp/does-not-exist"),
                next_limit=1,
            )

        self.assertEqual(dashboard.contract_type, "manager_stage_run_dashboard")
        self.assertEqual(dashboard.coverage["ready_count"], 3)
        self.assertEqual(dashboard.coverage["pending_count"], 17)
        self.assertTrue(dashboard.next_provider_dispatch.available)
        self.assertEqual(dashboard.next_provider_dispatch.request_count, 1)
        self.assertEqual(dashboard.next_provider_dispatch.request_ids, ("mgrreq_backfill_alpaca_bars_arkg_2016_01",))
        self.assertEqual(dashboard.next_provider_dispatch.worker_preview[0]["worker_id"], "provider-worker-1")
        self.assertEqual(dashboard.next_action, "autonomous_provider_dispatch_ready")
        self.assertFalse(dashboard.broker_execution_performed)
        self.assertFalse(dashboard.model_activation_performed)

    def test_dashboard_prioritizes_failed_coverage_over_dispatch_preview(self) -> None:
        with patch("trading_manager_tasks.stage_run_dashboard.collect_stage_coverage", return_value=_coverage(status="failed")), patch(
            "trading_manager_tasks.stage_run_dashboard.preview_next_provider_dispatch",
            return_value=_preview(),
        ):
            dashboard = build_stage_run_dashboard(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_storage_root=Path("/tmp/does-not-exist"),
                next_limit=1,
            )

        self.assertEqual(dashboard.next_action, "review_stage_failures")
        self.assertIn("downstream remains blocked", dashboard.blocking_reason)

    def test_failed_provider_policy_coverage_can_retry_autonomously(self) -> None:
        retry_preview = StageRunProviderDispatchPreview(
            available=True,
            reason="retryable provider policy failures available for autonomous retry",
            request_count=1,
            request_ids=("mgrreq_backfill_alpaca_bars_xop_2016_01",),
            skipped_registered_request_ids=(),
            command_preview=(("python3", "-m", "data_feed.01_feed_alpaca_bars", "task_key.json"),),
            execute_command_template=("PYTHONPATH=src", "python3", "scripts/tasks/dispatch_and_reconcile_provider_stage.py"),
        )
        with patch("trading_manager_tasks.stage_run_dashboard.collect_stage_coverage", return_value=_coverage(status="failed")), patch(
            "trading_manager_tasks.stage_run_dashboard.preview_next_provider_dispatch",
            return_value=retry_preview,
        ):
            dashboard = build_stage_run_dashboard(
                stage_id="layer_02_sector_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                packet_storage_root=Path("/tmp/does-not-exist"),
                next_limit=1,
            )

        self.assertEqual(dashboard.next_action, "autonomous_provider_failure_retry_ready")
        self.assertEqual(dashboard.next_provider_dispatch.request_ids, ("mgrreq_backfill_alpaca_bars_xop_2016_01",))

    def test_default_dashboard_path_is_stable(self) -> None:
        self.assertEqual(
            default_dashboard_path(stage_id="layer_02_sector_context.data_acquisition", start_month="2016-01"),
            DEFAULT_STAGE_RUN_DASHBOARD_ROOT / "layer_02_sector_context_data_acquisition_2016-01.json",
        )


if __name__ == "__main__":
    unittest.main()

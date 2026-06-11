from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.stage_coverage import StageCoverageReport
from trading_manager_tasks.stage_reconcile import (
    classify_provider_failure,
    discover_stage_receipts,
    exclude_accepted_failure_rows,
    propose_failure_register_rows,
    reconcile_provider_stage,
)


def _write_receipt(root: Path, *, symbol: str = "SPY", month: str = "2016-01", status: str = "succeeded") -> Path:
    path = root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": f"run_{symbol.lower()}_{month.replace('-', '_')}",
                        "status": status,
                        "started_at": "2026-05-10T00:00:00Z",
                        "completed_at": "2026-05-10T00:00:01Z",
                        "outputs": ["trading_data.model_01_market_regime_data_acquisition"],
                        "row_counts": {"equity_bar": 10},
                        "error": {"type": "AlpacaBarsError", "message": "bars unavailable"} if status != "succeeded" else None,
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_retry_receipt(root: Path, *, symbol: str = "SPY", month: str = "2016-01") -> Path:
    path = root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": f"run_{symbol.lower()}_{month.replace('-', '_')}_failed",
                        "status": "failed",
                        "started_at": "2026-05-10T00:00:00Z",
                        "completed_at": "2026-05-10T00:00:01Z",
                        "error": {"type": "ProviderPolicyError", "message": "provider not allowed: thetadata"},
                    },
                    {
                        "run_id": f"run_{symbol.lower()}_{month.replace('-', '_')}_succeeded",
                        "status": "succeeded",
                        "started_at": "2026-05-10T00:01:00Z",
                        "completed_at": "2026-05-10T00:01:01Z",
                        "outputs": ["trading_data.model_01_market_regime_data_acquisition"],
                        "row_counts": {"equity_bar": 10},
                    },
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_connection_refused_receipt(root: Path, *, symbol: str = "SPY", month: str = "2016-01") -> Path:
    path = root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": f"run_{symbol.lower()}_{month.replace('-', '_')}_connection_refused",
                        "status": "failed",
                        "started_at": "2026-05-10T00:00:00Z",
                        "completed_at": "2026-05-10T00:00:01Z",
                        "error": {
                            "type": "ThetaDataOptionSelectionSnapshotError",
                            "message": "request failed before HTTP response: URLError: <urlopen error [Errno 111] Connection refused>",
                        },
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _coverage(stage_id: str = "model_01_background_context.data_acquisition") -> StageCoverageReport:
    return StageCoverageReport(
        contract_type="manager_stage_coverage",
        stage_id=stage_id,
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
        ready_request_ids=("mgrreq_backfill_alpaca_bars_spy_2016_01",),
        failed_request_ids=(),
        accepted_failed_request_ids=(
            "mgrreq_backfill_alpaca_bars_aiq_2016_01",
            "mgrreq_backfill_alpaca_bars_arkf_2016_01",
            "mgrreq_backfill_alpaca_bars_arkx_2016_01",
            "mgrreq_backfill_alpaca_bars_bkch_2016_01",
            "mgrreq_backfill_alpaca_bars_xlc_2016_01",
        ),
        pending_request_ids=(),
        accepted_failure_refs=("review://model1-preflight",),
        reason="stage coverage partial 1 ready + 5 reviewed failed/skip / 25; downstream remains blocked",
    )


class StageReconcileTests(unittest.TestCase):
    def test_discovers_m01_receipts_by_reviewed_universe(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            receipt = _write_receipt(root, symbol="SPY")
            refs = discover_stage_receipts(
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
            )

        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0].symbol, "SPY")
        self.assertEqual(refs[0].request_id, "mgrreq_backfill_alpaca_bars_spy_2016_01")
        self.assertEqual(refs[0].receipt_path, receipt)
        self.assertEqual(refs[0].receipt_uri, "storage://trading-data/monthly_backfill/alpaca_bars/SPY/2016-01/completion_receipt.json")

    def test_reconcile_normalizes_receipts_without_provider_calls_or_writes_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(),
        ) as collect_mock, patch(
            "trading_manager_tasks.stage_reconcile.persist_completion_rows",
        ) as persist_mock:
            root = Path(raw_tmp)
            _write_receipt(root, symbol="SPY")
            summary = reconcile_provider_stage(
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
                locks_dir=root / "locks",
            )

        self.assertEqual(summary.contract_type, "manager_provider_stage_reconcile")
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

    def test_failed_receipts_generate_auto_repair_required_failure_proposals(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            _write_receipt(root, symbol="SPY", status="failed")
            refs = discover_stage_receipts(
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
            )
            rows = propose_failure_register_rows(
                refs,
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["contract_type"], "manager_failure_register")
        self.assertEqual(rows[0]["request_id"], "mgrreq_backfill_alpaca_bars_spy_2016_01")
        self.assertEqual(rows[0]["failure_status"], "auto_repair_required")
        self.assertEqual(rows[0]["failure_kind"], "unclassified_provider_failure")
        self.assertFalse(rows[0]["skip_future_matching"])
        self.assertIsNone(rows[0]["agent_review_ref"])
        self.assertIn("AlpacaBarsError", rows[0]["error_summary"])

    def test_retryable_provider_runtime_failures_generate_retry_required_proposals(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            _write_connection_refused_receipt(root, symbol="SPY")
            refs = discover_stage_receipts(
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
            )
            rows = propose_failure_register_rows(
                refs,
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
            )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["failure_status"], "retry_required")
        self.assertEqual(rows[0]["failure_kind"], "provider_service_unavailable")
        self.assertIn("automatic retry", rows[0]["note"])

    def test_accepted_failure_rows_do_not_reopen_reconcile_proposals(self) -> None:
        row = {
            "request_id": "mgrreq_option_chain_window_aapl_2018_07_2018_12_05_0930",
            "failure_status": "auto_repair_required",
        }

        with patch(
            "trading_manager_tasks.stage_reconcile.accepted_failure_request_ids_from_register",
            return_value=((row["request_id"],), ("server_error_repair:ERR-000040",)),
        ):
            rows = exclude_accepted_failure_rows(
                [row],
                stage_id="model_05_option_expression.option_chain_data_acquisition",
                start_month="2018-07",
                end_month="2018-12",
            )

        self.assertEqual(rows, ())

    def test_provider_html_status_errors_generate_retry_required_proposals(self) -> None:
        status, kind, note = classify_provider_failure(
            'AuthenticationError: <!doctype html><html><head><title>HTTP Status 500 - Internal Server Error</title></head></html>'
        )
        self.assertEqual(status, "retry_required")
        self.assertEqual(kind, "provider_http_retryable")
        self.assertIn("automatic retry", note)

    def test_failure_classifier_routes_provider_policy_errors_to_auto_repair(self) -> None:
        status, kind, note = classify_provider_failure("ProviderPolicyError: provider not allowed: thetadata")
        self.assertEqual(status, "auto_repair_required")
        self.assertEqual(kind, "unclassified_provider_failure")
        self.assertIn("automatic repair", note)

    def test_retried_receipt_with_latest_success_does_not_propose_stale_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            _write_retry_receipt(root, symbol="SPY")
            refs = discover_stage_receipts(
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
            )
            rows = propose_failure_register_rows(
                refs,
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
            )

        self.assertEqual(rows, ())

    def test_reconcile_can_write_failure_proposal_without_accepting_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(),
        ), patch("trading_manager_tasks.stage_reconcile.persist_failure_register_rows") as failure_persist_mock, patch(
            "trading_manager_tasks.stage_reconcile.mark_failure_register_requests_corrected"
        ) as correction_mock:
            with patch("trading_manager_tasks.stage_reconcile.handle_server_error") as error_handoff_mock:
                error_handoff_mock.return_value = {
                    "error_number": 12,
                    "error_ref": "ERR-000012",
                    "request_path": "/tmp/request.json",
                    "diagnosis_path": "/tmp/diagnosis.json",
                    "status": "queued",
                }
                root = Path(raw_tmp)
                _write_receipt(root, symbol="SPY", status="failed")
                proposal_path = root / "failure_proposals.jsonl"
                summary = reconcile_provider_stage(
                    stage_id="model_01_background_context.data_acquisition",
                    start_month="2016-01",
                    end_month="2016-01",
                    component_storage_root=root,
                    failure_proposal_path=proposal_path,
                    write_failure_proposal=True,
                    persist_failure_register=True,
                    locks_dir=root / "locks",
                )

            self.assertEqual(summary.failure_proposal_count, 1)
            self.assertEqual(summary.failure_proposal_path, str(proposal_path))
            self.assertTrue(summary.persisted_failure_register)
            self.assertEqual(summary.agent_error_ref, "ERR-000012")
            self.assertEqual(summary.agent_error_status, "queued")
            row = json.loads(proposal_path.read_text(encoding="utf-8").strip())
            self.assertEqual(row["failure_status"], "auto_repair_required")
            self.assertFalse(row["skip_future_matching"])
            correction_mock.assert_called_once()
            failure_persist_mock.assert_called_once()
            error_handoff_mock.assert_called_once()

    def test_reconcile_does_not_open_agent_error_for_retryable_provider_failures(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(),
        ), patch("trading_manager_tasks.stage_reconcile.persist_failure_register_rows") as failure_persist_mock, patch(
            "trading_manager_tasks.stage_reconcile.mark_failure_register_requests_corrected"
        ) as correction_mock:
            with patch("trading_manager_tasks.stage_reconcile.handle_server_error") as error_handoff_mock:
                root = Path(raw_tmp)
                _write_connection_refused_receipt(root, symbol="SPY")
                proposal_path = root / "failure_proposals.jsonl"
                summary = reconcile_provider_stage(
                    stage_id="model_01_background_context.data_acquisition",
                    start_month="2016-01",
                    end_month="2016-01",
                    component_storage_root=root,
                    failure_proposal_path=proposal_path,
                    write_failure_proposal=True,
                    persist_failure_register=True,
                    locks_dir=root / "locks",
                )

            self.assertEqual(summary.failure_proposal_count, 1)
            self.assertIsNone(summary.agent_error_ref)
            row = json.loads(proposal_path.read_text(encoding="utf-8").strip())
            self.assertEqual(row["failure_status"], "retry_required")
            self.assertEqual(row["failure_kind"], "provider_service_unavailable")
            correction_mock.assert_called_once()
            failure_persist_mock.assert_called_once()
            error_handoff_mock.assert_not_called()

    def test_reconcile_can_write_coverage_and_advance_workflow_only_from_written_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(),
        ), patch("trading_manager_tasks.stage_reconcile.persist_completion_rows") as persist_mock, patch(
            "trading_manager_tasks.stage_reconcile.advance_workflow_state",
        ) as advance_mock:
            root = Path(raw_tmp)
            _write_receipt(root, symbol="SPY")
            coverage_path = root / "coverage.json"
            summary = reconcile_provider_stage(
                stage_id="model_01_background_context.data_acquisition",
                start_month="2016-01",
                end_month="2016-01",
                component_storage_root=root,
                persist_control_plane=True,
                coverage_report_path=coverage_path,
                write_coverage_report=True,
                advance_workflow=True,
                workflow_state_path=root / "workflow.json",
                write_workflow_state=True,
                locks_dir=root / "locks",
            )

            self.assertTrue(summary.persisted_control_plane)
            self.assertEqual(summary.coverage_report_path, str(coverage_path))
            self.assertTrue(coverage_path.exists())
            self.assertTrue(summary.workflow_advanced)
            persist_mock.assert_called_once()
            advance_mock.assert_called_once()

    def test_option_chain_reconcile_advances_full_target_workflow_by_default(self) -> None:
        stage_id = "model_05_option_expression.option_chain_data_acquisition"
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.stage_reconcile.discover_stage_receipts",
            return_value=(),
        ), patch(
            "trading_manager_tasks.stage_reconcile.collect_stage_coverage",
            return_value=_coverage(stage_id),
        ), patch(
            "trading_manager_tasks.stage_reconcile.advance_workflow_state",
        ) as advance_mock:
            root = Path(raw_tmp)
            coverage_path = root / "coverage.json"
            summary = reconcile_provider_stage(
                stage_id=stage_id,
                start_month="2016-01",
                end_month="2016-06",
                manager_storage_root=root,
                coverage_report_path=coverage_path,
                write_coverage_report=True,
                advance_workflow=True,
                workflow_state_path=root / "workflow.json",
                write_workflow_state=True,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=True,
                locks_dir=root / "locks",
            )

            self.assertTrue(summary.workflow_advanced)
            advance_mock.assert_called_once()
            self.assertFalse(advance_mock.call_args.kwargs["foundation_catch_up_only"])


if __name__ == "__main__":
    unittest.main()

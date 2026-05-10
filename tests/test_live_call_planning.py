from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.live_call_planning import plan_live_call_approval_proposal, validate_live_call_approval_against_proposal
from trading_manager_tasks.monthly_backfill import LAYER_TWO_MODEL_LAYER


def _reviewed_approval(proposal):
    template = dict(proposal.approval_template)
    template.update(
        {
            "approval_id": "lcav1_reviewed_test",
            "decision_status": "approved",
            "approved_by": "reviewer-agent",
            "approved_at_utc": "2026-05-10T12:00:00Z",
            "expires_at_utc": "2026-05-11T12:00:00Z",
        }
    )
    return template


class LiveCallApprovalPlanningTests(unittest.TestCase):
    def test_layer_two_proposal_excludes_registered_accepted_skips(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=(
                (
                    "mgrreq_backfill_alpaca_bars_aiq_2016_01",
                    "mgrreq_backfill_alpaca_bars_arkf_2016_01",
                    "mgrreq_backfill_alpaca_bars_arkx_2016_01",
                    "mgrreq_backfill_alpaca_bars_bkch_2016_01",
                ),
                ("review://layer2-preflight",),
            ),
        ):
            proposal = plan_live_call_approval_proposal(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=Path(raw_tmp),
                limit=6,
            )

        self.assertEqual(proposal.contract_type, "manager_live_call_approval_proposal_v1")
        self.assertEqual(proposal.stage_id, "layer_02_sector_context.data_acquisition")
        self.assertEqual(proposal.request_ids, ("mgrreq_backfill_alpaca_bars_arkg_2016_01", "mgrreq_backfill_alpaca_bars_arkw_2016_01"))
        self.assertEqual(proposal.skipped_registered_count, 4)
        self.assertEqual(proposal.request_count, 2)
        self.assertEqual(proposal.provider_calls, 0)
        self.assertFalse(proposal.dispatch_performed)
        self.assertEqual(proposal.approval_template["decision_status"], "REVIEW_REQUIRED_REPLACE_WITH_APPROVED")
        self.assertEqual(proposal.approval_template["max_requests"], 2)
        self.assertIn("--skip-registered-failures", proposal.dispatch_plan_command)
        self.assertNotIn("--execute-approved-provider-calls", proposal.dispatch_plan_command)
        self.assertIn("--execute-approved-provider-calls", proposal.dispatch_execute_command_template)

    def test_reviewed_approval_validates_exactly_against_proposal(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=((), ()),
        ):
            proposal = plan_live_call_approval_proposal(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=Path(raw_tmp),
                symbols=("XLK", "XLE", "XLB"),
            )

        validation = validate_live_call_approval_against_proposal(
            proposal.summary_row(),
            _reviewed_approval(proposal),
            now_utc=datetime(2026, 5, 10, 13, 0, tzinfo=UTC),
        )

        self.assertEqual(validation.contract_type, "manager_live_call_approval_proposal_validation_v1")
        self.assertEqual(validation.model_layer, LAYER_TWO_MODEL_LAYER)
        self.assertEqual(validation.stage_id, "layer_02_sector_context.data_acquisition")
        self.assertEqual(validation.request_count, 3)
        self.assertEqual(validation.gate_validation_count, 3)
        self.assertEqual(validation.provider_calls, 0)
        self.assertFalse(validation.dispatch_performed)

    def test_reviewed_approval_rejects_extra_request_not_in_proposal(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=((), ()),
        ):
            proposal = plan_live_call_approval_proposal(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=Path(raw_tmp),
                symbols=("XLK", "XLE"),
            )
        approval = _reviewed_approval(proposal)
        approval["request_ids"] = [*proposal.request_ids, "mgrreq_backfill_alpaca_bars_xlv_2016_01"]
        approval["max_requests"] = len(approval["request_ids"])

        with self.assertRaisesRegex(TaskSystemError, "exactly match proposal"):
            validate_live_call_approval_against_proposal(
                proposal.summary_row(),
                approval,
                now_utc=datetime(2026, 5, 10, 13, 0, tzinfo=UTC),
            )

    def test_reviewed_approval_rejects_registered_skip_overlap(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=((), ()),
        ):
            proposal = plan_live_call_approval_proposal(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=Path(raw_tmp),
                symbols=("XLK",),
            )
        payload = proposal.summary_row()
        payload["skipped_registered_request_ids"] = [proposal.request_ids[0]]

        with self.assertRaisesRegex(TaskSystemError, "registered skip"):
            validate_live_call_approval_against_proposal(
                payload,
                _reviewed_approval(proposal),
                now_utc=datetime(2026, 5, 10, 13, 0, tzinfo=UTC),
            )

    def test_reviewed_approval_rejects_overwide_max_requests(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=((), ()),
        ):
            proposal = plan_live_call_approval_proposal(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=Path(raw_tmp),
                symbols=("XLK",),
            )
        approval = _reviewed_approval(proposal)
        approval["max_requests"] = 10

        with self.assertRaisesRegex(TaskSystemError, "proposal request_count"):
            validate_live_call_approval_against_proposal(
                proposal.summary_row(),
                approval,
                now_utc=datetime(2026, 5, 10, 13, 0, tzinfo=UTC),
            )

    def test_all_registered_skips_do_not_need_live_approval(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=(("mgrreq_backfill_alpaca_bars_aiq_2016_01",), ("review://layer2-preflight",)),
        ):
            with self.assertRaisesRegex(TaskSystemError, "all selected requests are registered accepted skips"):
                plan_live_call_approval_proposal(
                    model_layer=LAYER_TWO_MODEL_LAYER,
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=Path(raw_tmp),
                    symbols=("AIQ",),
                )


if __name__ == "__main__":
    unittest.main()

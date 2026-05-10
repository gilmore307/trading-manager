from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.live_call_planning import plan_live_call_approval_proposal
from trading_manager_tasks.monthly_backfill import LAYER_TWO_MODEL_LAYER


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

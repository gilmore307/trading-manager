from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.live_call_packet import create_live_call_approval_packet
from trading_manager_tasks.monthly_backfill import LAYER_TWO_MODEL_LAYER


class LiveCallApprovalPacketTests(unittest.TestCase):
    def test_packet_writes_proposal_placeholder_and_command_bundle_without_provider_calls(self):
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
                symbols=("XLK", "XLE", "XLB"),
                write=True,
            )

            packet_path = Path(packet.packet_dir) / "packet.json"
            proposal_path = Path(packet.proposal_path)
            approval_path = Path(packet.reviewed_approval_template_path)
            readme_path = Path(packet.packet_dir) / "README.md"

            self.assertTrue(packet_path.exists())
            self.assertTrue(proposal_path.exists())
            self.assertTrue(approval_path.exists())
            self.assertTrue(readme_path.exists())
            payload = json.loads(packet_path.read_text(encoding="utf-8"))

        self.assertEqual(packet.contract_type, "manager_live_call_approval_packet_v1")
        self.assertEqual(packet.request_count, 3)
        self.assertEqual(packet.provider_calls, 0)
        self.assertFalse(packet.dispatch_performed)
        self.assertIn("validate_live_call_approval_proposal.py", " ".join(packet.validate_approval_command))
        self.assertIn("--approval-validation", packet.dispatch_plan_command)
        self.assertIn("--execute-approved-provider-calls", packet.dispatch_execute_command_template)
        self.assertIn("reconcile_provider_stage.py", " ".join(packet.reconcile_command_template))
        self.assertEqual(payload["packet_id"], packet.packet_id)
        self.assertEqual(payload["provider_calls"], 0)

    def test_packet_excludes_registered_skips_before_building_commands(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.live_call_planning.accepted_failure_request_ids_from_register",
            return_value=(("mgrreq_backfill_alpaca_bars_xlk_2016_01",), ("review://skip",)),
        ):
            packet = create_live_call_approval_packet(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=Path(raw_tmp) / "manager_storage",
                packet_root=Path(raw_tmp) / "packets",
                symbols=("XLK", "XLE"),
                write=False,
            )

        self.assertEqual(packet.request_count, 1)
        self.assertEqual(packet.skipped_registered_count, 1)
        self.assertEqual(packet.proposal_request_ids, ("mgrreq_backfill_alpaca_bars_xle_2016_01",))
        self.assertEqual(packet.skipped_registered_request_ids, ("mgrreq_backfill_alpaca_bars_xlk_2016_01",))
        self.assertNotIn("mgrreq_backfill_alpaca_bars_xlk_2016_01", packet.dispatch_execute_command_template)


if __name__ == "__main__":
    unittest.main()

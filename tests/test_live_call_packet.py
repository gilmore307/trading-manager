from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.live_call_packet import create_live_call_approval_packet, inspect_live_call_approval_packet
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
        self.assertIn("--write", packet.dispatch_plan_command)
        self.assertIn(str(Path(packet.dispatch_plan_output_path)), packet.dispatch_plan_command)
        self.assertIn("inspect_live_call_approval_packet.py", " ".join(packet.inspect_status_command))

    def test_packet_status_progresses_from_review_template_to_reconciled(self):
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
                symbols=("XLK", "XLE"),
                write=True,
            )
            packet_path = Path(packet.packet_dir) / "packet.json"
            status = inspect_live_call_approval_packet(packet_path=packet_path)
            self.assertEqual(status.status, "template_pending_review")
            self.assertFalse(status.can_validate_approval)

            approval = json.loads(Path(packet.reviewed_approval_template_path).read_text(encoding="utf-8"))
            approval.update(
                {
                    "approval_id": "lcav1_layer2_packet_unit",
                    "decision_status": "approved",
                    "approved_by": "unit-test",
                    "approved_at_utc": "2026-05-10T00:00:00Z",
                    "expires_at_utc": "2026-05-11T00:00:00Z",
                }
            )
            approval.pop("review_note", None)
            Path(packet.reviewed_approval_template_path).write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            status = inspect_live_call_approval_packet(packet_path=packet_path)
            self.assertEqual(status.status, "approval_ready_pending_validation")
            self.assertTrue(status.can_validate_approval)

            Path(packet.validation_output_path).write_text(
                json.dumps(
                    {
                        "contract_type": "manager_live_call_approval_proposal_validation_v1",
                        "approval_id": "lcav1_layer2_packet_unit",
                        "stage_id": packet.stage_id,
                        "request_ids": list(packet.proposal_request_ids),
                        "provider_calls": 0,
                        "dispatch_performed": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = inspect_live_call_approval_packet(packet_path=packet_path)
            self.assertEqual(status.status, "approval_validated_pending_dispatch_plan")
            self.assertTrue(status.can_plan_dispatch)

            Path(packet.dispatch_plan_output_path).write_text(
                json.dumps(
                    {
                        "contract_type": "manager_provider_dispatch_summary_v1",
                        "dispatch_performed": False,
                        "provider_calls": 0,
                        "items": [{"request_id": request_id} for request_id in packet.proposal_request_ids],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = inspect_live_call_approval_packet(packet_path=packet_path)
            self.assertEqual(status.status, "dispatch_plan_ready_pending_execute")
            self.assertTrue(status.can_execute_dispatch)

            Path(packet.dispatch_execute_output_path).write_text(
                json.dumps(
                    {
                        "contract_type": "manager_provider_dispatch_summary_v1",
                        "dispatch_performed": True,
                        "provider_calls": 2,
                        "items": [{"request_id": request_id} for request_id in packet.proposal_request_ids],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = inspect_live_call_approval_packet(packet_path=packet_path)
            self.assertEqual(status.status, "executed_pending_reconcile")
            self.assertTrue(status.can_reconcile)

            Path(packet.reconcile_summary_output_path).write_text(
                json.dumps(
                    {
                        "contract_type": "manager_provider_stage_reconcile_v1",
                        "stage_id": packet.stage_id,
                        "start_month": packet.start_month,
                        "provider_calls": 0,
                        "dispatch_performed": False,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            status = inspect_live_call_approval_packet(packet_path=packet_path)
            self.assertEqual(status.status, "reconciled")
            self.assertTrue(status.reconcile_ready)

    def test_packet_detects_mismatched_validation_as_inconsistent(self):
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
            approval = json.loads(Path(packet.reviewed_approval_template_path).read_text(encoding="utf-8"))
            approval.update(
                {
                    "approval_id": "lcav1_layer2_packet_unit",
                    "decision_status": "approved",
                    "approved_by": "unit-test",
                    "approved_at_utc": "2026-05-10T00:00:00Z",
                    "expires_at_utc": "2026-05-11T00:00:00Z",
                }
            )
            Path(packet.reviewed_approval_template_path).write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            Path(packet.validation_output_path).write_text(
                json.dumps(
                    {
                        "contract_type": "manager_live_call_approval_proposal_validation_v1",
                        "approval_id": "wrong",
                        "request_ids": list(packet.proposal_request_ids),
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = inspect_live_call_approval_packet(packet_path=Path(packet.packet_dir))

        self.assertEqual(status.status, "packet_inconsistent")
        self.assertTrue(status.inconsistent_reasons)

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

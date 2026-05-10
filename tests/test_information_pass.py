from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from trading_manager_tasks.historical_training import prepare_layer_one_historical_training_batch
from trading_manager_tasks.information_pass import build_controlled_information_pass, collect_resource_snapshot


class ControlledInformationPassTests(unittest.TestCase):
    def test_information_pass_writes_safe_report_and_layer_one_payloads(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            report = build_controlled_information_pass(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=root,
                write=True,
                output_path=root / "runtime" / "information_pass" / "report.json",
            )

            self.assertEqual(report.contract_type, "manager_controlled_information_pass_v1")
            self.assertEqual(report.start_month, "2016-01")
            self.assertTrue(report.wrote_report)
            self.assertEqual(report.provider_calls, 0)
            self.assertFalse(report.model_activation_performed)
            self.assertFalse(report.broker_execution_performed)
            self.assertFalse(report.storage_lifecycle_mutation_performed)
            self.assertEqual(report.dataset_expansion_plan.selected_decision.layer, 1)
            self.assertEqual(report.dataset_expansion_plan.implementation.provider_calls, 0)
            topics = {item.topic for item in report.information_needs}
            self.assertEqual(
                topics,
                {
                    "provider_dispatch_expansion",
                    "concurrency_defaults",
                    "l3_l7_target_queue_rules",
                    "dataset_thresholds",
                    "artifact_discovery",
                    "storage_lifecycle_implementation",
                },
            )
            self.assertTrue((root / "runtime" / "information_pass" / "report.json").exists())
            self.assertTrue((root / "runtime" / "information_pass" / "manager_dataset_expansion_plan.json").exists())
            task_keys = list((root / "monthly_backfill_v1" / "alpaca_bars").glob("*/2016-01/task_key.json"))
            self.assertEqual(len(task_keys), 22)

    def test_information_pass_can_validate_approval_without_dispatching(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            root = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=root,
                write=True,
                validate_handoff=False,
            )
            approval = root / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_information_pass_test",
                        "decision_status": "approved",
                        "approved_by": "unit-test",
                        "approved_at_utc": datetime.now(UTC).isoformat(),
                        "expires_at_utc": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
                        "request_ids": [request["request_id"] for request in requests],
                        "approval_scope": "provider_data_acquisition_only",
                        "broker_execution_allowed": False,
                        "allowed_providers": ["alpaca"],
                        "max_requests": summary.request_count,
                        "max_window_days": 31,
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_controlled_information_pass(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=root,
                approval_path=approval,
                write=False,
            )

            self.assertIsNotNone(report.provider_dispatch_validation)
            self.assertEqual(report.provider_dispatch_validation.validation_count, 22)
            self.assertEqual(report.provider_dispatch_validation.dispatch_count, 0)
            self.assertEqual(report.provider_dispatch_validation.provider_calls, 0)
            self.assertFalse(report.provider_dispatch_validation.dispatch_performed)

    def test_resource_snapshot_is_non_stressful(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            snapshot = collect_resource_snapshot(Path(raw_tmp))
            self.assertEqual(snapshot.storage_root, raw_tmp)
            self.assertIsInstance(snapshot.summary_row(), dict)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from trading_manager_tasks.historical_training import prepare_layer_one_historical_training_batch, prepare_layer_two_historical_training_batch
from trading_manager_tasks.monthly_backfill import LAYER_TWO_MODEL_LAYER
from trading_manager_tasks.provider_dispatch import dispatch_layer_one_provider_acquisition, dispatch_layer_provider_acquisition


class ProviderDispatchTests(unittest.TestCase):
    def test_layer_one_dispatch_validates_approval_without_provider_calls_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_test",
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
            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                approval_path=approval,
                execute_approved_provider_calls=False,
            )
        self.assertEqual(dispatch.contract_type, "manager_provider_dispatch_summary_v1")
        self.assertEqual(dispatch.stage_id, "layer_01_market_regime.data_acquisition")
        self.assertEqual(dispatch.request_count, 22)
        self.assertEqual(dispatch.validation_count, 22)
        self.assertEqual(dispatch.dispatch_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertFalse(dispatch.dispatch_performed)
        self.assertEqual(dispatch.items[0].status, "validated_not_dispatched")
        self.assertIn("data_feed.01_feed_alpaca_bars", dispatch.items[0].command)
        self.assertTrue(Path(dispatch.items[0].task_key_path).is_absolute())

    def test_layer_two_dispatch_validates_approval_without_provider_calls_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_two_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer2_test",
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
            dispatch = dispatch_layer_provider_acquisition(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                approval_path=approval,
                execute_approved_provider_calls=False,
            )
        self.assertEqual(dispatch.stage_id, "layer_02_sector_context.data_acquisition")
        self.assertEqual(dispatch.request_count, 25)
        self.assertEqual(dispatch.validation_count, 25)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertFalse(dispatch.dispatch_performed)
        self.assertTrue(any("XLK/2016-01/task_key.json" in item.task_key_path for item in dispatch.items))

    def test_layer_one_dispatch_can_limit_to_symbol_allowlist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_subset_test",
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

            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                approval_path=approval,
                symbols=("SPY", "QQQ", "TLT"),
                execute_approved_provider_calls=False,
            )

        self.assertEqual(dispatch.request_count, 3)
        self.assertEqual(dispatch.validation_count, 3)
        self.assertEqual(dispatch.dispatch_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        commands = [" ".join(item.command) for item in dispatch.items]
        self.assertTrue(any("SPY/2016-01/task_key.json" in command for command in commands))
        self.assertTrue(any("QQQ/2016-01/task_key.json" in command for command in commands))
        self.assertTrue(any("TLT/2016-01/task_key.json" in command for command in commands))

    def test_layer_one_dispatch_limit_applies_after_filter(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_limit_test",
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

            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                approval_path=approval,
                symbols=("SPY", "QQQ", "TLT"),
                limit=2,
                execute_approved_provider_calls=False,
            )

        self.assertEqual(dispatch.request_count, 2)
        self.assertEqual(dispatch.validation_count, 2)
        self.assertEqual(len(dispatch.items), 2)

    def test_execute_dispatch_can_continue_after_individual_failure(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_continue_test",
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

            with patch(
                "trading_manager_tasks.provider_dispatch.subprocess.run",
                return_value=SimpleNamespace(returncode=1, stdout="", stderr="component failed"),
            ):
                dispatch = dispatch_layer_one_provider_acquisition(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    approval_path=approval,
                    trading_data_root=tmp,
                    symbols=("SPY",),
                    execute_approved_provider_calls=True,
                    continue_on_error=True,
                )

        self.assertEqual(dispatch.dispatch_count, 1)
        self.assertEqual(dispatch.provider_calls, 1)
        self.assertEqual(dispatch.items[0].status, "dispatched_failed")
        self.assertEqual(dispatch.items[0].return_code, 1)
        self.assertIn("component failed", dispatch.items[0].error_summary or "")

    def test_layer_one_dispatch_skips_registered_accepted_failures(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_skip_registered_test",
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

            with patch(
                "trading_manager_tasks.provider_dispatch.accepted_failure_request_ids_from_register",
                return_value=(("mgrreq_backfill_alpaca_bars_bitw_2016_01",), ("storage://review.json",)),
            ):
                dispatch = dispatch_layer_one_provider_acquisition(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    approval_path=approval,
                    symbols=("BITW",),
                    execute_approved_provider_calls=False,
                    skip_registered_failures=True,
                )

        self.assertEqual(dispatch.request_count, 1)
        self.assertEqual(dispatch.validation_count, 0)
        self.assertEqual(dispatch.dispatch_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertEqual(dispatch.items[0].status, "skipped_registered_accepted_failure")
        self.assertEqual(dispatch.items[0].command, [])
        self.assertIn("storage://review.json", dispatch.items[0].error_summary or "")

    def test_layer_one_dispatch_reports_absolute_source_task_key_paths(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            summary, requests, _payloads, _validations = prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            approval = tmp / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "contract_type": "live_call_approval_v1",
                        "approval_id": "approval_layer1_absolute_path_test",
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

            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                approval_path=approval,
                symbols=("SPY",),
                execute_approved_provider_calls=False,
            )

        self.assertTrue(Path(dispatch.items[0].task_key_path).is_absolute())


if __name__ == "__main__":
    unittest.main()

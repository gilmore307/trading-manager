from __future__ import annotations

import tempfile
import unittest
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from trading_manager_tasks.historical_training import (
    prepare_layer_one_historical_training_batch,
    prepare_layer_two_historical_training_batch,
    prepare_target_local_historical_training_batch,
)
from trading_manager_tasks.monthly_backfill import LAYER_THREE_TARGET_STATE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe
from trading_manager_tasks.provider_dispatch import dispatch_layer_one_provider_acquisition, dispatch_layer_provider_acquisition, select_provider_worker_count
from trading_manager_tasks.request_payloads import ALPACA_BARS_MONTHLY_MAX_PAGES


class ProviderDispatchTests(unittest.TestCase):
    def test_layer_one_dispatch_plans_without_provider_calls_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                execute_provider_calls=False,
            )
        self.assertEqual(dispatch.contract_type, "manager_provider_dispatch_summary")
        self.assertEqual(dispatch.stage_id, "layer_01_market_regime.data_acquisition")
        self.assertEqual(dispatch.request_count, 19)
        self.assertEqual(dispatch.validation_count, 0)
        self.assertEqual(dispatch.dispatch_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertFalse(dispatch.dispatch_performed)
        self.assertEqual(dispatch.worker_selection.selected_worker_count, 0)
        self.assertEqual(dispatch.items[0].status, "validated_not_dispatched")
        self.assertIn("data_feed.01_feed_alpaca_bars", dispatch.items[0].command)
        self.assertTrue(Path(dispatch.items[0].task_key_path).is_absolute())

    def test_layer_two_dispatch_plans_without_provider_calls_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_two_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            dispatch = dispatch_layer_provider_acquisition(
                model_layer=LAYER_TWO_MODEL_LAYER,
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                execute_provider_calls=False,
            )
        self.assertEqual(dispatch.stage_id, "layer_02_sector_context.data_acquisition")
        self.assertEqual(dispatch.request_count, len(load_market_regime_universe(model_layers=(LAYER_TWO_MODEL_LAYER,))))
        self.assertEqual(dispatch.validation_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertFalse(dispatch.dispatch_performed)
        self.assertTrue(any("XLK/2016-01/task_key.json" in item.task_key_path for item in dispatch.items))

    def test_target_local_dispatch_plans_selected_layer_three_target(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_target_local_historical_training_batch(
                start_month="2016-07",
                end_month="2016-07",
                target_symbols=("AAPL",),
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            dispatch = dispatch_layer_provider_acquisition(
                model_layer=LAYER_THREE_TARGET_STATE_MODEL_LAYER,
                start_month="2016-07",
                end_month="2016-07",
                storage_root=tmp,
                target_symbols=("AAPL",),
                execute_provider_calls=False,
            )

        self.assertEqual(dispatch.stage_id, "layer_03_target_state_vector.data_acquisition")
        self.assertEqual(dispatch.request_count, 1)
        self.assertEqual(dispatch.provider_calls, 0)
        self.assertFalse(dispatch.dispatch_performed)
        self.assertEqual(dispatch.items[0].request_id, "mgrreq_backfill_alpaca_bars_aapl_2016_07")
        self.assertIn("AAPL/2016-07/task_key.json", dispatch.items[0].task_key_path)

    def test_layer_one_dispatch_can_limit_to_symbol_allowlist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                symbols=("SPY", "QQQ", "TLT"),
                execute_provider_calls=False,
            )

        self.assertEqual(dispatch.request_count, 3)
        self.assertEqual(dispatch.validation_count, 0)
        self.assertEqual(dispatch.dispatch_count, 0)
        self.assertEqual(dispatch.provider_calls, 0)
        commands = [" ".join(item.command) for item in dispatch.items]
        self.assertTrue(any("SPY/2016-01/task_key.json" in command for command in commands))
        self.assertTrue(any("QQQ/2016-01/task_key.json" in command for command in commands))
        self.assertTrue(any("TLT/2016-01/task_key.json" in command for command in commands))

    def test_layer_one_dispatch_limit_applies_after_filter(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                symbols=("SPY", "QQQ", "TLT"),
                limit=2,
                execute_provider_calls=False,
            )

        self.assertEqual(dispatch.request_count, 2)
        self.assertEqual(dispatch.validation_count, 0)
        self.assertEqual(len(dispatch.items), 2)

    def test_dynamic_worker_selection_uses_load_and_memory_bounds(self):
        with patch("trading_manager_tasks.provider_dispatch.os.cpu_count", return_value=16), patch(
            "trading_manager_tasks.provider_dispatch.os.getloadavg", return_value=(0.2, 0.1, 0.1)
        ), patch("trading_manager_tasks.provider_dispatch._available_memory_mb", return_value=24_000):
            selection = select_provider_worker_count(request_count=10, execute_provider_calls=True, max_workers=4)
        self.assertTrue(selection.dynamic_enabled)
        self.assertEqual(selection.selected_worker_count, 4)
        self.assertEqual(selection.requested_max_workers, 4)

    def test_execute_dispatch_can_use_multiple_provider_worker_threads(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            with patch("trading_manager_tasks.provider_dispatch.os.cpu_count", return_value=16), patch(
                "trading_manager_tasks.provider_dispatch.os.getloadavg", return_value=(0.1, 0.1, 0.1)
            ), patch("trading_manager_tasks.provider_dispatch._available_memory_mb", return_value=24_000), patch(
                "trading_manager_tasks.provider_dispatch.subprocess.run",
                return_value=SimpleNamespace(returncode=0, stdout="", stderr=""),
            ) as run_mock:
                dispatch = dispatch_layer_one_provider_acquisition(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    trading_data_root=tmp,
                    symbols=("SPY", "QQQ", "TLT"),
                    execute_provider_calls=True,
                    max_workers=3,
                )
        self.assertEqual(dispatch.worker_selection.selected_worker_count, 3)
        self.assertEqual(dispatch.dispatch_count, 3)
        self.assertEqual(run_mock.call_count, 3)
        self.assertEqual(
            set(item.request_id for item in dispatch.items),
            {
                "mgrreq_backfill_alpaca_bars_qqq_2016_01",
                "mgrreq_backfill_alpaca_bars_spy_2016_01",
                "mgrreq_backfill_alpaca_bars_tlt_2016_01",
            },
        )

    def test_execute_dispatch_rejects_terminal_coverage_when_enabled(self):
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.provider_dispatch.collect_stage_coverage",
            return_value=SimpleNamespace(
                failed_request_ids=(),
                ready_request_ids=("mgrreq_backfill_alpaca_bars_xlk_2016_01",),
                accepted_failed_request_ids=(),
            ),
        ):
            tmp = Path(raw_tmp)
            prepare_layer_two_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            selected_id = "mgrreq_backfill_alpaca_bars_xlk_2016_01"

            with self.assertRaisesRegex(Exception, "terminal stage requests"):
                dispatch_layer_provider_acquisition(
                    model_layer=LAYER_TWO_MODEL_LAYER,
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    request_ids=(selected_id,),
                    execute_provider_calls=True,
                    reject_terminal_coverage=True,
                )

    def test_execute_dispatch_can_continue_after_individual_failure(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )

            with patch(
                "trading_manager_tasks.provider_dispatch.subprocess.run",
                return_value=SimpleNamespace(returncode=1, stdout="", stderr="component failed"),
            ):
                dispatch = dispatch_layer_one_provider_acquisition(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    trading_data_root=tmp,
                    symbols=("SPY",),
                    execute_provider_calls=True,
                    continue_on_error=True,
                )
            retained_runtime_key_exists = Path(dispatch.items[0].runtime_task_key_path or "").exists()

        self.assertEqual(dispatch.dispatch_count, 1)
        self.assertEqual(dispatch.provider_calls, 1)
        self.assertEqual(dispatch.items[0].status, "dispatched_failed")
        self.assertEqual(dispatch.items[0].return_code, 1)
        self.assertIn("component failed", dispatch.items[0].error_summary or "")
        self.assertTrue(dispatch.items[0].runtime_task_key_retained)
        self.assertTrue(retained_runtime_key_exists)

    def test_execute_dispatch_removes_successful_autonomous_runtime_task_key(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            captured_payloads = []

            def fake_run(command, **_kwargs):
                captured_payloads.append(json.loads(Path(command[3]).read_text(encoding="utf-8")))
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch(
                "trading_manager_tasks.provider_dispatch.subprocess.run",
                side_effect=fake_run,
            ):
                dispatch = dispatch_layer_one_provider_acquisition(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    trading_data_root=tmp,
                    symbols=("SPY",),
                    execute_provider_calls=True,
                )
            retained_runtime_keys = list((tmp / "runtime" / "provider_task_keys").glob("*/task_key.json"))
            payload = captured_payloads[0]
        self.assertEqual(retained_runtime_keys, [])
        self.assertIsNone(dispatch.items[0].runtime_task_key_path)
        self.assertFalse(dispatch.items[0].runtime_task_key_retained)
        self.assertFalse(payload["dry_run"])
        self.assertEqual(payload["production_mode"], "historical_provider_acquisition")
        self.assertTrue(payload["manager_controls"]["allow_live_provider_calls"])
        self.assertTrue(payload["manager_controls"]["autonomous_historical_provider_acquisition"])
        self.assertEqual(payload["manager_controls"]["allowed_providers"], ["alpaca"])
        self.assertEqual(payload["manager_controls"]["allowed_endpoint_families"], ["bars"])
        self.assertEqual(payload["manager_controls"]["max_symbols"], 1)
        self.assertEqual(payload["manager_controls"]["max_requests"], ALPACA_BARS_MONTHLY_MAX_PAGES)
        self.assertEqual(payload["manager_controls"]["max_time_window"], "31d")
        self.assertIn("autonomous_historical_provider_acquisition", payload.get("policy_refs", []))

    def test_layer_one_dispatch_skips_registered_accepted_failures(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            with patch(
                "trading_manager_tasks.provider_dispatch.accepted_failure_request_ids_from_register",
                return_value=(("mgrreq_backfill_alpaca_bars_bitw_2016_01",), ("storage://review.json",)),
            ):
                dispatch = dispatch_layer_one_provider_acquisition(
                    start_month="2016-01",
                    end_month="2016-01",
                    storage_root=tmp,
                    symbols=("BITW",),
                    execute_provider_calls=False,
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
            prepare_layer_one_historical_training_batch(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                write=True,
                validate_handoff=False,
            )
            dispatch = dispatch_layer_one_provider_acquisition(
                start_month="2016-01",
                end_month="2016-01",
                storage_root=tmp,
                symbols=("SPY",),
                execute_provider_calls=False,
            )

        self.assertTrue(Path(dispatch.items[0].task_key_path).is_absolute())


if __name__ == "__main__":
    unittest.main()

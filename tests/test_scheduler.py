from __future__ import annotations

import tempfile
import textwrap
import unittest
from unittest.mock import patch
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from trading_manager_tasks.model_training_workflow import BASE_STACK_LAYER_COUNT
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe
from trading_manager_tasks import scheduler
from trading_manager_tasks.scheduler import (
    ResourceSnapshot,
    SchedulerConfig,
    _execute_autonomous_provider_stage,
    is_regular_us_equity_trading_day,
    live_runtime_historical_task_gate,
    main as scheduler_main,
    market_hours_gate,
    resource_gate,
    run_scheduler_once,
)


class SchedulerTests(unittest.TestCase):
    def _healthy_resource_snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(cpu_count=8, load_1m=1.0, available_memory_mb=32768, free_disk_gb=500.0)

    def _write_task_keys(self, root: Path, *, model_layer: str, month: str = "2016-01") -> None:
        for member in load_market_regime_universe(model_layers=(model_layer,)):
            path = root / "monthly_backfill" / "alpaca_bars" / member.symbol / month / "task_key.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")

    def _fake_data_src(self, tmp: Path) -> Path:
        src = tmp / "trading-data-src"
        package = src / "data_feed" / "01_feed_alpaca_bars"
        package.mkdir(parents=True)
        (src / "data_feed" / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "__init__.py").write_text("\n", encoding="utf-8")
        (package / "pipeline.py").write_text(
            textwrap.dedent(
                """
                from dataclasses import dataclass
                from pathlib import Path

                @dataclass(frozen=True)
                class Context:
                    run_dir: Path

                def build_context(task_key, run_id):
                    if task_key.get('feed') != '01_feed_alpaca_bars':
                        raise ValueError('wrong feed')
                    if not task_key.get('params', {}).get('symbol'):
                        raise ValueError('missing symbol')
                    return Context(Path(task_key['output_root']) / 'runs' / run_id)
                """
            ),
            encoding="utf-8",
        )
        return src

    def test_market_gate_blocks_only_regular_trading_day_protection_window(self):
        monday_market_time = datetime(2026, 5, 11, 14, 0, tzinfo=UTC)  # 10:00 ET Monday.
        result = market_hours_gate(monday_market_time)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "regular_trading_day_market_hours_protection")

        sunday_same_wall_clock_window = datetime(2026, 5, 10, 14, 0, tzinfo=UTC)  # 10:00 ET Sunday.
        result = market_hours_gate(sunday_same_wall_clock_window)
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason_code, "not_regular_trading_day")

        monday_after_close = datetime(2026, 5, 11, 22, 0, tzinfo=UTC)  # 18:00 ET Monday.
        result = market_hours_gate(monday_after_close)
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason_code, "outside_market_hours_protection")

    def test_market_gate_can_be_disabled_for_pre_promotion_full_training(self):
        monday_market_time = datetime(2026, 5, 11, 14, 0, tzinfo=UTC)  # 10:00 ET Monday.
        result = market_hours_gate(monday_market_time, SchedulerConfig(market_hours_protection_enabled=False))
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason_code, "market_hours_protection_disabled_pre_promotion")

    def test_regular_trading_day_excludes_weekends_and_market_holidays(self):
        self.assertFalse(is_regular_us_equity_trading_day(datetime(2026, 5, 10, tzinfo=UTC).date()))
        self.assertFalse(is_regular_us_equity_trading_day(datetime(2026, 1, 1, tzinfo=UTC).date()))
        self.assertFalse(is_regular_us_equity_trading_day(datetime(2018, 12, 5, tzinfo=UTC).date()))
        self.assertTrue(is_regular_us_equity_trading_day(datetime(2026, 5, 11, tzinfo=UTC).date()))

    def test_resource_gate_reserves_live_capacity(self):
        pressure = ResourceSnapshot(cpu_count=2, load_1m=4.0, available_memory_mb=512, free_disk_gb=2.0)
        result = resource_gate(pressure, SchedulerConfig(min_available_memory_mb=2048, min_free_disk_gb=10.0))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "resource_pressure")
        self.assertIn("load_per_cpu", result.reason)
        self.assertIn("available_memory_mb", result.reason)
        self.assertIn("free_disk_gb", result.reason)

    def test_live_runtime_gate_pauses_historical_model_tasks(self):
        result = live_runtime_historical_task_gate(SchedulerConfig(live_runtime_mode_enabled=True))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "live_runtime_historical_model_tasks_paused")

    def test_scheduler_backs_off_historical_tasks_when_live_runtime_enabled(self):
        decision = run_scheduler_once(
            now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
            config=SchedulerConfig(live_runtime_mode_enabled=True, market_hours_protection_enabled=False),
            resource_snapshot=self._healthy_resource_snapshot(),
        )
        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "live_runtime_historical_model_tasks_paused")
        self.assertIsNone(decision.selected_work)

    def test_scheduler_reports_ready_safe_work_without_side_effects(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                storage_root=Path(raw_tmp),
                execute_safe_preparation=False,
            )
        self.assertEqual(decision.decision_status, "ready")
        self.assertEqual(decision.reason_code, "safe_offline_work_ready")
        self.assertEqual(decision.selected_work, "prepare_layer_one_historical_training_batch")
        self.assertEqual(decision.next_internal_stage, "autonomous_historical_provider_acquisition")
        self.assertIsNone(decision.approval_gate_required)
        self.assertIsNotNone(decision.execution_summary)
        self.assertEqual(decision.execution_summary["workflow_plan"]["layer_count"], BASE_STACK_LAYER_COUNT)
        self.assertFalse(decision.dispatch_performed)
        self.assertEqual(decision.provider_calls, 0)
        self.assertEqual(decision.lock_plan["contract_type"], "scheduler_lock_plan")
        self.assertIn("daemon", decision.lock_plan["required_lock_scopes"])

    def test_scheduler_backs_off_during_regular_trading_day_window(self):
        decision = run_scheduler_once(
            now_utc=datetime(2026, 5, 11, 14, 0, tzinfo=UTC),
            resource_snapshot=self._healthy_resource_snapshot(),
        )
        self.assertEqual(decision.decision_status, "backoff")
        self.assertTrue(decision.market_protection_active)
        self.assertEqual(decision.reason_code, "regular_trading_day_market_hours_protection")

    def test_scheduler_allows_training_during_market_hours_when_pre_promotion_gate_disabled(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 11, 14, 0, tzinfo=UTC),
                config=SchedulerConfig(market_hours_protection_enabled=False),
                resource_snapshot=self._healthy_resource_snapshot(),
                storage_root=Path(raw_tmp),
                execute_safe_preparation=False,
            )
        self.assertEqual(decision.decision_status, "ready")
        self.assertFalse(decision.market_protection_active)
        self.assertEqual(decision.reason_code, "safe_offline_work_ready")

    def test_scheduler_executes_safe_preparation_without_provider_dispatch(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                storage_root=tmp / "manager-storage",
                component_src_root=self._fake_data_src(tmp),
                execute_safe_preparation=True,
            )

        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "safe_offline_preparation_executed")
        self.assertEqual(decision.next_internal_stage, "autonomous_historical_provider_acquisition")
        self.assertIsNone(decision.approval_gate_required)
        self.assertEqual(decision.provider_calls, 0)
        self.assertFalse(decision.dispatch_performed)
        self.assertFalse(decision.model_activation_performed)
        self.assertFalse(decision.broker_execution_performed)
        self.assertIsNotNone(decision.execution_summary)
        self.assertEqual(decision.execution_summary["request_count"], 19)
        self.assertEqual(decision.execution_summary["handoff_validation_count"], 19)
        self.assertEqual(decision.execution_summary["workflow_plan"]["layer_count"], BASE_STACK_LAYER_COUNT)
        self.assertEqual(decision.execution_summary["workflow_plan"]["next_stage"]["stage_id"], "model_01_background_context.data_acquisition")

    def test_scheduler_progresses_to_autonomous_provider_acquisition_after_layer_one_payloads_exist(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            self._write_task_keys(tmp / "manager-storage", model_layer=LAYER_ONE_MODEL_LAYER)
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                storage_root=tmp / "manager-storage",
                execute_safe_preparation=False,
            )
        self.assertEqual(decision.decision_status, "ready")
        self.assertEqual(decision.reason_code, "autonomous_provider_stage_ready")
        self.assertEqual(decision.selected_work, "model_01_background_context.data_acquisition")
        self.assertIsNone(decision.approval_gate_required)
        self.assertEqual(decision.execution_summary["workflow_plan"]["layer_count"], BASE_STACK_LAYER_COUNT)
        self.assertEqual(
            decision.lock_plan["required_lock_scopes"],
            ["daemon", "month_stage", "reconcile", "provider_partition"],
        )
        self.assertEqual(
            decision.lock_plan["lock_templates"][0]["lock_key_template"],
            "lock:provider:2016-01:model_01_background_context.data_acquisition:<provider_id>:<partition_id>",
        )

    def test_safe_offline_stage_flag_does_not_execute_provider_acquisition(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            self._write_task_keys(tmp / "manager-storage", model_layer=LAYER_ONE_MODEL_LAYER)
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                storage_root=tmp / "manager-storage",
                execute_safe_offline_stages=True,
            )
        self.assertEqual(decision.decision_status, "ready")
        self.assertEqual(decision.reason_code, "autonomous_provider_stage_ready")
        self.assertFalse(decision.dispatch_performed)
        self.assertEqual(decision.provider_calls, 0)

    def test_scheduler_executes_bounded_autonomous_provider_stage_when_enabled(self):
        fake_summary = {
            "provider_calls": 5,
            "dispatch_performed": True,
            "model_activation_performed": False,
            "broker_execution_performed": False,
            "storage_lifecycle_mutation_performed": False,
        }
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.scheduler._execute_autonomous_provider_stage", return_value=fake_summary
        ) as execute_provider_stage:
            tmp = Path(raw_tmp)
            self._write_task_keys(tmp / "manager-storage", model_layer=LAYER_ONE_MODEL_LAYER)
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                storage_root=tmp / "manager-storage",
                execute_autonomous_provider_stages=True,
                provider_stage_next_limit=5,
                selected_target_symbol="AAPL",
            )
        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.reason_code, "autonomous_provider_stage_executed")
        self.assertEqual(decision.provider_calls, 5)
        self.assertTrue(decision.dispatch_performed)
        self.assertFalse(decision.model_activation_performed)
        self.assertFalse(decision.broker_execution_performed)
        self.assertFalse(decision.storage_lifecycle_mutation_performed)
        execute_provider_stage.assert_called_once()
        self.assertEqual(execute_provider_stage.call_args.kwargs["selected_target_symbol"], "AAPL")

    def test_fold_provider_stage_uses_post_foundation_workflow_plan(self):
        fake_summary = {
            "provider_calls": 0,
            "dispatch_performed": False,
            "model_activation_performed": False,
            "broker_execution_performed": False,
            "storage_lifecycle_mutation_performed": False,
        }
        ready_stage = SimpleNamespace(
            stage_id="model_05_option_expression.option_chain_data_acquisition",
            status="ready",
            command=["prepare-option-chain-source"],
            stage_type="data_acquisition",
        )
        state = SimpleNamespace(
            stages=(ready_stage,),
            summary_row=lambda: {"stages": [{"stage_id": ready_stage.stage_id, "status": ready_stage.status}]},
        )
        plan = SimpleNamespace(
            summary_row=lambda: {"next_stage": {"stage_id": ready_stage.stage_id}},
            next_stage=ready_stage,
            layer_one_task_key_count=99,
            layer_two_task_key_count=99,
        )
        with patch("trading_manager_tasks.scheduler.build_model_training_workflow_plan", return_value=plan), patch(
            "trading_manager_tasks.scheduler.advance_workflow_state", return_value=state
        ), patch("trading_manager_tasks.scheduler.next_ready_or_blocked_stage", return_value=ready_stage), patch(
            "trading_manager_tasks.scheduler.first_blocked_stage", return_value=None
        ), patch("trading_manager_tasks.scheduler._execute_autonomous_provider_stage", return_value=fake_summary) as execute_provider_stage:
            state_path = Path("/tmp/model_training_fold_state_aapl_2016-01_2016-06.json")
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                execute_autonomous_provider_stages=True,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=False,
                state_path=state_path,
            )

        self.assertEqual(decision.decision_status, "executed")
        self.assertEqual(decision.selected_work, "model_05_option_expression.option_chain_data_acquisition")
        self.assertFalse(execute_provider_stage.call_args.kwargs["foundation_catch_up_only"])
        self.assertEqual(execute_provider_stage.call_args.kwargs["state_path"], state_path)

    def test_scheduler_cli_passes_fold_state_path_and_post_foundation_scope(self):
        fake_decision = SimpleNamespace(summary_row=lambda: {"decision_status": "ready"})
        state_path = Path("/tmp/model_training_fold_state_aapl_2016-01_2016-06.json")

        with patch.object(scheduler, "run_scheduler_once", return_value=fake_decision) as run_mock, patch.object(
            scheduler, "write_scheduler_decision"
        ):
            status = scheduler_main(
                [
                    "--start-month",
                    "2016-01",
                    "--end-month",
                    "2016-06",
                    "--target-symbol",
                    "AAPL",
                    "--state-path",
                    str(state_path),
                    "--allow-post-foundation-model-stages",
                    "--execute-autonomous-provider-stages",
                ]
            )

        self.assertEqual(status, 0)
        self.assertEqual(run_mock.call_args.kwargs["state_path"], state_path)
        self.assertFalse(run_mock.call_args.kwargs["foundation_catch_up_only"])

    def test_option_chain_provider_execution_advances_full_target_workflow(self):
        state = SimpleNamespace(
            stages=(),
            summary_row=lambda: {"stages": []},
        )
        controller_receipt = SimpleNamespace(
            provider_calls=0,
            dispatch_performed=False,
            model_activation_performed=False,
            broker_execution_performed=False,
            storage_lifecycle_mutation_performed=False,
            summary_row=lambda: {"provider_calls": 0},
        )
        dashboard = SimpleNamespace(summary_row=lambda: {"status": "partial_ready"})
        reconcile_summary = SimpleNamespace(
            summary_row=lambda: {
                "workflow_advanced": True,
                "provider_calls": 0,
                "dispatch_performed": False,
                "model_activation_performed": False,
                "broker_execution_performed": False,
                "storage_lifecycle_mutation_performed": False,
            }
        )
        with tempfile.TemporaryDirectory() as raw_tmp, patch(
            "trading_manager_tasks.scheduler.prepare_option_chain_source_acquisition",
            return_value=(SimpleNamespace(status="ready"), (), ()),
        ), patch(
            "trading_manager_tasks.scheduler.advance_workflow_state",
            return_value=state,
        ) as advance_mock, patch(
            "trading_manager_tasks.scheduler.mark_stage_started",
            return_value=state,
        ), patch(
            "trading_manager_tasks.scheduler.write_workflow_state",
        ), patch(
            "trading_manager_tasks.scheduler.run_stage_controller_step",
            return_value=(controller_receipt, dashboard),
        ), patch(
            "trading_manager_tasks.scheduler.reconcile_provider_stage",
            return_value=reconcile_summary,
        ) as reconcile_mock:
            target_state_path = Path(raw_tmp) / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            _execute_autonomous_provider_stage(
                stage_id="model_05_option_expression.option_chain_data_acquisition",
                start_month="2016-01",
                end_month="2016-06",
                storage_root=Path(raw_tmp),
                component_src_root=Path(raw_tmp) / "trading-data",
                state_path=target_state_path,
                next_limit=5,
                max_workers=1,
                selected_target_symbol="AAPL",
                foundation_catch_up_only=True,
            )

        self.assertEqual(len(advance_mock.call_args_list), 2)
        self.assertTrue(all(not call.kwargs["foundation_catch_up_only"] for call in advance_mock.call_args_list))
        self.assertTrue(all(call.kwargs["state_path"] == target_state_path for call in advance_mock.call_args_list))
        reconcile_mock.assert_called_once()
        self.assertFalse(reconcile_mock.call_args.kwargs["foundation_catch_up_only"])
        self.assertEqual(reconcile_mock.call_args.kwargs["workflow_state_path"], target_state_path)

    def test_scheduler_reports_first_blocked_stage_instead_of_plan_fallback(self):
        blocked_stage = SimpleNamespace(
            stage_id="model_02_target_state.data_acquisition",
            status="blocked",
            blockers=("model_02_target_local_feed_artifacts_ready",),
            command=["materialize-l3"],
            stage_type="data_acquisition",
        )
        state = SimpleNamespace(
            stages=(blocked_stage,),
            summary_row=lambda: {"stages": [{"stage_id": blocked_stage.stage_id, "status": blocked_stage.status}]},
        )
        plan_stage = SimpleNamespace(stage_id="model_01_background_context.data_acquisition", command=["layer1"], stage_type="data_acquisition")
        plan = SimpleNamespace(
            summary_row=lambda: {"next_stage": {"stage_id": plan_stage.stage_id}},
            next_stage=plan_stage,
            layer_one_task_key_count=99,
            layer_two_task_key_count=99,
        )
        with patch("trading_manager_tasks.scheduler.build_model_training_workflow_plan", return_value=plan), patch(
            "trading_manager_tasks.scheduler.advance_workflow_state", return_value=state
        ), patch("trading_manager_tasks.scheduler.next_ready_or_blocked_stage", return_value=None), patch(
            "trading_manager_tasks.scheduler.first_blocked_stage", return_value=blocked_stage
        ):
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                selected_target_symbol=None,
            )

        self.assertEqual(decision.decision_status, "backoff")
        self.assertEqual(decision.reason_code, "workflow_stage_blocked")
        self.assertEqual(decision.selected_work, "model_02_target_state.data_acquisition")
        self.assertEqual(decision.command, ["materialize-l3"])

    def test_scheduler_surfaces_target_local_provider_work_for_layer_three_blocker(self):
        blocked_stage = SimpleNamespace(
            stage_id="model_02_target_state.data_acquisition",
            status="blocked",
            blockers=("model_02_target_local_feed_artifacts_ready",),
            command=["materialize-l3"],
            stage_type="data_acquisition",
        )
        state = SimpleNamespace(
            stages=(blocked_stage,),
            summary_row=lambda: {"stages": [{"stage_id": blocked_stage.stage_id, "status": blocked_stage.status}]},
        )
        plan = SimpleNamespace(
            summary_row=lambda: {"next_stage": None},
            next_stage=None,
            layer_one_task_key_count=99,
            layer_two_task_key_count=99,
        )
        with patch("trading_manager_tasks.scheduler.build_model_training_workflow_plan", return_value=plan), patch(
            "trading_manager_tasks.scheduler.advance_workflow_state", return_value=state
        ), patch("trading_manager_tasks.scheduler.next_ready_or_blocked_stage", return_value=None), patch(
            "trading_manager_tasks.scheduler.first_blocked_stage", return_value=blocked_stage
        ), patch(
            "trading_manager_tasks.scheduler._missing_target_local_feed_months", return_value=("2016-07", "2016-08")
        ):
            decision = run_scheduler_once(
                now_utc=datetime(2026, 5, 10, 14, 0, tzinfo=UTC),
                resource_snapshot=self._healthy_resource_snapshot(),
                selected_target_symbol="AAPL",
                execute_autonomous_provider_stages=False,
            )

        self.assertEqual(decision.decision_status, "ready")
        self.assertEqual(decision.reason_code, "target_local_provider_stage_ready")
        self.assertEqual(decision.selected_work, "model_02_target_state.data_acquisition")
        self.assertEqual(decision.next_internal_stage, "autonomous_target_local_provider_acquisition")
        self.assertIn("--target-symbol", decision.command)


if __name__ == "__main__":
    unittest.main()

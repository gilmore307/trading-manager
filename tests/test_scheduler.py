from __future__ import annotations

import tempfile
import textwrap
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe
from trading_manager_tasks.scheduler import (
    ResourceSnapshot,
    SchedulerConfig,
    is_regular_us_equity_trading_day,
    market_hours_gate,
    resource_gate,
    run_scheduler_once,
)


class SchedulerTests(unittest.TestCase):
    def _healthy_resource_snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(cpu_count=8, load_1m=1.0, available_memory_mb=32768, free_disk_gb=500.0)

    def _write_task_keys(self, root: Path, *, model_layer: str, month: str = "2016-01") -> None:
        for member in load_market_regime_universe(model_layers=(model_layer,)):
            path = root / "monthly_backfill_v1" / "alpaca_bars" / member.symbol / month / "task_key.json"
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
        self.assertTrue(is_regular_us_equity_trading_day(datetime(2026, 5, 11, tzinfo=UTC).date()))

    def test_resource_gate_reserves_live_capacity(self):
        pressure = ResourceSnapshot(cpu_count=2, load_1m=4.0, available_memory_mb=512, free_disk_gb=2.0)
        result = resource_gate(pressure, SchedulerConfig(min_available_memory_mb=2048, min_free_disk_gb=10.0))
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason_code, "resource_pressure")
        self.assertIn("load_per_cpu", result.reason)
        self.assertIn("available_memory_mb", result.reason)
        self.assertIn("free_disk_gb", result.reason)

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
        self.assertEqual(decision.execution_summary["workflow_plan"]["layer_count"], 8)
        self.assertFalse(decision.dispatch_performed)
        self.assertEqual(decision.provider_calls, 0)

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
        self.assertEqual(decision.execution_summary["request_count"], 22)
        self.assertEqual(decision.execution_summary["handoff_validation_count"], 22)
        self.assertEqual(decision.execution_summary["workflow_plan"]["layer_count"], 8)
        self.assertEqual(decision.execution_summary["workflow_plan"]["next_stage"]["stage_id"], "layer_01_market_regime.data_acquisition")

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
        self.assertEqual(decision.reason_code, "workflow_stage_ready")
        self.assertEqual(decision.selected_work, "layer_01_market_regime.data_acquisition")
        self.assertIsNone(decision.approval_gate_required)
        self.assertEqual(decision.execution_summary["workflow_plan"]["layer_count"], 8)


if __name__ == "__main__":
    unittest.main()

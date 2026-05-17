from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import validate

from trading_manager_tasks.scheduler_locks import (
    acquire_scheduler_lock,
    daemon_lock_ref,
    lock_token,
    month_stage_lock_ref,
    promotion_lock_ref,
    provider_partition_lock_ref,
    reconcile_lock_ref,
)


SCHEMA = json.loads(Path("schemas/scheduler_lock.schema.json").read_text(encoding="utf-8"))


class SchedulerLocksTest(unittest.TestCase):
    def test_helper_rows_validate_against_contract_schema(self) -> None:
        refs = [
            daemon_lock_ref(),
            month_stage_lock_ref("2016-01", "layer_01_market_regime.data_acquisition"),
            provider_partition_lock_ref("2016-01", "layer_01_market_regime.data_acquisition", "alpaca", "SPY"),
            reconcile_lock_ref("2016-01", "layer_01_market_regime.data_acquisition"),
            promotion_lock_ref("model_05_alpha_confidence", "candidate_001"),
        ]
        for ref in refs:
            validate(instance=ref.summary_row(), schema=SCHEMA)

    def test_daemon_lock_ref_preserves_current_single_instance_path(self) -> None:
        ref = daemon_lock_ref()
        self.assertEqual(ref.contract_type, "scheduler_lock")
        self.assertEqual(ref.lock_scope, "daemon")
        self.assertEqual(ref.lock_key, "lock:daemon:historical_scheduler")
        self.assertEqual(ref.lock_path, "storage/runtime/historical_scheduler.lock")

    def test_month_stage_and_reconcile_lock_keys_are_distinct(self) -> None:
        stage = month_stage_lock_ref("2016-01", "layer_01_market_regime.data_acquisition")
        reconcile = reconcile_lock_ref("2016-01", "layer_01_market_regime.data_acquisition")
        self.assertEqual(stage.lock_key, "lock:stage:2016-01:layer_01_market_regime.data_acquisition")
        self.assertEqual(reconcile.lock_key, "lock:reconcile:2016-01:layer_01_market_regime.data_acquisition")
        self.assertNotEqual(stage.lock_path, reconcile.lock_path)

    def test_provider_partition_lock_is_partitioned_by_provider_and_symbol(self) -> None:
        spy = provider_partition_lock_ref(
            "2016-01",
            "layer_01_market_regime.data_acquisition",
            "alpaca",
            "SPY",
        )
        qqq = provider_partition_lock_ref(
            "2016-01",
            "layer_01_market_regime.data_acquisition",
            "alpaca",
            "QQQ",
        )
        self.assertEqual(
            spy.lock_key,
            "lock:provider:2016-01:layer_01_market_regime.data_acquisition:alpaca:SPY",
        )
        self.assertNotEqual(spy.lock_path, qqq.lock_path)
        self.assertIn("storage/runtime/locks/provider/2016-01", spy.lock_path)

    def test_promotion_lock_uses_model_and_candidate_identity(self) -> None:
        ref = promotion_lock_ref("model_05_alpha_confidence", "trading-model://promotion-candidates/candidate one")
        self.assertEqual(
            ref.lock_key,
            "lock:promotion:model_05_alpha_confidence:trading-model://promotion-candidates/candidate one",
        )
        self.assertIn("model_05_alpha_confidence", ref.lock_path)
        self.assertIn("trading-model_promotion-candidates_candidate_one.lock", ref.lock_path)

    def test_lock_token_is_filesystem_safe_and_readable(self) -> None:
        self.assertEqual(lock_token("trading-model://promotion-candidates/candidate one"), "trading-model_promotion-candidates_candidate_one")

    def test_invalid_month_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            month_stage_lock_ref("2016-13", "stage")

    def test_acquire_scheduler_lock_creates_and_releases_lock_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            locks_dir = Path(raw_tmp) / "locks"
            ref = month_stage_lock_ref("2016-01", "layer_01_market_regime.data_acquisition", locks_dir=locks_dir)
            path = Path(ref.lock_path)

            with acquire_scheduler_lock(ref):
                self.assertTrue(path.exists())
                with self.assertRaisesRegex(RuntimeError, "scheduler lock is active"):
                    with acquire_scheduler_lock(ref):
                        pass

            self.assertFalse(path.exists())

    def test_lock_paths_can_use_custom_lock_root(self) -> None:
        ref = reconcile_lock_ref("2016-01", "layer_01_market_regime.data_acquisition", locks_dir=Path("runtime/locks"))
        self.assertEqual(ref.lock_path, "runtime/locks/reconcile/2016-01/layer_01_market_regime.data_acquisition.lock")


if __name__ == "__main__":
    unittest.main()

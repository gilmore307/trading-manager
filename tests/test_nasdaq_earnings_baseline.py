import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.nasdaq_earnings_baseline import (
    plan_nasdaq_baseline_snapshot_requests,
    prepare_nasdaq_baseline_snapshots,
)


class NasdaqEarningsBaselineTests(unittest.TestCase):
    def test_plans_one_calendar_discovery_request_per_date(self):
        requests = plan_nasdaq_baseline_snapshot_requests(start_date="2026-05-18", end_date="2026-05-20")
        self.assertEqual(len(requests), 3)
        self.assertEqual({row["target_repo_id"] for row in requests}, {"trading-execution"})
        self.assertEqual({row["target_component_id"] for row in requests}, {"calendar_discovery"})
        self.assertEqual({row["request_kind"] for row in requests}, {"expectation_baseline_snapshot"})
        self.assertTrue(all(row["dry_run"] is True for row in requests))
        self.assertTrue(all("point_in_time_baseline_capture" in row["policy_refs"] for row in requests))

    def test_writes_calendar_discovery_task_keys_without_provider_calls(self):
        with tempfile.TemporaryDirectory() as td:
            summary = prepare_nasdaq_baseline_snapshots(
                start_date="2026-05-18",
                end_date="2026-05-18",
                storage_root=Path(td),
                write_files=True,
            )
            self.assertEqual(summary.task_key_count, 1)
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertFalse(summary.broker_execution_performed)
            payload = json.loads(Path(summary.task_keys[0].local_path).read_text())
            self.assertEqual(payload["bundle"], "calendar_discovery")
            self.assertEqual(payload["params"]["calendar_source"], "nasdaq_earnings_calendar")
            self.assertEqual(payload["params"]["date"], "2026-05-18")
            self.assertEqual(payload["manager_controls"]["allow_live_provider_calls"], False)
            self.assertIn("exclude_eps_actual", payload["manager_controls"]["baseline_use_policy"])


if __name__ == "__main__":
    unittest.main()

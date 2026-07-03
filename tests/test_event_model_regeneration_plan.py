from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.event_model_regeneration_plan import build_event_model_regeneration_plan, write_plan_file


class EventModelRegenerationPlanTests(unittest.TestCase):
    def test_plan_preserves_foundation_and_blocks_storage_cleanup_until_review(self) -> None:
        plan = build_event_model_regeneration_plan(start_month="2016-01", end_month="2016-12", target_symbol="aapl")
        row = plan.summary_row()

        self.assertEqual(row["contract_type"], "manager_event_model_regeneration_plan")
        self.assertEqual(
            row["fold_months"],
            [
                "2016-01",
                "2016-02",
                "2016-03",
                "2016-04",
                "2016-05",
                "2016-06",
                "2016-07",
                "2016-08",
                "2016-09",
                "2016-10",
                "2016-11",
                "2016-12",
            ],
        )
        self.assertIn("model_01_market_context_and_model_01_sector_context_persistent_foundation_data", row["preserved_surfaces"])
        self.assertIn("pre_replay_event_state_outputs_built_from_non_current_event_sources", row["superseded_surfaces"])
        self.assertIn("base-stack and replay outputs remain reusable", row["invalidation_scope"])
        self.assertFalse(row["write_performed"])
        self.assertFalse(row["model_activation_performed"])
        self.assertFalse(row["broker_execution_performed"])
        self.assertFalse(row["storage_lifecycle_mutation_performed"])
        self.assertIn("Do not delete dashboard snapshots", row["storage_cleanup_gate"])

    def test_provider_calls_are_limited_to_explicit_event_feed_dispatch_step(self) -> None:
        plan = build_event_model_regeneration_plan(start_month="2016-01", end_month="2016-01")
        steps = {item["step_id"]: item for item in plan.summary_row()["regeneration_steps"]}

        provider_steps = [step_id for step_id, item in steps.items() if item["provider_calls_allowed"]]
        self.assertEqual(provider_steps, ["03_dispatch_or_verify_event_feed_artifacts"])
        self.assertTrue(steps["03_dispatch_or_verify_event_feed_artifacts"]["requires_review_before_apply"])
        self.assertEqual(steps["08_state_only_invalidation_if_old_outputs_remain"]["mutation_class"], "workflow_state_only_no_artifact_deletion")
        self.assertTrue(steps["09_revisit_storage_lifecycle_hold"]["requires_review_before_apply"])
        self.assertIn("materialize_model_03_event_impact_inputs.py", steps["04_materialize_model_03_event_event_observation_fold_pool"]["command_ref"])
        self.assertEqual(steps["05_run_concentrated_live_flow_replay"]["status"], "blocked_until_model_03_event_event_observation_pool_ready")
        self.assertEqual(steps["06_run_replay_review_event_attribution"]["status"], "blocked_until_model_group_replay_complete")
        self.assertIn("run_model_group_replay_review.py", steps["06_run_replay_review_event_attribution"]["command_ref"])
        self.assertIn("--model model_group", steps["07_evaluate_and_review_without_activation"]["command_ref"])
        self.assertNotIn("--model model_06_residual_event_governance", steps["07_evaluate_and_review_without_activation"]["command_ref"])
        self.assertEqual(steps["07_evaluate_and_review_without_activation"]["status"], "blocked_until_replay_review_event_attribution_ready")

    def test_writes_plan_file(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "plan.json"
            plan = build_event_model_regeneration_plan(start_month="2016-01", end_month="2016-01")
            write_plan_file(plan, path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_type"], "manager_event_model_regeneration_plan")


if __name__ == "__main__":
    unittest.main()

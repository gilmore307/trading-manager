import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.event_family_modelability_acquisition import (
    canonical_event_family_id,
    plan_event_family_modelability_acquisition,
    required_feeds_for_event_family,
)


class EventFamilyModelabilityAcquisitionTests(unittest.TestCase):
    def test_earnings_acquisition_plan_requires_multiple_same_family_observations(self):
        with tempfile.TemporaryDirectory() as td:
            plan = plan_event_family_modelability_acquisition(
                event_family_id="earnings",
                start_month="2024-01",
                end_month="2024-03",
                target_symbol="AAPL",
                target_cik="320193",
                candidate_seed_event_ref="event://aapl/fy2025-q2-10q",
                storage_root=Path(td),
                minimum_same_family_observations=8,
                write_files=True,
            )

            self.assertEqual(plan.contract_type, "model_06_event_family_modelability_acquisition_plan")
            self.assertEqual(plan.event_family_id, "company_earnings_or_financial_results")
            self.assertEqual(plan.minimum_same_family_observations, 8)
            self.assertEqual(plan.provider_calls, 0)
            self.assertFalse(plan.modelability_review_performed)
            self.assertIn("single event is only a candidate seed", plan.single_observation_policy)
            self.assertIn("Program gates own acquisition scope", plan.deterministic_control_policy)
            self.assertIn("semantic reviewers only", plan.agent_role_policy)
            self.assertEqual(
                set(plan.required_feed_ids),
                {"08_feed_sec_company_financials", "03_feed_alpaca_news", "05_feed_gdelt_news"},
            )
            self.assertEqual(plan.task_key_count, 9)

            task_key_path = Path(plan.task_keys[0].local_path)
            self.assertTrue(task_key_path.exists())
            payload = json.loads(task_key_path.read_text(encoding="utf-8"))
            self.assertTrue(payload["dry_run"])

    def test_single_observation_threshold_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(Exception, "requires multiple same-family observations"):
                plan_event_family_modelability_acquisition(
                    event_family_id="earnings",
                    start_month="2024-01",
                    end_month="2024-01",
                    storage_root=Path(td),
                    minimum_same_family_observations=1,
                )

    def test_family_aliases_resolve_to_canonical_routes(self):
        self.assertEqual(canonical_event_family_id("earnings-release"), "company_earnings_or_financial_results")
        self.assertEqual(canonical_event_family_id("cpi"), "cpi_release")
        self.assertEqual(canonical_event_family_id("product-pricing-change"), "target_product_price_change_news")
        self.assertEqual(
            required_feeds_for_event_family("financial_results"),
            ("08_feed_sec_company_financials", "03_feed_alpaca_news", "05_feed_gdelt_news"),
        )

    def test_rejects_source_buckets_as_event_families(self):
        for invalid_family in ("news", "target_news_or_disclosure", "scheduled_macro_release", "macro"):
            with self.subTest(invalid_family=invalid_family):
                with self.assertRaisesRegex(Exception, "not a source/category bucket"):
                    canonical_event_family_id(invalid_family)


if __name__ == "__main__":
    unittest.main()

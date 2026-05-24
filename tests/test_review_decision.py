from __future__ import annotations

import unittest

from trading_manager_tasks.review_decision import (
    build_agent_model_promotion_decision,
    build_review_decision,
    validate_agent_model_promotion_decision,
    validate_review_decision,
)


class ReviewDecisionArtifactTests(unittest.TestCase):
    def test_builds_review_decision_artifact_as_advisory_evidence(self):
        decision = build_review_decision(
            review_target_ref="storage://trading-model/promotion/candidate.json",
            reviewer_ref="openclaw",
            decision_status="defer",
            decision_reason="missing production calibration evidence",
            conditions=["supply_real_sample_eval"],
            evidence_refs=["storage://trading-model/evidence/eval.json"],
            created_at_utc="2026-05-09T08:00:00Z",
        )

        normalized = validate_review_decision(decision)
        self.assertEqual(normalized["contract_type"], "review_decision")
        self.assertEqual(normalized["decision_status"], "defer")
        self.assertEqual(normalized["conditions"], ["supply_real_sample_eval"])

    def test_builds_agent_model_promotion_decision_artifact(self):
        decision = build_agent_model_promotion_decision(
            promotion_request_ref="manager_request://model_01_market_regime",
            agent_ref="codex_cli_gpt_5_5",
            decision_status="defer",
            decision_reason="missing production calibration evidence",
            evidence_refs=["storage://trading-model/evidence/eval.json"],
            advisory_review_refs=["review_decision://candidate_review"],
            conditions=["supply_real_sample_eval"],
            created_at_utc="2026-05-09T08:00:00Z",
        )

        normalized = validate_agent_model_promotion_decision(decision)
        self.assertEqual(normalized["contract_type"], "agent_model_promotion_decision")
        self.assertTrue(normalized["owner_observed_automation"])
        self.assertEqual(normalized["advisory_review_refs"], ["review_decision://candidate_review"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.review_decision import (
    build_activation_record,
    build_agent_model_promotion_decision,
    build_review_decision,
    validate_activation_record,
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
        self.assertEqual(normalized["contract_type"], "review_decision_v1")
        self.assertEqual(normalized["decision_status"], "defer")
        self.assertEqual(normalized["conditions"], ["supply_real_sample_eval"])

    def test_builds_agent_model_promotion_decision_artifact(self):
        decision = build_agent_model_promotion_decision(
            promotion_request_ref="manager_request://model_01_market_regime",
            agent_ref="openclaw_agent_under_owner_observation",
            decision_status="defer",
            decision_reason="missing production calibration evidence",
            evidence_refs=["storage://trading-model/evidence/eval.json"],
            advisory_review_refs=["review_decision://candidate_review"],
            conditions=["supply_real_sample_eval"],
            created_at_utc="2026-05-09T08:00:00Z",
        )

        normalized = validate_agent_model_promotion_decision(decision)
        self.assertEqual(normalized["contract_type"], "agent_model_promotion_decision_v1")
        self.assertTrue(normalized["owner_observed_automation"])
        self.assertEqual(normalized["advisory_review_refs"], ["review_decision://candidate_review"])

    def test_activation_requires_approved_agent_model_promotion_decision(self):
        decision = build_agent_model_promotion_decision(
            promotion_request_ref="manager_request://model_03_target_state_vector",
            agent_ref="openclaw_agent_under_owner_observation",
            decision_status="defer",
            decision_reason="missing production calibration evidence",
        )

        with self.assertRaisesRegex(TaskSystemError, "approving agent_model_promotion_decision_v1"):
            build_activation_record(
                agent_decision=decision,
                activated_component="model_03_target_state_vector",
                activated_config_ref="registry://model-config/new",
                rollback_ref="registry://model-config/old",
                activated_by="openclaw",
            )

    def test_activation_record_links_to_approved_agent_decision(self):
        decision = build_agent_model_promotion_decision(
            promotion_request_ref="manager_request://model_01_market_regime",
            agent_ref="openclaw_agent_under_owner_observation",
            decision_status="approve",
            decision_reason="agent decision found evidence passes accepted gates",
        )

        activation = build_activation_record(
            agent_decision=decision,
            activated_component="model_01_market_regime",
            activated_config_ref="registry://model-config/new",
            replaced_config_ref="registry://model-config/old",
            rollback_ref="registry://model-config/old",
            activated_by="openclaw_agent_under_owner_observation",
        )

        self.assertEqual(activation["contract_type"], "activation_record_v1")
        self.assertEqual(
            activation["approved_agent_model_promotion_decision_ref"],
            decision["agent_model_promotion_decision_id"],
        )
        self.assertEqual(validate_activation_record(activation, agent_decision=decision), activation)


if __name__ == "__main__":
    unittest.main()

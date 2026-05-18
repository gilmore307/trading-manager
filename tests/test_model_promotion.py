from __future__ import annotations

import io
import json
import unittest

from trading_manager_tasks.control_plane import TaskSystemError, validate_manager_request
from trading_manager_tasks.model_promotion import (
    MODEL_PROMOTION_TARGETS,
    REQUEST_KIND,
    build_model_promotion_review_request,
    build_model_promotion_review_requests,
    write_requests,
)


class ModelPromotionRequestTests(unittest.TestCase):
    def test_all_model_layers_use_one_request_kind(self):
        self.assertEqual(len(MODEL_PROMOTION_TARGETS), 9)
        self.assertEqual({target.model_id for target in MODEL_PROMOTION_TARGETS}, {
            "market_regime_model",
            "sector_context_model",
            "target_state_vector_model",
            "event_failure_risk_model",
            "alpha_confidence_model",
            "position_projection_model",
            "underlying_action_model",
            "option_expression_model",
            "event_risk_governor",
        })

        requests = build_model_promotion_review_requests(
            models=[target.model_id for target in MODEL_PROMOTION_TARGETS],
            candidate_ref="trading-model://promotion-candidates/example",
        )
        self.assertEqual({row["request_kind"] for row in requests}, {REQUEST_KIND})
        self.assertEqual({row["target_repo_id"] for row in requests}, {"trading-manager"})
        self.assertEqual({row["target_component_id"] for row in requests}, {"manager_model_promotion_review"})

    def test_builds_valid_manager_request_for_any_model_layer(self):
        request = build_model_promotion_review_request(
            model="layer_09_option_expression",
            candidate_ref="trading-model://promotion-candidates/mpcand_example",
            evaluation_run_refs=["trading-model://eval-runs/mdevrun_example"],
            evidence_refs=["storage://trading-model/evidence/example.json"],
            priority="high",
            deadline_at_utc="2026-05-09T14:30:00Z",
        )

        normalized = validate_manager_request(request)
        self.assertEqual(normalized["request_kind"], "model_promotion_review")
        self.assertEqual(normalized["priority"], "high")
        self.assertEqual(request["model_id"], "option_expression_model")
        self.assertEqual(request["model_layer"], "layer_09_option_expression")
        self.assertEqual(request["output_contract"], "option_expression_plan")
        self.assertEqual(request["candidate_ref"], "trading-model://promotion-candidates/mpcand_example")
        self.assertEqual(request["evaluation_run_refs"], ["trading-model://eval-runs/mdevrun_example"])
        self.assertIn("model_promotion_unified_review", request["policy_refs"])
        self.assertIn("model_promotion_script_called_agent_decision", request["policy_refs"])
        self.assertIn("model_promotion_no_activation_without_agent_decision", request["policy_refs"])
        self.assertIn("agent_model_promotion_decision", request["expected_outputs"])
        self.assertIn("activation_record_if_agent_approved", request["expected_outputs"])


    def test_accepts_layer_or_stable_model_ids_for_current_surfaces(self):
        request = build_model_promotion_review_request(
            model="option_expression_model",
            candidate_ref="trading-model://promotion-candidates/mpcand_example",
        )

        self.assertEqual(request["model_id"], "option_expression_model")
        self.assertEqual(request["model_layer"], "layer_09_option_expression")
        self.assertEqual(request["evidence_component_id"], "option_expression_model")

    def test_rejects_unknown_model_target(self):
        with self.assertRaises(TaskSystemError):
            build_model_promotion_review_request(
                model="unknown_event_risk_governor",
                candidate_ref="trading-model://promotion-candidates/mpcand_example",
            )

    def test_write_jsonl_keeps_single_entrypoint_shape(self):
        request = build_model_promotion_review_request(
            model="market_regime_model",
            candidate_ref="trading-model://promotion-candidates/mpcand_example",
        )
        buffer = io.StringIO()

        write_requests([request], output=buffer, output_format="jsonl")

        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["request_kind"], "model_promotion_review")
        self.assertEqual(payload["target_component_kind"], "review_helper")
        self.assertTrue(payload["parameter_ref"].startswith("storage://trading-manager/model_promotion/market_regime_model/"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.layer_four_event_failure_features import materialize_layer_four_event_failure_features


class LayerFourEventFailureFeatureTests(unittest.TestCase):
    def test_empty_observation_payload_writes_neutral_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            receipt = materialize_layer_four_event_failure_features(
                start_month="2016-01",
                end_month="2016-06",
                input_root=tmp / "missing",
                output_root=tmp / "output",
                write=True,
            )

            self.assertEqual(receipt.event_feature_state, "no_reviewed_event_interpretations")
            self.assertEqual(receipt.target_routed_gate_row_count, 0)
            self.assertEqual(Path(str(receipt.feature_rows_path)).read_text(encoding="utf-8"), "")

    def test_accepted_routed_interpretation_becomes_gate_row(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            input_root = tmp / "input"
            input_root.mkdir()
            (input_root / "2016-01_2016-06.json").write_text(
                json.dumps(
                    {
                        "reviewed_event_interpretations": [
                            {
                                "schema_version": "event_interpretation_v1",
                                "review_status": "accepted",
                                "standardization_status": "standardized",
                                "available_time": "2016-01-04T10:00:00-05:00",
                                "target_candidate_id": "tcand_test",
                                "normalized_event_type": "earnings_guidance_event_family",
                                "intensity_score": 0.8,
                                "uncertainty_score": 0.2,
                                "novelty_score": 0.7,
                                "evidence_confidence_score": 0.9,
                                "source_artifact_ref": "fixture",
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            receipt = materialize_layer_four_event_failure_features(
                start_month="2016-01",
                end_month="2016-06",
                input_root=input_root,
                output_root=tmp / "output",
                write=True,
            )

            self.assertEqual(receipt.event_feature_state, "target_routed_event_failure_gate_rows_ready")
            self.assertEqual(receipt.target_routed_gate_row_count, 1)
            rows = [json.loads(line) for line in Path(str(receipt.feature_rows_path)).read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[0]["target_candidate_id"], "tcand_test")
            self.assertEqual(rows[0]["event_strategy_failure_gate"]["agent_review_decision"], "accept_layer_04_event_failure_risk_scope")


if __name__ == "__main__":
    unittest.main()

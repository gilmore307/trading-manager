import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.dataset_expansion import (
    DatasetRoleEvidence,
    LayerDatasetEvidence,
    build_dataset_expansion_plan,
    decide_dataset_expansion,
    load_dataset_evidence,
)


class DatasetExpansionTests(unittest.TestCase):
    def empty_evidence(self):
        return tuple(
            LayerDatasetEvidence(layer=layer, layer_key=f"layer_{layer:02d}_test", roles=())
            for layer in range(1, 9)
        )

    def complete_layer(self, layer: int, *, gaps=(), approved=False):
        return LayerDatasetEvidence(
            layer=layer,
            layer_key=f"layer_{layer:02d}_test",
            roles=(
                DatasetRoleEvidence("train", month_count=60),
                DatasetRoleEvidence("calibration", month_count=12),
                DatasetRoleEvidence("validation", month_count=12),
                DatasetRoleEvidence("test", month_count=12),
            ),
            promotion_gaps=tuple(gaps),
            production_approved=approved,
        )

    def test_manager_selects_layer_one_train_when_no_evidence_exists(self):
        decision = decide_dataset_expansion(self.empty_evidence())

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 1)
        self.assertEqual(decision.dataset_role, "train")
        self.assertEqual(decision.action, "prepare_layer_one_historical_training_batch")
        self.assertIsNone(decision.approval_gate_required)
        self.assertFalse(decision.safe_without_provider_calls)
        self.assertTrue(decision.provider_calls_allowed)
        self.assertFalse(decision.model_activation_allowed)
        self.assertFalse(decision.broker_execution_allowed)

    def test_manager_fills_calibration_before_validation_or_test(self):
        evidence = list(self.empty_evidence())
        evidence[0] = LayerDatasetEvidence(
            layer=1,
            layer_key="layer_01_market_regime",
            roles=(DatasetRoleEvidence("train", month_count=60),),
        )

        decision = decide_dataset_expansion(tuple(evidence))

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 1)
        self.assertEqual(decision.dataset_role, "calibration")

    def test_manager_blocks_downstream_until_upstream_minimum_roles_are_complete(self):
        evidence = list(self.empty_evidence())
        evidence[0] = self.complete_layer(1)
        # Layer 2 is incomplete, so manager should expand Layer 2 before Layer 3.

        decision = decide_dataset_expansion(tuple(evidence))

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 2)
        self.assertEqual(decision.dataset_role, "train")

    def test_manager_expands_forward_holdout_for_split_stability_gap(self):
        evidence = [self.complete_layer(layer) for layer in range(1, 9)]
        evidence[2] = self.complete_layer(3, gaps=("split_stability",))

        decision = decide_dataset_expansion(tuple(evidence))

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 3)
        self.assertEqual(decision.dataset_role, "forward_holdout")
        self.assertIn("split_stability", decision.reason)

    def test_write_prepares_layer_one_payloads_without_provider_calls(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            plan = build_dataset_expansion_plan(
                start_month="2016-01",
                end_month="2016-01",
                evidence=self.empty_evidence(),
                storage_root=root,
                write=True,
                output_path=root / "runtime" / "dataset_expansion" / "plan.json",
            )

            self.assertEqual(plan.selected_decision.layer, 1)
            self.assertEqual(plan.implementation.status, "prepared")
            self.assertTrue(plan.implementation.wrote_layer_one_payloads)
            self.assertEqual(plan.implementation.provider_calls, 0)
            self.assertFalse(plan.implementation.model_activation_performed)
            self.assertFalse(plan.implementation.broker_execution_performed)
            self.assertTrue((root / "runtime" / "dataset_expansion" / "plan.json").exists())
            task_keys = list((root / "monthly_backfill" / "alpaca_bars").glob("*/2016-01/task_key.json"))
            self.assertEqual(len(task_keys), 22)

    def test_load_dataset_evidence_from_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "evidence.json"
            path.write_text(
                json.dumps(
                    {
                        "layers": {
                            "1": {
                                "roles": {"train": {"month_count": 60, "sample_count": 1000}},
                                "promotion_gaps": ["coverage"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )

            evidence = load_dataset_evidence(path)

            self.assertEqual(evidence[0].role("train").month_count, 60)
            self.assertEqual(evidence[0].promotion_gaps, ("coverage",))
            self.assertEqual(len(evidence), 8)


if __name__ == "__main__":
    unittest.main()

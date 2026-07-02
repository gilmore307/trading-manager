import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.dataset_expansion import (
    DatasetRoleEvidence,
    LayerDatasetEvidence,
    build_dataset_expansion_plan,
    decide_dataset_expansion,
    DATASET_EXPANSION_LAYERS,
    load_dataset_evidence,
)


class DatasetExpansionTests(unittest.TestCase):
    def empty_evidence(self):
        return tuple(
            LayerDatasetEvidence(layer=layer, layer_key=f"layer_{layer:02d}_test", roles=())
            for layer in DATASET_EXPANSION_LAYERS
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

    def test_panel_layers_do_not_inherit_selected_target_symbol(self):
        decision = decide_dataset_expansion(self.empty_evidence(), selected_target_symbol="AAPL")

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 1)
        self.assertEqual(decision.dataset_unit_kind, "walk_forward_12_3_3_panel")
        self.assertFalse(decision.target_required)
        self.assertIsNone(decision.target_symbol)
        self.assertIn("fixed M01 panel", decision.task_scope_description)

        plan = build_dataset_expansion_plan(
            start_month="2016-01",
            end_month="2016-12",
            evidence=self.empty_evidence(),
            selected_target_symbol="AAPL",
        )
        self.assertIsNone(plan.selected_target_symbol)
        self.assertIsNone(plan.selected_decision.target_symbol)

    def test_manager_fills_calibration_before_validation_or_test(self):
        evidence = list(self.empty_evidence())
        evidence[0] = LayerDatasetEvidence(
            layer=1,
            layer_key="model_01_market_context",
            roles=(DatasetRoleEvidence("train", month_count=60),),
        )

        decision = decide_dataset_expansion(tuple(evidence))

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 1)
        self.assertEqual(decision.dataset_role, "calibration")

    def test_manager_blocks_downstream_until_upstream_minimum_roles_are_complete(self):
        evidence = list(self.empty_evidence())
        evidence[0] = self.complete_layer(1)
        # M02 is incomplete, so manager should expand M02 before M02.

        decision = decide_dataset_expansion(tuple(evidence))

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 2)
        self.assertEqual(decision.dataset_role, "train")

    def test_manager_expands_forward_holdout_for_split_stability_gap(self):
        evidence = [self.complete_layer(layer) for layer in DATASET_EXPANSION_LAYERS]
        evidence[2] = self.complete_layer(3, gaps=("split_stability",))

        decision = decide_dataset_expansion(tuple(evidence), selected_target_symbol="AAPL")

        self.assertIsNotNone(decision)
        self.assertEqual(decision.layer, 3)
        self.assertEqual(decision.dataset_role, "forward_holdout")
        self.assertEqual(decision.dataset_unit_kind, "target_symbol_walk_forward_12_3_3")
        self.assertEqual(decision.dataset_unit_months, 18)
        self.assertEqual(decision.target_symbol, "AAPL")
        self.assertIn("target AAPL over 18 months", decision.task_scope_description)
        self.assertIn("split_stability", decision.reason)

    def test_later_layer_expansion_blocks_until_target_symbol_is_named(self):
        evidence = [self.complete_layer(layer) for layer in DATASET_EXPANSION_LAYERS]
        evidence[2] = self.complete_layer(3, gaps=("coverage",))

        plan = build_dataset_expansion_plan(
            start_month="2016-01",
            end_month="2016-12",
            evidence=tuple(evidence),
            write=True,
        )

        self.assertEqual(plan.selected_decision.layer, 3)
        self.assertEqual(plan.selected_decision.action, "select_target_symbol_for_walk_forward_unit")
        self.assertTrue(plan.selected_decision.target_required)
        self.assertIsNone(plan.selected_decision.target_symbol)
        self.assertEqual(plan.implementation.status, "blocked")
        self.assertIn("target symbol", plan.implementation.note)

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
            self.assertEqual(len(task_keys), 19)

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
            self.assertEqual(len(evidence), len(DATASET_EXPANSION_LAYERS))


if __name__ == "__main__":
    unittest.main()

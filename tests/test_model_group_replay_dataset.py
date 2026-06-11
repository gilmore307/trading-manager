from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_replay_dataset import run_model_group_replay_dataset_if_ready


class ModelGroupReplayDatasetTests(unittest.TestCase):
    def _write_completed_fold(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True)
        stages = []
        for layer in range(1, 7):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"layer_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"layer_{layer:02d}_fixture",
                        "status": "succeeded",
                        "dataset_split": {
                            "split_name": split_name,
                            "split_policy": "chronological_rolling_fold_4_1_1",
                        },
                    }
                )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": "2016-01",
                    "end_month": "2016-06",
                    "target_symbol": "AAPL",
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        artifact_path = (
            storage_root.parent
            / "03_model_artifacts"
            / "runtime"
            / "model_05_option_expression"
            / "option_expression_model_aapl_2016-01_2016-06.json"
        )
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text('{"artifacts_by_horizon": {}}\n', encoding="utf-8")

    def _write_contract(self, path: Path, *, base_context_ref: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "baseline_refs": ["baseline://active_model", "baseline://no_trade"],
                    "replay_mode": "candidate_policy_replay",
                    "candidate_policy_ref": "trading-model://layer_03_target_candidate_universe_policy/live_equivalent",
                    "contract_id": "promotion_replay_candidate_policy",
                    "cost_model_ref": "storage://replay/promotion_replay_candidate_policy/cost_model/pending_review",
                    "data_snapshot_ref": "storage://replay/promotion_replay_candidate_policy/data_snapshot/pending_materialization",
                    "end_date": "2026-01-01",
                    "excluded_training_windows": [
                        {
                            "end_date": "2026-01-01",
                            "reason": "canonical promotion replay holdout",
                            "start_date": "2021-01-01",
                        }
                    ],
                    "guardrail_refs": ["replay://guardrail/liquidity_regime"],
                    "market_condition_tags": ["trend_up", "drawdown", "high_volatility", "event_shock"],
                    "min_trading_days": 1255,
                    "replay_route_ref": "trading-execution://execution_runtime_component_graph/replay",
                    "selection_metric_refs": [
                        "metric://net_return_after_costs",
                        "metric://max_drawdown",
                        "metric://selection_hit_rate",
                    ],
                    "start_date": "2021-01-01",
                    "base_context_policy_ref": "trading-model://layer_03_target_candidate_universe_policy/live_equivalent",
                    "base_context_ref": str(base_context_ref),
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_prepare_script(self, path: Path, *, missing_count: int) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            textwrap.dedent(
                f"""
                import argparse
                import json
                from pathlib import Path

                parser = argparse.ArgumentParser()
                parser.add_argument("--contract")
                parser.add_argument("--candidate-fold-id")
                parser.add_argument("--base-context-ref")
                parser.add_argument("--output-root")
                parser.add_argument("--data-root")
                args = parser.parse_args()
                dataset_root = Path(args.output_root) / "promotion_replay_candidate_policy"
                dataset_root.mkdir(parents=True, exist_ok=True)
                manifest = {{
                    "contract_type": "replay_dataset_preparation_manifest",
                    "contract_id": "promotion_replay_candidate_policy",
                    "freeze_status": "not_frozen",
                    "missing_feed_acquisition_count": {missing_count},
                    "feed_acquisition_plan_ref": str(dataset_root / "feed_acquisition_plan.csv"),
                    "candidate_fold_id": args.candidate_fold_id,
                    "pre_replay_target_refs": ["AAPL"],
                }}
                (dataset_root / "dataset_manifest.json").write_text(json.dumps(manifest) + "\\n", encoding="utf-8")
                (dataset_root / "feed_acquisition_plan.csv").write_text("acquisition_id,source_id,coverage_status,target_ref\\n", encoding="utf-8")
                (dataset_root / "coverage_summary.csv").write_text("contract_id,source_id,required_acquisition_count,available_acquisition_count,deferred_acquisition_count,missing_acquisition_count,coverage_status,notes\\n", encoding="utf-8")
                print(json.dumps(manifest))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return path

    def _write_freeze_script(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            textwrap.dedent(
                """
                import argparse
                import json
                from pathlib import Path

                parser = argparse.ArgumentParser()
                parser.add_argument("--dataset-root")
                args = parser.parse_args()
                dataset_root = Path(args.dataset_root)
                manifest_path = dataset_root / "dataset_manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["freeze_status"] = "frozen"
                receipt = {"freeze_status": "frozen", "validation": {"validation_status": "passed"}}
                manifest_path.write_text(json.dumps(manifest) + "\\n", encoding="utf-8")
                (dataset_root / "replay_freeze_receipt.json").write_text(json.dumps(receipt) + "\\n", encoding="utf-8")
                print(json.dumps(receipt))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_prepares_base_context_and_freezes_dataset(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_completed_fold(storage_root)
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            contract_path = tmp / "replays" / "promotion_replay_candidate_policy.json"
            self._write_contract(contract_path, base_context_ref=dataset_root / "base_context.json")

            decision = run_model_group_replay_dataset_if_ready(
                storage_root=storage_root,
                contract_path=contract_path,
                prepare_runner_path=self._write_prepare_script(tmp / "prepare.py", missing_count=0),
                freeze_runner_path=self._write_freeze_script(tmp / "freeze.py"),
                evaluation_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_dataset_frozen")
            self.assertTrue((dataset_root / "base_context.json").exists())
            self.assertTrue((dataset_root / "replay_freeze_receipt.json").exists())
            base_context = json.loads((dataset_root / "base_context.json").read_text(encoding="utf-8"))
            self.assertEqual(base_context["pre_replay_target_refs"], ["AAPL"])
            self.assertFalse(decision.broker_execution_performed)
            self.assertEqual(decision.provider_calls, 0)

            second = run_model_group_replay_dataset_if_ready(
                storage_root=storage_root,
                contract_path=contract_path,
                prepare_runner_path=tmp / "missing_prepare.py",
                freeze_runner_path=tmp / "missing_freeze.py",
                evaluation_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )
            self.assertIsNone(second)

    def test_missing_coverage_requires_provider_acquisition_gate(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_completed_fold(storage_root)
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            contract_path = tmp / "replays" / "promotion_replay_candidate_policy.json"
            self._write_contract(contract_path, base_context_ref=dataset_root / "base_context.json")

            decision = run_model_group_replay_dataset_if_ready(
                storage_root=storage_root,
                contract_path=contract_path,
                prepare_runner_path=self._write_prepare_script(tmp / "prepare.py", missing_count=3),
                freeze_runner_path=self._write_freeze_script(tmp / "freeze.py"),
                evaluation_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute_provider_acquisition=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_dataset_acquisition_required")
            self.assertEqual(decision.provider_calls, 0)
            self.assertNotIn("--execute", decision.command)


if __name__ == "__main__":
    unittest.main()

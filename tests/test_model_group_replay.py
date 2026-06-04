from __future__ import annotations

import csv
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_replay import run_model_group_replay_if_ready


class ModelGroupReplayTests(unittest.TestCase):
    def _write_dataset(self, storage_root: Path) -> Path:
        dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
        dataset_root.mkdir(parents=True)
        plan_path = dataset_root / "feed_acquisition_plan.csv"
        with plan_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status", "target_ref"])
            writer.writeheader()
            writer.writerow({"month": "2021-01", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
            writer.writerow({"month": "2021-02", "source_id": "okx_crypto_market_data", "coverage_status": "available"})
        (dataset_root / "dataset_manifest.json").write_text(
            json.dumps(
                {
                    "contract_type": "replay_dataset_preparation_manifest",
                    "freeze_status": "frozen",
                    "missing_feed_acquisition_count": 0,
                    "feed_acquisition_plan_ref": str(plan_path),
                    "pre_replay_target_refs": ["AAPL"],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (dataset_root / "replay_freeze_receipt.json").write_text(
            json.dumps({"freeze_status": "frozen", "validation": {"validation_status": "passed"}}) + "\n",
            encoding="utf-8",
        )
        return dataset_root

    def _write_completed_fold(self, storage_root: Path) -> None:
        state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
        state_path.parent.mkdir(parents=True)
        stages = []
        for layer in range(1, 10):
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
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        artifact_path = storage_root.parent / "03_model_artifacts" / "runtime" / "model_05_alpha_confidence" / "after_cost_alpha_model_aapl_2016-01_2016-06.json"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text('{"artifacts_by_horizon": {}}\n', encoding="utf-8")

    def _write_runner(self, root: Path) -> Path:
        runner = root / "run_replay_execution.py"
        runner.write_text(
            textwrap.dedent(
                """
                import json
                import sys
                from pathlib import Path

                run_id = sys.argv[sys.argv.index("--run-id") + 1]
                candidate_model_ref = sys.argv[sys.argv.index("--candidate-model-ref") + 1]
                progress_path = Path(sys.argv[sys.argv.index("--progress-path") + 1])
                progress_path.parent.mkdir(parents=True, exist_ok=True)
                rows = [
                    {"contract_type": "evaluation_replay_progress", "stage_id": "model_group.replay", "replay_execution_run_id": run_id, "month": "2021-01", "status": "completed"},
                    {"contract_type": "evaluation_replay_progress", "stage_id": "model_group.replay", "replay_execution_run_id": run_id, "month": "2021-02", "status": "completed"},
                ]
                progress_path.write_text("\\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\\n", encoding="utf-8")
                print(json.dumps({
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": run_id,
                    "candidate_model_ref": candidate_model_ref,
                    "pre_replay_target_refs": ["XLK"],
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_equity_candidate_universe",
                    "candidate_handoff_symbols": ["AAPL"],
                    "decision_row_count": 2,
                }))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return runner

    def _write_fixed_equity_universe(self, path: Path, symbols: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["symbol", "replay_candidate_status"])
            writer.writeheader()
            for symbol in symbols:
                writer.writerow({"symbol": symbol, "replay_candidate_status": "active"})

    def test_runs_replay_when_fold_and_frozen_dataset_are_ready(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            runner = self._write_runner(tmp)

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=runner,
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_executed")
            self.assertEqual(decision.provider_calls, 0)
            self.assertFalse(decision.broker_execution_performed)
            self.assertIn("--candidate-model-ref", decision.command)
            self.assertIn("storage://trading-manager/model_group/aapl/2016-01_2016-06", decision.command)
            self.assertIn("--after-cost-alpha-model-json", decision.command)
            self.assertNotIn("--option-feature-database-url", decision.command)
            self.assertTrue(decision.execution_summary["option_feature_database_configured"])
            self.assertEqual(
                decision.execution_summary["replay_execution_receipt"]["candidate_model_ref"],
                "storage://trading-manager/model_group/aapl/2016-01_2016-06",
            )
            progress_rows = [json.loads(line) for line in (dataset_root / "replay_progress.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["month"] for row in progress_rows], ["2021-01", "2021-02"])

    def test_plan_passes_fixed_historical_equity_candidates_with_available_bars(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            fixed_universe = tmp / "historical_equity_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL", "MSFT", "NVDA"])
            plan_path = dataset_root / "feed_acquisition_plan.csv"
            with plan_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status", "target_ref"])
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "AAPL"})
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "MSFT"})
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "BAD SYMBOL"})

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                equity_candidate_universe_path=fixed_universe,
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            pairs = [
                decision.command[index + 1]
                for index, value in enumerate(decision.command)
                if value == "--equity-symbol"
            ]
            self.assertEqual(pairs, ["AAPL", "MSFT"])
            self.assertEqual(decision.execution_summary["equity_symbol_pool_symbol_count"], 2)
            self.assertEqual(decision.execution_summary["fixed_equity_candidate_universe_symbol_count"], 3)
            self.assertEqual(decision.execution_summary["equity_symbol_pool_source_policy"], "fixed_current_snapshot_historical_equity_candidate_universe")

    def test_rejects_runner_receipt_that_falls_back_to_placeholder_policy(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            runner = tmp / "run_replay_execution.py"
            runner.write_text(
                textwrap.dedent(
                    """
                    import json
                    print(json.dumps({
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "bad_run",
                        "candidate_model_ref": "trading-model://candidate_policy_replay/current_deterministic_crypto_policy",
                        "decision_row_count": 0,
                    }))
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=runner,
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_receipt_scope_mismatch")
            self.assertIn("deterministic crypto placeholder", decision.reason)

    def test_legacy_unsplit_model_generation_fold_does_not_unlock_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            state_path = storage_root / "runtime" / "model_training_fold_state_aapl_2016-01_2016-06.json"
            state_path.parent.mkdir(parents=True)
            state_path.write_text(
                json.dumps(
                    {
                        "contract_type": "manager_model_training_workflow_state",
                        "start_month": "2016-01",
                        "end_month": "2016-06",
                        "stages": [
                            {
                                "stage_id": f"layer_{layer:02d}_fixture.model_generation",
                                "stage_type": "model_generation",
                                "layer": layer,
                                "layer_key": f"layer_{layer:02d}_fixture",
                                "status": "succeeded",
                            }
                            for layer in range(1, 10)
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

        self.assertIsNone(decision)

    def test_replay_base_context_without_training_symbol_does_not_block_dataset(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            manifest_path = dataset_root / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["pre_replay_target_refs"] = ["BTC", "ETH", "SOL"]
            manifest.pop("target_refs", None)
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            self._write_completed_fold(storage_root)

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_executed")

    def test_replay_scope_mismatch_blocks_wrong_fold_dataset(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            manifest_path = dataset_root / "dataset_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["candidate_fold_id"] = "fold_2016-07_2016-12"
            manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
            self._write_completed_fold(storage_root)

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_scope_mismatch")
            self.assertIn("does not match completed training fold", decision.reason)

    def test_runner_failure_returns_backoff_decision(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            runner = tmp / "run_replay_execution.py"
            runner.write_text(
                textwrap.dedent(
                    """
                    import sys
                    print("missing fixed historical candidate universe evidence", file=sys.stderr)
                    raise SystemExit(2)
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=runner,
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_execution_failed")
            self.assertIn("missing fixed historical candidate universe evidence", decision.reason)
            self.assertEqual(decision.execution_summary["runner_returncode"], 2)

    def test_legacy_equity_replay_without_candidate_handoff_does_not_unlock_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            (dataset_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "legacy_run", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "legacy_run", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_root = dataset_root / "replay_execution_runs" / "legacy_run"
            receipt_root.mkdir(parents=True)
            (receipt_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "legacy_run",
                        "candidate_model_ref": "storage://trading-manager/model_group/2016-01_2016-06",
                        "pre_replay_target_refs": ["XLK"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "validation_status": "passed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_executed")

    def test_skips_replay_when_all_months_are_already_complete(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            (dataset_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "compatible_run", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "compatible_run", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_root = dataset_root / "replay_execution_runs" / "compatible_run"
            receipt_root.mkdir(parents=True)
            (receipt_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "compatible_run",
                        "candidate_model_ref": "storage://trading-manager/model_group/2016-01_2016-06",
                        "pre_replay_target_refs": ["XLK"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_equity_candidate_universe",
                        "candidate_handoff_symbols": ["AAPL"],
                        "validation_status": "passed",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(storage_root=storage_root, runner_path=tmp / "missing.py")

            self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()

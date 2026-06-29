from __future__ import annotations

import csv
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from trading_manager_tasks.model_group_replay_dataset import run_model_group_replay_dataset_if_ready


class ModelGroupReplayDatasetTests(unittest.TestCase):
    def _write_completed_fold(
        self,
        storage_root: Path,
        *,
        start_month: str = "2016-01",
        end_month: str = "2016-12",
    ) -> None:
        state_path = storage_root / "runtime" / f"model_training_fold_state_aapl_{start_month}_{end_month}.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
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
                            "split_policy": "chronological_rolling_fold_8_2_2",
                        },
                    }
                )
        stages.append(
            {
                "stage_id": "model_05_alpha_confidence.model_generation.checkpoint",
                "stage_type": "model_generation",
                "layer": 5,
                "layer_key": "model_05_alpha_confidence",
                "status": "succeeded",
            }
        )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": start_month,
                    "end_month": end_month,
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
            / f"option_expression_model_aapl_{start_month}_{end_month}.json"
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text('{"artifacts_by_horizon": {}}\n', encoding="utf-8")

    def _mark_m06_incomplete(self, storage_root: Path, *, start_month: str = "2016-01", end_month: str = "2016-12") -> None:
        state_path = storage_root / "runtime" / f"model_training_fold_state_aapl_{start_month}_{end_month}.json"
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        for stage in payload["stages"]:
            if int(stage.get("layer") or 0) != 6:
                continue
            split_name = stage.get("dataset_split", {}).get("split_name")
            stage["status"] = "ready" if split_name == "train" else "blocked"
        state_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

    def _write_contract(self, path: Path, *, base_context_ref: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "baseline_refs": ["baseline://active_model", "baseline://no_trade"],
                    "replay_mode": "candidate_policy_replay",
                    "candidate_policy_ref": "trading-model://model_02_target_candidate_universe_policy/live_equivalent",
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
                    "base_context_policy_ref": "trading-model://model_02_target_candidate_universe_policy/live_equivalent",
                    "base_context_ref": str(base_context_ref),
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_fixed_equity_universe(self, path: Path, symbols: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["symbol", "asset_class", "replay_candidate_status"])
            writer.writeheader()
            for symbol in symbols:
                writer.writerow(
                    {
                        "symbol": symbol,
                        "asset_class": "us_equity",
                        "replay_candidate_status": "active",
                    }
                )

    def _write_alpaca_month_source(self, storage_root: Path, symbol: str, month: str, *, status: str = "succeeded") -> None:
        month_dir = (
            storage_root.parent.parent
            / "storage"
            / "01_source_data"
            / "monthly_backfill"
            / "alpaca_bars"
            / symbol
            / month
        )
        month_dir.mkdir(parents=True, exist_ok=True)
        (month_dir / "completion_receipt.json").write_text(
            json.dumps({"contract_type": "source_completion_receipt", "runs": [{"status": status}]}) + "\n",
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

    def test_pre_replay_fold_admits_dataset_before_m06_generation(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_completed_fold(storage_root)
            self._mark_m06_incomplete(storage_root)
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            contract_path = tmp / "replays" / "promotion_replay_candidate_policy.json"
            self._write_contract(contract_path, base_context_ref=dataset_root / "base_context.json")

            decision = run_model_group_replay_dataset_if_ready(
                storage_root=storage_root,
                contract_path=contract_path,
                prepare_runner_path=tmp / "missing_prepare.py",
                freeze_runner_path=tmp / "missing_freeze.py",
                evaluation_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(decision.decision_status, "ready")
        self.assertEqual(decision.reason_code, "model_group_replay_dataset_base_context_ready")

    def test_frozen_manifest_is_fold_agnostic_after_latest_completed_fold_changes(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_completed_fold(storage_root, start_month="2016-01", end_month="2016-12")
            self._write_completed_fold(storage_root, start_month="2017-01", end_month="2017-12")
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            dataset_root.mkdir(parents=True, exist_ok=True)
            (dataset_root / "base_context.json").write_text(
                json.dumps({"candidate_fold_id": "fold_2016-01_2017-06", "pre_replay_target_refs": ["AAPL"]}) + "\n",
                encoding="utf-8",
            )
            (dataset_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "candidate_fold_id": "fold_2016-01_2017-06",
                        "missing_feed_acquisition_count": 0,
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

            self.assertIsNone(decision)
            manifest = json.loads((dataset_root / "dataset_manifest.json").read_text(encoding="utf-8"))
            base_context = json.loads((dataset_root / "base_context.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["candidate_fold_id"], "fold_2016-01_2017-06")
            self.assertEqual(base_context["candidate_fold_id"], "fold_2016-01_2017-06")

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

    def test_frozen_dataset_with_missing_fixed_candidate_bars_requires_acquisition_gate(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_completed_fold(storage_root)
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            dataset_root.mkdir(parents=True, exist_ok=True)
            (dataset_root / "base_context.json").write_text(
                json.dumps({"candidate_fold_id": "fold_2016-01_2017-06", "pre_replay_target_refs": ["AAPL"]}) + "\n",
                encoding="utf-8",
            )
            (dataset_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "candidate_fold_id": "fold_2016-01_2017-06",
                        "missing_feed_acquisition_count": 0,
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
            (dataset_root / "feed_acquisition_plan.csv").write_text(
                "acquisition_id,source_id,coverage_status,target_ref,feed,month,output_root,params_json\n",
                encoding="utf-8",
            )
            (storage_root.parent / "01_source_data" / "monthly_backfill" / "alpaca_bars" / "AAPL").mkdir(parents=True)
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL", "MSFT"])
            contract_path = tmp / "replays" / "promotion_replay_candidate_policy.json"
            self._write_contract(contract_path, base_context_ref=dataset_root / "base_context.json")

            decision = run_model_group_replay_dataset_if_ready(
                storage_root=storage_root,
                contract_path=contract_path,
                prepare_runner_path=self._write_prepare_script(tmp / "prepare.py", missing_count=0),
                freeze_runner_path=self._write_freeze_script(tmp / "freeze.py"),
                evaluation_repo_root=tmp,
                python_executable=sys.executable,
                source_data_root=storage_root.parent / "01_source_data",
                candidate_universe_path=fixed_universe,
                selected_target_symbol="AAPL",
                execute_provider_acquisition=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_dataset_acquisition_required")
            self.assertEqual(decision.execution_summary["fixed_candidate_coverage_gap"]["missing_equity_candidate_symbols_sample"], ["MSFT"])
            self.assertIn("--include-fixed-candidate-alpaca-bars", decision.command)
            self.assertIn(str(fixed_universe), decision.command)

    def test_fixed_candidate_bar_gap_is_month_specific(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_completed_fold(storage_root)
            dataset_root = storage_root.parent / "05_replay_datasets" / "promotion_replay_candidate_policy"
            dataset_root.mkdir(parents=True, exist_ok=True)
            (dataset_root / "base_context.json").write_text(
                json.dumps({"candidate_fold_id": "fold_2016-01_2017-06", "pre_replay_target_refs": ["AAPL"]}) + "\n",
                encoding="utf-8",
            )
            (dataset_root / "dataset_manifest.json").write_text(
                json.dumps(
                    {
                        "contract_type": "replay_dataset_preparation_manifest",
                        "contract_id": "promotion_replay_candidate_policy",
                        "freeze_status": "frozen",
                        "candidate_fold_id": "fold_2016-01_2017-06",
                        "missing_feed_acquisition_count": 0,
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
            plan_path = dataset_root / "feed_acquisition_plan.csv"
            with plan_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["acquisition_id", "source_id", "coverage_status", "target_ref", "feed", "month", "output_root", "params_json"],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "acquisition_id": "aapl_2021_01",
                        "source_id": "alpaca_bars",
                        "coverage_status": "available",
                        "target_ref": "AAPL",
                        "feed": "01_feed_alpaca_bars",
                        "month": "2021-01",
                        "output_root": "",
                        "params_json": "{}",
                    }
                )
                writer.writerow(
                    {
                        "acquisition_id": "aapl_2021_02",
                        "source_id": "alpaca_bars",
                        "coverage_status": "available",
                        "target_ref": "AAPL",
                        "feed": "01_feed_alpaca_bars",
                        "month": "2021-02",
                        "output_root": "",
                        "params_json": "{}",
                    }
                )
            self._write_alpaca_month_source(storage_root, "AAPL", "2021-01")
            self._write_alpaca_month_source(storage_root, "AAPL", "2021-02")
            self._write_alpaca_month_source(storage_root, "MSFT", "2021-03")
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL", "MSFT"])
            contract_path = tmp / "replays" / "promotion_replay_candidate_policy.json"
            self._write_contract(contract_path, base_context_ref=dataset_root / "base_context.json")

            decision = run_model_group_replay_dataset_if_ready(
                storage_root=storage_root,
                contract_path=contract_path,
                prepare_runner_path=self._write_prepare_script(tmp / "prepare.py", missing_count=0),
                freeze_runner_path=self._write_freeze_script(tmp / "freeze.py"),
                evaluation_repo_root=tmp,
                python_executable=sys.executable,
                source_data_root=storage_root.parent / "01_source_data",
                candidate_universe_path=fixed_universe,
                selected_target_symbol="AAPL",
                provider_acquisition_limit=None,
                execute_provider_acquisition=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_dataset_acquisition_required")
            gap = decision.execution_summary["fixed_candidate_coverage_gap"]
            self.assertEqual(gap["replay_month_count"], 2)
            self.assertEqual(gap["missing_equity_candidate_symbol_count"], 1)
            self.assertEqual(gap["missing_equity_candidate_symbol_month_count"], 2)
            self.assertEqual(
                gap["missing_equity_candidate_symbol_months_sample"],
                [{"month": "2021-01", "symbol": "MSFT"}, {"month": "2021-02", "symbol": "MSFT"}],
            )
            self.assertEqual(decision.command[decision.command.index("--limit") + 1], "2")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import csv
import json
import sys
import tempfile
import textwrap
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import trading_manager_tasks.model_group_replay as model_group_replay
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

    def _write_completed_fold(
        self,
        storage_root: Path,
        *,
        start_month: str = "2016-01",
        end_month: str = "2016-06",
        parent_start_month: str | None = None,
        parent_end_month: str | None = None,
    ) -> None:
        fold_key = f"{start_month}_{end_month}"
        state_path = storage_root / "runtime" / f"model_training_fold_state_aapl_{fold_key}.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_fixed_equity_universe(self._default_fixed_universe_path(storage_root), ["AAPL"])
        artifact_path = (
            storage_root.parent
            / "03_model_artifacts"
            / "runtime"
            / "model_05_alpha_confidence"
            / f"after_cost_alpha_model_{start_month}_{end_month}.json"
        )
        parent_checkpoint_ref = None
        if parent_start_month and parent_end_month:
            parent_checkpoint_ref = str(
                storage_root.parent
                / "03_model_artifacts"
                / "runtime"
                / "model_05_alpha_confidence"
                / f"after_cost_alpha_model_{parent_start_month}_{parent_end_month}.json"
            )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            json.dumps(
                {
                    "contract_type": "current_replay_entry_utility_model_bundle",
                    "fold_id": f"fold_{start_month}_{end_month}",
                    "target_symbol": "AAPL",
                    "learning_contract": "replayable_cumulative_fold_checkpoint",
                    "seed_checkpoint_ref": parent_checkpoint_ref,
                    "parent_checkpoint_ref": parent_checkpoint_ref,
                    "checkpoint_ref": str(artifact_path),
                    "training_summary": {
                        "training_mode": "supervised_fit",
                        "cumulative_learning_mode": "cumulative_checkpoint",
                        "sample_count": 128,
                    },
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        (
            storage_root.parent
            / "01_source_data"
            / "monthly_backfill"
            / "alpaca_bars"
            / "AAPL"
            / "2016-01"
        ).mkdir(parents=True, exist_ok=True)
        self._write_alpaca_month_source(storage_root, "AAPL", "2021-01")
        self._write_alpaca_month_source(storage_root, "AAPL", "2021-02")
        target_candidates_path = (
            storage_root
            / "runtime"
            / "model_02_target_state"
            / "input_materialization"
            / "2016_01_2016_06"
            / "target_candidates.jsonl"
        )
        target_candidates_path.parent.mkdir(parents=True, exist_ok=True)
        target_candidates_path.write_text(
            json.dumps(
                {
                    "target_candidate_id": "tcand_fixture_aapl",
                    "fold_id": f"fold_{start_month}_{end_month}",
                    "fold_start_month": start_month,
                    "fold_end_month": end_month,
                    "routing_symbol_ref": "AAPL",
                    "audit_symbol_ref": "AAPL",
                    "candidate_eligibility_state": "eligible",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        stages = []
        for layer in range(1, 7):
            for split_name in ("train", "validation", "test"):
                stages.append(
                    {
                        "stage_id": f"model_{layer:02d}_fixture.model_generation.{split_name}",
                        "stage_type": "model_generation",
                        "layer": layer,
                        "layer_key": f"model_{layer:02d}_fixture",
                        "status": "succeeded",
                        "dataset_split": {
                            "split_name": split_name,
                            "split_policy": "chronological_rolling_fold_8_2_2",
                        },
                    }
                )
        state_path.write_text(
            json.dumps(
                {
                    "contract_type": "manager_model_training_workflow_state",
                    "start_month": start_month,
                    "end_month": end_month,
                    "stages": stages,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_runner(self, root: Path) -> Path:
        runner = root / "run_replay_execution.py"
        runner.write_text(
            textwrap.dedent(
                """
                import csv
                import json
                import sys
                from pathlib import Path

                run_id = sys.argv[sys.argv.index("--run-id") + 1]
                candidate_model_ref = sys.argv[sys.argv.index("--candidate-model-ref") + 1]
                initial_capital_usd = float(sys.argv[sys.argv.index("--initial-capital-usd") + 1])
                candidate_universe_path = Path(sys.argv[sys.argv.index("--candidate-universe-path") + 1])
                candidate_symbols = []
                if candidate_universe_path.suffix == ".csv":
                    with candidate_universe_path.open("r", encoding="utf-8", newline="") as handle:
                        for row in csv.DictReader(handle):
                            symbol = str(row.get("symbol") or "").strip().upper()
                            status = str(row.get("replay_candidate_status") or "active").strip().lower()
                            if symbol and status == "active":
                                candidate_symbols.append(symbol)
                    candidate_source = "fixed_current_snapshot_historical_candidate_universe"
                else:
                    candidate_symbols = ["AAPL"]
                    candidate_source = "model_02_target_candidate_handoff"
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
                    "candidate_handoff_source": candidate_source,
                    "candidate_handoff_symbols": candidate_symbols,
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                    },
                    "initial_capital_usd": initial_capital_usd,
                    "initial_capital": {"amount": initial_capital_usd, "currency": "USD"},
                    "replay_completion_scope": "full_candidate_universe",
                    "replay_continuity_policy": "continuous_cross_month_portfolio_path",
                    "decision_row_count": 2,
                }))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return runner

    def _write_runner_with_missing_selected_contract_path(self, root: Path) -> Path:
        runner = root / "run_replay_execution_missing_contract_path.py"
        runner.write_text(
            textwrap.dedent(
                """
                import json
                import sys
                from pathlib import Path

                run_id = sys.argv[sys.argv.index("--run-id") + 1]
                candidate_model_ref = sys.argv[sys.argv.index("--candidate-model-ref") + 1]
                replay_month = "2021-01"
                progress_path = Path(sys.argv[sys.argv.index("--progress-path") + 1])
                dataset_root = Path(sys.argv[sys.argv.index("--dataset-root") + 1])
                run_root = dataset_root / "replay_execution_runs" / run_id
                run_root.mkdir(parents=True, exist_ok=True)
                decision_rows_ref = run_root / "decision_rows.jsonl"
                decision_rows_ref.write_text(json.dumps({
                    "decision_id": "ed_missing_path",
                    "timestamp": f"{replay_month}-05T16:00:00-05:00",
                    "target_ref": "AAPL",
                    "selected_option_contract_ref": "AAPL_2021-01-08_C_142",
                    "option_contract_path_status": "missing",
                    "replay_time_pointer": f"{replay_month}-05T16:00:00-05:00",
                    "next_timestamp": f"{replay_month}-06T16:00:00-05:00"
                }, sort_keys=True) + "\\n", encoding="utf-8")
                progress_path.parent.mkdir(parents=True, exist_ok=True)
                progress_path.write_text(json.dumps({
                    "contract_type": "evaluation_replay_progress",
                    "stage_id": "model_group.replay",
                    "replay_execution_run_id": run_id,
                    "month": replay_month,
                    "replay_month": replay_month,
                    "status": "completed",
                    "decision_rows_ref": str(decision_rows_ref),
                }, sort_keys=True) + "\\n", encoding="utf-8")
                receipt = {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": run_id,
                    "candidate_model_ref": candidate_model_ref,
                    "candidate_fold_id": "fold_2016-01_2016-06",
                    "decision_rows_ref": str(decision_rows_ref),
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "candidate_handoff_symbols": ["AAPL"],
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                    },
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "decision_row_count": 1,
                    "max_decision_rows": None,
                    "replay_completion_scope": "full_candidate_universe",
                    "replay_continuity_policy": "continuous_cross_month_portfolio_path",
                    "validation_status": "passed",
                }
                print(json.dumps(receipt, sort_keys=True))
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        return runner

    def _write_completed_replay_month(
        self,
        dataset_root: Path,
        *,
        run_id: str,
        month: str,
        candidate_handoff_source: str = "fixed_current_snapshot_historical_candidate_universe",
    ) -> None:
        receipt_root = dataset_root / "replay_execution_runs" / run_id
        receipt_root.mkdir(parents=True, exist_ok=True)
        decision_rows_path = receipt_root / "decision_rows.jsonl"
        decision_rows_path.write_text(
            json.dumps({"decision_id": f"decision_{run_id}", "timestamp": f"{month}-02T16:00:00-05:00"}) + "\n",
            encoding="utf-8",
        )
        (receipt_root / "replay_execution_receipt.json").write_text(
            json.dumps(
                {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": run_id,
                    "replay_month": month,
                    "decision_rows_ref": str(decision_rows_path),
                    "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                    "candidate_fold_id": "fold_2016-01_2016-06",
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": candidate_handoff_source,
                    "candidate_handoff_symbols": ["AAPL"],
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                    },
                    "max_decision_rows": None,
                    "replay_completion_scope": "full_candidate_universe",
                    "replay_continuity_policy": "bounded_month_diagnostic",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        with (dataset_root / "replay_progress.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "stage_id": "model_group.replay",
                        "replay_execution_run_id": run_id,
                        "month": month,
                        "status": "completed",
                    }
                )
                + "\n"
            )

    def _write_completed_continuous_replay(
        self,
        dataset_root: Path,
        *,
        run_id: str = "continuous_run",
        start_month: str = "2016-01",
        end_month: str = "2016-06",
    ) -> None:
        receipt_root = dataset_root / "replay_execution_runs" / run_id
        receipt_root.mkdir(parents=True, exist_ok=True)
        decision_rows_path = receipt_root / "decision_rows.jsonl"
        decision_rows_path.write_text(
            "\n".join(
                [
                    json.dumps({"decision_id": "decision_2021_01", "timestamp": "2021-01-05T16:00:00-05:00"}),
                    json.dumps({"decision_id": "decision_2021_02", "timestamp": "2021-02-05T16:00:00-05:00"}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (receipt_root / "replay_execution_receipt.json").write_text(
            json.dumps(
                {
                    "contract_type": "evaluation_replay_execution_run",
                    "replay_execution_run_id": run_id,
                    "decision_rows_ref": str(decision_rows_path),
                    "candidate_model_ref": f"storage://trading-manager/model_group/aapl/{start_month}_{end_month}",
                    "candidate_fold_id": f"fold_{start_month}_{end_month}",
                    "target_refs": ["AAPL"],
                    "asset_class_counts": {"us_equity": 1},
                    "candidate_handoff_status": "available",
                    "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                    "candidate_handoff_symbols": ["AAPL"],
                    "portfolio_replay_policy": {
                        "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                        "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                        "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                        "max_positions": 5,
                        "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                        "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                    },
                    "max_decision_rows": None,
                    "completed_replay_month_count": 2,
                    "replay_completion_scope": "full_candidate_universe",
                    "replay_continuity_policy": "continuous_cross_month_portfolio_path",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        with (dataset_root / "replay_progress.jsonl").open("a", encoding="utf-8") as handle:
            for month in ("2021-01", "2021-02"):
                handle.write(
                    json.dumps(
                        {
                            "stage_id": "model_group.replay",
                            "replay_execution_run_id": run_id,
                            "month": month,
                            "status": "completed",
                        }
                    )
                    + "\n"
                )

    def _default_fixed_universe_path(self, storage_root: Path) -> Path:
        return storage_root.parent.parent / "main" / "shared" / "historical_candidate_universe.csv"

    def _write_fixed_equity_universe(self, path: Path, symbols: list[str], *, freeze_as_of_date: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["symbol", "asset_class", "replay_candidate_status", "freeze_as_of_date"])
            writer.writeheader()
            for symbol in symbols:
                asset_class = "crypto_spot" if symbol in {"BTC", "ETH", "SOL"} else "us_equity"
                writer.writerow({"symbol": symbol, "asset_class": asset_class, "replay_candidate_status": "active", "freeze_as_of_date": freeze_as_of_date})

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
            self.assertNotIn("--replay-month", decision.command)
            self.assertIn("--after-cost-alpha-model-json", decision.command)
            alpha_ref = decision.command[decision.command.index("--after-cost-alpha-model-json") + 1]
            self.assertTrue(alpha_ref.endswith("after_cost_alpha_model_2016-01_2016-06.json"))
            self.assertIn("--initial-capital-usd", decision.command)
            self.assertEqual(decision.command[decision.command.index("--initial-capital-usd") + 1], "25000.0")
            self.assertNotIn("--option-feature-database-url", decision.command)
            self.assertTrue(decision.execution_summary["option_feature_database_configured"])
            self.assertEqual(decision.execution_summary["initial_capital_usd"], 25000.0)
            self.assertTrue(decision.command[decision.command.index("--candidate-universe-path") + 1].endswith("historical_candidate_universe.csv"))
            self.assertEqual(decision.execution_summary["replay_execution_receipt"]["initial_capital_usd"], 25000.0)
            self.assertEqual(
                decision.execution_summary["replay_execution_receipt"]["replay_continuity_policy"],
                "continuous_cross_month_portfolio_path",
            )
            self.assertEqual(
                decision.execution_summary["replay_execution_receipt"]["candidate_handoff_source"],
                "fixed_current_snapshot_historical_candidate_universe",
            )

    def test_replay_ready_command_uses_latest_resume_checkpoint(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            checkpoint_path = dataset_root / "replay_execution_runs" / "previous_run" / "replay_resume_checkpoint.json"
            checkpoint_path.parent.mkdir(parents=True)
            decision_rows_path = checkpoint_path.parent / "decision_rows.jsonl"
            decision_rows_path.write_text(
                json.dumps({"decision_id": "decision_2021_01", "timestamp": "2021-01-05T16:00:00-05:00"}) + "\n",
                encoding="utf-8",
            )
            (checkpoint_path.parent / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "previous_run",
                        "decision_rows_ref": str(decision_rows_path),
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                        "candidate_fold_id": "fold_2016-01_2016-06",
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                            "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                        },
                        "max_decision_rows": None,
                        "replay_completion_scope": "full_candidate_universe",
                        "replay_continuity_policy": "continuous_cross_month_portfolio_path",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            checkpoint_path.write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_resume_checkpoint",
                        "replay_execution_run_id": "previous_run",
                        "replay_month": "2021-02",
                        "replay_time_pointer": "2021-02-17T16:00:00-05:00",
                        "cash_after": 20000.0,
                        "portfolio_state_after": {"cash": 20000.0, "positions": {}},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=tmp / "runner.py",
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.reason_code, "model_group_replay_ready")
            self.assertIn("--resume-checkpoint-path", decision.command)
            self.assertEqual(
                decision.command[decision.command.index("--resume-checkpoint-path") + 1],
                str(checkpoint_path),
            )

    def test_replay_selects_earliest_completed_fold_without_valid_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._write_completed_fold(
                storage_root,
                start_month="2016-07",
                end_month="2016-12",
                parent_start_month="2016-01",
                parent_end_month="2016-06",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=tmp / "runner.py",
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.reason_code, "model_group_replay_ready")
            self.assertEqual(
                decision.execution_summary["training_fold"]["candidate_model_ref"],
                "storage://trading-manager/model_group/aapl/2016-01_2016-06",
            )

    def test_replay_selects_next_fold_after_previous_fold_has_valid_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._write_completed_fold(
                storage_root,
                start_month="2016-07",
                end_month="2016-12",
                parent_start_month="2016-01",
                parent_end_month="2016-06",
            )
            self._write_completed_continuous_replay(dataset_root, run_id="fold1_run")

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=tmp / "runner.py",
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.reason_code, "model_group_replay_ready")
            self.assertEqual(
                decision.execution_summary["training_fold"]["candidate_model_ref"],
                "storage://trading-manager/model_group/aapl/2016-07_2016-12",
            )

    def test_replay_resume_checkpoint_is_fold_scoped(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._write_completed_fold(
                storage_root,
                start_month="2016-07",
                end_month="2016-12",
                parent_start_month="2016-01",
                parent_end_month="2016-06",
            )
            self._write_completed_continuous_replay(
                dataset_root,
                run_id="fold2_run",
                start_month="2016-07",
                end_month="2016-12",
            )
            checkpoint_path = dataset_root / "replay_execution_runs" / "fold2_run" / "replay_resume_checkpoint.json"
            checkpoint_path.write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_resume_checkpoint",
                        "replay_execution_run_id": "fold2_run",
                        "replay_month": "2021-02",
                        "replay_time_pointer": "2021-02-17T16:00:00-05:00",
                        "cash_after": 20000.0,
                        "portfolio_state_after": {"cash": 20000.0, "positions": {}},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=tmp / "runner.py",
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(
                decision.execution_summary["training_fold"]["candidate_model_ref"],
                "storage://trading-manager/model_group/aapl/2016-01_2016-06",
            )
            self.assertNotIn("--resume-checkpoint-path", decision.command)

    def test_replay_command_ignores_legacy_month_shard_completion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._write_completed_replay_month(dataset_root, run_id="first_month", month="2021-01")

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "ready")
            self.assertEqual(decision.execution_summary["ready_replay_months"], 0)
            self.assertIsNone(decision.execution_summary["replay_month"])
            self.assertNotIn("--replay-month", decision.command)

    def test_missing_selected_contract_path_blocks_replay_completion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner_with_missing_selected_contract_path(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_contract_path_acquisition_required")
            self.assertEqual(decision.execution_summary["missing_selected_contract_path_count"], 1)
            self.assertEqual(decision.execution_summary["acquisition_routes"], ["model_group.replay_contract_paths"])
            self.assertFalse((dataset_root / "replay_progress.jsonl").exists())
            candidate_progress_path = Path(decision.execution_summary["candidate_progress_path"])
            self.assertTrue(candidate_progress_path.exists())

            retry = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(retry)
            assert retry is not None
            self.assertEqual(retry.execution_summary["ready_replay_months"], 0)
            self.assertIsNone(retry.execution_summary["replay_month"])

    def test_replay_progress_month_must_match_receipt_and_decision_rows(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            run_id = "polluted_month"
            receipt_root = dataset_root / "replay_execution_runs" / run_id
            receipt_root.mkdir(parents=True)
            decision_rows_path = receipt_root / "decision_rows.jsonl"
            decision_rows_path.write_text('{"decision_id":"decision_1","timestamp":"2021-01-05T16:00:00-05:00"}\n', encoding="utf-8")
            (receipt_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": run_id,
                        "replay_month": "2021-02",
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                        "candidate_fold_id": "fold_2016-01_2016-06",
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "candidate_handoff_symbols": ["AAPL"],
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                            "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                        },
                        "decision_rows_ref": str(decision_rows_path),
                        "max_decision_rows": None,
                        "replay_completion_scope": "full_candidate_universe",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (dataset_root / "replay_progress.jsonl").write_text(
                json.dumps(
                    {
                        "stage_id": "model_group.replay",
                        "replay_execution_run_id": run_id,
                        "month": "2021-01",
                        "status": "completed",
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
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "ready")
            self.assertEqual(decision.execution_summary["ready_replay_months"], 0)
            self.assertIsNone(decision.execution_summary["replay_month"])

    def test_plan_passes_fixed_historical_candidate_universe_without_symbol_override(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL", "MSFT", "BTC"])
            plan_path = dataset_root / "feed_acquisition_plan.csv"
            with plan_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status", "target_ref"])
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "AAPL"})
                writer.writerow({"month": "2021-02", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "AAPL"})
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "MSFT"})
                writer.writerow({"month": "2021-02", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "MSFT"})
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "BAD SYMBOL"})
                writer.writerow({"month": "2021-02", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "BAD SYMBOL"})

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                candidate_universe_path=fixed_universe,
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertNotIn("--equity-symbol", decision.command)
            self.assertIn("--candidate-universe-path", decision.command)
            self.assertEqual(
                decision.command[decision.command.index("--candidate-universe-path") + 1],
                str(fixed_universe),
            )
            self.assertEqual(decision.execution_summary["equity_symbol_pool_symbol_count"], 2)
            self.assertEqual(decision.execution_summary["fixed_candidate_universe_symbol_count"], 3)
            self.assertEqual(decision.execution_summary["fixed_equity_candidate_symbol_count"], 2)
            self.assertEqual(decision.execution_summary["materialized_equity_candidate_symbol_count"], 2)
            self.assertEqual(decision.execution_summary["candidate_universe_source_policy"], "fixed_current_snapshot_historical_candidate_universe")

    def test_default_replay_candidate_universe_missing_blocks_instead_of_using_target_handoff(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._default_fixed_universe_path(storage_root).unlink()

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_candidate_universe_missing")
            self.assertTrue(decision.execution_summary["candidate_universe_path"].endswith("historical_candidate_universe.csv"))

    def test_missing_fold_scoped_alpha_training_script_blocks_before_subprocess(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            alpha_model_path = (
                storage_root.parent
                / "03_model_artifacts"
                / "runtime"
                / "model_05_alpha_confidence"
                / "after_cost_alpha_model_2016-01_2016-06.json"
            )
            alpha_model_path.unlink()

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                model_repo_root=tmp / "missing-model-repo",
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_after_cost_alpha_training_script_missing")
            self.assertEqual(decision.command, [])
            self.assertTrue(
                decision.execution_summary["after_cost_alpha_training_script_ref"].endswith(
                    "scripts/models/model_05_alpha_confidence/train_model_05_alpha_confidence.py"
                )
            )

    def test_cumulative_fold_blocks_when_parent_checkpoint_missing(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(
                storage_root,
                start_month="2016-07",
                end_month="2016-12",
                parent_start_month="2016-01",
                parent_end_month="2016-06",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_after_cost_alpha_parent_checkpoint_missing")
            self.assertTrue(decision.execution_summary["parent_checkpoint_ref"].endswith("after_cost_alpha_model_2016-01_2016-06.json"))

    def test_cumulative_fold_blocks_when_artifact_lacks_parent_lineage(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._write_completed_fold(storage_root, start_month="2016-07", end_month="2016-12")
            self._write_completed_continuous_replay(dataset_root, run_id="fold1_run")

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_after_cost_alpha_model_not_trained")
            self.assertEqual(
                decision.execution_summary["model_artifact_status"]["reason"],
                "after-cost alpha artifact parent checkpoint lineage does not match previous fold",
            )

    def test_current_entry_utility_policy_bundle_blocks_replay_without_supervised_fit(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            alpha_model_path = (
                storage_root.parent
                / "03_model_artifacts"
                / "runtime"
                / "model_05_alpha_confidence"
                / "after_cost_alpha_model_2016-01_2016-06.json"
            )
            alpha_model_path.write_text(
                json.dumps(
                    {
                        "contract_type": "current_replay_entry_utility_model_bundle",
                        "model_type": "replay_entry_utility_policy_bundle",
                        "score_policy": "derive_from_current_m02_m03_state",
                        "training_summary": {
                            "training_mode": "policy_bundle_no_supervised_fit",
                            "sample_count": None,
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            model_repo = tmp / "model-repo"
            script = model_repo / "scripts" / "models" / "model_05_alpha_confidence" / "train_model_05_alpha_confidence.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(
                "import sys\nprint('after_cost_alpha_supervised_training_labels_missing', file=sys.stderr)\nsys.exit(2)\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                model_repo_root=model_repo,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_after_cost_alpha_training_labels_missing")
            self.assertEqual(
                decision.execution_summary["stale_model_artifact_status"]["reason"],
                "after-cost alpha artifact lacks fold-specific supervised training evidence",
            )

    def test_no_fit_alpha_artifact_attempts_training_and_blocks_on_training_failure(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            alpha_model_path = (
                storage_root.parent
                / "03_model_artifacts"
                / "runtime"
                / "model_05_alpha_confidence"
                / "after_cost_alpha_model_2016-01_2016-06.json"
            )
            alpha_model_path.write_text(
                json.dumps(
                    {
                        "contract_type": "current_replay_entry_utility_model_bundle",
                        "model_type": "replay_entry_utility_policy_bundle",
                        "score_policy": "derive_from_current_m02_m03_state",
                        "training_summary": {
                            "training_mode": "policy_bundle_no_supervised_fit",
                            "sample_count": None,
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            model_repo = tmp / "model-repo"
            script = model_repo / "scripts" / "models" / "model_05_alpha_confidence" / "train_model_05_alpha_confidence.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(
                "import sys\nprint('after_cost_alpha_supervised_training_labels_missing', file=sys.stderr)\nsys.exit(2)\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                model_repo_root=model_repo,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_after_cost_alpha_training_labels_missing")
            self.assertIn("after_cost_alpha_supervised_training_labels_missing", decision.reason)
            self.assertEqual(
                decision.execution_summary["stale_model_artifact_status"]["training_mode"],
                "policy_bundle_no_supervised_fit",
            )

    def test_incomplete_alpha_artifact_without_accepted_policy_bundle_blocks_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            alpha_model_path = (
                storage_root.parent
                / "03_model_artifacts"
                / "runtime"
                / "model_05_alpha_confidence"
                / "after_cost_alpha_model_2016-01_2016-06.json"
            )
            alpha_model_path.write_text(
                json.dumps(
                    {
                        "contract_type": "unexpected_alpha_bundle",
                        "training_summary": {
                            "training_mode": "policy_bundle_no_supervised_fit",
                            "sample_count": None,
                        },
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            model_repo = tmp / "model-repo"
            script = model_repo / "scripts" / "models" / "model_05_alpha_confidence" / "train_model_05_alpha_confidence.py"
            script.parent.mkdir(parents=True, exist_ok=True)
            script.write_text(
                "import sys\nprint('after_cost_alpha_supervised_training_labels_missing', file=sys.stderr)\nsys.exit(2)\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                model_repo_root=model_repo,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_after_cost_alpha_training_labels_missing")
            self.assertIn("after_cost_alpha_supervised_training_labels_missing", decision.reason)

    def test_explicit_training_target_handoff_does_not_run_canonical_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            handoff_path = (
                storage_root
                / "runtime"
                / "model_02_target_state"
                / "input_materialization"
                / "2016_01_2016_06"
                / "target_candidates.jsonl"
            )

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                candidate_universe_path=handoff_path,
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_candidate_universe_not_canonical")
            self.assertEqual(
                decision.execution_summary["candidate_universe_source_policy"],
                "model_02_target_candidate_handoff",
            )

    def test_bounded_replay_receipt_does_not_satisfy_full_replay_completion(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL"])
            plan_path = dataset_root / "feed_acquisition_plan.csv"
            with plan_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status", "target_ref"])
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "AAPL"})

            run_id = "bounded_run"
            (dataset_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": run_id, "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": run_id, "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_root = dataset_root / "replay_execution_runs" / run_id
            receipt_root.mkdir(parents=True)
            decision_rows_path = receipt_root / "decision_rows.jsonl"
            decision_rows_path.write_text("{}\n", encoding="utf-8")
            (receipt_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": run_id,
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                        "candidate_fold_id": "fold_2016-01_2016-06",
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "decision_rows_ref": str(decision_rows_path),
                        "max_decision_rows": 5000,
                        "replay_completion_scope": "bounded_diagnostic",
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
                candidate_universe_path=fixed_universe,
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "ready")
            self.assertEqual(decision.execution_summary["ready_replay_months"], 0)

    def test_plan_blocks_when_fixed_candidate_universe_bars_are_incomplete(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL", "MSFT"])
            plan_path = dataset_root / "feed_acquisition_plan.csv"
            with plan_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status", "target_ref"])
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "AAPL"})

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                candidate_universe_path=fixed_universe,
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_candidate_bar_coverage_incomplete")
            self.assertEqual(decision.execution_summary["missing_equity_candidate_symbol_count"], 1)
            self.assertEqual(decision.execution_summary["missing_equity_candidate_symbols_sample"], ["MSFT"])

    def test_plan_blocks_when_symbol_only_has_non_replay_month_bars(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL", "MSFT"])
            self._write_alpaca_month_source(storage_root, "MSFT", "2021-03")

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                candidate_universe_path=fixed_universe,
                execute=False,
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_candidate_bar_coverage_incomplete")
            self.assertIsNone(decision.execution_summary["replay_month"])
            self.assertEqual(decision.execution_summary["missing_equity_candidate_symbols_sample"], ["MSFT"])

    def test_execution_blocks_current_day_candidate_universe_before_post_close_ready_time(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            fixed_universe = tmp / "historical_candidate_universe.csv"
            self._write_fixed_equity_universe(fixed_universe, ["AAPL"], freeze_as_of_date="2026-06-04")
            plan_path = dataset_root / "feed_acquisition_plan.csv"
            with plan_path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["month", "source_id", "coverage_status", "target_ref"])
                writer.writerow({"month": "2021-01", "source_id": "alpaca_bars", "coverage_status": "available", "target_ref": "AAPL"})

            decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                candidate_universe_path=fixed_universe,
                now_utc=datetime(2026, 6, 4, 15, 30, tzinfo=UTC),
            )

            self.assertIsNotNone(decision)
            assert decision is not None
            self.assertEqual(decision.decision_status, "backoff")
            self.assertEqual(decision.reason_code, "model_group_replay_candidate_universe_intraday_pending_close")
            self.assertFalse(decision.execution_summary["candidate_universe_close_status"]["ready_for_replay"])

            plan_decision = run_model_group_replay_if_ready(
                storage_root=storage_root,
                runner_path=self._write_runner(tmp),
                evaluation_repo_root=tmp,
                execution_repo_root=tmp,
                python_executable=sys.executable,
                selected_target_symbol="AAPL",
                candidate_universe_path=fixed_universe,
                now_utc=datetime(2026, 6, 4, 15, 30, tzinfo=UTC),
                execute=False,
            )

            self.assertIsNotNone(plan_decision)
            assert plan_decision is not None
            self.assertEqual(plan_decision.decision_status, "ready")

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
                                "stage_id": f"model_{layer:02d}_fixture.model_generation",
                                "stage_type": "model_generation",
                                "layer": layer,
                                "layer_key": f"model_{layer:02d}_fixture",
                                "status": "succeeded",
                            }
                            for layer in range(1, 7)
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

    def test_replay_dataset_manifest_fold_id_does_not_block_missing_fold_replay(self):
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
            self.assertEqual(decision.decision_status, "executed")
            self.assertEqual(decision.reason_code, "model_group_replay_executed")
            self.assertEqual(
                decision.execution_summary["training_fold"]["candidate_model_ref"],
                "storage://trading-manager/model_group/aapl/2016-01_2016-06",
            )

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

    def test_option_feature_acquisition_requirement_returns_specific_backoff(self):
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
                    print("replay_option_feature_acquisition_required: missing AAPL 2021-01-04T16:00:00-05:00", file=sys.stderr)
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
            self.assertEqual(decision.reason_code, "model_group_replay_option_feature_acquisition_required")
            self.assertEqual(decision.execution_summary["blocked_stage_id"], "model_05_option_expression.option_chain_data_acquisition")
            self.assertEqual(decision.execution_summary["resume_stage_id"], "model_group.replay")

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
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
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

    def test_diagnostic_symbol_override_replay_does_not_unlock_canonical_replay(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            (dataset_root / "replay_progress.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "diagnostic_run", "month": "2021-01", "status": "completed"}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": "diagnostic_run", "month": "2021-02", "status": "completed"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            receipt_root = dataset_root / "replay_execution_runs" / "diagnostic_run"
            receipt_root.mkdir(parents=True)
            decision_rows_path = receipt_root / "decision_rows.jsonl"
            decision_rows_path.write_text('{"decision_id":"decision_1"}\n', encoding="utf-8")
            (receipt_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": "diagnostic_run",
                        "decision_rows_ref": str(decision_rows_path),
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                        "pre_replay_target_refs": ["XLK"],
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "override",
                        "candidate_handoff_source": "explicit_candidate_symbols_override",
                        "candidate_handoff_symbols": ["AAPL"],
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
            self._write_completed_continuous_replay(dataset_root)

            decision = run_model_group_replay_if_ready(storage_root=storage_root, runner_path=tmp / "missing.py")

            self.assertIsNone(decision)

    def test_full_replay_receipt_skips_progress_scan_when_plan_is_complete(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)
            self._write_completed_continuous_replay(dataset_root)

            with patch.object(model_group_replay, "_ready_replay_months") as ready_months:
                decision = run_model_group_replay_if_ready(storage_root=storage_root, runner_path=tmp / "missing.py")

            self.assertIsNone(decision)
            ready_months.assert_not_called()

    def test_skips_replay_when_progress_covers_month_without_decisions(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage" / "02_control_plane"
            storage_root.mkdir(parents=True)
            dataset_root = self._write_dataset(storage_root)
            self._write_completed_fold(storage_root)

            run_id = "complete_with_empty_month"
            receipt_root = dataset_root / "replay_execution_runs" / run_id
            receipt_root.mkdir(parents=True, exist_ok=True)
            decision_rows_path = receipt_root / "decision_rows.jsonl"
            decision_rows_path.write_text(
                json.dumps({"decision_id": "decision_2021_01", "timestamp": "2021-01-05T16:00:00-05:00"})
                + "\n",
                encoding="utf-8",
            )
            progress_path = dataset_root / "replay_progress.jsonl"
            progress_path.write_text(
                "\n".join(
                    [
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": run_id, "month": "2021-01", "status": "completed", "decision_row_count": 1}),
                        json.dumps({"stage_id": "model_group.replay", "replay_execution_run_id": run_id, "month": "2021-02", "status": "completed", "decision_row_count": 0}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (receipt_root / "replay_execution_receipt.json").write_text(
                json.dumps(
                    {
                        "contract_type": "evaluation_replay_execution_run",
                        "replay_execution_run_id": run_id,
                        "decision_rows_ref": str(decision_rows_path),
                        "progress_ref": str(progress_path),
                        "candidate_model_ref": "storage://trading-manager/model_group/aapl/2016-01_2016-06",
                        "candidate_fold_id": "fold_2016-01_2016-06",
                        "target_refs": ["AAPL"],
                        "asset_class_counts": {"us_equity": 1},
                        "candidate_handoff_status": "available",
                        "candidate_handoff_source": "fixed_current_snapshot_historical_candidate_universe",
                        "candidate_handoff_symbols": ["AAPL"],
                        "portfolio_replay_policy": {
                            "full_budget_replacement_policy": "continue_scanning_after_budget_full",
                            "residual_cash_replacement_policy": "insufficient_cash_falls_through_to_replacement",
                            "portfolio_capacity_policy": "default_5_simultaneous_risk_slots_from_20pct_allocation",
                            "max_positions": 5,
                            "position_sizing_policy": "rank_ordered_best_first_with_simultaneous_position_cap_target_allocation_floor_option_contract_round_up",
                            "switch_threshold_policy": "score_scale_aware_absolute_rank_delta",
                        },
                        "max_decision_rows": None,
                        "replay_completion_scope": "full_candidate_universe",
                        "replay_continuity_policy": "continuous_cross_month_portfolio_path",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            decision = run_model_group_replay_if_ready(storage_root=storage_root, runner_path=tmp / "missing.py")

            self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()

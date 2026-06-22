from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trading_manager_tasks.layer_three_target_state import (
    FeedArtifactRef,
    build_source_task_key,
    discover_target_candidate_feed_artifacts,
    main,
    materialize_layer_three_target_state_inputs,
)


def _write_bar_receipt(storage_root: Path, symbol: str, month: str, *, row_count: int = 1, write_task_key: bool = True, manifest_timeframe: str | None = None) -> Path:
    receipt_path = storage_root / "monthly_backfill" / "alpaca_bars" / symbol / month / "completion_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    if write_task_key:
        (receipt_path.parent / "task_key.json").write_text(
            json.dumps({"params": {"timeframe": "1Min"}}),
            encoding="utf-8",
        )
    output_dir = receipt_path.parent / "runs" / "run_001"
    if manifest_timeframe:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "request_manifest.json").write_text(
            json.dumps({"params": {"timeframe": manifest_timeframe}}),
            encoding="utf-8",
        )
    receipt_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "run_id": "run_001",
                        "status": "succeeded",
                        "output_dir": str(output_dir),
                        "outputs": ["trading_data.model_01_market_regime_data_acquisition"],
                        "row_counts": {"equity_bar": row_count},
                        "steps": {"save": {"references": ["trading_data.model_01_market_regime_data_acquisition"]}},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return receipt_path


class LayerThreeTargetStateTests(unittest.TestCase):
    def test_cli_accepts_persist_sql_stage_command_alias(self) -> None:
        with (
            patch("trading_manager_tasks.layer_three_target_state.materialize_layer_three_target_state_inputs") as materialize,
            patch("trading_manager_tasks.layer_three_target_state.write_summary"),
        ):
            materialize.return_value = object()

            result = main(
                [
                    "--start-month",
                    "2016-01",
                    "--end-month",
                    "2016-06",
                    "--target-symbol",
                    "AAPL",
                    "--persist-sql",
                ]
            )

            self.assertEqual(result, 0)
            self.assertTrue(materialize.call_args.kwargs["write"])

    def test_discovers_successful_target_candidate_feed_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,replay_candidate_status\nXLF,active\nSPY,active\n", encoding="utf-8")
            _write_bar_receipt(storage_root, "XLF", "2016-01")

            refs = discover_target_candidate_feed_artifacts(
                start_month="2016-01",
                trading_data_root=tmp / "trading-data",
                trading_storage_root=storage_root,
                universe_path=universe_path,
            )

            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0].symbol, "XLF")
            self.assertEqual(refs[0].row_count, 1)
            self.assertEqual(refs[0].bar_source_ref, "trading_data.model_01_market_regime_data_acquisition")
            self.assertEqual(refs[0].timeframe, "1Min")

    def test_discovers_timeframe_from_run_manifest_when_task_key_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,replay_candidate_status\nAAPL,active\n", encoding="utf-8")
            _write_bar_receipt(storage_root, "AAPL", "2021-01", write_task_key=False, manifest_timeframe="1Day")

            refs = discover_target_candidate_feed_artifacts(
                start_month="2021-01",
                trading_data_root=tmp / "trading-data",
                trading_storage_root=storage_root,
                universe_path=universe_path,
                symbols=("AAPL",),
            )

            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0].timeframe, "1Day")

    def test_default_candidate_universe_can_be_symbol_limited(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "historical_candidate_universe.csv"
            universe_path.write_text(
                "symbol,replay_candidate_status\n"
                "AAPL,active\n"
                "MSFT,active\n"
                "TSLA,active\n",
                encoding="utf-8",
            )
            for symbol in ("AAPL", "MSFT", "TSLA"):
                _write_bar_receipt(storage_root, symbol, "2021-01")

            refs = discover_target_candidate_feed_artifacts(
                start_month="2021-01",
                trading_data_root=tmp / "trading-data",
                trading_storage_root=storage_root,
                universe_path=universe_path,
                symbol_limit=2,
            )

            self.assertEqual([ref.symbol for ref in refs], ["AAPL", "MSFT"])

    def test_builds_source_task_key_with_sql_bar_sources(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            refs = [
                FeedArtifactRef(
                    symbol="XLF",
                    month="2016-01",
                    receipt_path=str(tmp / "completion_receipt.json"),
                    bar_source_ref="trading_data.model_01_market_regime_data_acquisition",
                    run_id="run_001",
                    row_count=17,
                    timeframe="1Min",
                )
            ]

            task_key, task_key_path, candidate_path, bar_sources_path, bar_count = build_source_task_key(
                start_month="2016-01",
                end_month="2016-01",
                output_dir=tmp / "out",
                trading_data_output_root=tmp / "td-out",
                refs=refs,
            )

            self.assertEqual(task_key["source"], "m03_target_state_vector_data_acquisition")
            self.assertEqual(bar_count, 17)
            self.assertTrue(task_key_path.exists())
            self.assertTrue(candidate_path.exists())
            self.assertTrue(bar_sources_path.exists())
            self.assertIn("bar_sql_sources", task_key["params"])
            self.assertEqual(
                task_key["downstream_feature_inputs"]["shared_option_chain_source_table"],
                "trading_data.option_chain_state_source",
            )
            self.assertEqual(
                task_key["downstream_feature_inputs"]["model_02_target_state_usage"],
                "target_level_option_chain_state_reduction_only",
            )
            self.assertNotIn("bar_rows_path", task_key["params"])
            source = task_key["params"]["bar_sql_sources"][0]
            self.assertEqual(source["source_symbol"], "XLF")
            self.assertEqual(source["target_symbol"], "XLF")
            self.assertEqual(source["table"], "model_01_market_regime_data_acquisition")
            self.assertEqual(source["timeframe"], "1Min")

    def test_dry_run_writes_task_evidence_but_does_not_call_provider(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,replay_candidate_status\nXLF,active\n", encoding="utf-8")
            _write_bar_receipt(storage_root, "XLF", "2016-01")

            summary = materialize_layer_three_target_state_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=tmp / "trading-data",
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )

            self.assertEqual(summary.contract_type, "manager_layer_three_target_state_input_materialization")
            self.assertEqual(summary.feed_artifact_count, 1)
            self.assertEqual(summary.provider_calls, 0)
            self.assertFalse(summary.model_activation_performed)
            self.assertTrue(Path(summary.task_key_path).exists())
            self.assertTrue(Path(summary.bar_sources_path).exists())
            task_key = json.loads(Path(summary.task_key_path).read_text(encoding="utf-8"))
            self.assertTrue(Path(task_key["output_root"]).is_relative_to(tmp / "manager-storage"))
            self.assertIn("bar_sql_sources", task_key["params"])
            self.assertEqual(summary.option_chain_source_table, "option_chain_state_source")
            self.assertEqual(summary.option_chain_source_usage, "optional_sql_overlay_for_model_02_target_state_target_level_reduction")

    def test_write_summary_reads_downstream_output_table_row_count(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,replay_candidate_status\nAAPL,active\n", encoding="utf-8")
            _write_bar_receipt(storage_root, "AAPL", "2021-01", write_task_key=False, manifest_timeframe="1Day")

            with patch("trading_manager_tasks.layer_three_target_state.subprocess.run") as run:
                run.return_value.returncode = 0
                run.return_value.stdout = json.dumps(
                    {
                        "row_counts": {"model_03_target_state_vector_data_acquisition": 20},
                        "references": [str(tmp / "completion_receipt.json")],
                    }
                )
                run.return_value.stderr = ""

                summary = materialize_layer_three_target_state_inputs(
                    start_month="2021-01",
                    end_month="2021-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=tmp / "trading-data",
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    target_symbol="AAPL",
                    write=True,
                )

            self.assertEqual(summary.source_row_count, 20)

    def test_selected_target_symbol_limits_materialization_to_that_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,replay_candidate_status\nXLF,active\n", encoding="utf-8")
            _write_bar_receipt(storage_root, "AAPL", "2016-01")
            _write_bar_receipt(storage_root, "XLF", "2016-01")

            summary = materialize_layer_three_target_state_inputs(
                start_month="2016-01",
                end_month="2016-01",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=tmp / "trading-data",
                trading_storage_root=storage_root,
                universe_path=universe_path,
                target_symbol="AAPL",
                write=False,
            )
            candidates = [json.loads(line) for line in Path(summary.candidate_rows_path).read_text(encoding="utf-8").splitlines()]

            self.assertEqual(summary.symbols, ("AAPL",))
            self.assertEqual(summary.target_candidate_count, 1)
            self.assertEqual(candidates[0]["routing_symbol_ref"], "AAPL")

    def test_crypto_target_uses_reviewed_layer_two_context_proxy_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            mapping_path = tmp / "target_context_mapping.csv"
            universe_path = tmp / "universe.csv"
            mapping_path.write_text(
                "target_symbol,target_asset_class,spot_ref,layer2_context_symbol,review_status\n"
                "BTC,crypto_spot,BTC,BKCH,accepted\n",
                encoding="utf-8",
            )
            universe_path.write_text("symbol,replay_candidate_status\nBKCH,active\n", encoding="utf-8")
            _write_bar_receipt(storage_root, "BKCH", "2016-01")

            with patch("trading_manager_tasks.layer_three_target_state.DEFAULT_TARGET_CONTEXT_MAPPING", mapping_path):
                summary = materialize_layer_three_target_state_inputs(
                    start_month="2016-01",
                    end_month="2016-01",
                    manager_storage_root=tmp / "manager-storage",
                    trading_data_root=tmp / "trading-data",
                    trading_storage_root=storage_root,
                    universe_path=universe_path,
                    target_symbol="BTC",
                    write=False,
                )

            sources = json.loads(Path(summary.bar_sources_path).read_text(encoding="utf-8"))

            self.assertEqual(summary.symbols, ("BTC",))
            self.assertEqual(summary.feed_artifacts[0].evidence_symbol, "BKCH")
            self.assertEqual(sources[0]["source_symbol"], "BKCH")
            self.assertEqual(sources[0]["target_symbol"], "BTC")

    def test_fold_materialization_uses_one_candidate_per_symbol_across_months(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            storage_root = tmp / "storage"
            universe_path = tmp / "universe.csv"
            universe_path.write_text("symbol,replay_candidate_status\nXLF,active\n", encoding="utf-8")
            for month in ("2016-01", "2016-02"):
                _write_bar_receipt(storage_root, "XLF", month)

            summary = materialize_layer_three_target_state_inputs(
                start_month="2016-01",
                end_month="2016-02",
                manager_storage_root=tmp / "manager-storage",
                trading_data_root=tmp / "trading-data",
                trading_storage_root=storage_root,
                universe_path=universe_path,
                write=False,
            )
            task_key = json.loads(Path(summary.task_key_path).read_text(encoding="utf-8"))
            candidates = [json.loads(line) for line in Path(summary.candidate_rows_path).read_text(encoding="utf-8").splitlines()]
            sources = json.loads(Path(summary.bar_sources_path).read_text(encoding="utf-8"))

            self.assertEqual(summary.feed_artifact_count, 2)
            self.assertEqual(summary.target_candidate_count, 1)
            self.assertEqual(task_key["params"]["start"], "2016-01-01T00:00:00-05:00")
            self.assertEqual(task_key["params"]["end"], "2016-03-01T00:00:00-05:00")
            self.assertEqual(task_key["params"]["timeframe"], "1Min")
            self.assertEqual(candidates[0]["fold_id"], "fold_2016-01_2016-02")
            self.assertEqual(candidates[0]["fold_months"], "2016-01;2016-02")
            self.assertEqual(len(sources), 2)
            self.assertEqual({row["month"] for row in sources}, {"2016-01", "2016-02"})


if __name__ == "__main__":
    unittest.main()

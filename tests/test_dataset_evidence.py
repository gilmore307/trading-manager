import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.dataset_evidence import (
    collect_dataset_evidence_from_rows,
    month_coverage,
    normalize_split_role,
)
from trading_manager_tasks.dataset_expansion import decide_dataset_expansion, load_dataset_evidence


class DatasetEvidenceTests(unittest.TestCase):
    def test_split_role_aliases_and_month_coverage(self):
        self.assertEqual(normalize_split_role("training"), "train")
        self.assertEqual(normalize_split_role("out-of-time"), "forward_holdout")
        self.assertEqual(normalize_split_role("promotion_holdout"), "test")
        self.assertIsNone(normalize_split_role("unknown_bucket"))
        self.assertEqual(month_coverage("2020-01-01T00:00:00", "2020-12-31T00:00:00"), 12)
        self.assertEqual(month_coverage("2020-12-01", "2021-02-01"), 3)

    def test_collects_layer_role_coverage_from_model_governance_rows(self):
        collection = collect_dataset_evidence_from_rows(
            snapshot_rows=[
                {
                    "snapshot_id": "snap_l1",
                    "model_id": "market_regime_model",
                    "data_start_time": "2016-01-01T00:00:00",
                    "data_end_time": "2022-12-31T00:00:00",
                    "feature_row_count": 1000,
                }
            ],
            split_rows=[
                {
                    "split_id": "split_l1_train",
                    "snapshot_id": "snap_l1",
                    "split_name": "train",
                    "split_start_time": "2016-01-01T00:00:00",
                    "split_end_time": "2020-12-31T00:00:00",
                    "split_payload_json": {"sample_count": 700},
                },
                {
                    "split_id": "split_l1_cal",
                    "snapshot_id": "snap_l1",
                    "split_name": "calibration",
                    "split_start_time": "2021-01-01T00:00:00",
                    "split_end_time": "2021-12-31T00:00:00",
                    "split_payload_json": {"sample_count": 150},
                },
                {
                    "split_id": "split_l1_val",
                    "snapshot_id": "snap_l1",
                    "split_name": "validation",
                    "split_start_time": "2022-01-01T00:00:00",
                    "split_end_time": "2022-12-31T00:00:00",
                    "split_payload_json": {"sample_count": 150},
                },
            ],
            label_rows=[{"label_id": "lbl1", "snapshot_id": "snap_l1"}],
            eval_run_rows=[{"eval_run_id": "eval1", "model_id": "market_regime_model", "snapshot_id": "snap_l1", "run_status": "succeeded"}],
        )

        layer_one = collection.summary_row()["layers"]["1"]
        self.assertEqual(layer_one["roles"]["train"]["month_count"], 60)
        self.assertEqual(layer_one["roles"]["calibration"]["month_count"], 12)
        self.assertEqual(layer_one["roles"]["validation"]["sample_count"], 150)
        self.assertEqual(layer_one["roles"]["test"]["month_count"], 0)
        self.assertIn("shadow_monitoring", layer_one["roles"])
        self.assertIn("coverage", layer_one["promotion_gaps"])
        self.assertEqual(collection.provider_calls, 0)
        self.assertFalse(collection.model_activation_performed)
        self.assertFalse(collection.broker_execution_performed)

    def test_collected_evidence_feeds_dataset_expansion_planner(self):
        collection = collect_dataset_evidence_from_rows(
            snapshot_rows=[{"snapshot_id": "snap_l1", "model_id": "market_regime_model", "feature_row_count": 1000}],
            split_rows=[
                {"split_id": "train", "snapshot_id": "snap_l1", "split_name": "train", "split_start_time": "2016-01-01", "split_end_time": "2020-12-31"},
                {"split_id": "cal", "snapshot_id": "snap_l1", "split_name": "calibration", "split_start_time": "2021-01-01", "split_end_time": "2021-12-31"},
                {"split_id": "val", "snapshot_id": "snap_l1", "split_name": "validation", "split_start_time": "2022-01-01", "split_end_time": "2022-12-31"},
            ],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "evidence.json"
            path.write_text(json.dumps(collection.summary_row()), encoding="utf-8")

            evidence = load_dataset_evidence(path)
            decision = decide_dataset_expansion(evidence)

        self.assertEqual(decision.layer, 1)
        self.assertEqual(decision.dataset_role, "test")

    def test_promotion_metric_failure_creates_forward_holdout_gap(self):
        split_rows = []
        for name, start, end in (
            ("train", "2016-01-01", "2020-12-31"),
            ("calibration", "2021-01-01", "2021-12-31"),
            ("validation", "2022-01-01", "2022-12-31"),
            ("test", "2023-01-01", "2023-12-31"),
        ):
            split_rows.append(
                {"split_id": name, "snapshot_id": "snap_l1", "split_name": name, "split_start_time": start, "split_end_time": end}
            )
        collection = collect_dataset_evidence_from_rows(
            snapshot_rows=[{"snapshot_id": "snap_l1", "model_id": "market_regime_model", "feature_row_count": 1000}],
            split_rows=split_rows,
            label_rows=[{"label_id": "lbl1", "snapshot_id": "snap_l1"}],
            eval_run_rows=[{"eval_run_id": "eval1", "model_id": "market_regime_model", "snapshot_id": "snap_l1", "run_status": "succeeded"}],
            metric_rows=[
                {
                    "metric_id": "metric1",
                    "eval_run_id": "eval1",
                    "metric_name": "split_stability_gate",
                    "metric_payload_json": {"gate_status": "failed", "reason": "unstable split stability"},
                }
            ],
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "evidence.json"
            path.write_text(json.dumps(collection.summary_row()), encoding="utf-8")
            evidence = load_dataset_evidence(path)
            decision = decide_dataset_expansion(evidence)

        self.assertEqual(decision.layer, 1)
        self.assertEqual(decision.dataset_role, "forward_holdout")
        self.assertIn("split_stability", decision.reason)


if __name__ == "__main__":
    unittest.main()

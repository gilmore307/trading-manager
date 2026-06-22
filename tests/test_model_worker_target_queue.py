from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "tasks" / "prepare_model_worker_target_queue.py"
_SPEC = importlib.util.spec_from_file_location("prepare_model_worker_target_queue", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_target_queue = _MODULE.build_target_queue


class ModelWorkerTargetQueueTests(unittest.TestCase):
    def test_queue_uses_bootstrap_then_accepted_mapping_targets_without_duplicates(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            mapping = Path(raw_tmp) / "mapping.csv"
            with mapping.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["target_symbol", "review_status"])
                writer.writeheader()
                writer.writerow({"target_symbol": "AAOI", "review_status": "accepted"})
                writer.writerow({"target_symbol": "AAPL", "review_status": "accepted"})
                writer.writerow({"target_symbol": "SKIP", "review_status": "pending"})

            payload = build_target_queue(bootstrap_targets=["AAPL"], mapping_csv=mapping, generated_at_utc="2026-05-20T00:00:00Z")

        self.assertEqual(payload["contract_type"], "manager_model_training_target_queue")
        self.assertEqual([row["symbol"] for row in payload["targets"]], ["AAPL", "AAOI"])
        self.assertFalse(payload["promotion_evidence"])

    def test_queue_drops_bootstrap_targets_without_accepted_mapping(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            mapping = Path(raw_tmp) / "mapping.csv"
            with mapping.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["target_symbol", "review_status"])
                writer.writeheader()
                writer.writerow({"target_symbol": "AAOI", "review_status": "accepted"})

            payload = build_target_queue(bootstrap_targets=["AAPL"], mapping_csv=mapping, generated_at_utc="2026-05-20T00:00:00Z")

        self.assertEqual([row["symbol"] for row in payload["targets"]], ["AAOI"])

    def test_queue_defers_crypto_targets_by_default(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            mapping = Path(raw_tmp) / "mapping.csv"
            with mapping.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["target_symbol", "target_asset_class", "review_status"])
                writer.writeheader()
                writer.writerow({"target_symbol": "BTC", "target_asset_class": "crypto_spot", "review_status": "accepted"})
                writer.writerow({"target_symbol": "AAPL", "target_asset_class": "equity_common", "review_status": "accepted"})

            payload = build_target_queue(bootstrap_targets=["BTC", "AAPL"], mapping_csv=mapping, generated_at_utc="2026-05-20T00:00:00Z")

        self.assertEqual([row["symbol"] for row in payload["targets"]], ["AAPL"])

    def test_queue_can_include_crypto_targets_with_no_option_capability(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            mapping = Path(raw_tmp) / "mapping.csv"
            with mapping.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["target_symbol", "target_asset_class", "review_status"])
                writer.writeheader()
                writer.writerow({"target_symbol": "BTC", "target_asset_class": "crypto_spot", "review_status": "accepted"})
                writer.writerow({"target_symbol": "AAPL", "target_asset_class": "equity_common", "review_status": "accepted"})

            payload = build_target_queue(
                bootstrap_targets=["BTC", "AAPL"],
                mapping_csv=mapping,
                generated_at_utc="2026-05-20T00:00:00Z",
                include_crypto_spot=True,
            )

        self.assertEqual([row["symbol"] for row in payload["targets"]], ["BTC", "AAPL"])
        self.assertEqual(payload["targets"][0]["target_asset_class"], "crypto_spot")
        self.assertEqual(payload["targets"][0]["option_capability"], "structurally_no_listed_options")


if __name__ == "__main__":
    unittest.main()

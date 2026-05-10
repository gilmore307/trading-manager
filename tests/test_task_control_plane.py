from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.control_plane import (
    TASK_PRIORITY_RANKS,
    TASK_SUMMARY_ORDER_BY,
    TaskSystemError,
    load_json_or_jsonl,
    normalize_completion_receipt,
    validate_manager_request,
)


class TaskControlPlaneTests(unittest.TestCase):
    def test_validate_manager_request_keeps_component_request_shape(self):
        row = validate_manager_request(
            {
                "request_id": "mgrreq_sample",
                "request_kind": "data_backfill_month_v1",
                "requested_by": "openclaw",
                "target_component_id": "01_feed_alpaca_bars",
                "target_component_kind": "data_feed",
                "target_repo_id": "trading-data",
                "expected_outputs": "storage://example/output/",
                "policy_refs": ["monthly_backfill_v1"],
                "priority": "high",
                "deadline_at_utc": "2026-05-09T14:30:00Z",
                "parameter_ref": "storage://example/task_key.json",
            }
        )

        self.assertEqual(row["contract_type"], "manager_request_v1")
        self.assertEqual(row["status"], "requested")
        self.assertEqual(row["expected_outputs"], ["storage://example/output/"])
        self.assertEqual(row["priority"], "high")
        self.assertEqual(row["deadline_at_utc"], "2026-05-09T14:30:00Z")
        self.assertTrue(row["dry_run"])

    def test_rejects_unknown_priority(self):
        with self.assertRaises(TaskSystemError):
            validate_manager_request(
                {
                    "request_id": "mgrreq_bad_priority",
                    "request_kind": "data_backfill_month_v1",
                    "requested_by": "openclaw",
                    "target_component_id": "01_feed_alpaca_bars",
                    "target_repo_id": "trading-data",
                    "priority": "whenever",
                }
            )

    def test_task_summary_sort_policy_is_priority_first(self):
        self.assertEqual(list(TASK_PRIORITY_RANKS), ["critical", "high", "normal", "low", "backlog"])
        self.assertTrue(TASK_SUMMARY_ORDER_BY.startswith("priority_rank ASC"))
        self.assertIn("deadline_at_utc ASC NULLS LAST", TASK_SUMMARY_ORDER_BY)

    def test_completion_receipt_normalizes_to_run_artifact_and_ready_signal(self):
        receipt = {
            "task_id": "task_001",
            "bundle": "alpaca_bars",
            "runs": [
                {
                    "run_id": "run_001",
                    "status": "succeeded",
                    "started_at": "2026-05-09T01:00:00Z",
                    "completed_at": "2026-05-09T01:01:00Z",
                    "outputs": ["storage://example/equity_bar.csv"],
                    "row_counts": {"equity_bar": 10},
                    "error": None,
                }
            ],
        }

        rows = normalize_completion_receipt(
            receipt,
            request_id="mgrreq_001",
            component_id="01_feed_alpaca_bars",
            component_kind="data_feed",
            repo_id="trading-data",
            receipt_uri="storage://example/completion_receipt.json",
            receipt_hash="sha256:abc",
            parameter_ref="storage://example/task_key.json",
        )

        self.assertEqual(rows.run_manifests[0]["run_id"], "run_001")
        self.assertEqual(rows.run_manifests[0]["status"], "succeeded")
        self.assertEqual(rows.artifact_refs[0]["artifact_kind"], "component_completion_receipt")
        self.assertEqual(rows.artifact_refs[0]["row_count"], 10)
        self.assertEqual(rows.artifact_refs[1]["artifact_kind"], "equity_bar")
        self.assertEqual(rows.artifact_refs[1]["uri"], "storage://example/equity_bar.csv")
        self.assertEqual(rows.artifact_refs[1]["row_count"], 10)
        self.assertEqual(rows.artifact_refs[1]["media_type"], "text/csv")
        self.assertEqual(rows.ready_signals[0]["signal_kind"], "component_task_ready")
        self.assertEqual(rows.ready_signals[0]["status"], "ready")
        self.assertEqual(rows.ready_signals[0]["artifact_refs"], ["art_receipt_run_001", "art_output_run_001_001"])

    def test_relative_storage_output_refs_are_canonicalized_to_repo_storage_uris(self):
        receipt = {
            "runs": [
                {
                    "run_id": "run_001",
                    "status": "succeeded",
                    "started_at": "2026-05-09T01:00:00Z",
                    "completed_at": "2026-05-09T01:01:00Z",
                    "outputs": ["storage/monthly_backfill_v1/alpaca_bars/SPY/2016-01/saved/equity_bar.csv"],
                    "row_counts": {"equity_bar": 1000},
                }
            ]
        }

        rows = normalize_completion_receipt(
            receipt,
            request_id="mgrreq_spy",
            component_id="01_feed_alpaca_bars",
            component_kind="data_feed",
            repo_id="trading-data",
            receipt_uri="storage://trading-data/monthly_backfill_v1/alpaca_bars/SPY/2016-01/completion_receipt.json",
        )

        output = rows.artifact_refs[1]
        self.assertEqual(output["uri"], "storage://trading-data/monthly_backfill_v1/alpaca_bars/SPY/2016-01/saved/equity_bar.csv")
        self.assertEqual(output["artifact_kind"], "equity_bar")
        self.assertEqual(output["row_count"], 1000)
        self.assertEqual(output["media_type"], "text/csv")

    def test_failed_receipt_does_not_emit_ready_status(self):
        receipt = {
            "run_id": "run_failed",
            "status": "failed",
            "started_at": "2026-05-09T01:00:00Z",
            "completed_at": "2026-05-09T01:01:00Z",
            "error": {"type": "ProviderError", "message": "rate limited"},
        }

        rows = normalize_completion_receipt(
            receipt,
            request_id="mgrreq_failed",
            component_id="05_feed_gdelt_news",
            component_kind="data_feed",
            repo_id="trading-data",
            receipt_uri="storage://example/failed_receipt.json",
        )

        self.assertEqual(rows.run_manifests[0]["status"], "failed")
        self.assertEqual(rows.ready_signals[0]["status"], "failed")
        self.assertIn("rate limited", rows.ready_signals[0]["blocking_reason"])

    def test_missing_started_at_is_rejected(self):
        with self.assertRaises(TaskSystemError):
            normalize_completion_receipt(
                {"run_id": "run_missing", "status": "succeeded"},
                request_id="mgrreq_missing",
                component_id="component",
                component_kind="data_feed",
                repo_id="trading-data",
                receipt_uri="storage://example/receipt.json",
            )

    def test_jsonl_loader_accepts_planner_output_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "requests.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "request_id": "mgrreq_one",
                        "request_kind": "data_backfill_month_v1",
                        "requested_by": "openclaw",
                        "target_component_id": "01_feed_alpaca_bars",
                        "target_repo_id": "trading-data",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            rows = load_json_or_jsonl(path)

        self.assertEqual(rows[0]["request_id"], "mgrreq_one")


if __name__ == "__main__":
    unittest.main()

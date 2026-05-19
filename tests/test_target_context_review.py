from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.target_context_review import (
    TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT,
    TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT,
    build_target_context_agent_review_request,
    handle_target_context_agent_review,
    validate_target_context_agent_review_decision,
    validate_target_context_agent_review_request,
)


class TargetContextReviewTests(unittest.TestCase):
    def test_builds_review_request_for_crypto_proxy_mapping(self) -> None:
        request = build_target_context_agent_review_request(target_symbols=["BTC"])

        normalized = validate_target_context_agent_review_request(request)
        self.assertEqual(normalized["contract_type"], TARGET_CONTEXT_AGENT_REVIEW_REQUEST_CONTRACT)
        self.assertEqual(normalized["target_symbols"], ["BTC"])
        self.assertEqual(normalized["mapping_rows"][0]["layer2_context_symbol"], "BKCH")
        self.assertEqual(normalized["mapping_rows"][0]["listed_proxy_symbol"], "IBIT")
        self.assertIn("do not dispatch provider calls", normalized["forbidden_actions"])
        self.assertIn("target_layer2_context_agent_review_decision", normalized["agent_prompt"])
        self.assertIn("target-context-review", normalized["agent_prompt"])

    def test_builds_review_request_for_multi_context_equity_mapping(self) -> None:
        request = build_target_context_agent_review_request(target_symbols=["AAOI"])

        normalized = validate_target_context_agent_review_request(request)
        self.assertEqual(normalized["target_symbols"], ["AAOI"])
        self.assertEqual(len(normalized["mapping_rows"]), 4)
        self.assertEqual(
            {row["layer2_context_symbol"] for row in normalized["mapping_rows"]},
            {"AIQ", "XLK", "SMH", "XLC"},
        )
        self.assertTrue(all(row["optionable_proxy_status"] == "not_applicable" for row in normalized["mapping_rows"]))
        self.assertIn("target_context_business_mapping", normalized["policy_refs"])

    def test_rejects_missing_target_symbol(self) -> None:
        with self.assertRaisesRegex(TaskSystemError, "not found"):
            build_target_context_agent_review_request(target_symbols=["NOTAREALTARGET"])

    def test_handle_review_writes_queued_artifacts_without_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            result = handle_target_context_agent_review(
                target_symbols=["ETH", "SOL"],
                output_root=Path(raw_tmp),
                call_agent=False,
                write=True,
            )

            self.assertEqual(result["contract_type"], "target_layer2_context_agent_review_result")
            self.assertEqual(result["decision_status"], "queued")
            request_path = Path(result["request_path"])
            decision_path = Path(result["decision_path"])
            self.assertTrue(request_path.exists())
            self.assertTrue(decision_path.exists())
            request = json.loads(request_path.read_text(encoding="utf-8"))
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            self.assertEqual(request["target_symbols"], ["ETH", "SOL"])
            self.assertEqual(validate_target_context_agent_review_decision(decision)["decision_status"], "queued")

    def test_calls_runner_and_accepts_decision_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            runner = tmp / "runner.py"
            runner.write_text(
                "import json, sys\n"
                "request=json.load(sys.stdin)\n"
                "print(json.dumps({\n"
                f"  'contract_type': '{TARGET_CONTEXT_AGENT_REVIEW_DECISION_CONTRACT}',\n"
                "  'schema_version': '1',\n"
                "  'decision_id': 'tl2ctxdecision_test',\n"
                "  'request_ref': request['request_id'],\n"
                "  'agent_ref': request['agent_ref'],\n"
                "  'decision_status': 'approved',\n"
                "  'decision_reason': 'mapping preserves proxy boundary',\n"
                "  'reviewed_rows': request['mapping_rows'],\n"
                "  'completed_at_utc': '2026-05-14T10:00:00Z'\n"
                "}))\n",
                encoding="utf-8",
            )

            result = handle_target_context_agent_review(
                target_symbols=["BTC"],
                output_root=tmp / "out",
                call_agent=True,
                runner_command=f"python3 {runner}",
                write=True,
            )

            self.assertEqual(result["decision_status"], "approved")
            decision = json.loads(Path(result["decision_path"]).read_text(encoding="utf-8"))
            self.assertEqual(decision["reviewed_rows"][0]["target_symbol"], "BTC")


if __name__ == "__main__":
    unittest.main()

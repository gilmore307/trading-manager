from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.scheduler import SchedulerDecision


_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "tasks" / "run_model_group_replay_with_option_auto_acquisition.py"
_SPEC = importlib.util.spec_from_file_location("run_model_group_replay_with_option_auto_acquisition", _SCRIPT_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


class ModelGroupReplayAutoOptionAcquisitionTests(unittest.TestCase):
    def test_successful_replay_with_missing_contract_paths_drains_then_retries(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            alpha_model = tmp / "alpha.json"
            alpha_model.write_text("{}\n", encoding="utf-8")
            status_path = tmp / "status.jsonl"
            latest_path = tmp / "latest.json"
            decision_rows = tmp / "decision_rows.jsonl"
            decision_rows.write_text("{}\n", encoding="utf-8")
            replay_calls: list[str] = []
            path_calls: list[dict] = []

            def fake_run_replay(args, *, run_id: str, database_url: str | None):
                replay_calls.append(run_id)
                return subprocess.CompletedProcess(args=["replay"], returncode=0, stdout="", stderr="")

            def fake_receipt(args, *, run_id: str):
                if len(replay_calls) == 1:
                    return {
                        "decision_rows_ref": str(decision_rows),
                        "option_replay_coverage": {"selected_option_path_missing_count": 2},
                    }
                return {
                    "decision_rows_ref": str(decision_rows),
                    "option_replay_coverage": {"selected_option_path_missing_count": 0},
                }

            def fake_contract_paths(**kwargs):
                path_calls.append(dict(kwargs))
                now = datetime.now(UTC).isoformat()
                return SchedulerDecision(
                    contract_type="manager_scheduler_decision",
                    now_utc=now,
                    now_et=now,
                    decision_status="executed",
                    reason_code="model_group_replay_contract_paths_executed",
                    reason="fixture",
                    market_protection_active=False,
                    resource_pressure_active=False,
                    selected_work="model_group.replay_contract_paths",
                    command=[],
                    provider_calls=2,
                    execution_summary={
                        "selected_contract_requirement_count": 2,
                        "selected_contract_symbol_count": 2,
                        "task_key_path": str(tmp / "task_key.json"),
                    },
                )

            original_run_replay = _MODULE._run_replay
            original_replay_receipt = _MODULE._replay_receipt
            original_contract_paths = _MODULE.run_model_group_replay_contract_paths
            try:
                _MODULE._run_replay = fake_run_replay
                _MODULE._replay_receipt = fake_receipt
                _MODULE.run_model_group_replay_contract_paths = fake_contract_paths
                result = _MODULE.main(
                    [
                        "--candidate-model-ref",
                        "storage://fixture/model",
                        "--after-cost-alpha-model-json",
                        str(alpha_model),
                        "--replay-month",
                        "2021-02",
                        "--max-provider-calls",
                        "3",
                        "--max-replay-attempts",
                        "3",
                        "--execute-provider-acquisition",
                        "--status-jsonl",
                        str(status_path),
                        "--latest-status-json",
                        str(latest_path),
                    ]
                )
            finally:
                _MODULE._run_replay = original_run_replay
                _MODULE._replay_receipt = original_replay_receipt
                _MODULE.run_model_group_replay_contract_paths = original_contract_paths

            self.assertEqual(result, 0)
            self.assertEqual(len(replay_calls), 2)
            self.assertEqual(len(path_calls), 1)
            self.assertEqual(path_calls[0]["decision_rows_ref"], decision_rows)
            self.assertTrue(path_calls[0]["execute_provider_acquisition"])
            self.assertEqual(path_calls[0]["limit"], 3)
            rows = [json.loads(line) for line in status_path.read_text(encoding="utf-8").splitlines()]
            self.assertIn("selected_contract_path_backoff_detected", {row.get("event") for row in rows})
            self.assertIn("selected_contract_path_batch_complete", {row.get("event") for row in rows})
            self.assertEqual(rows[-1]["event"], "completed")
            self.assertEqual(rows[-1]["provider_calls_used"], 2)
            self.assertEqual(json.loads(latest_path.read_text(encoding="utf-8"))["event"], "completed")

    def test_successful_replay_with_missing_contract_paths_requires_provider_flag(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            alpha_model = tmp / "alpha.json"
            alpha_model.write_text("{}\n", encoding="utf-8")
            status_path = tmp / "status.jsonl"
            latest_path = tmp / "latest.json"

            def fake_run_replay(args, *, run_id: str, database_url: str | None):
                return subprocess.CompletedProcess(args=["replay"], returncode=0, stdout="", stderr="")

            def fake_receipt(args, *, run_id: str):
                return {
                    "decision_rows_ref": str(tmp / "decision_rows.jsonl"),
                    "option_replay_coverage": {"selected_option_path_missing_count": 1},
                }

            original_run_replay = _MODULE._run_replay
            original_replay_receipt = _MODULE._replay_receipt
            try:
                _MODULE._run_replay = fake_run_replay
                _MODULE._replay_receipt = fake_receipt
                result = _MODULE.main(
                    [
                        "--candidate-model-ref",
                        "storage://fixture/model",
                        "--after-cost-alpha-model-json",
                        str(alpha_model),
                        "--replay-month",
                        "2021-02",
                        "--max-provider-calls",
                        "3",
                        "--max-replay-attempts",
                        "3",
                        "--status-jsonl",
                        str(status_path),
                        "--latest-status-json",
                        str(latest_path),
                    ]
                )
            finally:
                _MODULE._run_replay = original_run_replay
                _MODULE._replay_receipt = original_replay_receipt

            self.assertEqual(result, 2)
            rows = [json.loads(line) for line in status_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[-1]["event"], "stopped")
            self.assertEqual(rows[-1]["reason"], "selected_contract_path_provider_required")
            self.assertEqual(json.loads(latest_path.read_text(encoding="utf-8"))["reason"], "selected_contract_path_provider_required")

    def test_stops_with_provider_budget_exhausted_after_budget_retry(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            alpha_model = tmp / "alpha.json"
            alpha_model.write_text("{}\n", encoding="utf-8")
            status_path = tmp / "status.jsonl"
            latest_path = tmp / "latest.json"
            artifact = tmp / "option_feature_requirements.jsonl"
            replay_calls: list[str] = []
            drain_kwargs: list[dict] = []

            def fake_run_replay(args, *, run_id: str, database_url: str | None):
                replay_calls.append(run_id)
                return subprocess.CompletedProcess(args=["replay"], returncode=1, stdout="", stderr="option backoff")

            def fake_payload_from_text(text: str):
                return {
                    "requirements_artifact_ref": str(artifact),
                    "missing_count": 2,
                    "required_next_step": "drain option features",
                }

            def fake_drain(*args, **kwargs):
                drain_kwargs.append(dict(kwargs))
                now = datetime.now(UTC).isoformat()
                return SchedulerDecision(
                    contract_type="manager_scheduler_decision",
                    now_utc=now,
                    now_et=now,
                    decision_status="executed",
                    reason_code="model_group_replay_option_feature_repair_executed",
                    reason="fixture",
                    market_protection_active=False,
                    resource_pressure_active=False,
                    selected_work="model_group.replay_option_features",
                    command=[],
                    provider_calls=1,
                    execution_summary={
                        "batch_count": 1,
                        "missing_option_feature_count": 2,
                        "option_source_unavailable_count": 0,
                        "post_repair_missing_count": 1,
                        "required_next_step": "continue replay option feature drain before retrying model_group.replay",
                    },
                )

            original_run_replay = _MODULE._run_replay
            original_payload_from_text = _MODULE.replay_option_feature_payload_from_text
            original_drain = _MODULE.run_model_group_replay_option_features_for_replay_backoff
            try:
                _MODULE._run_replay = fake_run_replay
                _MODULE.replay_option_feature_payload_from_text = fake_payload_from_text
                _MODULE.run_model_group_replay_option_features_for_replay_backoff = fake_drain
                result = _MODULE.main(
                    [
                        "--candidate-model-ref",
                        "storage://fixture/model",
                        "--after-cost-alpha-model-json",
                        str(alpha_model),
                        "--replay-month",
                        "2021-02",
                        "--max-provider-calls",
                        "1",
                        "--max-replay-attempts",
                        "3",
                        "--status-jsonl",
                        str(status_path),
                        "--latest-status-json",
                        str(latest_path),
                    ]
                )
            finally:
                _MODULE._run_replay = original_run_replay
                _MODULE.replay_option_feature_payload_from_text = original_payload_from_text
                _MODULE.run_model_group_replay_option_features_for_replay_backoff = original_drain

            self.assertEqual(result, 2)
            self.assertEqual(len(replay_calls), 2)
            self.assertEqual(drain_kwargs[0]["provider_acquisition_limit"], 1)
            self.assertIsNone(drain_kwargs[0]["feature_repair_limit"])
            rows = [json.loads(line) for line in status_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[-1]["event"], "stopped")
            self.assertEqual(rows[-1]["reason"], "provider_budget_exhausted")
            self.assertNotIn("max_replay_attempts_reached", {row.get("reason") for row in rows})
            self.assertEqual(json.loads(latest_path.read_text(encoding="utf-8"))["reason"], "provider_budget_exhausted")


if __name__ == "__main__":
    unittest.main()

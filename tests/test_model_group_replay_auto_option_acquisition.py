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
    def test_stops_with_provider_budget_exhausted_after_budget_retry(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            alpha_model = tmp / "alpha.json"
            alpha_model.write_text("{}\n", encoding="utf-8")
            status_path = tmp / "status.jsonl"
            latest_path = tmp / "latest.json"
            artifact = tmp / "option_feature_requirements.jsonl"
            replay_calls: list[str] = []

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
            rows = [json.loads(line) for line in status_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[-1]["event"], "stopped")
            self.assertEqual(rows[-1]["reason"], "provider_budget_exhausted")
            self.assertNotIn("max_replay_attempts_reached", {row.get("reason") for row in rows})
            self.assertEqual(json.loads(latest_path.read_text(encoding="utf-8"))["reason"], "provider_budget_exhausted")


if __name__ == "__main__":
    unittest.main()

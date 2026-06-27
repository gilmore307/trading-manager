from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from trading_manager_tasks.scheduler import SchedulerDecision


_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "tasks" / "drain_model_group_replay_option_features.py"
_SPEC = importlib.util.spec_from_file_location("drain_model_group_replay_option_features", _SCRIPT_PATH)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)


class DrainModelGroupReplayOptionFeaturesTests(unittest.TestCase):
    def test_preflight_only_emits_summary_without_drain(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            artifact = tmp / "option_feature_requirements.jsonl"
            artifact.write_text('{"target_ref":"AAPL","timestamp":"2021-02-01T16:00:00-05:00"}\n', encoding="utf-8")
            status_path = tmp / "status.jsonl"
            latest_path = tmp / "latest.json"
            calls: list[Path] = []

            def fake_preflight(path: Path):
                calls.append(path)
                return {
                    "contract_type": "manager_model_group_replay_option_feature_preflight",
                    "raw_requirement_count": 1,
                    "deduped_requirement_count": 1,
                    "estimated_provider_calls_after_preflight": 1,
                }

            original_preflight = _MODULE.replay_option_feature_preflight_summary
            try:
                _MODULE.replay_option_feature_preflight_summary = fake_preflight
                result = _MODULE.main(
                    [
                        "--requirements-artifact-ref",
                        str(artifact),
                        "--preflight-only",
                        "--status-jsonl",
                        str(status_path),
                        "--latest-status-json",
                        str(latest_path),
                    ]
                )
            finally:
                _MODULE.replay_option_feature_preflight_summary = original_preflight

            self.assertEqual(result, 0)
            self.assertEqual(calls, [artifact])
            rows = [json.loads(line) for line in status_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(rows[-1]["event"], "preflight_complete")
            self.assertEqual(rows[-1]["preflight"]["estimated_provider_calls_after_preflight"], 1)
            self.assertEqual(json.loads(latest_path.read_text(encoding="utf-8"))["event"], "preflight_complete")

    def test_default_feature_repair_limit_is_not_batch_size(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            artifact = tmp / "option_feature_requirements.jsonl"
            artifact.write_text('{"target_ref":"AAPL","timestamp":"2021-02-01T16:00:00-05:00"}\n', encoding="utf-8")
            calls: list[dict] = []

            def fake_drain(*args, **kwargs):
                calls.append(dict(kwargs))
                now = datetime.now(UTC).isoformat()
                return SchedulerDecision(
                    contract_type="manager_scheduler_decision",
                    now_utc=now,
                    now_et=now,
                    decision_status="executed",
                    reason_code="model_group_replay_option_features_already_ready",
                    reason="fixture",
                    market_protection_active=False,
                    resource_pressure_active=False,
                    selected_work="model_group.replay_option_features",
                    command=[],
                    execution_summary={
                        "batch_count": 0,
                        "source_missing_count": 0,
                        "source_ready_count": 0,
                        "required_next_step": "retry model_group.replay after the repaired frontier requirements",
                    },
                )

            original_drain = _MODULE.run_model_group_replay_option_features_for_replay_backoff
            try:
                _MODULE.run_model_group_replay_option_features_for_replay_backoff = fake_drain
                result = _MODULE.main(
                    [
                        "--requirements-artifact-ref",
                        str(artifact),
                        "--batch-size",
                        "17",
                        "--max-batches",
                        "1",
                    ]
                )
            finally:
                _MODULE.run_model_group_replay_option_features_for_replay_backoff = original_drain

            self.assertEqual(result, 0)
            self.assertEqual(calls[0]["provider_acquisition_limit"], 17)
            self.assertIsNone(calls[0]["feature_repair_limit"])

    def test_batch_status_preserves_drain_started_at(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            status_path = tmp / "status.jsonl"
            latest_path = tmp / "latest.json"
            latest_path.write_text(
                json.dumps({"drain_started_at_utc": "2026-06-24T17:00:00Z"}) + "\n",
                encoding="utf-8",
            )

            _MODULE._emit(
                {
                    "event": "batch_complete",
                    "batch_index": 2,
                    "batch_size": 12,
                    "elapsed_seconds": 5,
                },
                args=SimpleNamespace(status_jsonl=status_path, latest_status_json=latest_path),
            )

            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            rows = [json.loads(line) for line in status_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(latest["drain_started_at_utc"], "2026-06-24T17:00:00Z")
        self.assertEqual(rows[-1]["drain_started_at_utc"], "2026-06-24T17:00:00Z")


if __name__ == "__main__":
    unittest.main()

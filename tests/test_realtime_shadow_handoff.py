from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks import realtime_shadow_handoff as handoff_module
from trading_manager_tasks.realtime_shadow_handoff import (
    build_realtime_shadow_handoff_control_plane_bundle,
    build_realtime_shadow_handoff_receipt,
    validate_realtime_shadow_handoff_pair,
)


def _decision_input_snapshot() -> dict[str, object]:
    layers = [
        ("layer_01_market_regime", "model_01_market_regime", "market_context_state"),
        ("layer_02_sector_context", "model_02_sector_context", "sector_context_state"),
        ("layer_03_target_state_vector", "model_03_target_state_vector", "target_context_state"),
        ("layer_04_event_failure_risk", "model_04_event_failure_risk", "event_failure_risk_vector"),
        ("layer_05_alpha_confidence", "model_05_alpha_confidence", "alpha_confidence_vector"),
        ("layer_06_position_projection", "model_06_position_projection", "position_projection_vector"),
        ("layer_07_underlying_action", "model_07_underlying_action", "underlying_action_plan"),
        ("layer_08_option_expression", "model_08_option_expression", "option_expression_plan"),
        ("layer_09_event_risk_governor", "model_09_event_risk_governor", "event_context_vector"),
    ]
    return {
        "contract_type": "execution_model_decision_input_snapshot",
        "decision_input_snapshot_id": "rtdecision_unit",
        "decision_time": "2026-05-11T13:30:00+00:00",
        "instrument_ref": "AAPL",
        "dataset_role": "shadow_monitoring",
        "historical_dataset_snapshot_ref": "trading-model://snapshots/historical/unit",
        "frozen_model_config_ref": "trading-model://configs/frozen/unit",
        "realtime_feature_snapshot_ref": "realtime-feature-snapshot://rtfeat_unit",
        "layer_input_refs": [
            {
                "contract_type": "execution_model_decision_layer_input",
                "decision_input_snapshot_id": "rtdecision_unit",
                "model_layer": layer,
                "model_id": model_id,
                "expected_model_output": output,
                "feature_ref": f"realtime-feature://rtfeat_unit/{layer}",
                "upstream_context_refs": [],
                "frozen_model_config_ref": "trading-model://configs/frozen/unit",
                "historical_dataset_snapshot_ref": "trading-model://snapshots/historical/unit",
                "realtime_feature_snapshot_ref": "realtime-feature-snapshot://rtfeat_unit",
                "decision_handoff_status": "ready_for_historical_model_decision_input",
            }
            for layer, model_id, output in layers
        ],
    }


def _route_plan() -> dict[str, object]:
    decision = _decision_input_snapshot()
    routes = []
    for row in decision["layer_input_refs"]:  # type: ignore[index]
        routes.append(
            {
                "contract_type": "model_realtime_decision_layer_route",
                "route_plan_id": "rtdroute_unit",
                "model_layer": row["model_layer"],
                "model_id": row["model_id"],
                "expected_model_output": row["expected_model_output"],
                "feature_ref": row["feature_ref"],
                "upstream_context_refs": row["upstream_context_refs"],
                "frozen_model_config_ref": row["frozen_model_config_ref"],
                "historical_dataset_snapshot_ref": row["historical_dataset_snapshot_ref"],
                "generator_entrypoint_ref": f"trading-model/scripts/models/{row['model_id']}/generate_{row['model_id']}.py",
                "generation_mode": "shadow_monitoring",
                "route_status": "ready_for_fixture_shadow_generation",
            }
        )
    return {
        "contract_type": "model_realtime_decision_route_plan",
        "route_plan_id": "rtdroute_unit",
        "decision_input_snapshot_id": "rtdecision_unit",
        "decision_time": "2026-05-11T13:30:00+00:00",
        "instrument_ref": "AAPL",
        "handoff_mode": "shadow_monitoring",
        "input_validation": {"valid": True},
        "layer_routes": routes,
        "readiness_status": "ready_for_fixture_shadow_historical_model_decision_route",
        "provider_calls_performed": 0,
        "model_activation_performed": False,
        "broker_calls_performed": 0,
    }


class RealtimeShadowHandoffTests(unittest.TestCase):
    def test_validate_realtime_shadow_handoff_pair(self) -> None:
        validation = validate_realtime_shadow_handoff_pair(
            decision_input=_decision_input_snapshot(),
            route_plan=_route_plan(),
            request_id="mgrreq_unit",
        )

        self.assertTrue(validation["valid"])
        self.assertEqual(validation["missing_model_layers"], [])
        self.assertEqual(validation["provider_calls_performed"], 0)
        self.assertFalse(validation["model_activation_performed"])

    def test_build_receipt_is_component_completion_receipt(self) -> None:
        receipt = build_realtime_shadow_handoff_receipt(
            decision_input=_decision_input_snapshot(),
            route_plan=_route_plan(),
            request_id="mgrreq_unit",
        )

        self.assertEqual(receipt["contract_type"], "component_completion_receipt")
        self.assertEqual(receipt["receipt_kind"], "manager_realtime_shadow_handoff_receipt")
        self.assertEqual(receipt["status"], "succeeded")
        self.assertEqual(receipt["runs"][0]["row_counts"]["layer_routes"], 9)
        self.assertFalse(receipt["model_activation_performed"])
        self.assertFalse(receipt["broker_order_construction_performed"])

    def test_build_control_plane_bundle_normalizes_receipt_rows(self) -> None:
        bundle = build_realtime_shadow_handoff_control_plane_bundle(
            decision_input=_decision_input_snapshot(),
            route_plan=_route_plan(),
            request_id="mgrreq_unit",
            receipt_uri="artifact://trading-manager/mgrreq_unit/receipt.json",
        )

        self.assertEqual(bundle["contract_type"], "manager_realtime_shadow_handoff_control_plane_bundle")
        self.assertEqual(bundle["run_manifest_count"], 1)
        self.assertGreaterEqual(bundle["artifact_ref_count"], 4)
        self.assertEqual(bundle["ready_signal_count"], 1)
        ready_rows = [row for row in bundle["normalized_rows"] if row["table"] == "trading_manager.ready_signal"]
        self.assertEqual(ready_rows[0]["signal_kind"], "realtime_shadow_decision_handoff_ready")
        self.assertEqual(ready_rows[0]["status"], "ready")

    def test_build_control_plane_bundle_can_persist_rows_when_explicit(self) -> None:
        captured = []

        def fake_persist(rows, *, database_url=None):
            captured.extend(rows.jsonl_rows())
            self.assertEqual(database_url, "postgresql://unit")

        original = handoff_module.persist_completion_rows
        handoff_module.persist_completion_rows = fake_persist
        try:
            bundle = build_realtime_shadow_handoff_control_plane_bundle(
                decision_input=_decision_input_snapshot(),
                route_plan=_route_plan(),
                request_id="mgrreq_unit",
                receipt_uri="artifact://trading-manager/mgrreq_unit/receipt.json",
                persist_rows=True,
                database_url="postgresql://unit",
            )
        finally:
            handoff_module.persist_completion_rows = original

        self.assertTrue(bundle["persistence_performed"])
        self.assertGreaterEqual(len(captured), 4)
        self.assertTrue(any(row["table"] == "trading_manager.ready_signal" for row in captured))

    def test_forbidden_model_activation_blocks_validation(self) -> None:
        decision = _decision_input_snapshot()
        decision["requested_actions"] = ["model_activation"]
        validation = validate_realtime_shadow_handoff_pair(decision_input=decision, route_plan=_route_plan())

        self.assertFalse(validation["valid"])
        self.assertIn("model_activation", validation["forbidden_actions_present"])

    def test_rehearsal_cli_runs_execution_model_manager_chain(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/tasks/rehearse_realtime_shadow_handoff.py",
                "--fixture-only",
                "--decision-time",
                "2026-05-11T13:30:00+00:00",
                "--available-time",
                "2026-05-11T13:30:01+00:00",
                "--tradeable-time",
                "2026-05-11T13:30:02+00:00",
                "--historical-dataset-snapshot-ref",
                "trading-model://snapshots/historical/unit",
                "--frozen-model-config-ref",
                "trading-model://configs/frozen/unit",
            ],
            check=True,
            cwd=Path(__file__).resolve().parents[1],
            env={"PYTHONPATH": "src"},
            text=True,
            capture_output=True,
        )
        bundle = json.loads(result.stdout)
        self.assertEqual(bundle["contract_type"], "manager_realtime_shadow_handoff_rehearsal")
        self.assertEqual(bundle["rehearsal_status"], "ready")
        self.assertEqual(bundle["provider_calls_performed"], 0)
        self.assertFalse(bundle["broker_order_construction_performed"])
        self.assertEqual(len(bundle["route_plan"]["layer_routes"]), 9)
        self.assertEqual(bundle["manager_handoff"]["receipt"]["status"], "succeeded")

    def test_cli_emits_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            decision_path = Path(temp_dir) / "decision.json"
            route_path = Path(temp_dir) / "route.json"
            decision_path.write_text(json.dumps(_decision_input_snapshot()), encoding="utf-8")
            route_path.write_text(json.dumps(_route_plan()), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/tasks/record_realtime_shadow_handoff.py",
                    "--decision-input",
                    str(decision_path),
                    "--route-plan",
                    str(route_path),
                    "--request-id",
                    "mgrreq_unit",
                ],
                check=True,
                cwd="/root/projects/trading-manager",
                env={"PYTHONPATH": "src"},
                text=True,
                capture_output=True,
            )
        bundle = json.loads(result.stdout)
        self.assertEqual(bundle["receipt"]["status"], "succeeded")
        self.assertEqual(bundle["provider_calls_performed"], 0)


if __name__ == "__main__":
    unittest.main()

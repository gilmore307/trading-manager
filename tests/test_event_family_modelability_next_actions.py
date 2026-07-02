import json
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.event_family_modelability_evidence import build_event_family_modelability_evidence_packet
from trading_manager_tasks.event_family_modelability_next_actions import (
    MODELABILITY_NEXT_ACTION_ROUTE_CONTRACT_TYPE,
    MODELABILITY_NEXT_ACTION_SUMMARY_CONTRACT_TYPE,
    route_event_families_from_database,
    route_packet_next_action,
)


def _news_row(row_id: str, headline: str) -> dict[str, object]:
    return {
        "id": row_id,
        "timeline_headline": headline,
        "summary": "",
        "created_at": "2024-01-03T14:30:00Z",
        "updated_at": "2024-01-03T14:35:00Z",
        "symbols": ["AAPL"],
        "event_link_url": f"https://example.test/{row_id}",
    }


class EventFamilyModelabilityNextActionTests(unittest.TestCase):
    def test_missing_same_family_evidence_prepares_acquisition_task_keys(self) -> None:
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="cpi_release",
            target_symbol="AAPL",
            target_cik="0000320193",
            start_month="2024-01",
            end_month="2024-03",
            scheduled_macro_release_rows=[],
            same_family_observation_count=0,
            minimum_same_family_observations=8,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = route_packet_next_action(
                packet,
                storage_root=root / "storage",
                packet_root=root / "packets",
                next_action_root=root / "routes",
                write_files=True,
            )

            self.assertEqual(route.contract_type, MODELABILITY_NEXT_ACTION_ROUTE_CONTRACT_TYPE)
            self.assertEqual(route.route_status, "prepared_acquisition_task_keys")
            self.assertEqual(route.next_action_owner, "program_acquisition")
            self.assertEqual(route.route_plan["required_feed_ids"], ["05_feed_gdelt_news"])
            self.assertEqual(route.route_plan["task_key_count"], 3)
            self.assertTrue(Path(route.route_artifact_path).exists())
            acquisition_plan = Path(route.route_plan["action_artifact_path"])
            self.assertTrue(acquisition_plan.exists())
            first_task_key = Path(route.route_plan["task_keys"][0]["local_path"])
            self.assertTrue(first_task_key.exists())

    def test_missing_structured_evidence_queues_program_enrichment(self) -> None:
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="cpi_release",
            target_symbol="AAPL",
            target_cik="0000320193",
            start_month="2024-01",
            end_month="2024-12",
            scheduled_macro_release_rows=[
                {
                    "event_id": "cpi-2024-01",
                    "event_time": "2024-01-11T08:30:00-05:00",
                    "scheduled_known_at": "2024-01-01T00:00:00-05:00",
                    "event_type": "CPI Release",
                    "event_scope": "macro",
                    "country": "US",
                    "symbol": "CPI",
                    "source_priority": "approved_calendar",
                    "source_url": "https://example.test/cpi",
                    "raw_artifact_ref": "calendar/cpi-2024-01",
                }
            ],
            same_family_observation_count=8,
            minimum_same_family_observations=8,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = route_packet_next_action(
                packet,
                storage_root=root / "storage",
                packet_root=root / "packets",
                next_action_root=root / "routes",
                write_files=True,
            )

            self.assertEqual(route.route_status, "queued_for_program_enrichment")
            self.assertEqual(route.next_action_owner, "program_enrichment")
            payload = json.loads(Path(route.route_plan["action_artifact_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_type"], "model_06_event_family_structured_evidence_enrichment_plan")
            self.assertIn("actual/surprise fields when applicable", payload["required_outputs"])

    def test_missing_modelability_gates_queues_gate_builder(self) -> None:
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="target_product_price_change_news",
            target_symbol="AAPL",
            target_cik="0000320193",
            start_month="2024-01",
            end_month="2024-12",
            target_news_rows=[
                _news_row("n1", "Apple raises prices on iPhone"),
                _news_row("n2", "Apple cuts prices on iPad"),
            ],
            same_family_observation_count=8,
            minimum_same_family_observations=8,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = route_packet_next_action(
                packet,
                storage_root=root / "storage",
                packet_root=root / "packets",
                next_action_root=root / "routes",
                write_files=True,
            )

            self.assertEqual(route.route_status, "queued_for_modelability_gate_builder")
            self.assertEqual(route.next_action_owner, "program_modelability_gate_builder")
            payload = json.loads(Path(route.route_plan["action_artifact_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["contract_type"], "model_06_event_family_modelability_gate_build_plan")
            self.assertIn("matched_control_gate", payload["missing_gates"])
            self.assertFalse(payload["codex_review_allowed"])

    def test_context_only_admissible_packet_queues_semantic_review_handoff(self) -> None:
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="market_session_calendar_event",
            target_symbol="AAPL",
            target_cik="0000320193",
            start_month="2026-01",
            end_month="2026-12",
            market_session_rows=[
                {
                    "venue": "NASDAQ",
                    "calendar_date": "2026-01-19",
                    "timezone": "America/New_York",
                    "is_trading_day": False,
                    "session_type": "closed",
                    "open_time": None,
                    "close_time": None,
                    "holiday_name": "Martin Luther King Jr. Day",
                    "source_priority": "deterministic_rule",
                    "source_ref": "unit-test",
                }
            ],
            same_family_observation_count=8,
            minimum_same_family_observations=8,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            route = route_packet_next_action(
                packet,
                storage_root=root / "storage",
                packet_root=root / "packets",
                next_action_root=root / "routes",
                write_files=True,
            )

            self.assertEqual(route.route_status, "queued_for_codex_semantic_review")
            self.assertEqual(route.next_action_owner, "codex_semantic_review")
            payload = json.loads(Path(route.route_plan["action_artifact_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["required_skill"], "event-context-projection-review")
            self.assertFalse(payload["codex_review_performed"])

    def test_batch_summary_writes_routes_for_database_packets(self) -> None:
        def fake_build_packet(**kwargs):
            return build_event_family_modelability_evidence_packet(
                event_family_id="target_product_price_change_news",
                target_symbol=kwargs["target_symbol"],
                target_cik=kwargs["target_cik"],
                start_month=kwargs["start_month"],
                end_month=kwargs["end_month"],
                target_news_rows=[_news_row("n1", "Apple raises prices on iPhone")],
                same_family_observation_count=8,
                minimum_same_family_observations=8,
            )

        import trading_manager_tasks.event_family_modelability_next_actions as module

        original = module.build_packet_from_database
        module.build_packet_from_database = fake_build_packet
        try:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                summary = route_event_families_from_database(
                    event_family_ids=("target_product_price_change_news",),
                    target_symbol="AAPL",
                    target_cik="0000320193",
                    start_month="2024-01",
                    end_month="2024-12",
                    storage_root=root / "storage",
                    packet_root=root / "packets",
                    next_action_root=root / "routes",
                    write_files=True,
                )
                self.assertTrue(Path(summary.output_path).exists())
        finally:
            module.build_packet_from_database = original

        self.assertEqual(summary.contract_type, MODELABILITY_NEXT_ACTION_SUMMARY_CONTRACT_TYPE)
        self.assertEqual(summary.event_family_count, 1)
        self.assertEqual(summary.routes[0].route_status, "queued_for_modelability_gate_builder")


if __name__ == "__main__":
    unittest.main()

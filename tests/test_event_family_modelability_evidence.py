import unittest

from trading_manager_tasks.event_family_modelability_evidence import (
    MODELABILITY_EVIDENCE_PACKET_CONTRACT_TYPE,
    build_event_family_modelability_evidence_packet,
)


def _fact(accession: str, filed: str, form: str, fy: str, fp: str, tag: str, value: str):
    return {
        "cik": "0000320193",
        "entity_name": "Apple Inc.",
        "taxonomy": "us-gaap",
        "tag": tag,
        "label": tag,
        "description": "",
        "unit": "USD",
        "fy": fy,
        "fp": fp,
        "form": form,
        "filed": filed,
        "frame": "",
        "end": f"{int(fy) - 1}-12-31" if fp == "Q1" else f"{fy}-09-30",
        "value": value,
        "accession_number": accession,
    }


class EventFamilyModelabilityEvidenceTests(unittest.TestCase):
    def test_builds_multi_observation_earnings_packet_without_review_or_provider_calls(self):
        rows = [
            _fact("a1", "2024-02-02", "10-Q", "2024", "Q1", "Revenues", "119575000000"),
            _fact("a1", "2024-02-02", "10-Q", "2024", "Q1", "NetIncomeLoss", "33916000000"),
            _fact("a2", "2024-11-01", "10-K", "2024", "FY", "Revenues", "391035000000"),
            _fact("a2", "2024-11-01", "10-K", "2024", "FY", "EarningsPerShareDiluted", "6.08"),
        ]

        packet = build_event_family_modelability_evidence_packet(
            event_family_id="earnings",
            target_symbol="aapl",
            target_cik="320193",
            start_month="2024-01",
            end_month="2024-12",
            sec_company_fact_rows=rows,
            minimum_same_family_observations=2,
        )

        self.assertEqual(packet.contract_type, MODELABILITY_EVIDENCE_PACKET_CONTRACT_TYPE)
        self.assertEqual(packet.event_family_id, "company_earnings_or_financial_results")
        self.assertEqual(packet.same_family_observation_count, 2)
        self.assertEqual(packet.provider_calls, 0)
        self.assertFalse(packet.projection_mode_decision_performed)
        self.assertFalse(packet.probability_function_class_decision_performed)
        self.assertFalse(packet.model_training_performed)
        self.assertEqual(packet.deterministic_gate_results["same_family_sample_gate"], "passed")
        self.assertEqual(packet.readiness_status, "ready_with_pit_clock_limitations")
        self.assertEqual(packet.observations[0].target_symbol, "AAPL")
        self.assertEqual(packet.observations[0].normalized_event_parameters["metrics"]["revenue"], 119575000000)

    def test_blocks_single_observation_packet(self):
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="company_earnings_or_financial_results",
            target_symbol="AAPL",
            target_cik="0000320193",
            start_month="2024-01",
            end_month="2024-03",
            sec_company_fact_rows=[
                _fact("a1", "2024-02-02", "10-Q", "2024", "Q1", "Revenues", "119575000000"),
            ],
            minimum_same_family_observations=2,
        )

        self.assertEqual(packet.same_family_observation_count, 1)
        self.assertEqual(packet.readiness_status, "blocked_missing_same_family_evidence")
        self.assertEqual(packet.deterministic_gate_results["same_family_sample_gate"], "blocked")

    def test_builds_concrete_product_price_news_packet_with_truncated_observation_sample(self):
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="target_product_price_change_news",
            target_symbol="AAPL",
            target_cik="0000320193",
            start_month="2024-01",
            end_month="2024-12",
            target_news_rows=[
                {
                    "id": "n1",
                    "timeline_headline": "Apple raises iPhone prices",
                    "summary": "AAPL product pricing increase event summary",
                    "created_at": "2024-01-03T14:30:00Z",
                    "updated_at": "2024-01-03T14:35:00Z",
                    "symbols": ["AAPL"],
                    "event_link_url": "https://example.test/n1",
                }
            ],
            same_family_observation_count=12,
            minimum_same_family_observations=8,
            observation_sample_limit=1,
        )

        self.assertEqual(packet.event_family_id, "target_product_price_change_news")
        self.assertEqual(packet.same_family_observation_count, 12)
        self.assertEqual(packet.observation_sample_count, 1)
        self.assertTrue(packet.observation_rows_truncated)
        self.assertEqual(packet.readiness_status, "ready_for_codex_modelability_review")
        self.assertEqual(packet.observations[0].affected_scope, "target")
        self.assertEqual(packet.observations[0].affected_entities, ("AAPL",))
        self.assertEqual(packet.observations[0].normalized_event_parameters["source_category"], "news")
        self.assertEqual(packet.observations[0].normalized_event_parameters["product_price_change_direction"], "increase")

    def test_rejects_news_source_bucket_as_event_family(self):
        with self.assertRaisesRegex(Exception, "not a source/category bucket"):
            build_event_family_modelability_evidence_packet(
                event_family_id="news",
                target_symbol="AAPL",
                target_cik="0000320193",
                start_month="2024-01",
                end_month="2024-12",
                target_news_rows=[],
            )

    def test_builds_market_session_calendar_packet(self):
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="market_session_calendar_event",
            target_symbol="",
            target_cik="",
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
            same_family_observation_count=10,
            minimum_same_family_observations=8,
        )

        self.assertEqual(packet.event_family_id, "market_session_calendar_event")
        self.assertEqual(packet.deterministic_gate_results["pit_clock_gate"], "passed")
        self.assertEqual(packet.observations[0].affected_scope, "market")
        self.assertEqual(packet.observations[0].source_name, "calendar_market_session")

    def test_blocks_empty_cpi_release_packet(self):
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="cpi_release",
            target_symbol="",
            target_cik="",
            start_month="2024-01",
            end_month="2024-12",
            scheduled_macro_release_rows=[],
            same_family_observation_count=0,
            minimum_same_family_observations=8,
        )

        self.assertEqual(packet.event_family_id, "cpi_release")
        self.assertEqual(packet.readiness_status, "blocked_missing_same_family_evidence")
        self.assertEqual(packet.deterministic_gate_results["same_family_sample_gate"], "blocked")

    def test_builds_concrete_cpi_release_packet(self):
        packet = build_event_family_modelability_evidence_packet(
            event_family_id="consumer_price_index",
            target_symbol="",
            target_cik="",
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

        self.assertEqual(packet.event_family_id, "cpi_release")
        self.assertEqual(packet.readiness_status, "ready_for_codex_modelability_review")
        self.assertEqual(packet.observations[0].normalized_event_parameters["source_category"], "scheduled_macro_release")
        self.assertEqual(packet.observations[0].normalized_event_parameters["event_kind"], "cpi_release")


if __name__ == "__main__":
    unittest.main()

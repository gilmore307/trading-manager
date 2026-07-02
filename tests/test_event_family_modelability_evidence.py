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


if __name__ == "__main__":
    unittest.main()

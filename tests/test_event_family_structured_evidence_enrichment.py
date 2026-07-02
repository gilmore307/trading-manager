import csv
import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.event_family_structured_evidence_enrichment import (
    STRUCTURED_EVIDENCE_ENRICHMENT_CONTRACT_TYPE,
    build_structured_macro_rows_from_te_source,
    enrich_structured_macro_evidence,
)


def _write_te_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "event_time",
        "country",
        "event",
        "source_event_type",
        "reference",
        "actual",
        "previous",
        "consensus",
        "te_forecast",
        "revised",
        "importance",
        "symbol",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class EventFamilyStructuredEvidenceEnrichmentTests(unittest.TestCase):
    def test_builds_cpi_rows_from_trading_economics_calendar_source(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _write_te_csv(
                root
                / "2024-01"
                / "runs"
                / "run-a"
                / "saved"
                / "trading_economics_calendar_event.csv",
                [
                    {
                        "event_time": "2024-01-11T08:30:00-05:00",
                        "country": "United States",
                        "event": "Inflation Rate YoY",
                        "source_event_type": "inflation rate",
                        "reference": "DEC",
                        "actual": "3.4%",
                        "previous": "3.1%",
                        "consensus": "3.2%",
                        "te_forecast": "",
                        "revised": "",
                        "importance": "3",
                        "symbol": "",
                    },
                    {
                        "event_time": "2024-01-12T08:30:00-05:00",
                        "country": "United States",
                        "event": "PPI MoM",
                        "source_event_type": "producer price inflation mom",
                        "reference": "DEC",
                        "actual": "0.2%",
                        "previous": "0.1%",
                        "consensus": "0.1%",
                        "te_forecast": "",
                        "revised": "",
                        "importance": "3",
                        "symbol": "",
                    },
                ],
            )

            file_count, source_count, matched_count, malformed_clock_count, rows = build_structured_macro_rows_from_te_source(
                event_family_id="cpi_release",
                start_month="2024-01",
                end_month="2024-01",
                source_root=root,
            )

        self.assertEqual(file_count, 1)
        self.assertEqual(source_count, 2)
        self.assertEqual(matched_count, 1)
        self.assertEqual(malformed_clock_count, 0)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].scheduled_row["event_type"], "cpi_release")
        self.assertEqual(rows[0].scheduled_row["symbol"], "CPI")
        self.assertEqual(rows[0].result_row["actual_payload"]["value"], 3.4)
        self.assertEqual(rows[0].result_row["consensus_payload"]["value"], 3.2)
        self.assertAlmostEqual(rows[0].result_row["surprise_payload"]["value"], 0.2)

    def test_enrichment_receipt_dry_run_performs_no_provider_or_sql_calls(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "source"
            output_root = Path(td) / "out"
            _write_te_csv(
                root
                / "2024-01"
                / "runs"
                / "run-a"
                / "saved"
                / "trading_economics_calendar_event.csv",
                [
                    {
                        "event_time": "2024-01-12T08:30:00-05:00",
                        "country": "United States",
                        "event": "PPI MoM",
                        "source_event_type": "producer price inflation mom",
                        "reference": "DEC",
                        "actual": "0.2%",
                        "previous": "0.1%",
                        "consensus": "",
                        "te_forecast": "",
                        "revised": "",
                        "importance": "3",
                        "symbol": "",
                    }
                ],
            )

            receipt = enrich_structured_macro_evidence(
                event_family_id="ppi_release",
                start_month="2024-01",
                end_month="2024-01",
                source_root=root,
                output_root=output_root,
                write_sql=False,
                write_file=True,
            )
            self.assertTrue(Path(receipt.output_path).exists())

        self.assertEqual(receipt.contract_type, STRUCTURED_EVIDENCE_ENRICHMENT_CONTRACT_TYPE)
        self.assertEqual(receipt.unique_event_count, 1)
        self.assertEqual(receipt.malformed_clock_row_count, 0)
        self.assertEqual(receipt.consensus_or_forecast_count, 0)
        self.assertEqual(receipt.surprise_count, 0)
        self.assertFalse(receipt.write_sql_performed)
        self.assertEqual(receipt.provider_calls, 0)


if __name__ == "__main__":
    unittest.main()

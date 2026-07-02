"""Build M06 event-family modelability evidence packets.

The packet builder is deterministic glue between acquired source evidence and
Codex semantic review. It performs no provider calls, no modelability judgment,
no parameter training, no model activation, and no broker/account mutation.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO
from zoneinfo import ZoneInfo

from .control_plane import TaskSystemError
from .event_family_modelability_acquisition import (
    DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
    MODELABILITY_ACQUISITION_CONTRACT_TYPE,
    canonical_event_family_id,
)
from .event_feed_coverage import parse_event_feed_time
from .storage_paths import manager_storage_root

MODELABILITY_EVIDENCE_PACKET_CONTRACT_TYPE = "model_06_event_family_modelability_evidence_packet"
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_PACKET_ROOT = manager_storage_root() / "runtime" / "model_06_event_family_modelability" / "evidence_packets"
ET = ZoneInfo("America/New_York")

EARNINGS_METRIC_TAGS = {
    "Revenues": "revenue",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "NetIncomeLoss": "net_income",
    "EarningsPerShareDiluted": "diluted_eps",
    "OperatingIncomeLoss": "operating_income",
    "GrossProfit": "gross_profit",
}


@dataclass(frozen=True)
class EventFamilyObservation:
    event_ref: str
    event_family_id: str
    target_symbol: str
    target_cik: str
    available_time: str
    pit_clock_quality: str
    form: str
    fiscal_year: str
    fiscal_period: str
    period_end: str
    accession_number: str
    source_fact_count: int
    normalized_event_parameters: dict[str, Any]
    source_refs: tuple[str, ...]

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventFamilyModelabilityEvidencePacket:
    contract_type: str
    source_contract_type: str
    model_surface: str
    event_family_id: str
    target_symbol: str
    target_cik: str
    start_month: str
    end_month: str
    minimum_same_family_observations: int
    same_family_observation_count: int
    deterministic_control_policy: str
    agent_role_policy: str
    projection_mode_decision_performed: bool
    probability_function_class_decision_performed: bool
    provider_calls: int
    model_training_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    readiness_status: str
    readiness_reasons: tuple[str, ...]
    deterministic_gate_results: dict[str, Any]
    observations: tuple[EventFamilyObservation, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["observations"] = [item.summary_row() for item in self.observations]
        return row


def _database_url(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    value = os.environ.get("OPENCLAW_DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()
    if value:
        return value
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise TaskSystemError(f"database URL required: pass --database-url or create {DEFAULT_DB_URL_FILE}")


def _month_start(month: str) -> str:
    if len(month) != 7 or month[4] != "-":
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    return f"{month}-01T00:00:00-05:00"


def _next_month(month: str) -> str:
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _month_end_exclusive(month: str) -> str:
    return _month_start(_next_month(month))


def _available_time_from_filed(filed: str) -> tuple[str, str]:
    parsed = parse_event_feed_time(filed)
    if parsed is None:
        return "", "missing_or_unparseable_filed_time"
    if len(str(filed or "").strip()) == 10:
        return parsed.astimezone(ET).isoformat(), "filed_date_only"
    return parsed.astimezone(ET).isoformat(), "timestamped"


def _metric_value(row: Mapping[str, Any]) -> Any:
    raw = row.get("value")
    text = str(raw if raw is not None else "").strip()
    if not text:
        return None
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return text


def _normalize_fact_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append({str(key): value for key, value in dict(row).items()})
    return normalized


def read_sec_company_fact_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return _normalize_fact_rows(csv.DictReader(handle))


def fetch_sec_company_fact_rows_from_database(
    *,
    target_cik: str,
    start_month: str,
    end_month: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency/environment guard
        raise TaskSystemError(f"psycopg is required for SQL evidence packet reads: {exc}") from exc

    cik_variants = sorted({str(target_cik).strip(), str(target_cik).strip().lstrip("0"), str(target_cik).zfill(10)})
    query = """
        SELECT cik, entity_name, taxonomy, tag, label, description, unit, fy, fp,
               form, filed, frame, "end", value, accession_number
        FROM trading_data.feed_08_sec_company_fact
        WHERE cik = ANY(%s)
          AND filed >= %s
          AND filed < %s
          AND form IN ('10-Q', '10-K')
        ORDER BY filed, accession_number, tag
    """
    start = _month_start(start_month)
    end = _month_end_exclusive(end_month)
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (cik_variants, start, end))
            return _normalize_fact_rows(cursor.fetchall())


def build_earnings_observations_from_sec_facts(
    *,
    rows: Sequence[Mapping[str, Any]],
    target_symbol: str,
    target_cik: str,
    event_family_id: str,
) -> tuple[EventFamilyObservation, ...]:
    grouped: dict[tuple[str, str, str, str, str], list[Mapping[str, Any]]] = {}
    for row in rows:
        form = str(row.get("form") or "").strip()
        if form not in {"10-Q", "10-K"}:
            continue
        accession = str(row.get("accession_number") or "").strip()
        filed = str(row.get("filed") or "").strip()
        fy = str(row.get("fy") or "").strip()
        fp = str(row.get("fp") or "").strip()
        if not accession or not filed:
            continue
        key = (accession, filed, form, fy, fp)
        grouped.setdefault(key, []).append(row)

    observations: list[EventFamilyObservation] = []
    for key, fact_rows in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        accession, filed, form, fy, fp = key
        metric_period_ends = sorted(
            {
                str(row.get("end") or "").strip()
                for row in fact_rows
                if EARNINGS_METRIC_TAGS.get(str(row.get("tag") or "").strip()) and str(row.get("end") or "").strip()
            }
        )
        period_end = metric_period_ends[-1] if metric_period_ends else ""
        current_period_rows = [row for row in fact_rows if not period_end or str(row.get("end") or "").strip() == period_end]
        metrics: dict[str, Any] = {}
        metric_units: dict[str, str] = {}
        present_tags: list[str] = []
        for row in current_period_rows:
            tag = str(row.get("tag") or "").strip()
            metric_name = EARNINGS_METRIC_TAGS.get(tag)
            if not metric_name:
                continue
            present_tags.append(tag)
            metrics.setdefault(metric_name, _metric_value(row))
            unit = str(row.get("unit") or "").strip()
            if unit:
                metric_units.setdefault(metric_name, unit)
        available_time, pit_clock_quality = _available_time_from_filed(filed)
        normalized_event_parameters = {
            "event_kind": "company_financial_results",
            "form": form,
            "fiscal_year": fy,
            "fiscal_period": fp,
            "period_end": period_end,
            "metrics": metrics,
            "metric_units": metric_units,
            "present_metric_tags": sorted(set(present_tags)),
            "raw_sec_fact_count": len(fact_rows),
            "current_period_sec_fact_count": len(current_period_rows),
        }
        observations.append(
            EventFamilyObservation(
                event_ref=f"sec-company-financials://{str(target_cik).zfill(10)}/{accession}",
                event_family_id=event_family_id,
                target_symbol=target_symbol.upper(),
                target_cik=str(target_cik).zfill(10),
                available_time=available_time,
                pit_clock_quality=pit_clock_quality,
                form=form,
                fiscal_year=fy,
                fiscal_period=fp,
                period_end=period_end,
                accession_number=accession,
                source_fact_count=len(current_period_rows),
                normalized_event_parameters=normalized_event_parameters,
                source_refs=(f"trading_data.feed_08_sec_company_fact:{accession}",),
            )
        )
    return tuple(observations)


def build_event_family_modelability_evidence_packet(
    *,
    event_family_id: str,
    target_symbol: str,
    target_cik: str,
    start_month: str,
    end_month: str,
    sec_company_fact_rows: Sequence[Mapping[str, Any]],
    minimum_same_family_observations: int = DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
) -> EventFamilyModelabilityEvidencePacket:
    if minimum_same_family_observations < 2:
        raise TaskSystemError("M06 modelability evidence requires multiple same-family observations")
    canonical_family = canonical_event_family_id(event_family_id)
    if canonical_family != "company_earnings_or_financial_results":
        raise TaskSystemError(f"unsupported evidence packet builder route: {event_family_id}")
    observations = build_earnings_observations_from_sec_facts(
        rows=sec_company_fact_rows,
        target_symbol=target_symbol,
        target_cik=target_cik,
        event_family_id=canonical_family,
    )
    reasons: list[str] = []
    sample_gate = "passed" if len(observations) >= minimum_same_family_observations else "blocked"
    if sample_gate != "passed":
        reasons.append("same-family observation count is below threshold")
    pit_quality_values = sorted({item.pit_clock_quality for item in observations})
    pit_gate = "passed_with_date_only_clocks" if pit_quality_values == ["filed_date_only"] else "passed" if observations else "blocked_no_observations"
    if pit_gate != "passed":
        reasons.append("PIT clocks are usable for sequencing but lack precise intraday filing/release time")
    readiness_status = "ready_for_codex_modelability_review" if sample_gate == "passed" and observations else "blocked_missing_same_family_evidence"
    if readiness_status == "ready_for_codex_modelability_review" and pit_gate != "passed":
        readiness_status = "ready_with_pit_clock_limitations"
    return EventFamilyModelabilityEvidencePacket(
        contract_type=MODELABILITY_EVIDENCE_PACKET_CONTRACT_TYPE,
        source_contract_type=MODELABILITY_ACQUISITION_CONTRACT_TYPE,
        model_surface="model_06_residual_event_governance",
        event_family_id=canonical_family,
        target_symbol=target_symbol.upper(),
        target_cik=str(target_cik).zfill(10),
        start_month=start_month,
        end_month=end_month,
        minimum_same_family_observations=minimum_same_family_observations,
        same_family_observation_count=len(observations),
        deterministic_control_policy="Program-built evidence packet; Codex review consumes this packet and performs no provider calls or scope expansion.",
        agent_role_policy="Codex may review taxonomy/modelability/probability-function class only; it must not train parameters or output signed impact.",
        projection_mode_decision_performed=False,
        probability_function_class_decision_performed=False,
        provider_calls=0,
        model_training_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        readiness_status=readiness_status,
        readiness_reasons=tuple(reasons),
        deterministic_gate_results={
            "same_family_sample_gate": sample_gate,
            "pit_clock_gate": pit_gate,
            "source_family_gate": "sec_company_financials_grouped_by_accession",
            "overlap_confounder_gate": "not_performed_in_packet_builder",
            "leakage_gate": "not_performed_in_packet_builder",
            "matched_control_gate": "not_performed_in_packet_builder",
        },
        observations=observations,
    )


def build_packet_from_database(
    *,
    event_family_id: str,
    target_symbol: str,
    target_cik: str,
    start_month: str,
    end_month: str,
    minimum_same_family_observations: int = DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
    database_url: str | None = None,
) -> EventFamilyModelabilityEvidencePacket:
    rows = fetch_sec_company_fact_rows_from_database(
        target_cik=target_cik,
        start_month=start_month,
        end_month=end_month,
        database_url=database_url,
    )
    return build_event_family_modelability_evidence_packet(
        event_family_id=event_family_id,
        target_symbol=target_symbol,
        target_cik=target_cik,
        start_month=start_month,
        end_month=end_month,
        sec_company_fact_rows=rows,
        minimum_same_family_observations=minimum_same_family_observations,
    )


def write_packet(packet: EventFamilyModelabilityEvidencePacket, *, output: TextIO) -> None:
    json.dump(packet.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def packet_output_path(packet: EventFamilyModelabilityEvidencePacket, *, output_root: Path = DEFAULT_PACKET_ROOT) -> Path:
    safe_window = f"{packet.start_month}_{packet.end_month}".replace("-", "_")
    return output_root / packet.event_family_id / packet.target_symbol.lower() / safe_window / "evidence_packet.json"


def persist_packet(packet: EventFamilyModelabilityEvidencePacket, *, output_root: Path = DEFAULT_PACKET_ROOT) -> Path:
    path = packet_output_path(packet, output_root=output_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build M06 event-family modelability evidence packet without provider calls or modelability review.")
    parser.add_argument("--event-family-id", default="company_earnings_or_financial_results")
    parser.add_argument("--target-symbol", default="AAPL")
    parser.add_argument("--target-cik", default="0000320193")
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--minimum-same-family-observations", type=int, default=DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS)
    parser.add_argument("--database-url")
    parser.add_argument("--sec-company-fact-csv", type=Path, action="append", default=[])
    parser.add_argument("--write-file", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_PACKET_ROOT)
    args = parser.parse_args(argv)
    if args.sec_company_fact_csv:
        rows: list[dict[str, Any]] = []
        for path in args.sec_company_fact_csv:
            rows.extend(read_sec_company_fact_csv(path))
        packet = build_event_family_modelability_evidence_packet(
            event_family_id=args.event_family_id,
            target_symbol=args.target_symbol,
            target_cik=args.target_cik,
            start_month=args.start_month,
            end_month=args.end_month,
            sec_company_fact_rows=rows,
            minimum_same_family_observations=args.minimum_same_family_observations,
        )
    else:
        packet = build_packet_from_database(
            event_family_id=args.event_family_id,
            target_symbol=args.target_symbol,
            target_cik=args.target_cik,
            start_month=args.start_month,
            end_month=args.end_month,
            minimum_same_family_observations=args.minimum_same_family_observations,
            database_url=args.database_url,
        )
    if args.write_file:
        path = persist_packet(packet, output_root=args.output_root)
        print(str(path))
    else:
        write_packet(packet, output=sys.stdout)
    return 0


__all__ = [
    "MODELABILITY_EVIDENCE_PACKET_CONTRACT_TYPE",
    "EventFamilyModelabilityEvidencePacket",
    "EventFamilyObservation",
    "build_event_family_modelability_evidence_packet",
    "build_packet_from_database",
    "persist_packet",
    "write_packet",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

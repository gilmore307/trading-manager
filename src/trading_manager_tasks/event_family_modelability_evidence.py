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
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
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

DEFAULT_OBSERVATION_SAMPLE_LIMIT = 100

MODELABILITY_REQUIRED_CONTROL_GATES = (
    "matched_control_gate",
    "overlap_confounder_gate",
    "leakage_gate",
    "horizon_label_gate",
    "fold_calibration_gate",
)

CONTEXT_ONLY_EVENT_FAMILIES = {"market_session_calendar_event"}

PRODUCT_PRICE_CHANGE_TERMS = (
    "price",
    "prices",
    "pricing",
)
PRODUCT_PRICE_SUBJECT_TERMS = (
    "iphone",
    "ipad",
    "mac",
    "macbook",
    "airpods",
    "apple watch",
    "app store",
    "icloud",
    "subscription",
    "service",
    "services",
    "apple sales",
    "device",
    "devices",
)
PRODUCT_LAUNCH_SUBJECT_TERMS = (
    "iphone",
    "ipad",
    "mac",
    "macbook",
    "airpods",
    "apple watch",
    "app store",
    "icloud",
    "vision pro",
    "apple tv",
    "apple intelligence",
)
TARGET_NEWS_CONTEXT_TERMS = (
    "apple",
    "aapl",
    "iphone",
    "ipad",
    "mac",
    "macbook",
    "airpods",
    "apple watch",
    "app store",
    "icloud",
    "vision pro",
)
PRODUCT_PRICE_INCREASE_PHRASES = (
    "price hike",
    "price hikes",
    "price increase",
    "price increases",
    "prices increase",
    "prices increased",
    "prices rise",
    "raises prices",
    "raised prices",
    "raise prices",
    "raises price",
    "raised price",
    "raise price",
    "higher prices",
    "more expensive",
    "get more expensive",
    "gets more expensive",
    "price raised",
    "hike in prices",
)
PRODUCT_PRICE_DECREASE_PHRASES = (
    "price cut",
    "price cuts",
    "price decrease",
    "price decreases",
    "prices decrease",
    "prices decreased",
    "prices fall",
    "cuts prices",
    "cut prices",
    "cutting prices",
    "cuts price",
    "cut price",
    "cutting price",
    "lower prices",
    "lowers prices",
    "lowered prices",
    "reduce prices",
    "reduced prices",
    "discount",
    "discounts",
)
PRODUCT_LAUNCH_PHRASES = (
    "launches",
    "launched",
    "unveils",
    "unveiled",
    "introduces",
    "introduced",
    "announces new",
    "announced new",
    "debut",
    "debuts",
    "release of",
    "releases new",
    "rolls out",
    "rolled out",
)
SUPPLY_CHAIN_DISRUPTION_PHRASES = (
    "production cut",
    "production cuts",
    "shipment delay",
    "shipment delays",
    "supply shortage",
    "supply shortages",
    "component shortage",
    "component shortages",
    "factory shutdown",
    "factory disruptions",
    "supply chain disruption",
    "supply chain disruptions",
)
SUPPLY_CHAIN_CONTEXT_TERMS = (
    "supply chain",
    "supplier",
    "suppliers",
    "factory",
    "factories",
    "shipment",
    "shipments",
    "production",
)
SUPPLY_CHAIN_DISRUPTION_TERMS = (
    "shortage",
    "shortages",
    "delay",
    "delays",
    "delayed",
    "disruption",
    "disruptions",
)
REGULATORY_ANTITRUST_PHRASES = (
    "antitrust",
    "regulator",
    "regulators",
    "regulatory",
    "probe",
    "investigation",
    "investigations",
    "lawsuit",
    "lawsuits",
    "fine",
    "fines",
    "european union",
    "doj",
    "department of justice",
    "app store rules",
)
TARGET_REGULATORY_CONTEXT_TERMS = (
    "apple",
    "aapl",
    "iphone",
    "ipad",
    "mac",
    "app store",
    "icloud",
    "apple pay",
)
ANALYST_PRICE_TARGET_TERMS = (
    "price target",
    "analyst",
    "maintains",
    "rating",
    "overweight",
    "underweight",
    "neutral",
    "buy rating",
    "sell rating",
)

MACRO_RELEASE_EVENT_TYPE_TERMS = {
    "cpi_release": ("cpi", "consumer price index"),
    "ppi_release": ("ppi", "producer price index"),
}

NEWS_EVENT_FAMILY_SQL_TERMS = {
    "target_product_price_change_news": (
        PRODUCT_PRICE_CHANGE_TERMS,
        PRODUCT_PRICE_SUBJECT_TERMS,
        (*PRODUCT_PRICE_INCREASE_PHRASES, *PRODUCT_PRICE_DECREASE_PHRASES),
    ),
    "target_product_launch_news": (
        PRODUCT_LAUNCH_SUBJECT_TERMS,
        PRODUCT_LAUNCH_PHRASES,
    ),
    "target_supply_chain_disruption_news": (
        TARGET_NEWS_CONTEXT_TERMS,
        SUPPLY_CHAIN_CONTEXT_TERMS,
        SUPPLY_CHAIN_DISRUPTION_TERMS,
    ),
    "target_regulatory_antitrust_news": (
        TARGET_REGULATORY_CONTEXT_TERMS,
        REGULATORY_ANTITRUST_PHRASES,
    ),
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
    event_time: str = ""
    affected_scope: str = ""
    affected_entities: tuple[str, ...] = ()
    event_title: str = ""
    event_summary: str = ""
    source_name: str = ""

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
    observation_sample_count: int
    observation_rows_truncated: bool
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


def _stringify_time(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.astimezone(ET).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    parsed = parse_event_feed_time(text)
    if parsed is not None:
        return parsed.astimezone(ET).isoformat()
    return text


def _target_entities(target_symbol: str) -> tuple[str, ...]:
    symbol = target_symbol.strip().upper()
    return (symbol,) if symbol else ()


def _bounded_rows(rows: Sequence[Mapping[str, Any]], *, limit: int) -> list[Mapping[str, Any]]:
    if limit <= 0 or len(rows) <= limit:
        return list(rows)
    if limit == 1:
        return [rows[0]]
    head_count = limit // 2
    tail_count = limit - head_count
    return [*rows[:head_count], *rows[-tail_count:]]


def _text_contains_any(text: str, terms: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _event_text_segments(text: str) -> list[str]:
    return [segment.strip().lower() for segment in re.split(r"[\n.;,?]| - |: ", text) if segment.strip()]


def _product_price_change_direction(text: str) -> str:
    if _text_contains_any(text, ANALYST_PRICE_TARGET_TERMS):
        return ""
    matching_segments = [
        segment
        for segment in _event_text_segments(text)
        if _text_contains_any(segment, PRODUCT_PRICE_SUBJECT_TERMS)
        and _text_contains_any(segment, PRODUCT_PRICE_CHANGE_TERMS)
    ]
    has_increase = any(_text_contains_any(segment, PRODUCT_PRICE_INCREASE_PHRASES) for segment in matching_segments)
    has_decrease = any(_text_contains_any(segment, PRODUCT_PRICE_DECREASE_PHRASES) for segment in matching_segments)
    if has_increase and has_decrease:
        return "mixed_or_unclear"
    if has_increase:
        return "increase"
    if has_decrease:
        return "decrease"
    return ""


def _target_product_launch_match(text: str) -> bool:
    if _text_contains_any(text, ANALYST_PRICE_TARGET_TERMS):
        return False
    matching_segments = [
        segment
        for segment in _event_text_segments(text)
        if _text_contains_any(segment, TARGET_NEWS_CONTEXT_TERMS)
        and _text_contains_any(segment, PRODUCT_LAUNCH_SUBJECT_TERMS)
        and _text_contains_any(segment, PRODUCT_LAUNCH_PHRASES)
    ]
    return bool(matching_segments)


def _target_supply_chain_disruption_match(text: str) -> bool:
    lowered = text.lower()
    if _text_contains_any(lowered, ANALYST_PRICE_TARGET_TERMS):
        return False
    if not _text_contains_any(lowered, TARGET_NEWS_CONTEXT_TERMS):
        return False
    if _text_contains_any(lowered, SUPPLY_CHAIN_DISRUPTION_PHRASES):
        return True
    return _text_contains_any(lowered, SUPPLY_CHAIN_CONTEXT_TERMS) and _text_contains_any(
        lowered, SUPPLY_CHAIN_DISRUPTION_TERMS
    )


def _target_regulatory_antitrust_match(text: str) -> bool:
    lowered = text.lower()
    if _text_contains_any(lowered, ANALYST_PRICE_TARGET_TERMS):
        return False
    return _text_contains_any(lowered, TARGET_REGULATORY_CONTEXT_TERMS) and _text_contains_any(
        lowered, REGULATORY_ANTITRUST_PHRASES
    )


def _news_event_family_subtype(text: str, *, event_family_id: str) -> str:
    if event_family_id == "target_product_price_change_news":
        return _product_price_change_direction(text)
    if event_family_id == "target_product_launch_news":
        return "product_launch_or_announcement" if _target_product_launch_match(text) else ""
    if event_family_id == "target_supply_chain_disruption_news":
        return "supply_chain_disruption" if _target_supply_chain_disruption_match(text) else ""
    if event_family_id == "target_regulatory_antitrust_news":
        return "regulatory_or_antitrust_action" if _target_regulatory_antitrust_match(text) else ""
    return ""


def _observation_subtype(observation: EventFamilyObservation) -> str:
    value = observation.normalized_event_parameters.get("event_subtype")
    if value is None:
        value = observation.normalized_event_parameters.get("product_price_change_direction")
    if value is None:
        value = observation.normalized_event_parameters.get("event_kind")
    return str(value or "").strip()


def _subtype_counts(observations: Sequence[EventFamilyObservation]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for observation in observations:
        subtype = _observation_subtype(observation) or "unspecified"
        counts[subtype] = counts.get(subtype, 0) + 1
    return dict(sorted(counts.items()))


def _family_purity_gate(
    *,
    event_family_id: str,
    observations: Sequence[EventFamilyObservation],
) -> tuple[str, tuple[str, ...], dict[str, Any]]:
    if not observations:
        return "blocked_no_observations", (), {"subtype_counts": {}}
    subtype_counts = _subtype_counts(observations)
    detail = {"subtype_counts": subtype_counts}
    if event_family_id == "target_product_price_change_news" and len(subtype_counts) > 1:
        return (
            "blocked_mixed_family",
            (
                "target_product_price_change_news mixes increase/decrease/unclear rows; split into direction-specific event families before modelability review",
            ),
            detail,
        )
    if "mixed_or_unclear" in subtype_counts:
        return (
            "blocked_mixed_family",
            ("event family sample contains mixed_or_unclear subtype rows",),
            detail,
        )
    return "passed_mechanical_subtype_check", (), detail


def _structured_evidence_gate(
    *,
    event_family_id: str,
    observations: Sequence[EventFamilyObservation],
    pit_gate: str,
) -> tuple[str, tuple[str, ...], dict[str, Any]]:
    detail: dict[str, Any] = {}
    if not observations:
        return "blocked_no_observations", ("structured evidence cannot be checked without observations",), detail
    if event_family_id == "company_earnings_or_financial_results":
        expectation_fields = ("consensus_eps", "consensus_revenue", "expected_eps", "expected_revenue")
        has_expectation_baseline = any(
            any(field in observation.normalized_event_parameters for field in expectation_fields)
            for observation in observations
        )
        detail["expectation_baseline_available"] = has_expectation_baseline
        detail["requires_intraday_release_clock"] = True
        if pit_gate != "passed" or not has_expectation_baseline:
            reasons: list[str] = []
            if pit_gate != "passed":
                reasons.append("earnings/guidance modelability requires timestamped PIT release clocks, not date-only filing clocks")
            if not has_expectation_baseline:
                reasons.append("earnings/guidance modelability requires PIT expectation baseline or surprise fields")
            return "blocked_missing_structured_evidence", tuple(reasons), detail
    if event_family_id in MACRO_RELEASE_EVENT_TYPE_TERMS:
        required_fields = ("actual_value", "consensus_value", "surprise_value")
        has_release_distribution_inputs = any(
            all(observation.normalized_event_parameters.get(field) not in (None, "") for field in required_fields)
            for observation in observations
        )
        detail["actual_consensus_surprise_available"] = has_release_distribution_inputs
        if not has_release_distribution_inputs:
            return (
                "blocked_missing_structured_evidence",
                ("scheduled macro release modelability requires actual/consensus/surprise fields with timestamped release clocks",),
                detail,
            )
    if event_family_id == "target_product_price_change_news":
        direction_values = {
            str(observation.normalized_event_parameters.get("product_price_change_direction") or "").strip()
            for observation in observations
        }
        detail["direction_values"] = sorted(value for value in direction_values if value)
        if len(detail["direction_values"]) != 1 or detail["direction_values"][0] not in {"increase", "decrease"}:
            return (
                "blocked_missing_structured_evidence",
                ("product price change modelability requires a single clean direction-specific subtype",),
                detail,
            )
    if event_family_id in CONTEXT_ONLY_EVENT_FAMILIES:
        return "passed_context_only_structured_evidence", (), detail
    return "passed_minimum_structured_evidence", (), detail


def _modelability_control_gate_results() -> dict[str, str]:
    return {gate: "not_performed_in_packet_builder" for gate in MODELABILITY_REQUIRED_CONTROL_GATES}


def _readiness_from_deterministic_gates(
    *,
    event_family_id: str,
    sample_gate: str,
    pit_gate: str,
    family_purity_gate: str,
    structured_evidence_gate: str,
    control_gate_results: Mapping[str, str],
) -> tuple[str, tuple[str, ...]]:
    if sample_gate != "passed":
        return "blocked_missing_same_family_evidence", ()
    if family_purity_gate.startswith("blocked_mixed_family"):
        return "blocked_mixed_family", ()
    if structured_evidence_gate.startswith("blocked_missing_structured_evidence"):
        return "blocked_missing_structured_evidence", ()
    if event_family_id in CONTEXT_ONLY_EVENT_FAMILIES:
        return "admissible_for_context_only_review", ()
    if pit_gate != "passed":
        return "blocked_missing_structured_evidence", ()
    missing_gates = tuple(
        gate for gate in MODELABILITY_REQUIRED_CONTROL_GATES if control_gate_results.get(gate) != "passed"
    )
    if missing_gates:
        return (
            "blocked_missing_modelability_gates",
            tuple(f"{gate} is required before Codex modelability review" for gate in missing_gates),
        )
    return "admissible_for_modelability_review", ()


def _news_row_matches_event_family(row: Mapping[str, Any], *, event_family_id: str) -> bool:
    headline = str(row.get("timeline_headline") or "").strip()
    summary = str(row.get("summary") or "").strip()
    text = f"{headline}\n{summary}"
    return bool(_news_event_family_subtype(text, event_family_id=event_family_id))


def _scheduled_macro_release_matches_event_family(row: Mapping[str, Any], *, event_family_id: str) -> bool:
    terms = MACRO_RELEASE_EVENT_TYPE_TERMS.get(event_family_id)
    if not terms:
        return False
    text = " ".join(
        str(row.get(key) or "")
        for key in ("event_type", "event_name", "title", "description", "symbol", "raw_artifact_ref")
    )
    return _text_contains_any(text, terms)


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


def fetch_target_news_rows_from_database(
    *,
    target_symbol: str,
    event_family_id: str,
    start_month: str,
    end_month: str,
    database_url: str | None = None,
    sample_limit: int = DEFAULT_OBSERVATION_SAMPLE_LIMIT,
) -> tuple[int, list[dict[str, Any]]]:
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency/environment guard
        raise TaskSystemError(f"psycopg is required for SQL evidence packet reads: {exc}") from exc

    symbol = target_symbol.strip().upper()
    start = _month_start(start_month)
    end = _month_end_exclusive(end_month)
    pattern = f'%"{symbol}"%'
    family_term_groups = NEWS_EVENT_FAMILY_SQL_TERMS.get(event_family_id)
    if not family_term_groups:
        raise TaskSystemError(f"unsupported concrete news event family: {event_family_id}")
    analyst_exclusion_patterns = [f"%{term}%" for term in ANALYST_PRICE_TARGET_TERMS]
    family_filter_parts = []
    family_filter_params: list[list[str]] = []
    for term_group in family_term_groups:
        patterns = [f"%{term}%" for term in term_group]
        family_filter_parts.append(
            "AND (COALESCE(timeline_headline, '') ILIKE ANY(%s) OR COALESCE(summary, '') ILIKE ANY(%s))"
        )
        family_filter_params.extend([patterns, patterns])
    family_filter_parts.append(
        "AND NOT (COALESCE(timeline_headline, '') ILIKE ANY(%s) OR COALESCE(summary, '') ILIKE ANY(%s))"
    )
    family_filter_params.extend([analyst_exclusion_patterns, analyst_exclusion_patterns])
    family_filter = "\n".join(family_filter_parts)
    broad_query = """
        SELECT id, timeline_headline, summary, created_at, updated_at,
               symbols, event_link_url
        FROM trading_data.feed_03_alpaca_news
        WHERE created_at >= %s
          AND created_at < %s
          AND symbols::text ILIKE %s
    """ + family_filter + """
        ORDER BY created_at, id
    """
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(broad_query, (start, end, pattern, *family_filter_params))
            filtered_rows = [
                row
                for row in _normalize_fact_rows(cursor.fetchall())
                if _news_row_matches_event_family(row, event_family_id=event_family_id)
            ]
            return len(filtered_rows), filtered_rows[: max(sample_limit, 0)]


def fetch_market_session_rows_from_database(
    *,
    start_month: str,
    end_month: str,
    database_url: str | None = None,
    sample_limit: int = DEFAULT_OBSERVATION_SAMPLE_LIMIT,
) -> tuple[int, list[dict[str, Any]]]:
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency/environment guard
        raise TaskSystemError(f"psycopg is required for SQL evidence packet reads: {exc}") from exc

    start_date = f"{start_month}-01"
    end_date = f"{_next_month(end_month)}-01"
    count_query = """
        SELECT count(*) AS row_count
        FROM trading_data.calendar_market_session
        WHERE venue IN ('NASDAQ', 'NYSE')
          AND calendar_date >= %s
          AND calendar_date < %s
          AND (holiday_name IS NOT NULL OR session_type = 'early_close')
    """
    sample_query = """
        SELECT venue, calendar_date, timezone, is_trading_day, session_type,
               open_time, close_time, holiday_name, source_priority, source_ref
        FROM trading_data.calendar_market_session
        WHERE venue IN ('NASDAQ', 'NYSE')
          AND calendar_date >= %s
          AND calendar_date < %s
          AND (holiday_name IS NOT NULL OR session_type = 'early_close')
        ORDER BY calendar_date, venue
        LIMIT %s
    """
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(count_query, (start_date, end_date))
            row_count = int(cursor.fetchone()["row_count"])
            cursor.execute(sample_query, (start_date, end_date, max(sample_limit, 0)))
            return row_count, _normalize_fact_rows(cursor.fetchall())


def fetch_scheduled_macro_release_rows_from_database(
    *,
    event_family_id: str,
    start_month: str,
    end_month: str,
    database_url: str | None = None,
    sample_limit: int = DEFAULT_OBSERVATION_SAMPLE_LIMIT,
) -> tuple[int, list[dict[str, Any]]]:
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency/environment guard
        raise TaskSystemError(f"psycopg is required for SQL evidence packet reads: {exc}") from exc

    start = _month_start(start_month)
    end = _month_end_exclusive(end_month)
    terms = MACRO_RELEASE_EVENT_TYPE_TERMS.get(event_family_id)
    if not terms:
        raise TaskSystemError(f"unsupported concrete scheduled macro event family: {event_family_id}")
    event_type_patterns = [f"%{term}%" for term in terms]
    family_filter = """
          AND (
            event_type ILIKE ANY(%s)
            OR COALESCE(symbol, '') ILIKE ANY(%s)
            OR COALESCE(raw_artifact_ref, '') ILIKE ANY(%s)
          )
    """
    count_query = """
        SELECT count(*) AS row_count
        FROM trading_data.calendar_scheduled_event
        WHERE event_time >= %s
          AND event_time < %s
    """ + family_filter
    sample_query = """
        SELECT *
        FROM trading_data.calendar_scheduled_event
        WHERE event_time >= %s
          AND event_time < %s
    """ + family_filter + """
        ORDER BY event_time
        LIMIT %s
    """
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            filter_params = (event_type_patterns, event_type_patterns, event_type_patterns)
            cursor.execute(count_query, (start, end, *filter_params))
            row_count = int(cursor.fetchone()["row_count"])
            cursor.execute(sample_query, (start, end, *filter_params, max(sample_limit, 0)))
            return row_count, _normalize_fact_rows(cursor.fetchall())


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


def build_target_news_observations(
    *,
    rows: Sequence[Mapping[str, Any]],
    target_symbol: str,
    target_cik: str,
    event_family_id: str,
) -> tuple[EventFamilyObservation, ...]:
    observations: list[EventFamilyObservation] = []
    for row in rows:
        if not _news_row_matches_event_family(row, event_family_id=event_family_id):
            continue
        row_id = str(row.get("id") or "").strip()
        created_at = _stringify_time(row.get("created_at"))
        updated_at = _stringify_time(row.get("updated_at"))
        headline = str(row.get("timeline_headline") or "").strip()
        summary = str(row.get("summary") or "").strip()
        text = f"{headline}\n{summary}"
        event_subtype = _news_event_family_subtype(text, event_family_id=event_family_id)
        symbols = row.get("symbols")
        if isinstance(symbols, str):
            affected_entities = (target_symbol.upper(),)
        elif isinstance(symbols, (list, tuple, set)):
            affected_entities = tuple(sorted({str(item).upper() for item in symbols if str(item).strip()}))
        else:
            affected_entities = _target_entities(target_symbol)
        normalized_event_parameters = {
            "event_kind": event_family_id,
            "source_category": "news",
            "headline": headline,
            "summary_available": bool(summary),
            "event_subtype": event_subtype,
            "updated_at": updated_at,
            "symbols": list(affected_entities),
            "source_url": str(row.get("event_link_url") or "").strip(),
            "raw_source_table": "trading_data.feed_03_alpaca_news",
        }
        if event_family_id == "target_product_price_change_news":
            normalized_event_parameters["product_price_change_direction"] = event_subtype
        observations.append(
            EventFamilyObservation(
                event_ref=f"alpaca-news://{row_id or created_at}",
                event_family_id=event_family_id,
                target_symbol=target_symbol.upper(),
                target_cik=str(target_cik).zfill(10),
                available_time=created_at,
                pit_clock_quality="timestamped" if created_at else "missing_or_unparseable_created_at",
                form="",
                fiscal_year="",
                fiscal_period="",
                period_end="",
                accession_number="",
                source_fact_count=1,
                normalized_event_parameters=normalized_event_parameters,
                source_refs=(f"trading_data.feed_03_alpaca_news:{row_id}",),
                event_time=created_at,
                affected_scope="target",
                affected_entities=affected_entities,
                event_title=headline,
                event_summary=summary,
                source_name="alpaca_news",
            )
        )
    return tuple(observations)


def build_market_session_observations(
    *,
    rows: Sequence[Mapping[str, Any]],
    event_family_id: str,
) -> tuple[EventFamilyObservation, ...]:
    observations: list[EventFamilyObservation] = []
    for row in rows:
        calendar_date = str(row.get("calendar_date") or "").strip()
        venue = str(row.get("venue") or "").strip()
        session_type = str(row.get("session_type") or "").strip()
        holiday_name = str(row.get("holiday_name") or "").strip()
        close_time = _stringify_time(row.get("close_time"))
        open_time = _stringify_time(row.get("open_time"))
        event_title = holiday_name or f"{venue} {session_type}".strip()
        is_trading_day = row.get("is_trading_day")
        normalized_event_parameters = {
            "event_kind": "market_session_calendar_event",
            "venue": venue,
            "calendar_date": calendar_date,
            "is_trading_day": bool(is_trading_day),
            "session_type": session_type,
            "holiday_name": holiday_name,
            "open_time": open_time,
            "close_time": close_time,
            "source_priority": str(row.get("source_priority") or "").strip(),
            "source_ref": str(row.get("source_ref") or "").strip(),
        }
        observations.append(
            EventFamilyObservation(
                event_ref=f"market-session-calendar://{venue}/{calendar_date}/{session_type or 'closed'}",
                event_family_id=event_family_id,
                target_symbol="",
                target_cik="",
                available_time=_stringify_time(row.get("open_time")) or calendar_date,
                pit_clock_quality="deterministic_calendar_rule",
                form="",
                fiscal_year="",
                fiscal_period="",
                period_end="",
                accession_number="",
                source_fact_count=1,
                normalized_event_parameters=normalized_event_parameters,
                source_refs=(f"trading_data.calendar_market_session:{venue}:{calendar_date}",),
                event_time=open_time or calendar_date,
                affected_scope="market",
                affected_entities=(venue,) if venue else (),
                event_title=event_title,
                event_summary=f"{venue} {calendar_date} {session_type} {holiday_name}".strip(),
                source_name="calendar_market_session",
            )
        )
    return tuple(observations)


def build_scheduled_macro_release_observations(
    *,
    rows: Sequence[Mapping[str, Any]],
    event_family_id: str,
) -> tuple[EventFamilyObservation, ...]:
    observations: list[EventFamilyObservation] = []
    for row in rows:
        if not _scheduled_macro_release_matches_event_family(row, event_family_id=event_family_id):
            continue
        event_id = str(row.get("event_id") or "").strip()
        event_time = _stringify_time(row.get("event_time"))
        known_at = _stringify_time(row.get("scheduled_known_at"))
        event_type = str(row.get("event_type") or "").strip()
        country = str(row.get("country") or "").strip()
        normalized_event_parameters = {
            "event_kind": event_family_id,
            "source_category": "scheduled_macro_release",
            "event_type": event_type,
            "event_scope": str(row.get("event_scope") or "").strip(),
            "country": country,
            "symbol": str(row.get("symbol") or "").strip(),
            "scheduled_known_at": known_at,
            "source_priority": str(row.get("source_priority") or "").strip(),
            "source_url": str(row.get("source_url") or "").strip(),
            "raw_artifact_ref": str(row.get("raw_artifact_ref") or "").strip(),
        }
        observations.append(
            EventFamilyObservation(
                event_ref=f"scheduled-macro-release://{event_id or event_time}",
                event_family_id=event_family_id,
                target_symbol="",
                target_cik="",
                available_time=known_at,
                pit_clock_quality="timestamped" if known_at else "missing_scheduled_known_at",
                form="",
                fiscal_year="",
                fiscal_period="",
                period_end="",
                accession_number="",
                source_fact_count=1,
                normalized_event_parameters=normalized_event_parameters,
                source_refs=(f"trading_data.calendar_scheduled_event:{event_id}",),
                event_time=event_time,
                affected_scope=str(row.get("event_scope") or "").strip() or "macro",
                affected_entities=(country,) if country else (),
                event_title=event_type,
                event_summary=f"{country} {event_type}".strip(),
                source_name="calendar_scheduled_event",
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
    sec_company_fact_rows: Sequence[Mapping[str, Any]] = (),
    target_news_rows: Sequence[Mapping[str, Any]] = (),
    market_session_rows: Sequence[Mapping[str, Any]] = (),
    scheduled_macro_release_rows: Sequence[Mapping[str, Any]] = (),
    same_family_observation_count: int | None = None,
    minimum_same_family_observations: int = DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
    observation_sample_limit: int = DEFAULT_OBSERVATION_SAMPLE_LIMIT,
) -> EventFamilyModelabilityEvidencePacket:
    if minimum_same_family_observations < 2:
        raise TaskSystemError("M06 modelability evidence requires multiple same-family observations")
    canonical_family = canonical_event_family_id(event_family_id)
    source_family_gate = ""
    if canonical_family == "company_earnings_or_financial_results":
        observations = build_earnings_observations_from_sec_facts(
            rows=sec_company_fact_rows,
            target_symbol=target_symbol,
            target_cik=target_cik,
            event_family_id=canonical_family,
        )
        source_family_gate = "sec_company_financials_grouped_by_accession"
    elif canonical_family in NEWS_EVENT_FAMILY_SQL_TERMS:
        sample_rows = _bounded_rows(target_news_rows, limit=observation_sample_limit)
        observations = build_target_news_observations(
            rows=sample_rows,
            target_symbol=target_symbol,
            target_cik=target_cik,
            event_family_id=canonical_family,
        )
        source_family_gate = f"alpaca_news_{canonical_family}_rows"
    elif canonical_family == "market_session_calendar_event":
        sample_rows = _bounded_rows(market_session_rows, limit=observation_sample_limit)
        observations = build_market_session_observations(rows=sample_rows, event_family_id=canonical_family)
        source_family_gate = "calendar_market_session_holiday_or_early_close_rows"
    elif canonical_family in MACRO_RELEASE_EVENT_TYPE_TERMS:
        sample_rows = _bounded_rows(scheduled_macro_release_rows, limit=observation_sample_limit)
        observations = build_scheduled_macro_release_observations(rows=sample_rows, event_family_id=canonical_family)
        source_family_gate = f"calendar_scheduled_event_{canonical_family}_rows"
    else:
        raise TaskSystemError(f"unsupported evidence packet builder route: {event_family_id}")
    total_observations = len(observations) if same_family_observation_count is None else same_family_observation_count
    reasons: list[str] = []
    sample_gate = "passed" if total_observations >= minimum_same_family_observations else "blocked"
    if sample_gate != "passed":
        reasons.append("same-family observation count is below threshold")
    pit_quality_values = sorted({item.pit_clock_quality for item in observations})
    if not observations:
        pit_gate = "blocked_no_observations"
    elif pit_quality_values == ["filed_date_only"]:
        pit_gate = "passed_with_date_only_clocks"
    elif all(value in {"timestamped", "deterministic_calendar_rule"} for value in pit_quality_values):
        pit_gate = "passed"
    else:
        pit_gate = "passed_with_clock_limitations"
    if pit_gate == "passed_with_date_only_clocks":
        reasons.append("PIT clocks are date-only filing clocks; intraday release timing is not available in this packet")
    elif pit_gate != "passed":
        reasons.append("PIT clocks are usable for sequencing but lack precise intraday filing/release time")
    family_purity_gate, family_purity_reasons, family_purity_detail = _family_purity_gate(
        event_family_id=canonical_family,
        observations=observations,
    )
    reasons.extend(family_purity_reasons)
    structured_evidence_gate, structured_evidence_reasons, structured_evidence_detail = _structured_evidence_gate(
        event_family_id=canonical_family,
        observations=observations,
        pit_gate=pit_gate,
    )
    reasons.extend(structured_evidence_reasons)
    modelability_control_gates = _modelability_control_gate_results()
    readiness_status, readiness_gate_reasons = _readiness_from_deterministic_gates(
        event_family_id=canonical_family,
        sample_gate=sample_gate,
        pit_gate=pit_gate,
        family_purity_gate=family_purity_gate,
        structured_evidence_gate=structured_evidence_gate,
        control_gate_results=modelability_control_gates,
    )
    reasons.extend(readiness_gate_reasons)
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
        same_family_observation_count=total_observations,
        observation_sample_count=len(observations),
        observation_rows_truncated=total_observations > len(observations),
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
            "source_family_gate": source_family_gate,
            "family_purity_gate": family_purity_gate,
            "family_purity_detail": family_purity_detail,
            "structured_evidence_gate": structured_evidence_gate,
            "structured_evidence_detail": structured_evidence_detail,
            **modelability_control_gates,
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
    observation_sample_limit: int = DEFAULT_OBSERVATION_SAMPLE_LIMIT,
    database_url: str | None = None,
) -> EventFamilyModelabilityEvidencePacket:
    canonical_family = canonical_event_family_id(event_family_id)
    if canonical_family == "company_earnings_or_financial_results":
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
            observation_sample_limit=observation_sample_limit,
        )
    if canonical_family in NEWS_EVENT_FAMILY_SQL_TERMS:
        row_count, rows = fetch_target_news_rows_from_database(
            target_symbol=target_symbol,
            event_family_id=canonical_family,
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
            sample_limit=observation_sample_limit,
        )
        return build_event_family_modelability_evidence_packet(
            event_family_id=event_family_id,
            target_symbol=target_symbol,
            target_cik=target_cik,
            start_month=start_month,
            end_month=end_month,
            target_news_rows=rows,
            same_family_observation_count=row_count,
            minimum_same_family_observations=minimum_same_family_observations,
            observation_sample_limit=observation_sample_limit,
        )
    if canonical_family == "market_session_calendar_event":
        row_count, rows = fetch_market_session_rows_from_database(
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
            sample_limit=observation_sample_limit,
        )
        return build_event_family_modelability_evidence_packet(
            event_family_id=event_family_id,
            target_symbol=target_symbol,
            target_cik=target_cik,
            start_month=start_month,
            end_month=end_month,
            market_session_rows=rows,
            same_family_observation_count=row_count,
            minimum_same_family_observations=minimum_same_family_observations,
            observation_sample_limit=observation_sample_limit,
        )
    if canonical_family in MACRO_RELEASE_EVENT_TYPE_TERMS:
        row_count, rows = fetch_scheduled_macro_release_rows_from_database(
            event_family_id=canonical_family,
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
            sample_limit=observation_sample_limit,
        )
        return build_event_family_modelability_evidence_packet(
            event_family_id=event_family_id,
            target_symbol=target_symbol,
            target_cik=target_cik,
            start_month=start_month,
            end_month=end_month,
            scheduled_macro_release_rows=rows,
            same_family_observation_count=row_count,
            minimum_same_family_observations=minimum_same_family_observations,
            observation_sample_limit=observation_sample_limit,
        )
    raise TaskSystemError(f"unsupported evidence packet builder route: {event_family_id}")


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
    parser.add_argument("--observation-sample-limit", type=int, default=DEFAULT_OBSERVATION_SAMPLE_LIMIT)
    parser.add_argument("--database-url")
    parser.add_argument("--sec-company-fact-csv", type=Path, action="append", default=[])
    parser.add_argument("--write-file", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_PACKET_ROOT)
    args = parser.parse_args(argv)
    try:
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
                observation_sample_limit=args.observation_sample_limit,
            )
        else:
            packet = build_packet_from_database(
                event_family_id=args.event_family_id,
                target_symbol=args.target_symbol,
                target_cik=args.target_cik,
                start_month=args.start_month,
                end_month=args.end_month,
                minimum_same_family_observations=args.minimum_same_family_observations,
                observation_sample_limit=args.observation_sample_limit,
                database_url=args.database_url,
            )
    except TaskSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
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
    "fetch_market_session_rows_from_database",
    "fetch_scheduled_macro_release_rows_from_database",
    "fetch_target_news_rows_from_database",
    "build_packet_from_database",
    "persist_packet",
    "write_packet",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

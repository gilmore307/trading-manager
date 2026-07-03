"""Materialize structured event-family evidence from reviewed local sources.

This module owns deterministic enrichment work after an M03 event-family modelability packet
blocks on missing structured evidence. It reads existing local source artifacts
and writes canonical SQL calendar tables; it performs no provider calls, Codex
review, model training, model activation, broker execution, or dashboard writes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .event_family_modelability_evidence import (
    MACRO_RELEASE_EVENT_TYPE_TERMS,
    _database_url,
    _next_month,
    _stringify_time,
)
from .event_feed_coverage import parse_event_feed_time
from .storage_paths import manager_storage_root

STRUCTURED_EVIDENCE_ENRICHMENT_CONTRACT_TYPE = "model_06_event_family_structured_evidence_enrichment_receipt"
DEFAULT_TE_SOURCE_ROOT = (
    Path("/root/projects/trading-storage/storage/01_source_data/monthly_backfill")
    / "trading_economics_calendar_web"
)
DEFAULT_OUTPUT_ROOT = (
    manager_storage_root()
    / "runtime"
    / "model_06_event_family_modelability"
    / "structured_evidence_enrichment"
)

_MACRO_SYMBOLS = {
    "cpi_release": "CPI",
    "ppi_release": "PPI",
}

_MACRO_CANONICAL_TYPE = {
    "cpi_release": "cpi_release",
    "ppi_release": "ppi_release",
}

_MACRO_EXCLUDE_TERMS = {
    "cpi_release": ("producer price", "ppi"),
    "ppi_release": ("consumer price", "cpi", "inflation rate"),
}


@dataclass(frozen=True)
class StructuredMacroEventRows:
    scheduled_row: dict[str, Any]
    result_row: dict[str, Any]


@dataclass(frozen=True)
class EventFamilyStructuredEvidenceEnrichmentReceipt:
    contract_type: str
    event_family_id: str
    start_month: str
    end_month: str
    source_root: str
    output_path: str
    source_file_count: int
    source_row_count: int
    matched_source_row_count: int
    malformed_clock_row_count: int
    unique_event_count: int
    scheduled_event_rows_written: int
    event_result_rows_written: int
    consensus_or_forecast_count: int
    surprise_count: int
    write_sql_performed: bool
    provider_calls: int
    codex_review_performed: bool
    model_training_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    next_rebuild_gate: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _month_range(start_month: str, end_month: str) -> tuple[str, ...]:
    months: list[str] = []
    current = start_month
    while current <= end_month:
        months.append(current)
        current = _next_month(current)
    return tuple(months)


def _candidate_te_csv_files(source_root: Path, *, start_month: str, end_month: str) -> tuple[Path, ...]:
    paths: list[Path] = []
    for month in _month_range(start_month, end_month):
        month_dir = source_root / month
        if not month_dir.exists():
            continue
        paths.extend(sorted(month_dir.glob("runs/*/saved/trading_economics_calendar_event.csv")))
    return tuple(paths)


def _read_csv_rows(paths: Iterable[Path]) -> tuple[int, list[dict[str, str]]]:
    rows: list[dict[str, str]] = []
    file_count = 0
    for path in paths:
        file_count += 1
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                normalized = {str(key): str(value or "").strip() for key, value in row.items()}
                normalized["_source_file"] = str(path)
                rows.append(normalized)
    return file_count, rows


def _text_contains_any(text: str, terms: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _te_row_matches_event_family(row: Mapping[str, Any], *, event_family_id: str) -> bool:
    terms = MACRO_RELEASE_EVENT_TYPE_TERMS.get(event_family_id)
    if not terms:
        raise TaskSystemError(f"unsupported structured evidence enrichment family: {event_family_id}")
    text = " ".join(str(row.get(key) or "") for key in ("event", "source_event_type", "symbol")).lower()
    if _text_contains_any(text, _MACRO_EXCLUDE_TERMS.get(event_family_id, ())):
        return False
    return _text_contains_any(text, terms)


def _te_row_quality_score(row: Mapping[str, Any]) -> tuple[int, int, int, str]:
    structured_count = sum(
        1
        for key in ("actual", "consensus", "te_forecast", "previous", "event_time", "reference")
        if str(row.get(key) or "").strip()
    )
    surprise_ready = int(
        bool(str(row.get("actual") or "").strip())
        and bool(str(row.get("consensus") or "").strip() or str(row.get("te_forecast") or "").strip())
    )
    path = str(row.get("_source_file") or "")
    authenticated_refresh = int("te_authenticated_baseline_refresh" in path)
    return structured_count, surprise_ready, authenticated_refresh, path


def _parse_numeric_value(raw: str) -> float | None:
    text = str(raw or "").strip()
    if not text:
        return None
    cleaned = text.replace(",", "")
    multiplier = 1.0
    if cleaned.endswith("%"):
        cleaned = cleaned[:-1].strip()
    elif cleaned[-1:].upper() == "K":
        multiplier = 1_000.0
        cleaned = cleaned[:-1].strip()
    elif cleaned[-1:].upper() == "M":
        multiplier = 1_000_000.0
        cleaned = cleaned[:-1].strip()
    elif cleaned[-1:].upper() == "B":
        multiplier = 1_000_000_000.0
        cleaned = cleaned[:-1].strip()
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None


def _payload(raw: str, *, unit: str = "") -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    payload: dict[str, Any] = {"raw": text}
    numeric = _parse_numeric_value(text)
    if numeric is not None:
        payload["value"] = numeric
    if unit:
        payload["unit"] = unit
    return payload


def _event_id_for_te_row(row: Mapping[str, Any], *, event_family_id: str) -> str:
    seed = "|".join(
        str(row.get(key) or "").strip()
        for key in ("event_time", "country", "event", "source_event_type", "reference")
    )
    digest = hashlib.sha256(f"{event_family_id}|{seed}".encode("utf-8")).hexdigest()[:16]
    return f"te:{event_family_id}:{digest}"


def _event_date(event_time: str) -> str:
    text = _stringify_time(event_time)
    if not text:
        return ""
    return text[:10]


def _raw_ref(row: Mapping[str, Any]) -> str:
    source_file = str(row.get("_source_file") or "").strip()
    event_time = str(row.get("event_time") or "").strip()
    event = str(row.get("event") or "").strip()
    return f"trading-economics-calendar-web:{source_file}:{event_time}:{event}"


def _unit_for_row(row: Mapping[str, Any]) -> str:
    for key in ("actual", "previous", "consensus", "te_forecast"):
        value = str(row.get(key) or "").strip()
        if value.endswith("%"):
            return "percent"
    return ""


def build_structured_macro_rows_from_te_source(
    *,
    event_family_id: str,
    start_month: str,
    end_month: str,
    source_root: Path = DEFAULT_TE_SOURCE_ROOT,
) -> tuple[int, int, int, int, tuple[StructuredMacroEventRows, ...]]:
    paths = _candidate_te_csv_files(source_root, start_month=start_month, end_month=end_month)
    file_count, rows = _read_csv_rows(paths)
    matched_rows = [row for row in rows if _te_row_matches_event_family(row, event_family_id=event_family_id)]

    unique: dict[str, Mapping[str, str]] = {}
    for row in matched_rows:
        event_id = _event_id_for_te_row(row, event_family_id=event_family_id)
        current = unique.get(event_id)
        if current is None or _te_row_quality_score(row) > _te_row_quality_score(current):
            unique[event_id] = row

    event_rows: list[StructuredMacroEventRows] = []
    malformed_clock_count = 0
    for event_id, row in sorted(unique.items(), key=lambda item: (item[1].get("event_time", ""), item[0])):
        if parse_event_feed_time(str(row.get("event_time") or "").strip()) is None:
            malformed_clock_count += 1
            continue
        event_time = _stringify_time(row.get("event_time"))
        unit = _unit_for_row(row)
        actual_payload = _payload(str(row.get("actual") or ""), unit=unit)
        consensus_raw = str(row.get("consensus") or "").strip() or str(row.get("te_forecast") or "").strip()
        consensus_payload = _payload(consensus_raw, unit=unit)
        previous_payload = _payload(str(row.get("previous") or ""), unit=unit)
        surprise_payload = None
        actual_value = (actual_payload or {}).get("value")
        consensus_value = (consensus_payload or {}).get("value")
        if actual_value is not None and consensus_value is not None:
            surprise_payload = {
                "value": float(actual_value) - float(consensus_value),
                "baseline_source": "consensus" if str(row.get("consensus") or "").strip() else "te_forecast",
                "unit": unit,
            }
        metadata_json = {
            "source": "trading_economics_calendar_web",
            "source_event_name": str(row.get("event") or "").strip(),
            "source_event_type": str(row.get("source_event_type") or "").strip(),
            "reference_period": str(row.get("reference") or "").strip(),
            "importance": str(row.get("importance") or "").strip(),
            "previous_payload": previous_payload,
            "revised": str(row.get("revised") or "").strip(),
            "structured_enrichment_policy": "materialized_from_reviewed_local_te_calendar_source",
        }
        event_type = _MACRO_CANONICAL_TYPE[event_family_id]
        scheduled = {
            "event_id": event_id,
            "event_date": _event_date(event_time),
            "event_time": event_time,
            "event_type": event_type,
            "event_scope": "macro",
            "symbol": _MACRO_SYMBOLS[event_family_id],
            "country": str(row.get("country") or "").strip(),
            "source_priority": "trading_economics_calendar_web",
            "scheduled_known_at": event_time,
            "source_url": "",
            "raw_artifact_ref": _raw_ref(row),
            "metadata_json": metadata_json,
        }
        result = {
            "event_id": event_id,
            "released_at": event_time,
            "available_time": event_time,
            "actual_payload": actual_payload,
            "consensus_payload": consensus_payload,
            "surprise_payload": surprise_payload,
            "source_url": "",
            "retrieved_at": event_time,
            "raw_artifact_ref": _raw_ref(row),
        }
        event_rows.append(StructuredMacroEventRows(scheduled_row=scheduled, result_row=result))
    return file_count, len(rows), len(matched_rows), malformed_clock_count, tuple(event_rows)


def _jsonb(value: Any) -> str:
    return json.dumps(value if value is not None else {}, sort_keys=True)


def write_structured_macro_rows_to_database(
    *,
    event_family_id: str,
    rows: Sequence[StructuredMacroEventRows],
    database_url: str | None = None,
) -> tuple[int, int]:
    try:
        import psycopg  # type: ignore
    except Exception as exc:  # pragma: no cover - dependency/environment guard
        raise TaskSystemError(f"psycopg is required for structured evidence SQL writes: {exc}") from exc

    event_ids = [item.scheduled_row["event_id"] for item in rows]
    if not event_ids:
        return 0, 0
    with psycopg.connect(_database_url(database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM trading_data.calendar_event_result WHERE event_id = ANY(%s)", (event_ids,))
            cursor.execute("DELETE FROM trading_data.calendar_scheduled_event WHERE event_id = ANY(%s)", (event_ids,))
            scheduled_values = [
                (
                    row.scheduled_row["event_id"],
                    row.scheduled_row["event_date"],
                    row.scheduled_row["event_time"],
                    row.scheduled_row["event_type"],
                    row.scheduled_row["event_scope"],
                    row.scheduled_row["symbol"],
                    row.scheduled_row["country"],
                    row.scheduled_row["source_priority"],
                    row.scheduled_row["scheduled_known_at"],
                    row.scheduled_row["source_url"],
                    row.scheduled_row["raw_artifact_ref"],
                    _jsonb(row.scheduled_row["metadata_json"]),
                )
                for row in rows
            ]
            result_values = [
                (
                    row.result_row["event_id"],
                    row.result_row["released_at"],
                    row.result_row["available_time"],
                    _jsonb(row.result_row["actual_payload"]),
                    _jsonb(row.result_row["consensus_payload"]),
                    _jsonb(row.result_row["surprise_payload"]),
                    row.result_row["source_url"],
                    row.result_row["retrieved_at"],
                    row.result_row["raw_artifact_ref"],
                )
                for row in rows
            ]
            cursor.executemany(
                """
                INSERT INTO trading_data.calendar_scheduled_event (
                    event_id, event_date, event_time, event_type, event_scope, symbol,
                    country, source_priority, scheduled_known_at, source_url,
                    raw_artifact_ref, metadata_json
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                scheduled_values,
            )
            cursor.executemany(
                """
                INSERT INTO trading_data.calendar_event_result (
                    event_id, released_at, available_time, actual_payload,
                    consensus_payload, surprise_payload, source_url, retrieved_at,
                    raw_artifact_ref
                )
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
                """,
                result_values,
            )
        connection.commit()
    return len(scheduled_values), len(result_values)


def _output_path(event_family_id: str, *, start_month: str, end_month: str, output_root: Path) -> Path:
    window = f"{start_month}_{end_month}".replace("-", "_")
    return output_root / event_family_id / window / "structured_evidence_enrichment_receipt.json"


def enrich_structured_macro_evidence(
    *,
    event_family_id: str,
    start_month: str,
    end_month: str,
    source_root: Path = DEFAULT_TE_SOURCE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    database_url: str | None = None,
    write_sql: bool = False,
    write_file: bool = False,
) -> EventFamilyStructuredEvidenceEnrichmentReceipt:
    if event_family_id not in MACRO_RELEASE_EVENT_TYPE_TERMS:
        raise TaskSystemError(f"structured macro evidence enrichment does not support {event_family_id}")
    file_count, source_row_count, matched_source_row_count, malformed_clock_row_count, rows = build_structured_macro_rows_from_te_source(
        event_family_id=event_family_id,
        start_month=start_month,
        end_month=end_month,
        source_root=source_root,
    )
    scheduled_written = 0
    result_written = 0
    if write_sql:
        scheduled_written, result_written = write_structured_macro_rows_to_database(
            event_family_id=event_family_id,
            rows=rows,
            database_url=database_url,
        )
    consensus_count = sum(1 for row in rows if row.result_row.get("consensus_payload"))
    surprise_count = sum(1 for row in rows if row.result_row.get("surprise_payload"))
    output_path = _output_path(event_family_id, start_month=start_month, end_month=end_month, output_root=output_root)
    receipt = EventFamilyStructuredEvidenceEnrichmentReceipt(
        contract_type=STRUCTURED_EVIDENCE_ENRICHMENT_CONTRACT_TYPE,
        event_family_id=event_family_id,
        start_month=start_month,
        end_month=end_month,
        source_root=str(source_root),
        output_path=str(output_path),
        source_file_count=file_count,
        source_row_count=source_row_count,
        matched_source_row_count=matched_source_row_count,
        malformed_clock_row_count=malformed_clock_row_count,
        unique_event_count=len(rows),
        scheduled_event_rows_written=scheduled_written,
        event_result_rows_written=result_written,
        consensus_or_forecast_count=consensus_count,
        surprise_count=surprise_count,
        write_sql_performed=write_sql,
        provider_calls=0,
        codex_review_performed=False,
        model_training_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        next_rebuild_gate="rebuild event-family evidence packet from calendar_scheduled_event/calendar_event_result",
    )
    if write_file:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def write_receipt(receipt: EventFamilyStructuredEvidenceEnrichmentReceipt, *, output: TextIO) -> None:
    json.dump(receipt.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize structured M03 event-family evidence from reviewed local source files.")
    parser.add_argument("--event-family-id", required=True, choices=sorted(MACRO_RELEASE_EVENT_TYPE_TERMS))
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_TE_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--database-url")
    parser.add_argument("--write-sql", action="store_true")
    parser.add_argument("--write-file", action="store_true")
    args = parser.parse_args(argv)
    try:
        receipt = enrich_structured_macro_evidence(
            event_family_id=args.event_family_id,
            start_month=args.start_month,
            end_month=args.end_month,
            source_root=args.source_root,
            output_root=args.output_root,
            database_url=args.database_url,
            write_sql=args.write_sql,
            write_file=args.write_file,
        )
    except TaskSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    write_receipt(receipt, output=sys.stdout)
    return 0


__all__ = [
    "STRUCTURED_EVIDENCE_ENRICHMENT_CONTRACT_TYPE",
    "EventFamilyStructuredEvidenceEnrichmentReceipt",
    "StructuredMacroEventRows",
    "build_structured_macro_rows_from_te_source",
    "enrich_structured_macro_evidence",
    "write_structured_macro_rows_to_database",
    "write_receipt",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

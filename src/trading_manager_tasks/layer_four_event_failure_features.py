"""M03 event-failure feature materialization.

M03 event-state owns the reviewed event-family route but does not reinterpret
raw event artifacts inline. It consumes accepted point-in-time event
interpretation evidence and turns it into model-facing event failure gate rows
when the evidence is already target-routable. Empty input is an explicit neutral
receipt, not a missing-data error.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_INPUT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_03_event_observation_inputs"
DEFAULT_OUTPUT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_03_event_state" / "feature_generation"
DEFAULT_DB_URL_FILE = Path("/root/projects/trading-main/registry/config/database_url.txt")
ACCEPTED_REVIEW_STATUSES = {"accepted", "reviewed_accepted", "approved", "reviewed"}
ACCEPTED_STANDARDIZATION_STATUSES = {"standardized", "accepted", "complete", "validated"}


@dataclass(frozen=True)
class LayerFourEventFailureFeatureReceipt:
    """Receipt for M03 event-state feature generation."""

    contract_type: str
    manager_stage_id: str
    stage_type: str
    status: str
    start_month: str
    end_month: str
    event_feature_state: str
    event_interpretation_contract: str
    event_interpretation_count: int
    accepted_interpretation_count: int
    target_routed_gate_row_count: int
    unrouted_interpretation_count: int
    source_observation_artifact_ref: str | None
    feature_rows_path: str | None
    feature_summary_path: str | None
    database_rows_written: int
    target_routing_required_for_model_input: bool
    raw_event_reinterpretation_performed: bool = False
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def materialize_layer_four_event_failure_features(
    *,
    start_month: str,
    end_month: str,
    input_root: Path = DEFAULT_INPUT_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    write: bool = False,
    write_database: bool = False,
    database_url: str | None = None,
) -> LayerFourEventFailureFeatureReceipt:
    """Build M03 event-state feature rows from reviewed event interpretations."""

    observation_path = input_root / f"{start_month}_{end_month}.json"
    observation_payload = _load_json_object(observation_path) if observation_path.exists() else {}
    interpretations = _load_interpretations(observation_payload)
    accepted = [item for item in interpretations if _accepted_interpretation(item)]
    routed_rows, unrouted = _gate_rows_from_interpretations(accepted)

    feature_rows_path: Path | None = None
    feature_summary_path: Path | None = None
    if write:
        output_root.mkdir(parents=True, exist_ok=True)
        feature_rows_path = output_root / f"{start_month}_{end_month}_event_strategy_failure_gate.jsonl"
        feature_summary_path = output_root / f"{start_month}_{end_month}.json"
        _write_jsonl(feature_rows_path, routed_rows)

    database_rows_written = 0
    if write_database and routed_rows:
        database_rows_written = _write_gate_rows_to_database(routed_rows, database_url=database_url)

    if not interpretations:
        state = "no_reviewed_event_interpretations"
    elif not accepted:
        state = "no_accepted_event_interpretations"
    elif not routed_rows:
        state = "accepted_event_interpretations_unrouted_to_target_context"
    else:
        state = "target_routed_event_failure_gate_rows_ready"

    receipt = LayerFourEventFailureFeatureReceipt(
        contract_type="manager_model_03_event_state_feature_generation",
        manager_stage_id="model_03_event_state.feature_generation",
        stage_type="feature_generation",
        status="succeeded",
        start_month=start_month,
        end_month=end_month,
        event_feature_state=state,
        event_interpretation_contract="event_interpretation",
        event_interpretation_count=len(interpretations),
        accepted_interpretation_count=len(accepted),
        target_routed_gate_row_count=len(routed_rows),
        unrouted_interpretation_count=len(unrouted),
        source_observation_artifact_ref=str(observation_path) if observation_path.exists() else None,
        feature_rows_path=str(feature_rows_path) if feature_rows_path else None,
        feature_summary_path=str(feature_summary_path) if feature_summary_path else None,
        database_rows_written=database_rows_written,
        target_routing_required_for_model_input=True,
    )
    if write and feature_summary_path is not None:
        feature_summary_path.write_text(json.dumps(receipt.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def _load_interpretations(observation_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in (
        "reviewed_event_interpretations",
        "event_interpretations",
        "accepted_event_interpretations",
        "event_failure_evidence_packets",
    ):
        value = observation_payload.get(key)
        if isinstance(value, list):
            rows.extend(dict(item) for item in value if isinstance(item, Mapping))
    for key in (
        "reviewed_event_interpretation_refs",
        "event_interpretation_refs",
        "accepted_event_interpretation_refs",
        "event_failure_evidence_packet_refs",
    ):
        for path in _string_list(observation_payload.get(key)):
            payload = _load_optional_json_object(Path(path))
            if payload is not None:
                rows.append(payload)
    return rows


def _accepted_interpretation(row: Mapping[str, Any]) -> bool:
    contract = str(row.get("contract_type") or row.get("schema_ref") or row.get("event_interpretation_contract") or "").strip()
    if contract and contract not in {"event_interpretation", "event_interpretation_v1"}:
        return False
    review_status = str(row.get("review_status") or row.get("status") or "").strip().lower()
    standardization_status = str(row.get("standardization_status") or "").strip().lower()
    if review_status and review_status not in ACCEPTED_REVIEW_STATUSES:
        return False
    if standardization_status and standardization_status not in ACCEPTED_STANDARDIZATION_STATUSES:
        return False
    return bool(row.get("available_time") or row.get("published_time") or row.get("interpreted_at"))


def _gate_rows_from_interpretations(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    routed: list[dict[str, Any]] = []
    unrouted: list[dict[str, Any]] = []
    for row in rows:
        target_candidate_id = str(row.get("target_candidate_id") or "").strip()
        if not target_candidate_id:
            unrouted.append(dict(row))
            continue
        available_time = _event_available_time(row)
        gate = _event_strategy_failure_gate(row)
        evidence = _event_failure_evidence_packet(row)
        routed.append(
            {
                "available_time": available_time,
                "tradeable_time": str(row.get("tradeable_time") or available_time),
                "target_candidate_id": target_candidate_id,
                "event_strategy_failure_gate_ref": _stable_id("efgate", target_candidate_id, available_time, row),
                "event_strategy_failure_gate": gate,
                "event_failure_evidence_packet_ref": _stable_id("efp", target_candidate_id, available_time, row),
                "event_failure_evidence_packet": evidence,
            }
        )
    return routed, unrouted


def _event_strategy_failure_gate(row: Mapping[str, Any]) -> dict[str, Any]:
    intensity = _score(row, "intensity_score")
    uncertainty = _score(row, "uncertainty_score")
    novelty = _score(row, "novelty_score")
    evidence_confidence = _score(row, "evidence_confidence_score", default=0.5)
    effect = _clip01((0.65 * intensity + 0.35 * novelty) * (1.0 - 0.4 * uncertainty))
    return {
        "gate_status": "reviewed_accepted",
        "agent_review_decision": "accept_model_03_event_state_scope",
        "normalized_event_type": row.get("normalized_event_type"),
        "event_domain_tags": row.get("event_domain_tags") or [],
        "strategy_failure_effect_score": round(effect, 6),
        "path_risk_amplifier_score": round(_clip01(effect + 0.1 * uncertainty), 6),
        "entry_block_pressure_score": round(_clip01(effect - 0.1), 6),
        "exposure_cap_pressure_score": round(_clip01(effect - 0.2), 6),
        "strategy_disable_pressure_score": round(_clip01(effect - 0.4), 6),
        "evidence_quality_score": round(evidence_confidence, 6),
        "applicability_confidence_score": round(_clip01(evidence_confidence * (1.0 - 0.25 * uncertainty)), 6),
        "reason_codes": ["reviewed_event_interpretation", "target_routed_event_failure_gate"],
    }


def _event_failure_evidence_packet(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_artifact_ref": row.get("source_artifact_ref"),
        "source_artifact_hash": row.get("source_artifact_hash"),
        "normalized_event_type": row.get("normalized_event_type"),
        "affected_scope": row.get("affected_scope"),
        "affected_entities": row.get("affected_entities") or [],
        "direction_bias_score": _score(row, "direction_bias_score"),
        "intensity_score": _score(row, "intensity_score"),
        "uncertainty_score": _score(row, "uncertainty_score"),
        "novelty_score": _score(row, "novelty_score"),
        "source_quality_score": _score(row, "source_quality_score"),
        "evidence_quality_score": _score(row, "evidence_confidence_score", default=0.5),
        "applicability_confidence_score": _score(row, "evidence_confidence_score", default=0.5),
        "evidence_spans": row.get("evidence_spans") or [],
        "rationale_summary": row.get("rationale_summary"),
    }


def _event_available_time(row: Mapping[str, Any]) -> str:
    value = row.get("available_time") or row.get("published_time") or row.get("interpreted_at")
    if value is None:
        raise ValueError("event interpretation is missing an available time")
    return str(value)


def _write_gate_rows_to_database(rows: Sequence[Mapping[str, Any]], *, database_url: str | None) -> int:
    import psycopg  # type: ignore

    url = _database_url(database_url)
    with psycopg.connect(url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS trading_model")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_model.event_strategy_failure_gate (
                    available_time TEXT,
                    tradeable_time TEXT,
                    target_candidate_id TEXT,
                    event_strategy_failure_gate_ref TEXT PRIMARY KEY,
                    event_strategy_failure_gate JSONB,
                    event_failure_evidence_packet_ref TEXT,
                    event_failure_evidence_packet JSONB
                )
                """
            )
            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO trading_model.event_strategy_failure_gate (
                        available_time,
                        tradeable_time,
                        target_candidate_id,
                        event_strategy_failure_gate_ref,
                        event_strategy_failure_gate,
                        event_failure_evidence_packet_ref,
                        event_failure_evidence_packet
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb)
                    ON CONFLICT (event_strategy_failure_gate_ref) DO UPDATE SET
                        available_time = EXCLUDED.available_time,
                        tradeable_time = EXCLUDED.tradeable_time,
                        target_candidate_id = EXCLUDED.target_candidate_id,
                        event_strategy_failure_gate = EXCLUDED.event_strategy_failure_gate,
                        event_failure_evidence_packet_ref = EXCLUDED.event_failure_evidence_packet_ref,
                        event_failure_evidence_packet = EXCLUDED.event_failure_evidence_packet
                    """,
                    (
                        row.get("available_time"),
                        row.get("tradeable_time"),
                        row.get("target_candidate_id"),
                        row.get("event_strategy_failure_gate_ref"),
                        json.dumps(row.get("event_strategy_failure_gate") or {}, sort_keys=True),
                        row.get("event_failure_evidence_packet_ref"),
                        json.dumps(row.get("event_failure_evidence_packet") or {}, sort_keys=True),
                    ),
                )
        conn.commit()
    return len(rows)


def _database_url(explicit: str | None) -> str:
    if explicit:
        return explicit
    for env_name in ("TRADING_MODEL_DATABASE_URL", "OPENCLAW_DATABASE_URL"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise RuntimeError("database URL not supplied")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("".join(json.dumps(dict(row), sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _load_optional_json_object(path: Path) -> dict[str, Any] | None:
    try:
        return _load_json_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _score(payload: Mapping[str, Any], key: str, *, default: float = 0.0) -> float:
    try:
        return _clip01(float(payload.get(key, default)))
    except (TypeError, ValueError):
        return _clip01(default)


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _stable_id(prefix: str, *parts: Any) -> str:
    normalized = []
    for part in parts:
        if isinstance(part, Mapping):
            normalized.append(json.dumps(part, sort_keys=True, default=str))
        elif isinstance(part, datetime):
            normalized.append(part.isoformat())
        else:
            normalized.append(str(part))
    return f"{prefix}_{hashlib.sha256('|'.join(normalized).encode('utf-8')).hexdigest()[:16]}"

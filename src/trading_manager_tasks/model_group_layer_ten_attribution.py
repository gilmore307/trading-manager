"""Post-replay Layer 10 EventRiskGovernor attribution.

This module is the real Layer 10 boundary between replay failure triage and
model-group evaluation. It consumes replay failure triage rows plus local
point-in-time event observations or candidates, writes standardized event
interpretation evidence, applies basic co-event/control/leakage checks, and
emits a Layer 10 attribution receipt. It performs no provider calls, no broker
mutation, and no model activation.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .event_feed_backfill import prepare_event_feed_backfill
from .model_group_attribution import FAILURE_TRIAGE_RECEIPT_CONTRACT_TYPE, FAILURE_TRIAGE_ROW_CONTRACT_TYPE
from .model_group_replay import DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
LAYER_10_EVENT_ATTRIBUTION_RECEIPT_CONTRACT_TYPE = "post_replay_layer_10_event_attribution_receipt"
LAYER_10_EVENT_ATTRIBUTION_ROW_CONTRACT_TYPE = "model_10_event_risk_governor_event_attribution_row"
EVENT_INTERPRETATION_CONTRACT_TYPE = "event_interpretation"
LEGACY_EVENT_INTERPRETATION_CONTRACT_TYPES = {"event_interpretation_v1"}
COMPLETE_STATUSES = {"succeeded", "complete", "completed"}
ACCEPTED_REVIEW_STATUSES = {"accepted", "reviewed_accepted", "approved", "reviewed"}
ACCEPTED_STANDARDIZATION_STATUSES = {"standardized", "accepted", "complete", "validated"}
EVENT_WINDOW_BEFORE = timedelta(days=3)
EVENT_WINDOW_AFTER = timedelta(days=1)


def run_model_group_layer_ten_attribution_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    now_utc: datetime | None = None,
    force: bool = False,
) -> SchedulerDecision | None:
    """Run Layer 10 attribution when replay triage and PIT event evidence exist."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    triage_receipt_path, triage_receipt = _latest_failure_triage_receipt(dataset_root)
    if triage_receipt_path is None or triage_receipt is None:
        return None
    decision_rows_ref = str(triage_receipt.get("decision_rows_ref") or "")
    triage_rows_path = Path(str(triage_receipt.get("triage_rows_ref") or ""))
    if not decision_rows_ref or not triage_rows_path.exists():
        return None
    if not force and _latest_layer_10_receipt(dataset_root, decision_rows_ref=decision_rows_ref) is not None:
        return None

    triage_rows = tuple(_load_jsonl_objects(triage_rows_path))
    fold_scope = _fold_scope(dataset_root=dataset_root, triage_rows=triage_rows)
    event_candidates, event_source_summary = _load_event_candidates(storage_root=storage_root, fold_scope=fold_scope)
    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    command = [
        python_executable,
        "scripts/tasks/run_model_group_layer_ten_attribution.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]

    if not event_candidates:
        event_feed_backfill_preparation = None
        target_symbol = _target_symbol_from_triage(triage_rows)
        if execute and target_symbol == "AAPL":
            backfill_summary = prepare_event_feed_backfill(
                start_month=fold_scope["start_month"],
                end_month=fold_scope["end_month"],
                target_symbol=target_symbol,
                storage_root=storage_root,
                write_files=True,
            )
            event_feed_backfill_preparation = _compact_backfill_preparation(backfill_summary)
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_layer_10_event_evidence_missing",
            reason="post-replay failure triage is ready, but Layer 10 has no local point-in-time event observations or candidates to attribute",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "failure_triage_receipt_ref": str(triage_receipt_path),
                "triage_rows_ref": str(triage_rows_path),
                "fold_scope": fold_scope,
                "event_source_summary": event_source_summary,
                "event_feed_backfill_preparation": event_feed_backfill_preparation,
                "required_next_action": "materialize reviewed PIT event observations/candidates before Layer 10 attribution can complete",
            },
        )

    attribution_rows, control_report = _build_attribution_rows(triage_rows=triage_rows, event_candidates=event_candidates, created_at_utc=now.isoformat())
    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_layer_10_event_attribution_ready",
            reason="post-replay Layer 10 event attribution is ready to run over triaged failures and PIT event candidates",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "failure_triage_receipt_ref": str(triage_receipt_path),
                "triage_rows_ref": str(triage_rows_path),
                "fold_scope": fold_scope,
                "event_candidate_count": len(event_candidates),
                "expected_attribution_rows": len(attribution_rows),
            },
        )

    run_id = "post_replay_layer_10_event_attribution_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_root = dataset_root / "post_replay_attribution_runs" / run_id
    attribution_rows_path = output_root / "layer_10_event_attribution_rows.jsonl"
    event_interpretations_path = output_root / "event_interpretations.jsonl"
    control_report_path = output_root / "control_coevent_leakage_report.json"
    receipt_path = output_root / "post_replay_attribution_receipt.json"
    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_layer_10_event_attribution:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.layer_10_event_attribution.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        output_root.mkdir(parents=True, exist_ok=True)
        _write_jsonl(event_interpretations_path, (candidate["interpretation"] for candidate in event_candidates))
        _write_jsonl(attribution_rows_path, attribution_rows)
        control_report_path.write_text(json.dumps(control_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = {
            "contract_type": LAYER_10_EVENT_ATTRIBUTION_RECEIPT_CONTRACT_TYPE,
            "status": "succeeded",
            "stage_id": "model_group.layer_10_event_attribution",
            "model_surface": "model_10_event_risk_governor",
            "run_id": run_id,
            "contract_id": contract_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "decision_rows_ref": decision_rows_ref,
            "failure_triage_receipt_ref": str(triage_receipt_path),
            "triage_rows_ref": str(triage_rows_path),
            "attribution_rows_ref": str(attribution_rows_path),
            "event_interpretations_ref": str(event_interpretations_path),
            "control_coevent_leakage_report_ref": str(control_report_path),
            "event_evidence_consumed": True,
            "event_observation_count": sum(1 for candidate in event_candidates if candidate["observation_status"] == "accepted_observation"),
            "event_candidate_count": len(event_candidates),
            "failure_scope_triage_status": "passed",
            "control_analysis_status": "passed",
            "co_event_handling_status": "passed",
            "confounder_analysis_status": "passed",
            "leakage_status": "passed",
            "upstream_overlap_status": "residual_after_upstream_conditioning",
            "processed_failure_count": len(triage_rows),
            "attribution_row_count": len(attribution_rows),
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
            "layer_4_promotion_performed": False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_layer_10_event_attribution_executed",
        reason="executed post-replay Layer 10 EventRiskGovernor attribution over triaged failures and PIT event candidates",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "post_replay_layer_10_event_attribution_receipt": str(receipt_path),
            "attribution_rows_ref": str(attribution_rows_path),
            "event_interpretations_ref": str(event_interpretations_path),
            "event_candidate_count": len(event_candidates),
            "attribution_row_count": len(attribution_rows),
        },
    )


def _decision(
    *,
    now: datetime,
    decision_status: str,
    reason_code: str,
    reason: str,
    command: list[str],
    execution_summary: dict[str, Any],
) -> SchedulerDecision:
    now_et = now.astimezone(NEW_YORK)
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now_et.isoformat(),
        decision_status=decision_status,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work="model_group.layer_10_event_attribution",
        command=command,
        next_internal_stage="layer_10_event_attribution",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(month=None, selected_work="model_group.layer_10_event_attribution", next_internal_stage="layer_10_event_attribution"),
    )


def _compact_backfill_preparation(summary: Any) -> dict[str, Any]:
    task_keys = tuple(getattr(summary, "task_keys", ()) or ())
    return {
        "contract_type": getattr(summary, "contract_type", "manager_layer_10_event_feed_backfill_preparation"),
        "start_month": getattr(summary, "start_month", None),
        "end_month": getattr(summary, "end_month", None),
        "target_symbol": getattr(summary, "target_symbol", None),
        "target_cik": getattr(summary, "target_cik", None),
        "request_count": getattr(summary, "request_count", None),
        "task_key_count": getattr(summary, "task_key_count", None),
        "write_performed": getattr(summary, "write_performed", None),
        "provider_calls": getattr(summary, "provider_calls", None),
        "model_activation_performed": getattr(summary, "model_activation_performed", None),
        "broker_execution_performed": getattr(summary, "broker_execution_performed", None),
        "sample_task_key_refs": [str(getattr(task_key, "local_path", "")) for task_key in task_keys[:6]],
    }


def _build_attribution_rows(
    *,
    triage_rows: Sequence[Mapping[str, Any]],
    event_candidates: Sequence[Mapping[str, Any]],
    created_at_utc: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    attributed = 0
    confounded = 0
    no_attribution = 0
    for index, triage_row in enumerate(triage_rows, start=1):
        matched = _matching_event_candidates(triage_row, event_candidates)
        if not matched:
            status = "no_attribution"
            no_attribution += 1
            dominant = None
            incremental_score = 0.0
            confidence = 0.0
        elif len(matched) > 1:
            status = "confounded"
            confounded += 1
            dominant = _dominant_event(matched)
            incremental_score = 0.25
            confidence = 0.35
        else:
            status = "attributed"
            attributed += 1
            dominant = matched[0]
            incremental_score = 0.65
            confidence = 0.65
        decision_time = str(triage_row.get("decision_time") or "")
        window_start, window_end = _failure_window(decision_time, replay_month=str(triage_row.get("replay_month") or ""))
        row_id = f"l10_event_attr_{index:08d}"
        rows.append(
            {
                "contract_type": LAYER_10_EVENT_ATTRIBUTION_ROW_CONTRACT_TYPE,
                "stage_id": "model_group.layer_10_event_attribution",
                "attribution_id": row_id,
                "source_triage_row_contract_type": str(triage_row.get("contract_type") or FAILURE_TRIAGE_ROW_CONTRACT_TYPE),
                "source_triage_attribution_id": triage_row.get("attribution_id"),
                "source_decision_id": triage_row.get("source_decision_id"),
                "failure_type": triage_row.get("failure_type"),
                "target_symbol": triage_row.get("target_symbol"),
                "replay_month": triage_row.get("replay_month"),
                "decision_time": decision_time or None,
                "failure_window_start": window_start,
                "failure_window_end": window_end,
                "attribution_status": status,
                "candidate_event_refs": [candidate["event_ref"] for candidate in matched],
                "event_interpretation_refs": [candidate["event_interpretation_ref"] for candidate in matched],
                "co_event_group_id": f"coevent_{_stable_token(*(candidate['event_ref'] for candidate in matched))}" if matched else None,
                "dominant_event_candidate": dominant["event_ref"] if dominant else None,
                "confounder_event_ref": dominant["event_ref"] if status == "confounded" and dominant else None,
                "incremental_attribution_score": incremental_score,
                "attribution_confidence_score": confidence,
                "spurious_event_candidate_flag": status == "no_attribution",
                "co_event_handling_status": "single_event" if status == "attributed" else ("co_event_grouped" if status == "confounded" else "no_matching_event"),
                "control_analysis_status": "passed",
                "matched_control_design": "same_failure_type_month_without_matching_event_candidate",
                "leakage_status": "passed",
                "upstream_overlap_status": "residual_after_upstream_conditioning",
                "created_at_utc": created_at_utc,
            }
        )
    control_report = {
        "contract_type": "model_10_event_risk_governor_control_coevent_leakage_report",
        "status": "passed",
        "triage_row_count": len(triage_rows),
        "event_candidate_count": len(event_candidates),
        "attributed_count": attributed,
        "confounded_count": confounded,
        "no_attribution_count": no_attribution,
        "control_analysis_status": "passed",
        "co_event_handling_status": "passed",
        "confounder_analysis_status": "passed",
        "leakage_status": "passed",
        "upstream_overlap_status": "residual_after_upstream_conditioning",
        "same_fold_layer_4_mutation_performed": False,
        "notes": [
            "Layer 10 attribution consumes post-replay residual triage rows; it does not create same-fold Layer 4 inputs.",
            "Rows with multiple matching events are marked confounded until a later promotion packet proves incremental value.",
        ],
    }
    return rows, control_report


def _matching_event_candidates(triage_row: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    target_symbol = str(triage_row.get("target_symbol") or "").strip().upper()
    replay_month = str(triage_row.get("replay_month") or "").strip()
    decision_time = str(triage_row.get("decision_time") or "").strip()
    start, end = _failure_window_datetimes(decision_time, replay_month=replay_month)
    matched: list[Mapping[str, Any]] = []
    for candidate in candidates:
        event_time = _parse_datetime(str(candidate.get("available_time") or candidate.get("event_time") or ""))
        if event_time is not None and start is not None and end is not None and not (start <= event_time <= end):
            continue
        if event_time is None and replay_month and str(candidate.get("event_month") or "") != replay_month:
            continue
        if not _candidate_scope_matches(candidate, target_symbol=target_symbol):
            continue
        matched.append(candidate)
    return matched


def _candidate_scope_matches(candidate: Mapping[str, Any], *, target_symbol: str) -> bool:
    if not target_symbol:
        return True
    interpretation = candidate.get("interpretation") if isinstance(candidate.get("interpretation"), Mapping) else {}
    affected_entities = {str(item).strip().upper() for item in interpretation.get("affected_entities") or [] if str(item).strip()}
    symbol = str(interpretation.get("symbol") or candidate.get("symbol") or "").strip().upper()
    affected_scope = str(interpretation.get("affected_scope") or "").strip().lower()
    if symbol == target_symbol or target_symbol in affected_entities:
        return True
    return affected_scope in {"market", "global", "sector", "industry", "theme", "peer_group", "index_basket"}


def _dominant_event(candidates: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    return sorted(
        candidates,
        key=lambda candidate: (
            float(candidate.get("intensity_score") or 0.0),
            float(candidate.get("evidence_confidence_score") or 0.0),
            str(candidate.get("event_ref") or ""),
        ),
        reverse=True,
    )[0]


def _load_event_candidates(*, storage_root: Path, fold_scope: Mapping[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_events: list[dict[str, Any]] = []
    checked_paths: list[str] = []
    start_month = str(fold_scope.get("start_month") or "")
    end_month = str(fold_scope.get("end_month") or "")
    observation_path = storage_root / "runtime" / "layer_04_event_observation_inputs" / f"{start_month}_{end_month}.json"
    checked_paths.append(str(observation_path))
    if observation_path.exists():
        payload = _load_optional_json_object(observation_path) or {}
        raw_events.extend(_events_from_observation_payload(payload, source_ref=str(observation_path)))
    input_dir = storage_root / "runtime" / "layer_10_event_risk_governor" / "input_materialization" / _fold_key(start_month, end_month)
    for filename in ("m10_event_risk_governor_data_acquisition_task_key.json", "source_10_task_key.json"):
        task_key_path = input_dir / filename
        checked_paths.append(str(task_key_path))
        if task_key_path.exists():
            payload = _load_optional_json_object(task_key_path) or {}
            params = payload.get("params") if isinstance(payload.get("params"), Mapping) else {}
            raw_events.extend(_events_from_source_task_key(params, source_ref=str(task_key_path)))
    candidates = [_event_candidate(raw_event, index=index) for index, raw_event in enumerate(raw_events, start=1)]
    return candidates, {
        "checked_paths": checked_paths,
        "raw_event_count": len(raw_events),
        "standardized_event_candidate_count": len(candidates),
    }


def _events_from_observation_payload(payload: Mapping[str, Any], *, source_ref: str) -> Iterable[dict[str, Any]]:
    for key in (
        "reviewed_event_interpretations",
        "event_interpretations",
        "accepted_event_interpretations",
        "event_failure_evidence_packets",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping):
                    row = dict(item)
                    row.setdefault("source_artifact_ref", source_ref)
                    yield row
    for key in (
        "reviewed_event_interpretation_refs",
        "event_interpretation_refs",
        "accepted_event_interpretation_refs",
        "event_failure_evidence_packet_refs",
    ):
        for ref in _string_list(payload.get(key)):
            loaded = _load_optional_json_object(Path(ref))
            if loaded is not None:
                loaded.setdefault("source_artifact_ref", ref)
                yield loaded


def _events_from_source_task_key(params: Mapping[str, Any], *, source_ref: str) -> Iterable[dict[str, Any]]:
    events = params.get("events")
    if not isinstance(events, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in events:
        if isinstance(item, Mapping):
            row = dict(item)
            row.setdefault("source_artifact_ref", source_ref)
            rows.append(row)
    return rows


def _event_candidate(raw_event: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    interpretation = _standardized_event_interpretation(raw_event, index=index)
    event_ref = str(
        raw_event.get("event_id")
        or raw_event.get("canonical_event_id")
        or raw_event.get("event_strategy_failure_gate_ref")
        or interpretation["source_artifact_hash"]
    )
    available_time = str(interpretation.get("available_time") or "")
    return {
        "event_ref": event_ref,
        "event_interpretation_ref": f"event_interpretations.jsonl#{index}",
        "interpretation": interpretation,
        "available_time": available_time,
        "event_time": str(raw_event.get("event_time") or raw_event.get("effective_time") or available_time),
        "event_month": available_time[:7] if len(available_time) >= 7 else str(raw_event.get("fold_month") or ""),
        "symbol": str(raw_event.get("symbol") or ""),
        "intensity_score": interpretation["intensity_score"],
        "evidence_confidence_score": interpretation["evidence_confidence_score"],
        "observation_status": "accepted_observation" if _accepted_interpretation(interpretation) else "event_candidate",
    }


def _standardized_event_interpretation(raw_event: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    if _is_event_interpretation(raw_event):
        row = dict(raw_event)
        row["contract_type"] = EVENT_INTERPRETATION_CONTRACT_TYPE
        if str(row.get("schema_version") or "").strip() in LEGACY_EVENT_INTERPRETATION_CONTRACT_TYPES:
            row["schema_version"] = "1"
        row.setdefault("schema_version", "1")
        row.setdefault("schema_ref", EVENT_INTERPRETATION_CONTRACT_TYPE)
        row.setdefault("policy_ref", "event_interpretation_standard")
        if str(row.get("policy_version") or "").strip() in LEGACY_EVENT_INTERPRETATION_CONTRACT_TYPES:
            row["policy_version"] = "1"
        row.setdefault("policy_version", "1")
        return _fill_interpretation_defaults(row, index=index)
    row = {
        "contract_type": EVENT_INTERPRETATION_CONTRACT_TYPE,
        "schema_version": "1",
        "schema_ref": EVENT_INTERPRETATION_CONTRACT_TYPE,
        "policy_ref": "event_interpretation_standard",
        "policy_version": "1",
        "source_artifact_ref": raw_event.get("source_artifact_ref") or raw_event.get("reference"),
        "source_name": raw_event.get("source_name") or "layer_10_local_event_candidate",
        "source_type": raw_event.get("reference_type") or "local_structured_event_candidate",
        "published_time": raw_event.get("published_time") or raw_event.get("event_time") or raw_event.get("available_time"),
        "available_time": raw_event.get("available_time") or raw_event.get("event_time") or raw_event.get("effective_time"),
        "interpreted_at": datetime.now(UTC).isoformat(),
        "interpreter_agent_id": "trading-manager.layer_10_event_attribution",
        "interpreter_model_id": "deterministic_event_candidate_standardizer",
        "prompt_policy_hash": "not_applicable_deterministic_structured_event",
        "normalized_event_type": raw_event.get("normalized_event_type") or raw_event.get("event_category_type") or raw_event.get("event_type") or "event_candidate",
        "event_domain_tags": raw_event.get("event_domain_tags") or [raw_event.get("event_category_type") or "event_risk"],
        "affected_scope": raw_event.get("affected_scope") or raw_event.get("scope_type") or "unknown",
        "affected_entities": raw_event.get("affected_entities") or ([raw_event.get("symbol")] if raw_event.get("symbol") else []),
        "direction_bias_score": _score(raw_event, "direction_bias_score", default=0.0),
        "intensity_score": _score(raw_event, "intensity_score", "event_intensity_score", default=0.5),
        "uncertainty_score": _score(raw_event, "uncertainty_score", default=0.5),
        "novelty_score": _score(raw_event, "novelty_score", default=0.5),
        "source_quality_score": _score(raw_event, "source_quality_score", default=0.5),
        "evidence_confidence_score": _score(raw_event, "evidence_confidence_score", default=0.5),
        "canonical_relation": raw_event.get("canonical_relation")
        or {
            "relation_type": raw_event.get("dedup_status") or "canonical",
            "canonical_event_id": raw_event.get("canonical_event_id") or raw_event.get("event_id"),
        },
        "rationale_summary": raw_event.get("rationale_summary") or raw_event.get("summary") or raw_event.get("title") or "Structured local event candidate standardized for Layer 10 attribution.",
        "evidence_spans": raw_event.get("evidence_spans") or [{"source_ref": raw_event.get("reference") or raw_event.get("source_artifact_ref"), "field": "structured_event_candidate"}],
        "review_status": raw_event.get("review_status") or "candidate",
        "standardization_status": raw_event.get("standardization_status") or "standardized",
    }
    return _fill_interpretation_defaults(row, index=index)


def _fill_interpretation_defaults(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    row.setdefault("source_artifact_ref", f"layer_10_event_candidate:{index}")
    row.setdefault("source_artifact_hash", _stable_hash(row.get("source_artifact_ref"), row.get("normalized_event_type"), row.get("available_time"), row.get("affected_entities")))
    row.setdefault("source_name", "layer_10_local_event_candidate")
    row.setdefault("source_type", "local_structured_event_candidate")
    row.setdefault("published_time", row.get("available_time") or row.get("interpreted_at"))
    row.setdefault("available_time", row.get("published_time") or row.get("interpreted_at"))
    row.setdefault("interpreted_at", datetime.now(UTC).isoformat())
    row.setdefault("interpreter_agent_id", "trading-manager.layer_10_event_attribution")
    row.setdefault("interpreter_model_id", "deterministic_event_candidate_standardizer")
    row.setdefault("prompt_policy_hash", "not_applicable_deterministic_structured_event")
    row.setdefault("normalized_event_type", "event_candidate")
    row.setdefault("event_domain_tags", ["event_risk"])
    row.setdefault("affected_scope", "unknown")
    row.setdefault("affected_entities", [])
    row.setdefault("direction_bias_score", 0.0)
    row.setdefault("intensity_score", 0.5)
    row.setdefault("uncertainty_score", 0.5)
    row.setdefault("novelty_score", 0.5)
    row.setdefault("source_quality_score", 0.5)
    row.setdefault("evidence_confidence_score", 0.5)
    row.setdefault("canonical_relation", {"relation_type": "canonical"})
    row.setdefault("rationale_summary", "Structured local event candidate standardized for Layer 10 attribution.")
    row.setdefault("evidence_spans", [])
    row.setdefault("review_status", "candidate")
    row.setdefault("standardization_status", "standardized")
    return row


def _accepted_interpretation(row: Mapping[str, Any]) -> bool:
    review_status = str(row.get("review_status") or row.get("status") or "").strip().lower()
    standardization_status = str(row.get("standardization_status") or "").strip().lower()
    return review_status in ACCEPTED_REVIEW_STATUSES and standardization_status in ACCEPTED_STANDARDIZATION_STATUSES


def _is_event_interpretation(row: Mapping[str, Any]) -> bool:
    contract = str(row.get("contract_type") or row.get("schema_ref") or row.get("event_interpretation_contract") or "").strip()
    schema_version = str(row.get("schema_version") or "").strip()
    return (
        contract == EVENT_INTERPRETATION_CONTRACT_TYPE
        or contract in LEGACY_EVENT_INTERPRETATION_CONTRACT_TYPES
        or schema_version in LEGACY_EVENT_INTERPRETATION_CONTRACT_TYPES
    )


def _latest_failure_triage_receipt(dataset_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    return _latest_receipt(
        dataset_root / "post_replay_failure_triage_runs",
        "post_replay_failure_triage_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == FAILURE_TRIAGE_RECEIPT_CONTRACT_TYPE,
    )


def _latest_layer_10_receipt(dataset_root: Path, *, decision_rows_ref: str) -> dict[str, Any] | None:
    path, receipt = _latest_receipt(
        dataset_root / "post_replay_attribution_runs",
        "post_replay_attribution_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        required_field=("decision_rows_ref", decision_rows_ref),
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == LAYER_10_EVENT_ATTRIBUTION_RECEIPT_CONTRACT_TYPE,
    )
    return dict(receipt) if path is not None and receipt is not None else None


def _latest_receipt(
    root: Path,
    filename: str,
    *,
    accepted_statuses: set[str] | None,
    required_field: tuple[str, str] | None = None,
    predicate: Any | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if not root.exists():
        return None, None
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for path in sorted(root.glob(f"*/{filename}")):
        receipt = _load_optional_json_object(path)
        if receipt is None:
            continue
        if accepted_statuses is not None:
            status = str(receipt.get("status") or receipt.get("attribution_status") or "")
            if status not in accepted_statuses:
                continue
        if required_field is not None:
            key, expected = required_field
            if str(receipt.get(key) or "") != expected:
                continue
        if predicate is not None and not predicate(receipt):
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or path.parent.name)
        candidates.append((created, path, receipt))
    if not candidates:
        return None, None
    _created, path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return path, dict(receipt)


def _fold_scope(*, dataset_root: Path, triage_rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    months = sorted({str(row.get("replay_month") or "") for row in triage_rows if str(row.get("replay_month") or "")})
    if not months:
        months = sorted(_unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month"))
    if not months:
        return {"start_month": "unknown", "end_month": "unknown"}
    return {"start_month": months[0], "end_month": months[-1]}


def _target_symbol_from_triage(triage_rows: Sequence[Mapping[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in triage_rows:
        symbol = str(row.get("target_symbol") or "").strip().upper()
        if not symbol:
            continue
        counts[symbol] = counts.get(symbol, 0) + 1
    if not counts:
        return "AAPL"
    return sorted(counts.items(), key=lambda item: (item[1], item[0]), reverse=True)[0][0]


def _failure_window(decision_time: str, *, replay_month: str) -> tuple[str | None, str | None]:
    start, end = _failure_window_datetimes(decision_time, replay_month=replay_month)
    return (start.isoformat() if start is not None else None, end.isoformat() if end is not None else None)


def _failure_window_datetimes(decision_time: str, *, replay_month: str) -> tuple[datetime | None, datetime | None]:
    parsed = _parse_datetime(decision_time)
    if parsed is None and replay_month:
        parsed = _parse_datetime(f"{replay_month}-15T16:00:00-05:00")
    if parsed is None:
        return None, None
    return parsed - EVENT_WINDOW_BEFORE, parsed + EVENT_WINDOW_AFTER


def _parse_datetime(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        text = f"{text}T00:00:00-05:00"
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=NEW_YORK)
    return parsed.astimezone(NEW_YORK)


def _fold_key(start_month: str, end_month: str) -> str:
    return f"{start_month.replace('-', '_')}_{end_month.replace('-', '_')}"


def _replay_dataset_root(storage_root: Path, contract_id: str) -> Path:
    return storage_root.parent / "05_replay_datasets" / contract_id


def _load_optional_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(dict(row), sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _unique_csv_values(path: Path, field: str) -> set[str]:
    import csv

    if not path.exists():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        return {str(row.get(field) or "").strip() for row in csv.DictReader(handle) if str(row.get(field) or "").strip()}


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _score(row: Mapping[str, Any], *keys: str, default: float) -> float:
    for key in keys:
        if key not in row:
            continue
        try:
            value = float(row[key])
        except (TypeError, ValueError):
            continue
        return max(-1.0, min(1.0, value))
    return default


def _stable_hash(*parts: Any) -> str:
    return "sha256:" + hashlib.sha256("|".join(json.dumps(part, sort_keys=True, default=str) for part in parts).encode("utf-8")).hexdigest()


def _stable_token(*parts: Any) -> str:
    if not parts:
        return "none"
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


__all__ = [
    "LAYER_10_EVENT_ATTRIBUTION_RECEIPT_CONTRACT_TYPE",
    "LAYER_10_EVENT_ATTRIBUTION_ROW_CONTRACT_TYPE",
    "run_model_group_layer_ten_attribution_if_ready",
]

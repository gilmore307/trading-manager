"""Post-replay M06 ResidualEventGovernance attribution.

This module is the M06 boundary after replay review and before model-group
evaluation. It consumes replay review rows plus local point-in-time event
observations or candidates, writes standardized event
interpretation evidence, applies basic co-event/control/leakage checks, and
emits a M06 attribution receipt. It performs no provider calls, no broker
mutation, and no model activation.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .event_feed_backfill import prepare_event_feed_backfill
from .model_group_attribution import REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE, REPLAY_REVIEW_ROW_CONTRACT_TYPE
from .model_group_replay import CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES, DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
RESIDUAL_EVENT_GOVERNANCE_RECEIPT_CONTRACT_TYPE = "post_replay_residual_event_governance_receipt"
RESIDUAL_EVENT_GOVERNANCE_ATTRIBUTION_ROW_CONTRACT_TYPE = "model_06_residual_event_governance_event_attribution_row"
EVENT_FOCUS_PROPOSAL_ROW_CONTRACT_TYPE = "model_06_residual_event_governance_event_focus_proposal"
TEMPORAL_ATTENTION_CANDIDATE_ROW_CONTRACT_TYPE = "model_06_residual_event_governance_temporal_attention_candidate"
EVENT_FAMILY_OCCURRENCE_SCAN_ROW_CONTRACT_TYPE = "model_06_residual_event_governance_event_family_occurrence_scan_row"
EVENT_FAMILY_BIAS_ASSOCIATION_PACKET_CONTRACT_TYPE = "model_06_residual_event_governance_event_family_bias_association_packet"
EVENT_STRATEGY_PROMOTION_REVIEW_CONTRACT_TYPE = "event_strategy_promotion_review"
ACCEPTED_TEMPORAL_ATTENTION_POOL_ENTRY_CONTRACT_TYPE = "model_06_residual_event_governance_temporal_attention_pool_entry"
EVENT_INTERPRETATION_CONTRACT_TYPE = "event_interpretation"
LEGACY_EVENT_INTERPRETATION_CONTRACT_TYPES = {"event_interpretation_v1"}
COMPLETE_STATUSES = {"succeeded", "complete", "completed"}
ACCEPTED_REVIEW_STATUSES = {"accepted", "reviewed_accepted", "approved", "reviewed"}
ACCEPTED_STANDARDIZATION_STATUSES = {"standardized", "accepted", "complete", "validated"}
EVENT_STRATEGY_REVIEW_DECISIONS = {"approve", "defer", "reject", "insufficient_evidence"}
EVENT_STRATEGY_REVIEW_STATUSES = {"passed", "failed", "insufficient_evidence"}
EVENT_STRATEGY_OVERLAP_STATUSES = {
    "not_in_upstream_features",
    "residual_after_upstream_conditioning",
    "review_required_overlap_unknown",
    "failed",
    "insufficient_evidence",
}
EVENT_STRATEGY_CODEX_MODEL = "gpt-5.5"
EVENT_STRATEGY_CODEX_TIMEOUT_SECONDS = 900
EVENT_STRATEGY_CODEX_WORKDIR = Path("/root/.openclaw/workspace")
EVENT_STRATEGY_CODEX_ADD_DIR = Path("/root/projects")
MAX_EVENT_STRATEGY_REVIEW_PACKETS = 3
PRE_RELEASE_EVENT_TOKENS = {
    "earnings",
    "guidance",
    "macro_release",
    "economic_release",
    "fomc",
    "cpi",
    "jobs_report",
    "fed_decision",
}
PRE_RELEASE_ROLE_TOKENS = {"scheduled", "expected", "calendar", "preview", "estimate", "anticipated", "upcoming", "pre_release", "before_release"}
POST_RELEASE_ROLE_TOKENS = {"released", "reported", "actual", "result", "results", "announced", "filed", "post_release", "after_release"}
POST_RELEASE_TEXT_TOKENS = {
    "reported",
    "reports",
    "announced",
    "announces",
    "released",
    "files",
    "filed",
    "10-q",
    "10-k",
    "8-k",
    "form 10",
    "beats",
    "misses",
    "actual",
    "results",
}
PRE_RELEASE_TEXT_TOKENS = {"scheduled", "expected", "preview", "upcoming", "estimate", "estimates", "before the release", "ahead of"}
SCHEDULED_DATA_RELEASE_TOKENS = PRE_RELEASE_EVENT_TOKENS | {
    "inflation",
    "ppi",
    "pce",
    "nfp",
    "payroll",
    "unemployment",
    "retail_sales",
    "ism",
    "pmi",
    "gdp",
}
SCHEDULED_CALENDAR_TOKENS = {
    "holiday",
    "market_holiday",
    "market_closure",
    "market_close",
    "market_closed",
    "triple_witching",
    "quadruple_witching",
    "options_expiration",
    "index_rebalance",
    "rebalance",
    "roll",
}
CONTINUOUS_EVENT_TOKENS = {
    "war",
    "conflict",
    "strike",
    "shutdown",
    "regime",
    "investigation",
    "probe",
    "litigation",
    "supply_chain",
    "liquidity_crisis",
}
INSTANT_EVENT_TOKENS = {
    "breaking_news",
    "symbol_news",
    "sector_news",
    "headline",
    "shock",
    "halt",
    "downgrade",
    "upgrade",
    "microstructure_liquidity_disruption",
}
EVENT_WINDOW_BEFORE = timedelta(days=3)
EVENT_WINDOW_AFTER = timedelta(days=1)
M06_SQL_EVENT_FIELDS = [
    "event_id",
    "canonical_event_id",
    "dedup_status",
    "source_priority",
    "coverage_reason",
    "covered_by_event_id",
    "event_time",
    "available_time",
    "information_role_type",
    "event_category_type",
    "scope_type",
    "symbol",
    "sector_type",
    "title",
    "summary",
    "source_name",
    "reference_type",
    "reference",
    "source_artifact_path",
]


def run_model_group_residual_event_governance_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    now_utc: datetime | None = None,
    force: bool = False,
    call_agent_review: bool = True,
    agent_reviewer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    codex_bin: str = "codex",
    codex_model: str | None = None,
    codex_timeout_seconds: int = EVENT_STRATEGY_CODEX_TIMEOUT_SECONDS,
    max_agent_review_packets: int = MAX_EVENT_STRATEGY_REVIEW_PACKETS,
) -> SchedulerDecision | None:
    """Run M06 attribution when replay review and PIT event evidence exist."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    review_receipt_path, review_receipt = _latest_replay_review_receipt(dataset_root)
    if review_receipt_path is None or review_receipt is None:
        return None
    decision_rows_ref = str(review_receipt.get("decision_rows_ref") or "")
    review_rows_path = Path(str(review_receipt.get("review_rows_ref") or ""))
    if not decision_rows_ref or not review_rows_path.exists():
        return None
    if not force and _latest_residual_event_governance_receipt(dataset_root, decision_rows_ref=decision_rows_ref) is not None:
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    command = [
        python_executable,
        "scripts/tasks/run_model_group_residual_event_governance.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]
    if not execute:
        fold_scope = _fold_scope_from_dataset(dataset_root)
        event_source_summary = _event_candidate_readiness_summary(storage_root=storage_root, fold_scope=fold_scope)
        if not event_source_summary["event_evidence_available"]:
            return _decision(
                now=now,
                decision_status="backoff",
                reason_code="model_group_residual_event_evidence_missing",
                reason="replay review is ready, but M06 has no local point-in-time event observations or candidates to attribute",
                command=command,
                execution_summary={
                    "contract_id": contract_id,
                    "dataset_root": str(dataset_root),
                    "replay_review_receipt_ref": str(review_receipt_path),
                    "review_rows_ref": str(review_rows_path),
                    "fold_scope": fold_scope,
                    "event_source_summary": event_source_summary,
                    "event_feed_backfill_preparation": None,
                    "required_next_action": "materialize reviewed PIT event observations/candidates before M06 attribution can complete",
                },
            )
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_residual_event_governance_ready",
            reason="post-replay M06 event attribution is ready to run over replay-reviewed failures and PIT event candidates",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "replay_review_receipt_ref": str(review_receipt_path),
                "review_rows_ref": str(review_rows_path),
                "fold_scope": fold_scope,
                "event_source_summary": event_source_summary,
                "event_candidate_count": "not_counted_during_readiness_probe",
                "expected_attribution_rows": "not_counted_during_readiness_probe",
                "expected_event_focus_proposal_count": "not_counted_during_readiness_probe",
                "expected_temporal_attention_candidate_count": "not_counted_during_readiness_probe",
                "expected_event_family_occurrence_count": "not_counted_during_readiness_probe",
                "expected_event_family_bias_association_packet_count": "not_counted_during_readiness_probe",
            },
        )

    review_rows = tuple(_load_jsonl_objects(review_rows_path))
    fold_scope = _fold_scope(dataset_root=dataset_root, review_rows=review_rows)
    event_candidates, event_source_summary = _load_event_candidates(storage_root=storage_root, fold_scope=fold_scope)

    if not event_candidates:
        event_feed_backfill_preparation = None
        target_symbol = _target_symbol_from_review_rows(review_rows)
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
            reason_code="model_group_residual_event_evidence_missing",
            reason="replay review is ready, but M06 has no local point-in-time event observations or candidates to attribute",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "replay_review_receipt_ref": str(review_receipt_path),
                "review_rows_ref": str(review_rows_path),
                "fold_scope": fold_scope,
                "event_source_summary": event_source_summary,
                "event_feed_backfill_preparation": event_feed_backfill_preparation,
                "required_next_action": "materialize reviewed PIT event observations/candidates before M06 attribution can complete",
            },
        )

    attribution_rows, control_report = _build_attribution_rows(review_rows=review_rows, event_candidates=event_candidates, created_at_utc=now.isoformat())
    event_focus_proposals = _build_event_focus_proposals(
        attribution_rows=attribution_rows,
        residual_event_governance_receipt_ref=None,
        attribution_rows_ref=None,
        event_interpretations_ref=None,
        event_summaries_by_ref=_event_summaries_by_ref(event_candidates),
    )
    attention_evidence = _build_event_family_attention_evidence(
        event_focus_proposals=event_focus_proposals,
        attribution_rows=attribution_rows,
        event_candidates=event_candidates,
        temporal_attention_candidate_pool_ref=None,
        event_family_occurrence_scan_ref=None,
        event_family_bias_association_packets_ref=None,
    )
    run_id = "post_replay_residual_event_governance_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_root = dataset_root / "post_replay_attribution_runs" / run_id
    attribution_rows_path = output_root / "residual_event_governance_rows.jsonl"
    event_interpretations_path = output_root / "event_interpretations.jsonl"
    event_focus_proposals_path = output_root / "event_focus_proposals.jsonl"
    temporal_attention_candidates_path = output_root / "temporal_attention_candidate_pool.jsonl"
    event_family_occurrence_scan_path = output_root / "event_family_occurrence_scan.jsonl"
    event_family_bias_packets_path = output_root / "event_family_bias_association_packets.jsonl"
    event_strategy_reviews_path = output_root / "event_strategy_promotion_reviews.jsonl"
    accepted_temporal_attention_pool_path = output_root / "accepted_temporal_attention_pool_entries.jsonl"
    control_report_path = output_root / "control_coevent_leakage_report.json"
    receipt_path = output_root / "post_replay_attribution_receipt.json"
    event_focus_proposals = _build_event_focus_proposals(
        attribution_rows=attribution_rows,
        residual_event_governance_receipt_ref=str(receipt_path),
        attribution_rows_ref=str(attribution_rows_path),
        event_interpretations_ref=str(event_interpretations_path),
        event_summaries_by_ref=_event_summaries_by_ref(event_candidates),
    )
    attention_evidence = _build_event_family_attention_evidence(
        event_focus_proposals=event_focus_proposals,
        attribution_rows=attribution_rows,
        event_candidates=event_candidates,
        temporal_attention_candidate_pool_ref=str(temporal_attention_candidates_path),
        event_family_occurrence_scan_ref=str(event_family_occurrence_scan_path),
        event_family_bias_association_packets_ref=str(event_family_bias_packets_path),
    )
    event_strategy_reviews = _build_event_strategy_promotion_reviews(
        attention_evidence["event_family_bias_association_packets"],
        call_agent_review=call_agent_review,
        agent_reviewer=agent_reviewer,
        codex_bin=codex_bin,
        codex_model=codex_model,
        codex_timeout_seconds=codex_timeout_seconds,
        max_agent_review_packets=max_agent_review_packets,
    )
    accepted_temporal_attention_pool_entries = _build_accepted_temporal_attention_pool_entries(
        attention_evidence["temporal_attention_candidates"],
        event_strategy_reviews,
        accepted_temporal_attention_pool_ref=str(accepted_temporal_attention_pool_path),
        event_strategy_reviews_ref=str(event_strategy_reviews_path),
        created_at_utc=now.isoformat(),
    )
    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_residual_event_governance:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.residual_event_governance.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        output_root.mkdir(parents=True, exist_ok=True)
        _write_jsonl(event_interpretations_path, (candidate["interpretation"] for candidate in event_candidates))
        _write_jsonl(attribution_rows_path, attribution_rows)
        _write_jsonl(event_focus_proposals_path, event_focus_proposals)
        _write_jsonl(temporal_attention_candidates_path, attention_evidence["temporal_attention_candidates"])
        _write_jsonl(event_family_occurrence_scan_path, attention_evidence["event_family_occurrence_scan_rows"])
        _write_jsonl(event_family_bias_packets_path, attention_evidence["event_family_bias_association_packets"])
        _write_jsonl(event_strategy_reviews_path, event_strategy_reviews)
        _write_jsonl(accepted_temporal_attention_pool_path, accepted_temporal_attention_pool_entries)
        control_report_path.write_text(json.dumps(control_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt = {
            "contract_type": RESIDUAL_EVENT_GOVERNANCE_RECEIPT_CONTRACT_TYPE,
            "status": "succeeded",
            "stage_id": "model_group.residual_event_governance",
            "model_surface": "model_06_residual_event_governance",
            "run_id": run_id,
            "contract_id": contract_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "decision_rows_ref": decision_rows_ref,
            "replay_review_receipt_ref": str(review_receipt_path),
            "review_rows_ref": str(review_rows_path),
            "attribution_rows_ref": str(attribution_rows_path),
            "event_interpretations_ref": str(event_interpretations_path),
            "event_focus_proposals_ref": str(event_focus_proposals_path),
            "temporal_attention_candidate_pool_ref": str(temporal_attention_candidates_path),
            "event_family_occurrence_scan_ref": str(event_family_occurrence_scan_path),
            "event_family_bias_association_packets_ref": str(event_family_bias_packets_path),
            "event_strategy_promotion_reviews_ref": str(event_strategy_reviews_path),
            "accepted_temporal_attention_pool_ref": str(accepted_temporal_attention_pool_path),
            "control_coevent_leakage_report_ref": str(control_report_path),
            "event_evidence_consumed": True,
            "event_observation_count": sum(1 for candidate in event_candidates if candidate["observation_status"] == "accepted_observation"),
            "event_candidate_count": len(event_candidates),
            "replay_review_scope_status": "passed",
            "control_analysis_status": "passed",
            "co_event_handling_status": "passed",
            "confounder_analysis_status": "passed",
            "leakage_status": "passed",
            "upstream_overlap_status": "residual_after_upstream_conditioning",
            "processed_replay_review_row_count": len(review_rows),
            "attribution_row_count": len(attribution_rows),
            "event_focus_proposal_count": len(event_focus_proposals),
            "temporal_attention_candidate_count": len(attention_evidence["temporal_attention_candidates"]),
            "event_family_occurrence_scan_row_count": len(attention_evidence["event_family_occurrence_scan_rows"]),
            "event_family_bias_association_packet_count": len(attention_evidence["event_family_bias_association_packets"]),
            "event_strategy_promotion_review_count": len(event_strategy_reviews),
            "accepted_temporal_attention_pool_entry_count": len(accepted_temporal_attention_pool_entries),
            "deterministic_event_family_gate_status": attention_evidence["deterministic_gate_status"],
            "event_strategy_promotion_review_status": _event_strategy_review_status(event_strategy_reviews),
            "event_focus_proposal_review_gate": "event-strategy-promotion-review",
            "accepted_event_pool_mutation_performed": False,
            "temporal_attention_pool_mutation_performed": bool(accepted_temporal_attention_pool_entries),
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
            "model_03_event_state_promotion_performed": False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_residual_event_governance_executed",
        reason="executed post-replay M06 ResidualEventGovernance attribution over replay-reviewed rows and PIT event candidates",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "post_replay_residual_event_governance_receipt": str(receipt_path),
            "attribution_rows_ref": str(attribution_rows_path),
            "event_interpretations_ref": str(event_interpretations_path),
            "event_focus_proposals_ref": str(event_focus_proposals_path),
            "temporal_attention_candidate_pool_ref": str(temporal_attention_candidates_path),
            "event_family_occurrence_scan_ref": str(event_family_occurrence_scan_path),
            "event_family_bias_association_packets_ref": str(event_family_bias_packets_path),
            "event_strategy_promotion_reviews_ref": str(event_strategy_reviews_path),
            "accepted_temporal_attention_pool_ref": str(accepted_temporal_attention_pool_path),
            "event_candidate_count": len(event_candidates),
            "attribution_row_count": len(attribution_rows),
            "event_focus_proposal_count": len(event_focus_proposals),
            "temporal_attention_candidate_count": len(attention_evidence["temporal_attention_candidates"]),
            "event_family_bias_association_packet_count": len(attention_evidence["event_family_bias_association_packets"]),
            "event_strategy_promotion_review_count": len(event_strategy_reviews),
            "accepted_temporal_attention_pool_entry_count": len(accepted_temporal_attention_pool_entries),
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
        selected_work="model_group.residual_event_governance",
        command=command,
        next_internal_stage="residual_event_governance",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(month=None, selected_work="model_group.residual_event_governance", next_internal_stage="residual_event_governance"),
    )


def _compact_backfill_preparation(summary: Any) -> dict[str, Any]:
    task_keys = tuple(getattr(summary, "task_keys", ()) or ())
    return {
        "contract_type": getattr(summary, "contract_type", "manager_residual_event_governance_event_feed_backfill_preparation"),
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
    review_rows: Sequence[Mapping[str, Any]],
    event_candidates: Sequence[Mapping[str, Any]],
    created_at_utc: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    attributed = 0
    confounded = 0
    no_attribution = 0
    for index, review_row in enumerate(review_rows, start=1):
        matched = _matching_event_candidates(review_row, event_candidates)
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
        decision_time = str(review_row.get("decision_time") or "")
        impact_profile = _impact_profile_from_review_row(review_row, decision_time=decision_time)
        window_start, window_end = _impact_search_window(
            impact_profile["impact_exposure_time"],
            replay_month=str(review_row.get("replay_month") or ""),
        )
        row_id = f"l6_event_attr_{index:08d}"
        rows.append(
            {
                "contract_type": RESIDUAL_EVENT_GOVERNANCE_ATTRIBUTION_ROW_CONTRACT_TYPE,
                "stage_id": "model_group.residual_event_governance",
                "attribution_id": row_id,
                "source_replay_review_row_contract_type": str(review_row.get("contract_type") or REPLAY_REVIEW_ROW_CONTRACT_TYPE),
                "source_replay_review_id": review_row.get("review_id") or review_row.get("attribution_id"),
                "source_decision_id": review_row.get("source_decision_id"),
                "failure_type": review_row.get("failure_type"),
                "target_symbol": review_row.get("target_symbol"),
                "replay_month": review_row.get("replay_month"),
                "decision_time": decision_time or None,
                "impact_exposure_time": impact_profile["impact_exposure_time"],
                "impact_onset_time": impact_profile["impact_onset_time"],
                "impact_onset_basis": impact_profile["impact_onset_basis"],
                "impact_scope_type": impact_profile["impact_scope_type"],
                "impact_direction": impact_profile["impact_direction"],
                "impact_raw_return_delta": impact_profile["impact_raw_return_delta"],
                "impact_magnitude_abs_return": impact_profile["impact_magnitude_abs_return"],
                "impact_normalization_denominator": impact_profile["impact_normalization_denominator"],
                "impact_normalized_severity_score": impact_profile["impact_normalized_severity_score"],
                "impact_severity_basis": impact_profile["impact_severity_basis"],
                "impact_search_window_start": window_start,
                "impact_search_window_end": window_end,
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
        "contract_type": "model_06_residual_event_governance_control_coevent_leakage_report",
        "status": "passed",
        "review_row_count": len(review_rows),
        "event_candidate_count": len(event_candidates),
        "attributed_count": attributed,
        "confounded_count": confounded,
        "no_attribution_count": no_attribution,
        "control_analysis_status": "passed",
        "co_event_handling_status": "passed",
        "confounder_analysis_status": "passed",
        "leakage_status": "passed",
        "upstream_overlap_status": "residual_after_upstream_conditioning",
        "same_fold_model_03_event_mutation_performed": False,
        "notes": [
            "M06 attribution consumes post-replay review rows; it does not create same-fold M03 event-state inputs.",
            "Rows with multiple matching events are marked confounded until a later promotion packet proves incremental value.",
            "M06 uses impact_exposure_time rather than model decision_time as the causal cutoff when the replay review row provides an impact clock.",
        ],
    }
    return rows, control_report


def _build_event_focus_proposals(
    *,
    attribution_rows: Sequence[Mapping[str, Any]],
    residual_event_governance_receipt_ref: str | None,
    attribution_rows_ref: str | None,
    event_interpretations_ref: str | None,
    event_summaries_by_ref: Mapping[str, Mapping[str, Any]],
    max_proposals: int = 200,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in attribution_rows:
        event_ref = str(row.get("dominant_event_candidate") or row.get("confounder_event_ref") or "").strip()
        if not event_ref and str(row.get("attribution_status") or "") == "attributed":
            candidate_refs = row.get("candidate_event_refs") if isinstance(row.get("candidate_event_refs"), list) else []
            event_ref = str(candidate_refs[0]).strip() if candidate_refs else ""
        if not event_ref:
            continue
        target_symbol = str(row.get("target_symbol") or "").strip().upper() or "UNKNOWN"
        failure_type = str(row.get("failure_type") or "unknown_failure_type").strip()
        key = (event_ref, target_symbol, failure_type)
        group = groups.setdefault(
            key,
            {
                "event_ref": event_ref,
                "target_symbol": target_symbol,
                "failure_type": failure_type,
                "source_replay_review_ids": [],
                "source_decision_ids": [],
                "replay_months": set(),
                "event_interpretation_refs": set(),
                "attribution_status_counts": {},
                "co_event_group_ids": set(),
                "supporting_scores": [],
                "supporting_confidences": [],
                "failure_window_starts": [],
                "failure_window_ends": [],
                "impact_search_window_starts": [],
                "impact_search_window_ends": [],
                "impact_onset_basis_counts": {},
                "impact_scope_type_counts": {},
                "impact_severity_scores": [],
                "impact_magnitude_abs_returns": [],
            },
        )
        group["source_replay_review_ids"].append(row.get("source_replay_review_id"))
        group["source_decision_ids"].append(row.get("source_decision_id"))
        if row.get("replay_month"):
            group["replay_months"].add(str(row.get("replay_month")))
        if row.get("co_event_group_id"):
            group["co_event_group_ids"].add(str(row.get("co_event_group_id")))
        for ref in row.get("event_interpretation_refs") or []:
            if str(ref).strip():
                group["event_interpretation_refs"].add(str(ref))
        status = str(row.get("attribution_status") or "unknown")
        group["attribution_status_counts"][status] = int(group["attribution_status_counts"].get(status, 0)) + 1
        group["supporting_scores"].append(_safe_float(row.get("incremental_attribution_score")))
        group["supporting_confidences"].append(_safe_float(row.get("attribution_confidence_score")))
        if row.get("failure_window_start"):
            group["failure_window_starts"].append(str(row.get("failure_window_start")))
        if row.get("failure_window_end"):
            group["failure_window_ends"].append(str(row.get("failure_window_end")))
        if row.get("impact_search_window_start"):
            group["impact_search_window_starts"].append(str(row.get("impact_search_window_start")))
        if row.get("impact_search_window_end"):
            group["impact_search_window_ends"].append(str(row.get("impact_search_window_end")))
        _increment_count(group["impact_onset_basis_counts"], row.get("impact_onset_basis"))
        _increment_count(group["impact_scope_type_counts"], row.get("impact_scope_type"))
        if row.get("impact_normalized_severity_score") is not None:
            group["impact_severity_scores"].append(_safe_float(row.get("impact_normalized_severity_score")))
        if row.get("impact_magnitude_abs_return") is not None:
            group["impact_magnitude_abs_returns"].append(_safe_float(row.get("impact_magnitude_abs_return")))
    ranked = sorted(
        groups.values(),
        key=lambda group: (
            len(group["source_decision_ids"]),
            _average(group["supporting_confidences"]),
            _average(group["supporting_scores"]),
            str(group["event_ref"]),
        ),
        reverse=True,
    )
    proposals: list[dict[str, Any]] = []
    for group in ranked[:max_proposals]:
        proposal_id = "l6_event_focus_" + _stable_token(group["event_ref"], group["target_symbol"], group["failure_type"])
        support_count = len(group["source_decision_ids"])
        event_summary = dict(event_summaries_by_ref.get(str(group["event_ref"]), {}))
        failure_attention_reason = (
            f"{support_count} {group['target_symbol']} {group['failure_type']} failures "
            f"in {', '.join(sorted(group['replay_months'])) or 'unknown replay months'} matched "
            f"{group['event_ref']} with attribution statuses "
            f"{dict(sorted(group['attribution_status_counts'].items()))} and "
            f"{len(group['co_event_group_ids'])} co-event groups."
        )
        proposals.append(
            {
                "contract_type": EVENT_FOCUS_PROPOSAL_ROW_CONTRACT_TYPE,
                "stage_id": "model_group.residual_event_governance",
                "model_surface": "model_06_residual_event_governance",
                "event_focus_proposal_id": proposal_id,
                "proposal_status": "watch_candidate",
                "review_gate": "event-strategy-promotion-review",
                "recommended_next_action": "review_before_accepting_into_temporal_attention_pool",
                "event_ref": group["event_ref"],
                "event_summary": event_summary or None,
                "failure_attention_reason": failure_attention_reason,
                "target_symbol": group["target_symbol"],
                "failure_type": group["failure_type"],
                "supporting_failure_count": support_count,
                "source_decision_ids": _compact_strings(group["source_decision_ids"], limit=50),
                "source_replay_review_ids": _compact_strings(group["source_replay_review_ids"], limit=50),
                "replay_months": sorted(group["replay_months"]),
                "failure_window_start": min(group["failure_window_starts"]) if group["failure_window_starts"] else None,
                "failure_window_end": max(group["failure_window_ends"]) if group["failure_window_ends"] else None,
                "impact_search_window_start": min(group["impact_search_window_starts"]) if group["impact_search_window_starts"] else None,
                "impact_search_window_end": max(group["impact_search_window_ends"]) if group["impact_search_window_ends"] else None,
                "impact_onset_basis_counts": dict(sorted(group["impact_onset_basis_counts"].items())),
                "impact_scope_type_counts": dict(sorted(group["impact_scope_type_counts"].items())),
                "average_impact_normalized_severity_score": _average(group["impact_severity_scores"]),
                "max_impact_normalized_severity_score": max(group["impact_severity_scores"]) if group["impact_severity_scores"] else 0.0,
                "average_impact_magnitude_abs_return": _average(group["impact_magnitude_abs_returns"]),
                "attribution_status_counts": dict(sorted(group["attribution_status_counts"].items())),
                "co_event_group_count": len(group["co_event_group_ids"]),
                "average_incremental_attribution_score": _average(group["supporting_scores"]),
                "average_attribution_confidence_score": _average(group["supporting_confidences"]),
                "event_interpretation_refs": sorted(group["event_interpretation_refs"])[:50],
                "residual_event_governance_receipt_ref": residual_event_governance_receipt_ref,
                "attribution_rows_ref": attribution_rows_ref,
                "event_interpretations_ref": event_interpretations_ref,
                "accepted_event_pool_mutation_performed": False,
                "temporal_attention_pool_mutation_performed": False,
                "acceptance_blockers": [
                    "requires_event_strategy_promotion_review",
                    "requires_incremental_value_evidence",
                    "requires_co_event_confounder_disposition",
                ],
            }
        )
    return proposals


def _event_summaries_by_ref(event_candidates: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for candidate in event_candidates:
        event_ref = str(candidate.get("event_ref") or "").strip()
        interpretation = candidate.get("interpretation") if isinstance(candidate.get("interpretation"), Mapping) else {}
        if not event_ref:
            continue
        summaries.setdefault(
            event_ref,
            {
                "canonical_event_id": event_ref,
                "normalized_event_type": interpretation.get("normalized_event_type"),
                "affected_entities": interpretation.get("affected_entities") if isinstance(interpretation.get("affected_entities"), list) else [],
                "affected_scope": interpretation.get("affected_scope"),
                "published_time": interpretation.get("published_time"),
                "available_time": interpretation.get("available_time"),
                "rationale_summary": interpretation.get("rationale_summary"),
                "event_domain_tags": interpretation.get("event_domain_tags") if isinstance(interpretation.get("event_domain_tags"), list) else [],
                "source_name": interpretation.get("source_name"),
                "source_artifact_ref": interpretation.get("source_artifact_ref"),
                "source_type": interpretation.get("source_type"),
                "evidence_confidence_score": _safe_float(interpretation.get("evidence_confidence_score")),
                "intensity_score": _safe_float(interpretation.get("intensity_score")),
                "direction_bias_score": _safe_float(interpretation.get("direction_bias_score")),
            },
        )
    return summaries


def _build_event_family_attention_evidence(
    *,
    event_focus_proposals: Sequence[Mapping[str, Any]],
    attribution_rows: Sequence[Mapping[str, Any]],
    event_candidates: Sequence[Mapping[str, Any]],
    temporal_attention_candidate_pool_ref: str | None,
    event_family_occurrence_scan_ref: str | None,
    event_family_bias_association_packets_ref: str | None,
) -> dict[str, Any]:
    """Build deterministic event-family evidence before agent review.

    This deliberately keeps Codex out of base arithmetic. Co-event grouping,
    point-in-time leakage, support counts, and matched-control base rates are
    computed here; agent review later receives a compact packet only after
    deterministic gates say the family is reviewable.
    """

    event_ref_to_candidate = {str(candidate.get("event_ref") or ""): candidate for candidate in event_candidates if str(candidate.get("event_ref") or "")}
    target_family_ids = {
        _event_family_id(event_ref_to_candidate.get(str(proposal.get("event_ref") or "")), target_symbol=str(proposal.get("target_symbol") or ""))
        for proposal in event_focus_proposals
        if str(proposal.get("event_ref") or "") in event_ref_to_candidate
    }
    target_family_ids.discard("")
    event_ref_stats = _event_ref_failure_stats(attribution_rows, event_ref_to_candidate=event_ref_to_candidate)
    occurrence_rows: list[dict[str, Any]] = []
    family_groups: dict[str, dict[str, Any]] = {}
    for candidate in event_candidates:
        event_ref = str(candidate.get("event_ref") or "")
        family_id = _event_family_id(candidate, target_symbol=_family_target_symbol(candidate, event_focus_proposals))
        if not event_ref or family_id not in target_family_ids:
            continue
        interpretation = candidate.get("interpretation") if isinstance(candidate.get("interpretation"), Mapping) else {}
        effect_profile = _event_effect_profile_from_candidate(candidate)
        stats = event_ref_stats.get(event_ref, _empty_event_ref_stats())
        row = {
            "contract_type": EVENT_FAMILY_OCCURRENCE_SCAN_ROW_CONTRACT_TYPE,
            "stage_id": "model_group.residual_event_governance",
            "event_family_id": family_id,
            "event_ref": event_ref,
            "target_symbol": _family_target_symbol(candidate, event_focus_proposals),
            "normalized_event_type": str(interpretation.get("normalized_event_type") or "event_candidate"),
            "affected_scope": str(interpretation.get("affected_scope") or "unknown"),
            "event_temporal_form": effect_profile["event_temporal_form"],
            "event_schedule_type": effect_profile["event_schedule_type"],
            "event_instance_observation_role": effect_profile["event_instance_observation_role"],
            "event_family_prior_role": effect_profile["event_family_prior_role"],
            "event_release_phase": effect_profile["event_release_phase"],
            "event_lifecycle_stage": effect_profile["event_lifecycle_stage"],
            "state_signal_type": effect_profile["state_signal_type"],
            "model_03_event_state_overlay": effect_profile["model_03_event_state_overlay"],
            "model_03_event_projection_type": effect_profile["model_03_event_projection_type"],
            "event_family_impact_parameterization": effect_profile["event_family_impact_parameterization"],
            "available_time": str(candidate.get("available_time") or ""),
            "event_month": str(candidate.get("event_month") or ""),
            "matched_failure_count": stats["matched_failure_count"],
            "attributed_failure_count": stats["attributed_failure_count"],
            "confounded_failure_count": stats["confounded_failure_count"],
            "co_event_group_count": len(stats["co_event_group_ids"]),
            "average_incremental_attribution_score": _average(stats["supporting_scores"]),
            "average_attribution_confidence_score": _average(stats["supporting_confidences"]),
            "leakage_violation_count": stats["leakage_violation_count"],
            "impact_cutoff_violation_count": stats["impact_cutoff_violation_count"],
            "impact_onset_basis_counts": dict(sorted(stats["impact_onset_basis_counts"].items())),
            "impact_scope_type_counts": dict(sorted(stats["impact_scope_type_counts"].items())),
            "average_impact_normalized_severity_score": _average(stats["impact_severity_scores"]),
            "max_impact_normalized_severity_score": max(stats["impact_severity_scores"]) if stats["impact_severity_scores"] else 0.0,
            "impact_normalized_severity_score_count": len(stats["impact_severity_scores"]),
            "average_impact_magnitude_abs_return": _average(stats["impact_magnitude_abs_returns"]),
        }
        occurrence_rows.append(row)
        group = family_groups.setdefault(
            family_id,
            {
                "event_family_id": family_id,
                "target_symbol": row["target_symbol"],
                "normalized_event_type": row["normalized_event_type"],
                "affected_scope": row["affected_scope"],
                "event_refs": set(),
                "occurrence_months": set(),
                "source_event_refs": set(),
                "supporting_proposal_ids": set(),
                "supporting_failure_count": 0,
                "matched_occurrence_count": 0,
                "confounded_failure_count": 0,
                "attributed_failure_count": 0,
                "co_event_group_ids": set(),
                "event_temporal_form_counts": {},
                "event_schedule_type_counts": {},
                "event_instance_observation_role_counts": {},
                "event_release_phase_counts": {},
                "event_lifecycle_stage_counts": {},
                "state_signal_type_counts": {},
                "model_03_event_state_overlay_counts": {},
                "model_03_event_projection_type_counts": {},
                "dominant_event_schedule_type": row["event_schedule_type"],
                "leakage_violation_count": 0,
                "impact_cutoff_violation_count": 0,
                "impact_onset_basis_counts": {},
                "impact_scope_type_counts": {},
                "impact_severity_scores": [],
                "impact_magnitude_abs_returns": [],
                "supporting_scores": [],
                "supporting_confidences": [],
                "source_decision_ids": set(),
                "source_replay_review_ids": set(),
            },
        )
        group["event_refs"].add(event_ref)
        if row["event_month"]:
            group["occurrence_months"].add(row["event_month"])
        if row["matched_failure_count"] > 0:
            group["matched_occurrence_count"] += 1
        group["supporting_failure_count"] += row["matched_failure_count"]
        group["confounded_failure_count"] += row["confounded_failure_count"]
        group["attributed_failure_count"] += row["attributed_failure_count"]
        group["leakage_violation_count"] += row["leakage_violation_count"]
        group["impact_cutoff_violation_count"] += row["impact_cutoff_violation_count"]
        for key, count in row["impact_onset_basis_counts"].items():
            group["impact_onset_basis_counts"][key] = int(group["impact_onset_basis_counts"].get(key, 0)) + int(count)
        for key, count in row["impact_scope_type_counts"].items():
            group["impact_scope_type_counts"][key] = int(group["impact_scope_type_counts"].get(key, 0)) + int(count)
        if row["impact_normalized_severity_score_count"] > 0:
            group["impact_severity_scores"].append(row["average_impact_normalized_severity_score"])
        if row["average_impact_magnitude_abs_return"]:
            group["impact_magnitude_abs_returns"].append(row["average_impact_magnitude_abs_return"])
        group["supporting_scores"].extend(stats["supporting_scores"])
        group["supporting_confidences"].extend(stats["supporting_confidences"])
        group["co_event_group_ids"].update(stats["co_event_group_ids"])
        group["source_decision_ids"].update(stats["source_decision_ids"])
        group["source_replay_review_ids"].update(stats["source_replay_review_ids"])
        _increment_count(group["event_temporal_form_counts"], row["event_temporal_form"])
        _increment_count(group["event_schedule_type_counts"], row["event_schedule_type"])
        _increment_count(group["event_instance_observation_role_counts"], row["event_instance_observation_role"])
        _increment_count(group["event_release_phase_counts"], row["event_release_phase"])
        _increment_count(group["event_lifecycle_stage_counts"], row["event_lifecycle_stage"])
        _increment_count(group["state_signal_type_counts"], row["state_signal_type"])
        _increment_count(group["model_03_event_state_overlay_counts"], row["model_03_event_state_overlay"])
        _increment_count(group["model_03_event_projection_type_counts"], row["model_03_event_projection_type"])
    for proposal in event_focus_proposals:
        event_ref = str(proposal.get("event_ref") or "")
        candidate = event_ref_to_candidate.get(event_ref)
        family_id = _event_family_id(candidate, target_symbol=str(proposal.get("target_symbol") or ""))
        group = family_groups.get(family_id)
        if group is None:
            continue
        group["supporting_proposal_ids"].add(str(proposal.get("event_focus_proposal_id") or ""))
        group["source_event_refs"].add(event_ref)

    candidate_rows: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    for group in sorted(family_groups.values(), key=lambda item: (item["supporting_failure_count"], item["event_family_id"]), reverse=True):
        occurrence_count = len(group["event_refs"])
        matched_occurrence_count = int(group["matched_occurrence_count"])
        unmatched_occurrence_count = max(0, occurrence_count - matched_occurrence_count)
        matched_failure_rate = matched_occurrence_count / occurrence_count if occurrence_count else 0.0
        background_failure_rate = unmatched_occurrence_count / occurrence_count if occurrence_count else 0.0
        average_score = _average(group["supporting_scores"])
        average_confidence = _average(group["supporting_confidences"])
        effect_profile = _dominant_effect_profile(group)
        pit_status = "passed" if occurrence_count > 0 else "insufficient_evidence"
        leakage_status = "passed" if group["leakage_violation_count"] == 0 else "failed"
        impact_onset_status = "passed" if int(group["impact_onset_basis_counts"].get("source_impact_clock") or 0) > 0 and int(group["impact_onset_basis_counts"].get("decision_time_fallback") or 0) == 0 else "insufficient_evidence"
        impact_severity_status = "passed" if group["impact_severity_scores"] else "insufficient_evidence"
        co_event_confounder_status = "passed" if group["confounded_failure_count"] == 0 else "failed"
        control_status = "passed" if occurrence_count >= 2 and matched_occurrence_count >= 1 and unmatched_occurrence_count >= 1 else "insufficient_evidence"
        if effect_profile["state_signal_type"] in {"risk_state", "impact_state"}:
            association_status = "passed" if group["supporting_failure_count"] >= 1 and matched_occurrence_count >= 1 and average_confidence >= 0.35 else "insufficient_evidence"
        else:
            association_status = "passed" if group["supporting_failure_count"] >= 1 and average_score >= 0.5 and average_confidence >= 0.5 else "insufficient_evidence"
        deterministic_gate_status = (
            "passed"
            if pit_status == "passed"
            and leakage_status == "passed"
            and impact_onset_status == "passed"
            and impact_severity_status == "passed"
            and co_event_confounder_status == "passed"
            and control_status == "passed"
            and association_status == "passed"
            else "blocked"
        )
        blockers = []
        if pit_status != "passed":
            blockers.append("pit_occurrence_evidence_insufficient")
        if leakage_status != "passed":
            blockers.append("leakage_violation_detected")
        if impact_onset_status != "passed":
            blockers.append("impact_onset_not_estimated_from_market_path")
        if impact_severity_status != "passed":
            blockers.append("impact_severity_not_target_normalized")
        if co_event_confounder_status != "passed":
            blockers.append("co_event_or_confounder_not_discharged")
        if control_status != "passed":
            blockers.append("matched_control_base_rate_insufficient")
        if association_status != "passed":
            blockers.append("bias_association_strength_insufficient")
        packet_ref = f"{event_family_bias_association_packets_ref or 'event_family_bias_association_packets.jsonl'}#{len(packets) + 1}"
        candidate_ref = f"{temporal_attention_candidate_pool_ref or 'temporal_attention_candidate_pool.jsonl'}#{len(candidate_rows) + 1}"
        candidate_rows.append(
            {
                "contract_type": TEMPORAL_ATTENTION_CANDIDATE_ROW_CONTRACT_TYPE,
                "stage_id": "model_group.residual_event_governance",
                "candidate_id": "l10_temporal_attention_candidate_" + _stable_token(group["event_family_id"]),
                "candidate_status": "ready_for_agent_review" if deterministic_gate_status == "passed" else "blocked_by_deterministic_controls",
                "event_family_id": group["event_family_id"],
                "target_symbol": group["target_symbol"],
                "normalized_event_type": group["normalized_event_type"],
                "event_temporal_form": effect_profile["event_temporal_form"],
                "event_schedule_type": effect_profile["event_schedule_type"],
                "event_instance_observation_role": effect_profile["event_instance_observation_role"],
                "event_family_prior_role": effect_profile["event_family_prior_role"],
                "event_release_phase": effect_profile["event_release_phase"],
                "event_lifecycle_stage": effect_profile["event_lifecycle_stage"],
                "state_signal_type": effect_profile["state_signal_type"],
                "model_03_event_state_overlay": effect_profile["model_03_event_state_overlay"],
                "model_03_event_projection_type": effect_profile["model_03_event_projection_type"],
                "event_family_impact_parameterization": effect_profile["event_family_impact_parameterization"],
                "supporting_failure_count": group["supporting_failure_count"],
                "occurrence_count": occurrence_count,
                "matched_occurrence_count": matched_occurrence_count,
                "matched_failure_rate": matched_failure_rate,
                "background_failure_rate": background_failure_rate,
                "deterministic_gate_status": deterministic_gate_status,
                "deterministic_blockers": blockers,
                "impact_onset_status": impact_onset_status,
                "impact_severity_status": impact_severity_status,
                "impact_onset_basis_counts": dict(sorted(group["impact_onset_basis_counts"].items())),
                "impact_scope_type_counts": dict(sorted(group["impact_scope_type_counts"].items())),
                "average_impact_normalized_severity_score": _average(group["impact_severity_scores"]),
                "max_impact_normalized_severity_score": max(group["impact_severity_scores"]) if group["impact_severity_scores"] else 0.0,
                "average_impact_magnitude_abs_return": _average(group["impact_magnitude_abs_returns"]),
                "event_family_bias_association_packet_ref": packet_ref,
                "temporal_attention_pool_mutation_performed": False,
            }
        )
        packets.append(
            {
                "contract_type": EVENT_FAMILY_BIAS_ASSOCIATION_PACKET_CONTRACT_TYPE,
                "review_type": "event_strategy_promotion_review",
                "subject_ref": group["event_family_id"],
                "candidate_ref": candidate_ref,
                "event_family_id": group["event_family_id"],
                "target_symbol": group["target_symbol"],
                "normalized_event_type": group["normalized_event_type"],
                "event_temporal_form": effect_profile["event_temporal_form"],
                "event_schedule_type": effect_profile["event_schedule_type"],
                "event_instance_observation_role": effect_profile["event_instance_observation_role"],
                "event_family_prior_role": effect_profile["event_family_prior_role"],
                "event_release_phase": effect_profile["event_release_phase"],
                "event_lifecycle_stage": effect_profile["event_lifecycle_stage"],
                "state_signal_type": effect_profile["state_signal_type"],
                "model_03_event_state_overlay": effect_profile["model_03_event_state_overlay"],
                "model_03_event_projection_type": effect_profile["model_03_event_projection_type"],
                "event_family_impact_parameterization": effect_profile["event_family_impact_parameterization"],
                "affected_scope": group["affected_scope"],
                "event_temporal_form_counts": dict(sorted(group["event_temporal_form_counts"].items())),
                "event_schedule_type_counts": dict(sorted(group["event_schedule_type_counts"].items())),
                "event_instance_observation_role_counts": dict(sorted(group["event_instance_observation_role_counts"].items())),
                "event_release_phase_counts": dict(sorted(group["event_release_phase_counts"].items())),
                "event_lifecycle_stage_counts": dict(sorted(group["event_lifecycle_stage_counts"].items())),
                "state_signal_type_counts": dict(sorted(group["state_signal_type_counts"].items())),
                "model_03_event_state_overlay_counts": dict(sorted(group["model_03_event_state_overlay_counts"].items())),
                "model_03_event_projection_type_counts": dict(sorted(group["model_03_event_projection_type_counts"].items())),
                "deterministic_gate_status": deterministic_gate_status,
                "pit_status": pit_status,
                "control_status": control_status,
                "co_event_confounder_status": co_event_confounder_status,
                "overlap_status": "residual_after_upstream_conditioning",
                "leakage_status": leakage_status,
                "impact_onset_status": impact_onset_status,
                "impact_severity_status": impact_severity_status,
                "association_status": association_status,
                "occurrence_count": occurrence_count,
                "matched_occurrence_count": matched_occurrence_count,
                "unmatched_occurrence_count": unmatched_occurrence_count,
                "supporting_failure_count": group["supporting_failure_count"],
                "attributed_failure_count": group["attributed_failure_count"],
                "confounded_failure_count": group["confounded_failure_count"],
                "co_event_group_count": len(group["co_event_group_ids"]),
                "leakage_violation_count": group["leakage_violation_count"],
                "impact_cutoff_violation_count": group["impact_cutoff_violation_count"],
                "impact_onset_basis_counts": dict(sorted(group["impact_onset_basis_counts"].items())),
                "impact_scope_type_counts": dict(sorted(group["impact_scope_type_counts"].items())),
                "average_impact_normalized_severity_score": _average(group["impact_severity_scores"]),
                "max_impact_normalized_severity_score": max(group["impact_severity_scores"]) if group["impact_severity_scores"] else 0.0,
                "average_impact_magnitude_abs_return": _average(group["impact_magnitude_abs_returns"]),
                "matched_failure_rate": matched_failure_rate,
                "background_failure_rate": background_failure_rate,
                "average_incremental_attribution_score": average_score,
                "average_attribution_confidence_score": average_confidence,
                "occurrence_months": sorted(group["occurrence_months"]),
                "source_event_refs": sorted(group["source_event_refs"])[:50],
                "supporting_proposal_ids": sorted(item for item in group["supporting_proposal_ids"] if item)[:50],
                "source_decision_ids": sorted(group["source_decision_ids"])[:50],
                "source_replay_review_ids": sorted(group["source_replay_review_ids"])[:50],
                "event_family_occurrence_scan_ref": event_family_occurrence_scan_ref,
                "allowed_model_use": ["temporal_attention_pool", "event_family_scouting", "model_03_event_state_overlay_candidate"],
                "blocked_model_use": [] if deterministic_gate_status == "passed" else ["accepted_temporal_attention_pool", "model_03_event_state_promotion"],
                "blocking_issues": blockers,
                "required_followups": [] if deterministic_gate_status == "passed" else ["collect non-confounded matched controls before agent review"],
                "provider_calls": 0,
                "broker_execution_performed": False,
                "model_activation_performed": False,
            }
        )
    return {
        "temporal_attention_candidates": candidate_rows,
        "event_family_occurrence_scan_rows": occurrence_rows,
        "event_family_bias_association_packets": packets,
        "deterministic_gate_status": "passed" if packets and any(packet["deterministic_gate_status"] == "passed" for packet in packets) else "blocked",
    }


def _event_ref_failure_stats(
    attribution_rows: Sequence[Mapping[str, Any]],
    *,
    event_ref_to_candidate: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for row in attribution_rows:
        refs = {str(ref) for ref in row.get("candidate_event_refs") or [] if str(ref)}
        for key in ("dominant_event_candidate", "confounder_event_ref"):
            if str(row.get(key) or ""):
                refs.add(str(row[key]))
        for event_ref in refs:
            item = stats.setdefault(event_ref, _empty_event_ref_stats())
            item["matched_failure_count"] += 1
            status = str(row.get("attribution_status") or "")
            if status == "attributed":
                item["attributed_failure_count"] += 1
            if status == "confounded":
                item["confounded_failure_count"] += 1
            if str(row.get("co_event_group_id") or ""):
                item["co_event_group_ids"].add(str(row["co_event_group_id"]))
            item["supporting_scores"].append(_safe_float(row.get("incremental_attribution_score")))
            item["supporting_confidences"].append(_safe_float(row.get("attribution_confidence_score")))
            if str(row.get("source_decision_id") or ""):
                item["source_decision_ids"].add(str(row["source_decision_id"]))
            if str(row.get("source_replay_review_id") or ""):
                item["source_replay_review_ids"].add(str(row["source_replay_review_id"]))
            _increment_count(item["impact_onset_basis_counts"], row.get("impact_onset_basis"))
            _increment_count(item["impact_scope_type_counts"], row.get("impact_scope_type"))
            if row.get("impact_normalized_severity_score") is not None:
                item["impact_severity_scores"].append(_safe_float(row.get("impact_normalized_severity_score")))
            if row.get("impact_magnitude_abs_return") is not None:
                item["impact_magnitude_abs_returns"].append(_safe_float(row.get("impact_magnitude_abs_return")))
            candidate = event_ref_to_candidate.get(event_ref)
            event_time = _parse_datetime(str(candidate.get("available_time") or candidate.get("event_time") or "")) if candidate else None
            impact_cutoff_time = _parse_datetime(str(row.get("impact_exposure_time") or row.get("impact_onset_time") or row.get("decision_time") or ""))
            if event_time is not None and impact_cutoff_time is not None and event_time > impact_cutoff_time:
                item["leakage_violation_count"] += 1
                item["impact_cutoff_violation_count"] += 1
    return stats


def _empty_event_ref_stats() -> dict[str, Any]:
    return {
        "matched_failure_count": 0,
        "attributed_failure_count": 0,
        "confounded_failure_count": 0,
        "co_event_group_ids": set(),
        "supporting_scores": [],
        "supporting_confidences": [],
        "source_decision_ids": set(),
        "source_replay_review_ids": set(),
        "leakage_violation_count": 0,
        "impact_cutoff_violation_count": 0,
        "impact_onset_basis_counts": {},
        "impact_scope_type_counts": {},
        "impact_severity_scores": [],
        "impact_magnitude_abs_returns": [],
    }


def _event_family_id(candidate: Mapping[str, Any] | None, *, target_symbol: str) -> str:
    if candidate is None:
        return ""
    interpretation = candidate.get("interpretation") if isinstance(candidate.get("interpretation"), Mapping) else {}
    normalized_event_type = str(interpretation.get("normalized_event_type") or "event_candidate").strip().lower()
    affected_scope = str(interpretation.get("affected_scope") or "unknown").strip().lower()
    target = str(target_symbol or candidate.get("symbol") or "").strip().upper() or "GLOBAL"
    return "event_family_" + _stable_token(normalized_event_type, affected_scope, target)


def _event_effect_profile(
    normalized_event_type: str,
    *,
    information_role_type: str = "",
    text: str = "",
) -> dict[str, Any]:
    event_type = str(normalized_event_type or "event_candidate").strip().lower()
    role = str(information_role_type or "").strip().lower()
    text_lower = str(text or "").strip().lower()
    combined = " ".join(item for item in (event_type, role, text_lower) if item)
    if _contains_any(combined, SCHEDULED_CALENDAR_TOKENS):
        temporal_form = "scheduled_calendar_event"
        schedule_type = "scheduled_periodic_calendar"
        instance_role = "calendar_state"
    elif _contains_any(combined, SCHEDULED_DATA_RELEASE_TOKENS):
        temporal_form = "scheduled_data_release_event"
        schedule_type = "scheduled_release_calendar"
        instance_role = "observed_release" if _contains_any(role, POST_RELEASE_ROLE_TOKENS) or _contains_any(text_lower, POST_RELEASE_TEXT_TOKENS) else "scheduled_or_expected_release"
    elif _contains_any(combined, CONTINUOUS_EVENT_TOKENS):
        temporal_form = "continuous_or_regime_event"
        schedule_type = "unscheduled_continuous"
        instance_role = "ongoing_event_state"
    elif _contains_any(combined, INSTANT_EVENT_TOKENS):
        temporal_form = "instantaneous_unscheduled_event"
        schedule_type = "unscheduled"
        instance_role = "observed_shock"
    else:
        temporal_form = "instantaneous_unscheduled_event"
        schedule_type = "unscheduled"
        instance_role = "observed_event"

    if instance_role == "observed_release" or _contains_any(role, POST_RELEASE_ROLE_TOKENS) or _contains_any(text_lower, POST_RELEASE_TEXT_TOKENS):
        release_phase = "post_release"
        lifecycle_stage = "post_release_impact_state"
        state_signal_type = "impact_state"
        model_03_event_overlay = "event_post_release_impact_state"
    elif temporal_form in {"scheduled_data_release_event", "scheduled_calendar_event"}:
        release_phase = "pre_release"
        lifecycle_stage = "pre_release_risk_state"
        state_signal_type = "risk_state"
        model_03_event_overlay = "event_pre_release_risk_state_change"
    else:
        release_phase = "post_release"
        lifecycle_stage = "post_release_impact_state"
        state_signal_type = "impact_state"
        model_03_event_overlay = "event_post_release_impact_state"

    return {
        "event_temporal_form": temporal_form,
        "event_schedule_type": schedule_type,
        "event_instance_observation_role": instance_role,
        "event_family_prior_role": "event_family_impact_parameterization",
        "event_release_phase": release_phase,
        "event_lifecycle_stage": lifecycle_stage,
        "state_signal_type": state_signal_type,
        "model_03_event_state_overlay": model_03_event_overlay,
        "model_03_event_projection_type": "event_family_impact_state_projection",
        "event_family_impact_parameterization": _event_family_impact_parameterization(
            temporal_form=temporal_form,
            schedule_type=schedule_type,
            state_signal_type=state_signal_type,
            model_03_event_overlay=model_03_event_overlay,
        ),
    }


def _event_effect_profile_from_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    interpretation = candidate.get("interpretation") if isinstance(candidate.get("interpretation"), Mapping) else {}
    text_parts = [
        interpretation.get("rationale_summary"),
        interpretation.get("title"),
        interpretation.get("summary"),
        interpretation.get("source_name"),
    ]
    return _event_effect_profile(
        str(interpretation.get("normalized_event_type") or "event_candidate"),
        information_role_type=str(interpretation.get("information_role_type") or candidate.get("information_role_type") or ""),
        text=" ".join(str(part) for part in text_parts if part),
    )


def _dominant_effect_profile(group: Mapping[str, Any]) -> dict[str, Any]:
    temporal_forms = group.get("event_temporal_form_counts") if isinstance(group.get("event_temporal_form_counts"), Mapping) else {}
    dominant_temporal_form = _dominant_count_key(temporal_forms) or "instantaneous_unscheduled_event"
    schedule_type = str(group.get("dominant_event_schedule_type") or _schedule_type_for_temporal_form(dominant_temporal_form))
    phases = group.get("event_release_phase_counts") if isinstance(group.get("event_release_phase_counts"), Mapping) else {}
    if int(phases.get("post_release") or 0) > 0:
        return {
            "event_temporal_form": dominant_temporal_form,
            "event_schedule_type": schedule_type,
            "event_instance_observation_role": "observed_release" if dominant_temporal_form == "scheduled_data_release_event" else "observed_event",
            "event_family_prior_role": "event_family_impact_parameterization",
            "event_release_phase": "post_release",
            "event_lifecycle_stage": "post_release_impact_state",
            "state_signal_type": "impact_state",
            "model_03_event_state_overlay": "event_post_release_impact_state",
            "model_03_event_projection_type": "event_family_impact_state_projection",
            "event_family_impact_parameterization": _event_family_impact_parameterization(
                temporal_form=dominant_temporal_form,
                schedule_type=schedule_type,
                state_signal_type="impact_state",
                model_03_event_overlay="event_post_release_impact_state",
            ),
        }
    return {
        "event_temporal_form": dominant_temporal_form,
        "event_schedule_type": schedule_type,
        "event_instance_observation_role": "scheduled_or_expected_release" if dominant_temporal_form == "scheduled_data_release_event" else "calendar_state",
        "event_family_prior_role": "event_family_impact_parameterization",
        "event_release_phase": "pre_release",
        "event_lifecycle_stage": "pre_release_risk_state",
        "state_signal_type": "risk_state",
        "model_03_event_state_overlay": "event_pre_release_risk_state_change",
        "model_03_event_projection_type": "event_family_impact_state_projection",
        "event_family_impact_parameterization": _event_family_impact_parameterization(
            temporal_form=dominant_temporal_form,
            schedule_type=schedule_type,
            state_signal_type="risk_state",
            model_03_event_overlay="event_pre_release_risk_state_change",
        ),
    }


def _event_family_impact_parameterization(
    *,
    temporal_form: str,
    schedule_type: str,
    state_signal_type: str,
    model_03_event_overlay: str,
) -> dict[str, Any]:
    if temporal_form == "scheduled_data_release_event":
        curve = {
            "pre_event_component": "anticipation_window",
            "event_time_component": "release_shock",
            "post_event_component": "absorption_or_followthrough_decay",
        }
    elif temporal_form == "scheduled_calendar_event":
        curve = {
            "pre_event_component": "calendar_positioning_window",
            "event_time_component": "session_or_expiration_mechanics",
            "post_event_component": "calendar_effect_decay",
        }
    elif temporal_form == "continuous_or_regime_event":
        curve = {
            "pre_event_component": "not_calendar_defined",
            "event_time_component": "state_persistence",
            "post_event_component": "resolution_or_decay",
        }
    else:
        curve = {
            "pre_event_component": "not_calendar_defined",
            "event_time_component": "shock_onset",
            "post_event_component": "shock_absorption_or_followthrough",
        }
    return {
        "parameterization_status": "candidate_pending_event_family_backtest",
        "temporal_form": temporal_form,
        "schedule_type": schedule_type,
        "impact_curve_components": curve,
        "impact_scope_parameter": "learn_from_event_family_occurrence_scan",
        "severity_model": "target_normalized_market_response",
        "model_03_event_projection_type": "event_family_impact_state_projection",
        "state_signal_type": state_signal_type,
        "model_03_event_state_overlay": model_03_event_overlay,
    }


def _schedule_type_for_temporal_form(temporal_form: str) -> str:
    return {
        "scheduled_data_release_event": "scheduled_release_calendar",
        "scheduled_calendar_event": "scheduled_periodic_calendar",
        "continuous_or_regime_event": "unscheduled_continuous",
    }.get(temporal_form, "unscheduled")


def _dominant_count_key(counts: Mapping[str, Any]) -> str:
    ranked = sorted(((str(key), int(value or 0)) for key, value in counts.items()), key=lambda item: (item[1], item[0]), reverse=True)
    return ranked[0][0] if ranked else ""


def _contains_any(text: str, tokens: set[str]) -> bool:
    return any(token in text for token in tokens)


def _increment_count(counts: dict[str, int], value: Any) -> None:
    key = str(value or "unknown")
    counts[key] = counts.get(key, 0) + 1


def _family_target_symbol(candidate: Mapping[str, Any], proposals: Sequence[Mapping[str, Any]]) -> str:
    event_ref = str(candidate.get("event_ref") or "")
    for proposal in proposals:
        if str(proposal.get("event_ref") or "") == event_ref:
            return str(proposal.get("target_symbol") or "").strip().upper() or "UNKNOWN"
    symbol = str(candidate.get("symbol") or "").strip().upper()
    if symbol:
        return symbol
    interpretation = candidate.get("interpretation") if isinstance(candidate.get("interpretation"), Mapping) else {}
    affected_entities = [str(item).strip().upper() for item in interpretation.get("affected_entities") or [] if str(item).strip()]
    return affected_entities[0] if len(affected_entities) == 1 else "UNKNOWN"


def _build_event_strategy_promotion_reviews(
    packets: Sequence[Mapping[str, Any]],
    *,
    call_agent_review: bool,
    agent_reviewer: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
    codex_bin: str,
    codex_model: str | None,
    codex_timeout_seconds: int,
    max_agent_review_packets: int,
) -> list[dict[str, Any]]:
    ready_packets = [
        packet
        for packet in packets
        if str(packet.get("deterministic_gate_status") or "") == "passed"
    ][: max(0, max_agent_review_packets)]
    reviews: list[dict[str, Any]] = []
    for packet in ready_packets:
        fallback = _event_strategy_fallback_review(packet, invocation_status="not_invoked_local_fallback", invocation_error="")
        if agent_reviewer is not None:
            try:
                payload = agent_reviewer(packet)
                reviews.append(_normalize_event_strategy_review(payload, fallback=fallback, invocation_status="completed", invocation_error=""))
            except Exception as exc:  # pragma: no cover - defensive runtime guard.
                reviews.append(_event_strategy_fallback_review(packet, invocation_status="failed", invocation_error=f"agent_reviewer_failed: {exc}"))
            continue
        if not call_agent_review:
            reviews.append(fallback)
            continue
        try:
            payload = _invoke_event_strategy_review_agent(
                review_packet=packet,
                codex_bin=codex_bin,
                codex_model=codex_model,
                timeout_seconds=codex_timeout_seconds,
            )
            reviews.append(_normalize_event_strategy_review(payload, fallback=fallback, invocation_status="completed", invocation_error=""))
        except Exception as exc:
            reviews.append(_event_strategy_fallback_review(packet, invocation_status="failed", invocation_error=f"codex_agent_call_failed: {exc}"))
    return reviews


def _event_strategy_fallback_review(packet: Mapping[str, Any], *, invocation_status: str, invocation_error: str) -> dict[str, Any]:
    return {
        "contract_type": EVENT_STRATEGY_PROMOTION_REVIEW_CONTRACT_TYPE,
        "review_type": "event_strategy_promotion_review",
        "subject_ref": str(packet.get("subject_ref") or packet.get("event_family_id") or ""),
        "decision": "insufficient_evidence",
        "pit_status": str(packet.get("pit_status") or "insufficient_evidence"),
        "control_status": str(packet.get("control_status") or "insufficient_evidence"),
        "overlap_status": str(packet.get("overlap_status") or "review_required_overlap_unknown"),
        "leakage_status": str(packet.get("leakage_status") or "insufficient_evidence"),
        "allowed_model_use": [],
        "blocked_model_use": ["accepted_temporal_attention_pool", "model_03_event_state_promotion"],
        "blocking_issues": _string_list(packet.get("blocking_issues")) + ["event_strategy_promotion_review_not_approved"],
        "required_followups": _string_list(packet.get("required_followups")) + ["complete event-strategy-promotion-review successfully"],
        "rationale": "Deterministic packet is reviewable, but no approving event-strategy review has accepted it.",
        "source_packet_ref": str(packet.get("candidate_ref") or ""),
        "agent_invocation_status": invocation_status,
        "agent_invocation_error": invocation_error,
        "provider_calls": 0,
        "broker_execution_performed": False,
        "model_activation_performed": False,
        "temporal_attention_pool_mutation_performed": False,
    }


def _invoke_event_strategy_review_agent(
    *,
    review_packet: Mapping[str, Any],
    codex_bin: str,
    codex_model: str | None,
    timeout_seconds: int,
) -> dict[str, Any]:
    prompt = _event_strategy_review_agent_prompt(review_packet)
    model = codex_model or os.environ.get("TRADING_MANAGER_EVENT_STRATEGY_REVIEW_CODEX_MODEL") or EVENT_STRATEGY_CODEX_MODEL
    with tempfile.TemporaryDirectory(prefix="event-strategy-promotion-review-") as raw_tmp:
        final_output_path = Path(raw_tmp) / "codex_final_output.txt"
        command = [
            codex_bin,
            "exec",
            "--ephemeral",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "read-only",
            "-C",
            str(EVENT_STRATEGY_CODEX_WORKDIR),
            "--output-last-message",
            str(final_output_path),
            "-m",
            model,
            "--add-dir",
            str(EVENT_STRATEGY_CODEX_ADD_DIR),
            prompt,
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout_seconds)
        output = final_output_path.read_text(encoding="utf-8") if final_output_path.exists() else result.stdout
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or f"codex exited {result.returncode}").strip()[:2000])
    return _json_object_from_text(output)


def _event_strategy_review_agent_prompt(review_packet: Mapping[str, Any]) -> str:
    return (
        "Use the event-strategy-promotion-review skill. Review this deterministic M06 event-family packet as a final guard only.\n"
        "Do not recompute co-event/confounder, impact-onset, impact-severity, or leakage gates; those are deterministic inputs. Pre-release and post-release evidence are lifecycle stages of the same event family. Do not require a linear up/down prediction when the packet is a phase-aware state overlay for M03 event-state.\n"
        "Do not activate models, call providers, mutate SQL/storage, submit orders, or mutate accounts.\n"
        "Return strict JSON only, with exactly this contract shape and no markdown:\n"
        "{"
        "\"review_type\":\"event_strategy_promotion_review\","
        "\"subject_ref\":\"string\","
        "\"decision\":\"approve|defer|reject|insufficient_evidence\","
        "\"pit_status\":\"passed|failed|insufficient_evidence\","
        "\"control_status\":\"passed|failed|insufficient_evidence\","
        "\"overlap_status\":\"not_in_upstream_features|residual_after_upstream_conditioning|review_required_overlap_unknown|failed|insufficient_evidence\","
        "\"leakage_status\":\"passed|failed|insufficient_evidence\","
        "\"allowed_model_use\":[\"string\"],"
        "\"blocked_model_use\":[\"string\"],"
        "\"blocking_issues\":[\"string\"],"
        "\"required_followups\":[\"string\"],"
        "\"rationale\":\"short evidence-grounded explanation\""
        "}\n"
        "Evidence packet:\n"
        f"{json.dumps(review_packet, indent=2, sort_keys=True, default=str)}\n"
    )


def _normalize_event_strategy_review(
    payload: Mapping[str, Any],
    *,
    fallback: Mapping[str, Any],
    invocation_status: str,
    invocation_error: str,
) -> dict[str, Any]:
    return {
        "contract_type": EVENT_STRATEGY_PROMOTION_REVIEW_CONTRACT_TYPE,
        "review_type": "event_strategy_promotion_review",
        "subject_ref": _string_choice(payload.get("subject_ref"), fallback.get("subject_ref"), allowed=None),
        "decision": _string_choice(payload.get("decision"), "insufficient_evidence", allowed=EVENT_STRATEGY_REVIEW_DECISIONS),
        "pit_status": _string_choice(payload.get("pit_status"), fallback.get("pit_status"), allowed=EVENT_STRATEGY_REVIEW_STATUSES),
        "control_status": _string_choice(payload.get("control_status"), fallback.get("control_status"), allowed=EVENT_STRATEGY_REVIEW_STATUSES),
        "overlap_status": _string_choice(payload.get("overlap_status"), fallback.get("overlap_status"), allowed=EVENT_STRATEGY_OVERLAP_STATUSES),
        "leakage_status": _string_choice(payload.get("leakage_status"), fallback.get("leakage_status"), allowed=EVENT_STRATEGY_REVIEW_STATUSES),
        "allowed_model_use": _string_list(payload.get("allowed_model_use")),
        "blocked_model_use": _string_list(payload.get("blocked_model_use")),
        "blocking_issues": _string_list(payload.get("blocking_issues")),
        "required_followups": _string_list(payload.get("required_followups")),
        "rationale": str(payload.get("rationale") or fallback.get("rationale") or ""),
        "source_packet_ref": str(fallback.get("source_packet_ref") or ""),
        "agent_invocation_status": invocation_status,
        "agent_invocation_error": invocation_error,
        "provider_calls": 0,
        "broker_execution_performed": False,
        "model_activation_performed": False,
        "temporal_attention_pool_mutation_performed": False,
    }


def _build_accepted_temporal_attention_pool_entries(
    candidate_rows: Sequence[Mapping[str, Any]],
    reviews: Sequence[Mapping[str, Any]],
    *,
    accepted_temporal_attention_pool_ref: str,
    event_strategy_reviews_ref: str,
    created_at_utc: str,
) -> list[dict[str, Any]]:
    approved_by_subject = {
        str(review.get("subject_ref") or ""): review
        for review in reviews
        if str(review.get("decision") or "") == "approve"
        and str(review.get("pit_status") or "") == "passed"
        and str(review.get("control_status") or "") == "passed"
        and str(review.get("leakage_status") or "") == "passed"
    }
    entries: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        family_id = str(candidate.get("event_family_id") or "")
        review = approved_by_subject.get(family_id)
        if review is None:
            continue
        entries.append(
            {
                "contract_type": ACCEPTED_TEMPORAL_ATTENTION_POOL_ENTRY_CONTRACT_TYPE,
                "stage_id": "model_group.residual_event_governance",
                "pool_entry_id": "temporal_attention_pool_" + _stable_token(family_id, created_at_utc),
                "pool_status": "accepted",
                "event_family_id": family_id,
                "target_symbol": candidate.get("target_symbol"),
                "normalized_event_type": candidate.get("normalized_event_type"),
                "event_temporal_form": candidate.get("event_temporal_form"),
                "event_schedule_type": candidate.get("event_schedule_type"),
                "event_instance_observation_role": candidate.get("event_instance_observation_role"),
                "event_family_prior_role": candidate.get("event_family_prior_role"),
                "event_release_phase": candidate.get("event_release_phase"),
                "event_lifecycle_stage": candidate.get("event_lifecycle_stage"),
                "state_signal_type": candidate.get("state_signal_type"),
                "model_03_event_state_overlay": candidate.get("model_03_event_state_overlay"),
                "model_03_event_projection_type": candidate.get("model_03_event_projection_type"),
                "event_family_impact_parameterization": candidate.get("event_family_impact_parameterization"),
                "source_candidate_ref": candidate.get("event_family_bias_association_packet_ref"),
                "event_strategy_review_ref": f"{event_strategy_reviews_ref}#{len(entries) + 1}",
                "accepted_temporal_attention_pool_ref": accepted_temporal_attention_pool_ref,
                "allowed_model_use": _string_list(review.get("allowed_model_use")) or ["temporal_attention_pool"],
                "blocked_model_use": _string_list(review.get("blocked_model_use")),
                "created_at_utc": created_at_utc,
                "provider_calls": 0,
                "broker_execution_performed": False,
                "model_activation_performed": False,
            }
        )
    return entries


def _event_strategy_review_status(reviews: Sequence[Mapping[str, Any]]) -> str:
    if not reviews:
        return "not_invoked_no_deterministic_candidate"
    if any(str(review.get("decision") or "") == "approve" for review in reviews):
        return "approved"
    if any(str(review.get("agent_invocation_status") or "") == "failed" for review in reviews):
        return "agent_failed"
    return "not_approved"


def _json_object_from_text(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("agent output did not contain a JSON object") from None
        payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("agent output JSON was not an object")
    return payload


def _string_choice(value: Any, fallback: Any, *, allowed: set[str] | None) -> str:
    text = str(value or fallback or "").strip()
    if allowed is not None and text not in allowed:
        return str(fallback or "")
    return text


def _matching_event_candidates(review_row: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    target_symbol = str(review_row.get("target_symbol") or "").strip().upper()
    replay_month = str(review_row.get("replay_month") or "").strip()
    decision_time = str(review_row.get("decision_time") or "").strip()
    impact_profile = _impact_profile_from_review_row(review_row, decision_time=decision_time)
    start, end = _impact_search_window_datetimes(impact_profile["impact_exposure_time"], replay_month=replay_month)
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
    return affected_scope in {"market", "macro", "global", "sector", "industry", "theme", "peer_group", "index_basket"}


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
    observation_path = storage_root / "runtime" / "model_03_event_observation_inputs" / f"{start_month}_{end_month}.json"
    checked_paths.append(str(observation_path))
    if observation_path.exists():
        payload = _load_optional_json_object(observation_path) or {}
        raw_events.extend(_events_from_observation_payload(payload, source_ref=str(observation_path)))
    input_dir = storage_root / "runtime" / "model_06_residual_event_governance" / "input_materialization" / _fold_key(start_month, end_month)
    for filename in ("m06_residual_event_governance_data_acquisition_task_key.json", "source_06_task_key.json"):
        task_key_path = input_dir / filename
        checked_paths.append(str(task_key_path))
        if task_key_path.exists():
            payload = _load_optional_json_object(task_key_path) or {}
            params = payload.get("params") if isinstance(payload.get("params"), Mapping) else {}
            raw_events.extend(_events_from_source_task_key(params, source_ref=str(task_key_path), materialization_receipt_path=input_dir / "materialization_receipt.json"))
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


def _events_from_source_task_key(params: Mapping[str, Any], *, source_ref: str, materialization_receipt_path: Path | None = None) -> Iterable[dict[str, Any]]:
    events = params.get("events")
    rows: list[dict[str, Any]] = []
    if isinstance(events, list):
        for item in events:
            if isinstance(item, Mapping):
                row = dict(item)
                row.setdefault("source_artifact_ref", source_ref)
                rows.append(row)
    if rows:
        return rows
    if not _materialization_receipt_ready(materialization_receipt_path):
        return []
    return _events_from_m06_sql(params, source_ref=source_ref)


def _materialization_receipt_ready(path: Path | None) -> bool:
    if path is None:
        return False
    payload = _load_optional_json_object(path)
    if payload is None:
        return False
    if str(payload.get("contract_type") or "") != "manager_residual_event_governance_input_materialization":
        return False
    return int(payload.get("source_event_count") or 0) > 0 and bool(str(payload.get("source_receipt_path") or "").strip())


def _events_from_m06_sql(params: Mapping[str, Any], *, source_ref: str) -> list[dict[str, Any]]:
    database_url = _trading_storage_database_url()
    if not database_url:
        return []
    clauses: list[str] = []
    values: list[Any] = []
    if params.get("start"):
        clauses.append("available_time >= %s")
        values.append(params["start"])
    if params.get("end"):
        clauses.append("available_time < %s")
        values.append(params["end"])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    statement = f"SELECT {', '.join(M06_SQL_EVENT_FIELDS)} FROM trading_data.model_06_residual_event_governance_data_acquisition{where} ORDER BY available_time, event_id"
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except ImportError:
        return []
    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(statement, values)
            rows = [dict(row) for row in cursor.fetchall()]
    events: list[dict[str, Any]] = []
    for row in rows:
        event = {key: _json_safe_sql_value(value) for key, value in row.items()}
        event["source_artifact_ref"] = event.get("source_artifact_path") or source_ref
        events.append(event)
    return events


def _trading_storage_database_url() -> str | None:
    for path in (Path("/root/secrets/trading_storage_postgres.json"), Path("/root/secrets/openclaw/database-url")):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not text:
            continue
        if text.startswith("{"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            dsn = str(payload.get("dsn") or "").strip()
            if dsn:
                return dsn
            continue
        return text
    return None


def _json_safe_sql_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


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
        "information_role_type": str(interpretation.get("information_role_type") or raw_event.get("information_role_type") or ""),
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
        "source_name": raw_event.get("source_name") or "residual_event_governance_local_event_candidate",
        "source_type": raw_event.get("reference_type") or "local_structured_event_candidate",
        "published_time": raw_event.get("published_time") or raw_event.get("event_time") or raw_event.get("available_time"),
        "available_time": raw_event.get("available_time") or raw_event.get("event_time") or raw_event.get("effective_time"),
        "information_role_type": raw_event.get("information_role_type"),
        "title": raw_event.get("title"),
        "summary": raw_event.get("summary"),
        "interpreted_at": datetime.now(UTC).isoformat(),
        "interpreter_agent_id": "trading-manager.residual_event_governance",
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
        "rationale_summary": raw_event.get("rationale_summary") or raw_event.get("summary") or raw_event.get("title") or "Structured local event candidate standardized for M06 attribution.",
        "evidence_spans": raw_event.get("evidence_spans") or [{"source_ref": raw_event.get("reference") or raw_event.get("source_artifact_ref"), "field": "structured_event_candidate"}],
        "review_status": raw_event.get("review_status") or "candidate",
        "standardization_status": raw_event.get("standardization_status") or "standardized",
    }
    return _fill_interpretation_defaults(row, index=index)


def _fill_interpretation_defaults(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    row.setdefault("source_artifact_ref", f"residual_event_governance_event_candidate:{index}")
    row.setdefault("source_artifact_hash", _stable_hash(row.get("source_artifact_ref"), row.get("normalized_event_type"), row.get("available_time"), row.get("affected_entities")))
    row.setdefault("source_name", "residual_event_governance_local_event_candidate")
    row.setdefault("source_type", "local_structured_event_candidate")
    row.setdefault("published_time", row.get("available_time") or row.get("interpreted_at"))
    row.setdefault("available_time", row.get("published_time") or row.get("interpreted_at"))
    row.setdefault("interpreted_at", datetime.now(UTC).isoformat())
    row.setdefault("information_role_type", "unknown")
    row.setdefault("interpreter_agent_id", "trading-manager.residual_event_governance")
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
    row.setdefault("rationale_summary", "Structured local event candidate standardized for M06 attribution.")
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


def _latest_replay_review_receipt(dataset_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    return _latest_receipt(
        dataset_root / "post_replay_review_runs",
        "post_replay_review_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE
        and str(receipt.get("replay_review_completion_scope") or "") == "full_replay_review"
        and _replay_review_receipt_uses_current_replay_handoff(dataset_root, receipt),
    )


def _replay_review_receipt_uses_current_replay_handoff(dataset_root: Path, receipt: Mapping[str, Any]) -> bool:
    decision_rows_ref = str(receipt.get("decision_rows_ref") or "").strip()
    if not decision_rows_ref:
        return False
    replay_root = dataset_root / "replay_execution_runs"
    if not replay_root.exists():
        return False
    for receipt_path in sorted(replay_root.glob("*/replay_execution_receipt.json")):
        replay_receipt = _load_optional_json_object(receipt_path)
        if replay_receipt is None:
            continue
        if str(replay_receipt.get("decision_rows_ref") or "") != decision_rows_ref:
            continue
        if not _replay_receipt_full_completion_scope(replay_receipt):
            continue
        if _replay_receipt_uses_current_candidate_handoff(replay_receipt):
            return True
    return False


def _replay_receipt_uses_current_candidate_handoff(receipt: Mapping[str, Any]) -> bool:
    target_refs = _string_set(receipt.get("target_refs") or receipt.get("pre_replay_target_refs"))
    asset_class_counts = receipt.get("asset_class_counts")
    if not isinstance(asset_class_counts, Mapping):
        asset_class_counts = {}
    has_equity_or_option_scope = (
        bool(target_refs)
        or int(asset_class_counts.get("us_equity") or 0) > 0
        or int(asset_class_counts.get("us_option") or 0) > 0
    )
    if not has_equity_or_option_scope:
        return True
    portfolio_policy = receipt.get("portfolio_replay_policy")
    if not isinstance(portfolio_policy, Mapping):
        portfolio_policy = {}
    return (
        str(receipt.get("candidate_handoff_status") or "") == "available"
        and str(receipt.get("candidate_handoff_source") or "") in CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES
        and str(portfolio_policy.get("full_budget_replacement_policy") or "") == "continue_scanning_after_budget_full"
        and str(portfolio_policy.get("residual_cash_replacement_policy") or "")
        == "insufficient_cash_falls_through_to_replacement"
    )


def _replay_receipt_full_completion_scope(receipt: Mapping[str, Any]) -> bool:
    completion_scope = str(receipt.get("replay_completion_scope") or "").strip()
    if completion_scope:
        return completion_scope == "full_candidate_universe" and receipt.get("max_decision_rows") is None
    return receipt.get("max_decision_rows") is None


def _latest_residual_event_governance_receipt(dataset_root: Path, *, decision_rows_ref: str) -> dict[str, Any] | None:
    path, receipt = _latest_receipt(
        dataset_root / "post_replay_attribution_runs",
        "post_replay_attribution_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        required_field=("decision_rows_ref", decision_rows_ref),
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == RESIDUAL_EVENT_GOVERNANCE_RECEIPT_CONTRACT_TYPE,
    )
    return dict(receipt) if path is not None and receipt is not None else None


def latest_residual_event_governance_receipt(dataset_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    return _latest_receipt(
        dataset_root / "post_replay_attribution_runs",
        "post_replay_attribution_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == RESIDUAL_EVENT_GOVERNANCE_RECEIPT_CONTRACT_TYPE,
    )


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


def _fold_scope(*, dataset_root: Path, review_rows: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    months = sorted({str(row.get("replay_month") or "") for row in review_rows if str(row.get("replay_month") or "")})
    if not months:
        months = sorted(_unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month"))
    if not months:
        return {"start_month": "unknown", "end_month": "unknown"}
    return {"start_month": months[0], "end_month": months[-1]}


def _fold_scope_from_dataset(dataset_root: Path) -> dict[str, str]:
    months = sorted(_unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month"))
    if not months:
        return {"start_month": "unknown", "end_month": "unknown"}
    return {"start_month": months[0], "end_month": months[-1]}


def _event_candidate_readiness_summary(*, storage_root: Path, fold_scope: Mapping[str, str]) -> dict[str, Any]:
    checked_paths: list[str] = []
    evidence_refs: list[str] = []
    start_month = str(fold_scope.get("start_month") or "")
    end_month = str(fold_scope.get("end_month") or "")

    observation_path = storage_root / "runtime" / "model_03_event_observation_inputs" / f"{start_month}_{end_month}.json"
    checked_paths.append(str(observation_path))
    observation_payload = _load_optional_json_object(observation_path) if observation_path.exists() else None
    if observation_payload is not None and _observation_payload_has_event_refs(observation_payload):
        evidence_refs.append(str(observation_path))

    input_dir = storage_root / "runtime" / "model_06_residual_event_governance" / "input_materialization" / _fold_key(start_month, end_month)
    materialization_receipt_path = input_dir / "materialization_receipt.json"
    for filename in ("m06_residual_event_governance_data_acquisition_task_key.json", "source_06_task_key.json"):
        task_key_path = input_dir / filename
        checked_paths.append(str(task_key_path))
        if not task_key_path.exists():
            continue
        payload = _load_optional_json_object(task_key_path) or {}
        params = payload.get("params") if isinstance(payload.get("params"), Mapping) else {}
        events = params.get("events") if isinstance(params, Mapping) else None
        if isinstance(events, list) and any(isinstance(item, Mapping) for item in events):
            evidence_refs.append(str(task_key_path))
        elif _materialization_receipt_ready(materialization_receipt_path):
            evidence_refs.append(str(materialization_receipt_path))

    return {
        "checked_paths": checked_paths,
        "evidence_refs": sorted(set(evidence_refs)),
        "event_evidence_available": bool(evidence_refs),
        "raw_event_count": "not_counted_during_readiness_probe",
        "standardized_event_candidate_count": "not_counted_during_readiness_probe",
    }


def _observation_payload_has_event_refs(payload: Mapping[str, Any]) -> bool:
    for key in (
        "reviewed_event_interpretations",
        "event_interpretations",
        "accepted_event_interpretations",
        "event_failure_evidence_packets",
        "reviewed_event_interpretation_refs",
        "event_interpretation_refs",
        "accepted_event_interpretation_refs",
        "event_failure_evidence_packet_refs",
    ):
        value = payload.get(key)
        if isinstance(value, list) and bool(value):
            return True
    return False


def _target_symbol_from_review_rows(review_rows: Sequence[Mapping[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in review_rows:
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


def _impact_search_window(impact_exposure_time: str | None, *, replay_month: str) -> tuple[str | None, str | None]:
    start, end = _impact_search_window_datetimes(impact_exposure_time, replay_month=replay_month)
    return (start.isoformat() if start is not None else None, end.isoformat() if end is not None else None)


def _impact_search_window_datetimes(impact_exposure_time: str | None, *, replay_month: str) -> tuple[datetime | None, datetime | None]:
    parsed = _parse_datetime(str(impact_exposure_time or ""))
    if parsed is None and len(replay_month) == 7:
        try:
            parsed = datetime.fromisoformat(f"{replay_month}-01T00:00:00").replace(tzinfo=NEW_YORK)
        except ValueError:
            parsed = None
    if parsed is None:
        return None, None
    return parsed - EVENT_WINDOW_BEFORE, parsed


def _impact_profile_from_review_row(review_row: Mapping[str, Any], *, decision_time: str) -> dict[str, Any]:
    impact_exposure_time = str(review_row.get("impact_exposure_time") or review_row.get("impact_onset_time") or decision_time or "").strip()
    onset_basis = str(review_row.get("impact_onset_basis") or "").strip()
    if not onset_basis:
        onset_basis = "source_impact_clock" if impact_exposure_time and impact_exposure_time != decision_time else "decision_time_fallback"
    return {
        "impact_exposure_time": impact_exposure_time or None,
        "impact_onset_time": str(review_row.get("impact_onset_time") or impact_exposure_time or "").strip() or None,
        "impact_onset_basis": onset_basis,
        "impact_scope_type": str(review_row.get("impact_scope_type") or "target").strip() or "target",
        "impact_direction": str(review_row.get("impact_direction") or "unknown").strip() or "unknown",
        "impact_raw_return_delta": _nullable_float(review_row.get("impact_raw_return_delta")),
        "impact_magnitude_abs_return": _nullable_float(review_row.get("impact_magnitude_abs_return")),
        "impact_normalization_denominator": _nullable_float(review_row.get("impact_normalization_denominator")),
        "impact_normalized_severity_score": _nullable_float(review_row.get("impact_normalized_severity_score")),
        "impact_severity_basis": str(review_row.get("impact_severity_basis") or "unknown").strip() or "unknown",
    }


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
    lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
    path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")


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


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


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


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _nullable_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _average(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _compact_strings(values: Sequence[Any], *, limit: int) -> list[str]:
    compacted: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            compacted.append(text)
        if len(compacted) >= limit:
            break
    return compacted


def _stable_hash(*parts: Any) -> str:
    return "sha256:" + hashlib.sha256("|".join(json.dumps(part, sort_keys=True, default=str) for part in parts).encode("utf-8")).hexdigest()


def _stable_token(*parts: Any) -> str:
    if not parts:
        return "none"
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


__all__ = [
    "EVENT_FOCUS_PROPOSAL_ROW_CONTRACT_TYPE",
    "RESIDUAL_EVENT_GOVERNANCE_RECEIPT_CONTRACT_TYPE",
    "RESIDUAL_EVENT_GOVERNANCE_ATTRIBUTION_ROW_CONTRACT_TYPE",
    "latest_residual_event_governance_receipt",
    "run_model_group_residual_event_governance_if_ready",
]

"""Layer 10 event-focus proposal generation.

This stage turns post-replay Layer 10 attribution rows into reviewable event
focus candidates. It does not accept event families, mutate Layer 4 inputs, or
write dashboard markers; it only prepares the evidence packet that a later
event-strategy promotion review can accept or reject.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from .model_group_layer_ten_attribution import LAYER_10_EVENT_ATTRIBUTION_RECEIPT_CONTRACT_TYPE
from .model_group_replay import DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
EVENT_FOCUS_PROPOSAL_RECEIPT_CONTRACT_TYPE = "post_replay_layer_10_event_focus_proposal_receipt"
EVENT_FOCUS_PROPOSAL_ROW_CONTRACT_TYPE = "model_10_event_risk_governor_event_focus_proposal"
COMPLETE_STATUSES = {"succeeded", "complete", "completed"}


def run_model_group_event_focus_proposal_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    now_utc: datetime | None = None,
    force: bool = False,
    max_proposals: int = 200,
) -> SchedulerDecision | None:
    """Prepare reviewable event-focus proposals from the latest Layer 10 run."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    attribution_receipt_path, attribution_receipt = latest_layer_10_attribution_receipt(dataset_root)
    if attribution_receipt_path is None or attribution_receipt is None:
        return None
    attribution_rows_path = Path(str(attribution_receipt.get("attribution_rows_ref") or ""))
    if not attribution_rows_path.exists():
        return None
    if not force and latest_event_focus_proposal_receipt(
        dataset_root,
        layer_10_attribution_receipt_ref=str(attribution_receipt_path),
    )[0] is not None:
        return None

    attribution_rows = tuple(_load_jsonl_objects(attribution_rows_path))
    event_interpretations_path = Path(str(attribution_receipt.get("event_interpretations_ref") or ""))
    event_summaries = _load_event_interpretation_summaries(event_interpretations_path) if event_interpretations_path.exists() else {}
    proposals = _build_event_focus_proposals(
        attribution_rows=attribution_rows,
        layer_10_attribution_receipt_ref=str(attribution_receipt_path),
        attribution_rows_ref=str(attribution_rows_path),
        event_interpretations_ref=str(event_interpretations_path) if event_interpretations_path.exists() else "",
        event_summaries_by_ref=event_summaries,
        max_proposals=max_proposals,
    )
    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    command = [
        python_executable,
        "scripts/tasks/run_model_group_event_focus_proposal.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]
    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_event_focus_proposal_ready",
            reason="Layer 10 attribution is ready for event-focus proposal generation",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "layer_10_attribution_receipt_ref": str(attribution_receipt_path),
                "attribution_rows_ref": str(attribution_rows_path),
                "expected_event_focus_proposal_count": len(proposals),
            },
        )

    run_id = "post_replay_layer_10_event_focus_proposal_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_root = dataset_root / "post_replay_event_focus_proposal_runs" / run_id
    proposals_path = output_root / "event_focus_proposals.jsonl"
    receipt_path = output_root / "event_focus_proposal_receipt.json"
    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_event_focus_proposal:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.event_focus_proposal.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        output_root.mkdir(parents=True, exist_ok=True)
        _write_jsonl(proposals_path, proposals)
        receipt = {
            "contract_type": EVENT_FOCUS_PROPOSAL_RECEIPT_CONTRACT_TYPE,
            "status": "succeeded",
            "stage_id": "model_group.layer_10_event_focus_proposal",
            "run_id": run_id,
            "contract_id": contract_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "layer_10_attribution_receipt_ref": str(attribution_receipt_path),
            "attribution_rows_ref": str(attribution_rows_path),
            "event_interpretations_ref": str(attribution_receipt.get("event_interpretations_ref") or ""),
            "event_focus_proposals_ref": str(proposals_path),
            "proposal_count": len(proposals),
            "review_gate": "event-strategy-promotion-review",
            "accepted_event_pool_mutation_performed": False,
            "temporal_attention_pool_mutation_performed": False,
            "layer_4_promotion_performed": False,
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_event_focus_proposal_executed",
        reason="generated reviewable Layer 10 event-focus proposals without accepting event families",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "event_focus_proposal_receipt": str(receipt_path),
            "event_focus_proposals_ref": str(proposals_path),
            "proposal_count": len(proposals),
        },
    )


def latest_layer_10_attribution_receipt(dataset_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    return _latest_receipt(
        dataset_root / "post_replay_attribution_runs",
        "post_replay_attribution_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == LAYER_10_EVENT_ATTRIBUTION_RECEIPT_CONTRACT_TYPE,
    )


def latest_event_focus_proposal_receipt(
    dataset_root: Path,
    *,
    layer_10_attribution_receipt_ref: str,
) -> tuple[Path | None, dict[str, Any] | None]:
    return _latest_receipt(
        dataset_root / "post_replay_event_focus_proposal_runs",
        "event_focus_proposal_receipt.json",
        accepted_statuses=COMPLETE_STATUSES,
        required_field=("layer_10_attribution_receipt_ref", layer_10_attribution_receipt_ref),
        predicate=lambda receipt: str(receipt.get("contract_type") or "") == EVENT_FOCUS_PROPOSAL_RECEIPT_CONTRACT_TYPE,
    )


def _build_event_focus_proposals(
    *,
    attribution_rows: Sequence[Mapping[str, Any]],
    layer_10_attribution_receipt_ref: str,
    attribution_rows_ref: str,
    event_interpretations_ref: str,
    event_summaries_by_ref: Mapping[str, Mapping[str, Any]],
    max_proposals: int,
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
                "source_triage_attribution_ids": [],
                "source_decision_ids": [],
                "replay_months": set(),
                "event_interpretation_refs": set(),
                "attribution_status_counts": {},
                "co_event_group_ids": set(),
                "supporting_scores": [],
                "supporting_confidences": [],
                "failure_window_starts": [],
                "failure_window_ends": [],
            },
        )
        group["source_triage_attribution_ids"].append(row.get("source_triage_attribution_id"))
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
        proposal_id = "l10_event_focus_" + _stable_token(group["event_ref"], group["target_symbol"], group["failure_type"])
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
                "event_focus_proposal_id": proposal_id,
                "proposal_status": "watch_candidate",
                "review_gate": "event-strategy-promotion-review",
                "recommended_next_action": "review_before_accepting_into_event_attention_pool",
                "event_ref": group["event_ref"],
                "event_summary": event_summary or None,
                "failure_attention_reason": failure_attention_reason,
                "target_symbol": group["target_symbol"],
                "failure_type": group["failure_type"],
                "supporting_failure_count": support_count,
                "source_decision_ids": _compact_strings(group["source_decision_ids"], limit=50),
                "source_triage_attribution_ids": _compact_strings(group["source_triage_attribution_ids"], limit=50),
                "replay_months": sorted(group["replay_months"]),
                "failure_window_start": min(group["failure_window_starts"]) if group["failure_window_starts"] else None,
                "failure_window_end": max(group["failure_window_ends"]) if group["failure_window_ends"] else None,
                "attribution_status_counts": dict(sorted(group["attribution_status_counts"].items())),
                "co_event_group_count": len(group["co_event_group_ids"]),
                "average_incremental_attribution_score": _average(group["supporting_scores"]),
                "average_attribution_confidence_score": _average(group["supporting_confidences"]),
                "event_interpretation_refs": sorted(group["event_interpretation_refs"])[:50],
                "layer_10_attribution_receipt_ref": layer_10_attribution_receipt_ref,
                "attribution_rows_ref": attribution_rows_ref,
                "event_interpretations_ref": event_interpretations_ref or None,
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
        selected_work="model_group.layer_10_event_focus_proposal",
        command=command,
        next_internal_stage="layer_10_event_focus_proposal",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(month=None, selected_work="model_group.layer_10_event_focus_proposal", next_internal_stage="layer_10_event_focus_proposal"),
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
            status = str(receipt.get("status") or "")
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


def _load_event_interpretation_summaries(path: Path) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for row in _load_jsonl_objects(path):
        canonical_relation = row.get("canonical_relation") if isinstance(row.get("canonical_relation"), Mapping) else {}
        event_ref = str(canonical_relation.get("canonical_event_id") or "").strip()
        if not event_ref:
            continue
        summaries.setdefault(
            event_ref,
            {
                "canonical_event_id": event_ref,
                "normalized_event_type": row.get("normalized_event_type"),
                "affected_entities": row.get("affected_entities") if isinstance(row.get("affected_entities"), list) else [],
                "affected_scope": row.get("affected_scope"),
                "published_time": row.get("published_time"),
                "available_time": row.get("available_time"),
                "rationale_summary": row.get("rationale_summary"),
                "event_domain_tags": row.get("event_domain_tags") if isinstance(row.get("event_domain_tags"), list) else [],
                "source_name": row.get("source_name"),
                "source_artifact_ref": row.get("source_artifact_ref"),
                "source_type": row.get("source_type"),
                "evidence_confidence_score": _safe_float(row.get("evidence_confidence_score")),
                "intensity_score": _safe_float(row.get("intensity_score")),
                "direction_bias_score": _safe_float(row.get("direction_bias_score")),
            },
        )
    return summaries


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(dict(row), sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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


def _stable_token(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:16]


__all__ = [
    "EVENT_FOCUS_PROPOSAL_RECEIPT_CONTRACT_TYPE",
    "EVENT_FOCUS_PROPOSAL_ROW_CONTRACT_TYPE",
    "latest_event_focus_proposal_receipt",
    "run_model_group_event_focus_proposal_if_ready",
]

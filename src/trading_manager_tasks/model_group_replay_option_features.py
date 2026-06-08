"""Manager lifecycle for replay option-feature repair.

Replay must advance like live operation: first run the replay clock through
Layers 1-8, then request option data only when Layer 8 emits a Layer 9
option-expression signal. This controller consumes that replay backoff, acquires
the minimal historical option source windows for the emitted signal timestamps,
generates Layer 9 features from the shared cache, and lets scheduler retry
replay on the next drain step.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .control_plane import persist_manager_requests
from .layer_nine_feature_stage import execute_layer_nine_feature_stage
from .model_group_replay import (
    DEFAULT_REPLAY_CONTRACT_ID,
    _completed_training_fold,
    _dataset_is_frozen_and_complete,
    _load_json_object,
    _replay_dataset_root,
)
from .option_chain_source_acquisition import (
    STAGE_ID as OPTION_CHAIN_SOURCE_STAGE_ID,
    OptionChainSourceReview,
    dispatch_option_chain_source_acquisition,
    manager_requests_from_review,
    request_previews_for_replay_decision_times,
    write_option_chain_task_keys,
)
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock

DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_LOCK_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "locks" / "model_group"
REPLAY_OPTION_FEATURE_STAGE_ID = "model_group.replay_option_features"
DEFAULT_OPTION_SOURCE_SCHEMA = "trading_data"
DEFAULT_OPTION_SOURCE_TABLE = "option_chain_state_source"
DEFAULT_OPTION_FEATURE_SCHEMA = "trading_data"
DEFAULT_OPTION_FEATURE_TABLE = "m09_option_expression_feature_generation"
REPLAY_OPTION_FEATURE_ACQUISITION_REQUIRED = "replay_option_feature_acquisition_required"
REPLAY_OPTION_FEATURE_BACKOFF_REASON = "model_group_replay_option_feature_acquisition_required"
NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class ReplayOptionFeatureRequirement:
    target_ref: str
    timestamp: str
    month: str


def run_model_group_replay_option_features_for_replay_backoff(
    replay_decision: SchedulerDecision,
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    execute_provider_acquisition: bool = False,
    provider_acquisition_limit: int | None = 1,
    selected_target_symbol: str | None = None,
    database_url: str | None = None,
    lock_root: Path = DEFAULT_LOCK_ROOT,
) -> SchedulerDecision | None:
    """Prepare only the option features requested by a replay signal backoff."""

    requirements = replay_option_feature_requirements_from_replay_decision(replay_decision)
    if not requirements:
        return None
    dataset_root = _replay_dataset_root(storage_root, contract_id)
    manifest_path = dataset_root / "dataset_manifest.json"
    freeze_receipt_path = dataset_root / "replay_freeze_receipt.json"
    if not manifest_path.exists() or not freeze_receipt_path.exists():
        return None
    manifest = _load_json_object(manifest_path)
    freeze_receipt = _load_json_object(freeze_receipt_path)
    if not _dataset_is_frozen_and_complete(manifest, freeze_receipt):
        return None
    training_fold = _completed_training_fold(storage_root=storage_root, selected_target_symbol=selected_target_symbol)
    if training_fold is None:
        return None

    db_url = _database_url(database_url)
    if not db_url:
        return _decision(
            decision_status="backoff",
            reason_code="model_group_replay_option_feature_database_missing",
            reason="replay option-feature repair requires the shared SQL database URL",
            selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
            execution_summary={"contract_id": contract_id, "dataset_root": str(dataset_root), "training_fold": training_fold},
        )

    limit = len(requirements) if provider_acquisition_limit is None else max(1, provider_acquisition_limit)
    batch = requirements[:limit]
    source_missing = [item for item in batch if not _source_rows_available(database_url=db_url, requirement=item)]
    source_ready = [item for item in batch if item not in source_missing]
    months_to_generate = {item.month for item in source_ready}
    provider_calls = 0
    dispatch_summary: dict[str, Any] | None = None
    generated_summaries: list[dict[str, Any]] = []
    source_request_ids_by_month: dict[str, list[str]] = {}

    if not execute:
        return _decision(
            decision_status="ready",
            reason_code="model_group_replay_option_feature_repair_ready",
            reason="model-group replay emitted option-expression signal timestamps that can be prepared automatically",
            selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
            execution_summary=_summary(
                contract_id=contract_id,
                dataset_root=dataset_root,
                training_fold=training_fold,
                missing=requirements,
                batch=batch,
                source_missing=source_missing,
                source_ready=source_ready,
            ),
        )

    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_replay_option_features:{contract_id}",
        lock_path=str(lock_root / f"{contract_id}_option_features.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        if source_missing:
            if not execute_provider_acquisition:
                return _decision(
                    decision_status="backoff",
                    reason_code="model_group_replay_option_source_acquisition_required",
                    reason="replay option features require historical option-chain source acquisition",
                    selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
                    execution_summary=_summary(
                        contract_id=contract_id,
                        dataset_root=dataset_root,
                        training_fold=training_fold,
                        missing=requirements,
                        batch=batch,
                        source_missing=source_missing,
                        source_ready=source_ready,
                        required_next_step="enable autonomous provider acquisition for replay option source preparation",
                    ),
                )
            source_request_ids_by_month = _persist_replay_option_source_requests(
                source_missing,
                storage_root=storage_root,
            )
            try:
                for month, request_ids in source_request_ids_by_month.items():
                    dispatch = dispatch_option_chain_source_acquisition(
                        start_month=month,
                        end_month=month,
                        storage_root=storage_root,
                        request_ids=tuple(request_ids),
                        execute_provider_calls=True,
                        continue_on_error=False,
                        database_url=db_url,
                        dynamic_workers=False,
                        max_workers=1,
                    )
                    provider_calls += dispatch.provider_calls
                    dispatch_summary = dispatch.summary_row()
                    months_to_generate.add(month)
            except Exception as exc:
                return _decision(
                    decision_status="backoff",
                    reason_code="model_group_replay_option_source_acquisition_failed",
                    reason=f"{type(exc).__name__}: {exc}",
                    selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
                    provider_calls=provider_calls,
                    dispatch_performed=True,
                    execution_summary=_summary(
                        contract_id=contract_id,
                        dataset_root=dataset_root,
                        training_fold=training_fold,
                        missing=requirements,
                        batch=batch,
                        source_missing=source_missing,
                        source_ready=source_ready,
                        required_next_step=(
                            "route replay option source provider failure to server-error agent repair, "
                            "then retry model_group.replay from the same replay clock"
                        ),
                        dispatch_summary=dispatch_summary,
                        generated_summaries=generated_summaries,
                        source_request_ids_by_month=source_request_ids_by_month,
                        provider_acquisition_error=f"{type(exc).__name__}: {exc}",
                    ),
                )

        for month in sorted(months_to_generate):
            generated = execute_layer_nine_feature_stage(start_month=month, end_month=month)
            generated_summaries.append(generated.summary_row())
            if generated.status != "succeeded":
                return _decision(
                    decision_status="backoff",
                    reason_code="model_group_replay_option_feature_generation_failed",
                    reason=generated.reason or "Layer 9 option feature generation failed",
                    selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
                    provider_calls=provider_calls,
                    dispatch_performed=provider_calls > 0,
                    execution_summary=_summary(
                        contract_id=contract_id,
                        dataset_root=dataset_root,
                        training_fold=training_fold,
                        missing=requirements,
                        batch=batch,
                        source_missing=source_missing,
                        source_ready=source_ready,
                        dispatch_summary=dispatch_summary,
                        generated_summaries=generated_summaries,
                    ),
                )

    return _decision(
        decision_status="executed",
        reason_code="model_group_replay_option_feature_repair_executed",
        reason="prepared replay option source/features for emitted Layer 8 signal timestamps; scheduler can retry replay from the same clock",
        selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
        provider_calls=provider_calls,
        dispatch_performed=provider_calls > 0,
        execution_summary=_summary(
            contract_id=contract_id,
            dataset_root=dataset_root,
            training_fold=training_fold,
            missing=requirements,
            batch=batch,
            source_missing=source_missing,
            source_ready=source_ready,
            dispatch_summary=dispatch_summary,
            generated_summaries=generated_summaries,
        ),
    )


def replay_option_feature_requirements_from_replay_decision(
    replay_decision: SchedulerDecision,
) -> tuple[ReplayOptionFeatureRequirement, ...]:
    if replay_decision.reason_code != REPLAY_OPTION_FEATURE_BACKOFF_REASON:
        return ()
    payload = _option_feature_payload_from_replay_decision(replay_decision)
    sample = payload.get("sample") if isinstance(payload, Mapping) else None
    if not isinstance(sample, Sequence):
        return ()
    requirements: list[ReplayOptionFeatureRequirement] = []
    seen: set[tuple[str, str]] = set()
    for item in sample:
        if not isinstance(item, Mapping):
            continue
        target = str(item.get("target_ref") or item.get("underlying") or "").upper()
        raw_timestamp = item.get("timestamp") or item.get("maximum_permitted_source_end")
        if not raw_timestamp:
            continue
        timestamp = _time_key(raw_timestamp)
        if not target or not timestamp:
            continue
        key = (target, timestamp)
        if key in seen:
            continue
        seen.add(key)
        requirements.append(ReplayOptionFeatureRequirement(target_ref=target, timestamp=timestamp, month=timestamp[:7]))
    return tuple(requirements)


def _option_feature_payload_from_replay_decision(replay_decision: SchedulerDecision) -> dict[str, Any]:
    summary = replay_decision.execution_summary if isinstance(replay_decision.execution_summary, Mapping) else {}
    texts = [
        str(summary.get("runner_stderr") or ""),
        str(summary.get("runner_stdout") or ""),
        replay_decision.reason,
    ]
    decoder = json.JSONDecoder()
    for text in texts:
        token_index = text.find(REPLAY_OPTION_FEATURE_ACQUISITION_REQUIRED)
        if token_index < 0:
            continue
        payload_start = text.find("{", token_index)
        if payload_start < 0:
            continue
        try:
            payload, _ = decoder.raw_decode(text[payload_start:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _database_url(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    if os.environ.get("OPENCLAW_DATABASE_URL"):
        return os.environ["OPENCLAW_DATABASE_URL"]
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    return None


def _source_rows_available(*, database_url: str, requirement: ReplayOptionFeatureRequirement) -> bool:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s) AS table_ref", (f"{DEFAULT_OPTION_SOURCE_SCHEMA}.{DEFAULT_OPTION_SOURCE_TABLE}",))
            exists = cursor.fetchone()
            if not exists or exists.get("table_ref") is None:
                return False
            cursor.execute(
                f"""
                SELECT 1
                FROM "{DEFAULT_OPTION_SOURCE_SCHEMA}"."{DEFAULT_OPTION_SOURCE_TABLE}"
                WHERE "underlying" = %s
                  AND "snapshot_time" = %s::timestamptz
                LIMIT 1
                """,
                (requirement.target_ref, requirement.timestamp),
            )
            return cursor.fetchone() is not None


def _persist_replay_option_source_requests(
    requirements: Sequence[ReplayOptionFeatureRequirement],
    *,
    storage_root: Path,
) -> dict[str, list[str]]:
    grouped: dict[tuple[str, str], list[ReplayOptionFeatureRequirement]] = defaultdict(list)
    for requirement in requirements:
        grouped[(requirement.month, requirement.target_ref)].append(requirement)
    request_ids_by_month: dict[str, list[str]] = {}
    for (month, target_ref), items in grouped.items():
        previews = request_previews_for_replay_decision_times(
            target_symbol=target_ref,
            decision_timestamps=[item.timestamp for item in items],
        )
        review = OptionChainSourceReview(
            contract_type="manager_replay_option_chain_state_source_acquisition_review",
            stage_id=OPTION_CHAIN_SOURCE_STAGE_ID,
            start_month=month,
            end_month=month,
            status="provider_acquisition_ready" if previews else "no_provider_skip_accepted",
            target_symbol=target_ref,
            request_count=len(previews),
            request_previews=previews,
            evidence_refs=("replay_dataset:feed_acquisition_plan",),
            reason=f"{len(previews)} replay signal option-chain source request(s) require ThetaData acquisition before replay retry.",
        )
        requests = manager_requests_from_review(review, storage_root=storage_root)
        write_option_chain_task_keys(requests)
        persist_manager_requests([{key: value for key, value in request.items() if not key.startswith("_")} for request in requests])
        request_ids_by_month.setdefault(month, []).extend(str(request["request_id"]) for request in requests)
    return request_ids_by_month


def _time_key(value: Any) -> str:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.isoformat()
    return parsed.isoformat()


def _decision(
    *,
    decision_status: str,
    reason_code: str,
    reason: str,
    selected_work: str,
    provider_calls: int = 0,
    dispatch_performed: bool = False,
    execution_summary: dict[str, Any] | None = None,
) -> SchedulerDecision:
    now = datetime.now(UTC)
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now.astimezone(NEW_YORK).isoformat(),
        decision_status=decision_status,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=[],
        next_internal_stage=selected_work,
        provider_calls=provider_calls,
        dispatch_performed=dispatch_performed,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
    )


def _summary(
    *,
    contract_id: str,
    dataset_root: Path,
    training_fold: Mapping[str, Any],
    missing: Sequence[ReplayOptionFeatureRequirement],
    batch: Sequence[ReplayOptionFeatureRequirement],
    source_missing: Sequence[ReplayOptionFeatureRequirement],
    source_ready: Sequence[ReplayOptionFeatureRequirement],
    required_next_step: str | None = None,
    dispatch_summary: Mapping[str, Any] | None = None,
    generated_summaries: Sequence[Mapping[str, Any]] = (),
    source_request_ids_by_month: Mapping[str, Sequence[str]] | None = None,
    provider_acquisition_error: str | None = None,
) -> dict[str, Any]:
    return {
        "contract_id": contract_id,
        "dataset_root": str(dataset_root),
        "training_fold": dict(training_fold),
        "missing_option_feature_count": len(missing),
        "batch_count": len(batch),
        "source_missing_count": len(source_missing),
        "source_ready_count": len(source_ready),
        "sample": [item.__dict__ for item in missing[:5]],
        "batch": [item.__dict__ for item in batch],
        "blocked_stage_id": OPTION_CHAIN_SOURCE_STAGE_ID if source_missing else None,
        "resume_stage_id": "model_group.replay",
        "required_next_step": required_next_step,
        "dispatch": dict(dispatch_summary) if dispatch_summary else None,
        "feature_generation": [dict(item) for item in generated_summaries],
        "source_request_ids_by_month": (
            {month: list(request_ids) for month, request_ids in source_request_ids_by_month.items()}
            if source_request_ids_by_month
            else {}
        ),
        "provider_acquisition_error": provider_acquisition_error,
    }


__all__ = [
    "REPLAY_OPTION_FEATURE_STAGE_ID",
    "ReplayOptionFeatureRequirement",
    "replay_option_feature_requirements_from_replay_decision",
    "run_model_group_replay_option_features_for_replay_backoff",
]

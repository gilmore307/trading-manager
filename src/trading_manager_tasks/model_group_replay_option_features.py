"""Manager lifecycle for replay option-feature prerequisites.

Replay execution consumes Layer 9 option-expression candidates at each equity
decision timestamp. This controller keeps that prerequisite automatic: detect
missing replay option features, acquire the minimal historical option source
windows, generate Layer 9 features from the shared cache, and let scheduler
retry replay on the next drain step.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
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
DEFAULT_BAR_SCHEMA = "trading_data"
DEFAULT_BAR_TABLE = "m01_market_regime_data_acquisition"
NEW_YORK = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class ReplayOptionFeatureRequirement:
    target_ref: str
    timestamp: str
    month: str


def run_model_group_replay_option_features_if_required(
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
    """Prepare missing option features for a frozen model-group replay dataset."""

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
            reason="replay option-feature preparation requires the shared SQL database URL",
            selected_work=REPLAY_OPTION_FEATURE_STAGE_ID,
            execution_summary={"contract_id": contract_id, "dataset_root": str(dataset_root), "training_fold": training_fold},
        )

    requirements = _missing_option_feature_requirements(dataset_root=dataset_root, database_url=db_url)
    if not requirements:
        return None

    limit = len(requirements) if provider_acquisition_limit is None else max(1, provider_acquisition_limit)
    batch = requirements[:limit]
    source_missing = [item for item in batch if not _source_rows_available(database_url=db_url, requirement=item)]
    source_ready = [item for item in batch if item not in source_missing]
    months_to_generate = {item.month for item in source_ready}
    provider_calls = 0
    dispatch_summary: dict[str, Any] | None = None
    generated_summaries: list[dict[str, Any]] = []

    if not execute:
        return _decision(
            decision_status="ready",
            reason_code="model_group_replay_option_feature_preparation_ready",
            reason="model-group replay has missing option features that can be prepared automatically",
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
            grouped = _persist_replay_option_source_requests(
                source_missing,
                storage_root=storage_root,
            )
            for month, request_ids in grouped.items():
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
        reason_code="model_group_replay_option_feature_preparation_executed",
        reason="prepared a bounded batch of replay option source/features; scheduler can retry replay after missing count reaches zero",
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


def _database_url(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    if os.environ.get("OPENCLAW_DATABASE_URL"):
        return os.environ["OPENCLAW_DATABASE_URL"]
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    return None


def _missing_option_feature_requirements(*, dataset_root: Path, database_url: str) -> tuple[ReplayOptionFeatureRequirement, ...]:
    plan_path = _feed_acquisition_plan_path(dataset_root)
    bars = _equity_replay_decision_bars(plan_path=plan_path, database_url=database_url)
    available = _available_option_feature_keys(database_url=database_url, targets=bars.keys())
    missing: list[ReplayOptionFeatureRequirement] = []
    for target, rows in sorted(bars.items()):
        for row in rows[:-1]:
            timestamp = str(row.get("timestamp") or "")
            if not timestamp:
                continue
            key = (target, _time_key(timestamp))
            if key in available:
                continue
            missing.append(
                ReplayOptionFeatureRequirement(
                    target_ref=target,
                    timestamp=_time_key(timestamp),
                    month=_time_key(timestamp)[:7],
                )
            )
    return tuple(missing)


def _feed_acquisition_plan_path(dataset_root: Path) -> Path:
    manifest = _load_json_object(dataset_root / "dataset_manifest.json")
    return Path(str(manifest["feed_acquisition_plan_ref"]))


def _equity_replay_decision_bars(*, plan_path: Path, database_url: str) -> dict[str, list[dict[str, Any]]]:
    rows_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with plan_path.open(newline="", encoding="utf-8") as handle:
        for plan_row in csv.DictReader(handle):
            if plan_row.get("source_id") != "alpaca_bars" or plan_row.get("coverage_status") != "available":
                continue
            symbol = str(plan_row.get("target_ref") or "").upper()
            start_date = str(plan_row.get("start_date") or "")
            end_date_exclusive = str(plan_row.get("end_date_exclusive") or "")
            if not symbol or not start_date or not end_date_exclusive:
                continue
            rows_by_target[symbol].extend(
                _load_equity_bars_from_sql(
                    database_url=database_url,
                    symbol=symbol,
                    start_date=start_date,
                    end_date_exclusive=end_date_exclusive,
                )
            )
    deduped: dict[str, list[dict[str, Any]]] = {}
    for target, rows in rows_by_target.items():
        by_timestamp = {str(row["timestamp"]): row for row in rows}
        deduped[target] = sorted(by_timestamp.values(), key=lambda row: str(row["timestamp"]))
    return deduped


def _load_equity_bars_from_sql(*, database_url: str, symbol: str, start_date: str, end_date_exclusive: str) -> list[dict[str, Any]]:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s) AS table_ref", (f"{DEFAULT_BAR_SCHEMA}.{DEFAULT_BAR_TABLE}",))
            exists = cursor.fetchone()
            if not exists or exists.get("table_ref") is None:
                return []
            cursor.execute(
                f"""
                SELECT "symbol", "timeframe", "timestamp", "bar_open", "bar_high", "bar_low", "bar_close", "bar_volume"
                FROM "{DEFAULT_BAR_SCHEMA}"."{DEFAULT_BAR_TABLE}"
                WHERE "symbol" = %s
                  AND "timestamp" >= %s::timestamptz
                  AND "timestamp" < %s::timestamptz
                  AND "bar_close" IS NOT NULL
                ORDER BY "timestamp" ASC
                """,
                (symbol, start_date, end_date_exclusive),
            )
            rows = [dict(row) for row in cursor.fetchall()]
    parsed: list[dict[str, Any]] = []
    for row in rows:
        timestamp_value = row.get("timestamp")
        if hasattr(timestamp_value, "date"):
            date_text = timestamp_value.date().isoformat()
        else:
            date_text = str(timestamp_value or "").split("T", 1)[0]
        if not date_text:
            continue
        parsed.append(
            {
                "symbol": str(row.get("symbol") or symbol).upper(),
                "asset_class": "us_equity",
                "source_id": "alpaca_bars",
                "timeframe": str(row.get("timeframe") or "1Day"),
                "timestamp": f"{date_text}T16:00:00-05:00",
                "date": date_text,
                "bar_open": float(row["bar_open"]),
                "bar_high": float(row["bar_high"]),
                "bar_low": float(row["bar_low"]),
                "bar_close": float(row["bar_close"]),
                "bar_volume": float(row.get("bar_volume") or 0.0),
            }
        )
    return parsed


def _available_option_feature_keys(*, database_url: str, targets: Sequence[str] | Any) -> set[tuple[str, str]]:
    target_filter = sorted({str(target).upper() for target in targets if str(target).strip()})
    if not target_filter:
        return set()
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    with psycopg.connect(database_url, row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s) AS table_ref", (f"{DEFAULT_OPTION_FEATURE_SCHEMA}.{DEFAULT_OPTION_FEATURE_TABLE}",))
            exists = cursor.fetchone()
            if not exists or exists.get("table_ref") is None:
                return set()
            cursor.execute(
                f"""
                SELECT DISTINCT "underlying", "snapshot_time"
                FROM "{DEFAULT_OPTION_FEATURE_SCHEMA}"."{DEFAULT_OPTION_FEATURE_TABLE}"
                WHERE "underlying" = ANY(%s)
                  AND COALESCE("snapshot_type", 'entry') IN ('entry', 'source_cache')
                """,
                (target_filter,),
            )
            return {(str(row["underlying"]).upper(), _time_key(row["snapshot_time"])) for row in cursor.fetchall()}


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
    grouped: dict[str, list[ReplayOptionFeatureRequirement]] = defaultdict(list)
    for requirement in requirements:
        grouped[requirement.month].append(requirement)
    request_ids_by_month: dict[str, list[str]] = {}
    for month, items in grouped.items():
        previews = request_previews_for_replay_decision_times(
            target_symbol=items[0].target_ref,
            decision_timestamps=[item.timestamp for item in items],
        )
        review = OptionChainSourceReview(
            contract_type="manager_replay_option_chain_state_source_acquisition_review",
            stage_id=OPTION_CHAIN_SOURCE_STAGE_ID,
            start_month=month,
            end_month=month,
            status="provider_acquisition_ready" if previews else "no_provider_skip_accepted",
            target_symbol=items[0].target_ref,
            request_count=len(previews),
            request_previews=previews,
            evidence_refs=("replay_dataset:feed_acquisition_plan",),
            reason=f"{len(previews)} replay decision option-chain source request(s) require ThetaData acquisition before replay retry.",
        )
        requests = manager_requests_from_review(review, storage_root=storage_root)
        write_option_chain_task_keys(requests)
        persist_manager_requests([{key: value for key, value in request.items() if not key.startswith("_")} for request in requests])
        request_ids_by_month[month] = [str(request["request_id"]) for request in requests]
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
    }


__all__ = [
    "REPLAY_OPTION_FEATURE_STAGE_ID",
    "ReplayOptionFeatureRequirement",
    "run_model_group_replay_option_features_if_required",
]

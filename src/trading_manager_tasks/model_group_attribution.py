"""Manager-owned replay review execution.

Replay review is the local, replay-derived review task that runs immediately
after model-group replay and before M06 ResidualEventGovernance attribution. It
converts replay failure/miss rows into durable review units and records the
ledger contract for later hierarchical component analysis. It is deliberately
not M06 event attribution because it does not consume point-in-time event
observations, event candidates, controls, co-events, or confounder evidence.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from .model_group_replay import CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES, DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")
REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE = "post_replay_review_receipt"
REPLAY_REVIEW_ROW_CONTRACT_TYPE = "post_replay_review_row"


def run_model_group_replay_review_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    max_review_rows: int | None = None,
    now_utc: datetime | None = None,
    force: bool = False,
) -> SchedulerDecision | None:
    """Run one replay review task when replay is complete."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    replay_receipt = _latest_replay_execution_receipt(dataset_root)
    if replay_receipt is None:
        return None
    if not _replay_receipt_uses_current_candidate_handoff(replay_receipt):
        return None
    expected_months = _expected_replay_months(dataset_root)
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "")
    ready_months = _ready_replay_months(dataset_root, replay_run_id=replay_run_id)
    if expected_months > 0 and len(ready_months) < expected_months:
        return None
    decision_rows_path = Path(str(replay_receipt.get("decision_rows_ref") or ""))
    if not decision_rows_path.exists():
        return None
    if not force and _latest_complete_replay_review_receipt(dataset_root, decision_rows_ref=str(decision_rows_path)) is not None:
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id = "post_replay_review_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_root = dataset_root / "post_replay_review_runs" / run_id
    review_rows_path = output_root / "replay_review_rows.jsonl"
    receipt_path = output_root / "post_replay_review_receipt.json"
    command = [
        python_executable,
        "scripts/tasks/run_model_group_replay_review.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]
    if max_review_rows is not None:
        command.extend(["--max-review-rows", str(max_review_rows)])

    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_replay_review_ready",
            reason="model-group replay is complete; replay review is ready",
            selected_work="model_group.replay_review",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "decision_rows_ref": str(decision_rows_path),
                "expected_replay_review_rows": "not_counted_during_readiness_probe",
            },
        )

    review_rows = tuple(_build_review_rows(decision_rows_path, max_rows=max_review_rows))
    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_replay_review:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.replay_review.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        output_root.mkdir(parents=True, exist_ok=True)
        _write_jsonl(review_rows_path, review_rows)
        receipt = {
            "contract_type": REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE,
            "status": "succeeded",
            "stage_id": "model_group.replay_review",
            "model_surface": "post_replay_review",
            "run_id": run_id,
            "contract_id": contract_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "decision_rows_ref": str(decision_rows_path),
            "replay_execution_run_id": replay_run_id,
            "replay_execution_receipt_ref": str(dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json")
            if replay_run_id
            else None,
            "review_rows_ref": str(review_rows_path),
            "expected_review_count": len(review_rows),
            "reviewed_failure_count": len(review_rows),
            "processed_review_count": len(review_rows),
            "review_sequence": ["eligibility_ledger", "decision_ledger", "outcome_ledger"],
            "review_scope": "post_replay_component_funnel_review",
            "cause_family_contract": ["data_insufficiency", "execution_connection_failure", "model_mechanism_defect"],
            "residual_event_governance_status": "not_performed",
            "event_evidence_consumed": False,
            "event_observation_count": 0,
            "event_candidate_count": 0,
            "control_analysis_performed": False,
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_replay_review_executed",
        reason="executed side-effect-free replay review over replay failures and missed opportunities",
        selected_work="model_group.replay_review",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "decision_rows_ref": str(decision_rows_path),
            "post_replay_review_receipt": str(receipt_path),
            "review_rows_ref": str(review_rows_path),
            "reviewed_failure_count": len(review_rows),
            "residual_event_governance_status": "not_performed",
        },
    )


def _decision(
    *,
    now: datetime,
    decision_status: str,
    reason_code: str,
    reason: str,
    selected_work: str,
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
        selected_work=selected_work,
        command=command,
        next_internal_stage="replay_review",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(
            month=None,
            selected_work=selected_work,
            next_internal_stage="replay_review",
        ),
    )


def _build_review_rows(decision_rows_path: Path, *, max_rows: int | None) -> Iterable[dict[str, Any]]:
    count = 0
    for index, row in enumerate(_load_jsonl_objects(decision_rows_path), start=1):
        if not _replay_row_needs_attribution(row):
            continue
        count += 1
        if max_rows is not None and count > max_rows:
            break
        yield _review_row(row, decision_index=index, review_index=count)


def _review_row(row: Mapping[str, Any], *, decision_index: int, review_index: int) -> dict[str, Any]:
    fill_status = str(row.get("fill_status") or "")
    decision_status = str(row.get("decision_status") or "")
    outcome_label = _int_field(row, "outcome_label")
    realized_return = _safe_float(row.get("realized_return"))
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    filled = fill_status == "simulated_filled" or decision_status in {"filled", "approved", "executed"}
    if filled:
        failure_type = "filled_negative_or_underperforming_outcome"
    else:
        failure_type = "rejected_positive_missed_opportunity"
    path_scope = _path_scope(row)
    candidate_set_scope = _candidate_set_scope(row)
    miss_attribution_layer = _miss_attribution_layer(row, filled=filled)
    miss_review_scope = _miss_review_scope(
        filled=filled,
        path_conditioning_policy=_path_conditioning_policy(row),
        candidate_set_scope=candidate_set_scope,
        miss_attribution_layer=miss_attribution_layer,
    )
    source_id = str(row.get("decision_id") or row.get("replay_decision_id") or f"decision_row_{decision_index}")
    decision_time = _decision_time(row)
    impact_profile = _impact_profile(row, failure_type=failure_type, decision_time=decision_time)
    return {
        "contract_type": REPLAY_REVIEW_ROW_CONTRACT_TYPE,
        "stage_id": "model_group.replay_review",
        "review_id": f"replay_review_{review_index:08d}",
        "source_decision_id": source_id,
        "source_decision_index": decision_index,
        "decision_time": decision_time,
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
        "review_status": "reviewed",
        "failure_type": failure_type,
        "cause_family": "model_mechanism_defect",
        "cause_family_basis": "replay row was visible and locally reviewable; event attribution is deferred to M06",
        "eligibility_ledger_status": "reviewable_from_replay_row",
        "decision_ledger_status": "reviewable_from_replay_row",
        "outcome_ledger_status": "reviewable_from_replay_row",
        "path_conditioning_policy": _path_conditioning_policy(row),
        "path_scope": path_scope,
        "candidate_set_scope": candidate_set_scope,
        "miss_attribution_layer": miss_attribution_layer,
        "miss_review_scope": miss_review_scope,
        "replay_month": _replay_month(row),
        "target_symbol": _target_symbol(row),
        "fill_status": fill_status,
        "decision_status": decision_status,
        "outcome_label": outcome_label,
        "realized_return": realized_return,
        "baseline_return": baseline_return,
        "attribution_basis": (
            "filled decision lost money or underperformed baseline"
            if filled
            else "path-conditioned non-taken decision missed a positive next outcome"
        ),
    }


def _impact_profile(row: Mapping[str, Any], *, failure_type: str, decision_time: str | None) -> dict[str, Any]:
    explicit_onset = _first_text(
        row,
        (
            "impact_exposure_time",
            "impact_onset_time",
            "impact_start_time",
            "adverse_move_start_time",
            "drawdown_start_time",
            "market_impact_start_time",
        ),
    )
    impact_exposure_time = explicit_onset or decision_time
    realized_return = _safe_float(row.get("realized_return")) or 0.0
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    raw_delta = realized_return - baseline_return
    magnitude = abs(raw_delta)
    denominator = _impact_normalization_denominator(row)
    normalized = magnitude / denominator if denominator and denominator > 0 else None
    if denominator and denominator > 0:
        severity_basis = "target_normalized_return_move"
    else:
        severity_basis = "raw_return_without_target_volatility_normalization"
    if failure_type == "rejected_positive_missed_opportunity":
        direction = "missed_upside"
    elif raw_delta < 0:
        direction = "adverse_downside"
    elif raw_delta > 0:
        direction = "relative_underperformance"
    else:
        direction = "outcome_failure_without_return_delta"
    return {
        "impact_exposure_time": impact_exposure_time,
        "impact_onset_time": impact_exposure_time,
        "impact_onset_basis": "source_impact_clock" if explicit_onset else "decision_time_fallback",
        "impact_scope_type": str(row.get("impact_scope_type") or row.get("scope_type") or "target").strip() or "target",
        "impact_direction": direction,
        "impact_raw_return_delta": raw_delta,
        "impact_magnitude_abs_return": magnitude,
        "impact_normalization_denominator": denominator,
        "impact_normalized_severity_score": normalized,
        "impact_severity_basis": severity_basis,
    }


def _impact_normalization_denominator(row: Mapping[str, Any]) -> float | None:
    for key in (
        "target_expected_move_abs_return",
        "expected_move_abs_return",
        "target_intraday_volatility",
        "target_realized_volatility",
        "realized_volatility",
        "atr_percent",
        "average_true_range_percent",
    ):
        value = _safe_float(row.get(key))
        if value and value > 0:
            return value
    return None


def _first_text(row: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return None


def _decision_time(row: Mapping[str, Any]) -> str | None:
    for key in ("decision_time", "timestamp", "decision_timestamp", "created_at", "created_at_utc"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return None


def _replay_month(row: Mapping[str, Any]) -> str | None:
    explicit_month = str(row.get("month") or row.get("replay_month") or "").strip()
    if explicit_month:
        return explicit_month
    timestamp = str(row.get("timestamp") or row.get("decision_timestamp") or "").strip()
    if len(timestamp) >= 7:
        return timestamp[:7]
    return None


def _target_symbol(row: Mapping[str, Any]) -> str | None:
    for key in ("target_symbol", "symbol", "target_ref"):
        value = str(row.get(key) or "").strip()
        if value:
            return value.split("-")[0].upper()
    instrument_ref = str(row.get("instrument_ref") or "").strip()
    if instrument_ref:
        return instrument_ref.split("-")[0].upper()
    return None


def _path_conditioning_policy(row: Mapping[str, Any]) -> str:
    value = _first_text(row, ("path_conditioning_policy", "replay_path_conditioning_policy"))
    return value or "upstream_selected_path_only"


def _path_scope(row: Mapping[str, Any]) -> str:
    value = _first_text(row, ("path_scope", "replay_path_scope"))
    if value:
        return value
    target = _target_symbol(row)
    if target:
        return f"selected_target:{target}"
    return "selected_path:unknown"


def _candidate_set_scope(row: Mapping[str, Any]) -> str:
    value = _first_text(row, ("candidate_set_scope", "replay_candidate_set_scope"))
    if value:
        return value
    if _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")):
        return "selected_target_selected_option_contract_path"
    instrument_scope = str(row.get("decision_instrument_scope") or "").strip()
    if instrument_scope == "listed_option_contract":
        return "selected_target_option_expression_candidates"
    if instrument_scope == "underlying_equity":
        return "selected_target_underlying_decision"
    return "selected_path_current_decision_set"


def _miss_attribution_layer(row: Mapping[str, Any], *, filled: bool) -> str:
    value = _first_text(row, ("miss_attribution_layer", "replay_miss_attribution_layer"))
    if value:
        return value
    if filled:
        return "taken_decision"
    if _first_text(row, ("selected_option_contract_ref", "selected_contract_ref")):
        return "model_05_option_expression"
    instrument_scope = str(row.get("decision_instrument_scope") or "").strip()
    if instrument_scope == "underlying_equity":
        return "model_04_unified_decision"
    return "current_decision_layer"


def _miss_review_scope(
    *,
    filled: bool,
    path_conditioning_policy: str,
    candidate_set_scope: str,
    miss_attribution_layer: str,
) -> str:
    if filled:
        return "taken_decision"
    if path_conditioning_policy in {"global_hindsight_oracle", "unconditioned_global_universe", "best_path_hindsight"}:
        return "not_path_conditioned"
    if candidate_set_scope.startswith("global_") or miss_attribution_layer in {"global_hindsight_oracle", "best_path_hindsight"}:
        return "not_path_conditioned"
    return "path_conditioned_current_scope"


def _replay_row_needs_attribution(row: Mapping[str, Any]) -> bool:
    fill_status = str(row.get("fill_status") or "")
    decision_status = str(row.get("decision_status") or "")
    outcome_label = _int_field(row, "outcome_label")
    realized_return = _safe_float(row.get("realized_return"))
    baseline_return = _safe_float(row.get("baseline_return")) or 0.0
    filled = fill_status == "simulated_filled" or decision_status in {"filled", "approved", "executed"}
    if filled:
        if outcome_label == 0:
            return True
        if realized_return is not None and realized_return <= baseline_return:
            return True
        return False
    if outcome_label != 1:
        return False
    return (
        _miss_review_scope(
            filled=False,
            path_conditioning_policy=_path_conditioning_policy(row),
            candidate_set_scope=_candidate_set_scope(row),
            miss_attribution_layer=_miss_attribution_layer(row, filled=False),
        )
        == "path_conditioned_current_scope"
    )


def _latest_replay_execution_receipt(dataset_root: Path) -> dict[str, Any] | None:
    replay_root = dataset_root / "replay_execution_runs"
    if not replay_root.exists():
        return None
    candidates: list[tuple[str, Path, Mapping[str, Any]]] = []
    for receipt_path in sorted(replay_root.glob("*/replay_execution_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        if "current_deterministic_crypto_policy" in str(receipt.get("candidate_model_ref") or ""):
            continue
        if not _replay_receipt_full_completion_scope(receipt):
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt.get("generated_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt_path, receipt))
    if not candidates:
        return None
    _created, _receipt_path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return dict(receipt)


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
    return (
        str(receipt.get("candidate_handoff_status") or "") == "available"
        and str(receipt.get("candidate_handoff_source") or "") in CURRENT_REPLAY_CANDIDATE_UNIVERSE_SOURCES
    )


def _replay_receipt_full_completion_scope(receipt: Mapping[str, Any]) -> bool:
    completion_scope = str(receipt.get("replay_completion_scope") or "").strip()
    if completion_scope:
        return completion_scope == "full_candidate_universe" and receipt.get("max_decision_rows") is None
    return receipt.get("max_decision_rows") is None


def _latest_complete_replay_review_receipt(dataset_root: Path, *, decision_rows_ref: str) -> dict[str, Any] | None:
    review_root = dataset_root / "post_replay_review_runs"
    if not review_root.exists():
        return None
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    for receipt_path in sorted(review_root.glob("*/post_replay_review_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        status = str(receipt.get("status") or receipt.get("attribution_status") or "")
        if status not in {"succeeded", "complete", "completed"}:
            continue
        contract_type = str(receipt.get("contract_type") or "")
        if contract_type != REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE:
            continue
        if str(receipt.get("decision_rows_ref") or "") != decision_rows_ref:
            continue
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt))
    if not candidates:
        return None
    _created, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return dict(receipt)


def _expected_replay_months(dataset_root: Path) -> int:
    months = _unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month")
    if months:
        return len(months)
    rows = _csv_rows(dataset_root / "replay_window_manifest.csv")
    if not rows:
        return 60
    try:
        start = datetime.fromisoformat(str(rows[0].get("start_date"))).date()
        end = datetime.fromisoformat(str(rows[0].get("end_date"))).date()
    except (TypeError, ValueError):
        return 60
    return max(1, (end.year - start.year) * 12 + end.month - start.month)


def _ready_replay_months(dataset_root: Path, *, replay_run_id: str) -> set[str]:
    ready: set[str] = set()
    paths = sorted((dataset_root / "replay_runs").glob("*.jsonl")) + [dataset_root / "replay_progress.jsonl"]
    for path in paths:
        if not path.exists():
            continue
        for row in _load_jsonl_objects(path):
            if replay_run_id and str(row.get("replay_execution_run_id") or "") != replay_run_id:
                continue
            status = str(row.get("status") or row.get("replay_status") or "").lower()
            month = str(row.get("month") or row.get("replay_month") or "").strip()
            if month and status in {"succeeded", "completed", "complete"}:
                ready.add(month)
    return ready


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
    return {str(row.get(field) or "").strip() for row in _csv_rows(path) if str(row.get(field) or "").strip()}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


def _int_field(row: Mapping[str, Any], key: str) -> int | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "REPLAY_REVIEW_RECEIPT_CONTRACT_TYPE",
    "REPLAY_REVIEW_ROW_CONTRACT_TYPE",
    "run_model_group_replay_review_if_ready",
]

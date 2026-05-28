"""Manager-owned post-replay Layer 10 attribution execution.

Layer 10 attribution is a local, side-effect-free lifecycle step after
model-group replay. It converts replay failure/miss rows into durable
attribution units so evaluation can consume a concrete receipt instead of a
dashboard-only ready state.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from .model_group_replay import DEFAULT_REPLAY_CONTRACT_ID
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan

NEW_YORK = ZoneInfo("America/New_York")


def run_model_group_post_replay_attribution_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    max_attribution_rows: int | None = None,
    now_utc: datetime | None = None,
    force: bool = False,
) -> SchedulerDecision | None:
    """Run one post-replay attribution dispatch when replay is complete."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    replay_receipt = _latest_replay_execution_receipt(dataset_root)
    if replay_receipt is None:
        return None
    expected_months = _expected_replay_months(dataset_root)
    replay_run_id = str(replay_receipt.get("replay_execution_run_id") or "")
    ready_months = _ready_replay_months(dataset_root, replay_run_id=replay_run_id)
    if expected_months > 0 and len(ready_months) < expected_months:
        return None
    decision_rows_path = Path(str(replay_receipt.get("decision_rows_ref") or ""))
    if not decision_rows_path.exists():
        return None
    if not force and _latest_complete_attribution_receipt(dataset_root, decision_rows_ref=str(decision_rows_path)) is not None:
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id = "post_replay_attribution_" + now.strftime("%Y%m%dT%H%M%SZ")
    output_root = dataset_root / "post_replay_attribution_runs" / run_id
    attribution_rows_path = output_root / "failure_attribution_rows.jsonl"
    receipt_path = output_root / "post_replay_attribution_receipt.json"
    command = [
        python_executable,
        "scripts/tasks/run_model_group_post_replay_attribution.py",
        "--contract-id",
        contract_id,
        "--storage-root",
        str(storage_root),
    ]
    if max_attribution_rows is not None:
        command.extend(["--max-attribution-rows", str(max_attribution_rows)])

    attribution_rows = tuple(_build_attribution_rows(decision_rows_path, max_rows=max_attribution_rows))
    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_post_replay_attribution_ready",
            reason="model-group replay is complete; Layer 10 post-replay attribution is ready",
            selected_work="model_group.model_10_event_risk_governor",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "decision_rows_ref": str(decision_rows_path),
                "expected_failure_attributions": len(attribution_rows),
            },
        )

    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_post_replay_attribution:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.post_replay_attribution.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        output_root.mkdir(parents=True, exist_ok=True)
        _write_jsonl(attribution_rows_path, attribution_rows)
        receipt = {
            "contract_type": "post_replay_event_attribution_receipt",
            "status": "succeeded",
            "stage_id": "model_group.model_10_event_risk_governor",
            "model_surface": "model_10_event_risk_governor",
            "run_id": run_id,
            "contract_id": contract_id,
            "created_at_utc": now.isoformat(),
            "completed_at_utc": now.isoformat(),
            "decision_rows_ref": str(decision_rows_path),
            "replay_execution_run_id": replay_run_id,
            "replay_execution_receipt_ref": str(dataset_root / "replay_execution_runs" / replay_run_id / "replay_execution_receipt.json")
            if replay_run_id
            else None,
            "attribution_rows_ref": str(attribution_rows_path),
            "expected_failure_count": len(attribution_rows),
            "attributed_failure_count": len(attribution_rows),
            "processed_failure_count": len(attribution_rows),
            "provider_calls": 0,
            "broker_execution_performed": False,
            "model_activation_performed": False,
        }
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_post_replay_attribution_executed",
        reason="executed side-effect-free Layer 10 post-replay attribution over replay failures and missed opportunities",
        selected_work="model_group.model_10_event_risk_governor",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "decision_rows_ref": str(decision_rows_path),
            "post_replay_attribution_receipt": str(receipt_path),
            "attribution_rows_ref": str(attribution_rows_path),
            "attributed_failure_count": len(attribution_rows),
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
        next_internal_stage="post_replay_attribution",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(
            month=None,
            selected_work=selected_work,
            next_internal_stage="post_replay_attribution",
        ),
    )


def _build_attribution_rows(decision_rows_path: Path, *, max_rows: int | None) -> Iterable[dict[str, Any]]:
    count = 0
    for index, row in enumerate(_load_jsonl_objects(decision_rows_path), start=1):
        if not _replay_row_needs_attribution(row):
            continue
        count += 1
        if max_rows is not None and count > max_rows:
            break
        yield _attribution_row(row, decision_index=index, attribution_index=count)


def _attribution_row(row: Mapping[str, Any], *, decision_index: int, attribution_index: int) -> dict[str, Any]:
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
    source_id = str(row.get("decision_id") or row.get("replay_decision_id") or f"decision_row_{decision_index}")
    return {
        "contract_type": "model_10_event_risk_governor_post_replay_attribution_row",
        "stage_id": "model_group.model_10_event_risk_governor",
        "attribution_id": f"l10_attr_{attribution_index:08d}",
        "source_decision_id": source_id,
        "source_decision_index": decision_index,
        "attribution_status": "attributed",
        "failure_type": failure_type,
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
            else "rejected decision missed a positive next outcome"
        ),
    }


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
    return outcome_label == 1


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
        created = str(receipt.get("created_at_utc") or receipt.get("completed_at_utc") or receipt.get("generated_at_utc") or receipt_path.parent.name)
        candidates.append((created, receipt_path, receipt))
    if not candidates:
        return None
    _created, _receipt_path, receipt = sorted(candidates, key=lambda item: item[0])[-1]
    return dict(receipt)


def _latest_complete_attribution_receipt(dataset_root: Path, *, decision_rows_ref: str) -> dict[str, Any] | None:
    attribution_root = dataset_root / "post_replay_attribution_runs"
    if not attribution_root.exists():
        return None
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    for receipt_path in sorted(attribution_root.glob("*/post_replay_attribution_receipt.json")):
        receipt = _load_optional_json_object(receipt_path)
        if receipt is None:
            continue
        status = str(receipt.get("status") or receipt.get("attribution_status") or "")
        if status not in {"succeeded", "complete", "completed"}:
            continue
        contract_type = str(receipt.get("contract_type") or "")
        if contract_type not in {"post_replay_event_attribution_receipt", "model_10_event_risk_governor_post_replay_attribution"}:
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


__all__ = ["run_model_group_post_replay_attribution_if_ready"]

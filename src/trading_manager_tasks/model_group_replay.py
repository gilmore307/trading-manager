"""Manager-owned dispatch for model-group replay execution.

The replay itself lives in ``trading-evaluation``. Manager owns admission:
only a completed model-training fold and a frozen replay dataset may trigger
the side-effect-free evaluation runner.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan
from .storage_paths import projects_root
from .model_training_workflow import base_stack_model_generation_splits_complete

DEFAULT_REPLAY_CONTRACT_ID = "promotion_replay_candidate_policy"
DEFAULT_EVALUATION_REPO_ROOT = projects_root() / "trading-evaluation"
DEFAULT_EXECUTION_REPO_ROOT = projects_root() / "trading-execution"
DEFAULT_EVALUATION_RUNNER_PATH = DEFAULT_EVALUATION_REPO_ROOT / "scripts" / "evaluation" / "run_replay_execution.py"
NEW_YORK = ZoneInfo("America/New_York")


def run_model_group_replay_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str = sys.executable,
    evaluation_repo_root: Path = DEFAULT_EVALUATION_REPO_ROOT,
    execution_repo_root: Path = DEFAULT_EXECUTION_REPO_ROOT,
    runner_path: Path = DEFAULT_EVALUATION_RUNNER_PATH,
    selected_target_symbol: str | None = None,
    max_decision_rows: int | None = None,
    now_utc: datetime | None = None,
) -> SchedulerDecision | None:
    """Run one model-group replay dispatch when the accepted prerequisites hold."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    manifest_path = dataset_root / "dataset_manifest.json"
    freeze_receipt_path = dataset_root / "replay_freeze_receipt.json"
    if not dataset_root.exists() or not manifest_path.exists() or not freeze_receipt_path.exists():
        return None

    manifest = _load_json_object(manifest_path)
    freeze_receipt = _load_json_object(freeze_receipt_path)
    if not _dataset_is_frozen_and_complete(manifest, freeze_receipt):
        return None

    training_fold = _completed_training_fold(storage_root=storage_root, selected_target_symbol=selected_target_symbol)
    if training_fold is None:
        return None

    expected_months = _expected_replay_months(dataset_root)
    ready_months = _ready_replay_months(dataset_root)
    if expected_months > 0 and len(ready_months) >= expected_months:
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id = "model_group_replay_" + now.strftime("%Y%m%dT%H%M%SZ")
    progress_path = dataset_root / "replay_progress.jsonl"
    command = [
        python_executable,
        str(runner_path),
        "--dataset-root",
        str(dataset_root),
        "--run-id",
        run_id,
        "--progress-path",
        str(progress_path),
    ]
    if max_decision_rows is not None:
        command.extend(["--max-decision-rows", str(max_decision_rows)])

    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_replay_ready",
            reason="model-group replay is ready; rerun with replay execution enabled to dispatch evaluation runner",
            selected_work="model_group.replay",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "expected_replay_months": expected_months,
                "ready_replay_months": len(ready_months),
            },
        )

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(evaluation_repo_root / "src"),
            str(execution_repo_root / "src"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)

    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_replay:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        completed = subprocess.run(
            command,
            cwd=evaluation_repo_root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    receipt = json.loads(completed.stdout)
    refreshed_ready_months = _ready_replay_months(dataset_root)
    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_replay_executed",
        reason="executed side-effect-free model-group replay over frozen local dataset",
        selected_work="model_group.replay",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "training_fold": training_fold,
            "expected_replay_months": expected_months,
            "ready_replay_months_before": len(ready_months),
            "ready_replay_months_after": len(refreshed_ready_months),
            "replay_execution_receipt": receipt,
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
        next_internal_stage="model_group_replay",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(
            month=None,
            selected_work=selected_work,
            next_internal_stage="model_group_replay",
        ),
    )


def _replay_dataset_root(storage_root: Path, contract_id: str) -> Path:
    return storage_root.parent / "05_replay_datasets" / contract_id


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _dataset_is_frozen_and_complete(manifest: Mapping[str, Any], freeze_receipt: Mapping[str, Any]) -> bool:
    validation = freeze_receipt.get("validation")
    return (
        manifest.get("freeze_status") == "frozen"
        and int(manifest.get("missing_feed_acquisition_count") or 0) == 0
        and freeze_receipt.get("freeze_status") == "frozen"
        and isinstance(validation, Mapping)
        and validation.get("validation_status") == "passed"
    )


def _completed_training_fold(*, storage_root: Path, selected_target_symbol: str | None) -> dict[str, Any] | None:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return None
    selected = str(selected_target_symbol or "").strip().lower()
    candidates: list[dict[str, Any]] = []
    for path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
        try:
            payload = _load_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if selected and f"_{selected}_" not in path.stem.lower():
            continue
        stages = payload.get("stages")
        if not isinstance(stages, list) or not stages:
            continue
        if not base_stack_model_generation_splits_complete(stages):
            continue
        if not all(str(stage.get("status") or "").lower() in {"succeeded", "not_applicable"} for stage in stages if isinstance(stage, Mapping)):
            continue
        start_month = str(payload.get("start_month") or "")
        end_month = str(payload.get("end_month") or "")
        if not start_month or not end_month:
            continue
        candidates.append(
            {
                "fold_id": f"fold_{start_month}_{end_month}",
                "fold_label": _fold_label(start_month, end_month),
                "start_month": start_month,
                "end_month": end_month,
                "state_path": str(path),
            }
        )
    return sorted(candidates, key=lambda row: (row["start_month"], row["end_month"], row["state_path"]))[0] if candidates else None


def _fold_label(start_month: str, end_month: str) -> str:
    try:
        start_year, start_month_number = (int(part) for part in start_month.split("-", 1))
        end_year, end_month_number = (int(part) for part in end_month.split("-", 1))
    except ValueError:
        return f"{start_month}..{end_month}"
    if start_year != end_year or (end_month_number - start_month_number) != 5:
        return f"{start_month}..{end_month}"
    fold_number = ((start_month_number - 1) // 6) + 1
    return f"{start_year:04d}-fold{fold_number}"


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


def _ready_replay_months(dataset_root: Path) -> set[str]:
    ready: set[str] = set()
    paths = sorted((dataset_root / "replay_runs").glob("*.jsonl")) + [dataset_root / "replay_progress.jsonl"]
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                status = str(row.get("status") or row.get("replay_status") or "").lower()
                month = str(row.get("month") or row.get("replay_month") or "").strip()
                if month and status in {"succeeded", "completed", "complete"}:
                    ready.add(month)
    return ready


def _unique_csv_values(path: Path, field: str) -> set[str]:
    return {str(row.get(field) or "").strip() for row in _csv_rows(path) if str(row.get(field) or "").strip()}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


__all__ = [
    "DEFAULT_REPLAY_CONTRACT_ID",
    "run_model_group_replay_if_ready",
]

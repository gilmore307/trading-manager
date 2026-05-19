"""Fold-scoped cleanup gate and logical-backup plan helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .model_training_workflow import BASE_STACK_LAYER_COUNT
from .scheduler_daemon import MODEL_WORKER_STAGE_TYPES, model_worker_fold_state_path

FOLD_CLEANUP_PLAN_CONTRACT = "manager_fold_cleanup_plan"
FOLD_SQL_LOGICAL_BACKUP_CONTRACT = "manager_fold_sql_logical_backup_plan"
COMPLETE_STATUSES = {"succeeded", "not_applicable"}


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True)
class FoldCleanupPlan:
    """Manager gate proving a whole fold can enter storage cleanup."""

    contract_type: str
    plan_id: str
    fold_id: str
    start_month: str
    end_month: str
    state_path: str
    generated_at_utc: str
    cleanup_granularity: str
    cleanup_ready: bool
    cleanup_status: str
    blocked_reasons: tuple[str, ...]
    required_stage_count: int
    completed_stage_count: int
    required_model_stage_count: int
    completed_model_stage_count: int
    layer_count: int
    completed_model_layers: tuple[int, ...]
    open_stage_ids: tuple[str, ...]
    failed_stage_ids: tuple[str, ...]
    logical_backup_required: bool
    logical_backup_plan: dict[str, Any]
    cleanup_action_status: str
    storage_lifecycle_mutation_performed: bool
    database_mutation_performed: bool
    source_delete_performed: bool

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        for key in ("blocked_reasons", "completed_model_layers", "open_stage_ids", "failed_stage_ids"):
            row[key] = list(row[key])
        return row


def _stage_rows(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    stages = payload.get("stages")
    if not isinstance(stages, list) or not stages:
        raise TaskSystemError("fold state must contain non-empty stages")
    rows: list[dict[str, Any]] = []
    for stage in stages:
        if not isinstance(stage, Mapping):
            raise TaskSystemError("fold state stages must be objects")
        rows.append(dict(stage))
    return rows


def _fold_id(start_month: str, end_month: str) -> str:
    return f"fold_{start_month}_{end_month}"


def _backup_relative_path(*, fold_id: str, generated_at_utc: str, database_label: str) -> str:
    safe_time = generated_at_utc.replace(":", "").replace("-", "").replace("+00:00", "Z")
    safe_label = "".join(char.lower() if char.isalnum() else "_" for char in database_label).strip("_") or "database"
    return f"storage/sql_backups/folds/{fold_id}/{safe_time}/{safe_label}.dump"


def _logical_backup_plan(
    *,
    fold_id: str,
    start_month: str,
    end_month: str,
    generated_at_utc: str,
    database_label: str,
) -> dict[str, Any]:
    output_path = _backup_relative_path(fold_id=fold_id, generated_at_utc=generated_at_utc, database_label=database_label)
    return {
        "contract_type": FOLD_SQL_LOGICAL_BACKUP_CONTRACT,
        "backup_plan_id": _stable_id("foldsqlbackup", fold_id, generated_at_utc, database_label),
        "backup_scope": "fold_cleanup_precondition",
        "backup_mode": "logical_pg_dump_custom",
        "fold_id": fold_id,
        "start_month": start_month,
        "end_month": end_month,
        "database_label": database_label,
        "output_path": output_path,
        "backup_command": [
            "pg_dump",
            "-Fc",
            "--no-owner",
            "--no-acl",
            "--file",
            output_path,
            "$DATABASE_URL",
        ],
        "globals_backup_command": [
            "pg_dumpall",
            "--globals-only",
            "--file",
            output_path.removesuffix(".dump") + ".globals.sql",
        ],
        "restore_smoke_required": True,
        "checksum_required": True,
        "backup_must_complete_before_cleanup": True,
        "database_mutation_performed": False,
    }


def build_fold_cleanup_plan(
    *,
    state_path: Path,
    database_label: str = "trading_database",
    generated_at_utc: str | None = None,
) -> FoldCleanupPlan:
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TaskSystemError("fold state must be a JSON object")
    start_month = str(payload.get("start_month") or "").strip()
    end_month = str(payload.get("end_month") or "").strip()
    if not start_month or not end_month:
        raise TaskSystemError("fold state must include start_month and end_month")
    fold_id = _fold_id(start_month, end_month)
    generated = generated_at_utc or _now_utc()
    stages = _stage_rows(payload)
    model_stages = [stage for stage in stages if str(stage.get("stage_type") or "") in MODEL_WORKER_STAGE_TYPES]
    open_stages = [str(stage.get("stage_id") or "") for stage in stages if str(stage.get("status") or "") not in COMPLETE_STATUSES]
    failed_stages = [str(stage.get("stage_id") or "") for stage in stages if str(stage.get("status") or "") == "failed"]
    completed_model = [stage for stage in model_stages if str(stage.get("status") or "") in COMPLETE_STATUSES]
    model_layers_by_stage_type: dict[int, set[str]] = {}
    for stage in model_stages:
        layer = int(stage.get("layer") or 0)
        model_layers_by_stage_type.setdefault(layer, set()).add(str(stage.get("stage_type") or ""))
    expected_stage_types = set(MODEL_WORKER_STAGE_TYPES)
    expected_layer_numbers = tuple(range(1, BASE_STACK_LAYER_COUNT + 1))
    complete_layers = tuple(
        sorted(
            layer
            for layer, stage_types in model_layers_by_stage_type.items()
            if stage_types >= expected_stage_types
            and all(
                str(stage.get("status") or "") in COMPLETE_STATUSES
                for stage in model_stages
                if int(stage.get("layer") or 0) == layer
            )
        )
    )
    blocked: list[str] = []
    if open_stages:
        blocked.append("fold_has_open_or_failed_stages")
    if failed_stages:
        blocked.append("fold_has_failed_stages")
    if complete_layers != expected_layer_numbers:
        blocked.append("not_all_model_layers_completed")
    cleanup_ready = not blocked
    backup_plan = _logical_backup_plan(
        fold_id=fold_id,
        start_month=start_month,
        end_month=end_month,
        generated_at_utc=generated,
        database_label=database_label,
    )
    return FoldCleanupPlan(
        contract_type=FOLD_CLEANUP_PLAN_CONTRACT,
        plan_id=_stable_id("foldcleanup", state_path, fold_id, generated, database_label),
        fold_id=fold_id,
        start_month=start_month,
        end_month=end_month,
        state_path=str(state_path),
        generated_at_utc=generated,
        cleanup_granularity="fold_all_models_all_tasks_once",
        cleanup_ready=cleanup_ready,
        cleanup_status="ready_for_logical_backup" if cleanup_ready else "blocked",
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        required_stage_count=len(stages),
        completed_stage_count=len(stages) - len(open_stages),
        required_model_stage_count=BASE_STACK_LAYER_COUNT * len(expected_stage_types),
        completed_model_stage_count=len(completed_model),
        layer_count=BASE_STACK_LAYER_COUNT,
        completed_model_layers=complete_layers,
        open_stage_ids=tuple(stage_id for stage_id in open_stages if stage_id),
        failed_stage_ids=tuple(stage_id for stage_id in failed_stages if stage_id),
        logical_backup_required=True,
        logical_backup_plan=backup_plan,
        cleanup_action_status="not_performed_plan_only",
        storage_lifecycle_mutation_performed=False,
        database_mutation_performed=False,
        source_delete_performed=False,
    )


def build_fold_cleanup_plan_for_months(
    *,
    start_month: str,
    end_month: str,
    storage_root: Path,
    database_label: str = "trading_database",
    generated_at_utc: str | None = None,
) -> FoldCleanupPlan:
    return build_fold_cleanup_plan(
        state_path=model_worker_fold_state_path(start_month, end_month, root=storage_root / "runtime"),
        database_label=database_label,
        generated_at_utc=generated_at_utc,
    )


def write_fold_cleanup_plan(plan: FoldCleanupPlan, *, output: TextIO) -> None:
    json.dump(plan.to_dict(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan one fold-scoped cleanup gate and required SQL logical backup.")
    parser.add_argument("--state-path", type=Path, help="Fold state path. Overrides --start-month/--end-month.")
    parser.add_argument("--start-month")
    parser.add_argument("--end-month")
    parser.add_argument("--storage-root", type=Path, default=Path("storage"))
    parser.add_argument("--database-label", default="trading_database")
    args = parser.parse_args(argv)
    if args.state_path:
        plan = build_fold_cleanup_plan(state_path=args.state_path, database_label=args.database_label)
    else:
        if not args.start_month or not args.end_month:
            raise SystemExit("--state-path or both --start-month and --end-month are required")
        plan = build_fold_cleanup_plan_for_months(
            start_month=args.start_month,
            end_month=args.end_month,
            storage_root=args.storage_root,
            database_label=args.database_label,
        )
    write_fold_cleanup_plan(plan, output=sys.stdout)
    return 0


__all__ = [
    "FOLD_CLEANUP_PLAN_CONTRACT",
    "FOLD_SQL_LOGICAL_BACKUP_CONTRACT",
    "FoldCleanupPlan",
    "build_fold_cleanup_plan",
    "build_fold_cleanup_plan_for_months",
    "write_fold_cleanup_plan",
]

"""Controlled model-group rerun planning and state reset."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal, TextIO

from .model_training_state import (
    StageProgress,
    WorkflowState,
    load_workflow_state,
    refresh_workflow_state,
    write_workflow_state,
)
from .model_training_workflow import build_model_training_workflow_plan
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler_daemon import model_worker_fold_state_path

RerunStage = Literal[
    "data_acquisition",
    "feature_generation",
    "model_training",
    "model_generation",
    "model_evaluation",
    "replay_execution",
    "post_replay_attribution",
    "fold_settlement",
    "promotion_review",
    "maintenance",
    "read_model_refresh",
]

PROTECTED_SOURCE_REFS = (
    "storage://01_source_data/monthly_backfill/alpaca_bars/",
    "storage://01_source_data/monthly_backfill/trading_economics_calendar_web/",
)
PROTECTED_SOURCE_POLICIES = {
    "storage://01_source_data/monthly_backfill/alpaca_bars/": (
        "source data is protected for this rerun; reusable partitions remain controlled upstream evidence"
    ),
    "storage://01_source_data/monthly_backfill/trading_economics_calendar_web/": (
        "Trading Economics calendar source data is append-only protected; daily tracked changes belong in routine maintenance commits"
    ),
}


@dataclass(frozen=True)
class ModelGroupRerunResult:
    """Summary for a dry-run or executed model-group rerun reset."""

    contract_type: str
    plan_id: str
    rerun_id: str
    dry_run: bool
    state_path: str
    changed_stage_count: int
    preserved_stage_count: int
    cutpoint_stage_id: str
    source_data_delete_required: bool
    write_performed: bool
    reset_receipt_path: str | None
    reset_receipt_written: bool
    plan: dict[str, Any]

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "plan_id": self.plan_id,
            "rerun_id": self.rerun_id,
            "dry_run": self.dry_run,
            "state_path": self.state_path,
            "changed_stage_count": self.changed_stage_count,
            "preserved_stage_count": self.preserved_stage_count,
            "cutpoint_stage_id": self.cutpoint_stage_id,
            "source_data_delete_required": self.source_data_delete_required,
            "write_performed": self.write_performed,
            "reset_receipt_path": self.reset_receipt_path,
            "reset_receipt_written": self.reset_receipt_written,
            "plan": self.plan,
        }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _stage_ref(state_path: Path, stage_id: str) -> str:
    return f"storage://02_control_plane/runtime/{state_path.name}#{stage_id}"


def _artifact_class_for_stage(stage: StageProgress) -> str:
    if stage.stage_type == "data_acquisition":
        return "runtime_state"
    if stage.stage_type == "feature_generation":
        return "feature_data"
    if stage.stage_type == "model_training":
        return "model_artifact"
    if stage.stage_type == "model_generation":
        return "model_output"
    if stage.stage_type == "model_evaluation":
        return "evaluation_artifact"
    if stage.stage_type == "promotion_review":
        return "promotion_artifact"
    return "runtime_state"


def _safe_timestamp_for_path(value: str) -> str:
    return value.replace(":", "").replace("+00:00", "Z")


def _component_root_for_manager_storage(storage_root: Path, component_dir: str) -> Path:
    if storage_root.name == "02_control_plane":
        return storage_root.parent / component_dir
    return storage_root / component_dir


def _controlled_artifact_roots(storage_root: Path) -> list[dict[str, str]]:
    data_root = _component_root_for_manager_storage(storage_root, "01_source_data")
    model_root = _component_root_for_manager_storage(storage_root, "03_model_artifacts")
    replay_root = _component_root_for_manager_storage(storage_root, "05_replay_datasets")
    dashboard_root = _component_root_for_manager_storage(storage_root, "06_dashboard_cache")
    return [
        {
            "root_class": "workflow_state",
            "path": str(storage_root / "runtime"),
            "policy": "manager-owned runtime state; rerun may invalidate bounded stage progress",
        },
        {
            "root_class": "stage_receipts",
            "path": str(storage_root / "runtime" / "model_training_stage_receipts"),
            "policy": "manager-owned stage execution receipts; append-only evidence for scheduler progress",
        },
        {
            "root_class": "stage_logs",
            "path": str(storage_root / "runtime" / "model_training_stage_logs"),
            "policy": "manager-owned execution logs; lifecycle cleanup requires explicit storage policy",
        },
        {
            "root_class": "provider_task_keys",
            "path": str(storage_root / "runtime" / "provider_task_keys"),
            "policy": "runtime provider dispatch bookkeeping; empty residual directories are housekeeping candidates only",
        },
        {
            "root_class": "rerun_reset_receipts",
            "path": str(storage_root / "runtime" / "model_group_rerun_resets"),
            "policy": "durable reset receipts for state invalidation and scheduler reentry evidence",
        },
        {
            "root_class": "protected_source_data",
            "path": str(data_root / "monthly_backfill" / "alpaca_bars"),
            "policy": "protected reusable source data; rerun executor must not delete",
        },
        {
            "root_class": "protected_source_data",
            "path": str(data_root / "monthly_backfill" / "trading_economics_calendar_web"),
            "policy": "append-only protected TE source data; changed/new files are normal maintenance commit inputs",
        },
        {
            "root_class": "model_artifacts",
            "path": str(model_root / "runtime"),
            "policy": "generated model artifacts; stale artifacts require bounded invalidation evidence",
        },
        {
            "root_class": "replay_datasets",
            "path": str(replay_root),
            "policy": "generated replay inputs/outputs; lifecycle cleanup requires explicit storage policy",
        },
        {
            "root_class": "dashboard_cache",
            "path": str(dashboard_root),
            "policy": "generated dashboard/read-model cache; rebuildable from accepted sources and receipts",
        },
    ]


def _empty_provider_task_key_dirs(storage_root: Path) -> list[str]:
    root = storage_root / "runtime" / "provider_task_keys"
    if not root.exists():
        return []
    empty_dirs: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_dir()):
        try:
            next(path.iterdir())
        except StopIteration:
            empty_dirs.append(str(path.relative_to(root)))
    return empty_dirs


def _retained_set(storage_root: Path) -> list[dict[str, Any]]:
    retained: list[dict[str, Any]] = []
    for ref in PROTECTED_SOURCE_REFS:
        retained.append(
            {
                "ref": ref,
                "retain_reason": PROTECTED_SOURCE_POLICIES[ref],
                "control_policy": "preserve during rerun; include tracked changes in routine repository maintenance commits",
            }
        )
    empty_task_key_dirs = _empty_provider_task_key_dirs(storage_root)
    if empty_task_key_dirs:
        retained.append(
            {
                "ref": "storage://02_control_plane/runtime/provider_task_keys/",
                "retain_reason": "no task_key.json files remain; empty directories are harmless runtime residue until housekeeping runs",
                "control_policy": "do not treat as rerun blocker; clean only through bounded housekeeping/lifecycle policy",
                "empty_dir_count": len(empty_task_key_dirs),
                "empty_dir_examples": empty_task_key_dirs[:10],
            }
        )
    return retained


def _storage_lifecycle_request(
    *,
    rerun_id: str,
    plan_id: str,
    delete_set: list[dict[str, Any]],
    protected_set: list[dict[str, str]],
    retained_set: list[dict[str, Any]],
    controlled_artifact_roots: list[dict[str, str]],
    reason: str,
) -> dict[str, Any]:
    return {
        "contract_type": "storage_lifecycle_request",
        "request_id": f"storage_lifecycle_request_{rerun_id}",
        "request_origin": "model_group_rerun_plan",
        "origin_ref": plan_id,
        "origin_rerun_id": rerun_id,
        "requested_action": "classify_rerun_invalidated_artifacts",
        "reason": reason,
        "candidate_refs": [str(row["ref"]) for row in delete_set],
        "protected_refs": [str(row["ref"]) for row in protected_set],
        "retained_refs": [str(row["ref"]) for row in retained_set],
        "controlled_artifact_roots": controlled_artifact_roots,
        "requires_storage_lifecycle_review": True,
        "requires_artifact_index": True,
        "requires_protected_set_clearance": True,
        "requires_quarantine_recheck_before_delete": True,
        "mutation_allowed_by_request": False,
        "broker_execution_performed": False,
        "model_activation_performed": False,
        "storage_lifecycle_mutation_performed": False,
    }


def _stage_order_index(stages: Iterable[StageProgress], *, layer_id: int, stage_type: str) -> int:
    for index, stage in enumerate(stages):
        if stage.layer == layer_id and stage.stage_type == stage_type:
            return index
    raise ValueError(f"cutpoint stage not found: layer={layer_id} stage={stage_type}")


def _reset_stage(stage: StageProgress, *, now: str, reason: str) -> StageProgress:
    return StageProgress(
        stage_id=stage.stage_id,
        layer=stage.layer,
        layer_key=stage.layer_key,
        stage_type=stage.stage_type,
        status="pending",
        command=list(stage.command),
        blockers=tuple(stage.blockers),
        dataset_unit=stage.dataset_unit,
        dataset_split=dict(stage.dataset_split) if stage.dataset_split is not None else None,
        approval_gate_required=stage.approval_gate_required,
        approval_status=None,
        artifact_refs=(),
        receipt_refs=(),
        last_reason=reason,
        updated_utc=now,
        created_at_utc=stage.created_at_utc or now,
        started_at_utc=None,
        ended_at_utc=None,
        status_updated_at_utc=now,
    )


def build_model_group_rerun_plan(
    *,
    state: WorkflowState,
    state_path: Path,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    layer_id: int,
    stage: RerunStage,
    reason: str,
    target_symbols: tuple[str, ...],
    rerun_id: str | None = None,
    plan_id: str | None = None,
    source_data_delete_required: bool = False,
    source_data_delete_scope_refs: tuple[str, ...] = (),
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build the current rerun-plan contract from the affected state."""

    if source_data_delete_required:
        raise ValueError("source data deletion requires a separate storage lifecycle review path")
    created = created_at_utc or _utc_now()
    plan_id_value = plan_id or f"mgr_rerun_plan_{state.start_month}_{state.end_month}_{layer_id:02d}_{stage}"
    rerun_id_value = rerun_id or f"model_group_rerun_{state.start_month}_{state.end_month}_{layer_id:02d}_{stage}"
    stages = tuple(state.stages)
    cutpoint_index = _stage_order_index(stages, layer_id=layer_id, stage_type=stage)
    affected = stages[cutpoint_index:]
    delete_set: list[dict[str, Any]] = []
    for affected_stage in affected:
        delete_set.append(
            {
                "artifact_class": "workflow_state",
                "ref": _stage_ref(state_path, affected_stage.stage_id),
                "delete_reason": reason,
                "requires_storage_lifecycle_review": False,
            }
        )
        for ref in (*affected_stage.artifact_refs, *affected_stage.receipt_refs):
            delete_set.append(
                {
                    "artifact_class": _artifact_class_for_stage(affected_stage),
                    "ref": ref,
                    "delete_reason": reason,
                    "requires_storage_lifecycle_review": str(ref).startswith("storage://01_source_data/"),
                }
            )
    protected_set = [
        {
            "ref": ref,
            "protect_reason": PROTECTED_SOURCE_POLICIES[ref],
        }
        for ref in PROTECTED_SOURCE_REFS
    ]
    retained_set = _retained_set(storage_root)
    controlled_artifact_roots = _controlled_artifact_roots(storage_root)
    return {
        "plan_id": plan_id_value,
        "contract_type": "model_group_rerun_plan",
        "rerun_id": rerun_id_value,
        "reason": reason,
        "created_at_utc": created,
        "dry_run": True,
        "change_origin": {
            "layer_id": layer_id,
            "stage": stage,
            "description": reason,
        },
        "affected_scope": {
            "fold_id": f"fold_{state.start_month}_{state.end_month}",
            "start_month": state.start_month,
            "end_month": state.end_month,
            "target_symbols": list(target_symbols),
        },
        "source_data_delete": {
            "required": False,
            "reason": None,
            "scope_refs": list(source_data_delete_scope_refs),
        },
        "delete_set": delete_set,
        "protected_set": protected_set,
        "retained_set": retained_set,
        "controlled_artifact_roots": controlled_artifact_roots,
        "storage_lifecycle_request": _storage_lifecycle_request(
            rerun_id=rerun_id_value,
            plan_id=plan_id_value,
            delete_set=delete_set,
            protected_set=protected_set,
            retained_set=retained_set,
            controlled_artifact_roots=controlled_artifact_roots,
            reason=reason,
        ),
        "scheduler_reentry_stage": {
            "layer_id": layer_id,
            "stage": stage,
        },
        "expected_verification_gates": [
            "model_group_rerun_plan_schema_validation",
            "rerun_reset_receipt_written",
            "controlled_artifact_root_audit",
            "workflow_state_reentry_from_cutpoint",
            "historical_scheduler_decision_executed_after_reentry",
        ],
    }


def _reset_receipt_path(*, storage_root: Path, rerun_id: str, created_at_utc: str) -> Path:
    safe_rerun_id = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in rerun_id)
    filename = f"{_safe_timestamp_for_path(created_at_utc)}.reset_receipt.json"
    return storage_root / "runtime" / "model_group_rerun_resets" / safe_rerun_id / filename


def _reset_batch_receipt_path(*, storage_root: Path, batch_id: str) -> Path:
    safe_batch_id = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in batch_id)
    return storage_root / "runtime" / "model_group_rerun_resets" / "batches" / f"{safe_batch_id}.reset_batch_receipt.json"


def _write_reset_receipt(
    *,
    storage_root: Path,
    result_summary: dict[str, Any],
    reset_state: WorkflowState,
    created_at_utc: str,
) -> str:
    receipt_path = _reset_receipt_path(
        storage_root=storage_root,
        rerun_id=str(result_summary["rerun_id"]),
        created_at_utc=created_at_utc,
    )
    payload = {
        "contract_type": "manager_model_group_rerun_reset_receipt",
        "created_at_utc": created_at_utc,
        "rerun_id": result_summary["rerun_id"],
        "plan_id": result_summary["plan_id"],
        "dry_run": result_summary["dry_run"],
        "write_performed": result_summary["write_performed"],
        "state_path": result_summary["state_path"],
        "cutpoint_stage_id": result_summary["cutpoint_stage_id"],
        "changed_stage_count": result_summary["changed_stage_count"],
        "preserved_stage_count": result_summary["preserved_stage_count"],
        "source_data_delete_required": result_summary["source_data_delete_required"],
        "protected_set": result_summary["plan"]["protected_set"],
        "retained_set": result_summary["plan"]["retained_set"],
        "controlled_artifact_roots": result_summary["plan"]["controlled_artifact_roots"],
        "runtime_residue": {
            "empty_provider_task_key_dirs": _empty_provider_task_key_dirs(storage_root),
            "cleanup_policy": "empty runtime directories may be cleaned only by bounded housekeeping; protected source data is never cleaned by rerun reset",
        },
        "post_reset_stage_statuses": [
            {
                "stage_id": stage.stage_id,
                "status": stage.status,
                "last_reason": stage.last_reason,
            }
            for stage in reset_state.stages
        ],
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(receipt_path)


def _load_reset_receipt(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("contract_type") != "manager_model_group_rerun_reset_receipt":
        raise ValueError(f"not a model-group reset receipt: {path}")
    return payload


def _month_key_from_state_path(state_path: str) -> str | None:
    stem = Path(state_path).stem
    if stem.startswith("model_training_workflow_state_"):
        return stem.removeprefix("model_training_workflow_state_")
    if stem.startswith("model_training_fold_state_"):
        parts = stem.split("_")
        if len(parts) >= 6:
            return parts[-2]
    return None


def _target_symbol_from_state_path(state_path: str) -> str | None:
    stem = Path(state_path).stem
    prefix = "model_training_fold_state_"
    if not stem.startswith(prefix):
        return None
    rest = stem.removeprefix(prefix)
    parts = rest.split("_")
    if len(parts) == 3:
        return parts[0].upper()
    return None


def write_reset_batch_receipt(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    batch_id: str,
    receipt_paths: Iterable[Path],
    reason: str,
    created_at_utc: str | None = None,
) -> str:
    """Write the human-facing summary receipt for a batch of state reset receipts."""

    created = created_at_utc or _utc_now()
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for path in receipt_paths:
        loaded.append((path, _load_reset_receipt(path)))
    if not loaded:
        raise ValueError("at least one reset receipt is required")

    receipt_rows: list[dict[str, Any]] = []
    months: list[str] = []
    targets: set[str] = set()
    cutpoints: set[str] = set()
    changed_total = 0
    preserved_total = 0
    source_data_delete_required = False
    protected_refs: set[str] = set()
    retained_refs: set[str] = set()

    for path, payload in sorted(loaded, key=lambda item: (str(item[1].get("state_path") or ""), str(item[0]))):
        state_path = str(payload["state_path"])
        month_key = _month_key_from_state_path(state_path)
        if month_key:
            months.append(month_key)
        target_symbol = _target_symbol_from_state_path(state_path)
        if target_symbol:
            targets.add(target_symbol)
        cutpoints.add(str(payload["cutpoint_stage_id"]))
        changed_total += int(payload["changed_stage_count"])
        preserved_total += int(payload["preserved_stage_count"])
        source_data_delete_required = source_data_delete_required or bool(payload["source_data_delete_required"])
        protected_refs.update(str(row["ref"]) for row in payload.get("protected_set", []))
        retained_refs.update(str(row["ref"]) for row in payload.get("retained_set", []))
        receipt_rows.append(
            {
                "state_path": state_path,
                "rerun_id": payload["rerun_id"],
                "plan_id": payload["plan_id"],
                "receipt_path": str(path),
                "cutpoint_stage_id": payload["cutpoint_stage_id"],
                "changed_stage_count": payload["changed_stage_count"],
                "preserved_stage_count": payload["preserved_stage_count"],
            }
        )

    payload = {
        "contract_type": "manager_model_group_rerun_reset_batch_receipt",
        "created_at_utc": created,
        "batch_id": batch_id,
        "reason": reason,
        "operator_entrypoint": (
            "Use this batch receipt as the reset summary; per-state reset receipts are audit drill-down references."
        ),
        "scope": {
            "start_month": min(months) if months else None,
            "end_month": max(months) if months else None,
            "target_symbols": sorted(targets),
            "cutpoint_stage_ids": sorted(cutpoints),
        },
        "receipt_count": len(receipt_rows),
        "state_count": len({row["state_path"] for row in receipt_rows}),
        "changed_stage_count": changed_total,
        "preserved_stage_count": preserved_total,
        "source_data_delete_required": source_data_delete_required,
        "protected_refs": sorted(protected_refs),
        "retained_refs": sorted(retained_refs),
        "reset_receipts": receipt_rows,
    }
    batch_path = _reset_batch_receipt_path(storage_root=storage_root, batch_id=batch_id)
    batch_path.parent.mkdir(parents=True, exist_ok=True)
    batch_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(batch_path)


def execute_model_group_rerun_reset(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    state_path: Path | None = None,
    start_month: str,
    end_month: str,
    target_symbol: str | None,
    layer_id: int,
    stage: RerunStage,
    reason: str,
    write: bool = False,
) -> ModelGroupRerunResult:
    """Reset workflow stage state from a rerun cutpoint while preserving source data."""

    resolved_state_path = state_path or model_worker_fold_state_path(
        start_month,
        end_month,
        root=storage_root / "runtime",
        selected_target_symbol=target_symbol,
    )
    plan = build_model_training_workflow_plan(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        selected_target_symbol=target_symbol,
        foundation_catch_up_only=False,
    )
    state = load_workflow_state(resolved_state_path, plan)
    rerun_plan = build_model_group_rerun_plan(
        state=state,
        state_path=resolved_state_path,
        storage_root=storage_root,
        layer_id=layer_id,
        stage=stage,
        reason=reason,
        target_symbols=(target_symbol,) if target_symbol else (),
    )
    cutpoint_index = _stage_order_index(state.stages, layer_id=layer_id, stage_type=stage)
    now = _utc_now()
    reset_reason = f"rerun reset from layer_{layer_id:02d}.{stage}: {reason}"
    stages = []
    changed = 0
    preserved = 0
    for index, current_stage in enumerate(state.stages):
        if index >= cutpoint_index and current_stage.status != "not_applicable":
            stages.append(_reset_stage(current_stage, now=now, reason=reset_reason))
            changed += 1
        else:
            stages.append(current_stage)
            preserved += 1
    reset_state = refresh_workflow_state(
        WorkflowState(
            contract_type=state.contract_type,
            start_month=state.start_month,
            end_month=state.end_month,
            stages=tuple(stages),
            updated_utc=now,
            provider_calls=state.provider_calls,
            provider_calls_observed=state.provider_calls_observed,
            model_activation_performed=False,
            broker_execution_performed=False,
        ),
        plan=plan,
    )
    if write:
        write_workflow_state(resolved_state_path, reset_state)
    result_kwargs = {
        "contract_type": "manager_model_group_rerun_reset",
        "plan_id": str(rerun_plan["plan_id"]),
        "rerun_id": str(rerun_plan["rerun_id"]),
        "dry_run": not write,
        "state_path": str(resolved_state_path),
        "changed_stage_count": changed,
        "preserved_stage_count": preserved,
        "cutpoint_stage_id": state.stages[cutpoint_index].stage_id,
        "source_data_delete_required": False,
        "write_performed": write,
        "reset_receipt_path": None,
        "reset_receipt_written": False,
        "plan": rerun_plan,
    }
    if write:
        result_kwargs["reset_receipt_path"] = _write_reset_receipt(
            storage_root=storage_root,
            result_summary=result_kwargs,
            reset_state=reset_state,
            created_at_utc=now,
        )
        result_kwargs["reset_receipt_written"] = True
    return ModelGroupRerunResult(
        **result_kwargs,
    )


def write_summary(result: ModelGroupRerunResult, *, output: TextIO) -> None:
    json.dump(result.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def _parse_created_at(value: str) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _iter_reset_receipt_paths(
    *,
    storage_root: Path,
    receipt_glob: str,
    created_after: str | None,
    created_before: str | None,
) -> list[Path]:
    lower = _parse_created_at(created_after) if created_after else None
    upper = _parse_created_at(created_before) if created_before else None
    candidates = [
        path
        for path in (storage_root / "runtime" / "model_group_rerun_resets").glob(receipt_glob)
        if path.is_file() and path.name.endswith(".reset_receipt.json")
    ]
    selected: list[Path] = []
    for path in candidates:
        payload = _load_reset_receipt(path)
        created = _parse_created_at(str(payload["created_at_utc"]))
        if lower and created < lower:
            continue
        if upper and created > upper:
            continue
        selected.append(path)
    return sorted(selected)


def batch_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize model-group rerun reset receipts into one batch receipt.")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--receipt-glob", default="*/*.reset_receipt.json")
    parser.add_argument("--created-after")
    parser.add_argument("--created-before")
    args = parser.parse_args(argv)
    receipt_paths = _iter_reset_receipt_paths(
        storage_root=args.storage_root,
        receipt_glob=args.receipt_glob,
        created_after=args.created_after,
        created_before=args.created_before,
    )
    batch_path = write_reset_batch_receipt(
        storage_root=args.storage_root,
        batch_id=args.batch_id,
        receipt_paths=receipt_paths,
        reason=args.reason,
    )
    json.dump({"batch_receipt_path": batch_path, "receipt_count": len(receipt_paths)}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or execute a controlled model-group rerun state reset.")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--state-path", type=Path)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--target-symbol")
    parser.add_argument("--layer-id", required=True, type=int)
    parser.add_argument("--stage", required=True, choices=list(RerunStage.__args__))  # type: ignore[attr-defined]
    parser.add_argument("--reason", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    result = execute_model_group_rerun_reset(
        storage_root=args.storage_root,
        state_path=args.state_path,
        start_month=args.start_month,
        end_month=args.end_month,
        target_symbol=args.target_symbol,
        layer_id=args.layer_id,
        stage=args.stage,
        reason=args.reason,
        write=args.execute,
    )
    write_summary(result, output=sys.stdout)
    return 0


__all__ = [
    "ModelGroupRerunResult",
    "build_model_group_rerun_plan",
    "execute_model_group_rerun_reset",
    "write_reset_batch_receipt",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

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
    if stage.stage_type == "model_generation":
        return "model_output"
    if stage.stage_type == "model_evaluation":
        return "evaluation_artifact"
    if stage.stage_type == "promotion_review":
        return "promotion_artifact"
    return "runtime_state"


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
            "protect_reason": "source data is protected for this rerun; source_data_delete.required is false",
        }
        for ref in PROTECTED_SOURCE_REFS
    ]
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
        "scheduler_reentry_stage": {
            "layer_id": layer_id,
            "stage": stage,
        },
        "expected_verification_gates": [
            "model_group_rerun_plan_schema_validation",
            "workflow_state_reentry_from_cutpoint",
            "historical_scheduler_decision_executed_after_reentry",
        ],
    }


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
    return ModelGroupRerunResult(
        contract_type="manager_model_group_rerun_reset",
        plan_id=str(rerun_plan["plan_id"]),
        rerun_id=str(rerun_plan["rerun_id"]),
        dry_run=not write,
        state_path=str(resolved_state_path),
        changed_stage_count=changed,
        preserved_stage_count=preserved,
        cutpoint_stage_id=state.stages[cutpoint_index].stage_id,
        source_data_delete_required=False,
        write_performed=write,
        plan=rerun_plan,
    )


def write_summary(result: ModelGroupRerunResult, *, output: TextIO) -> None:
    json.dump(result.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


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
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

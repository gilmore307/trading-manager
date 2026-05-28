"""Durable state progression for the historical base-stack workflow."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, TextIO

from .model_training_workflow import (
    FOUNDATION_CATCH_UP_BLOCKER,
    FOLD_STACK_PROMOTION_BLOCKER,
    POST_MODEL_GENERATION_REBUILD_BLOCKER,
    DatasetUnit,
    ModelTrainingWorkflowPlan,
    WorkflowStage,
    base_stack_model_generation_splits_complete,
    build_model_training_workflow_plan,
    model_generation_splits_complete,
)
from .request_payloads import DEFAULT_STORAGE_ROOT
from .dashboard_refresh_events import trigger_dashboard_refresh_from_workflow_state_write

DEFAULT_WORKFLOW_STATE_PATH = DEFAULT_STORAGE_ROOT / "runtime" / "model_training_workflow_state.json"
DEFAULT_WORKFLOW_STATE_ROOT = DEFAULT_STORAGE_ROOT / "runtime"


def workflow_state_path_for_month(start_month: str, *, root: Path = DEFAULT_WORKFLOW_STATE_ROOT) -> Path:
    """Return the scheduler-owned month-scoped workflow checkpoint path."""

    return root / f"model_training_workflow_state_{start_month}.json"


def resolve_workflow_state_path(
    start_month: str,
    state_path: Path | None = None,
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> Path:
    """Resolve explicit or automatic month-scoped workflow checkpoint path."""

    return state_path if state_path is not None else workflow_state_path_for_month(start_month, root=storage_root / "runtime")


StageProgressStatus = Literal["pending", "blocked", "ready", "succeeded", "failed", "not_applicable"]
TERMINAL_STAGE_STATUSES = {"succeeded", "failed", "not_applicable"}


@dataclass(frozen=True)
class StageProgress:
    """Durable progress for one workflow stage."""

    stage_id: str
    layer: int
    layer_key: str
    stage_type: str
    status: StageProgressStatus
    command: list[str]
    blockers: tuple[str, ...]
    dataset_unit: DatasetUnit | None = None
    dataset_split: dict[str, Any] | None = None
    approval_gate_required: str | None = None
    approval_status: str | None = None
    artifact_refs: tuple[str, ...] = ()
    receipt_refs: tuple[str, ...] = ()
    last_reason: str | None = None
    updated_utc: str | None = None
    created_at_utc: str | None = None
    started_at_utc: str | None = None
    ended_at_utc: str | None = None
    status_updated_at_utc: str | None = None

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["blockers"] = list(self.blockers)
        row["dataset_unit"] = self.dataset_unit.summary_row() if self.dataset_unit else None
        if self.dataset_split is not None:
            row["dataset_split"] = dict(self.dataset_split)
        row["artifact_refs"] = list(self.artifact_refs)
        row["receipt_refs"] = list(self.receipt_refs)
        return row


@dataclass(frozen=True)
class WorkflowState:
    """Durable manager-owned workflow checkpoint."""

    contract_type: str
    start_month: str
    end_month: str
    stages: tuple[StageProgress, ...]
    updated_utc: str
    provider_calls: int = 0
    provider_calls_observed: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "stages": [stage.summary_row() for stage in self.stages],
            "next_stage": next_ready_or_blocked_stage(self).summary_row() if next_ready_or_blocked_stage(self) else None,
            "updated_utc": self.updated_utc,
            "provider_calls": self.provider_calls,
            "provider_calls_observed": self.provider_calls_observed,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
        }


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stage_from_plan(stage: WorkflowStage, *, now: str) -> StageProgress:
    status: StageProgressStatus = "not_applicable" if stage.status == "not_applicable" else "pending"
    return StageProgress(
        stage_id=stage.stage_id,
        layer=stage.layer,
        layer_key=stage.layer_key,
        stage_type=stage.stage_type,
        status=status,
        command=stage.command,
        blockers=stage.blockers,
        dataset_unit=stage.dataset_unit,
        dataset_split=dict(stage.dataset_split) if stage.dataset_split is not None else None,
        approval_gate_required=stage.approval_gate_required,
        updated_utc=now,
        created_at_utc=now,
        status_updated_at_utc=now,
    )


def _stage_with_update(stage: StageProgress, *, now: str, **changes: Any) -> StageProgress:
    next_status = changes.get("status", stage.status)
    if next_status != stage.status and "status_updated_at_utc" not in changes:
        changes["status_updated_at_utc"] = now
    if "updated_utc" not in changes:
        changes["updated_utc"] = now
    return replace(stage, **changes)


def initial_workflow_state(plan: ModelTrainingWorkflowPlan) -> WorkflowState:
    now = utc_now_iso()
    stages = tuple(_stage_from_plan(stage, now=now) for layer in plan.layers for stage in layer.stages)
    return refresh_workflow_state(
        WorkflowState(
            contract_type="manager_model_training_workflow_state",
            start_month=plan.start_month,
            end_month=plan.end_month,
            stages=stages,
            updated_utc=now,
        ),
        plan=plan,
    )


def load_workflow_state(path: Path, plan: ModelTrainingWorkflowPlan) -> WorkflowState:
    if not path.exists():
        return initial_workflow_state(plan)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("start_month") != plan.start_month or payload.get("end_month") != plan.end_month:
        return initial_workflow_state(plan)
    by_plan = {stage.stage_id: stage for layer in plan.layers for stage in layer.stages}
    loaded = {}
    now = utc_now_iso()
    for row in payload.get("stages", []):
        if not isinstance(row, Mapping) or row.get("stage_id") not in by_plan:
            continue
        stage = by_plan[str(row["stage_id"])]
        status = str(row.get("status") or "pending")
        loaded[stage.stage_id] = StageProgress(
            stage_id=stage.stage_id,
            layer=stage.layer,
            layer_key=stage.layer_key,
            stage_type=stage.stage_type,
            status=status,  # type: ignore[arg-type]
            command=stage.command,
            blockers=stage.blockers,
            dataset_unit=stage.dataset_unit,
            dataset_split=dict(stage.dataset_split) if stage.dataset_split is not None else None,
            approval_gate_required=stage.approval_gate_required,
            approval_status=row.get("approval_status"),
            artifact_refs=tuple(str(item) for item in row.get("artifact_refs") or []),
            receipt_refs=tuple(str(item) for item in row.get("receipt_refs") or []),
            last_reason=row.get("last_reason"),
            updated_utc=row.get("updated_utc"),
            created_at_utc=row.get("created_at_utc"),
            started_at_utc=row.get("started_at_utc"),
            ended_at_utc=row.get("ended_at_utc"),
            status_updated_at_utc=row.get("status_updated_at_utc"),
        )
    stages = tuple(loaded.get(stage.stage_id) or _stage_from_plan(stage, now=now) for layer in plan.layers for stage in layer.stages)
    state = WorkflowState(
        contract_type="manager_model_training_workflow_state",
        start_month=plan.start_month,
        end_month=plan.end_month,
        stages=stages,
        updated_utc=str(payload.get("updated_utc") or now),
        provider_calls=int(payload.get("provider_calls") or 0),
        provider_calls_observed=int(payload.get("provider_calls_observed") or 0),
        model_activation_performed=bool(payload.get("model_activation_performed", False)),
        broker_execution_performed=bool(payload.get("broker_execution_performed", False)),
    )
    return refresh_workflow_state(state, plan=plan)


def write_workflow_state(path: Path, state: WorkflowState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
    trigger_dashboard_refresh_from_workflow_state_write(state_path=path)


def _stage_map(state: WorkflowState) -> dict[str, StageProgress]:
    return {stage.stage_id: stage for stage in state.stages}


def _layer_stage_ids(state: WorkflowState, layer: int) -> list[str]:
    return [stage.stage_id for stage in state.stages if stage.layer == layer]


def _layer_complete(layer_number: int, stages: Mapping[str, StageProgress]) -> bool:
    layer_stages = [stage for stage in stages.values() if stage.layer == layer_number]
    return bool(layer_stages) and all(stage.status in {"succeeded", "not_applicable"} for stage in layer_stages)


def _layer_model_evaluation_complete(layer_number: int, stages: Mapping[str, StageProgress]) -> bool:
    layer_stages = [stage for stage in stages.values() if stage.layer == layer_number and stage.stage_type == "model_evaluation"]
    return bool(layer_stages) and all(stage.status in {"succeeded", "not_applicable"} for stage in layer_stages)


def _layer_model_generation_complete(layer_number: int, stages: Mapping[str, StageProgress]) -> bool:
    return model_generation_splits_complete(stages.values(), layer_number=layer_number)


def _is_satisfied(blocker: str, stages: Mapping[str, StageProgress]) -> bool:
    if blocker in {"layer_01_task_key_preparation", FOUNDATION_CATCH_UP_BLOCKER, POST_MODEL_GENERATION_REBUILD_BLOCKER}:
        return False
    if blocker == FOLD_STACK_PROMOTION_BLOCKER:
        return base_stack_model_generation_splits_complete(stages.values())
    if blocker == "upstream_layers_01_08_complete":
        return all(_layer_complete(layer_number, stages) for layer_number in range(1, 9))
    if blocker == "active_target_chain_complete":
        return _layer_complete(8, stages)
    if blocker.startswith("upstream_layer_") and blocker.endswith("_model_evaluation_complete"):
        layer_number = int(blocker.removeprefix("upstream_layer_").removesuffix("_model_evaluation_complete"))
        return _layer_model_evaluation_complete(layer_number, stages)
    if blocker.startswith("upstream_layer_") and blocker.endswith("_model_generation_complete"):
        layer_number = int(blocker.removeprefix("upstream_layer_").removesuffix("_model_generation_complete"))
        return _layer_model_generation_complete(layer_number, stages)
    if blocker.startswith("upstream_layer_") and blocker.endswith("_complete"):
        layer_number = int(blocker.removeprefix("upstream_layer_").removesuffix("_complete"))
        return _layer_complete(layer_number, stages)
    if blocker.endswith("_complete"):
        stage_id = blocker.removesuffix("_complete")
        stage = stages.get(stage_id)
        return stage is not None and stage.status in {"succeeded", "not_applicable"}
    if blocker.endswith(".feature_or_input_ready"):
        layer_key = blocker.removesuffix(".feature_or_input_ready")
        feature = stages.get(f"{layer_key}.feature_generation")
        acquisition = stages.get(f"{layer_key}.data_acquisition")
        return (feature is not None and feature.status in {"succeeded", "not_applicable"}) or (
            acquisition is not None and acquisition.status in {"succeeded", "not_applicable"}
        )
    return False


def _ready_last_reason(stage: StageProgress) -> str | None:
    """Keep evidence reasons on ready stages while clearing stale blocker text."""

    if not stage.last_reason:
        return None
    if stage.last_reason.startswith("waiting for ") or stage.last_reason == "approval gate satisfied":
        return None
    return stage.last_reason


def _ready_started_at(stage: StageProgress, ready_reason: str | None) -> str | None:
    if not ready_reason:
        return None
    normalized = ready_reason.lower()
    if "stage execution started" in normalized or "stage started" in normalized:
        return stage.started_at_utc
    return None


def _blocker_reason(stage: StageProgress, stages: Mapping[str, StageProgress]) -> str | None:
    missing = []
    for blocker in stage.blockers:
        if blocker == stage.approval_gate_required and stage.approval_status == "approved":
            continue
        if not _is_satisfied(blocker, stages):
            missing.append(blocker)
    if not missing:
        return None
    if stage.approval_gate_required and missing == [stage.approval_gate_required]:
        return f"waiting for {stage.approval_gate_required}"
    return "waiting for " + ",".join(missing)


def refresh_workflow_state(state: WorkflowState, *, plan: ModelTrainingWorkflowPlan) -> WorkflowState:
    """Refresh ready/blocked status from durable completions and current plan."""

    plan_stages = {stage.stage_id: stage for layer in plan.layers for stage in layer.stages}
    current = _stage_map(state)
    refreshed: list[StageProgress] = []
    now = utc_now_iso()
    working = dict(current)
    for plan_stage in plan_stages.values():
        stage = working.get(plan_stage.stage_id) or _stage_from_plan(plan_stage, now=now)
        stage = replace(
            stage,
            command=plan_stage.command,
            blockers=plan_stage.blockers,
            dataset_split=dict(plan_stage.dataset_split) if plan_stage.dataset_split is not None else None,
            approval_gate_required=plan_stage.approval_gate_required,
        )
        if stage.status in {"succeeded", "failed", "not_applicable"}:
            refreshed.append(stage)
            working[stage.stage_id] = stage
            continue
        reason = _blocker_reason(stage, working)
        if reason is None:
            status: StageProgressStatus = "ready"
            approval_status = stage.approval_status
            if stage.approval_gate_required and approval_status != "approved":
                status = "blocked"
                reason = f"waiting for {stage.approval_gate_required}"
            ready_reason = None if status == "blocked" else _ready_last_reason(stage)
            stage = _stage_with_update(
                stage,
                status=status,
                last_reason=reason if status == "blocked" else ready_reason,
                started_at_utc=stage.started_at_utc if status == "blocked" else _ready_started_at(stage, ready_reason),
                now=now,
            )
        else:
            stage = _stage_with_update(stage, status="blocked", last_reason=reason, now=now)
        refreshed.append(stage)
        working[stage.stage_id] = stage
    return replace(state, stages=tuple(refreshed), updated_utc=now)


def next_ready_or_blocked_stage(state: WorkflowState) -> StageProgress | None:
    for stage in state.stages:
        if stage.status == "ready":
            return stage
    for stage in state.stages:
        if (
            stage.status == "blocked"
            and stage.approval_gate_required
            and stage.last_reason == f"waiting for {stage.approval_gate_required}"
        ):
            return stage
    return None


def _terminal_receipt_success(receipt: Mapping[str, Any]) -> bool:
    runs = receipt.get("runs")
    if isinstance(runs, list) and runs:
        latest = [run for run in runs if isinstance(run, Mapping)]
        if not latest:
            return False
        return str(latest[-1].get("status") or "").lower() in {"succeeded", "success", "completed", "complete", "ready"}
    return str(receipt.get("status") or "").lower() in {"succeeded", "success", "completed", "complete", "ready"}


def _task_key_count_for_stage(stage_id: str, *, storage_root: Path, start_month: str, end_month: str) -> int | None:
    if start_month != end_month:
        return None
    if stage_id == "layer_01_market_regime.data_acquisition":
        return len(list((storage_root / "monthly_backfill" / "alpaca_bars").glob(f"*/{start_month}/task_key.json")))
    return None


def _expected_receipt_count(
    stage_id: str,
    *,
    storage_root: Path,
    start_month: str,
    end_month: str,
    explicit_counts: Mapping[str, int] | None = None,
) -> int:
    if explicit_counts and stage_id in explicit_counts:
        return explicit_counts[stage_id]
    discovered = _task_key_count_for_stage(stage_id, storage_root=storage_root, start_month=start_month, end_month=end_month)
    if discovered:
        return discovered
    return 1


def _attach_stage_evidence(
    state: WorkflowState,
    *,
    stage_id: str,
    receipt_refs: Iterable[str] = (),
    artifact_refs: Iterable[str] = (),
    reason: str | None = None,
) -> WorkflowState:
    now = utc_now_iso()
    changed = []
    found = False
    for stage in state.stages:
        if stage.stage_id != stage_id:
            changed.append(stage)
            continue
        found = True
        receipts = tuple(dict.fromkeys([*stage.receipt_refs, *[str(item) for item in receipt_refs]]))
        artifacts = tuple(dict.fromkeys([*stage.artifact_refs, *[str(item) for item in artifact_refs]]))
        changed.append(_stage_with_update(stage, receipt_refs=receipts, artifact_refs=artifacts, last_reason=reason or stage.last_reason, now=now))
    if not found:
        raise ValueError(f"unknown workflow stage: {stage_id}")
    return replace(state, stages=tuple(changed), updated_utc=now)


def mark_stage_started(state: WorkflowState, *, stage_id: str, started_at: str | None = None, reason: str | None = None) -> WorkflowState:
    now = started_at or utc_now_iso()
    changed = []
    found = False
    for stage in state.stages:
        if stage.stage_id != stage_id:
            changed.append(stage)
            continue
        found = True
        if stage.status in TERMINAL_STAGE_STATUSES:
            changed.append(stage)
            continue
        changed.append(
            _stage_with_update(
                stage,
                started_at_utc=stage.started_at_utc or now,
                last_reason=reason or stage.last_reason,
                now=now,
            )
        )
    if not found:
        raise ValueError(f"unknown workflow stage: {stage_id}")
    return replace(state, stages=tuple(changed), updated_utc=now)


def mark_stage_succeeded(
    state: WorkflowState,
    *,
    stage_id: str,
    receipt_ref: str | None = None,
    artifact_refs: Iterable[str] = (),
    reason: str | None = None,
    ended_at: str | None = None,
) -> WorkflowState:
    now = ended_at or utc_now_iso()
    changed = []
    found = False
    for stage in state.stages:
        if stage.stage_id != stage_id:
            changed.append(stage)
            continue
        found = True
        receipts = tuple(dict.fromkeys([*stage.receipt_refs, *([receipt_ref] if receipt_ref else [])]))
        artifacts = tuple(dict.fromkeys([*stage.artifact_refs, *[str(item) for item in artifact_refs]]))
        status_is_changing = stage.status != "succeeded"
        ended_at_utc = stage.ended_at_utc or (now if status_is_changing else None)
        changed.append(
            _stage_with_update(
                stage,
                status="succeeded",
                receipt_refs=receipts,
                artifact_refs=artifacts,
                last_reason=reason or "stage completed from manager evidence",
                started_at_utc=stage.started_at_utc,
                ended_at_utc=ended_at_utc,
                now=now,
            )
        )
    if not found:
        raise ValueError(f"unknown workflow stage: {stage_id}")
    return replace(state, stages=tuple(changed), updated_utc=now)


def mark_stage_failed(
    state: WorkflowState,
    *,
    stage_id: str,
    receipt_ref: str | None = None,
    reason: str | None = None,
    ended_at: str | None = None,
) -> WorkflowState:
    now = ended_at or utc_now_iso()
    changed = []
    found = False
    for stage in state.stages:
        if stage.stage_id != stage_id:
            changed.append(stage)
            continue
        found = True
        receipts = tuple(dict.fromkeys([*stage.receipt_refs, *([receipt_ref] if receipt_ref else [])]))
        status_is_changing = stage.status != "failed"
        ended_at_utc = stage.ended_at_utc or (now if status_is_changing else None)
        changed.append(
            _stage_with_update(
                stage,
                status="failed",
                receipt_refs=receipts,
                last_reason=reason or "stage execution failed",
                started_at_utc=stage.started_at_utc,
                ended_at_utc=ended_at_utc,
                now=now,
            )
        )
    if not found:
        raise ValueError(f"unknown workflow stage: {stage_id}")
    return replace(state, stages=tuple(changed), updated_utc=now)


def mark_stage_approved(state: WorkflowState, *, stage_id: str, approval_ref: str) -> WorkflowState:
    now = utc_now_iso()
    changed = []
    found = False
    for stage in state.stages:
        if stage.stage_id != stage_id:
            changed.append(stage)
            continue
        found = True
        changed.append(
            _stage_with_update(
                stage,
                approval_status="approved",
                artifact_refs=tuple(dict.fromkeys([*stage.artifact_refs, approval_ref])),
                last_reason="approval gate satisfied",
                now=now,
            )
        )
    if not found:
        raise ValueError(f"unknown workflow stage: {stage_id}")
    return replace(state, stages=tuple(changed), updated_utc=now)


def _receipt_stage_id(receipt: Mapping[str, Any]) -> str | None:
    for key in ("manager_stage_id", "stage_id", "workflow_stage_id"):
        if receipt.get(key):
            return str(receipt[key])
    for run in receipt.get("runs") or []:
        if isinstance(run, Mapping):
            for key in ("manager_stage_id", "stage_id", "workflow_stage_id"):
                if run.get(key):
                    return str(run[key])
    return None


def _receipt_artifacts(receipt: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for run in receipt.get("runs") or ([receipt] if receipt.get("run_id") else []):
        if not isinstance(run, Mapping):
            continue
        for output in run.get("output_refs") or run.get("outputs") or run.get("artifacts") or []:
            if isinstance(output, str):
                refs.append(output)
            elif isinstance(output, Mapping):
                value = output.get("uri") or output.get("ref") or output.get("path")
                if value:
                    refs.append(str(value))
    return refs


def _receipt_provider_calls(receipt: Mapping[str, Any]) -> int:
    try:
        return int(receipt.get("provider_calls") or 0)
    except (TypeError, ValueError):
        return 0


def _receipt_ref_known(state: WorkflowState, receipt_ref: str) -> bool:
    return any(receipt_ref in stage.receipt_refs for stage in state.stages)


def _add_observed_provider_calls_if_new(state: WorkflowState, *, receipt_ref: str, receipt: Mapping[str, Any]) -> WorkflowState:
    if _receipt_ref_known(state, receipt_ref):
        return state
    provider_calls = _receipt_provider_calls(receipt)
    if provider_calls <= 0:
        return state
    return replace(state, provider_calls_observed=state.provider_calls_observed + provider_calls)

def ingest_completion_receipts(state: WorkflowState, receipt_paths: Iterable[Path]) -> WorkflowState:
    updated = state
    for path in receipt_paths:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(receipt, Mapping):
            raise ValueError(f"receipt must be a JSON object: {path}")
        stage_id = _receipt_stage_id(receipt)
        if not stage_id:
            raise ValueError(f"receipt missing manager_stage_id/stage_id: {path}")
        updated = _add_observed_provider_calls_if_new(updated, receipt_ref=str(path), receipt=receipt)
        if not _terminal_receipt_success(receipt):
            updated = _attach_stage_evidence(
                updated,
                stage_id=stage_id,
                receipt_refs=[str(path)],
                artifact_refs=_receipt_artifacts(receipt),
                reason="component receipt observed but not successful",
            )
            continue
        updated = mark_stage_succeeded(
            updated,
            stage_id=stage_id,
            receipt_ref=str(path),
            artifact_refs=_receipt_artifacts(receipt),
            reason="stage completed from component receipt",
        )
    return updated


def parse_stage_receipt_arg(raw: str) -> tuple[str, Path]:
    if "=" not in raw:
        raise ValueError("stage receipt must use STAGE_ID=PATH")
    stage_id, path = raw.split("=", 1)
    if not stage_id.strip() or not path.strip():
        raise ValueError("stage receipt must use STAGE_ID=PATH")
    return stage_id.strip(), Path(path)


def parse_expected_count_arg(raw: str) -> tuple[str, int]:
    if "=" not in raw:
        raise ValueError("expected count must use STAGE_ID=COUNT")
    stage_id, count_text = raw.split("=", 1)
    count = int(count_text)
    if count <= 0:
        raise ValueError("expected receipt count must be positive")
    return stage_id.strip(), count


def ingest_stage_receipts(
    state: WorkflowState,
    stage_receipts: Sequence[tuple[str, Path]],
    *,
    storage_root: Path,
    start_month: str,
    end_month: str,
    expected_counts: Mapping[str, int] | None = None,
) -> WorkflowState:
    """Attach component receipts to explicit workflow stages.

    Component-local receipts do not always include manager workflow stage ids.
    This path lets manager bind those receipts without prematurely marking a
    stage complete. A stage succeeds only when successful receipt coverage meets
    the expected count for that stage.
    """

    updated = state
    by_stage: dict[str, list[Path]] = {}
    for stage_id, path in stage_receipts:
        by_stage.setdefault(stage_id, []).append(path)
    for stage_id, paths in by_stage.items():
        successful_receipts = []
        artifact_refs: list[str] = []
        observed_receipts = []
        failed_receipts = []
        for path in paths:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(receipt, Mapping):
                raise ValueError(f"receipt must be a JSON object: {path}")
            observed_receipts.append(str(path))
            updated = _add_observed_provider_calls_if_new(updated, receipt_ref=str(path), receipt=receipt)
            artifact_refs.extend(_receipt_artifacts(receipt))
            if _terminal_receipt_success(receipt):
                successful_receipts.append(str(path))
            else:
                failed_receipts.append(str(path))
        updated = _attach_stage_evidence(
            updated,
            stage_id=stage_id,
            receipt_refs=observed_receipts,
            artifact_refs=artifact_refs,
            reason="component receipt evidence attached",
        )
        stage = _stage_map(updated)[stage_id]
        expected = _expected_receipt_count(
            stage_id,
            storage_root=storage_root,
            start_month=start_month,
            end_month=end_month,
            explicit_counts=expected_counts,
        )
        successful_total = len([ref for ref in stage.receipt_refs if ref not in failed_receipts])
        if successful_total >= expected:
            updated = mark_stage_succeeded(
                updated,
                stage_id=stage_id,
                artifact_refs=stage.artifact_refs,
                reason=f"stage completed from component receipt coverage {successful_total}/{expected}",
            )
        else:
            updated = _attach_stage_evidence(
                updated,
                stage_id=stage_id,
                reason=f"partial component receipt coverage {successful_total}/{expected}; waiting for remaining receipts",
            )
    return updated


def ingest_stage_coverage_reports(state: WorkflowState, coverage_report_paths: Iterable[Path]) -> WorkflowState:
    """Apply manager_stage_coverage reports without bypassing coverage.

    A coverage report can attach SQL-derived control-plane evidence to a stage.
    It may mark the stage succeeded only when the report explicitly says the
    full stage is ready and downstream unlock is allowed.
    """

    updated = state
    for path in coverage_report_paths:
        report = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(report, Mapping):
            raise ValueError(f"stage coverage report must be a JSON object: {path}")
        if report.get("contract_type") != "manager_stage_coverage":
            raise ValueError(f"stage coverage report has unsupported contract_type: {path}")
        stage_id = str(report.get("stage_id") or "")
        if not stage_id:
            raise ValueError(f"stage coverage report missing stage_id: {path}")
        reason = str(report.get("reason") or "stage coverage evidence attached")
        updated = _attach_stage_evidence(updated, stage_id=stage_id, receipt_refs=[str(path)], reason=reason)
        if report.get("status") == "ready" and report.get("can_unlock_downstream") is True:
            updated = mark_stage_succeeded(
                updated,
                stage_id=stage_id,
                receipt_ref=str(path),
                reason=reason,
            )
    return updated


def advance_workflow_state(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    state_path: Path | None = None,
    receipt_paths: Iterable[Path] = (),
    stage_receipts: Sequence[tuple[str, Path]] = (),
    stage_coverage_reports: Iterable[Path] = (),
    expected_receipt_counts: Mapping[str, int] | None = None,
    completed_stage_ids: Iterable[str] = (),
    approved_stage_refs: Iterable[str] = (),
    selected_target_symbol: str | None = None,
    foundation_catch_up_only: bool = True,
    write: bool = False,
) -> WorkflowState:
    state_path = resolve_workflow_state_path(start_month, state_path, storage_root=storage_root)
    plan = build_model_training_workflow_plan(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=foundation_catch_up_only,
    )
    state = load_workflow_state(state_path, plan)
    state = ingest_completion_receipts(state, receipt_paths)
    for raw in approved_stage_refs:
        if "=" in raw:
            stage_id, approval_ref = raw.split("=", 1)
        else:
            stage_id, approval_ref = raw, "stage_approval_ref"
        state = mark_stage_approved(state, stage_id=stage_id, approval_ref=approval_ref)
    state = ingest_stage_receipts(
        state,
        stage_receipts,
        storage_root=storage_root,
        start_month=start_month,
        end_month=end_month,
        expected_counts=expected_receipt_counts,
    )
    state = ingest_stage_coverage_reports(state, stage_coverage_reports)
    for stage_id in completed_stage_ids:
        state = mark_stage_succeeded(state, stage_id=stage_id, reason="stage completed from manager operator evidence")
    state = refresh_workflow_state(state, plan=plan)
    if write:
        write_workflow_state(state_path, state)
    return state


def write_state_output(state: WorkflowState, *, output: TextIO) -> None:
    json.dump(state.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Advance the durable historical base-stack workflow state.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--state-path", type=Path, default=None, help="Workflow checkpoint path; defaults to the manager runtime root under trading-storage/storage/02_control_plane/runtime.")
    parser.add_argument("--receipt", action="append", type=Path, default=[], help="Component receipt JSON with manager_stage_id/stage_id to ingest.")
    parser.add_argument("--stage-receipt", action="append", default=[], help="Bind a component receipt to a stage without requiring embedded stage id: STAGE_ID=PATH.")
    parser.add_argument("--expected-receipt-count", action="append", default=[], help="Override expected successful receipt count for a stage: STAGE_ID=COUNT.")
    parser.add_argument("--stage-coverage-report", action="append", type=Path, default=[], help="Ingest manager_stage_coverage report; only ready/full coverage may complete a stage.")
    parser.add_argument("--complete-stage", action="append", default=[], help="Mark a workflow stage succeeded from manager evidence.")
    parser.add_argument("--approve-stage", action="append", default=[], help="Mark stage approval as satisfied: stage_id=approval_ref.")
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for Layer 3+ six-month dataset units.")
    parser.add_argument(
        "--allow-post-foundation-model-stages",
        action="store_true",
        help="Allow model generation/evaluation/promotion stages after the Layer 1/2 historical substrate catch-up has been explicitly accepted.",
    )
    parser.add_argument("--write", action="store_true", help="Persist the refreshed workflow state checkpoint.")
    args = parser.parse_args(argv)
    state = advance_workflow_state(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        state_path=args.state_path,
        receipt_paths=args.receipt,
        stage_receipts=[parse_stage_receipt_arg(item) for item in args.stage_receipt],
        stage_coverage_reports=args.stage_coverage_report,
        expected_receipt_counts=dict(parse_expected_count_arg(item) for item in args.expected_receipt_count),
        completed_stage_ids=args.complete_stage,
        approved_stage_refs=args.approve_stage,
        selected_target_symbol=args.target_symbol,
        foundation_catch_up_only=not args.allow_post_foundation_model_stages,
        write=args.write,
    )
    write_state_output(state, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_WORKFLOW_STATE_PATH",
    "workflow_state_path_for_month",
    "resolve_workflow_state_path",
    "StageProgress",
    "WorkflowState",
    "advance_workflow_state",
    "initial_workflow_state",
    "ingest_completion_receipts",
    "ingest_stage_receipts",
    "ingest_stage_coverage_reports",
    "load_workflow_state",
    "mark_stage_approved",
    "mark_stage_failed",
    "mark_stage_started",
    "mark_stage_succeeded",
    "next_ready_or_blocked_stage",
    "refresh_workflow_state",
    "write_workflow_state",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Execution adapter for ready model-training workflow stages."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .agent_error_handler import handle_server_error
from .control_plane import TaskSystemError
from .model_training_state import (
    DEFAULT_WORKFLOW_STATE_PATH,
    StageProgress,
    resolve_workflow_state_path,
    WorkflowState,
    advance_workflow_state,
    mark_stage_failed,
    mark_stage_started,
    mark_stage_succeeded,
    next_ready_or_blocked_stage,
    refresh_workflow_state,
    write_workflow_state,
)
from .model_training_workflow import build_model_training_workflow_plan
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_RECEIPT_ROOT = Path("storage/runtime/model_training_stage_receipts")
DEFAULT_LOG_ROOT = Path("storage/runtime/model_training_stage_logs")
SAFE_OFFLINE_STAGE_TYPES = {
    "data_acquisition",
    "feature_generation",
    "model_generation",
    "model_evaluation",
    "promotion_review",
    "maintenance",
}


@dataclass(frozen=True)
class StageExecutionSummary:
    """Result of one safe offline stage execution attempt."""

    contract_type: str
    stage_id: str
    status: str
    command: list[str]
    return_code: int | None
    receipt_path: str | None
    stdout_path: str | None
    stderr_path: str | None
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    reason: str | None = None
    agent_error_request_path: str | None = None
    agent_error_diagnosis_path: str | None = None
    agent_error_number: int | None = None
    agent_error_ref: str | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _exclusive_month_start(month: str) -> str:
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number == 12:
        year += 1
        month_number = 1
    else:
        month_number += 1
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00"


def _month_start(month: str) -> str:
    return f"{month}-01T00:00:00-05:00"


def _resolve_command_placeholders(command: list[str], *, start_month: str, end_month: str) -> list[str]:
    replacements = {
        "${START_MONTH}": start_month,
        "${END_MONTH}": end_month,
        "${START_MONTH_START_ET}": _month_start(start_month),
        "${END_MONTH_EXCLUSIVE_START_ET}": _exclusive_month_start(end_month),
    }
    resolved = []
    for token in command:
        text = token
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        resolved.append(text)
    return resolved


def _split_env(command: list[str]) -> tuple[dict[str, str], list[str]]:
    env: dict[str, str] = {}
    argv: list[str] = []
    for token in command:
        if not argv and "=" in token and not token.startswith("--"):
            key, value = token.split("=", 1)
            if key.isidentifier():
                env[key] = value
                continue
        argv.append(token)
    return env, argv


def _cwd_for_stage(stage: StageProgress, *, manager_root: Path, trading_data_root: Path, trading_model_root: Path) -> Path:
    command_text = " ".join(stage.command)
    argv = _split_env(stage.command)[1]
    if len(argv) >= 2 and argv[1].startswith("scripts/tasks/"):
        return manager_root
    if "trading-data" in command_text or stage.stage_type == "feature_generation":
        return trading_data_root
    if "trading-model" in command_text or stage.stage_type in {"model_generation", "model_evaluation", "promotion_review"}:
        return trading_model_root
    return manager_root


def _validate_safe_stage(stage: StageProgress) -> None:
    if stage.status != "ready":
        raise TaskSystemError(f"stage is not ready: {stage.stage_id} status={stage.status}")
    if stage.approval_gate_required:
        raise TaskSystemError(f"stage requires approval and cannot use safe offline executor: {stage.stage_id}")
    if stage.stage_type not in SAFE_OFFLINE_STAGE_TYPES:
        raise TaskSystemError(f"stage type is not safe offline executable: {stage.stage_type}")
    if stage.stage_type == "data_acquisition" and any(
        token.endswith("dispatch_and_reconcile_provider_stage.py")
        or token.endswith("dispatch_provider_acquisition.py")
        or token.endswith("dispatch_event_feed_backfill.py")
        for token in stage.command
    ):
        raise TaskSystemError(f"provider-dispatch stage requires the autonomous provider-stage controller: {stage.stage_id}")
    if stage.stage_type == "data_acquisition" and not any(
        token.endswith("materialize_layer_three_target_state_inputs.py")
        or token.endswith("materialize_layer_four_event_overlay_inputs.py")
        or token.endswith("review_layer_eight_option_expression_gate.py")
        for token in stage.command
    ):
        raise TaskSystemError(f"data_acquisition stage is not an allowed materialization/review command: {stage.stage_id}")
    if not stage.command:
        raise TaskSystemError(f"stage has no command: {stage.stage_id}")
    if any("${" in token for token in stage.command):
        raise TaskSystemError(f"stage command still contains unresolved placeholder: {stage.stage_id}")


def _extract_json_from_stdout(stdout: str) -> Mapping[str, Any]:
    text = stdout.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _provider_call_count_from_stdout(stdout: str) -> int:
    parsed = _extract_json_from_stdout(stdout)
    if not parsed:
        return 0
    value = parsed.get("provider_calls")
    if value is None and isinstance(parsed.get("dispatch"), Mapping):
        value = parsed["dispatch"].get("provider_calls")
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _receipt_payload(
    *,
    stage: StageProgress,
    summary: StageExecutionSummary,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    return {
        "contract_type": "component_completion_receipt",
        "manager_stage_id": stage.stage_id,
        "stage_type": stage.stage_type,
        "status": summary.status,
        "started_at": started_at,
        "completed_at": completed_at,
        "runs": [
            {
                "run_id": f"{stage.stage_id}.{started_at.replace(':', '').replace('+00:00', 'Z')}",
                "status": summary.status,
                "command": summary.command,
                "return_code": summary.return_code,
                "stdout_path": summary.stdout_path,
                "stderr_path": summary.stderr_path,
                "output_refs": [],
            }
        ],
        "provider_calls": summary.provider_calls,
        "model_activation_performed": summary.model_activation_performed,
        "broker_execution_performed": summary.broker_execution_performed,
    }


def execute_stage_process(
    stage: StageProgress,
    *,
    manager_root: Path = Path("/root/projects/trading-manager"),
    trading_data_root: Path = Path("/root/projects/trading-data"),
    trading_model_root: Path = Path("/root/projects/trading-model"),
    receipt_root: Path = DEFAULT_RECEIPT_ROOT,
    log_root: Path = DEFAULT_LOG_ROOT,
) -> StageExecutionSummary:
    """Execute one already-ready safe offline stage and write a receipt."""

    _validate_safe_stage(stage)
    env_assignments, argv = _split_env(stage.command)
    if not argv:
        raise TaskSystemError(f"stage command has no argv after env parsing: {stage.stage_id}")
    cwd = _cwd_for_stage(stage, manager_root=manager_root, trading_data_root=trading_data_root, trading_model_root=trading_model_root)
    stage_log_root = log_root / stage.stage_id.replace(".", "__")
    stage_receipt_root = receipt_root / stage.stage_id.replace(".", "__")
    stage_log_root.mkdir(parents=True, exist_ok=True)
    stage_receipt_root.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC).isoformat()
    stamp = started.replace(":", "").replace("+00:00", "Z")
    stdout_path = stage_log_root / f"{stamp}.stdout.log"
    stderr_path = stage_log_root / f"{stamp}.stderr.log"
    result = subprocess.run(
        argv,
        cwd=cwd,
        env={**os.environ, **env_assignments},
        text=True,
        capture_output=True,
        check=False,
    )
    completed = datetime.now(UTC).isoformat()
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    status = "succeeded" if result.returncode == 0 else "failed"
    receipt_path = stage_receipt_root / f"{stamp}.receipt.json"
    provider_calls = _provider_call_count_from_stdout(result.stdout) if result.returncode == 0 else 0
    agent_error_result: Mapping[str, Any] | None = None
    if result.returncode != 0:
        agent_error_result = handle_server_error(
            source_component="trading-manager.stage_executor",
            source_repo="trading-manager",
            error_scope="server.model_training_stage",
            error_kind="stage_command_failed",
            severity="error",
            summary=f"model training stage {stage.stage_id} command returned non-zero status",
            command=stage.command,
            exit_code=result.returncode,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            working_directory=str(cwd),
            evidence_refs=[f"manager_stage:{stage.stage_id}"],
            output_root=log_root.parent / "agent_error_handling",
            call_agent=bool(os.environ.get("MANAGER_AGENT_ERROR_AUTOCALL")),
        )
    summary = StageExecutionSummary(
        contract_type="manager_stage_execution_summary",
        stage_id=stage.stage_id,
        status=status,
        command=stage.command,
        return_code=result.returncode,
        receipt_path=str(receipt_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        provider_calls=provider_calls,
        reason=None if result.returncode == 0 else "stage command returned non-zero status",
        agent_error_request_path=str(agent_error_result.get("request_path")) if agent_error_result else None,
        agent_error_diagnosis_path=str(agent_error_result.get("diagnosis_path")) if agent_error_result else None,
        agent_error_number=int(agent_error_result["error_number"]) if agent_error_result and agent_error_result.get("error_number") else None,
        agent_error_ref=str(agent_error_result.get("error_ref")) if agent_error_result and agent_error_result.get("error_ref") else None,
    )
    receipt_path.write_text(
        json.dumps(_receipt_payload(stage=stage, summary=summary, started_at=started, completed_at=completed), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return summary


def execute_next_ready_stage(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    state_path: Path | None = None,
    manager_root: Path = Path("/root/projects/trading-manager"),
    trading_data_root: Path = Path("/root/projects/trading-data"),
    trading_model_root: Path = Path("/root/projects/trading-model"),
    receipt_root: Path = DEFAULT_RECEIPT_ROOT,
    log_root: Path = DEFAULT_LOG_ROOT,
    selected_target_symbol: str | None = None,
    foundation_catch_up_only: bool = True,
    write: bool = False,
) -> tuple[StageExecutionSummary, WorkflowState]:
    state_path = resolve_workflow_state_path(start_month, state_path, storage_root=storage_root)
    state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=state_path,
        selected_target_symbol=selected_target_symbol,
        foundation_catch_up_only=foundation_catch_up_only,
        write=False,
    )
    stage = next_ready_or_blocked_stage(state)
    if stage is None:
        raise TaskSystemError("no ready or approval-blocked workflow stage")
    if stage.status != "ready":
        raise TaskSystemError(f"next stage is not executable without approval: {stage.stage_id}")
    stage_id = stage.stage_id
    state = mark_stage_started(state, stage_id=stage_id, reason="stage execution started by manager stage executor")
    if write:
        write_workflow_state(state_path, state)
    stage = next(updated_stage for updated_stage in state.stages if updated_stage.stage_id == stage_id)
    stage = replace(stage, command=_resolve_command_placeholders(stage.command, start_month=start_month, end_month=end_month))
    summary = execute_stage_process(
        stage,
        manager_root=manager_root,
        trading_data_root=trading_data_root,
        trading_model_root=trading_model_root,
        receipt_root=receipt_root,
        log_root=log_root,
    )
    updated = state
    if summary.status == "succeeded" and summary.receipt_path:
        updated = mark_stage_succeeded(
            state,
            stage_id=stage.stage_id,
            receipt_ref=summary.receipt_path,
            reason="stage completed by manager stage executor",
        )
        plan = build_model_training_workflow_plan(
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            selected_target_symbol=selected_target_symbol,
            foundation_catch_up_only=foundation_catch_up_only,
        )
        updated = refresh_workflow_state(updated, plan=plan)
    elif summary.status == "failed":
        updated = mark_stage_failed(
            state,
            stage_id=stage.stage_id,
            receipt_ref=summary.receipt_path,
            reason=summary.reason or "stage command returned non-zero status",
        )
    if write:
        write_workflow_state(state_path, updated)
    return summary, updated


def write_stage_execution_summary(summary: StageExecutionSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the next ready model-training workflow stage.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--state-path", type=Path, default=None, help="Workflow checkpoint path; defaults to storage/runtime/model_training_workflow_state_YYYY-MM.json.")
    parser.add_argument("--manager-root", type=Path, default=Path("/root/projects/trading-manager"))
    parser.add_argument("--trading-data-root", type=Path, default=Path("/root/projects/trading-data"))
    parser.add_argument("--trading-model-root", type=Path, default=Path("/root/projects/trading-model"))
    parser.add_argument("--receipt-root", type=Path, default=DEFAULT_RECEIPT_ROOT)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for Layer 3+ six-month dataset units.")
    parser.add_argument(
        "--allow-post-foundation-model-stages",
        action="store_true",
        help="Allow fold-scoped model generation/evaluation/promotion stages after Layer 1/2 substrate readiness.",
    )
    parser.add_argument("--write", action="store_true", help="Persist successful stage progress to the workflow state checkpoint.")
    args = parser.parse_args(argv)
    summary, _state = execute_next_ready_stage(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        state_path=args.state_path,
        manager_root=args.manager_root,
        trading_data_root=args.trading_data_root,
        trading_model_root=args.trading_model_root,
        receipt_root=args.receipt_root,
        log_root=args.log_root,
        selected_target_symbol=args.target_symbol,
        foundation_catch_up_only=not args.allow_post_foundation_model_stages,
        write=args.write,
    )
    write_stage_execution_summary(summary, output=sys.stdout)
    return 0 if summary.status == "succeeded" else 1


__all__ = [
    "SAFE_OFFLINE_STAGE_TYPES",
    "StageExecutionSummary",
    "_resolve_command_placeholders",
    "execute_next_ready_stage",
    "execute_stage_process",
    "write_stage_execution_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

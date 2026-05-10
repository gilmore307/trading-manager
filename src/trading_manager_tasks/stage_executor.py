"""Safe execution adapter for ready offline model-training workflow stages."""

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

from .control_plane import TaskSystemError
from .model_training_state import (
    DEFAULT_WORKFLOW_STATE_PATH,
    StageProgress,
    WorkflowState,
    advance_workflow_state,
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
    "feature_generation",
    "model_generation",
    "model_evaluation",
    "promotion_review_preparation",
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

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_command_placeholders(command: list[str], *, start_month: str, end_month: str) -> list[str]:
    replacements = {"${START_MONTH}": start_month, "${END_MONTH}": end_month}
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
    if "trading-model" in command_text or stage.stage_type in {"model_generation", "model_evaluation", "promotion_review_preparation"}:
        return trading_model_root
    return manager_root


def _validate_safe_stage(stage: StageProgress) -> None:
    if stage.status != "ready":
        raise TaskSystemError(f"stage is not ready: {stage.stage_id} status={stage.status}")
    if stage.approval_gate_required:
        raise TaskSystemError(f"stage requires approval and cannot use safe offline executor: {stage.stage_id}")
    if stage.stage_type not in SAFE_OFFLINE_STAGE_TYPES:
        raise TaskSystemError(f"stage type is not safe offline executable: {stage.stage_type}")
    if not stage.command:
        raise TaskSystemError(f"stage has no command: {stage.stage_id}")
    if any("${" in token for token in stage.command):
        raise TaskSystemError(f"stage command still contains unresolved placeholder: {stage.stage_id}")


def _receipt_payload(
    *,
    stage: StageProgress,
    summary: StageExecutionSummary,
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    return {
        "contract_type": "component_completion_receipt_v1",
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
        "provider_calls": 0,
        "model_activation_performed": False,
        "broker_execution_performed": False,
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
    summary = StageExecutionSummary(
        contract_type="manager_stage_execution_summary_v1",
        stage_id=stage.stage_id,
        status=status,
        command=stage.command,
        return_code=result.returncode,
        receipt_path=str(receipt_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        reason=None if result.returncode == 0 else "safe offline command returned non-zero status",
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
    state_path: Path = DEFAULT_WORKFLOW_STATE_PATH,
    manager_root: Path = Path("/root/projects/trading-manager"),
    trading_data_root: Path = Path("/root/projects/trading-data"),
    trading_model_root: Path = Path("/root/projects/trading-model"),
    receipt_root: Path = DEFAULT_RECEIPT_ROOT,
    log_root: Path = DEFAULT_LOG_ROOT,
    write: bool = False,
) -> tuple[StageExecutionSummary, WorkflowState]:
    state = advance_workflow_state(
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        state_path=state_path,
        write=False,
    )
    stage = next_ready_or_blocked_stage(state)
    if stage is None:
        raise TaskSystemError("no ready or approval-blocked workflow stage")
    if stage.status != "ready":
        raise TaskSystemError(f"next stage is not executable without approval: {stage.stage_id}")
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
            reason="stage completed by safe offline executor",
        )
        plan = build_model_training_workflow_plan(start_month=start_month, end_month=end_month, storage_root=storage_root)
        updated = refresh_workflow_state(updated, plan=plan)
    if write:
        write_workflow_state(state_path, updated)
    return summary, updated


def write_stage_execution_summary(summary: StageExecutionSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the next ready safe offline model-training workflow stage.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_WORKFLOW_STATE_PATH)
    parser.add_argument("--manager-root", type=Path, default=Path("/root/projects/trading-manager"))
    parser.add_argument("--trading-data-root", type=Path, default=Path("/root/projects/trading-data"))
    parser.add_argument("--trading-model-root", type=Path, default=Path("/root/projects/trading-model"))
    parser.add_argument("--receipt-root", type=Path, default=DEFAULT_RECEIPT_ROOT)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
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

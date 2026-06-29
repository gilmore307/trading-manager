"""Execution adapter for ready model-training workflow stages."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .agent_error_handler import _env_truthy, handle_server_error
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
from .task_progress import DEFAULT_TASK_PROGRESS_ROOT, clear_worker_task_progress, progress_contract_for_stage, worker_progress_path, write_task_progress_node

DEFAULT_RECEIPT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_training_stage_receipts"
DEFAULT_LOG_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_training_stage_logs"
DEFAULT_STAGE_EXECUTION_TIMEOUT_SECONDS = 60 * 30
DEFAULT_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS = 60 * 60 * 4
DEFAULT_STAGE_PROGRESS_STALL_SECONDS = 60 * 10
DEFAULT_STAGE_PROGRESS_POLL_SECONDS = 5.0
LONG_DATABASE_STAGE_IDS = {
    "model_02_target_state.feature_generation",
    "model_05_option_expression.feature_generation",
}
SAFE_OFFLINE_STAGE_TYPES = {
    "data_acquisition",
    "feature_generation",
    "model_training",
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


def _stage_progress_worker_id(*, start_month: str, end_month: str) -> str:
    if start_month != end_month:
        return "model_worker_1"
    safe_month = start_month.replace("-", "_")
    return f"month_ingest_worker_stage_executor_{safe_month}"


def _stage_progress_unit_label(stage: StageProgress) -> str:
    if stage.stage_id == "model_03_event_state.data_acquisition":
        return "event substrate"
    if stage.stage_id == "model_05_option_expression.option_chain_data_acquisition":
        return "option source"
    return progress_contract_for_stage(stage.stage_id, fallback_unit_label="stage step")["unit_label"]


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


def _resolve_python_argv(argv: list[str]) -> list[str]:
    if argv and argv[0] in {"python", "python3"}:
        return [sys.executable, *argv[1:]]
    return argv


def _cwd_for_stage(stage: StageProgress, *, manager_root: Path, trading_data_root: Path, trading_model_root: Path) -> Path:
    command_text = " ".join(stage.command)
    argv = _split_env(stage.command)[1]
    if len(argv) >= 2 and argv[1].startswith("scripts/tasks/"):
        return manager_root
    if "trading-data" in command_text or stage.stage_type == "feature_generation":
        return trading_data_root
    if "trading-model" in command_text or stage.stage_type in {"model_training", "model_generation", "model_evaluation", "promotion_review"}:
        return trading_model_root
    return manager_root


def _contains_runtime_model_rows_output(command: list[str]) -> bool:
    for index, token in enumerate(command):
        if token in {"--output", "--output-jsonl"} and index + 1 < len(command):
            output_path = command[index + 1]
            if "model_rows" in output_path and output_path.endswith(".jsonl"):
                return True
        if "model_rows" in token and token.endswith(".jsonl"):
            return True
    return False


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
        or token.endswith("materialize_layer_four_event_observation_inputs.py")
        for token in stage.command
    ):
        raise TaskSystemError(f"data_acquisition stage is not an allowed materialization/review command: {stage.stage_id}")
    if not stage.command:
        raise TaskSystemError(f"stage has no command: {stage.stage_id}")
    if any("${" in token for token in stage.command):
        raise TaskSystemError(f"stage command still contains unresolved placeholder: {stage.stage_id}")
    if _contains_runtime_model_rows_output(stage.command):
        raise TaskSystemError(f"stage command attempts to write deprecated runtime model_rows JSONL output: {stage.stage_id}")


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
        "dataset_split": dict(stage.dataset_split) if stage.dataset_split is not None else None,
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


def _parse_json_object(text: str | None) -> Mapping[str, Any]:
    if not text:
        return {}
    try:
        parsed = json.loads(text.strip())
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _load_agent_diagnosis(agent_error_result: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not agent_error_result:
        return {}
    diagnosis_path = agent_error_result.get("diagnosis_path")
    if not diagnosis_path:
        return {}
    try:
        parsed = json.loads(Path(str(diagnosis_path)).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _agent_diagnosis_recommends_retry(agent_error_result: Mapping[str, Any] | None) -> bool:
    diagnosis = _load_agent_diagnosis(agent_error_result)
    if diagnosis.get("status") != "completed":
        return False
    payload = _parse_json_object(str(diagnosis.get("stdout") or ""))
    diagnosis_status = str(payload.get("diagnosis_status") or "").lower()
    retry_recommendation = str(payload.get("retry_recommendation") or "").lower()
    if not diagnosis_status.startswith(("fixed", "repaired")):
        return False
    if "do_not_retry" in retry_recommendation or "manual_review" in retry_recommendation or "blocked" in retry_recommendation:
        return False
    return "retry" in retry_recommendation


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _stage_timeout_seconds(stage: StageProgress) -> int:
    if stage.stage_id in LONG_DATABASE_STAGE_IDS:
        long_default = max(
            _env_int("TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS", DEFAULT_STAGE_EXECUTION_TIMEOUT_SECONDS),
            DEFAULT_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS,
        )
        return _env_int("TRADING_MANAGER_LONG_DATABASE_STAGE_EXECUTION_TIMEOUT_SECONDS", long_default)
    return _env_int("TRADING_MANAGER_STAGE_EXECUTION_TIMEOUT_SECONDS", DEFAULT_STAGE_EXECUTION_TIMEOUT_SECONDS)


def _progress_marker(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


def _stop_stage_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def _run_stage_subprocess_with_progress_guard(
    argv: list[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    stdout_path: Path,
    stderr_path: Path,
    progress_path: Path,
    timeout_seconds: int,
    stall_seconds: float | None = None,
) -> tuple[int | None, str | None]:
    """Run a stage command while enforcing timeout and active-progress freshness."""

    if stall_seconds is None:
        stall_seconds = _env_float("TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS", DEFAULT_STAGE_PROGRESS_STALL_SECONDS)
    poll_seconds = _env_float("TRADING_MANAGER_STAGE_PROGRESS_POLL_SECONDS", DEFAULT_STAGE_PROGRESS_POLL_SECONDS)
    poll_seconds = max(0.05, poll_seconds)
    started_monotonic = time.monotonic()
    last_progress_monotonic = started_monotonic
    last_marker = _progress_marker(progress_path)
    with stdout_path.open("w", encoding="utf-8") as stdout_handle, stderr_path.open("w", encoding="utf-8") as stderr_handle:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=dict(env),
            text=True,
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
        while True:
            return_code = process.poll()
            if return_code is not None:
                return return_code, None
            now = time.monotonic()
            marker = _progress_marker(progress_path)
            if marker is not None and marker != last_marker:
                last_marker = marker
                last_progress_monotonic = now
            if timeout_seconds > 0 and now - started_monotonic >= timeout_seconds:
                _stop_stage_process(process)
                return None, f"stage command exceeded timeout_seconds={timeout_seconds}"
            if stall_seconds > 0 and now - last_progress_monotonic >= stall_seconds:
                _stop_stage_process(process)
                return None, f"stage progress stalled for timeout_seconds={stall_seconds:g}"
            sleep_for = poll_seconds
            if timeout_seconds > 0:
                sleep_for = min(sleep_for, max(0.05, timeout_seconds - (now - started_monotonic)))
            if stall_seconds > 0:
                sleep_for = min(sleep_for, max(0.05, stall_seconds - (now - last_progress_monotonic)))
            time.sleep(sleep_for)


def _stage_progress_stall_seconds(stage: StageProgress) -> float:
    if stage.stage_id in LONG_DATABASE_STAGE_IDS:
        return 0.0
    return _env_float("TRADING_MANAGER_STAGE_PROGRESS_STALL_SECONDS", DEFAULT_STAGE_PROGRESS_STALL_SECONDS)


def execute_stage_process(
    stage: StageProgress,
    *,
    manager_root: Path = Path("/root/projects/trading-manager"),
    trading_data_root: Path = Path("/root/projects/trading-data"),
    trading_model_root: Path = Path("/root/projects/trading-model"),
    receipt_root: Path = DEFAULT_RECEIPT_ROOT,
    log_root: Path = DEFAULT_LOG_ROOT,
    progress_root: Path | None = None,
    task_uid: str | None = None,
    worker_id: str = "stage_executor",
    repair_retry_attempted: bool = False,
) -> StageExecutionSummary:
    """Execute one already-ready safe offline stage and write a receipt."""

    _validate_safe_stage(stage)
    env_assignments, argv = _split_env(stage.command)
    if not argv:
        raise TaskSystemError(f"stage command has no argv after env parsing: {stage.stage_id}")
    argv = _resolve_python_argv(argv)
    execution_command = [f"{key}={value}" for key, value in env_assignments.items()] + argv
    cwd = _cwd_for_stage(stage, manager_root=manager_root, trading_data_root=trading_data_root, trading_model_root=trading_model_root)
    progress_root = progress_root or DEFAULT_TASK_PROGRESS_ROOT
    task_uid = task_uid or f"{stage.dataset_unit.start_month if stage.dataset_unit else 'unscheduled'}:{stage.stage_id}"
    stage_log_root = log_root / stage.stage_id.replace(".", "__")
    stage_receipt_root = receipt_root / stage.stage_id.replace(".", "__")
    stage_log_root.mkdir(parents=True, exist_ok=True)
    stage_receipt_root.mkdir(parents=True, exist_ok=True)
    started = datetime.now(UTC).isoformat()
    stamp = started.replace(":", "").replace("+00:00", "Z")
    stdout_path = stage_log_root / f"{stamp}.stdout.log"
    stderr_path = stage_log_root / f"{stamp}.stderr.log"
    progress_path = worker_progress_path(progress_root, worker_id)
    write_task_progress_node(
        progress_root=progress_root,
        worker_id=worker_id,
        task_uid=task_uid,
        stage_id=stage.stage_id,
        status="running",
        unit_label=_stage_progress_unit_label(stage),
        node_id="stage_started",
        node_label="Stage process started",
        extra={
            "progress_basis": progress_contract_for_stage(stage.stage_id)["progress_basis"],
            **({"dataset_split": stage.dataset_split} if stage.dataset_split is not None else {}),
        },
    )
    timeout_seconds = _stage_timeout_seconds(stage)
    run_env = {
        **os.environ,
        **env_assignments,
        "TRADING_MANAGER_TASK_PROGRESS_ROOT": str(progress_root),
        "TRADING_MANAGER_TASK_PROGRESS_PATH": str(progress_path),
        "TRADING_MANAGER_TASK_PROGRESS_WORKER_ID": worker_id,
        "TRADING_MANAGER_TASK_PROGRESS_TASK_UID": task_uid,
        "TRADING_MANAGER_TASK_PROGRESS_STAGE_ID": stage.stage_id,
        **(
            {
                "TRADING_MODEL_DATASET_SPLIT_NAME": str(stage.dataset_split["split_name"]),
                "TRADING_MODEL_DATASET_SPLIT_POLICY": str(stage.dataset_split["split_policy"]),
            }
            if stage.dataset_split is not None
            else {}
        ),
    }
    return_code, guard_failure_reason = _run_stage_subprocess_with_progress_guard(
        argv,
        cwd=cwd,
        env=run_env,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        progress_path=progress_path,
        timeout_seconds=timeout_seconds,
        stall_seconds=_stage_progress_stall_seconds(stage),
    )
    completed = datetime.now(UTC).isoformat()
    stdout = stdout_path.read_text(encoding="utf-8") if stdout_path.exists() else ""
    stderr = stderr_path.read_text(encoding="utf-8") if stderr_path.exists() else ""
    failure_reason = guard_failure_reason or "stage command returned non-zero status"
    if guard_failure_reason:
        stderr = f"{stderr}\n{guard_failure_reason}\n"
        stderr_path.write_text(stderr, encoding="utf-8")
    status = "succeeded" if return_code == 0 else "failed"
    receipt_path = stage_receipt_root / f"{stamp}.receipt.json"
    provider_calls = _provider_call_count_from_stdout(stdout) if return_code == 0 else 0
    agent_error_result: Mapping[str, Any] | None = None
    if return_code != 0 and not repair_retry_attempted:
        agent_error_result = handle_server_error(
            source_component="trading-manager.stage_executor",
            source_repo="trading-manager",
            error_scope="server.model_training_stage",
            error_kind="stage_progress_stalled" if guard_failure_reason and "progress stalled" in guard_failure_reason else "stage_command_failed",
            severity="error",
            summary=f"model training stage {stage.stage_id} {failure_reason}",
            command=execution_command,
            exit_code=return_code,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            working_directory=str(cwd),
            evidence_refs=[f"manager_stage:{stage.stage_id}", f"task_progress:{progress_path}"],
            output_root=log_root.parent / "agent_error_handling",
            call_agent=_env_truthy("MANAGER_AGENT_ERROR_AUTOCALL"),
            catalog_storage=os.environ.get("MANAGER_AGENT_ERROR_CATALOG_STORAGE", "sql"),
        )
        if _agent_diagnosis_recommends_retry(agent_error_result):
            retry_summary = execute_stage_process(
                stage,
                manager_root=manager_root,
                trading_data_root=trading_data_root,
                trading_model_root=trading_model_root,
                receipt_root=receipt_root,
                log_root=log_root,
                progress_root=progress_root,
                task_uid=task_uid,
                worker_id=worker_id,
                repair_retry_attempted=True,
            )
            if retry_summary.status == "succeeded":
                return replace(
                    retry_summary,
                    reason="stage completed after automatic repair retry",
                    agent_error_request_path=str(agent_error_result.get("request_path")),
                    agent_error_diagnosis_path=str(agent_error_result.get("diagnosis_path")),
                    agent_error_number=int(agent_error_result["error_number"]) if agent_error_result.get("error_number") else None,
                    agent_error_ref=str(agent_error_result.get("error_ref")) if agent_error_result.get("error_ref") else None,
                )
    summary = StageExecutionSummary(
        contract_type="manager_stage_execution_summary",
        stage_id=stage.stage_id,
        status=status,
        command=execution_command,
        return_code=return_code,
        receipt_path=str(receipt_path),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        provider_calls=provider_calls,
        reason=None if return_code == 0 else failure_reason,
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
    clear_worker_task_progress(progress_root=progress_root, worker_id=worker_id)
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
    progress_root: Path | None = None,
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
    task_uid = f"{start_month if start_month == end_month else f'{start_month}..{end_month}'}:{stage.stage_id}"
    summary = execute_stage_process(
        stage,
        manager_root=manager_root,
        trading_data_root=trading_data_root,
        trading_model_root=trading_model_root,
        receipt_root=receipt_root,
        log_root=log_root,
        progress_root=progress_root or storage_root / "runtime" / "task_progress",
        task_uid=task_uid,
        worker_id=_stage_progress_worker_id(start_month=start_month, end_month=end_month),
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
    parser.add_argument("--state-path", type=Path, default=None, help="Workflow checkpoint path; defaults to the manager runtime root under trading-storage/storage/02_control_plane/runtime.")
    parser.add_argument("--manager-root", type=Path, default=Path("/root/projects/trading-manager"))
    parser.add_argument("--trading-data-root", type=Path, default=Path("/root/projects/trading-data"))
    parser.add_argument("--trading-model-root", type=Path, default=Path("/root/projects/trading-model"))
    parser.add_argument("--receipt-root", type=Path, default=DEFAULT_RECEIPT_ROOT)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    parser.add_argument("--progress-root", type=Path, default=None)
    parser.add_argument("--target-symbol", help="Required task-scope target symbol for M02+ 12+3+3 walk-forward dataset units.")
    parser.add_argument(
        "--allow-post-foundation-model-stages",
        action="store_true",
        help="Allow fold-scoped model generation/evaluation/promotion stages after M01/M02 substrate readiness.",
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
        progress_root=args.progress_root,
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
    "_stage_progress_worker_id",
    "execute_next_ready_stage",
    "execute_stage_process",
    "write_stage_execution_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

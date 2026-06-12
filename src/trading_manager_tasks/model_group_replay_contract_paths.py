"""Manager lifecycle for replay selected-contract path acquisition.

Replay can choose a listed option after M05 feature generation. The selected
contract then needs a separate market-path source before settlement can treat
the decision as executable. This stage prepares that source without broker,
account, model-activation, or storage-lifecycle mutation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_PYTHON_EXECUTABLE = Path("/root/projects/trading-manager/.venv/bin/python")
DEFAULT_TASK_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_05_option_expression" / "selected_contract_path"
STAGE_ID = "model_group.replay_contract_paths"
SOURCE_ID = "m05_option_expression_data_acquisition_contract_path"
NEW_YORK = ZoneInfo("America/New_York")
OPTION_SYMBOL_PATTERN = re.compile(
    r"^(?P<underlying>[A-Z0-9.]+)_(?P<expiration>\d{4}-\d{2}-\d{2})_(?P<right>[CP])_(?P<strike>\d+(?:\.\d+)?)$"
)


@dataclass(frozen=True)
class ReplayContractPathRequirement:
    underlying: str
    option_symbol: str
    expiration: str
    option_right_type: str
    strike: float
    entry_time: str
    exit_time: str
    month: str
    decision_id: str

    def selected_contract(self) -> dict[str, Any]:
        return {
            "underlying": self.underlying,
            "option_symbol": self.option_symbol,
            "expiration": self.expiration,
            "option_right_type": self.option_right_type,
            "strike": self.strike,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "timeframe": "1Min",
        }


def replay_contract_path_requirements_from_decision_rows(
    decision_rows_ref: Path,
    *,
    missing_only: bool = True,
) -> tuple[ReplayContractPathRequirement, ...]:
    """Extract selected option contracts that require replay market paths."""

    requirements: list[ReplayContractPathRequirement] = []
    seen: set[tuple[str, str, str]] = set()
    with decision_rows_ref.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            option_symbol = str(row.get("selected_option_contract_ref") or "").strip().upper()
            if not option_symbol:
                continue
            if missing_only and str(row.get("option_contract_path_status") or "").strip().lower() == "available":
                continue
            entry_time = str(row.get("replay_time_pointer") or row.get("timestamp") or "").strip()
            exit_time = str(row.get("next_timestamp") or "").strip()
            if not entry_time or not exit_time:
                continue
            parsed = _parse_option_symbol(option_symbol, fallback_underlying=str(row.get("target_ref") or ""))
            if not parsed:
                continue
            key = (option_symbol, entry_time, exit_time)
            if key in seen:
                continue
            seen.add(key)
            requirements.append(
                ReplayContractPathRequirement(
                    underlying=parsed["underlying"],
                    option_symbol=option_symbol,
                    expiration=parsed["expiration"],
                    option_right_type=parsed["option_right_type"],
                    strike=float(parsed["strike"]),
                    entry_time=entry_time,
                    exit_time=exit_time,
                    month=entry_time[:7],
                    decision_id=str(row.get("decision_id") or ""),
                )
            )
    return tuple(requirements)


def run_model_group_replay_contract_paths(
    *,
    decision_rows_ref: Path,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    execute: bool = True,
    execute_provider_acquisition: bool = False,
    limit: int | None = None,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    python_executable: Path = DEFAULT_PYTHON_EXECUTABLE,
) -> SchedulerDecision:
    """Prepare or execute selected-contract market-path acquisition."""

    requirements = replay_contract_path_requirements_from_decision_rows(decision_rows_ref)
    if limit is not None:
        requirements = requirements[: max(0, limit)]
    if not requirements:
        return _decision(
            decision_status="executed",
            reason_code="model_group_replay_contract_paths_not_needed",
            reason="replay decision rows contain no selected option contracts requiring market-path acquisition",
            selected_work=STAGE_ID,
            execution_summary=_summary(decision_rows_ref=decision_rows_ref, requirements=()),
        )

    if not execute:
        return _decision(
            decision_status="ready",
            reason_code="model_group_replay_contract_paths_ready",
            reason="replay selected option contracts can be prepared for market-path acquisition",
            selected_work=STAGE_ID,
            execution_summary=_summary(decision_rows_ref=decision_rows_ref, requirements=requirements),
        )

    task_key_path = write_selected_contract_path_task_key(
        requirements,
        storage_root=storage_root,
        decision_rows_ref=decision_rows_ref,
    )
    if not execute_provider_acquisition:
        return _decision(
            decision_status="backoff",
            reason_code="model_group_replay_contract_path_provider_required",
            reason="selected option contract paths require explicit provider acquisition before clean replay can produce executable fills",
            selected_work=STAGE_ID,
            execution_summary=_summary(
                decision_rows_ref=decision_rows_ref,
                requirements=requirements,
                task_key_path=task_key_path,
                required_next_step="rerun with --execute-provider-acquisition to call the selected-contract option tracking source",
            ),
        )

    run_id = "model_group_replay_contract_paths_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    command = [
        str(python_executable),
        "-m",
        "data_source.m05_option_expression_data_acquisition_contract_path",
        str(task_key_path),
        "--run-id",
        run_id,
    ]
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    completed = subprocess.run(command, cwd=trading_data_root, env=env, capture_output=True, text=True)
    if completed.returncode != 0:
        return _decision(
            decision_status="backoff",
            reason_code="model_group_replay_contract_path_acquisition_failed",
            reason=(completed.stderr or completed.stdout or "selected-contract path acquisition failed").strip(),
            selected_work=STAGE_ID,
            provider_calls=len(requirements),
            dispatch_performed=True,
            execution_summary=_summary(
                decision_rows_ref=decision_rows_ref,
                requirements=requirements,
                task_key_path=task_key_path,
                command=command,
                runner_stdout=completed.stdout,
                runner_stderr=completed.stderr,
                return_code=completed.returncode,
            ),
        )
    return _decision(
        decision_status="executed",
        reason_code="model_group_replay_contract_paths_executed",
        reason="selected option contract market paths were acquired; replay can be retried to settle executable option fills",
        selected_work=STAGE_ID,
        provider_calls=len(requirements),
        dispatch_performed=True,
        execution_summary=_summary(
            decision_rows_ref=decision_rows_ref,
            requirements=requirements,
            task_key_path=task_key_path,
            command=command,
            runner_stdout=completed.stdout,
            runner_stderr=completed.stderr,
            return_code=completed.returncode,
        ),
    )


def write_selected_contract_path_task_key(
    requirements: Sequence[ReplayContractPathRequirement],
    *,
    storage_root: Path,
    decision_rows_ref: Path,
) -> Path:
    generated_at = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    month = requirements[0].month if requirements else "unknown"
    task_id = f"mgrreq_replay_contract_path_{month.replace('-', '_')}_{generated_at}"
    task_root = storage_root / "runtime" / "model_05_option_expression" / "selected_contract_path" / month / task_id
    task_root.mkdir(parents=True, exist_ok=True)
    task_key = {
        "task_id": task_id,
        "source": SOURCE_ID,
        "params": {
            "selected_contracts": [item.selected_contract() for item in requirements],
            "decision_rows_ref": str(decision_rows_ref),
            "thetadata_transport": "python_library",
        },
        "output_root": str(task_root),
        "manager_controls": {
            "allow_live_provider_calls": True,
            "autonomous_historical_provider_acquisition": True,
            "allowed_providers": ["thetadata"],
            "allowed_endpoint_families": ["option_primary_tracking"],
            "max_symbols": len({item.option_symbol for item in requirements}),
            "max_requests": len(requirements),
            "max_time_window": "7d",
            "timeout_seconds": 120,
            "retry_attempts": 3,
            "retry_backoff_seconds": 1,
            "broker_execution_performed": False,
            "model_activation_performed": False,
            "storage_lifecycle_mutation_performed": False,
        },
    }
    task_key_path = task_root / "task_key.json"
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return task_key_path


def _parse_option_symbol(option_symbol: str, *, fallback_underlying: str) -> dict[str, Any] | None:
    match = OPTION_SYMBOL_PATTERN.match(option_symbol)
    if not match:
        return None
    right = "CALL" if match.group("right") == "C" else "PUT"
    return {
        "underlying": (match.group("underlying") or fallback_underlying).upper(),
        "expiration": match.group("expiration"),
        "option_right_type": right,
        "strike": float(match.group("strike")),
    }


def _decision(
    *,
    decision_status: str,
    reason_code: str,
    reason: str,
    selected_work: str,
    provider_calls: int = 0,
    dispatch_performed: bool = False,
    execution_summary: dict[str, Any] | None = None,
) -> SchedulerDecision:
    now = datetime.now(UTC)
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now.astimezone(NEW_YORK).isoformat(),
        decision_status=decision_status,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=[],
        next_internal_stage=selected_work,
        provider_calls=provider_calls,
        dispatch_performed=dispatch_performed,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
    )


def _summary(
    *,
    decision_rows_ref: Path,
    requirements: Sequence[ReplayContractPathRequirement],
    task_key_path: Path | None = None,
    required_next_step: str | None = None,
    command: Sequence[str] = (),
    runner_stdout: str = "",
    runner_stderr: str = "",
    return_code: int | None = None,
) -> dict[str, Any]:
    return {
        "decision_rows_ref": str(decision_rows_ref),
        "selected_contract_requirement_count": len(requirements),
        "selected_contract_symbol_count": len({item.option_symbol for item in requirements}),
        "selected_contract_months": sorted({item.month for item in requirements}),
        "sample": [asdict(item) for item in requirements[:5]],
        "task_key_path": str(task_key_path) if task_key_path else None,
        "blocked_stage_id": SOURCE_ID if requirements else None,
        "resume_stage_id": "model_group.replay",
        "required_next_step": required_next_step,
        "command": list(command),
        "runner_stdout": runner_stdout,
        "runner_stderr": runner_stderr,
        "return_code": return_code,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-rows-ref", type=Path, required=True)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--execute-provider-acquisition", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    decision = run_model_group_replay_contract_paths(
        decision_rows_ref=args.decision_rows_ref,
        storage_root=args.storage_root,
        execute=args.execute,
        execute_provider_acquisition=args.execute_provider_acquisition,
        limit=args.limit,
    )
    print(json.dumps(asdict(decision), indent=2, sort_keys=True))
    return 0


__all__ = [
    "ReplayContractPathRequirement",
    "replay_contract_path_requirements_from_decision_rows",
    "run_model_group_replay_contract_paths",
    "write_selected_contract_path_task_key",
]

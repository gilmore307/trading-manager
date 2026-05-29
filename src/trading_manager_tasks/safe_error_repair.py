"""Reviewed safe auto-repair helpers for server error handoffs.

This module intentionally supports only narrow, deterministic repairs. Unknown
errors are diagnosed but not modified. It never calls providers, brokers, account
APIs, package managers, or arbitrary shell commands.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .agent_error_handler import AGENT_ERROR_DIAGNOSIS_CONTRACT, _stable_id
from .scheduler_locks import DEFAULT_DAEMON_LOCK_PATH, inspect_scheduler_lock


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_path(raw: str, *, working_directory: str | None) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    base = Path(working_directory) if working_directory else Path.cwd()
    return base / path


def _extract_lock_path(request: Mapping[str, Any]) -> str | None:
    haystack = "\n".join(
        str(request.get(key) or "")
        for key in ("summary", "stderr_excerpt", "stdout_excerpt")
    )
    match = re.search(r"scheduler daemon lock is active: ([^\s]+)", haystack)
    if match:
        return match.group(1)
    if request.get("source_component") == "trading-manager.historical_scheduler_daemon":
        return str(DEFAULT_DAEMON_LOCK_PATH)
    return None


def repair_scheduler_dead_pid_lock(request: Mapping[str, Any]) -> dict[str, Any] | None:
    """Remove a scheduler lock only when it records a dead PID."""

    if request.get("source_component") != "trading-manager.historical_scheduler_daemon":
        return None
    if "scheduler daemon lock is active" not in str(request.get("summary") or ""):
        return None
    raw_lock_path = _extract_lock_path(request)
    if not raw_lock_path:
        return {
            "repair_status": "not_repaired",
            "repair_kind": "scheduler_dead_pid_lock",
            "reason": "could not resolve lock path",
            "files_changed": [],
        }
    lock_path = _resolve_path(raw_lock_path, working_directory=str(request.get("working_directory") or ""))
    if not lock_path.exists():
        return {
            "repair_status": "no_action_needed",
            "repair_kind": "scheduler_dead_pid_lock",
            "reason": "lock path no longer exists",
            "files_changed": [],
        }
    inspection = inspect_scheduler_lock(lock_path)
    if inspection.status not in {"dead_pid"}:
        return {
            "repair_status": "not_repaired",
            "repair_kind": "scheduler_dead_pid_lock",
            "reason": inspection.reason or f"lock status is {inspection.status}",
            "files_changed": [],
        }
    lock_path.unlink(missing_ok=True)
    return {
        "repair_status": "repaired",
        "repair_kind": "scheduler_dead_pid_lock",
        "reason": f"removed dead-PID scheduler lock for pid {inspection.pid}",
        "files_changed": [str(lock_path)],
        "verification": "lock file removed only after confirming recorded PID was not running",
    }


def build_diagnosis(request: Mapping[str, Any]) -> dict[str, Any]:
    started = _now_utc()
    repair = repair_scheduler_dead_pid_lock(request)
    if repair is None:
        repair = {
            "repair_status": "not_supported",
            "repair_kind": "unclassified",
            "reason": "no reviewed deterministic auto-repair is registered for this error fingerprint",
            "files_changed": [],
        }
    completed = _now_utc()
    report = {
        "diagnosis_status": "completed",
        "root_cause": request.get("summary"),
        "repair_attempted": repair["repair_status"] in {"repaired", "not_repaired", "no_action_needed"},
        "repair": repair,
        "retry_recommendation": "retry after repair" if repair.get("repair_status") == "repaired" else "manual review or wait for next scheduler tick",
        "blockers": [] if repair.get("repair_status") in {"repaired", "no_action_needed"} else [repair.get("reason")],
    }
    stdout = json.dumps(report, sort_keys=True)
    return {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request.get("request_id"), started, stdout),
        "request_ref": request.get("request_id"),
        "agent_ref": request.get("agent_ref"),
        "runner_command": "safe_error_repair",
        "status": "completed",
        "return_code": 0,
        "stdout": stdout,
        "stderr": "",
        "started_at_utc": started,
        "completed_at_utc": completed,
    }


def main(argv: list[str] | None = None, *, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    parser = argparse.ArgumentParser(description="Run reviewed deterministic safe repairs for server error requests.")
    parser.parse_args(argv)
    request = json.load(stdin)
    diagnosis = build_diagnosis(request)
    stdout.write(json.dumps(diagnosis, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

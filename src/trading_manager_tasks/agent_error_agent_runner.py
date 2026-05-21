"""OpenClaw-agent runner for server error handoffs.

The deterministic safe-repair runner is intentionally narrow. This runner is
the actual agent bridge: it passes the standard error request to OpenClaw's
default project agent and wraps the resulting turn in the existing
agent_error_diagnosis contract.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any, Mapping, TextIO

from .agent_error_handler import AGENT_ERROR_DIAGNOSIS_CONTRACT, _stable_id


DEFAULT_AGENT_ID = "trader"
DEFAULT_TIMEOUT_SECONDS = 1800


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return max(1, int(value))


def _agent_message(request: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "Handle this server error request as an internal project repair task.",
            "Use the workspace server-error-repair skill if available.",
            "Use the supplied safety boundaries. Diagnose the root cause, make safe repository/config fixes when appropriate, run verification, and report what changed.",
            "Autonomous repair is allowed for bounded internal repository bugs. Provider calls, broker/account mutation, destructive storage changes, model-output writes, runtime stage writes, package/system changes, and live service restarts require a separate gate.",
            "Do not deliver a user-facing chat reply from this run; return strict JSON matching the server-error-repair final output contract to the caller.",
            "",
            str(request.get("agent_prompt") or json.dumps(dict(request), indent=2, sort_keys=True)),
        ]
    )


def run_openclaw_agent_for_error(request: Mapping[str, Any]) -> dict[str, Any]:
    started = _now_utc()
    agent_id = os.environ.get("MANAGER_AGENT_ERROR_AGENT_ID", DEFAULT_AGENT_ID).strip() or DEFAULT_AGENT_ID
    timeout_seconds = _env_int("MANAGER_AGENT_ERROR_AGENT_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)
    thinking = os.environ.get("MANAGER_AGENT_ERROR_AGENT_THINKING", "high").strip()
    cmd = [
        "openclaw",
        "agent",
        "--agent",
        agent_id,
        "--message",
        _agent_message(request),
        "--json",
        "--timeout",
        str(timeout_seconds),
    ]
    if thinking:
        cmd.extend(["--thinking", thinking])
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_seconds + 30, check=False)
    completed = _now_utc()
    status = "completed" if result.returncode == 0 else "agent_call_failed"
    diagnosis = {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request.get("request_id"), started, result.returncode, result.stdout, result.stderr),
        "request_ref": request.get("request_id"),
        "agent_ref": request.get("agent_ref") or agent_id,
        "runner_command": "openclaw_agent",
        "status": status,
        "return_code": result.returncode,
        "stdout": result.stdout[-20000:],
        "stderr": result.stderr[-8000:],
        "started_at_utc": started,
        "completed_at_utc": completed,
    }
    return diagnosis


def main(argv: list[str] | None = None, *, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    parser = argparse.ArgumentParser(description="Run the OpenClaw agent for a server error request.")
    parser.parse_args(argv)
    request = json.load(stdin)
    diagnosis = run_openclaw_agent_for_error(request)
    stdout.write(json.dumps(diagnosis, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

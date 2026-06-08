"""Codex CLI runner for server error handoffs.

The deterministic safe-repair runner is intentionally narrow. This runner is
the actual Codex bridge: it passes the standard error request to Codex CLI with
the server-error-repair skill and wraps the resulting turn in the existing
agent_error_diagnosis contract.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .agent_error_handler import AGENT_ERROR_DIAGNOSIS_CONTRACT, _stable_id


DEFAULT_CODEX_MODEL = "gpt-5.5"
DEFAULT_CODEX_WORKDIR = "/root/.openclaw/workspace"
DEFAULT_CODEX_ADD_DIR = "/root/projects"
DEFAULT_CODEX_SANDBOX = "danger-full-access"
CODEX_SANDBOXES = {"read-only", "workspace-write", "danger-full-access"}
DEFAULT_TIMEOUT_SECONDS = 300


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    return max(1, int(value))


def _codex_prompt(request: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "Handle this server error request as an internal project repair task.",
            "Use the $server-error-repair skill.",
            "Your mission is to restore the system to the accepted current contract. Do not stop at diagnosis when a repair is possible.",
            "Autonomous repair may include code/config patches, provider/source calls, generated data repair, runtime/model-output writes, service restarts, storage maintenance, and system config changes only when the server-error-repair skill permits them, they are necessary to fix the bug, and they can be verified.",
            "The server-error-repair skill is the behavior boundary for powerful actions; follow its required evidence, safety, and receipt rules instead of broadening scope from this prompt.",
            "Never mutate broker/account/order/fill/position state. Never print, copy, or persist secrets.",
            "Keep every powerful action narrow, evidence-backed, and recorded in the final repair receipt.",
            "Do not deliver a user-facing chat reply from this run.",
            "Return ONLY strict JSON matching the server-error-repair final output contract.",
            "",
            str(request.get("agent_prompt") or json.dumps(dict(request), indent=2, sort_keys=True)),
        ]
    )


def _codex_workdir(request: Mapping[str, Any]) -> str:
    candidate = request.get("working_directory")
    if isinstance(candidate, str) and candidate.strip() and Path(candidate).exists():
        return candidate.strip()
    return os.environ.get("MANAGER_AGENT_ERROR_CODEX_WORKDIR", DEFAULT_CODEX_WORKDIR).strip() or DEFAULT_CODEX_WORKDIR


def _codex_add_dirs() -> list[str]:
    raw = os.environ.get("MANAGER_AGENT_ERROR_CODEX_ADD_DIRS", DEFAULT_CODEX_ADD_DIR).strip()
    return [part for part in raw.split(os.pathsep) if part]


def _codex_sandbox() -> str:
    sandbox = os.environ.get("MANAGER_AGENT_ERROR_CODEX_SANDBOX", DEFAULT_CODEX_SANDBOX).strip() or DEFAULT_CODEX_SANDBOX
    if sandbox not in CODEX_SANDBOXES:
        allowed = ", ".join(sorted(CODEX_SANDBOXES))
        raise ValueError(f"MANAGER_AGENT_ERROR_CODEX_SANDBOX must be one of: {allowed}")
    return sandbox


def run_codex_cli_for_error(request: Mapping[str, Any]) -> dict[str, Any]:
    started = _now_utc()
    model = os.environ.get("MANAGER_AGENT_ERROR_CODEX_MODEL", DEFAULT_CODEX_MODEL).strip() or DEFAULT_CODEX_MODEL
    timeout_seconds = _env_int(
        "MANAGER_AGENT_ERROR_CODEX_TIMEOUT_SECONDS",
        _env_int("MANAGER_AGENT_ERROR_AGENT_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS),
    )
    workdir = _codex_workdir(request)
    with tempfile.NamedTemporaryFile(prefix="codex-agent-error-", suffix=".json", delete=False) as final_file:
        final_output_path = final_file.name
    cmd = [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        _codex_sandbox(),
        "-C",
        workdir,
        "--output-last-message",
        final_output_path,
        "-m",
        model,
    ]
    for directory in _codex_add_dirs():
        cmd.extend(["--add-dir", directory])
    cmd.append(_codex_prompt(request))
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_seconds + 30, check=False)
        return_code = result.returncode
        result_stdout = result.stdout
        result_stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        return_code = None
        result_stdout = str(exc.stdout or "")
        result_stderr = f"codex repair runner timed out after {timeout_seconds} seconds\n{exc.stderr or ''}"
    try:
        final_output = Path(final_output_path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        final_output = ""
    try:
        Path(final_output_path).unlink(missing_ok=True)
    except OSError:
        pass
    completed = _now_utc()
    status = "completed" if return_code == 0 else "agent_call_failed"
    stdout = final_output or result_stdout
    diagnosis = {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request.get("request_id"), started, return_code, stdout, result_stderr),
        "request_ref": request.get("request_id"),
        "agent_ref": request.get("agent_ref") or f"codex_cli:{model}",
        "runner_command": "codex_cli",
        "status": status,
        "return_code": return_code,
        "stdout": stdout[-20000:],
        "stderr": (result_stderr or result_stdout)[-8000:],
        "started_at_utc": started,
        "completed_at_utc": completed,
    }
    return diagnosis


def main(argv: list[str] | None = None, *, stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    parser = argparse.ArgumentParser(description="Run Codex CLI for a server error request.")
    parser.parse_args(argv)
    request = json.load(stdin)
    diagnosis = run_codex_cli_for_error(request)
    stdout.write(json.dumps(diagnosis, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

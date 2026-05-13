"""Unified server-error agent handoff helpers.

This module is intentionally component-neutral. Any server-side workflow can call
it after an error to create one standard agent diagnosis/repair request. The
request is evidence-first and read-only by default; optional agent invocation is
behind an explicit runner command supplied by reviewed runtime configuration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

from .control_plane import TaskSystemError

SERVER_ERROR_AGENT_REQUEST_CONTRACT = "server_error_agent_request"
AGENT_ERROR_DIAGNOSIS_CONTRACT = "agent_error_diagnosis"
AGENT_ERROR_HANDLING_RESULT_CONTRACT = "agent_error_handling_result"
DEFAULT_AGENT_REF = "openclaw_agent_under_owner_observation"
DEFAULT_OUTPUT_ROOT = Path("storage/runtime/agent_error_handling")
DEFAULT_DISCORD_TARGET = "channel:1504100135200620665"
DEFAULT_DISCORD_SERVER_ID = "1480186849241731084"
ALLOWED_SEVERITIES = {"info", "warning", "error", "critical"}
SAFE_ALLOWED_ACTIONS = (
    "inspect referenced logs, receipts, status artifacts, source files, docs, and tests",
    "diagnose root cause and classify whether the failure is code, config, data, environment, provider, or operator-boundary related",
    "prepare internal code, test, config-template, or documentation patches when they are reversible and within repository boundaries",
    "run non-destructive verification commands such as tests, compile checks, lint/diff checks, and read-only status inspection",
    "recommend a retry only after the suspected cause is fixed or classified as transient",
)
FORBIDDEN_ACTIONS = (
    "do not call market-data providers unless a separate reviewed provider-dispatch gate authorizes it",
    "do not submit broker orders, construct live order submission, mutate accounts, or touch funds/positions",
    "do not exfiltrate secrets or print secret values; use aliases and redacted evidence only",
    "do not delete data, rewrite durable storage, restart services, or change system packages without an explicit higher-level approval path",
    "do not mark failures accepted, corrected, or skipped without durable diagnosis evidence and the appropriate review reference",
)


def _now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _as_list(values: Iterable[str] | None) -> list[str]:
    return [str(value) for value in values or [] if str(value)]


def _bounded_file_excerpt(path: str | None, *, max_chars: int = 4000) -> str | None:
    if not path:
        return None
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def build_agent_prompt(request: Mapping[str, Any]) -> str:
    """Build the standard prompt given to the diagnostic agent."""

    return "\n".join(
        [
            "You are the server-wide error diagnosis and repair agent for the trading system.",
            "Diagnose the failure from the supplied evidence, identify the root cause, and attempt only safe internal repairs.",
            "Return a concise JSON-compatible report with: diagnosis_status, root_cause, repair_attempted, files_changed, verification, retry_recommendation, and blockers.",
            "",
            "Allowed actions:",
            *[f"- {item}" for item in request.get("allowed_actions", [])],
            "",
            "Forbidden actions:",
            *[f"- {item}" for item in request.get("forbidden_actions", [])],
            "",
            "Error request:",
            json.dumps({key: value for key, value in request.items() if key != "agent_prompt"}, indent=2, sort_keys=True),
        ]
    )


def build_server_error_agent_request(
    *,
    source_component: str,
    summary: str,
    source_repo: str | None = None,
    error_scope: str = "server",
    error_kind: str = "unclassified_error",
    severity: str = "error",
    command: Iterable[str] | None = None,
    exit_code: int | None = None,
    stdout_path: str | None = None,
    stderr_path: str | None = None,
    working_directory: str | None = None,
    evidence_refs: Iterable[str] | None = None,
    occurred_at_utc: str | None = None,
    agent_ref: str = DEFAULT_AGENT_REF,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a component-neutral request for agent diagnosis/repair."""

    if not source_component:
        raise TaskSystemError("source_component is required")
    if not summary:
        raise TaskSystemError("summary is required")
    normalized_severity = severity.strip().lower()
    if normalized_severity not in ALLOWED_SEVERITIES:
        raise TaskSystemError(f"severity must be one of: {', '.join(sorted(ALLOWED_SEVERITIES))}")
    normalized_command = [str(part) for part in command or []]
    normalized_evidence = _as_list(evidence_refs)
    if stdout_path:
        normalized_evidence.append(f"stdout:{stdout_path}")
    if stderr_path:
        normalized_evidence.append(f"stderr:{stderr_path}")
    occurred = occurred_at_utc or _now_utc()
    stable_request_id = request_id or _stable_id(
        "erragent",
        source_component,
        source_repo,
        error_scope,
        error_kind,
        summary,
        normalized_command,
        exit_code,
        stdout_path,
        stderr_path,
        occurred,
    )
    request: dict[str, Any] = {
        "contract_type": SERVER_ERROR_AGENT_REQUEST_CONTRACT,
        "schema_version": "1",
        "request_id": stable_request_id,
        "source_component": source_component,
        "source_repo": source_repo,
        "error_scope": error_scope,
        "error_kind": error_kind,
        "severity": normalized_severity,
        "summary": summary,
        "command": normalized_command,
        "exit_code": exit_code,
        "stdout_path": stdout_path,
        "stderr_path": stderr_path,
        "stdout_excerpt": _bounded_file_excerpt(stdout_path),
        "stderr_excerpt": _bounded_file_excerpt(stderr_path),
        "working_directory": working_directory,
        "evidence_refs": normalized_evidence,
        "agent_ref": agent_ref,
        "allowed_actions": list(SAFE_ALLOWED_ACTIONS),
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "occurred_at_utc": occurred,
        "created_at_utc": _now_utc(),
    }
    request["agent_prompt"] = build_agent_prompt(request)
    validate_server_error_agent_request(request)
    return request


def validate_server_error_agent_request(request: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(request)
    required = (
        "contract_type",
        "schema_version",
        "request_id",
        "source_component",
        "error_scope",
        "error_kind",
        "severity",
        "summary",
        "agent_ref",
        "allowed_actions",
        "forbidden_actions",
        "occurred_at_utc",
        "created_at_utc",
        "agent_prompt",
    )
    for field in required:
        value = normalized.get(field)
        if value in (None, "", []):
            raise TaskSystemError(f"missing required server error agent request field: {field}")
    if normalized["contract_type"] != SERVER_ERROR_AGENT_REQUEST_CONTRACT:
        raise TaskSystemError(f"contract_type must be {SERVER_ERROR_AGENT_REQUEST_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if normalized["severity"] not in ALLOWED_SEVERITIES:
        raise TaskSystemError(f"unsupported severity: {normalized['severity']}")
    for field in ("command", "evidence_refs", "allowed_actions", "forbidden_actions"):
        if not isinstance(normalized.get(field, []), list):
            raise TaskSystemError(f"{field} must be a list")
        normalized[field] = normalized.get(field, [])
    return normalized


def write_json_artifact(payload: Mapping[str, Any], *, path: Path | None = None, output: TextIO | None = None) -> None:
    content = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if output is not None:
        output.write(content)


def default_request_path(request: Mapping[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / str(request["request_id"]) / "server_error_agent_request.json"


def default_diagnosis_path(request: Mapping[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    return output_root / str(request["request_id"]) / "agent_error_diagnosis.json"


def call_agent_runner(
    request: Mapping[str, Any],
    *,
    runner_command: str,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    """Call the configured agent runner with the request JSON on stdin."""

    argv = shlex.split(runner_command)
    if not argv:
        raise TaskSystemError("agent runner command is empty")
    started = _now_utc()
    try:
        result = subprocess.run(
            argv,
            input=json.dumps(dict(request), sort_keys=True),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
        status = "completed" if result.returncode == 0 else "agent_call_failed"
    except subprocess.TimeoutExpired as exc:
        return_code = None
        stdout = str(exc.stdout or "")
        stderr = f"agent runner timed out after {timeout_seconds} seconds\n{exc.stderr or ''}"
        status = "agent_call_failed"
    completed = _now_utc()
    diagnosis = {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request["request_id"], started, return_code, stdout, stderr),
        "request_ref": request["request_id"],
        "agent_ref": request["agent_ref"],
        "runner_command": runner_command,
        "status": status,
        "return_code": return_code,
        "stdout": stdout[-8000:],
        "stderr": stderr[-8000:],
        "started_at_utc": started,
        "completed_at_utc": completed,
    }
    validate_agent_error_diagnosis(diagnosis)
    return diagnosis


def build_queued_diagnosis(request: Mapping[str, Any], *, reason: str = "agent runner not configured") -> dict[str, Any]:
    diagnosis = {
        "contract_type": AGENT_ERROR_DIAGNOSIS_CONTRACT,
        "schema_version": "1",
        "diagnosis_id": _stable_id("errdiag", request["request_id"], reason),
        "request_ref": request["request_id"],
        "agent_ref": request["agent_ref"],
        "runner_command": None,
        "status": "queued",
        "return_code": None,
        "stdout": "",
        "stderr": reason,
        "started_at_utc": None,
        "completed_at_utc": _now_utc(),
    }
    validate_agent_error_diagnosis(diagnosis)
    return diagnosis


def validate_agent_error_diagnosis(diagnosis: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(diagnosis)
    required = ("contract_type", "schema_version", "diagnosis_id", "request_ref", "agent_ref", "status", "completed_at_utc")
    for field in required:
        value = normalized.get(field)
        if value in (None, ""):
            raise TaskSystemError(f"missing required agent error diagnosis field: {field}")
    if normalized["contract_type"] != AGENT_ERROR_DIAGNOSIS_CONTRACT:
        raise TaskSystemError(f"contract_type must be {AGENT_ERROR_DIAGNOSIS_CONTRACT}")
    if str(normalized["schema_version"]) != "1":
        raise TaskSystemError("schema_version must be 1")
    if normalized["status"] not in {"queued", "completed", "agent_call_failed"}:
        raise TaskSystemError(f"unsupported agent diagnosis status: {normalized['status']}")
    return normalized



def _discord_message(request: Mapping[str, Any], diagnosis: Mapping[str, Any], *, server_id: str | None = None) -> str:
    severity = str(request.get("severity") or "error").upper()
    component = request.get("source_component") or "unknown component"
    summary = request.get("summary") or "server error"
    error_kind = request.get("error_kind") or "unclassified_error"
    scope = request.get("error_scope") or "server"
    exit_code = request.get("exit_code")
    request_id = request.get("request_id")
    diagnosis_status = diagnosis.get("status")
    stderr_path = request.get("stderr_path")
    stdout_path = request.get("stdout_path")
    lines = [
        f"🚨 Trading server error [{severity}]",
        f"Component: {component}",
        f"Scope: {scope}",
        f"Kind: {error_kind}",
        f"Summary: {summary}",
        f"Agent diagnosis: {diagnosis_status}",
        f"Request: {request_id}",
    ]
    if server_id:
        lines.insert(1, f"Discord server: {server_id}")
    if exit_code is not None:
        lines.append(f"Exit code: {exit_code}")
    if stderr_path:
        lines.append(f"stderr: {stderr_path}")
    elif stdout_path:
        lines.append(f"stdout: {stdout_path}")
    lines.append("Boundaries: no provider calls, broker/account mutation, or destructive repair without separate approval.")
    return "\n".join(lines)


def notify_discord_for_error(
    request: Mapping[str, Any],
    diagnosis: Mapping[str, Any],
    *,
    target: str | None = None,
    server_id: str | None = None,
    account_id: str | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    """Send a best-effort Discord notification through OpenClaw's message CLI."""

    resolved_target = target or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_TARGET", "").strip() or DEFAULT_DISCORD_TARGET
    resolved_server_id = server_id or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_SERVER_ID", "").strip() or DEFAULT_DISCORD_SERVER_ID
    resolved_account_id = account_id or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_ACCOUNT_ID", "").strip() or None
    if not resolved_target:
        return {"status": "skipped", "reason": "discord target not configured"}
    message = _discord_message(request, diagnosis, server_id=resolved_server_id)
    cmd = [
        "openclaw",
        "message",
        "send",
        "--channel",
        "discord",
        "--target",
        resolved_target,
        "--message",
        message,
    ]
    if resolved_account_id:
        cmd.extend(["--account", resolved_account_id])
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_seconds, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "failed", "reason": str(exc), "target": resolved_target}
    return {
        "status": "sent" if result.returncode == 0 else "failed",
        "target": resolved_target,
        "return_code": result.returncode,
        "stdout": result.stdout[-1000:],
        "stderr": result.stderr[-1000:],
    }


def handle_server_error(
    *,
    source_component: str,
    summary: str,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    call_agent: bool = False,
    runner_command: str | None = None,
    notify_discord: bool | None = None,
    discord_target: str | None = None,
    discord_server_id: str | None = None,
    discord_account_id: str | None = None,
    **request_kwargs: Any,
) -> dict[str, Any]:
    """Create the standard request and optionally call the configured agent runner."""

    request = build_server_error_agent_request(source_component=source_component, summary=summary, **request_kwargs)
    request_path = default_request_path(request, output_root)
    write_json_artifact(request, path=request_path)
    configured_runner = runner_command or os.environ.get("MANAGER_AGENT_ERROR_RUNNER_COMMAND", "").strip()
    if call_agent and configured_runner:
        diagnosis = call_agent_runner(request, runner_command=configured_runner)
    else:
        diagnosis = build_queued_diagnosis(request, reason="agent runner not configured" if call_agent else "agent call not requested")
    diagnosis_path = default_diagnosis_path(request, output_root)
    write_json_artifact(diagnosis, path=diagnosis_path)
    should_notify_discord = (
        bool(notify_discord)
        if notify_discord is not None
        else bool(os.environ.get("MANAGER_AGENT_ERROR_NOTIFY_DISCORD") or discord_target or os.environ.get("MANAGER_AGENT_ERROR_DISCORD_TARGET"))
    )
    discord_notification = (
        notify_discord_for_error(
            request,
            diagnosis,
            target=discord_target,
            server_id=discord_server_id,
            account_id=discord_account_id,
        )
        if should_notify_discord
        else {"status": "skipped", "reason": "discord notification not requested"}
    )
    result = {
        "contract_type": AGENT_ERROR_HANDLING_RESULT_CONTRACT,
        "schema_version": "1",
        "request_id": request["request_id"],
        "request_path": str(request_path),
        "diagnosis_id": diagnosis["diagnosis_id"],
        "diagnosis_path": str(diagnosis_path),
        "status": diagnosis["status"],
        "discord_notification": discord_notification,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a server-wide agent diagnosis/repair request for an observed error.")
    parser.add_argument("--source-component", required=True)
    parser.add_argument("--source-repo")
    parser.add_argument("--error-scope", default="server")
    parser.add_argument("--error-kind", default="unclassified_error")
    parser.add_argument("--severity", default="error", choices=tuple(sorted(ALLOWED_SEVERITIES)))
    parser.add_argument("--summary", required=True)
    parser.add_argument("--command", action="append", default=[], help="Command token or full command string associated with the error; may be repeated.")
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--stdout-path")
    parser.add_argument("--stderr-path")
    parser.add_argument("--working-directory")
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--occurred-at-utc")
    parser.add_argument("--agent-ref", default=DEFAULT_AGENT_REF)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--call-agent", action="store_true", help="Invoke the configured agent runner; otherwise only queue/write the request artifacts.")
    parser.add_argument("--agent-runner-command", help="Reviewed local command that accepts request JSON on stdin and returns diagnosis text/JSON on stdout.")
    parser.add_argument("--notify-discord", action="store_true", help="Send a Discord alert through OpenClaw's message CLI after writing diagnosis artifacts.")
    parser.add_argument("--discord-target", default=None, help="Discord target such as channel:1504100135200620665; defaults to MANAGER_AGENT_ERROR_DISCORD_TARGET.")
    parser.add_argument("--discord-server-id", default=None, help="Optional Discord server/guild id for alert context.")
    parser.add_argument("--discord-account-id", default=None, help="Optional OpenClaw Discord account id; defaults to plugin account resolution.")
    args = parser.parse_args(argv)
    result = handle_server_error(
        source_component=args.source_component,
        source_repo=args.source_repo,
        error_scope=args.error_scope,
        error_kind=args.error_kind,
        severity=args.severity,
        summary=args.summary,
        command=args.command,
        exit_code=args.exit_code,
        stdout_path=args.stdout_path,
        stderr_path=args.stderr_path,
        working_directory=args.working_directory,
        evidence_refs=args.evidence_ref,
        occurred_at_utc=args.occurred_at_utc,
        agent_ref=args.agent_ref,
        output_root=args.output_root,
        call_agent=args.call_agent,
        runner_command=args.agent_runner_command,
        notify_discord=args.notify_discord,
        discord_target=args.discord_target,
        discord_server_id=args.discord_server_id,
        discord_account_id=args.discord_account_id,
    )
    write_json_artifact(result, output=sys.stdout)
    return 0


__all__ = [
    "AGENT_ERROR_DIAGNOSIS_CONTRACT",
    "AGENT_ERROR_HANDLING_RESULT_CONTRACT",
    "SERVER_ERROR_AGENT_REQUEST_CONTRACT",
    "build_agent_prompt",
    "build_queued_diagnosis",
    "build_server_error_agent_request",
    "call_agent_runner",
    "handle_server_error",
    "notify_discord_for_error",
    "validate_agent_error_diagnosis",
    "validate_server_error_agent_request",
    "write_json_artifact",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

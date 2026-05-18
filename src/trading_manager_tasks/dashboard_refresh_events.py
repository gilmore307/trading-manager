"""Event trigger for storage-owned dashboard read-model refreshes."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT = "trading-storage-dashboard-read-model-refresh.service"


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _refresh_command() -> tuple[str, ...]:
    explicit = os.environ.get("TRADING_MANAGER_DASHBOARD_REFRESH_COMMAND")
    if explicit:
        return tuple(shlex.split(explicit))
    service_unit = os.environ.get("TRADING_MANAGER_DASHBOARD_REFRESH_SERVICE_UNIT") or DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT
    command = ["systemctl", "start"]
    if _truthy(os.environ.get("TRADING_MANAGER_DASHBOARD_REFRESH_NO_BLOCK", "true")):
        command.append("--no-block")
    command.append(service_unit)
    return tuple(command)


def trigger_dashboard_refresh_from_workflow_state_write(*, state_path: Path) -> dict[str, Any]:
    """Nudge storage to refresh dashboard read models after workflow-state writes.

    This hook is intentionally opt-in via environment so library tests and local
    dry-runs do not reach out to systemd. In the resident scheduler service it
    turns workflow state writes, including stage-start writes, into event-driven
    dashboard refreshes. The periodic storage timer remains only a backstop.
    """

    if not _truthy(os.environ.get("TRADING_MANAGER_DASHBOARD_REFRESH_ON_WORKFLOW_STATE_WRITE")):
        return {"status": "disabled"}
    command = _refresh_command()
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=float(os.environ.get("TRADING_MANAGER_DASHBOARD_REFRESH_TRIGGER_TIMEOUT_SECONDS", "5")),
        )
    except Exception as exc:  # pragma: no cover - defensive operational path.
        return {
            "status": "failed",
            "command": list(command),
            "state_path": str(state_path),
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "status": "triggered" if completed.returncode == 0 else "failed",
        "command": list(command),
        "state_path": str(state_path),
        "return_code": completed.returncode,
        "stderr": completed.stderr[-1000:],
    }


__all__ = [
    "DEFAULT_DASHBOARD_REFRESH_SERVICE_UNIT",
    "trigger_dashboard_refresh_from_workflow_state_write",
]

#!/usr/bin/env python3
"""Run the persistent historical-training automation scheduler daemon."""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.agent_error_handler import _env_truthy, handle_server_error
from trading_manager_tasks.registry_values import registry_payload
from trading_manager_tasks.scheduler_daemon import main as scheduler_daemon_main
from trading_manager_tasks.storage_paths import manager_storage_root

TRADING_MANAGER_REPO = registry_payload("rep_H6S3V8LA")


def _fatal_stderr_path() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%S.%f+0000")
    return manager_storage_root() / "runtime" / "agent_error_handling" / "scheduler_daemon_fatal" / f"{timestamp}.stderr.log"


def main() -> int:
    try:
        return scheduler_daemon_main()
    except Exception as exc:
        stderr_path = _fatal_stderr_path()
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        stderr_path.write_text(traceback.format_exc(), encoding="utf-8")
        try:
            result = handle_server_error(
                source_component="trading-manager.historical_scheduler_daemon",
                source_repo=TRADING_MANAGER_REPO,
                error_scope="server_service",
                error_kind=exc.__class__.__name__,
                severity="error",
                summary=f"historical scheduler daemon failed: {exc}",
                command=sys.argv,
                exit_code=1,
                stderr_path=str(stderr_path),
                working_directory=str(Path.cwd()),
                call_agent=_env_truthy("MANAGER_AGENT_ERROR_AUTOCALL"),
            )
            print(json.dumps(result, sort_keys=True), file=sys.stderr)
        except Exception:  # pragma: no cover - preserves original fatal visibility if handoff fails.
            traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

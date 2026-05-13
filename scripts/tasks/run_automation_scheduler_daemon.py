#!/usr/bin/env python3
"""Run the persistent historical-training automation scheduler daemon."""

from __future__ import annotations

import json
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

from trading_manager_tasks.agent_error_handler import handle_server_error
from trading_manager_tasks.scheduler_daemon import main as scheduler_daemon_main


def _fatal_stderr_path() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%S.%f+0000")
    return Path("storage/runtime/agent_error_handling/scheduler_daemon_fatal") / f"{timestamp}.stderr.log"


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
                source_repo="trading-manager",
                error_scope="server_service",
                error_kind=exc.__class__.__name__,
                severity="error",
                summary=f"historical scheduler daemon failed: {exc}",
                command=sys.argv,
                exit_code=1,
                stderr_path=str(stderr_path),
                working_directory=str(Path.cwd()),
            )
            print(json.dumps(result, sort_keys=True), file=sys.stderr)
        except Exception:  # pragma: no cover - preserves original fatal visibility if handoff fails.
            traceback.print_exc(file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

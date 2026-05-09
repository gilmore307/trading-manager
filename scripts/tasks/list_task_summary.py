#!/usr/bin/env python3
"""List global manager task summary rows sorted by priority."""

from __future__ import annotations

from trading_manager_tasks.control_plane import list_task_summary_main


if __name__ == "__main__":
    raise SystemExit(list_task_summary_main())

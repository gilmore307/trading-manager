#!/usr/bin/env python3
"""Run the persistent historical-training automation scheduler daemon."""

from __future__ import annotations

from trading_manager_tasks.scheduler_daemon import main


if __name__ == "__main__":
    raise SystemExit(main())

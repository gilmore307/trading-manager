#!/usr/bin/env python3
"""Inspect historical scheduler service status without mutating runtime state."""

from __future__ import annotations

from trading_manager_tasks.scheduler_status import main


if __name__ == "__main__":
    raise SystemExit(main())

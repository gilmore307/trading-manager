#!/usr/bin/env python3
"""Validate or persist manager failure-register rows."""

from __future__ import annotations

from trading_manager_tasks.failure_register import register_failure_main


if __name__ == "__main__":
    raise SystemExit(register_failure_main())

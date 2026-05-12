#!/usr/bin/env python3
"""Validate or persist manager_request rows."""

from __future__ import annotations

from trading_manager_tasks.control_plane import submit_requests_main


if __name__ == "__main__":
    raise SystemExit(submit_requests_main())

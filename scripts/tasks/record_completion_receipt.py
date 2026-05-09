#!/usr/bin/env python3
"""Normalize or persist a component completion receipt."""

from __future__ import annotations

from trading_manager_tasks.control_plane import record_receipt_main


if __name__ == "__main__":
    raise SystemExit(record_receipt_main())

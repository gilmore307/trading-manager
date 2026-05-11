#!/usr/bin/env python3
"""Build manager realtime shadow handoff receipts/control-plane rows."""

from __future__ import annotations

from trading_manager_tasks.realtime_shadow_handoff import realtime_shadow_handoff_main


if __name__ == "__main__":
    raise SystemExit(realtime_shadow_handoff_main())

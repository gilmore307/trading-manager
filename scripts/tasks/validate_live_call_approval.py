#!/usr/bin/env python3
"""Validate live-call approval artifacts without dispatching provider calls."""

from __future__ import annotations

from trading_manager_tasks.live_call_gate import main

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Inspect a live-call approval packet lifecycle status without provider dispatch."""

from trading_manager_tasks.live_call_packet import status_main

if __name__ == "__main__":
    raise SystemExit(status_main())

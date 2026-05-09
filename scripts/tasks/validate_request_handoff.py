#!/usr/bin/env python3
"""Validate materialized manager request handoff without provider calls."""

from __future__ import annotations

from trading_manager_tasks.request_handoff import main

if __name__ == "__main__":
    raise SystemExit(main())

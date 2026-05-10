#!/usr/bin/env python3
"""Validate a reviewed live_call_approval_v1 exactly against a manager proposal."""

from trading_manager_tasks.live_call_planning import validate_proposal_main

if __name__ == "__main__":
    raise SystemExit(validate_proposal_main())

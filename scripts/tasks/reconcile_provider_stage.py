#!/usr/bin/env python3
"""Reconcile provider-stage receipts into manager SQL/coverage/workflow state safely."""

from trading_manager_tasks.stage_reconcile import main

if __name__ == "__main__":
    raise SystemExit(main())

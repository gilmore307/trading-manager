#!/usr/bin/env python3
"""Write one human-facing summary for a batch of model-group rerun reset receipts."""

from trading_manager_tasks.model_group_rerun import batch_main


if __name__ == "__main__":
    raise SystemExit(batch_main())

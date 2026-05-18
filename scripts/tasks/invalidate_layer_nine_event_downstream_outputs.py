#!/usr/bin/env python3
"""Mark event-risk-dependent historical model outputs stale after event-source contract repair."""

from trading_manager_tasks.model_training_invalidation import main

if __name__ == "__main__":
    raise SystemExit(main())

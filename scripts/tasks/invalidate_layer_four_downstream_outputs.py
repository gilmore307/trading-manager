#!/usr/bin/env python3
"""Mark Layer 4+ historical model outputs stale after event-source contract repair."""

from trading_manager_tasks.model_training_invalidation import main

if __name__ == "__main__":
    raise SystemExit(main())

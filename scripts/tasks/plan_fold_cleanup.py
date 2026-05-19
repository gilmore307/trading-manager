#!/usr/bin/env python3
"""Plan a fold-scoped cleanup gate and required SQL logical backup."""

from __future__ import annotations

from trading_manager_tasks.fold_cleanup import main


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

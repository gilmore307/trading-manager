#!/usr/bin/env python3
"""Dispatch reviewed Layer 9 option-expression source acquisition."""

from __future__ import annotations

import argparse
from pathlib import Path

from trading_manager_tasks.layer_nine_option_expression import (
    DEFAULT_TRADING_DATA_ROOT,
    dispatch_layer_nine_option_acquisition,
)
from trading_manager_tasks.provider_dispatch import write_dispatch_summary
from trading_manager_tasks.request_payloads import DEFAULT_STORAGE_ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--request-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--database-url")
    parser.add_argument("--execute-provider-calls", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dynamic-workers", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args(argv)
    summary = dispatch_layer_nine_option_acquisition(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        trading_data_root=args.trading_data_root,
        request_ids=args.request_id,
        limit=args.limit,
        execute_provider_calls=args.execute_provider_calls,
        continue_on_error=args.continue_on_error,
        database_url=args.database_url,
        dynamic_workers=args.dynamic_workers,
        max_workers=args.max_workers,
    )
    write_dispatch_summary(summary, output=__import__("sys").stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

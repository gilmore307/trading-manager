#!/usr/bin/env python3
"""Dispatch shared option-chain source acquisition requests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.option_chain_source_acquisition import dispatch_option_chain_source_acquisition


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path)
    parser.add_argument("--trading-data-root", type=Path)
    parser.add_argument("--request-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--execute-provider-calls", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--database-url")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--no-dynamic-workers", action="store_true")
    args = parser.parse_args()
    kwargs = {
        "start_month": args.start_month,
        "end_month": args.end_month,
        "request_ids": tuple(args.request_id),
        "limit": args.limit,
        "execute_provider_calls": args.execute_provider_calls,
        "continue_on_error": args.continue_on_error,
        "database_url": args.database_url,
        "dynamic_workers": not args.no_dynamic_workers,
        "max_workers": args.max_workers,
    }
    if args.storage_root is not None:
        kwargs["storage_root"] = args.storage_root
    if args.trading_data_root is not None:
        kwargs["trading_data_root"] = args.trading_data_root
    summary = dispatch_option_chain_source_acquisition(**kwargs)
    print(json.dumps(summary.summary_row(), indent=2, sort_keys=True))
    return 0 if all(item.status != "dispatched_failed" for item in summary.items) else 1


if __name__ == "__main__":
    raise SystemExit(main())

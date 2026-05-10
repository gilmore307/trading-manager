#!/usr/bin/env python3
"""Prepare Layer 2 sector-context historical-training task keys without provider dispatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trading_manager_tasks.historical_training import prepare_layer_two_historical_training_batch, write_batch_output
from trading_manager_tasks.request_handoff import DEFAULT_TRADING_DATA_SRC
from trading_manager_tasks.request_payloads import DEFAULT_STORAGE_ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--component-src-root", type=Path, default=DEFAULT_TRADING_DATA_SRC)
    parser.add_argument("--write", action="store_true", help="Persist manager requests, task payload files, and input bindings.")
    parser.add_argument("--write-files-only", action="store_true", help="Write task payload files without persisting SQL rows.")
    parser.add_argument("--no-handoff-validation", action="store_true")
    parser.add_argument("--database-url")
    parser.add_argument("--format", choices=("json", "jsonl"), default="json")
    args = parser.parse_args()

    summary, requests, payloads, validations = prepare_layer_two_historical_training_batch(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        component_src_root=args.component_src_root,
        write=args.write or args.write_files_only,
        persist_sql=args.write,
        validate_handoff=not args.no_handoff_validation,
        database_url=args.database_url,
    )
    write_batch_output(summary, requests, payloads, validations, output=sys.stdout, output_format=args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate M03 event-failure feature receipts from reviewed event evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.layer_four_event_failure_features import (
    DEFAULT_INPUT_ROOT,
    DEFAULT_OUTPUT_ROOT,
    materialize_layer_four_event_failure_features,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--write-database", dest="write_database", action="store_true")
    parser.add_argument("--persist-sql", dest="write_database", action="store_true")
    parser.add_argument("--database-url")
    args = parser.parse_args()

    receipt = materialize_layer_four_event_failure_features(
        start_month=args.start_month,
        end_month=args.end_month,
        input_root=args.input_root,
        output_root=args.output_root,
        write=args.write,
        write_database=args.write_database,
        database_url=args.database_url,
    )
    print(json.dumps(receipt.summary_row(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

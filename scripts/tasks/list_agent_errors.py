#!/usr/bin/env python3
"""List durable server error catalog entries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.agent_error_handler import (
    CATALOG_STORAGES,
    DEFAULT_ERROR_CATALOG_NAME,
    fetch_server_error_catalog_rows,
)


def _load_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="List server error catalog entries by human-facing error number.")
    parser.add_argument("--output-root", type=Path, default=Path("storage/runtime/agent_error_handling"))
    parser.add_argument("--error-ref", help="Filter to one error reference such as ERR-000001.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--database-url", help="Database URL for the SQL-backed server error catalog.")
    parser.add_argument("--catalog-storage", choices=tuple(sorted(CATALOG_STORAGES)), default="sql")
    args = parser.parse_args()

    if args.catalog_storage == "sql":
        rows = fetch_server_error_catalog_rows(database_url=args.database_url, error_ref=args.error_ref, limit=args.limit)
    else:
        rows = _load_rows(args.output_root / DEFAULT_ERROR_CATALOG_NAME)
        if args.error_ref:
            wanted = args.error_ref.strip().upper()
            rows = [row for row in rows if str(row.get("error_ref", "")).upper() == wanted]
        else:
            rows = rows[-max(args.limit, 0) :]
    for row in rows:
        print(json.dumps(row, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

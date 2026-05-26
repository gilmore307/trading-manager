#!/usr/bin/env python3
"""Sync the current trading registry table from ``scripts/registry/current.csv``.

The database URL is read from ``OPENCLAW_DATABASE_URL`` when set, otherwise
from ``/root/secrets/openclaw/database-url``.
"""

from __future__ import annotations

import argparse
import csv
import os
import shlex
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_ROOT = Path(__file__).resolve().parent
SCHEMA_SQL = REGISTRY_ROOT / "sql" / "trading_registry.sql"
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_CSV_PATH = REGISTRY_ROOT / "current.csv"

BASE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trading_registry (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  key TEXT NOT NULL UNIQUE,
  payload_format TEXT NOT NULL,
  payload TEXT NOT NULL,
  path TEXT,
  applies_to TEXT,
  artifact_sync_policy TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE IF EXISTS trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

ALTER TABLE IF EXISTS trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_payload_format_check;

ALTER TABLE IF EXISTS trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_artifact_sync_policy_check;

ALTER TABLE IF EXISTS trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_applies_to_check;
"""

REGISTRY_COLUMNS = (
    "id",
    "kind",
    "key",
    "payload_format",
    "payload",
    "path",
    "applies_to",
    "artifact_sync_policy",
    "note",
    "created_at",
    "updated_at",
)

REGISTRY_EXPORT_SQL = """
COPY (
  SELECT
    id,
    kind,
    key,
    payload_format,
    payload,
    path,
    applies_to,
    artifact_sync_policy,
    note,
    created_at,
    updated_at
  FROM trading_registry
  ORDER BY kind ASC, key ASC
) TO STDOUT WITH CSV HEADER
"""


def database_url() -> str:
    value = os.environ.get("OPENCLAW_DATABASE_URL", "").strip()
    if value:
        return value
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(
        "OPENCLAW_DATABASE_URL is unset and "
        f"{DEFAULT_DB_URL_FILE} does not exist"
    )


def run_psql(
    db_url: str,
    *,
    sql: str | None = None,
    file: Path | None = None,
    stdin_sql: str | None = None,
    quiet: bool = False,
) -> str:
    cmd = ["psql", db_url, "-v", "ON_ERROR_STOP=1"]
    if quiet:
        cmd.append("-q")
    if sql is not None:
        cmd.extend(["-Atc", sql])
        input_text = None
    elif file is not None:
        cmd.extend(["-f", str(file)])
        input_text = None
    elif stdin_sql is not None:
        input_text = stdin_sql
    else:
        raise ValueError("sql, file, or stdin_sql is required")

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        input=input_text,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise SystemExit(result.returncode)
    if not quiet and result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.stdout


def run_psql_stdout(db_url: str, sql: str) -> str:
    cmd = ["psql", db_url, "-v", "ON_ERROR_STOP=1", "-q", "-c", sql]
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stdout, end="")
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        raise SystemExit(result.returncode)
    return result.stdout


def read_registry_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REGISTRY_COLUMNS:
            raise SystemExit(
                f"{csv_path} header must be exactly: {','.join(REGISTRY_COLUMNS)}"
            )
        rows = list(reader)
    if not rows:
        raise SystemExit(f"{csv_path} has no registry rows")
    return rows


def apply_schema(db_url: str) -> None:
    run_psql(db_url, file=SCHEMA_SQL, quiet=True)


def prepare_table_for_sync(db_url: str) -> None:
    run_psql(db_url, stdin_sql=BASE_TABLE_SQL, quiet=True)


def sync_registry(db_url: str, csv_path: Path) -> int:
    rows = read_registry_rows(csv_path)
    column_sql = ", ".join(REGISTRY_COLUMNS)
    copy_path = shlex.quote(str(csv_path.resolve()))
    sync_sql = f"""
BEGIN;
CREATE TEMP TABLE trading_registry_import (
  id TEXT,
  kind TEXT,
  key TEXT,
  payload_format TEXT,
  payload TEXT,
  path TEXT,
  applies_to TEXT,
  artifact_sync_policy TEXT,
  note TEXT,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
) ON COMMIT DROP;
\\copy trading_registry_import ({column_sql}) FROM {copy_path} WITH CSV HEADER
DELETE FROM trading_registry
WHERE id NOT IN (SELECT id FROM trading_registry_import);
INSERT INTO trading_registry ({column_sql})
SELECT {column_sql}
FROM trading_registry_import
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  created_at = EXCLUDED.created_at,
  updated_at = EXCLUDED.updated_at;
COMMIT;
"""
    run_psql(db_url, stdin_sql=sync_sql, quiet=True)
    return len(rows)


def export_registry_csv(db_url: str, csv_path: Path = DEFAULT_CSV_PATH) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_data = run_psql_stdout(db_url, REGISTRY_EXPORT_SQL)
    csv_path.write_text(csv_data, encoding="utf-8")
    row_count = max(len(csv_data.splitlines()) - 1, 0)
    try:
        display_path = csv_path.relative_to(REPO_ROOT)
    except ValueError:
        display_path = csv_path
    print(f"exported {row_count} registry rows to {display_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="validate input and show planned sync")
    parser.add_argument("--export-only", action="store_true", help="export scripts/registry/current.csv without syncing")
    parser.add_argument("--no-export", action="store_true", help="skip CSV export after syncing")
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help="CSV path, default: scripts/registry/current.csv",
    )
    args = parser.parse_args()

    db_url = database_url()

    if args.export_only:
        export_registry_csv(db_url, args.csv_path)
        return 0

    rows = read_registry_rows(args.csv_path)
    if args.dry_run:
        print(f"would apply {SCHEMA_SQL.relative_to(REPO_ROOT)}")
        print(f"would sync {len(rows)} registry rows from {args.csv_path}")
        return 0

    prepare_table_for_sync(db_url)
    row_count = sync_registry(db_url, args.csv_path)
    apply_schema(db_url)
    print(f"synced {row_count} registry rows from {args.csv_path}")

    if not args.no_export:
        export_registry_csv(db_url, args.csv_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

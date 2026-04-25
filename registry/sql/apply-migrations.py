#!/usr/bin/env python3
"""Apply trading-main registry PostgreSQL migrations exactly once.

The database URL is read from OPENCLAW_DATABASE_URL when set, otherwise
from the local secret alias file /root/secrets/openclaw/database-url.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = Path(__file__).resolve().parent / "schema_migrations"
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")


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


def run_psql(db_url: str, sql: str | None = None, file: Path | None = None, quiet: bool = False) -> str:
    cmd = ["psql", db_url, "-v", "ON_ERROR_STOP=1"]
    if quiet:
        cmd.append("-q")
    if sql is not None:
        cmd.extend(["-Atc", sql])
    elif file is not None:
        cmd.extend(["-f", str(file)])
    else:
        raise ValueError("sql or file is required")
    result = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    if not quiet and result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.stdout


def ensure_ledger(db_url: str) -> None:
    run_psql(
        db_url,
        sql="""
        CREATE TABLE IF NOT EXISTS trading_registry_schema_migrations (
          version TEXT PRIMARY KEY,
          filename TEXT NOT NULL,
          checksum_sha256 TEXT NOT NULL,
          applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """,
        quiet=True,
    )


def applied_migrations(db_url: str) -> dict[str, str]:
    output = run_psql(db_url, sql="SELECT version || ' ' || checksum_sha256 FROM trading_registry_schema_migrations ORDER BY version;", quiet=True)
    applied: dict[str, str] = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        version, checksum = line.split(" ", 1)
        applied[version] = checksum
    return applied


def migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def migration_version(path: Path) -> str:
    return path.name.split("_", 1)[0]


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def apply_migration(db_url: str, path: Path, digest: str, dry_run: bool) -> None:
    version = migration_version(path)
    if dry_run:
        print(f"would apply {path.name} {digest}")
        return
    print(f"applying {path.name}")
    run_psql(db_url, file=path)
    run_psql(
        db_url,
        sql=(
            "INSERT INTO trading_registry_schema_migrations (version, filename, checksum_sha256) VALUES ("
            f"{sql_literal(version)}, {sql_literal(path.name)}, {sql_literal(digest)}"
            ");"
        ),
        quiet=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show pending migrations without applying")
    args = parser.parse_args()

    db_url = database_url()
    ensure_ledger(db_url)
    applied = applied_migrations(db_url)

    pending = 0
    for path in migration_files():
        version = migration_version(path)
        digest = checksum(path)
        if version in applied:
            if applied[version] != digest:
                raise SystemExit(
                    f"migration {version} checksum mismatch: "
                    f"database={applied[version]} file={digest}"
                )
            print(f"already applied {path.name}")
            continue
        pending += 1
        apply_migration(db_url, path, digest, args.dry_run)

    if pending == 0:
        print("no pending migrations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify ``scripts/registry/current.csv`` matches the database registry table."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SYNC = REPO_ROOT / "scripts/registry/sync_registry.py"
CURRENT = REPO_ROOT / "scripts/registry/current.csv"
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")


def database_available() -> bool:
    return bool(os.environ.get("OPENCLAW_DATABASE_URL", "").strip()) or DEFAULT_DB_URL_FILE.exists()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-missing-db", action="store_true", help="skip instead of failing when no database URL is configured")
    args = parser.parse_args()

    if not database_available():
        message = "OPENCLAW_DATABASE_URL is unset and /root/secrets/openclaw/database-url does not exist"
        if args.allow_missing_db:
            print(f"registry DB check skipped: {message}")
            return 0
        raise SystemExit(f"registry DB check failed: {message}")

    with tempfile.TemporaryDirectory() as tmp:
        exported = Path(tmp) / "current.csv"
        result = subprocess.run(
            [sys.executable, str(SYNC), "--export-only", "--csv-path", str(exported)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout, file=sys.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")
            return result.returncode
        if CURRENT.read_bytes() != exported.read_bytes():
            raise SystemExit("registry DB check failed: scripts/registry/current.csv differs from database export")
    print("registry DB snapshot OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

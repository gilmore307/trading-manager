#!/usr/bin/env python3
"""Verify scripts/registry/current.csv matches a fresh database export."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APPLY = REPO_ROOT / "scripts/registry/apply_registry_migrations.py"
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
            print(f"registry snapshot check skipped: {message}")
            return 0
        raise SystemExit(f"registry snapshot check failed: {message}")

    with tempfile.TemporaryDirectory() as tmp:
        exported = Path(tmp) / "current.csv"
        result = subprocess.run(
            [sys.executable, str(APPLY), "--export-only", "--csv-path", str(exported)],
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
            raise SystemExit("registry snapshot check failed: scripts/registry/current.csv differs from fresh database export")
    print("registry snapshot OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

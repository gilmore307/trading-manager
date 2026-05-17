#!/usr/bin/env python3
"""Validate checked-in contract fixtures against their JSON schemas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = REPO_ROOT / "schemas"
DEFAULT_FIXTURES_DIR = REPO_ROOT / "tests/fixtures/contracts"


def schema_path_for_fixture(path: Path) -> Path:
    return SCHEMAS_DIR / f"{path.stem}.schema.json"


def validate_fixture(path: Path) -> None:
    schema_path = schema_path_for_fixture(path)
    if not schema_path.exists():
        raise SystemExit(f"missing schema for fixture {path.relative_to(REPO_ROOT)}: {schema_path.relative_to(REPO_ROOT)}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(f"/{'/'.join(str(part) for part in error.path)}: {error.message}" for error in errors)
        raise SystemExit(f"contract fixture validation failed for {path.relative_to(REPO_ROOT)}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="specific fixture paths; defaults to tests/fixtures/contracts/*.json")
    args = parser.parse_args()
    paths = args.paths or sorted(DEFAULT_FIXTURES_DIR.glob("*.json"))
    if not paths:
        raise SystemExit("no contract fixtures found")
    for path in paths:
        validate_fixture(path if path.is_absolute() else REPO_ROOT / path)
    print(f"contract examples OK ({len(paths)} fixtures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

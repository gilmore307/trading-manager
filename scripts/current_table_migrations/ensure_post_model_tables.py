#!/usr/bin/env python3
"""Create registered post-model evaluation/execution SQL tables if missing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from trading_manager_tasks.post_model_schema import ensure_post_model_tables


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url")
    parser.add_argument("--registry-csv", type=Path)
    args = parser.parse_args(argv)

    kwargs = {"database_url_value": args.database_url}
    if args.registry_csv is not None:
        kwargs["registry_csv"] = args.registry_csv
    result = ensure_post_model_tables(**kwargs)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verification_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

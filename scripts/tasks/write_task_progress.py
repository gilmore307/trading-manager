#!/usr/bin/env python3
"""Write active manager task progress from a stage subprocess."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from trading_manager_tasks.task_progress import write_task_progress_from_env


def _json_object(value: str | None) -> dict[str, Any] | None:
    if not value:
        return None
    payload = json.loads(value)
    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError("--extra-json must decode to a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", default="running")
    parser.add_argument("--unit-label", default=None)
    parser.add_argument("--processed-count", type=int, default=None)
    parser.add_argument("--expected-count", type=int, default=None)
    parser.add_argument("--elapsed-seconds", type=float, default=None)
    parser.add_argument("--expected-seconds", type=float, default=None)
    parser.add_argument("--node-id", default=None)
    parser.add_argument("--node-label", default=None)
    parser.add_argument("--extra-json", default=None)
    args = parser.parse_args(argv)
    write_task_progress_from_env(
        status=args.status,
        unit_label=args.unit_label,
        processed_count=args.processed_count,
        expected_count=args.expected_count,
        elapsed_seconds=args.elapsed_seconds,
        expected_seconds=args.expected_seconds,
        node_id=args.node_id,
        node_label=args.node_label,
        extra=_json_object(args.extra_json),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

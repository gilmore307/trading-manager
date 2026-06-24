#!/usr/bin/env python3
"""Run model-group replay review when ready."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trading_manager_tasks.model_group_attribution import run_model_group_replay_review_if_ready


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default="promotion_replay_candidate_policy")
    parser.add_argument("--replay-execution-run-id", help="Specific replay execution run to review instead of the latest compatible run")
    parser.add_argument("--max-review-rows", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="write a fresh replay review even when one already exists for this replay")
    parser.add_argument(
        "--allow-partial-replay",
        action="store_true",
        help="write a diagnostic replay review for the latest completed replay run without unlocking downstream full-review gates",
    )
    args = parser.parse_args(argv)

    decision = run_model_group_replay_review_if_ready(
        storage_root=args.storage_root,
        contract_id=args.contract_id,
        replay_execution_run_id=args.replay_execution_run_id,
        execute=not args.dry_run,
        max_review_rows=args.max_review_rows,
        force=args.force,
        allow_partial_replay=args.allow_partial_replay,
    )
    if decision is None:
        print(json.dumps({"status": "not_ready", "reason_code": "model_group_replay_review_not_ready"}, sort_keys=True))
        return 0
    print(json.dumps(decision.summary_row(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

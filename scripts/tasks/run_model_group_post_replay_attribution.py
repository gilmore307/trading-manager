#!/usr/bin/env python3
"""Run model-group post-replay Layer 10 attribution when ready."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trading_manager_tasks.model_group_attribution import run_model_group_post_replay_attribution_if_ready


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default="promotion_replay_candidate_policy")
    parser.add_argument("--max-attribution-rows", type=int)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    decision = run_model_group_post_replay_attribution_if_ready(
        storage_root=args.storage_root,
        contract_id=args.contract_id,
        execute=not args.dry_run,
        max_attribution_rows=args.max_attribution_rows,
    )
    if decision is None:
        print(json.dumps({"status": "not_ready", "reason_code": "model_group_post_replay_attribution_not_ready"}, sort_keys=True))
        return 0
    print(json.dumps(decision.summary_row(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prepare, acquire, or freeze model-group replay dataset when ready."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from trading_manager_tasks.model_group_replay_dataset import run_model_group_replay_dataset_if_ready


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default="promotion_replay_candidate_policy")
    parser.add_argument("--target-symbol")
    parser.add_argument("--contract-path", type=Path, default=Path("/root/projects/trading-evaluation/replays/promotion_replay_candidate_policy.json"))
    parser.add_argument("--evaluation-repo-root", type=Path, default=Path("/root/projects/trading-evaluation"))
    parser.add_argument("--trading-data-repo-root", type=Path, default=Path("/root/projects/trading-data"))
    parser.add_argument("--source-data-root", type=Path, default=Path("/root/projects/trading-storage/storage/01_source_data"))
    parser.add_argument("--provider-acquisition-limit", type=int, default=1)
    parser.add_argument("--execute-provider-acquisition", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)

    decision = run_model_group_replay_dataset_if_ready(
        storage_root=args.storage_root,
        contract_id=args.contract_id,
        execute=not args.plan_only,
        execute_provider_acquisition=args.execute_provider_acquisition,
        provider_acquisition_limit=args.provider_acquisition_limit,
        selected_target_symbol=args.target_symbol,
        contract_path=args.contract_path,
        evaluation_repo_root=args.evaluation_repo_root,
        trading_data_repo_root=args.trading_data_repo_root,
        source_data_root=args.source_data_root,
    )
    if decision is None:
        print(json.dumps({"status": "not_ready", "reason_code": "model_group_replay_dataset_prerequisite_not_ready"}, sort_keys=True))
        return 0
    print(json.dumps(decision.summary_row(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

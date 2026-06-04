#!/usr/bin/env python3
"""Dispatch side-effect-free model-group replay when prerequisites are ready."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from trading_manager_tasks.model_group_replay import run_model_group_replay_if_ready


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default="promotion_replay_candidate_policy")
    parser.add_argument("--target-symbol")
    parser.add_argument("--runner-path", type=Path, default=Path("/root/projects/trading-evaluation/scripts/evaluation/run_replay_execution.py"))
    parser.add_argument("--evaluation-repo-root", type=Path, default=Path("/root/projects/trading-evaluation"))
    parser.add_argument("--execution-repo-root", type=Path, default=Path("/root/projects/trading-execution"))
    parser.add_argument("--model-repo-root", type=Path, default=Path("/root/projects/trading-model"))
    parser.add_argument("--equity-symbol-pool-path", type=Path)
    parser.add_argument("--max-decision-rows", type=int)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)

    decision = run_model_group_replay_if_ready(
        storage_root=args.storage_root,
        contract_id=args.contract_id,
        execute=not args.plan_only,
        runner_path=args.runner_path,
        evaluation_repo_root=args.evaluation_repo_root,
        execution_repo_root=args.execution_repo_root,
        model_repo_root=args.model_repo_root,
        equity_symbol_pool_path=args.equity_symbol_pool_path,
        selected_target_symbol=args.target_symbol,
        max_decision_rows=args.max_decision_rows,
    )
    if decision is None:
        print(json.dumps({"status": "not_ready", "reason_code": "model_group_replay_prerequisite_not_ready"}, sort_keys=True))
        return 0
    print(json.dumps(decision.summary_row(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run model-group evaluation when replay and residual-event audit are ready."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.model_group_evaluation import run_model_group_evaluation_if_ready


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default="promotion_replay_candidate_policy")
    parser.add_argument("--target-symbol")
    parser.add_argument("--start-month", help="Select a specific completed training fold start month")
    parser.add_argument("--end-month", help="Select a specific completed training fold end month")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="write a fresh evaluation run even when one already exists for this replay")
    parser.add_argument("--local-fallback-review", action="store_true", help="write deterministic insufficient-evidence review without invoking Codex")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-model")
    parser.add_argument("--codex-timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    decision = run_model_group_evaluation_if_ready(
        storage_root=args.storage_root,
        contract_id=args.contract_id,
        selected_target_symbol=args.target_symbol,
        execute=not args.dry_run,
        force=args.force,
        call_agent_review=not args.local_fallback_review,
        selected_start_month=args.start_month,
        selected_end_month=args.end_month,
        codex_bin=args.codex_bin,
        codex_model=args.codex_model,
        codex_timeout_seconds=args.codex_timeout_seconds,
    )
    if decision is None:
        print(json.dumps({"status": "not_ready", "reason_code": "model_group_evaluation_not_ready"}, sort_keys=True))
        return 0
    print(json.dumps(decision.summary_row(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

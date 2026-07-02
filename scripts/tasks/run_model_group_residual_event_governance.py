#!/usr/bin/env python3
"""Run model-group post-replay M06 ResidualEventGovernance attribution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from trading_manager_tasks.model_group_residual_event_governance import run_model_group_residual_event_governance_if_ready


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default="promotion_replay_candidate_policy")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="write a fresh residual-event audit run even when one already exists for this replay")
    parser.add_argument("--local-fallback-review", action="store_true", help="write deterministic event-family review fallbacks without invoking Codex")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-model")
    parser.add_argument("--codex-timeout-seconds", type=int, default=900)
    parser.add_argument("--max-agent-review-packets", type=int, default=3)
    args = parser.parse_args(argv)

    decision = run_model_group_residual_event_governance_if_ready(
        storage_root=args.storage_root,
        contract_id=args.contract_id,
        execute=not args.dry_run,
        force=args.force,
        call_agent_review=not args.local_fallback_review,
        codex_bin=args.codex_bin,
        codex_model=args.codex_model,
        codex_timeout_seconds=args.codex_timeout_seconds,
        max_agent_review_packets=args.max_agent_review_packets,
    )
    if decision is None:
        print(json.dumps({"status": "not_ready", "reason_code": "model_group_residual_event_governance_not_ready"}, sort_keys=True))
        return 0
    print(json.dumps(decision.summary_row(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Plan the manager-owned post-replay M06 workflow lane."""

from __future__ import annotations

import argparse
import sys

from trading_manager_tasks.model_training_workflow import (
    build_model_06_post_replay_workflow_plan,
    write_post_replay_workflow_plan,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2017-06")
    parser.add_argument("--target-symbol", help="Replay-scoped target symbol for the M06 post-replay lane.")
    parser.add_argument("--replay-review-complete", action="store_true")
    parser.add_argument("--event-universe-acquired", action="store_true")
    parser.add_argument("--modelability-gates-complete", action="store_true")
    parser.add_argument("--residual-attribution-complete", action="store_true")
    parser.add_argument("--evaluation-complete", action="store_true")
    parser.add_argument("--promotion-review-complete", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = build_model_06_post_replay_workflow_plan(
            start_month=args.start_month,
            end_month=args.end_month,
            selected_target_symbol=args.target_symbol,
            replay_review_complete=args.replay_review_complete,
            event_universe_acquired=args.event_universe_acquired,
            modelability_gates_complete=args.modelability_gates_complete,
            residual_attribution_complete=args.residual_attribution_complete,
            evaluation_complete=args.evaluation_complete,
            promotion_review_complete=args.promotion_review_complete,
        )
    except ValueError as exc:
        parser.error(str(exc))
    write_post_replay_workflow_plan(plan, output=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

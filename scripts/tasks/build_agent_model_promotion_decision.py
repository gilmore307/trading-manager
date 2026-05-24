#!/usr/bin/env python3
"""Build a script-called agent model-promotion decision artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from trading_manager_tasks.review_decision import build_agent_model_promotion_decision, write_artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build agent_model_promotion_decision artifacts without activation side effects.")
    parser.add_argument("--promotion-request-ref", required=True)
    parser.add_argument("--agent-ref", default="codex_cli_gpt_5_5")
    parser.add_argument("--decision-status", required=True, choices=("approve", "defer", "reject", "revoke", "supersede"))
    parser.add_argument("--decision-reason", required=True)
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--advisory-review-ref", action="append", default=[])
    parser.add_argument("--condition", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    decision = build_agent_model_promotion_decision(
        promotion_request_ref=args.promotion_request_ref,
        agent_ref=args.agent_ref,
        decision_status=args.decision_status,
        decision_reason=args.decision_reason,
        evidence_refs=args.evidence_ref,
        advisory_review_refs=args.advisory_review_ref,
        conditions=args.condition,
    )
    write_artifact(decision, output=sys.stdout, path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

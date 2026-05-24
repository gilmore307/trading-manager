#!/usr/bin/env python3
"""Build a script-called agent storage-lifecycle decision artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ALLOWED_DECISIONS = ("approve", "defer", "reject", "revoke", "supersede")


def _stable_id(*parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return "agstorlife_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build agent_storage_lifecycle_decision artifacts without storage mutation side effects.")
    parser.add_argument("--storage-lifecycle-request-ref", required=True)
    parser.add_argument("--agent-ref", default="codex_cli_gpt_5_5")
    parser.add_argument("--decision-status", required=True, choices=ALLOWED_DECISIONS)
    parser.add_argument("--decision-reason", required=True)
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--condition", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    decision = {
        "contract_type": "agent_storage_lifecycle_decision",
        "agent_storage_lifecycle_decision_id": _stable_id(
            args.storage_lifecycle_request_ref,
            args.agent_ref,
            args.decision_status,
            args.decision_reason,
            args.evidence_ref,
            args.condition,
        ),
        "storage_lifecycle_request_ref": args.storage_lifecycle_request_ref,
        "agent_ref": args.agent_ref,
        "decision_status": args.decision_status,
        "decision_reason": args.decision_reason,
        "evidence_refs": [str(item) for item in args.evidence_ref],
        "conditions": [str(item) for item in args.condition],
        "owner_observed_automation": True,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    content = json.dumps(decision, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

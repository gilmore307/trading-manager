"""Build advisory review and agent promotion-decision artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, TextIO

from .control_plane import TaskSystemError

REVIEW_DECISION_CONTRACT = "review_decision"
AGENT_MODEL_PROMOTION_DECISION_CONTRACT = "agent_model_promotion_decision"
ALLOWED_DECISION_STATUSES = {"approve", "defer", "reject", "revoke", "supersede"}


def _now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_id(prefix: str, *parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def _as_list(values: Iterable[str] | None) -> list[str]:
    return [str(value) for value in values or []]


def build_review_decision(
    *,
    review_target_ref: str,
    reviewer_ref: str,
    decision_status: Literal["approve", "defer", "reject", "revoke", "supersede"],
    decision_reason: str,
    conditions: Iterable[str] | None = None,
    evidence_refs: Iterable[str] | None = None,
    review_decision_id: str | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build an advisory review_decision artifact.

    This artifact may support evaluation evidence, but it is not sufficient for
    model activation. Activation belongs to `trading-evaluation`.
    """

    if decision_status not in ALLOWED_DECISION_STATUSES:
        raise TaskSystemError(f"decision_status must be one of: {', '.join(sorted(ALLOWED_DECISION_STATUSES))}")
    if not review_target_ref:
        raise TaskSystemError("review_target_ref is required")
    if not reviewer_ref:
        raise TaskSystemError("reviewer_ref is required")
    if not decision_reason:
        raise TaskSystemError("decision_reason is required")
    normalized_conditions = _as_list(conditions)
    normalized_evidence = _as_list(evidence_refs)
    decision_id = review_decision_id or _stable_id("revdec", review_target_ref, reviewer_ref, decision_status, decision_reason, normalized_conditions, normalized_evidence)
    decision = {
        "contract_type": REVIEW_DECISION_CONTRACT,
        "review_decision_id": decision_id,
        "review_target_ref": review_target_ref,
        "reviewer_ref": reviewer_ref,
        "decision_status": decision_status,
        "decision_reason": decision_reason,
        "conditions": normalized_conditions,
        "evidence_refs": normalized_evidence,
        "created_at_utc": created_at_utc or _now_utc(),
    }
    validate_review_decision(decision)
    return decision


def validate_review_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a review_decision artifact and return a normalized copy."""

    required = (
        "contract_type",
        "review_decision_id",
        "review_target_ref",
        "reviewer_ref",
        "decision_status",
        "decision_reason",
        "conditions",
        "created_at_utc",
    )
    normalized = dict(decision)
    for field in required:
        value = normalized.get(field)
        if value in (None, ""):
            raise TaskSystemError(f"missing required review decision field: {field}")
    if normalized["contract_type"] != REVIEW_DECISION_CONTRACT:
        raise TaskSystemError(f"contract_type must be {REVIEW_DECISION_CONTRACT}")
    if normalized["decision_status"] not in ALLOWED_DECISION_STATUSES:
        raise TaskSystemError(f"unsupported decision_status: {normalized['decision_status']}")
    if not isinstance(normalized.get("conditions"), list):
        raise TaskSystemError("conditions must be a list")
    evidence_refs = normalized.get("evidence_refs", [])
    if not isinstance(evidence_refs, list):
        raise TaskSystemError("evidence_refs must be a list")
    normalized["evidence_refs"] = evidence_refs
    return normalized


def build_agent_model_promotion_decision(
    *,
    promotion_request_ref: str,
    agent_ref: str,
    decision_status: Literal["approve", "defer", "reject", "revoke", "supersede"],
    decision_reason: str,
    evidence_refs: Iterable[str] | None = None,
    advisory_review_refs: Iterable[str] | None = None,
    conditions: Iterable[str] | None = None,
    decision_id: str | None = None,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build the required script-called agent decision for model promotion."""

    if decision_status not in ALLOWED_DECISION_STATUSES:
        raise TaskSystemError(f"decision_status must be one of: {', '.join(sorted(ALLOWED_DECISION_STATUSES))}")
    if not promotion_request_ref:
        raise TaskSystemError("promotion_request_ref is required")
    if not agent_ref:
        raise TaskSystemError("agent_ref is required")
    if not decision_reason:
        raise TaskSystemError("decision_reason is required")
    normalized_evidence = _as_list(evidence_refs)
    normalized_reviews = _as_list(advisory_review_refs)
    normalized_conditions = _as_list(conditions)
    stable_decision_id = decision_id or _stable_id(
        "agpromodec",
        promotion_request_ref,
        agent_ref,
        decision_status,
        decision_reason,
        normalized_evidence,
        normalized_reviews,
        normalized_conditions,
    )
    decision = {
        "contract_type": AGENT_MODEL_PROMOTION_DECISION_CONTRACT,
        "agent_model_promotion_decision_id": stable_decision_id,
        "promotion_request_ref": promotion_request_ref,
        "agent_ref": agent_ref,
        "decision_status": decision_status,
        "decision_reason": decision_reason,
        "evidence_refs": normalized_evidence,
        "advisory_review_refs": normalized_reviews,
        "conditions": normalized_conditions,
        "owner_observed_automation": True,
        "created_at_utc": created_at_utc or _now_utc(),
    }
    validate_agent_model_promotion_decision(decision)
    return decision


def validate_agent_model_promotion_decision(decision: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an agent_model_promotion_decision artifact."""

    required = (
        "contract_type",
        "agent_model_promotion_decision_id",
        "promotion_request_ref",
        "agent_ref",
        "decision_status",
        "decision_reason",
        "evidence_refs",
        "conditions",
        "created_at_utc",
    )
    normalized = dict(decision)
    for field in required:
        value = normalized.get(field)
        if value in (None, ""):
            raise TaskSystemError(f"missing required agent model promotion decision field: {field}")
    if normalized["contract_type"] != AGENT_MODEL_PROMOTION_DECISION_CONTRACT:
        raise TaskSystemError(f"contract_type must be {AGENT_MODEL_PROMOTION_DECISION_CONTRACT}")
    if normalized["decision_status"] not in ALLOWED_DECISION_STATUSES:
        raise TaskSystemError(f"unsupported decision_status: {normalized['decision_status']}")
    for field in ("evidence_refs", "advisory_review_refs", "conditions"):
        if field not in normalized:
            normalized[field] = []
        if not isinstance(normalized[field], list):
            raise TaskSystemError(f"{field} must be a list")
    normalized["owner_observed_automation"] = bool(normalized.get("owner_observed_automation", False))
    return normalized


def write_artifact(payload: Mapping[str, Any], *, output: TextIO | None = None, path: Path | None = None) -> None:
    content = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if output is not None:
        output.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build advisory review_decision artifacts without activation side effects.")
    parser.add_argument("--review-target-ref", required=True)
    parser.add_argument("--reviewer-ref", default="openclaw")
    parser.add_argument("--decision-status", required=True, choices=tuple(sorted(ALLOWED_DECISION_STATUSES)))
    parser.add_argument("--decision-reason", required=True)
    parser.add_argument("--condition", action="append", default=[])
    parser.add_argument("--evidence-ref", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    decision = build_review_decision(
        review_target_ref=args.review_target_ref,
        reviewer_ref=args.reviewer_ref,
        decision_status=args.decision_status,
        decision_reason=args.decision_reason,
        conditions=args.condition,
        evidence_refs=args.evidence_ref,
    )
    write_artifact(decision, output=sys.stdout, path=args.output)
    return 0


__all__ = [
    "AGENT_MODEL_PROMOTION_DECISION_CONTRACT",
    "ALLOWED_DECISION_STATUSES",
    "REVIEW_DECISION_CONTRACT",
    "build_agent_model_promotion_decision",
    "build_review_decision",
    "validate_agent_model_promotion_decision",
    "validate_review_decision",
    "write_artifact",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

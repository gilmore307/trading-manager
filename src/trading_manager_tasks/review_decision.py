"""Build and validate unified review decision and activation artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, TextIO

from .control_plane import TaskSystemError

REVIEW_DECISION_CONTRACT = "review_decision_v1"
ACTIVATION_RECORD_CONTRACT = "activation_record_v1"
APPROVING_STATUS = "approve"
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
    """Build a generic review_decision_v1 artifact."""

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
    """Validate a review_decision_v1 artifact and return a normalized copy."""

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


def build_activation_record(
    *,
    review_decision: Mapping[str, Any],
    activated_component: str,
    activated_config_ref: str,
    rollback_ref: str,
    activated_by: str,
    replaced_config_ref: str | None = None,
    activation_record_id: str | None = None,
    activated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build an activation_record_v1 only from an approving review decision."""

    decision = validate_review_decision(review_decision)
    if decision["decision_status"] != APPROVING_STATUS:
        raise TaskSystemError("activation_record_v1 requires approving review_decision_v1")
    for field_name, value in {
        "activated_component": activated_component,
        "activated_config_ref": activated_config_ref,
        "rollback_ref": rollback_ref,
        "activated_by": activated_by,
    }.items():
        if not value:
            raise TaskSystemError(f"{field_name} is required")
    activation_id = activation_record_id or _stable_id(
        "actrec",
        decision["review_decision_id"],
        activated_component,
        activated_config_ref,
        replaced_config_ref,
        rollback_ref,
    )
    activation = {
        "contract_type": ACTIVATION_RECORD_CONTRACT,
        "activation_record_id": activation_id,
        "activated_component": activated_component,
        "approved_review_decision_ref": decision["review_decision_id"],
        "activated_config_ref": activated_config_ref,
        "replaced_config_ref": replaced_config_ref,
        "rollback_ref": rollback_ref,
        "activated_at_utc": activated_at_utc or _now_utc(),
        "activated_by": activated_by,
    }
    validate_activation_record(activation, review_decision=decision)
    return activation


def validate_activation_record(activation: Mapping[str, Any], *, review_decision: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate activation_record_v1 boundary rules."""

    normalized = dict(activation)
    required = (
        "contract_type",
        "activation_record_id",
        "activated_component",
        "approved_review_decision_ref",
        "activated_config_ref",
        "rollback_ref",
        "activated_at_utc",
        "activated_by",
    )
    for field in required:
        if normalized.get(field) in (None, ""):
            raise TaskSystemError(f"missing required activation record field: {field}")
    if normalized["contract_type"] != ACTIVATION_RECORD_CONTRACT:
        raise TaskSystemError(f"contract_type must be {ACTIVATION_RECORD_CONTRACT}")
    if review_decision is not None:
        decision = validate_review_decision(review_decision)
        if decision["decision_status"] != APPROVING_STATUS:
            raise TaskSystemError("activation_record_v1 requires approving review_decision_v1")
        if normalized["approved_review_decision_ref"] != decision["review_decision_id"]:
            raise TaskSystemError("activation approved_review_decision_ref does not match review decision")
    return normalized


def write_artifact(payload: Mapping[str, Any], *, output: TextIO | None = None, path: Path | None = None) -> None:
    content = json.dumps(dict(payload), indent=2, sort_keys=True) + "\n"
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    if output is not None:
        output.write(content)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build unified review_decision_v1 artifacts without activation side effects.")
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
    "ACTIVATION_RECORD_CONTRACT",
    "ALLOWED_DECISION_STATUSES",
    "REVIEW_DECISION_CONTRACT",
    "build_activation_record",
    "build_review_decision",
    "validate_activation_record",
    "validate_review_decision",
    "write_artifact",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

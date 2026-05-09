"""Validate manager live-call approval artifacts before provider dispatch.

The manager gate is intentionally a validator, not a dispatcher. It proves that a
non-dry-run request has an explicit reviewed approval boundary before any
component is allowed to perform provider/API calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError, load_json_or_jsonl, validate_manager_request

LIVE_CALL_APPROVAL_CONTRACT = "live_call_approval_v1"
LIVE_CALL_GATE_POLICY_REF = "live_call_approval_gate_v1"
LIVE_CALL_POLICY_REQUIRED_REF = "live_call_policy_required"
_ALLOWED_DECISIONS = {"approve", "approved"}
_ALLOWED_TARGET_KINDS = {"data_feed", "data_source"}
_PROVIDER_ALIASES = {
    "alpaca_bars": "alpaca",
    "alpaca_liquidity": "alpaca",
    "alpaca_news": "alpaca",
    "gdelt_news": "gdelt",
    "okx_crypto_market_data": "okx",
    "sec_company_financials": "sec_edgar",
    "thetadata_option_primary_tracking": "thetadata",
    "thetadata_option_event_timeline": "thetadata",
}


@dataclass(frozen=True)
class LiveCallApprovalValidation:
    """Summary of one approved live-call gate validation."""

    request_id: str
    approval_id: str
    target_component_id: str
    target_repo_id: str
    allowed_providers: tuple[str, ...]
    max_requests: int
    max_window_days: int
    status: str = "approved_for_live_provider_handoff"
    dispatch_performed: bool = False
    provider_calls: int = 0

    def summary_row(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "approval_id": self.approval_id,
            "target_component_id": self.target_component_id,
            "target_repo_id": self.target_repo_id,
            "allowed_providers": list(self.allowed_providers),
            "max_requests": self.max_requests,
            "max_window_days": self.max_window_days,
            "status": self.status,
            "dispatch_performed": self.dispatch_performed,
            "provider_calls": self.provider_calls,
        }


def _required(mapping: Mapping[str, Any], key: str) -> Any:
    value = mapping.get(key)
    if value in (None, "", []):
        raise TaskSystemError(f"missing required live-call approval field: {key}")
    return value


def _list(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _parse_utc(value: Any, *, field_name: str) -> datetime:
    text = str(_required({field_name: value}, field_name))
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise TaskSystemError(f"{field_name} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None:
        raise TaskSystemError(f"{field_name} must include UTC timezone")
    return parsed.astimezone(UTC)


def _component_source_id(component_id: str) -> str:
    marker = "_feed_"
    if marker not in component_id:
        return component_id
    return component_id.split(marker, 1)[1]


def _provider_candidates(component_id: str) -> set[str]:
    source_id = _component_source_id(component_id).lower()
    candidates = {source_id}
    if source_id in _PROVIDER_ALIASES:
        candidates.add(_PROVIDER_ALIASES[source_id])
    if "_" in source_id:
        candidates.add(source_id.split("_", 1)[0])
    return candidates


def _window_days(request: Mapping[str, Any]) -> int | None:
    start = request.get("start_date")
    end = request.get("end_date_exclusive")
    if not start or not end:
        return None
    try:
        start_date = datetime.fromisoformat(str(start)).date()
        end_date = datetime.fromisoformat(str(end)).date()
    except ValueError as exc:
        raise TaskSystemError("request start_date/end_date_exclusive must be ISO dates") from exc
    return (end_date - start_date).days


def validate_live_call_approval(
    request_row: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    now_utc: datetime | None = None,
) -> LiveCallApprovalValidation:
    """Validate that `approval` permits live provider handoff for `request_row`.

    This function does not call providers, import component pipelines, dispatch
    tasks, or mutate SQL. It only validates the manager-side approval artifact.
    """

    request = validate_manager_request(request_row)
    if request.get("dry_run", True):
        raise TaskSystemError("live-call approval gate only applies to non-dry-run manager requests")
    if request["target_repo_id"] != "trading-data":
        raise TaskSystemError("live-call approval gate v1 only permits trading-data provider acquisition")
    if request["target_component_kind"] not in _ALLOWED_TARGET_KINDS:
        raise TaskSystemError("live-call approval gate v1 only permits data_feed/data_source targets")

    policy_refs = {str(item) for item in request.get("policy_refs") or []}
    if LIVE_CALL_POLICY_REQUIRED_REF not in policy_refs:
        raise TaskSystemError("request.policy_refs must include live_call_policy_required")
    if LIVE_CALL_GATE_POLICY_REF not in policy_refs:
        raise TaskSystemError("request.policy_refs must include live_call_approval_gate_v1")

    if approval.get("contract_type") != LIVE_CALL_APPROVAL_CONTRACT:
        raise TaskSystemError(f"approval.contract_type must be {LIVE_CALL_APPROVAL_CONTRACT}")
    decision = str(_required(approval, "decision_status")).strip().lower()
    if decision not in _ALLOWED_DECISIONS:
        raise TaskSystemError("live-call approval decision_status must be approve/approved")

    approval_id = str(_required(approval, "approval_id"))
    _required(approval, "approved_by")
    _parse_utc(approval.get("approved_at_utc"), field_name="approved_at_utc")
    expires_at = _parse_utc(approval.get("expires_at_utc"), field_name="expires_at_utc")
    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    if expires_at <= now:
        raise TaskSystemError("live-call approval is expired")

    request_ids = {str(item) for item in _list(approval.get("request_ids") or approval.get("request_id"))}
    if request["request_id"] not in request_ids:
        raise TaskSystemError("approval.request_ids must include the manager request_id")

    if str(approval.get("approval_scope") or "") != "provider_data_acquisition_only":
        raise TaskSystemError("approval_scope must be provider_data_acquisition_only")
    if approval.get("broker_execution_allowed") not in (False, None):
        raise TaskSystemError("broker_execution_allowed must be false for live provider acquisition")

    allowed_providers = tuple(str(item).lower() for item in _list(_required(approval, "allowed_providers")))
    if not allowed_providers:
        raise TaskSystemError("allowed_providers must not be empty")
    if _provider_candidates(request["target_component_id"]).isdisjoint(set(allowed_providers)):
        raise TaskSystemError("allowed_providers does not cover the request target provider")

    try:
        max_requests = int(_required(approval, "max_requests"))
        max_window_days = int(_required(approval, "max_window_days"))
    except (TypeError, ValueError) as exc:
        raise TaskSystemError("max_requests and max_window_days must be integers") from exc
    if max_requests <= 0:
        raise TaskSystemError("max_requests must be greater than zero")
    if max_window_days <= 0:
        raise TaskSystemError("max_window_days must be greater than zero")

    request_window_days = _window_days(request_row)
    if request_window_days is not None and request_window_days > max_window_days:
        raise TaskSystemError("request time window exceeds approved max_window_days")

    return LiveCallApprovalValidation(
        request_id=str(request["request_id"]),
        approval_id=approval_id,
        target_component_id=str(request["target_component_id"]),
        target_repo_id=str(request["target_repo_id"]),
        allowed_providers=allowed_providers,
        max_requests=max_requests,
        max_window_days=max_window_days,
    )


def validate_live_call_approvals(
    request_rows: Iterable[Mapping[str, Any]],
    approval: Mapping[str, Any],
    *,
    now_utc: datetime | None = None,
) -> list[LiveCallApprovalValidation]:
    rows = list(request_rows)
    validations = [validate_live_call_approval(row, approval, now_utc=now_utc) for row in rows]
    if validations:
        max_requests = validations[0].max_requests
        if len(validations) > max_requests:
            raise TaskSystemError("approved request batch exceeds approval.max_requests")
        request_ids = {str(item) for item in _list(approval.get("request_ids") or approval.get("request_id"))}
        missing = [validation.request_id for validation in validations if validation.request_id not in request_ids]
        if missing:
            raise TaskSystemError("approval.request_ids must include every manager request_id in the batch")
    return validations


def write_live_call_gate_output(
    validations: Sequence[LiveCallApprovalValidation],
    *,
    output: TextIO,
    output_format: Literal["jsonl", "json"] = "jsonl",
) -> None:
    rows = [item.summary_row() for item in validations]
    if output_format == "json":
        json.dump(rows, output, indent=2, sort_keys=True)
        output.write("\n")
        return
    for row in rows:
        output.write(json.dumps(row, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate live_call_approval_v1 artifacts before provider dispatch.")
    parser.add_argument("requests", type=Path, help="JSON, JSON array, or JSONL manager_request_v1 rows.")
    parser.add_argument("--approval", required=True, type=Path, help="live_call_approval_v1 JSON artifact.")
    parser.add_argument("--format", choices=("jsonl", "json"), default="jsonl")
    args = parser.parse_args(argv)

    request_rows = load_json_or_jsonl(args.requests)
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    if not isinstance(approval, Mapping):
        raise TaskSystemError("approval artifact must be a JSON object")
    validations = validate_live_call_approvals(request_rows, approval)
    write_live_call_gate_output(validations, output=sys.stdout, output_format=args.format)
    return 0


__all__ = [
    "LIVE_CALL_APPROVAL_CONTRACT",
    "LIVE_CALL_GATE_POLICY_REF",
    "LiveCallApprovalValidation",
    "validate_live_call_approval",
    "validate_live_call_approvals",
    "write_live_call_gate_output",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

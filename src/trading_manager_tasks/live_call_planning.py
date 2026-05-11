"""Plan reviewed live-call approval scopes without dispatching providers.

The output is deliberately a proposal/template, not an approval. It selects the
exact request ids that a future `live_call_approval_v1` could cover, excludes
registered accepted skips, can exclude already terminal stage-coverage requests,
and keeps provider_calls at zero.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .failure_register import accepted_failure_request_ids_from_register
from .historical_training import prepare_layer_historical_training_batch
from .live_call_gate import LIVE_CALL_APPROVAL_CONTRACT, validate_live_call_approvals
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .request_payloads import DEFAULT_STORAGE_ROOT
from .stage_coverage import collect_stage_coverage

SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS = (LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER)


@dataclass(frozen=True)
class LiveCallApprovalProposal:
    """Review packet for a bounded future live-call approval."""

    contract_type: str
    model_layer: str
    stage_id: str
    start_month: str
    end_month: str
    target_component_id: str
    request_count: int
    skipped_registered_count: int
    skipped_terminal_count: int
    request_ids: tuple[str, ...]
    skipped_registered_request_ids: tuple[str, ...]
    skipped_terminal_request_ids: tuple[str, ...]
    approval_template: dict[str, Any]
    dispatch_plan_command: tuple[str, ...]
    dispatch_execute_command_template: tuple[str, ...]
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["request_ids"] = list(self.request_ids)
        row["skipped_registered_request_ids"] = list(self.skipped_registered_request_ids)
        row["skipped_terminal_request_ids"] = list(self.skipped_terminal_request_ids)
        row["dispatch_plan_command"] = list(self.dispatch_plan_command)
        row["dispatch_execute_command_template"] = list(self.dispatch_execute_command_template)
        return row


@dataclass(frozen=True)
class LiveCallApprovalProposalValidation:
    """Validation that a reviewed approval is exactly bounded by a proposal."""

    contract_type: str
    proposal_contract_type: str
    approval_id: str
    model_layer: str
    stage_id: str
    start_month: str
    end_month: str
    request_count: int
    request_ids: tuple[str, ...]
    skipped_registered_request_ids: tuple[str, ...]
    gate_validation_count: int
    status: str = "approved_against_live_call_proposal"
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["request_ids"] = list(self.request_ids)
        row["skipped_registered_request_ids"] = list(self.skipped_registered_request_ids)
        return row


def _select_requests(
    requests: Sequence[Mapping[str, Any]],
    *,
    symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    symbol_filter = {item.strip().upper() for item in symbols if item.strip()}
    request_filter = {item.strip() for item in request_ids if item.strip()}
    selected = []
    for row in requests:
        symbol_ok = not symbol_filter or str(row.get("symbol") or "").upper() in symbol_filter
        request_ok = not request_filter or str(row.get("request_id") or "") in request_filter
        if symbol_ok and request_ok:
            selected.append(dict(row))
    if symbol_filter:
        found = {str(row.get("symbol") or "").upper() for row in selected}
        missing = sorted(symbol_filter - found)
        if missing:
            raise TaskSystemError("requested symbols are not in the approval-planning batch: " + ",".join(missing))
    if request_filter:
        found_ids = {str(row.get("request_id") or "") for row in selected}
        missing_ids = sorted(request_filter - found_ids)
        if missing_ids:
            raise TaskSystemError("requested ids are not in the approval-planning batch: " + ",".join(missing_ids))
    if limit is not None and limit <= 0:
        raise TaskSystemError("limit must be positive")
    if not selected:
        raise TaskSystemError("approval proposal selected no requests")
    return selected


def _approval_id(model_layer: str, start_month: str, end_month: str, request_count: int) -> str:
    month_token = start_month.replace("-", "_") if start_month == end_month else f"{start_month.replace('-', '_')}_{end_month.replace('-', '_')}"
    return f"lcav1_{model_layer}_{month_token}_alpaca_bars_{request_count}_requests_REVIEW_REQUIRED"


def _dispatch_command(*, model_layer: str, start_month: str, end_month: str, request_ids: Sequence[str], execute: bool) -> tuple[str, ...]:
    command = [
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/dispatch_approved_provider_acquisition.py",
        "--model-layer",
        model_layer,
        "--start-month",
        start_month,
        "--end-month",
        end_month,
        "--approval",
        "REVIEWED_APPROVAL_JSON_PATH",
        "--skip-registered-failures",
    ]
    for request_id in request_ids:
        command.extend(["--request-id", request_id])
    if execute:
        command.extend(["--execute-approved-provider-calls", "--continue-on-error", "--reject-terminal-coverage"])
    return tuple(command)


def _approval_template(*, model_layer: str, start_month: str, end_month: str, request_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "contract_type": "live_call_approval_v1",
        "approval_id": _approval_id(model_layer, start_month, end_month, len(request_ids)),
        "decision_status": "REVIEW_REQUIRED_REPLACE_WITH_APPROVED",
        "approved_by": "REVIEW_REQUIRED",
        "approved_at_utc": "REVIEW_REQUIRED_ISO_UTC",
        "expires_at_utc": "REVIEW_REQUIRED_ISO_UTC",
        "request_ids": list(request_ids),
        "approval_scope": "provider_data_acquisition_only",
        "broker_execution_allowed": False,
        "allowed_providers": ["alpaca"],
        "max_requests": len(request_ids),
        "max_window_days": 31,
        "model_activation_allowed": False,
        "storage_lifecycle_mutation_allowed": False,
        "review_note": (
            "Template only. It is intentionally invalid until an operator replaces review placeholders, "
            "confirms the exact request_ids, and sets decision_status=approved."
        ),
    }


def plan_live_call_approval_proposal(
    *,
    model_layer: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    skip_registered_failures: bool = True,
    skip_terminal_coverage: bool = False,
    database_url: str | None = None,
) -> LiveCallApprovalProposal:
    """Plan a skip-aware approval proposal without approving or dispatching calls."""

    if model_layer not in SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS:
        raise TaskSystemError(f"unsupported live-call approval planning model_layer: {model_layer}")
    _summary, requests, _payloads, _validations = prepare_layer_historical_training_batch(
        model_layer=model_layer,
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        write=False,
        persist_sql=False,
        validate_handoff=False,
    )
    selected = _select_requests(requests, symbols=symbols, request_ids=request_ids, limit=limit)
    stage_id = f"{model_layer}.data_acquisition"
    skipped_ids: tuple[str, ...] = ()
    if skip_registered_failures:
        registered_ids, _refs = accepted_failure_request_ids_from_register(
            database_url=database_url,
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
        )
        registered_set = set(registered_ids)
        skipped_ids = tuple(str(row["request_id"]) for row in selected if str(row.get("request_id") or "") in registered_set)
        selected = [row for row in selected if str(row.get("request_id") or "") not in registered_set]
    if not selected:
        raise TaskSystemError("all selected requests are registered accepted skips; no live-call approval proposal needed")
    skipped_terminal_ids: tuple[str, ...] = ()
    if skip_terminal_coverage:
        report = collect_stage_coverage(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
        )
        if report.failed_request_ids:
            raise TaskSystemError("stage has unreviewed failed requests; review/register failures before planning more live calls: " + ",".join(report.failed_request_ids))
        terminal_set = {str(item) for item in (*report.ready_request_ids, *report.accepted_failed_request_ids)}
        pending_set = {str(item) for item in report.pending_request_ids}
        skipped_terminal_ids = tuple(str(row["request_id"]) for row in selected if str(row.get("request_id") or "") in terminal_set)
        selected = [row for row in selected if str(row.get("request_id") or "") in pending_set]
        if not selected:
            raise TaskSystemError("selected requests are already terminal or not pending in stage coverage; no live-call approval proposal needed")
    if limit is not None:
        selected = selected[:limit]
    if not selected:
        raise TaskSystemError("all selected requests are terminal, registered skips, or outside pending coverage; no live-call approval proposal needed")
    selected_ids = tuple(str(row["request_id"]) for row in selected)
    return LiveCallApprovalProposal(
        contract_type="manager_live_call_approval_proposal_v1",
        model_layer=model_layer,
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        target_component_id="01_feed_alpaca_bars",
        request_count=len(selected_ids),
        skipped_registered_count=len(skipped_ids),
        skipped_terminal_count=len(skipped_terminal_ids),
        request_ids=selected_ids,
        skipped_registered_request_ids=skipped_ids,
        skipped_terminal_request_ids=skipped_terminal_ids,
        approval_template=_approval_template(model_layer=model_layer, start_month=start_month, end_month=end_month, request_ids=selected_ids),
        dispatch_plan_command=_dispatch_command(model_layer=model_layer, start_month=start_month, end_month=end_month, request_ids=selected_ids, execute=False),
        dispatch_execute_command_template=_dispatch_command(model_layer=model_layer, start_month=start_month, end_month=end_month, request_ids=selected_ids, execute=True),
    )


def write_live_call_approval_proposal(proposal: LiveCallApprovalProposal, *, output: TextIO) -> None:
    json.dump(proposal.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def _request_ids(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    return (str(value),)


def _live_requests_for_proposal(proposal: Mapping[str, Any]) -> list[dict[str, Any]]:
    model_layer = str(proposal.get("model_layer") or "")
    start_month = str(proposal.get("start_month") or "")
    end_month = str(proposal.get("end_month") or "")
    proposal_ids = _request_ids(proposal.get("request_ids"))
    if model_layer not in SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS:
        raise TaskSystemError(f"unsupported proposal model_layer: {model_layer}")
    if not start_month or not end_month:
        raise TaskSystemError("proposal must include start_month and end_month")
    if not proposal_ids:
        raise TaskSystemError("proposal must include request_ids")
    _summary, requests, _payloads, _validations = prepare_layer_historical_training_batch(
        model_layer=model_layer,
        start_month=start_month,
        end_month=end_month,
        storage_root=DEFAULT_STORAGE_ROOT,
        write=False,
        persist_sql=False,
        validate_handoff=False,
    )
    by_id = {str(row.get("request_id") or ""): dict(row) for row in requests}
    missing = [request_id for request_id in proposal_ids if request_id not in by_id]
    if missing:
        raise TaskSystemError("proposal request_ids are not in the reviewed batch: " + ",".join(missing))
    live_requests = []
    for request_id in proposal_ids:
        row = dict(by_id[request_id])
        policy_refs = list(row.get("policy_refs") or [])
        for required_policy in ("live_call_policy_required", "live_call_approval_gate_v1"):
            if required_policy not in policy_refs:
                policy_refs.append(required_policy)
        live_requests.append(row | {"dry_run": False, "policy_refs": policy_refs})
    return live_requests


def validate_live_call_approval_against_proposal(
    proposal: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    now_utc: datetime | None = None,
) -> LiveCallApprovalProposalValidation:
    """Validate a reviewed approval against an exact manager proposal.

    This is still plan-only validation: it does not write files, mutate SQL,
    dispatch provider commands, or call providers.
    """

    if proposal.get("contract_type") != "manager_live_call_approval_proposal_v1":
        raise TaskSystemError("proposal.contract_type must be manager_live_call_approval_proposal_v1")
    if approval.get("contract_type") != LIVE_CALL_APPROVAL_CONTRACT:
        raise TaskSystemError(f"approval.contract_type must be {LIVE_CALL_APPROVAL_CONTRACT}")
    proposal_ids = _request_ids(proposal.get("request_ids"))
    approval_ids = _request_ids(approval.get("request_ids") or approval.get("request_id"))
    skipped_ids = _request_ids(proposal.get("skipped_registered_request_ids"))
    if set(proposal_ids) != set(approval_ids) or len(proposal_ids) != len(approval_ids):
        raise TaskSystemError("approval.request_ids must exactly match proposal.request_ids")
    skipped_overlap = sorted(set(approval_ids).intersection(skipped_ids))
    if skipped_overlap:
        raise TaskSystemError("approval.request_ids include registered skip ids: " + ",".join(skipped_overlap))
    try:
        max_requests = int(approval.get("max_requests"))
    except (TypeError, ValueError) as exc:
        raise TaskSystemError("approval.max_requests must equal proposal request_count") from exc
    if max_requests != len(proposal_ids):
        raise TaskSystemError("approval.max_requests must equal proposal request_count")
    template = proposal.get("approval_template")
    if isinstance(template, Mapping):
        template_providers = {str(item).lower() for item in template.get("allowed_providers") or []}
        approval_providers = {str(item).lower() for item in approval.get("allowed_providers") or []}
        if template_providers and not approval_providers.issubset(template_providers):
            raise TaskSystemError("approval.allowed_providers must not exceed proposal allowed_providers")
        template_scope = template.get("approval_scope")
        if template_scope and approval.get("approval_scope") != template_scope:
            raise TaskSystemError("approval.approval_scope must match proposal approval_scope")
    if approval.get("model_activation_allowed") not in (False, None):
        raise TaskSystemError("model_activation_allowed must be false or omitted")
    if approval.get("storage_lifecycle_mutation_allowed") not in (False, None):
        raise TaskSystemError("storage_lifecycle_mutation_allowed must be false or omitted")
    validations = validate_live_call_approvals(_live_requests_for_proposal(proposal), approval, now_utc=now_utc)
    return LiveCallApprovalProposalValidation(
        contract_type="manager_live_call_approval_proposal_validation_v1",
        proposal_contract_type=str(proposal["contract_type"]),
        approval_id=str(approval.get("approval_id") or ""),
        model_layer=str(proposal.get("model_layer") or ""),
        stage_id=str(proposal.get("stage_id") or ""),
        start_month=str(proposal.get("start_month") or ""),
        end_month=str(proposal.get("end_month") or ""),
        request_count=len(proposal_ids),
        request_ids=proposal_ids,
        skipped_registered_request_ids=skipped_ids,
        gate_validation_count=len(validations),
    )


def write_live_call_approval_proposal_validation(validation: LiveCallApprovalProposalValidation, *, output: TextIO) -> None:
    json.dump(validation.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def validate_proposal_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a reviewed live_call_approval_v1 exactly against a manager proposal without dispatch.")
    parser.add_argument("--proposal", required=True, type=Path, help="manager_live_call_approval_proposal_v1 JSON.")
    parser.add_argument("--approval", required=True, type=Path, help="Reviewed live_call_approval_v1 JSON artifact.")
    parser.add_argument("--output-path", type=Path, help="Optional path for the validation artifact.")
    parser.add_argument("--write", action="store_true", help="Write the validation artifact to --output-path.")
    args = parser.parse_args(argv)
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    approval = json.loads(args.approval.read_text(encoding="utf-8"))
    if not isinstance(proposal, Mapping):
        raise TaskSystemError("proposal artifact must be a JSON object")
    if not isinstance(approval, Mapping):
        raise TaskSystemError("approval artifact must be a JSON object")
    validation = validate_live_call_approval_against_proposal(proposal, approval)
    if args.write:
        if args.output_path is None:
            raise TaskSystemError("--write requires --output-path")
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(validation.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_live_call_approval_proposal_validation(validation, output=sys.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a skip-aware live_call_approval_v1 review template without provider dispatch.")
    parser.add_argument("--model-layer", required=True, choices=SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--symbol", action="append", default=[], help="Limit to one symbol; repeatable.")
    parser.add_argument("--request-id", action="append", default=[], help="Limit to one request id; repeatable.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--include-registered-failures", action="store_true", help="Do not exclude accepted_skip rows from failure_register.")
    parser.add_argument("--pending-only", action="store_true", help="Use stage coverage to exclude already ready/reviewed-terminal requests and plan only pending work.")
    parser.add_argument("--database-url")
    parser.add_argument("--output-path", type=Path)
    parser.add_argument("--write", action="store_true", help="Write the proposal JSON to --output-path.")
    args = parser.parse_args(argv)

    proposal = plan_live_call_approval_proposal(
        model_layer=args.model_layer,
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        symbols=args.symbol,
        request_ids=args.request_id,
        limit=args.limit,
        skip_registered_failures=not args.include_registered_failures,
        skip_terminal_coverage=args.pending_only,
        database_url=args.database_url,
    )
    if args.write:
        if args.output_path is None:
            raise TaskSystemError("--write requires --output-path")
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(proposal.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_live_call_approval_proposal(proposal, output=sys.stdout)
    return 0


__all__ = [
    "LiveCallApprovalProposal",
    "LiveCallApprovalProposalValidation",
    "SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS",
    "plan_live_call_approval_proposal",
    "validate_live_call_approval_against_proposal",
    "validate_proposal_main",
    "write_live_call_approval_proposal",
    "write_live_call_approval_proposal_validation",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Create and inspect complete manager live-call approval packet bundles.

A packet is a local runtime bundle that keeps the proposal, reviewed-approval
placeholder, validation command, dispatch command templates, and reconcile command
together so future approved provider batches do not drift across mismatched paths
or request sets. Packet generation and packet-status inspection are non-mutating
with respect to providers: they never approve, validate as reviewed, dispatch, or
call providers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .live_call_planning import SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS, plan_live_call_approval_proposal
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_APPROVAL_PACKET_ROOT = Path("storage/runtime/approvals")
PACKET_FILE_NAME = "packet.json"
PACKET_STATUS_FILE_NAME = "packet_status.json"


@dataclass(frozen=True)
class LiveCallApprovalPacket:
    """Filesystem bundle for one bounded live-call approval review."""

    contract_type: str
    packet_id: str
    model_layer: str
    stage_id: str
    start_month: str
    end_month: str
    request_count: int
    skipped_registered_count: int
    packet_dir: str
    proposal_path: str
    reviewed_approval_template_path: str
    validation_output_path: str
    dispatch_plan_output_path: str
    dispatch_execute_output_path: str
    reconcile_summary_output_path: str
    reconcile_coverage_report_path: str
    failure_proposal_path: str
    status_output_path: str
    proposal_request_ids: tuple[str, ...]
    skipped_registered_request_ids: tuple[str, ...]
    validate_approval_command: tuple[str, ...]
    dispatch_plan_command: tuple[str, ...]
    dispatch_execute_command_template: tuple[str, ...]
    reconcile_command_template: tuple[str, ...]
    inspect_status_command: tuple[str, ...]
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        for key in (
            "proposal_request_ids",
            "skipped_registered_request_ids",
            "validate_approval_command",
            "dispatch_plan_command",
            "dispatch_execute_command_template",
            "reconcile_command_template",
            "inspect_status_command",
        ):
            row[key] = list(getattr(self, key))
        return row


@dataclass(frozen=True)
class LiveCallApprovalPacketStatus:
    """Read-only lifecycle/status view for a live-call approval packet."""

    contract_type: str
    packet_id: str | None
    packet_dir: str
    status: str
    next_action: str
    missing_files: tuple[str, ...]
    inconsistent_reasons: tuple[str, ...]
    model_layer: str | None
    stage_id: str | None
    start_month: str | None
    end_month: str | None
    request_count: int | None
    approval_id: str | None
    proposal_ready: bool
    approval_reviewed: bool
    validation_ready: bool
    dispatch_plan_ready: bool
    dispatch_executed: bool
    reconcile_ready: bool
    can_validate_approval: bool
    can_plan_dispatch: bool
    can_execute_dispatch: bool
    can_reconcile: bool
    provider_calls: int
    dispatch_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    storage_lifecycle_mutation_performed: bool

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["missing_files"] = list(self.missing_files)
        row["inconsistent_reasons"] = list(self.inconsistent_reasons)
        return row


def _token(value: str) -> str:
    return "_".join(part for part in "".join(char.lower() if char.isalnum() else "_" for char in value).split("_") if part)


def _packet_id(*, model_layer: str, start_month: str, end_month: str, request_ids: Sequence[str]) -> str:
    symbols = []
    for request_id in request_ids:
        prefix = "mgrreq_backfill_alpaca_bars_"
        suffix = f"_{start_month.replace('-', '_')}"
        text = request_id
        if text.startswith(prefix):
            text = text.removeprefix(prefix)
        if text.endswith(suffix):
            text = text.removesuffix(suffix)
        symbols.append(text)
    symbol_token = "_".join(symbols[:6]) if symbols else f"{len(request_ids)}_requests"
    if len(symbols) > 6:
        symbol_token += f"_plus_{len(symbols) - 6}"
    month_token = start_month if start_month == end_month else f"{start_month}_to_{end_month}"
    return _token(f"{model_layer}_{month_token}_{symbol_token}")


def _replace_token(command: Sequence[str], *, approval_path: str, validation_path: str | None = None) -> list[str]:
    result: list[str] = []
    for item in command:
        result.append(approval_path if item == "REVIEWED_APPROVAL_JSON_PATH" else item)
    if validation_path:
        insert_at = len(result)
        if "--skip-registered-failures" in result:
            insert_at = result.index("--skip-registered-failures")
        result[insert_at:insert_at] = ["--approval-validation", validation_path]
    return result


def _with_output(command: Sequence[str], *, output_path: str) -> tuple[str, ...]:
    return tuple(list(command) + ["--write", "--output-path", output_path])


def _validation_command(*, proposal_path: str, approval_path: str, validation_path: str) -> tuple[str, ...]:
    return (
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/validate_live_call_approval_proposal.py",
        "--proposal",
        proposal_path,
        "--approval",
        approval_path,
        "--write",
        "--output-path",
        validation_path,
    )


def _reconcile_command(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    coverage_path: str,
    failure_proposal_path: str,
    summary_path: str,
) -> tuple[str, ...]:
    return (
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/reconcile_provider_stage.py",
        "--stage-id",
        stage_id,
        "--start-month",
        start_month,
        "--end-month",
        end_month,
        "--write-control-plane",
        "--write-failure-proposal",
        "--failure-proposal-path",
        failure_proposal_path,
        "--write-failure-register",
        "--write-coverage-report",
        "--coverage-report-path",
        coverage_path,
        "--advance-workflow",
        "--write-workflow-state",
        "--write-summary",
        "--summary-output-path",
        summary_path,
    )


def _status_command(*, packet_path: str, status_path: str) -> tuple[str, ...]:
    return (
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/inspect_live_call_approval_packet.py",
        "--packet",
        packet_path,
        "--write",
        "--output-path",
        status_path,
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_readme(path: Path, packet: LiveCallApprovalPacket) -> None:
    lines = [
        f"# {packet.packet_id}",
        "",
        "This is a manager live-call approval packet bundle.",
        "",
        "Safety boundary:",
        "- Packet creation does not approve provider calls.",
        "- Packet creation does not dispatch providers.",
        "- Execution still requires a reviewed approval artifact plus proposal-bound validation.",
        "- Broker execution, model activation, and storage lifecycle mutation remain disabled.",
        "",
        "Lifecycle:",
        "1. Fill and review the approval template in `reviewed_approval_TEMPLATE.json`.",
        "2. Run the validation command recorded in `packet.json`.",
        "3. Run the plan-only dispatch command and inspect `dispatch_plan.json`.",
        "4. Only after explicit approval, run the execute command template.",
        "5. Run the reconcile command template to ingest receipts and refresh coverage.",
        "6. Run the inspect-status command any time to refresh `packet_status.json`.",
        "",
        "Files:",
        f"- Proposal: `{Path(packet.proposal_path).name}`",
        f"- Reviewed approval placeholder: `{Path(packet.reviewed_approval_template_path).name}`",
        f"- Validation output target: `{Path(packet.validation_output_path).name}`",
        f"- Dispatch plan output target: `{Path(packet.dispatch_plan_output_path).name}`",
        f"- Dispatch execute output target: `{Path(packet.dispatch_execute_output_path).name}`",
        f"- Reconcile summary output target: `{Path(packet.reconcile_summary_output_path).name}`",
        f"- Packet status output target: `{Path(packet.status_output_path).name}`",
        "",
        "Commands are recorded in `packet.json`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def create_live_call_approval_packet(
    *,
    model_layer: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    packet_root: Path = DEFAULT_APPROVAL_PACKET_ROOT,
    symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    skip_registered_failures: bool = True,
    database_url: str | None = None,
    write: bool = False,
) -> LiveCallApprovalPacket:
    """Create a complete local approval packet without provider dispatch."""

    if model_layer not in SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS:
        raise TaskSystemError(f"unsupported approval packet model_layer: {model_layer}")
    proposal = plan_live_call_approval_proposal(
        model_layer=model_layer,
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        symbols=symbols,
        request_ids=request_ids,
        limit=limit,
        skip_registered_failures=skip_registered_failures,
        database_url=database_url,
    )
    packet_id = _packet_id(model_layer=model_layer, start_month=start_month, end_month=end_month, request_ids=proposal.request_ids)
    packet_dir = packet_root / model_layer / packet_id
    proposal_path = packet_dir / "proposal.json"
    approval_path = packet_dir / "reviewed_approval_TEMPLATE.json"
    validation_path = packet_dir / "proposal_validation.json"
    dispatch_plan_path = packet_dir / "dispatch_plan.json"
    dispatch_execute_path = packet_dir / "dispatch_execute.json"
    reconcile_summary_path = packet_dir / "reconcile_summary.json"
    failure_proposal_path = packet_dir / "failure_register_proposals.jsonl"
    status_path = packet_dir / PACKET_STATUS_FILE_NAME
    packet_path = packet_dir / PACKET_FILE_NAME
    coverage_path = Path("storage/runtime/stage_coverage") / f"{proposal.stage_id.replace('.', '_')}_{start_month}.json"
    dispatch_plan_command = _with_output(
        _replace_token(proposal.dispatch_plan_command, approval_path=str(approval_path), validation_path=str(validation_path)),
        output_path=str(dispatch_plan_path),
    )
    dispatch_execute_command = _with_output(
        _replace_token(proposal.dispatch_execute_command_template, approval_path=str(approval_path), validation_path=str(validation_path)),
        output_path=str(dispatch_execute_path),
    )
    packet = LiveCallApprovalPacket(
        contract_type="manager_live_call_approval_packet_v1",
        packet_id=packet_id,
        model_layer=model_layer,
        stage_id=proposal.stage_id,
        start_month=start_month,
        end_month=end_month,
        request_count=proposal.request_count,
        skipped_registered_count=proposal.skipped_registered_count,
        packet_dir=str(packet_dir),
        proposal_path=str(proposal_path),
        reviewed_approval_template_path=str(approval_path),
        validation_output_path=str(validation_path),
        dispatch_plan_output_path=str(dispatch_plan_path),
        dispatch_execute_output_path=str(dispatch_execute_path),
        reconcile_summary_output_path=str(reconcile_summary_path),
        reconcile_coverage_report_path=str(coverage_path),
        failure_proposal_path=str(failure_proposal_path),
        status_output_path=str(status_path),
        proposal_request_ids=proposal.request_ids,
        skipped_registered_request_ids=proposal.skipped_registered_request_ids,
        validate_approval_command=_validation_command(proposal_path=str(proposal_path), approval_path=str(approval_path), validation_path=str(validation_path)),
        dispatch_plan_command=dispatch_plan_command,
        dispatch_execute_command_template=dispatch_execute_command,
        reconcile_command_template=_reconcile_command(
            stage_id=proposal.stage_id,
            start_month=start_month,
            end_month=end_month,
            coverage_path=str(coverage_path),
            failure_proposal_path=str(failure_proposal_path),
            summary_path=str(reconcile_summary_path),
        ),
        inspect_status_command=_status_command(packet_path=str(packet_path), status_path=str(status_path)),
    )
    if write:
        packet_dir.mkdir(parents=True, exist_ok=True)
        _write_json(proposal_path, proposal.summary_row())
        _write_json(approval_path, proposal.approval_template)
        _write_json(packet_path, packet.summary_row())
        _write_readme(packet_dir / "README.md", packet)
    return packet


def _read_json(path: Path) -> Mapping[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TaskSystemError(f"JSON artifact must be an object: {path}")
    return payload


def _bool_false(value: Any) -> bool:
    return value in (False, None)


def _has_review_placeholder(value: Any) -> bool:
    if isinstance(value, str) and "REVIEW_REQUIRED" in value:
        return True
    if isinstance(value, Mapping):
        return any(_has_review_placeholder(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_review_placeholder(item) for item in value)
    return False


def _ids(payload: Mapping[str, Any] | None, key: str) -> tuple[str, ...]:
    if not payload:
        return ()
    return tuple(str(item) for item in payload.get(key) or [])


def _resolve_packet_file(packet_or_dir: Path) -> Path:
    return packet_or_dir / PACKET_FILE_NAME if packet_or_dir.is_dir() else packet_or_dir


def inspect_live_call_approval_packet(*, packet_path: Path) -> LiveCallApprovalPacketStatus:
    """Inspect packet lifecycle status from local artifacts only."""

    packet_file = _resolve_packet_file(packet_path)
    packet_dir = packet_file.parent
    missing: list[str] = []
    inconsistent: list[str] = []
    packet = _read_json(packet_file)
    if packet is None:
        return LiveCallApprovalPacketStatus(
            contract_type="manager_live_call_approval_packet_status_v1",
            packet_id=None,
            packet_dir=str(packet_dir),
            status="missing_packet",
            next_action="create_live_call_approval_packet",
            missing_files=(str(packet_file),),
            inconsistent_reasons=(),
            model_layer=None,
            stage_id=None,
            start_month=None,
            end_month=None,
            request_count=None,
            approval_id=None,
            proposal_ready=False,
            approval_reviewed=False,
            validation_ready=False,
            dispatch_plan_ready=False,
            dispatch_executed=False,
            reconcile_ready=False,
            can_validate_approval=False,
            can_plan_dispatch=False,
            can_execute_dispatch=False,
            can_reconcile=False,
            provider_calls=0,
            dispatch_performed=False,
            model_activation_performed=False,
            broker_execution_performed=False,
            storage_lifecycle_mutation_performed=False,
        )
    if packet.get("contract_type") != "manager_live_call_approval_packet_v1":
        inconsistent.append("packet contract_type must be manager_live_call_approval_packet_v1")

    def artifact(name: str) -> tuple[Path, Mapping[str, Any] | None]:
        path = Path(str(packet.get(name) or ""))
        if not path:
            inconsistent.append(f"packet missing {name}")
            return path, None
        payload = _read_json(path)
        if payload is None:
            missing.append(str(path))
        return path, payload

    _proposal_path, proposal = artifact("proposal_path")
    _approval_path, approval = artifact("reviewed_approval_template_path")
    _validation_path, validation = artifact("validation_output_path")
    _dispatch_plan_path, dispatch_plan = artifact("dispatch_plan_output_path")
    _dispatch_execute_path, dispatch_execute = artifact("dispatch_execute_output_path")
    _reconcile_summary_path, reconcile = artifact("reconcile_summary_output_path")

    request_ids = tuple(str(item) for item in packet.get("proposal_request_ids") or [])
    proposal_ready = bool(proposal and proposal.get("contract_type") == "manager_live_call_approval_proposal_v1" and _ids(proposal, "request_ids") == request_ids)
    if proposal and not proposal_ready:
        inconsistent.append("proposal request_ids/contract_type do not match packet")
    approval_reviewed = bool(
        approval
        and approval.get("contract_type") == "live_call_approval_v1"
        and approval.get("decision_status") == "approved"
        and not _has_review_placeholder(approval)
        and set(_ids(approval, "request_ids")) == set(request_ids)
        and len(_ids(approval, "request_ids")) == len(request_ids)
    )
    approval_id = str(approval.get("approval_id")) if approval and approval.get("approval_id") else None
    validation_ready = bool(
        validation
        and validation.get("contract_type") == "manager_live_call_approval_proposal_validation_v1"
        and approval_id
        and validation.get("approval_id") == approval_id
        and set(_ids(validation, "request_ids")) == set(request_ids)
        and len(_ids(validation, "request_ids")) == len(request_ids)
        and validation.get("provider_calls") in (0, None)
        and validation.get("dispatch_performed") in (False, None)
    )
    if validation and not validation_ready:
        inconsistent.append("proposal validation artifact does not match packet/reviewed approval")
    dispatch_plan_ready = bool(
        dispatch_plan
        and dispatch_plan.get("contract_type") == "manager_provider_dispatch_summary_v1"
        and dispatch_plan.get("dispatch_performed") is False
        and int(dispatch_plan.get("provider_calls") or 0) == 0
        and set(str(item.get("request_id") or "") for item in dispatch_plan.get("items") or []) == set(request_ids)
    )
    if dispatch_plan and not dispatch_plan_ready:
        inconsistent.append("dispatch plan artifact does not match packet or is not plan-only")
    dispatch_executed = bool(
        dispatch_execute
        and dispatch_execute.get("contract_type") == "manager_provider_dispatch_summary_v1"
        and dispatch_execute.get("dispatch_performed") is True
        and int(dispatch_execute.get("provider_calls") or 0) > 0
        and set(str(item.get("request_id") or "") for item in dispatch_execute.get("items") or []) == set(request_ids)
    )
    if dispatch_execute and not dispatch_executed:
        inconsistent.append("dispatch execute artifact does not show executed matching packet request ids")
    reconcile_ready = bool(
        reconcile
        and reconcile.get("contract_type") == "manager_provider_stage_reconcile_v1"
        and reconcile.get("stage_id") == packet.get("stage_id")
        and reconcile.get("start_month") == packet.get("start_month")
        and _bool_false(reconcile.get("dispatch_performed"))
        and int(reconcile.get("provider_calls") or 0) == 0
    )
    if reconcile and not reconcile_ready:
        inconsistent.append("reconcile summary artifact does not match packet or safety boundary")

    can_validate = proposal_ready and approval_reviewed and not validation_ready
    can_plan = validation_ready and not dispatch_plan_ready
    can_execute = validation_ready and dispatch_plan_ready and not dispatch_executed
    can_reconcile = dispatch_executed and not reconcile_ready
    if inconsistent:
        status = "packet_inconsistent"
        next_action = "fix_packet_artifact_mismatch"
    elif reconcile_ready:
        status = "reconciled"
        next_action = "inspect_stage_coverage_and_continue_workflow_if_ready"
    elif dispatch_executed:
        status = "executed_pending_reconcile"
        next_action = "run_reconcile_command_template"
    elif dispatch_plan_ready:
        status = "dispatch_plan_ready_pending_execute"
        next_action = "review_plan_then_run_execute_command_only_with_explicit_provider_approval"
    elif validation_ready:
        status = "approval_validated_pending_dispatch_plan"
        next_action = "run_dispatch_plan_command"
    elif approval_reviewed:
        status = "approval_ready_pending_validation"
        next_action = "run_validate_approval_command"
    elif proposal_ready:
        status = "template_pending_review"
        next_action = "fill_reviewed_approval_template_and_get_explicit_review"
    else:
        status = "packet_incomplete"
        next_action = "regenerate_packet"

    provider_calls = int(dispatch_execute.get("provider_calls") or 0) if dispatch_execute else 0
    dispatch_performed = bool(dispatch_execute.get("dispatch_performed")) if dispatch_execute else False
    return LiveCallApprovalPacketStatus(
        contract_type="manager_live_call_approval_packet_status_v1",
        packet_id=str(packet.get("packet_id")) if packet.get("packet_id") else None,
        packet_dir=str(packet_dir),
        status=status,
        next_action=next_action,
        missing_files=tuple(missing),
        inconsistent_reasons=tuple(inconsistent),
        model_layer=str(packet.get("model_layer")) if packet.get("model_layer") else None,
        stage_id=str(packet.get("stage_id")) if packet.get("stage_id") else None,
        start_month=str(packet.get("start_month")) if packet.get("start_month") else None,
        end_month=str(packet.get("end_month")) if packet.get("end_month") else None,
        request_count=int(packet.get("request_count")) if packet.get("request_count") is not None else None,
        approval_id=approval_id,
        proposal_ready=proposal_ready,
        approval_reviewed=approval_reviewed,
        validation_ready=validation_ready,
        dispatch_plan_ready=dispatch_plan_ready,
        dispatch_executed=dispatch_executed,
        reconcile_ready=reconcile_ready,
        can_validate_approval=can_validate,
        can_plan_dispatch=can_plan,
        can_execute_dispatch=can_execute,
        can_reconcile=can_reconcile,
        provider_calls=provider_calls,
        dispatch_performed=dispatch_performed,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
    )


def write_live_call_approval_packet(packet: LiveCallApprovalPacket, *, output: TextIO) -> None:
    json.dump(packet.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def write_live_call_approval_packet_status(status: LiveCallApprovalPacketStatus, *, output: TextIO) -> None:
    json.dump(status.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a complete live-call approval packet bundle without provider dispatch.")
    parser.add_argument("--model-layer", required=True, choices=(LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER))
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--packet-root", type=Path, default=DEFAULT_APPROVAL_PACKET_ROOT)
    parser.add_argument("--symbol", action="append", default=[], help="Limit to one symbol; repeatable.")
    parser.add_argument("--request-id", action="append", default=[], help="Limit to one request id; repeatable.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--include-registered-failures", action="store_true")
    parser.add_argument("--database-url")
    parser.add_argument("--write", action="store_true", help="Write packet files under --packet-root.")
    args = parser.parse_args(argv)
    packet = create_live_call_approval_packet(
        model_layer=args.model_layer,
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        packet_root=args.packet_root,
        symbols=args.symbol,
        request_ids=args.request_id,
        limit=args.limit,
        skip_registered_failures=not args.include_registered_failures,
        database_url=args.database_url,
        write=args.write,
    )
    write_live_call_approval_packet(packet, output=sys.stdout)
    return 0


def status_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a live-call approval packet lifecycle status without provider dispatch.")
    parser.add_argument("--packet", required=True, type=Path, help="Path to packet.json or its containing packet directory.")
    parser.add_argument("--write", action="store_true", help="Write status JSON to --output-path.")
    parser.add_argument("--output-path", type=Path, help="Optional packet status output path.")
    args = parser.parse_args(argv)
    status = inspect_live_call_approval_packet(packet_path=args.packet)
    if args.write:
        output_path = args.output_path
        if output_path is None:
            output_path = Path(status.packet_dir) / PACKET_STATUS_FILE_NAME
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(status.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_live_call_approval_packet_status(status, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_APPROVAL_PACKET_ROOT",
    "LiveCallApprovalPacket",
    "LiveCallApprovalPacketStatus",
    "create_live_call_approval_packet",
    "inspect_live_call_approval_packet",
    "write_live_call_approval_packet",
    "write_live_call_approval_packet_status",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

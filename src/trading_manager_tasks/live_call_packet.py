"""Create complete manager live-call approval packet bundles.

A packet is a local runtime bundle that keeps the proposal, reviewed-approval
placeholder, validation command, dispatch command templates, and reconcile command
together so future approved provider batches do not drift across mismatched paths
or request sets. Packet generation is non-mutating with respect to providers:
it never approves, validates as reviewed, dispatches, or calls providers.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence, TextIO

from .control_plane import TaskSystemError
from .live_call_planning import SUPPORTED_PROVIDER_APPROVAL_MODEL_LAYERS, plan_live_call_approval_proposal
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_APPROVAL_PACKET_ROOT = Path("storage/runtime/approvals")


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
    reconcile_coverage_report_path: str
    proposal_request_ids: tuple[str, ...]
    skipped_registered_request_ids: tuple[str, ...]
    validate_approval_command: tuple[str, ...]
    dispatch_plan_command: tuple[str, ...]
    dispatch_execute_command_template: tuple[str, ...]
    reconcile_command_template: tuple[str, ...]
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["proposal_request_ids"] = list(self.proposal_request_ids)
        row["skipped_registered_request_ids"] = list(self.skipped_registered_request_ids)
        row["validate_approval_command"] = list(self.validate_approval_command)
        row["dispatch_plan_command"] = list(self.dispatch_plan_command)
        row["dispatch_execute_command_template"] = list(self.dispatch_execute_command_template)
        row["reconcile_command_template"] = list(self.reconcile_command_template)
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


def _replace_token(command: Sequence[str], *, approval_path: str, validation_path: str | None = None) -> tuple[str, ...]:
    result: list[str] = []
    for item in command:
        result.append(approval_path if item == "REVIEWED_APPROVAL_JSON_PATH" else item)
    if validation_path:
        insert_at = len(result)
        if "--skip-registered-failures" in result:
            insert_at = result.index("--skip-registered-failures")
        result[insert_at:insert_at] = ["--approval-validation", validation_path]
    return tuple(result)


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


def _reconcile_command(*, stage_id: str, start_month: str, end_month: str, coverage_path: str) -> tuple[str, ...]:
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
        "--write-failure-register",
        "--write-coverage-report",
        "--coverage-report-path",
        coverage_path,
        "--advance-workflow",
        "--write-workflow-state",
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
        "Files:",
        f"- Proposal: `{Path(packet.proposal_path).name}`",
        f"- Reviewed approval placeholder: `{Path(packet.reviewed_approval_template_path).name}`",
        f"- Validation output target: `{Path(packet.validation_output_path).name}`",
        f"- Dispatch plan output target: `{Path(packet.dispatch_plan_output_path).name}`",
        "",
        "Commands are also recorded in `packet.json`.",
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
    coverage_path = Path("storage/runtime/stage_coverage") / f"{proposal.stage_id.replace('.', '_')}_{start_month}.json"
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
        reconcile_coverage_report_path=str(coverage_path),
        proposal_request_ids=proposal.request_ids,
        skipped_registered_request_ids=proposal.skipped_registered_request_ids,
        validate_approval_command=_validation_command(proposal_path=str(proposal_path), approval_path=str(approval_path), validation_path=str(validation_path)),
        dispatch_plan_command=_replace_token(proposal.dispatch_plan_command, approval_path=str(approval_path), validation_path=str(validation_path)),
        dispatch_execute_command_template=_replace_token(proposal.dispatch_execute_command_template, approval_path=str(approval_path), validation_path=str(validation_path)),
        reconcile_command_template=_reconcile_command(stage_id=proposal.stage_id, start_month=start_month, end_month=end_month, coverage_path=str(coverage_path)),
    )
    if write:
        packet_dir.mkdir(parents=True, exist_ok=True)
        _write_json(proposal_path, proposal.summary_row())
        _write_json(approval_path, proposal.approval_template)
        _write_json(packet_dir / "packet.json", packet.summary_row())
        _write_readme(packet_dir / "README.md", packet)
    return packet


def write_live_call_approval_packet(packet: LiveCallApprovalPacket, *, output: TextIO) -> None:
    json.dump(packet.summary_row(), output, indent=2, sort_keys=True)
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


__all__ = [
    "DEFAULT_APPROVAL_PACKET_ROOT",
    "LiveCallApprovalPacket",
    "create_live_call_approval_packet",
    "write_live_call_approval_packet",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

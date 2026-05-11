"""One-step controller for manager provider-stage runtime flow.

The controller is intentionally conservative. It can perform safe internal
no-provider actions such as creating the next pending-only packet and refreshing
the dashboard. It stops at human/external gates: approval review, provider
execution, failure review, model activation, broker execution, and storage
lifecycle mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO

from .control_plane import TaskSystemError
from .live_call_packet import DEFAULT_APPROVAL_PACKET_ROOT, create_live_call_approval_packet
from .stage_run_dashboard import (
    SUPPORTED_DASHBOARD_STAGE_IDS,
    StageRunDashboard,
    build_stage_run_dashboard,
    default_dashboard_path,
    write_stage_run_dashboard,
)


@dataclass(frozen=True)
class StageRunControllerReceipt:
    """Receipt for one conservative controller step."""

    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    action_taken: str
    action_status: str
    dashboard_next_action_before: str
    dashboard_next_action_after: str
    blocking_reason_before: str
    blocking_reason_after: str
    dashboard_path: str
    created_packet_path: str | None
    created_packet_id: str | None
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _model_layer_for_stage(stage_id: str) -> str:
    if stage_id == "layer_01_market_regime.data_acquisition":
        return "layer_01_market_regime"
    if stage_id == "layer_02_sector_context.data_acquisition":
        return "layer_02_sector_context"
    raise TaskSystemError(f"unsupported stage controller: {stage_id}")


def _write_dashboard(dashboard: StageRunDashboard, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dashboard.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_stage_controller_step(
    *,
    stage_id: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    packet_root: Path = DEFAULT_APPROVAL_PACKET_ROOT,
    packet_storage_root: Path = Path("storage"),
    next_limit: int = 5,
    database_url: str | None = None,
    auto_create_packet: bool = True,
    dashboard_path: Path | None = None,
) -> tuple[StageRunControllerReceipt, StageRunDashboard]:
    """Run one safe controller step and return receipt plus refreshed dashboard."""

    output_dashboard_path = dashboard_path or default_dashboard_path(stage_id=stage_id, start_month=start_month)
    before = build_stage_run_dashboard(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        packet_root=packet_root,
        packet_storage_root=packet_storage_root,
        next_limit=next_limit,
        database_url=database_url,
    )
    created_packet_path: str | None = None
    created_packet_id: str | None = None
    action_taken = "none"
    action_status = "blocked_by_gate"

    if before.next_action == "create_or_review_next_pending_only_packet" and auto_create_packet:
        packet = create_live_call_approval_packet(
            model_layer=_model_layer_for_stage(stage_id),
            start_month=start_month,
            end_month=end_month,
            storage_root=packet_storage_root,
            packet_root=packet_root,
            limit=next_limit,
            skip_registered_failures=True,
            pending_only=True,
            database_url=database_url,
            write=True,
        )
        created_packet_path = str(Path(packet.packet_dir) / "packet.json")
        created_packet_id = packet.packet_id
        action_taken = "create_pending_only_packet"
        action_status = "completed"
    elif before.next_action == "create_or_review_next_pending_only_packet":
        action_taken = "create_pending_only_packet"
        action_status = "dry_run_no_write"
    elif before.next_action == "run_reconcile_for_executed_packet":
        action_taken = "reconcile_required"
        action_status = "manual_or_dedicated_reconcile_required"
    elif before.next_action == "review_execute_or_defer_ready_packet":
        action_taken = "provider_execution_review_required"
        action_status = "external_call_gate"
    elif before.next_action == "review_existing_pending_packet":
        action_taken = "approval_review_required"
        action_status = "human_review_gate"
    elif before.next_action == "review_stage_failures":
        action_taken = "failure_review_required"
        action_status = "human_review_gate"
    elif before.next_action == "advance_downstream_workflow":
        action_taken = "downstream_unlock_available"
        action_status = "requires_explicit_workflow_advance"
    elif before.next_action == "fix_packet_artifact_mismatch":
        action_taken = "packet_repair_required"
        action_status = "blocked_by_inconsistent_artifact"
    else:
        action_taken = before.next_action
        action_status = "no_safe_automatic_action"

    after = build_stage_run_dashboard(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        packet_root=packet_root,
        packet_storage_root=packet_storage_root,
        next_limit=next_limit,
        database_url=database_url,
    )
    _write_dashboard(after, output_dashboard_path)
    receipt = StageRunControllerReceipt(
        contract_type="manager_stage_run_controller_receipt_v1",
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        action_taken=action_taken,
        action_status=action_status,
        dashboard_next_action_before=before.next_action,
        dashboard_next_action_after=after.next_action,
        blocking_reason_before=before.blocking_reason,
        blocking_reason_after=after.blocking_reason,
        dashboard_path=str(output_dashboard_path),
        created_packet_path=created_packet_path,
        created_packet_id=created_packet_id,
    )
    return receipt, after


def write_stage_run_controller_receipt(receipt: StageRunControllerReceipt, *, output: TextIO) -> None:
    json.dump(receipt.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one conservative manager stage-run controller step without provider calls.")
    parser.add_argument("--stage-id", required=True, choices=SUPPORTED_DASHBOARD_STAGE_IDS)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--packet-root", type=Path, default=DEFAULT_APPROVAL_PACKET_ROOT)
    parser.add_argument("--packet-storage-root", type=Path, default=Path("storage"))
    parser.add_argument("--next-limit", type=int, default=5)
    parser.add_argument("--database-url")
    parser.add_argument("--no-auto-create-packet", action="store_true")
    parser.add_argument("--dashboard-path", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args(argv)
    receipt, _dashboard = run_stage_controller_step(
        stage_id=args.stage_id,
        start_month=args.start_month,
        end_month=args.end_month,
        packet_root=args.packet_root,
        packet_storage_root=args.packet_storage_root,
        next_limit=args.next_limit,
        database_url=args.database_url,
        auto_create_packet=not args.no_auto_create_packet,
        dashboard_path=args.dashboard_path,
    )
    if args.write:
        output_path = args.output_path or Path(receipt.dashboard_path).with_name(Path(receipt.dashboard_path).stem + "_controller_receipt.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_stage_run_controller_receipt(receipt, output=sys.stdout)
    return 0


__all__ = [
    "StageRunControllerReceipt",
    "run_stage_controller_step",
    "write_stage_run_controller_receipt",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

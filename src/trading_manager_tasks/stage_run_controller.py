"""One-step controller for autonomous manager provider-stage runtime flow.

The controller may execute the next bounded historical provider-dispatch slice
when coverage/resource controls say it is ready. It still never activates
models, constructs broker orders, mutates accounts, or performs storage
lifecycle mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO

from .control_plane import TaskSystemError
from .option_chain_source_acquisition import STAGE_ID as OPTION_CHAIN_SOURCE_STAGE_ID, dispatch_option_chain_source_acquisition
from .provider_dispatch import dispatch_layer_provider_acquisition
from .scheduler_locks import DEFAULT_LOCKS_DIR, acquire_scheduler_lock, provider_partition_lock_ref
from .stage_run_dashboard import (
    SUPPORTED_DASHBOARD_STAGE_IDS,
    StageRunDashboard,
    build_stage_run_dashboard,
    default_dashboard_path,
)
from .request_payloads import DEFAULT_STORAGE_ROOT


@dataclass(frozen=True)
class StageRunControllerReceipt:
    """Receipt for one autonomous controller step."""

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
    dispatch_request_ids: tuple[str, ...]
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["dispatch_request_ids"] = list(self.dispatch_request_ids)
        return row


def _model_layer_for_stage(stage_id: str) -> str:
    if stage_id == "layer_01_market_regime.data_acquisition":
        return "layer_01_market_regime"
    if stage_id == "layer_02_sector_context.data_acquisition":
        return "layer_02_sector_context"
    if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID:
        return OPTION_CHAIN_SOURCE_STAGE_ID
    raise TaskSystemError(f"unsupported stage controller: {stage_id}")


def _write_dashboard(dashboard: StageRunDashboard, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dashboard.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_stage_controller_step(
    *,
    stage_id: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    packet_root: Path | None = None,
    packet_storage_root: Path = DEFAULT_STORAGE_ROOT,
    next_limit: int = 5,
    max_workers: int = 4,
    dynamic_workers: bool = True,
    database_url: str | None = None,
    auto_create_packet: bool | None = None,
    auto_execute_provider_calls: bool = True,
    dashboard_path: Path | None = None,
    locks_dir: Path = DEFAULT_LOCKS_DIR,
) -> tuple[StageRunControllerReceipt, StageRunDashboard]:
    """Run one controller step and return receipt plus refreshed dashboard."""

    _ = auto_create_packet  # Accepted but unused; controller steps consume existing packets.
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
    request_ids = tuple(before.next_provider_dispatch.request_ids)
    action_taken = "none"
    action_status = "no_safe_automatic_action"
    provider_calls = 0
    dispatch_performed = False

    if before.next_action in {"autonomous_provider_dispatch_ready", "autonomous_provider_failure_retry_ready"} and request_ids:
        action_taken = (
            "retry_failed_provider_policy_requests"
            if before.next_action == "autonomous_provider_failure_retry_ready"
            else "execute_autonomous_provider_dispatch"
        )
        if auto_execute_provider_calls:
            with ExitStack() as stack:
                for request_id in sorted(set(request_ids)):
                    stack.enter_context(
                        acquire_scheduler_lock(
                            provider_partition_lock_ref(
                                start_month,
                                stage_id,
                                "option_chain_snapshot" if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID else "alpaca_bars",
                                request_id,
                                locks_dir=locks_dir,
                            )
                        )
                    )
                if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID:
                    summary = dispatch_option_chain_source_acquisition(
                        start_month=start_month,
                        end_month=end_month,
                        storage_root=packet_storage_root,
                        request_ids=request_ids,
                        execute_provider_calls=True,
                        continue_on_error=True,
                        database_url=database_url,
                        dynamic_workers=dynamic_workers,
                        max_workers=max_workers,
                    )
                else:
                    summary = dispatch_layer_provider_acquisition(
                        model_layer=_model_layer_for_stage(stage_id),
                        start_month=start_month,
                        end_month=end_month,
                        storage_root=packet_storage_root,
                        request_ids=request_ids,
                        execute_provider_calls=True,
                        continue_on_error=True,
                        skip_registered_failures=True,
                        reject_terminal_coverage=before.next_action != "autonomous_provider_failure_retry_ready",
                        database_url=database_url,
                        dynamic_workers=dynamic_workers,
                        max_workers=max_workers,
                    )
            provider_calls = summary.provider_calls
            dispatch_performed = summary.dispatch_performed
            action_status = "completed" if summary.dispatch_performed else "planned_no_dispatch"
        else:
            action_status = "dry_run_no_provider_calls"
    elif before.next_action == "automatic_repair_required":
        action_taken = "automatic_repair_required"
        action_status = "automatic_repair_pending"
    elif before.next_action == "advance_downstream_workflow":
        action_taken = "downstream_unlock_available"
        action_status = "requires_workflow_advance"
    else:
        action_taken = before.next_action

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
        contract_type="manager_stage_run_controller_receipt",
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
        dispatch_request_ids=request_ids,
        provider_calls=provider_calls,
        dispatch_performed=dispatch_performed,
    )
    return receipt, after


def write_stage_run_controller_receipt(receipt: StageRunControllerReceipt, *, output: TextIO) -> None:
    json.dump(receipt.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one autonomous manager stage-run controller step.")
    parser.add_argument("--stage-id", required=True, choices=SUPPORTED_DASHBOARD_STAGE_IDS)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--packet-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--packet-storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--next-limit", type=int, default=5)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--dynamic-workers", action=argparse.BooleanOptionalAction, default=True, help="Select provider workers dynamically from load and memory headroom.")
    parser.add_argument("--database-url")
    parser.add_argument("--no-execute-provider-calls", action="store_true", help="Plan only; do not execute the ready autonomous provider slice.")
    parser.add_argument("--dashboard-path", type=Path)
    parser.add_argument("--locks-dir", type=Path, default=DEFAULT_LOCKS_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args(argv)
    receipt, dashboard = run_stage_controller_step(
        stage_id=args.stage_id,
        start_month=args.start_month,
        end_month=args.end_month,
        packet_root=args.packet_root,
        packet_storage_root=args.packet_storage_root,
        next_limit=args.next_limit,
        max_workers=args.max_workers,
        dynamic_workers=args.dynamic_workers,
        database_url=args.database_url,
        auto_execute_provider_calls=not args.no_execute_provider_calls,
        dashboard_path=args.dashboard_path,
        locks_dir=args.locks_dir,
    )
    if args.write:
        output_path = args.output_path or DEFAULT_STORAGE_ROOT / "runtime" / "stage_run_controller" / f"{args.stage_id.replace('.', '_')}_{args.start_month}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_stage_run_controller_receipt(receipt, output=sys.stdout)
    _ = dashboard
    return 0


__all__ = [
    "StageRunControllerReceipt",
    "run_stage_controller_step",
    "write_stage_run_controller_receipt",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

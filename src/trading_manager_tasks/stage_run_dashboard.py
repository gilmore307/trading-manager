"""Single-entry dashboard for a manager provider-stage run.

The dashboard is the human-facing receipt for a stage/month. It summarizes
coverage, packet lifecycle state, evidence paths, and the next safe action while
leaving the lower-level artifacts in place for audit and replay.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .live_call_packet import DEFAULT_APPROVAL_PACKET_ROOT, PACKET_FILE_NAME, inspect_live_call_approval_packet
from .live_call_planning import plan_live_call_approval_proposal
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .stage_coverage import StageCoverageReport, collect_stage_coverage

DEFAULT_STAGE_RUN_DASHBOARD_ROOT = Path("storage/runtime/stage_run_dashboard")
SUPPORTED_DASHBOARD_STAGE_IDS = (
    "layer_01_market_regime.data_acquisition",
    "layer_02_sector_context.data_acquisition",
)


@dataclass(frozen=True)
class StageRunPacketSummary:
    """Compact packet lifecycle row for dashboard display."""

    packet_id: str | None
    packet_path: str
    packet_dir: str
    status: str
    next_action: str
    request_count: int | None
    provider_calls: int
    dispatch_performed: bool
    approval_id: str | None
    missing_files: tuple[str, ...]
    inconsistent_reasons: tuple[str, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["missing_files"] = list(self.missing_files)
        row["inconsistent_reasons"] = list(self.inconsistent_reasons)
        return row


@dataclass(frozen=True)
class StageRunNextPacket:
    """Preview of the next pending-only packet the operator should review."""

    available: bool
    reason: str
    request_count: int
    request_ids: tuple[str, ...]
    skipped_registered_request_ids: tuple[str, ...]
    skipped_terminal_request_ids: tuple[str, ...]
    create_packet_command: tuple[str, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["request_ids"] = list(self.request_ids)
        row["skipped_registered_request_ids"] = list(self.skipped_registered_request_ids)
        row["skipped_terminal_request_ids"] = list(self.skipped_terminal_request_ids)
        row["create_packet_command"] = list(self.create_packet_command)
        return row


@dataclass(frozen=True)
class StageRunDashboard:
    """Human-facing stage-run dashboard/receipt."""

    contract_type: str
    stage_id: str
    model_layer: str
    start_month: str
    end_month: str
    coverage: dict[str, Any]
    packet_count: int
    packets: tuple[StageRunPacketSummary, ...]
    latest_packet_status: str | None
    next_recommended_packet: StageRunNextPacket
    blocking_reason: str
    next_action: str
    evidence_refs: tuple[str, ...]
    provider_calls_observed: int
    dispatch_performed_observed: bool
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["packets"] = [packet.summary_row() for packet in self.packets]
        row["next_recommended_packet"] = self.next_recommended_packet.summary_row()
        row["evidence_refs"] = list(self.evidence_refs)
        return row


def _model_layer_for_stage(stage_id: str) -> str:
    if stage_id == "layer_01_market_regime.data_acquisition":
        return LAYER_ONE_MODEL_LAYER
    if stage_id == "layer_02_sector_context.data_acquisition":
        return LAYER_TWO_MODEL_LAYER
    raise TaskSystemError(f"unsupported stage dashboard: {stage_id}")


def _safe_stage(stage_id: str) -> str:
    return stage_id.replace(".", "_")


def default_dashboard_path(*, stage_id: str, start_month: str) -> Path:
    return DEFAULT_STAGE_RUN_DASHBOARD_ROOT / f"{_safe_stage(stage_id)}_{start_month}.json"


def _packet_sort_key(path: Path) -> tuple[float, str]:
    try:
        return (path.stat().st_mtime, str(path))
    except FileNotFoundError:
        return (0.0, str(path))


def collect_packet_summaries(
    *,
    model_layer: str,
    stage_id: str,
    start_month: str,
    end_month: str,
    packet_root: Path = DEFAULT_APPROVAL_PACKET_ROOT,
) -> tuple[StageRunPacketSummary, ...]:
    """Collect packet statuses matching the stage/month."""

    root = packet_root / model_layer
    if not root.exists():
        return ()
    summaries: list[StageRunPacketSummary] = []
    for packet_path in sorted(root.glob(f"*/{PACKET_FILE_NAME}"), key=_packet_sort_key, reverse=True):
        status = inspect_live_call_approval_packet(packet_path=packet_path)
        if status.stage_id != stage_id or status.start_month != start_month or status.end_month != end_month:
            continue
        summaries.append(
            StageRunPacketSummary(
                packet_id=status.packet_id,
                packet_path=str(packet_path),
                packet_dir=status.packet_dir,
                status=status.status,
                next_action=status.next_action,
                request_count=status.request_count,
                provider_calls=status.provider_calls,
                dispatch_performed=status.dispatch_performed,
                approval_id=status.approval_id,
                missing_files=status.missing_files,
                inconsistent_reasons=status.inconsistent_reasons,
            )
        )
    return tuple(summaries)


def _next_packet_command(*, stage_id: str, start_month: str, end_month: str, limit: int) -> tuple[str, ...]:
    return (
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/create_live_call_approval_packet.py",
        "--model-layer",
        _model_layer_for_stage(stage_id),
        "--start-month",
        start_month,
        "--end-month",
        end_month,
        "--pending-only",
        "--limit",
        str(limit),
        "--write",
    )


def preview_next_pending_packet(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    limit: int,
    packet_storage_root: Path,
    database_url: str | None = None,
) -> StageRunNextPacket:
    """Preview the next pending-only packet without writing it."""

    try:
        proposal = plan_live_call_approval_proposal(
            model_layer=_model_layer_for_stage(stage_id),
            start_month=start_month,
            end_month=end_month,
            storage_root=packet_storage_root,
            limit=limit,
            skip_registered_failures=True,
            skip_terminal_coverage=True,
            database_url=database_url,
        )
    except TaskSystemError as exc:
        return StageRunNextPacket(
            available=False,
            reason=str(exc),
            request_count=0,
            request_ids=(),
            skipped_registered_request_ids=(),
            skipped_terminal_request_ids=(),
            create_packet_command=_next_packet_command(stage_id=stage_id, start_month=start_month, end_month=end_month, limit=limit),
        )
    return StageRunNextPacket(
        available=True,
        reason="pending-only packet preview available",
        request_count=proposal.request_count,
        request_ids=proposal.request_ids,
        skipped_registered_request_ids=proposal.skipped_registered_request_ids,
        skipped_terminal_request_ids=proposal.skipped_terminal_request_ids,
        create_packet_command=_next_packet_command(stage_id=stage_id, start_month=start_month, end_month=end_month, limit=limit),
    )


def _coverage_payload(report: StageCoverageReport) -> dict[str, Any]:
    return {
        "contract_type": report.contract_type,
        "status": report.status,
        "expected_count": report.expected_count,
        "observed_count": report.observed_count,
        "ready_count": report.ready_count,
        "failed_count": report.failed_count,
        "accepted_failed_count": report.accepted_failed_count,
        "pending_count": report.pending_count,
        "can_unlock_downstream": report.can_unlock_downstream,
        "ready_request_ids": list(report.ready_request_ids),
        "failed_request_ids": list(report.failed_request_ids),
        "accepted_failed_request_ids": list(report.accepted_failed_request_ids),
        "pending_request_ids": list(report.pending_request_ids),
        "accepted_failure_refs": list(report.accepted_failure_refs),
        "reason": report.reason,
    }


def _next_action(*, coverage: StageCoverageReport, next_packet: StageRunNextPacket, packets: Sequence[StageRunPacketSummary]) -> tuple[str, str]:
    inconsistent = [packet.packet_id or packet.packet_path for packet in packets if packet.status == "packet_inconsistent"]
    if inconsistent:
        return ("fix_packet_artifact_mismatch", "packet inconsistency detected: " + ",".join(inconsistent))
    executable = [packet.packet_id or packet.packet_path for packet in packets if packet.status == "dispatch_plan_ready_pending_execute"]
    if executable:
        return ("review_execute_or_defer_ready_packet", "packet ready for explicit execution review: " + ",".join(executable))
    reconcile = [packet.packet_id or packet.packet_path for packet in packets if packet.status == "executed_pending_reconcile"]
    if reconcile:
        return ("run_reconcile_for_executed_packet", "executed packet needs reconcile: " + ",".join(reconcile))
    reviewable = [packet.packet_id or packet.packet_path for packet in packets if packet.status in {"template_pending_review", "approval_ready_pending_validation", "approval_validated_pending_dispatch_plan"}]
    if reviewable:
        return ("review_existing_pending_packet", "existing packet awaits review/validation/plan: " + ",".join(reviewable))
    if coverage.status == "failed":
        return ("review_stage_failures", coverage.reason)
    if coverage.can_unlock_downstream:
        return ("advance_downstream_workflow", coverage.reason)
    if next_packet.available:
        return ("create_or_review_next_pending_only_packet", f"{coverage.reason}; next pending packet has {next_packet.request_count} requests")
    return ("no_action_until_blocker_resolved", f"{coverage.reason}; {next_packet.reason}")


def build_stage_run_dashboard(
    *,
    stage_id: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    packet_root: Path = DEFAULT_APPROVAL_PACKET_ROOT,
    packet_storage_root: Path = Path("storage"),
    next_limit: int = 5,
    database_url: str | None = None,
) -> StageRunDashboard:
    """Build a single stage dashboard/receipt without mutating providers or storage."""

    model_layer = _model_layer_for_stage(stage_id)
    coverage = collect_stage_coverage(stage_id=stage_id, start_month=start_month, end_month=end_month, database_url=database_url)
    packets = collect_packet_summaries(
        model_layer=model_layer,
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        packet_root=packet_root,
    )
    next_packet = preview_next_pending_packet(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        limit=next_limit,
        packet_storage_root=packet_storage_root,
        database_url=database_url,
    )
    next_action, blocking_reason = _next_action(coverage=coverage, next_packet=next_packet, packets=packets)
    evidence_refs = [
        f"stage_coverage:{stage_id}:{start_month}:{coverage.status}",
        *[f"packet:{packet.packet_path}" for packet in packets],
    ]
    return StageRunDashboard(
        contract_type="manager_stage_run_dashboard_v1",
        stage_id=stage_id,
        model_layer=model_layer,
        start_month=start_month,
        end_month=end_month,
        coverage=_coverage_payload(coverage),
        packet_count=len(packets),
        packets=packets,
        latest_packet_status=packets[0].status if packets else None,
        next_recommended_packet=next_packet,
        blocking_reason=blocking_reason,
        next_action=next_action,
        evidence_refs=tuple(evidence_refs),
        provider_calls_observed=sum(packet.provider_calls for packet in packets),
        dispatch_performed_observed=any(packet.dispatch_performed for packet in packets),
    )


def write_stage_run_dashboard(dashboard: StageRunDashboard, *, output: TextIO) -> None:
    json.dump(dashboard.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize a provider-stage run as one dashboard/receipt without provider calls.")
    parser.add_argument("--stage-id", required=True, choices=SUPPORTED_DASHBOARD_STAGE_IDS)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--packet-root", type=Path, default=DEFAULT_APPROVAL_PACKET_ROOT)
    parser.add_argument("--packet-storage-root", type=Path, default=Path("storage"))
    parser.add_argument("--next-limit", type=int, default=5)
    parser.add_argument("--database-url")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args(argv)
    dashboard = build_stage_run_dashboard(
        stage_id=args.stage_id,
        start_month=args.start_month,
        end_month=args.end_month,
        packet_root=args.packet_root,
        packet_storage_root=args.packet_storage_root,
        next_limit=args.next_limit,
        database_url=args.database_url,
    )
    if args.write:
        output_path = args.output_path or default_dashboard_path(stage_id=args.stage_id, start_month=args.start_month)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(dashboard.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_stage_run_dashboard(dashboard, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_STAGE_RUN_DASHBOARD_ROOT",
    "StageRunDashboard",
    "StageRunNextPacket",
    "StageRunPacketSummary",
    "build_stage_run_dashboard",
    "collect_packet_summaries",
    "default_dashboard_path",
    "preview_next_pending_packet",
    "write_stage_run_dashboard",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

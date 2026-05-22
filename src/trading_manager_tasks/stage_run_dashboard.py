"""Single-entry dashboard for an autonomous manager provider-stage run.

The dashboard is the operator-facing receipt for a stage/month. It summarizes
coverage, the next bounded provider-dispatch preview, evidence paths, and the
next safe action. Historical provider dispatch is autonomous under manager
resource/coverage controls; this surface still never approves model activation,
broker execution, order construction, account mutation, or storage lifecycle
mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence, TextIO

from .control_plane import TaskSystemError
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .provider_dispatch import dispatch_layer_provider_acquisition
from .stage_coverage import StageCoverageReport, collect_stage_coverage
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_STAGE_RUN_DASHBOARD_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "stage_run_dashboard"
DEFAULT_COMPONENT_STORAGE_ROOT = data_storage_root()
SUPPORTED_DASHBOARD_STAGE_IDS = (
    "layer_01_market_regime.data_acquisition",
    "layer_02_sector_context.data_acquisition",
)


@dataclass(frozen=True)
class StageRunProviderDispatchPreview:
    """Preview of the next autonomous provider dispatch slice."""

    available: bool
    reason: str
    request_count: int
    request_ids: tuple[str, ...]
    skipped_registered_request_ids: tuple[str, ...]
    command_preview: tuple[tuple[str, ...], ...]
    execute_command_template: tuple[str, ...]
    worker_preview: tuple[dict[str, Any], ...] = ()

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["request_ids"] = list(self.request_ids)
        row["skipped_registered_request_ids"] = list(self.skipped_registered_request_ids)
        row["command_preview"] = [list(command) for command in self.command_preview]
        row["worker_preview"] = [dict(worker) for worker in self.worker_preview]
        row["execute_command_template"] = list(self.execute_command_template)
        return row


@dataclass(frozen=True)
class StageRunDashboard:
    """Operator-facing stage-run dashboard/receipt."""

    contract_type: str
    stage_id: str
    model_layer: str
    start_month: str
    end_month: str
    coverage: dict[str, Any]
    next_provider_dispatch: StageRunProviderDispatchPreview
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
        row["next_provider_dispatch"] = self.next_provider_dispatch.summary_row()
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


def _execute_command(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    request_ids: Sequence[str],
    reject_terminal_coverage: bool = True,
) -> tuple[str, ...]:
    command = [
        "PYTHONPATH=src",
        "python3",
        "scripts/tasks/dispatch_and_reconcile_provider_stage.py",
        "--model-layer",
        _model_layer_for_stage(stage_id),
        "--start-month",
        start_month,
        "--end-month",
        end_month,
        "--execute-provider-calls",
        "--continue-on-error",
        "--skip-registered-failures",
    ]
    if reject_terminal_coverage:
        command.append("--reject-terminal-coverage")
    for request_id in request_ids:
        command.extend(["--request-id", request_id])
    return tuple(command)


def _symbol_from_alpaca_bars_request_id(request_id: str, *, month: str) -> str | None:
    suffix = "_" + month.replace("-", "_")
    prefix = "mgrreq_backfill_alpaca_bars_"
    if not request_id.startswith(prefix) or not request_id.endswith(suffix):
        return None
    symbol = request_id.removeprefix(prefix)[: -len(suffix)]
    return symbol.upper() if symbol else None


def _latest_receipt_run_error(receipt_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    runs = payload.get("runs")
    if not isinstance(runs, list) or not runs:
        return {}
    latest = runs[-1]
    if not isinstance(latest, dict):
        return {}
    error = latest.get("error")
    return error if isinstance(error, dict) else {}


def _retryable_provider_policy_failures(
    *,
    failed_request_ids: Sequence[str],
    start_month: str,
    component_storage_root: Path = DEFAULT_COMPONENT_STORAGE_ROOT,
) -> tuple[str, ...]:
    retryable: list[str] = []
    for request_id in failed_request_ids:
        symbol = _symbol_from_alpaca_bars_request_id(str(request_id), month=start_month)
        if symbol is None:
            continue
        receipt_path = component_storage_root / "monthly_backfill" / "alpaca_bars" / symbol / start_month / "completion_receipt.json"
        error = _latest_receipt_run_error(receipt_path)
        error_type = str(error.get("type") or "")
        message = str(error.get("message") or "")
        if error_type == "ProviderPolicyError" and "provider not allowed" in message:
            retryable.append(str(request_id))
    return tuple(retryable)


def preview_next_provider_dispatch(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    limit: int,
    storage_root: Path,
    coverage: StageCoverageReport,
    database_url: str | None = None,
    component_storage_root: Path = DEFAULT_COMPONENT_STORAGE_ROOT,
) -> StageRunProviderDispatchPreview:
    """Preview the next bounded autonomous provider dispatch without calling providers."""

    retry_failed_policy = False
    if coverage.status == "failed":
        request_ids = _retryable_provider_policy_failures(
            failed_request_ids=coverage.failed_request_ids,
            start_month=start_month,
            component_storage_root=component_storage_root,
        )[:limit]
        retry_failed_policy = bool(request_ids)
    else:
        request_ids = tuple(str(item) for item in coverage.pending_request_ids[:limit])
    if not request_ids:
        return StageRunProviderDispatchPreview(
            available=False,
            reason=(
                "failed coverage requires review; no retryable provider-policy failures detected"
                if coverage.status == "failed"
                else "no pending request ids available for provider dispatch"
            ),
            request_count=0,
            request_ids=(),
            skipped_registered_request_ids=(),
            command_preview=(),
            worker_preview=(),
            execute_command_template=_execute_command(
                stage_id=stage_id,
                start_month=start_month,
                end_month=end_month,
                request_ids=(),
                reject_terminal_coverage=not retry_failed_policy,
            ),
        )
    try:
        summary = dispatch_layer_provider_acquisition(
            model_layer=_model_layer_for_stage(stage_id),
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            request_ids=request_ids,
            execute_provider_calls=False,
            skip_registered_failures=True,
            database_url=database_url,
        )
    except TaskSystemError as exc:
        return StageRunProviderDispatchPreview(
            available=False,
            reason=str(exc),
            request_count=0,
            request_ids=(),
            skipped_registered_request_ids=(),
            command_preview=(),
            worker_preview=(),
            execute_command_template=_execute_command(
                stage_id=stage_id,
                start_month=start_month,
                end_month=end_month,
                request_ids=request_ids,
                reject_terminal_coverage=not retry_failed_policy,
            ),
        )
    runnable = tuple(item.request_id for item in summary.items if item.status != "skipped_registered_accepted_failure")
    skipped = tuple(item.request_id for item in summary.items if item.status == "skipped_registered_accepted_failure")
    return StageRunProviderDispatchPreview(
        available=bool(runnable),
        reason=(
            "retryable provider policy failures available for autonomous retry"
            if retry_failed_policy and runnable
            else "autonomous provider dispatch preview available"
            if runnable
            else "all selected requests are registered accepted failures"
        ),
        request_count=len(runnable),
        request_ids=runnable,
        skipped_registered_request_ids=skipped,
        command_preview=tuple(tuple(item.command) for item in summary.items if item.command),
        worker_preview=tuple(
            {
                "request_id": item.request_id,
                "worker_id": item.worker_id,
                "worker_slot": item.worker_slot,
                "status": item.status,
            }
            for item in summary.items
            if item.status != "skipped_registered_accepted_failure"
        ),
        execute_command_template=_execute_command(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            request_ids=runnable,
            reject_terminal_coverage=not retry_failed_policy,
        ),
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


def _next_action(*, coverage: StageCoverageReport, preview: StageRunProviderDispatchPreview) -> tuple[str, str]:
    if coverage.status == "failed":
        if preview.available and "retryable provider policy" in preview.reason:
            return ("autonomous_provider_failure_retry_ready", f"{coverage.reason}; {preview.reason}")
        return ("review_stage_failures", coverage.reason)
    if coverage.can_unlock_downstream:
        return ("advance_downstream_workflow", coverage.reason)
    if preview.available:
        return ("autonomous_provider_dispatch_ready", f"{coverage.reason}; next dispatch has {preview.request_count} requests")
    return ("no_action_until_blocker_resolved", f"{coverage.reason}; {preview.reason}")


def build_stage_run_dashboard(
    *,
    stage_id: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    packet_root: Path | None = None,
    packet_storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_storage_root: Path = DEFAULT_COMPONENT_STORAGE_ROOT,
    next_limit: int = 5,
    database_url: str | None = None,
) -> StageRunDashboard:
    """Build a single stage dashboard/receipt without mutating providers or storage."""

    _ = packet_root  # Accepted but unused; dashboard reads from packet_storage_root.
    model_layer = _model_layer_for_stage(stage_id)
    coverage = collect_stage_coverage(stage_id=stage_id, start_month=start_month, end_month=end_month, database_url=database_url)
    preview = preview_next_provider_dispatch(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        limit=next_limit,
        storage_root=packet_storage_root,
        coverage=coverage,
        database_url=database_url,
        component_storage_root=component_storage_root,
    )
    next_action, blocking_reason = _next_action(coverage=coverage, preview=preview)
    evidence_refs = [f"stage_coverage:{stage_id}:{start_month}:{coverage.status}"]
    return StageRunDashboard(
        contract_type="manager_stage_run_dashboard",
        stage_id=stage_id,
        model_layer=model_layer,
        start_month=start_month,
        end_month=end_month,
        coverage=_coverage_payload(coverage),
        next_provider_dispatch=preview,
        blocking_reason=blocking_reason,
        next_action=next_action,
        evidence_refs=tuple(evidence_refs),
        provider_calls_observed=coverage.observed_count,
        dispatch_performed_observed=coverage.observed_count > 0,
    )


def write_stage_run_dashboard(dashboard: StageRunDashboard, *, output: TextIO) -> None:
    json.dump(dashboard.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize an autonomous provider-stage run as one dashboard/receipt without provider calls.")
    parser.add_argument("--stage-id", required=True, choices=SUPPORTED_DASHBOARD_STAGE_IDS)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--packet-root", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--packet-storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--component-storage-root", type=Path, default=DEFAULT_COMPONENT_STORAGE_ROOT)
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
        component_storage_root=args.component_storage_root,
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
    "StageRunProviderDispatchPreview",
    "build_stage_run_dashboard",
    "default_dashboard_path",
    "preview_next_provider_dispatch",
    "write_stage_run_dashboard",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Reconcile provider-stage receipts into manager coverage/workflow state.

This module owns the safe post-dispatch side of an autonomous historical provider stage. It discovers component completion receipts that already exist on disk,
normalizes them into manager control-plane rows, refreshes stage coverage, and
optionally advances workflow state. It never dispatches components or calls
providers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TextIO

from .control_plane import CompletionReceiptRows, TaskSystemError, _error_summary, _receipt_runs, _status, fetch_manager_requests, normalize_completion_receipt, persist_completion_rows
from .agent_error_handler import handle_server_error
from .failure_register import (
    mark_failure_register_requests_corrected,
    persist_failure_register_rows,
    validate_failure_register_row,
)
from .model_training_state import advance_workflow_state, resolve_workflow_state_path
from .request_payloads import DEFAULT_STORAGE_ROOT as DEFAULT_MANAGER_STORAGE_ROOT
from .scheduler_locks import DEFAULT_LOCKS_DIR, acquire_scheduler_lock, reconcile_lock_ref
from .stage_coverage import StageCoverageReport, collect_stage_coverage, write_stage_coverage
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, load_market_regime_universe
from .option_chain_source_acquisition import REQUEST_KIND as OPTION_CHAIN_REQUEST_KIND
from .option_chain_source_acquisition import SOURCE_ID as OPTION_CHAIN_SOURCE_ID
from .option_chain_source_acquisition import STAGE_ID as OPTION_CHAIN_SOURCE_STAGE_ID
from .option_chain_source_acquisition import TARGET_COMPONENT_ID as OPTION_CHAIN_TARGET_COMPONENT_ID
from .request_payloads import storage_uri_to_local_path
from .storage_paths import data_storage_root

DEFAULT_COMPONENT_STORAGE_ROOT = data_storage_root()
DEFAULT_COVERAGE_OUTPUT_ROOT = DEFAULT_MANAGER_STORAGE_ROOT / "runtime" / "stage_coverage"
SUPPORTED_PROVIDER_STAGE_IDS = (
    "model_01_background_context.data_acquisition",
    OPTION_CHAIN_SOURCE_STAGE_ID,
)
RETRYABLE_PROVIDER_FAILURE_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("connection refused",), "provider_service_unavailable"),
    (("request failed before http response",), "provider_transport_unavailable"),
    (("urlopen error",), "provider_transport_unavailable"),
    (("timed out",), "provider_transport_timeout"),
    (("timeout",), "provider_transport_timeout"),
    (("connection reset",), "provider_transport_unavailable"),
    (("network is unreachable",), "provider_transport_unavailable"),
    (("temporary failure in name resolution",), "provider_transport_unavailable"),
    (("request returned http 429",), "provider_rate_limited"),
    (("request returned http 500",), "provider_http_retryable"),
    (("request returned http 502",), "provider_http_retryable"),
    (("request returned http 503",), "provider_http_retryable"),
    (("request returned http 504",), "provider_http_retryable"),
    (("http status 500",), "provider_http_retryable"),
    (("http status 502",), "provider_http_retryable"),
    (("http status 503",), "provider_http_retryable"),
    (("http status 504",), "provider_http_retryable"),
)


@dataclass(frozen=True)
class StageReceiptRef:
    request_id: str
    symbol: str
    receipt_path: Path
    receipt_uri: str

    def summary_row(self) -> dict[str, str]:
        return {
            "request_id": self.request_id,
            "symbol": self.symbol,
            "receipt_path": str(self.receipt_path),
            "receipt_uri": self.receipt_uri,
        }


@dataclass(frozen=True)
class StageReconcileSummary:
    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    discovered_receipt_count: int
    normalized_run_manifest_count: int
    normalized_artifact_ref_count: int
    normalized_ready_signal_count: int
    failure_proposal_count: int
    failure_proposal_path: str | None
    persisted_failure_register: bool
    persisted_control_plane: bool
    coverage_report_path: str | None
    coverage_status: str | None
    coverage_ready_count: int | None
    coverage_failed_count: int | None
    coverage_accepted_failed_count: int | None
    coverage_pending_count: int | None
    workflow_state_path: str | None
    workflow_advanced: bool
    agent_error_request_path: str | None
    agent_error_diagnosis_path: str | None
    agent_error_number: int | None
    agent_error_ref: str | None
    agent_error_status: str | None
    receipt_refs: tuple[StageReceiptRef, ...]
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["receipt_refs"] = [ref.summary_row() for ref in self.receipt_refs]
        return row


def _model_layer_for_stage(stage_id: str) -> str:
    if stage_id == "model_01_background_context.data_acquisition":
        return LAYER_ONE_MODEL_LAYER
    if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID:
        return OPTION_CHAIN_SOURCE_STAGE_ID
    raise TaskSystemError(f"unsupported provider stage reconcile: {stage_id}")


def _request_id(symbol: str, month: str) -> str:
    return f"mgrreq_backfill_alpaca_bars_{symbol.lower()}_{month.replace('-', '_')}"


def _storage_uri(path: Path, *, storage_root: Path, repo_id: str) -> str:
    resolved = path.resolve()
    root = storage_root.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return str(path)
    return f"storage://{repo_id}/{relative.as_posix()}"


def discover_stage_receipts(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    component_storage_root: Path = DEFAULT_COMPONENT_STORAGE_ROOT,
    manager_storage_root: Path = DEFAULT_MANAGER_STORAGE_ROOT,
    database_url: str | None = None,
) -> tuple[StageReceiptRef, ...]:
    """Discover existing completion receipts for a supported provider stage."""

    if stage_id != OPTION_CHAIN_SOURCE_STAGE_ID and start_month != end_month:
        raise TaskSystemError("stage receipt discovery currently supports one month at a time")
    if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID:
        refs: list[StageReceiptRef] = []
        for row in fetch_manager_requests(database_url=database_url):
            if row.get("target_component_id") != OPTION_CHAIN_TARGET_COMPONENT_ID or row.get("request_kind") != OPTION_CHAIN_REQUEST_KIND:
                continue
            request_id = str(row.get("request_id") or "")
            if not request_id.startswith("mgrreq_option_chain_window_"):
                continue
            text = " ".join(str(row.get(key) or "") for key in ("request_id", "parameter_ref"))
            if start_month not in text and end_month not in text:
                continue
            task_key_path = storage_uri_to_local_path(str(row.get("parameter_ref") or ""), storage_root=manager_storage_root)
            if not task_key_path.exists():
                continue
            task_key = json.loads(task_key_path.read_text(encoding="utf-8"))
            output_root = Path(str(task_key.get("output_root") or ""))
            receipt_path = output_root / "completion_receipt.json"
            if not receipt_path.exists():
                continue
            refs.append(
                StageReceiptRef(
                    request_id=request_id,
                    symbol=str((task_key.get("params") or {}).get("underlying") or ""),
                    receipt_path=receipt_path,
                    receipt_uri=_storage_uri(receipt_path, storage_root=component_storage_root, repo_id="trading-data"),
                )
            )
        return tuple(refs)
    model_layer = _model_layer_for_stage(stage_id)
    refs: list[StageReceiptRef] = []
    for member in load_market_regime_universe(model_layers=(model_layer,)):
        symbol = member.symbol.upper()
        receipt_path = component_storage_root / "monthly_backfill" / "alpaca_bars" / symbol / start_month / "completion_receipt.json"
        if not receipt_path.exists():
            continue
        refs.append(
            StageReceiptRef(
                request_id=_request_id(symbol, start_month),
                symbol=symbol,
                receipt_path=receipt_path,
                receipt_uri=_storage_uri(receipt_path, storage_root=component_storage_root, repo_id="trading-data"),
            )
        )
    return tuple(refs)


def _merge_completion_rows(rows: Iterable[CompletionReceiptRows]) -> CompletionReceiptRows:
    run_manifests: list[dict[str, Any]] = []
    artifact_refs: list[dict[str, Any]] = []
    ready_signals: list[dict[str, Any]] = []
    for item in rows:
        run_manifests.extend(item.run_manifests)
        artifact_refs.extend(item.artifact_refs)
        ready_signals.extend(item.ready_signals)
    return CompletionReceiptRows(run_manifests=run_manifests, artifact_refs=artifact_refs, ready_signals=ready_signals)


def _read_receipt(path: Path) -> Mapping[str, Any]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(receipt, Mapping):
        raise TaskSystemError(f"completion receipt must be a JSON object: {path}")
    return receipt


def normalize_stage_receipts(refs: Sequence[StageReceiptRef]) -> CompletionReceiptRows:
    """Normalize discovered receipt files into manager control-plane rows."""

    normalized = []
    for ref in refs:
        receipt = _read_receipt(ref.receipt_path)
        normalized.append(
            normalize_completion_receipt(
                receipt,
                request_id=ref.request_id,
                component_id=OPTION_CHAIN_TARGET_COMPONENT_ID if ref.receipt_path.as_posix().find(OPTION_CHAIN_SOURCE_ID) >= 0 else "01_feed_alpaca_bars",
                component_kind="data_source" if ref.receipt_path.as_posix().find(OPTION_CHAIN_SOURCE_ID) >= 0 else "data_feed",
                repo_id="trading-data",
                receipt_uri=ref.receipt_uri,
                ready_signal_kind="component_task_ready",
                consumer_hint="manager_provider_stage_reconcile",
            )
        )
    return _merge_completion_rows(normalized)


def classify_provider_failure(error_summary: str) -> tuple[str, str, str]:
    normalized = error_summary.lower()
    for patterns, failure_kind in RETRYABLE_PROVIDER_FAILURE_PATTERNS:
        if all(pattern in normalized for pattern in patterns):
            return (
                "retry_required",
                failure_kind,
                "Generated by manager_provider_stage_reconcile from a retryable provider/runtime failure; scheduler automatic retry should resume after provider health is restored.",
            )
    return (
        "auto_repair_required",
        "unclassified_provider_failure",
        "Generated by manager_provider_stage_reconcile from a latest failed component receipt; automatic repair should diagnose, correct, retry, or escalate only if a development-route decision is required.",
    )


def propose_failure_register_rows(
    refs: Sequence[StageReceiptRef],
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
) -> tuple[dict[str, Any], ...]:
    """Create failure-register rows from failed receipts.

    Retryable provider/runtime errors are marked `retry_required`; semantic,
    contract, or unclassified errors become `auto_repair_required`. These rows
    preserve observed failures but do not accept, skip, or correct them.
    """

    rows: list[dict[str, Any]] = []
    for ref in refs:
        receipt = _read_receipt(ref.receipt_path)
        runs = _receipt_runs(receipt)
        latest_run = runs[-1]
        status = _status(latest_run.get("status") or "failed")
        if status in {"succeeded", "success", "completed", "complete", "ready"}:
            continue
        run_id = str(latest_run.get("run_id") or f"{ref.request_id}_run_unknown")
        error_summary = _error_summary(latest_run)
        failure_status, failure_kind, note = classify_provider_failure(error_summary)
        rows.append(
            validate_failure_register_row(
                {
                    "failure_id": f"fail_{ref.request_id}_{run_id}",
                    "request_id": ref.request_id,
                    "run_id": run_id,
                    "stage_id": stage_id,
                    "target_component_id": OPTION_CHAIN_TARGET_COMPONENT_ID if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID else "01_feed_alpaca_bars",
                    "source_id": OPTION_CHAIN_SOURCE_ID if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID else "alpaca_bars",
                    "symbol": ref.symbol,
                    "start_month": start_month,
                    "end_month": end_month,
                    "failure_status": failure_status,
                    "failure_kind": failure_kind,
                    "observed_status": status,
                    "error_summary": error_summary,
                    "skip_future_matching": False,
                    "evidence_refs": [ref.receipt_uri],
                    "note": note,
                }
            )
        )
    return tuple(rows)


def latest_successful_receipt_refs(refs: Sequence[StageReceiptRef]) -> dict[str, str]:
    """Map request ids to latest successful receipt refs for failure-register correction."""

    corrected: dict[str, str] = {}
    for ref in refs:
        receipt = _read_receipt(ref.receipt_path)
        runs = _receipt_runs(receipt)
        latest_run = runs[-1]
        status = _status(latest_run.get("status") or "failed")
        if status in {"succeeded", "success", "completed", "complete", "ready"}:
            corrected[ref.request_id] = ref.receipt_uri
    return corrected


def write_failure_proposals(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True) + "\n")


def _stage_failure_agent_request_id(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    rows: Sequence[Mapping[str, Any]],
) -> str:
    digest_source = json.dumps(
        {
            "stage_id": stage_id,
            "start_month": start_month,
            "end_month": end_month,
            "failures": [
                {
                    "request_id": row.get("request_id"),
                    "error_summary": row.get("error_summary"),
                    "failure_kind": row.get("failure_kind"),
                }
                for row in rows
            ],
        },
        sort_keys=True,
    )
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]
    safe_stage = "".join(char.lower() if char.isalnum() else "_" for char in stage_id)
    return f"erragent_stage_failure_{safe_stage}_{start_month.replace('-', '_')}_{end_month.replace('-', '_')}_{digest}"


def _stage_failure_agent_summary(*, stage_id: str, rows: Sequence[Mapping[str, Any]]) -> str:
    error_counts: dict[str, int] = {}
    for row in rows:
        error = str(row.get("error_summary") or "unclassified provider failure")
        error_counts[error] = error_counts.get(error, 0) + 1
    top_errors = sorted(error_counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    error_text = "; ".join(f"{count}x {error}" for error, count in top_errors)
    return f"provider stage {stage_id} has {len(rows)} failed request(s) requiring automatic repair: {error_text}"


def _handle_stage_failure_agent_handoff(
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    rows: Sequence[Mapping[str, Any]],
    proposal_path: Path | None,
    database_url: str | None,
) -> dict[str, Any] | None:
    if not rows:
        return None
    evidence_refs: list[str] = []
    if proposal_path is not None:
        evidence_refs.append(str(proposal_path))
    for row in rows[:20]:
        evidence = row.get("evidence_refs")
        if isinstance(evidence, list):
            evidence_refs.extend(str(ref) for ref in evidence if ref)
    return handle_server_error(
        source_component="trading-manager.stage_reconcile",
        source_repo="trading-manager",
        error_scope="server.provider_stage_failure_register",
        error_kind="provider_stage_requests_failed",
        severity="warning",
        summary=_stage_failure_agent_summary(stage_id=stage_id, rows=rows),
        evidence_refs=evidence_refs,
        command=[
            "reconcile_provider_stage",
            "--stage-id",
            stage_id,
            "--start-month",
            start_month,
            "--end-month",
            end_month,
        ],
        request_id=_stage_failure_agent_request_id(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            rows=rows,
        ),
        database_url=database_url,
    )


def default_coverage_report_path(*, stage_id: str, start_month: str) -> Path:
    safe_stage = stage_id.replace(".", "_")
    return DEFAULT_COVERAGE_OUTPUT_ROOT / f"{safe_stage}_{start_month}.json"


def workflow_foundation_catch_up_only_for_stage(stage_id: str, requested: bool) -> bool:
    """Return the workflow scope needed to ingest coverage for a provider stage."""

    if stage_id == OPTION_CHAIN_SOURCE_STAGE_ID:
        return False
    return requested


def _reconcile_provider_stage_unlocked(
    *,
    stage_id: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    component_storage_root: Path = DEFAULT_COMPONENT_STORAGE_ROOT,
    manager_storage_root: Path = DEFAULT_MANAGER_STORAGE_ROOT,
    database_url: str | None = None,
    persist_control_plane: bool = False,
    failure_proposal_path: Path | None = None,
    write_failure_proposal: bool = False,
    persist_failure_register: bool = False,
    collect_coverage: bool = True,
    coverage_report_path: Path | None = None,
    write_coverage_report: bool = False,
    advance_workflow: bool = False,
    workflow_state_path: Path | None = None,
    write_workflow_state: bool = False,
    selected_target_symbol: str | None = None,
    foundation_catch_up_only: bool = True,
) -> StageReconcileSummary:
    """Run safe offline receipt/control-plane/coverage reconciliation."""

    refs = discover_stage_receipts(
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        component_storage_root=component_storage_root,
        manager_storage_root=manager_storage_root,
        database_url=database_url,
    )
    rows = normalize_stage_receipts(refs)
    if persist_control_plane:
        persist_completion_rows(rows, database_url=database_url)
    failure_rows = propose_failure_register_rows(refs, stage_id=stage_id, start_month=start_month, end_month=end_month)
    auto_repair_failure_rows = tuple(
        row for row in failure_rows if str(row.get("failure_status") or "") == "auto_repair_required"
    )
    proposal_path = failure_proposal_path
    if write_failure_proposal:
        proposal_path = proposal_path or (DEFAULT_COVERAGE_OUTPUT_ROOT / f"{stage_id.replace('.', '_')}_{start_month}_failure_register_proposals.jsonl")
        write_failure_proposals(failure_rows, proposal_path)
    if persist_failure_register:
        mark_failure_register_requests_corrected(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            corrected_request_refs=latest_successful_receipt_refs(refs),
            database_url=database_url,
        )
        persist_failure_register_rows(failure_rows, database_url=database_url)
    agent_error_result = (
        _handle_stage_failure_agent_handoff(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            rows=auto_repair_failure_rows,
            proposal_path=proposal_path,
            database_url=database_url,
        )
        if persist_failure_register and auto_repair_failure_rows
        else None
    )

    report: StageCoverageReport | None = None
    if collect_coverage:
        report = collect_stage_coverage(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
        )
    output_path: Path | None = coverage_report_path
    if write_coverage_report:
        if report is None:
            raise TaskSystemError("write_coverage_report requires collect_coverage=True")
        output_path = output_path or default_coverage_report_path(stage_id=stage_id, start_month=start_month)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            write_stage_coverage(report, output=handle)
    resolved_workflow_state_path = resolve_workflow_state_path(start_month, workflow_state_path, storage_root=manager_storage_root)
    if advance_workflow:
        if output_path is None or not output_path.exists():
            raise TaskSystemError("advance_workflow requires a written stage coverage report")
        effective_foundation_catch_up_only = workflow_foundation_catch_up_only_for_stage(stage_id, foundation_catch_up_only)
        advance_workflow_state(
            start_month=start_month,
            end_month=end_month,
            storage_root=manager_storage_root,
            state_path=resolved_workflow_state_path,
            stage_coverage_reports=(output_path,),
            selected_target_symbol=selected_target_symbol,
            foundation_catch_up_only=effective_foundation_catch_up_only,
            write=write_workflow_state,
        )

    return StageReconcileSummary(
        contract_type="manager_provider_stage_reconcile",
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        discovered_receipt_count=len(refs),
        normalized_run_manifest_count=len(rows.run_manifests),
        normalized_artifact_ref_count=len(rows.artifact_refs),
        normalized_ready_signal_count=len(rows.ready_signals),
        failure_proposal_count=len(failure_rows),
        failure_proposal_path=str(proposal_path) if write_failure_proposal and proposal_path else None,
        persisted_failure_register=persist_failure_register,
        persisted_control_plane=persist_control_plane,
        coverage_report_path=str(output_path) if write_coverage_report and output_path else None,
        coverage_status=report.status if report else None,
        coverage_ready_count=report.ready_count if report else None,
        coverage_failed_count=report.failed_count if report else None,
        coverage_accepted_failed_count=report.accepted_failed_count if report else None,
        coverage_pending_count=report.pending_count if report else None,
        workflow_state_path=str(resolved_workflow_state_path) if advance_workflow else None,
        workflow_advanced=advance_workflow,
        agent_error_request_path=str(agent_error_result.get("request_path")) if agent_error_result else None,
        agent_error_diagnosis_path=str(agent_error_result.get("diagnosis_path")) if agent_error_result else None,
        agent_error_number=int(agent_error_result["error_number"]) if agent_error_result else None,
        agent_error_ref=str(agent_error_result.get("error_ref")) if agent_error_result else None,
        agent_error_status=str(agent_error_result.get("status")) if agent_error_result else None,
        receipt_refs=refs,
    )


def reconcile_provider_stage(
    *,
    stage_id: str,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    component_storage_root: Path = DEFAULT_COMPONENT_STORAGE_ROOT,
    manager_storage_root: Path = DEFAULT_MANAGER_STORAGE_ROOT,
    database_url: str | None = None,
    persist_control_plane: bool = False,
    failure_proposal_path: Path | None = None,
    write_failure_proposal: bool = False,
    persist_failure_register: bool = False,
    collect_coverage: bool = True,
    coverage_report_path: Path | None = None,
    write_coverage_report: bool = False,
    advance_workflow: bool = False,
    workflow_state_path: Path | None = None,
    write_workflow_state: bool = False,
    selected_target_symbol: str | None = None,
    foundation_catch_up_only: bool = True,
    locks_dir: Path = DEFAULT_LOCKS_DIR,
) -> StageReconcileSummary:
    """Run safe offline receipt/control-plane/coverage reconciliation under its reconcile lock."""

    with acquire_scheduler_lock(reconcile_lock_ref(start_month, stage_id, locks_dir=locks_dir)):
        return _reconcile_provider_stage_unlocked(
            stage_id=stage_id,
            start_month=start_month,
            end_month=end_month,
            component_storage_root=component_storage_root,
            manager_storage_root=manager_storage_root,
            database_url=database_url,
            persist_control_plane=persist_control_plane,
            failure_proposal_path=failure_proposal_path,
            write_failure_proposal=write_failure_proposal,
            persist_failure_register=persist_failure_register,
            collect_coverage=collect_coverage,
            coverage_report_path=coverage_report_path,
            write_coverage_report=write_coverage_report,
            advance_workflow=advance_workflow,
            workflow_state_path=workflow_state_path,
            write_workflow_state=write_workflow_state,
            selected_target_symbol=selected_target_symbol,
            foundation_catch_up_only=foundation_catch_up_only,
        )


def write_stage_reconcile_summary(summary: StageReconcileSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile existing provider-stage receipts into manager control-plane coverage without provider calls.")
    parser.add_argument("--stage-id", required=True, choices=SUPPORTED_PROVIDER_STAGE_IDS)
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--component-storage-root", type=Path, default=DEFAULT_COMPONENT_STORAGE_ROOT)
    parser.add_argument("--manager-storage-root", type=Path, default=DEFAULT_MANAGER_STORAGE_ROOT)
    parser.add_argument("--database-url")
    parser.add_argument("--write-control-plane", action="store_true", help="Persist normalized receipt rows to manager SQL.")
    parser.add_argument("--failure-proposal-path", type=Path)
    parser.add_argument("--write-failure-proposal", action="store_true", help="Write failure-register proposal rows for failed receipts.")
    parser.add_argument("--write-failure-register", action="store_true", help="Persist proposed failure-register rows; retryable provider/runtime failures become retry_required, while unclassified failures require automatic repair.")
    parser.add_argument("--skip-coverage", action="store_true", help="Skip task-summary coverage collection.")
    parser.add_argument("--coverage-report-path", type=Path)
    parser.add_argument("--write-coverage-report", action="store_true")
    parser.add_argument("--advance-workflow", action="store_true", help="Ingest the written coverage report into workflow state.")
    parser.add_argument("--workflow-state-path", type=Path, default=None, help="Workflow checkpoint path; defaults to the manager runtime root under trading-storage/storage/02_control_plane/runtime.")
    parser.add_argument("--write-workflow-state", action="store_true")
    parser.add_argument("--target-symbol", help="Optional target symbol for Layer 3+ workflow-state routing.")
    parser.add_argument(
        "--allow-post-foundation-model-stages",
        action="store_true",
        help="Use the full fold-scoped post-foundation workflow plan when advancing workflow state.",
    )
    parser.add_argument("--write-summary", action="store_true", help="Write reconcile summary JSON to --summary-output-path.")
    parser.add_argument("--locks-dir", type=Path, default=DEFAULT_LOCKS_DIR)
    parser.add_argument("--summary-output-path", type=Path)
    args = parser.parse_args(argv)

    summary = reconcile_provider_stage(
        stage_id=args.stage_id,
        start_month=args.start_month,
        end_month=args.end_month,
        component_storage_root=args.component_storage_root,
        manager_storage_root=args.manager_storage_root,
        database_url=args.database_url,
        persist_control_plane=args.write_control_plane,
        failure_proposal_path=args.failure_proposal_path,
        write_failure_proposal=args.write_failure_proposal,
        persist_failure_register=args.write_failure_register,
        collect_coverage=not args.skip_coverage,
        coverage_report_path=args.coverage_report_path,
        write_coverage_report=args.write_coverage_report,
        advance_workflow=args.advance_workflow,
        workflow_state_path=args.workflow_state_path,
        write_workflow_state=args.write_workflow_state,
        selected_target_symbol=args.target_symbol,
        foundation_catch_up_only=not args.allow_post_foundation_model_stages,
        locks_dir=args.locks_dir,
    )
    if args.write_summary:
        if args.summary_output_path is None:
            raise TaskSystemError("--write-summary requires --summary-output-path")
        args.summary_output_path.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output_path.write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_stage_reconcile_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_COMPONENT_STORAGE_ROOT",
    "StageReceiptRef",
    "StageReconcileSummary",
    "discover_stage_receipts",
    "classify_provider_failure",
    "latest_successful_receipt_refs",
    "normalize_stage_receipts",
    "propose_failure_register_rows",
    "reconcile_provider_stage",
    "workflow_foundation_catch_up_only_for_stage",
    "write_stage_reconcile_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

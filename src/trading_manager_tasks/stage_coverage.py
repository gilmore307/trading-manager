"""Stage coverage gates over manager task-summary rows.

A task can be individually ready while its workflow stage is only partially
covered. This module makes that distinction explicit so small real-provider
batches can harden the mechanism without accidentally unlocking downstream
feature/model stages.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError, fetch_task_summary
from .failure_register import accepted_failure_request_ids_from_register
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, load_market_regime_universe
from .request_payloads import DEFAULT_STORAGE_ROOT

StageCoverageStatus = Literal["blocked", "partial_ready", "ready", "failed"]
DEFAULT_STAGE_COVERAGE_PATH = DEFAULT_STORAGE_ROOT / "runtime" / "stage_coverage" / "layer_01_market_regime_data_acquisition_2016-01.json"


@dataclass(frozen=True)
class StageCoverageReport:
    """Manager-visible coverage gate for one workflow stage."""

    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    expected_count: int
    observed_count: int
    ready_count: int
    failed_count: int
    pending_count: int
    accepted_failed_count: int
    status: StageCoverageStatus
    can_unlock_downstream: bool
    ready_request_ids: tuple[str, ...]
    failed_request_ids: tuple[str, ...]
    accepted_failed_request_ids: tuple[str, ...]
    pending_request_ids: tuple[str, ...]
    accepted_failure_refs: tuple[str, ...]
    reason: str
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["ready_request_ids"] = list(self.ready_request_ids)
        row["failed_request_ids"] = list(self.failed_request_ids)
        row["accepted_failed_request_ids"] = list(self.accepted_failed_request_ids)
        row["pending_request_ids"] = list(self.pending_request_ids)
        row["accepted_failure_refs"] = list(self.accepted_failure_refs)
        return row


def _row_text(row: Mapping[str, Any]) -> str:
    parts = [str(row.get(key) or "") for key in ("request_id", "parameter_ref")]
    for value in row.get("expected_outputs") or []:
        parts.append(str(value))
    return " ".join(parts)


def _model_layer_for_stage(stage_id: str) -> str:
    if stage_id == "layer_01_market_regime.data_acquisition":
        return LAYER_ONE_MODEL_LAYER
    if stage_id == "layer_02_sector_context.data_acquisition":
        return LAYER_TWO_MODEL_LAYER
    raise TaskSystemError(f"unsupported stage coverage gate: {stage_id}")


def _stage_request_ids(*, stage_id: str, start_month: str) -> set[str]:
    model_layer = _model_layer_for_stage(stage_id)
    return {
        f"mgrreq_backfill_alpaca_bars_{member.symbol.lower()}_{start_month.replace('-', '_')}"
        for member in load_market_regime_universe(model_layers=(model_layer,))
    }


def _matches_stage(row: Mapping[str, Any], *, stage_id: str, start_month: str, end_month: str) -> bool:
    if row.get("target_component_id") != "01_feed_alpaca_bars":
        return False
    if row.get("request_kind") != "data_backfill_month":
        return False
    request_id = str(row.get("request_id") or "")
    if request_id not in _stage_request_ids(stage_id=stage_id, start_month=start_month):
        return False
    if start_month == end_month:
        return start_month in _row_text(row)
    return start_month in _row_text(row) or end_month in _row_text(row)


def _is_ready(row: Mapping[str, Any]) -> bool:
    return (
        row.get("task_status") == "ready"
        and row.get("latest_run_status") == "succeeded"
        and row.get("latest_ready_signal_status") == "ready"
    )


def _is_failed(row: Mapping[str, Any]) -> bool:
    return any(
        row.get(key) in {"failed", "failure", "error", "cancelled"}
        for key in ("task_status", "latest_run_status", "latest_ready_signal_status")
    )


def summarize_stage_coverage_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    stage_id: str,
    start_month: str,
    end_month: str,
    expected_count: int | None = None,
    accepted_failure_request_ids: Sequence[str] = (),
    accepted_failure_refs: Sequence[str] = (),
) -> StageCoverageReport:
    """Summarize stage readiness from task-summary-like rows."""

    matched = sorted(
        [dict(row) for row in rows if _matches_stage(row, stage_id=stage_id, start_month=start_month, end_month=end_month)],
        key=lambda row: str(row.get("request_id") or ""),
    )
    if expected_count is None:
        expected_count = len(matched)
    if expected_count <= 0:
        raise TaskSystemError("expected_count must be positive or discoverable from task_summary")

    ready = [str(row["request_id"]) for row in matched if _is_ready(row)]
    failed = [str(row["request_id"]) for row in matched if _is_failed(row)]
    pending = [str(row["request_id"]) for row in matched if not _is_ready(row) and not _is_failed(row)]
    matched_set = {str(row["request_id"]) for row in matched}
    accepted_failure_set = {str(request_id) for request_id in accepted_failure_request_ids} & matched_set
    if accepted_failure_set and not accepted_failure_refs:
        raise TaskSystemError("accepted failed requests require at least one agent failure review evidence ref")
    accepted_failed = [request_id for request_id in failed if request_id in accepted_failure_set]
    accepted_skipped = sorted(accepted_failure_set - set(failed))
    accepted_terminal = [*accepted_failed, *accepted_skipped]
    unaccepted_failed = [request_id for request_id in failed if request_id not in accepted_failure_set]
    terminal_covered = len(ready) + len(accepted_terminal)
    if unaccepted_failed:
        status: StageCoverageStatus = "failed"
        reason = f"{len(unaccepted_failed)}/{expected_count} requests failed without accepted review; downstream remains blocked"
    elif terminal_covered >= expected_count:
        status = "ready"
        if accepted_terminal:
            reason = (
                f"stage coverage accepted {len(ready)} ready + {len(accepted_terminal)} reviewed failed/skip / {expected_count}; "
                "downstream may unlock"
            )
        else:
            reason = f"stage coverage complete {len(ready)}/{expected_count}; downstream may unlock"
    elif terminal_covered:
        status = "partial_ready"
        reason = f"stage coverage partial {len(ready)} ready + {len(accepted_terminal)} reviewed failed/skip / {expected_count}; downstream remains blocked"
    else:
        status = "blocked"
        reason = f"stage coverage not ready 0/{expected_count}; downstream remains blocked"

    return StageCoverageReport(
        contract_type="manager_stage_coverage",
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        expected_count=expected_count,
        observed_count=len(matched),
        ready_count=len(ready),
        failed_count=len(failed),
        pending_count=max(expected_count - terminal_covered - len(unaccepted_failed), len([request_id for request_id in pending if request_id not in accepted_failure_set])),
        accepted_failed_count=len(accepted_terminal),
        status=status,
        can_unlock_downstream=status == "ready",
        ready_request_ids=tuple(ready),
        failed_request_ids=tuple(failed),
        accepted_failed_request_ids=tuple(accepted_terminal),
        pending_request_ids=tuple(request_id for request_id in pending if request_id not in accepted_failure_set),
        accepted_failure_refs=tuple(str(ref) for ref in accepted_failure_refs),
        reason=reason,
    )


def collect_stage_coverage(
    *,
    stage_id: str = "layer_01_market_regime.data_acquisition",
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    expected_count: int | None = None,
    database_url: str | None = None,
    accepted_failure_request_ids: Sequence[str] = (),
    accepted_failure_refs: Sequence[str] = (),
) -> StageCoverageReport:
    rows = fetch_task_summary(database_url=database_url)
    registered_request_ids, registered_refs = accepted_failure_request_ids_from_register(
        database_url=database_url,
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
    )
    return summarize_stage_coverage_from_rows(
        rows,
        stage_id=stage_id,
        start_month=start_month,
        end_month=end_month,
        expected_count=expected_count,
        accepted_failure_request_ids=tuple(dict.fromkeys([*accepted_failure_request_ids, *registered_request_ids])),
        accepted_failure_refs=tuple(dict.fromkeys([*accepted_failure_refs, *registered_refs])),
    )


def write_stage_coverage(report: StageCoverageReport, *, output: TextIO) -> None:
    json.dump(report.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check manager task-summary coverage for a workflow stage.")
    parser.add_argument("--stage-id", default="layer_01_market_regime.data_acquisition")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--database-url")
    parser.add_argument("--accepted-failure-request-id", action="append", default=[], help="Failed request id accepted by reviewed evidence; preserves failed_count but may satisfy terminal coverage.")
    parser.add_argument("--accepted-failure-ref", action="append", default=[], help="Review/agent/operator evidence reference for accepted failed requests.")
    parser.add_argument("--output-path", type=Path, default=DEFAULT_STAGE_COVERAGE_PATH)
    parser.add_argument("--write", action="store_true", help="Write the stage coverage report artifact. Does not mutate workflow state.")
    args = parser.parse_args(argv)

    report = collect_stage_coverage(
        stage_id=args.stage_id,
        start_month=args.start_month,
        end_month=args.end_month,
        expected_count=args.expected_count,
        database_url=args.database_url,
        accepted_failure_request_ids=args.accepted_failure_request_id,
        accepted_failure_refs=args.accepted_failure_ref,
    )
    if args.write:
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(report.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_stage_coverage(report, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_STAGE_COVERAGE_PATH",
    "StageCoverageReport",
    "collect_stage_coverage",
    "summarize_stage_coverage_from_rows",
    "write_stage_coverage",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

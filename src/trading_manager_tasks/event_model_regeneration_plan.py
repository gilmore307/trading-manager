"""Safe regeneration plan after the EventRiskGovernor redo closeout.

The plan is intentionally non-mutating. It defines what to preserve, what to
supersede/rebuild, and the ordered manager/model/data/storage gates required
before any later storage cleanup review.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO

from .event_feed_backfill import DEFAULT_TARGET_CIK, DEFAULT_TARGET_SYMBOL, REQUIRED_EVENT_FEED_IDS
from .monthly_backfill import iter_monthly_windows
from .request_payloads import DEFAULT_STORAGE_ROOT


@dataclass(frozen=True)
class RegenerationStep:
    step_id: str
    owner_repo: str
    action: str
    command_ref: str
    status: str
    mutation_class: str
    provider_calls_allowed: bool
    requires_review_before_apply: bool

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventModelRegenerationPlan:
    contract_type: str
    start_month: str
    end_month: str
    target_symbol: str
    target_cik: str
    fold_months: tuple[str, ...]
    required_event_feed_ids: tuple[str, ...]
    preserved_surfaces: tuple[str, ...]
    superseded_surfaces: tuple[str, ...]
    invalidation_scope: str
    regeneration_steps: tuple[RegenerationStep, ...]
    storage_cleanup_gate: str
    notes: tuple[str, ...]
    write_performed: bool = False
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "start_month": self.start_month,
            "end_month": self.end_month,
            "target_symbol": self.target_symbol,
            "target_cik": self.target_cik,
            "fold_months": list(self.fold_months),
            "required_event_feed_ids": list(self.required_event_feed_ids),
            "preserved_surfaces": list(self.preserved_surfaces),
            "superseded_surfaces": list(self.superseded_surfaces),
            "invalidation_scope": self.invalidation_scope,
            "regeneration_steps": [step.summary_row() for step in self.regeneration_steps],
            "storage_cleanup_gate": self.storage_cleanup_gate,
            "notes": list(self.notes),
            "write_performed": self.write_performed,
            "provider_calls": self.provider_calls,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "storage_lifecycle_mutation_performed": self.storage_lifecycle_mutation_performed,
        }


def _months(start_month: str, end_month: str) -> tuple[str, ...]:
    return tuple(window.month for window in iter_monthly_windows(start_month, end_month))


def build_event_model_regeneration_plan(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str = DEFAULT_TARGET_SYMBOL,
    target_cik: str = DEFAULT_TARGET_CIK,
) -> EventModelRegenerationPlan:
    """Build the safe event-model regeneration/invalidation plan.

    The returned artifact is a plan only. It never prepares task keys, dispatches
    providers, invalidates workflow state, runs models, activates models, or
    mutates storage. Separate reviewed entrypoints own each executable step.
    """

    fold_months = _months(start_month, end_month)
    return EventModelRegenerationPlan(
        contract_type="manager_event_model_regeneration_plan_v1",
        start_month=start_month,
        end_month=end_month,
        target_symbol=target_symbol.upper(),
        target_cik=str(target_cik).zfill(10),
        fold_months=fold_months,
        required_event_feed_ids=tuple(REQUIRED_EVENT_FEED_IDS),
        preserved_surfaces=(
            "reviewed_provider_data_and_monthly_cleaned_data_when_point_in_time_valid",
            "layer_01_market_regime_and_layer_02_sector_context_persistent_foundation_data",
            "base_layer_03_07_outputs_that_do_not_consume_legacy_event_overlay_or_abnormal_activity_only_inputs",
            "event_redo_diagnostic_evidence_artifacts_for_comparison_debug_and_audit",
            "storage_artifacts_and_dashboard_snapshots_until_regeneration_review_completes",
        ),
        superseded_surfaces=(
            "legacy_event_overlay_or_abnormal_activity_only_layer_8_outputs",
            "event_risk_governor_outputs_built_before_required_event_feed_coverage",
            "promotion_review_artifacts_claiming_event_alpha_without_closeout_gate_evidence",
            "model_run_metadata_that_depends_on_the_old_event_model_route_after_reviewed_rebuild_exists",
        ),
        invalidation_scope=(
            "state_only_layer_08_event_risk_governor_and_event_adjusted_outputs; base Layers 1-7 remain reusable "
            "unless a specific artifact consumed legacy event-overlay/source rows or violates the rolling-fold policy"
        ),
        regeneration_steps=(
            RegenerationStep(
                step_id="01_build_closeout_report",
                owner_repo="trading-model",
                action="emit event_model_closeout_report_v1 from accepted final judgment",
                command_ref="python3 scripts/models/model_08_event_risk_governor/build_event_model_closeout_report.py",
                status="ready_offline",
                mutation_class="report_artifact_only",
                provider_calls_allowed=False,
                requires_review_before_apply=False,
            ),
            RegenerationStep(
                step_id="02_prepare_event_feed_backfill_task_keys",
                owner_repo="trading-manager",
                action="prepare required monthly event-feed task keys for the fold without provider calls",
                command_ref="PYTHONPATH=src python3 scripts/tasks/prepare_layer_eight_event_feed_backfill.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write-files",
                status="ready_offline",
                mutation_class="manager_task_key_write_only",
                provider_calls_allowed=False,
                requires_review_before_apply=False,
            ),
            RegenerationStep(
                step_id="03_dispatch_or_verify_event_feed_artifacts",
                owner_repo="trading-manager",
                action="verify existing event-feed artifacts or dispatch bounded provider acquisition only when explicitly approved",
                command_ref="PYTHONPATH=src python3 scripts/tasks/dispatch_event_feed_backfill.py",
                status="approval_required_for_provider_calls",
                mutation_class="bounded_provider_data_acquisition_receipts",
                provider_calls_allowed=True,
                requires_review_before_apply=True,
            ),
            RegenerationStep(
                step_id="04_materialize_source_08_event_risk_governor",
                owner_repo="trading-manager",
                action="materialize source_08_event_risk_governor rows from reviewed local event feeds and detector evidence",
                command_ref="PYTHONPATH=src python3 scripts/tasks/materialize_layer_eight_event_risk_governor_inputs.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write",
                status="blocked_until_event_feed_coverage_ready",
                mutation_class="local_source_materialization_receipt",
                provider_calls_allowed=False,
                requires_review_before_apply=False,
            ),
            RegenerationStep(
                step_id="05_generate_feature_08_and_model_08",
                owner_repo="trading-data;trading-model",
                action="generate feature_08_event_risk_governor then model_08_event_risk_governor/event_context_vector outputs",
                command_ref="trading-data-feature-08-event-risk-governor; python3 scripts/models/model_08_event_risk_governor/generate_model_08_event_risk_governor.py",
                status="blocked_until_source_08_ready",
                mutation_class="offline_model_artifact_generation",
                provider_calls_allowed=False,
                requires_review_before_apply=False,
            ),
            RegenerationStep(
                step_id="06_evaluate_and_review_without_activation",
                owner_repo="trading-model;trading-manager",
                action="evaluate EventRiskGovernor with direction-neutral risk labels first, then submit conservative manager promotion review",
                command_ref="python3 scripts/models/model_08_event_risk_governor/evaluate_model_08_event_risk_governor.py; PYTHONPATH=src python3 scripts/tasks/plan_model_promotion_review.py --model model_08_event_risk_governor",
                status="blocked_until_model_08_ready",
                mutation_class="promotion_evidence_and_review_request_only",
                provider_calls_allowed=False,
                requires_review_before_apply=False,
            ),
            RegenerationStep(
                step_id="07_state_only_invalidation_if_old_outputs_remain",
                owner_repo="trading-manager",
                action="mark stale old event-risk-dependent workflow stages rebuild-required without deleting artifacts",
                command_ref="PYTHONPATH=src python3 scripts/tasks/invalidate_layer_eight_event_downstream_outputs.py --write",
                status="review_before_write",
                mutation_class="workflow_state_only_no_artifact_deletion",
                provider_calls_allowed=False,
                requires_review_before_apply=True,
            ),
            RegenerationStep(
                step_id="08_revisit_storage_lifecycle_hold",
                owner_repo="trading-storage;trading-manager",
                action="after reviewed rebuild, rerun lifecycle/dashboard-prune dry-runs and decide whether any deletion is safe",
                command_ref="PYTHONPATH=src python3 scripts/dashboard/prune_dashboard_snapshots.py --dry-run",
                status="blocked_until_regeneration_review_complete",
                mutation_class="dry_run_only_until_explicit_delete_approval",
                provider_calls_allowed=False,
                requires_review_before_apply=True,
            ),
        ),
        storage_cleanup_gate=(
            "Do not delete dashboard snapshots, model-run metadata, or old event diagnostic artifacts until the regenerated "
            "EventRiskGovernor fold has closeout/evaluation/review evidence and Chentong approves a storage lifecycle apply step."
        ),
        notes=(
            "Layer 1 and Layer 2 data are persistent foundations: compress/archive only, never auto-delete.",
            "The event redo closes as risk governance, not signed alpha or option-flow promotion.",
            "Current earnings/guidance route remains blocked for signed claims by missing comparable current guidance and PIT expectation baselines.",
            "This plan is non-mutating; executable steps remain separate reviewed tools.",
        ),
    )


def write_plan(plan: EventModelRegenerationPlan, *, output: TextIO) -> None:
    json.dump(plan.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def write_plan_file(plan: EventModelRegenerationPlan, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan safe EventRiskGovernor regeneration after the event-model redo closeout.")
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--target-symbol", default=DEFAULT_TARGET_SYMBOL)
    parser.add_argument("--target-cik", default=DEFAULT_TARGET_CIK)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT, help="Accepted for CLI consistency; not written by this planner.")
    args = parser.parse_args(argv)
    _ = args.storage_root
    plan = build_event_model_regeneration_plan(
        start_month=args.start_month,
        end_month=args.end_month,
        target_symbol=args.target_symbol,
        target_cik=args.target_cik,
    )
    if args.output_json:
        write_plan_file(plan, args.output_json)
    write_plan(plan, output=sys.stdout)
    return 0


__all__ = ["EventModelRegenerationPlan", "RegenerationStep", "build_event_model_regeneration_plan", "write_plan", "write_plan_file"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""M03 event-family modelability evidence acquisition planning.

This module owns the pre-review acquisition plan for M06 modelability work. It
may prepare bounded provider task keys through the existing event-feed backfill
route, but it does not call providers, judge probability-function classes,
activate models, submit broker orders, or write dashboard read models.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .event_feed_backfill import DEFAULT_TARGET_CIK, DEFAULT_TARGET_SYMBOL, EventFeedTaskKey, prepare_event_feed_backfill
from .request_payloads import DEFAULT_STORAGE_ROOT

MODELABILITY_ACQUISITION_CONTRACT_TYPE = "model_06_event_family_modelability_acquisition_plan"
DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS = 8

EVENT_FAMILY_FEED_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "company_earnings_or_financial_results": (
        "08_feed_sec_company_financials",
        "03_feed_alpaca_news",
        "05_feed_gdelt_news",
    ),
    "target_product_price_change_news": (
        "03_feed_alpaca_news",
        "05_feed_gdelt_news",
    ),
    "target_product_launch_news": (
        "03_feed_alpaca_news",
        "05_feed_gdelt_news",
    ),
    "target_supply_chain_disruption_news": (
        "03_feed_alpaca_news",
        "05_feed_gdelt_news",
    ),
    "target_regulatory_antitrust_news": (
        "03_feed_alpaca_news",
        "05_feed_gdelt_news",
    ),
    "cpi_release": (
        "05_feed_gdelt_news",
    ),
    "ppi_release": (
        "05_feed_gdelt_news",
    ),
}

COARSE_EVENT_SOURCE_CATEGORIES = {
    "news": "news is a source class; use a concrete news event family such as target_product_price_change_news",
    "target_news_or_disclosure": "target_news_or_disclosure is a source/category bucket; use a concrete news event family",
    "disclosure": "disclosure is a source/category bucket; use a concrete disclosure event family",
    "scheduled_macro_release": "scheduled_macro_release is a schedule/source category; use a concrete release family such as cpi_release or ppi_release",
    "macro": "macro is a domain bucket; use a concrete macro event family such as cpi_release or ppi_release",
    "macro_release": "macro_release is a release category; use a concrete macro event family such as cpi_release or ppi_release",
    "economic_release": "economic_release is a release category; use a concrete macro event family such as cpi_release or ppi_release",
}

TARGET_SPECIFIC_EVENT_FAMILY_ALIASES = {
    "apple_product_price_change",
    "aapl_product_price_change",
    "nvda_product_price_change",
    "amd_product_price_change",
    "apple_product_price_increase",
    "aapl_product_price_increase",
    "nvda_product_price_increase",
    "amd_product_price_increase",
    "apple_product_price_decrease",
    "aapl_product_price_decrease",
    "nvda_product_price_decrease",
    "amd_product_price_decrease",
    "apple_product_launch",
    "aapl_product_launch",
    "nvda_product_launch",
    "amd_product_launch",
    "apple_supply_chain_disruption",
    "aapl_supply_chain_disruption",
    "nvda_supply_chain_disruption",
    "amd_supply_chain_disruption",
    "apple_regulatory_antitrust",
    "aapl_regulatory_antitrust",
    "nvda_regulatory_antitrust",
    "amd_regulatory_antitrust",
}

EVENT_FAMILY_ALIASES = {
    "earnings": "company_earnings_or_financial_results",
    "earnings_release": "company_earnings_or_financial_results",
    "financial_results": "company_earnings_or_financial_results",
    "company_financials": "company_earnings_or_financial_results",
    "product_price_change": "target_product_price_change_news",
    "product_pricing_change": "target_product_price_change_news",
    "product_price_change_news": "target_product_price_change_news",
    "product_price_increase": "target_product_price_change_news",
    "product_price_increase_news": "target_product_price_change_news",
    "price_increase_news": "target_product_price_change_news",
    "product_price_decrease": "target_product_price_change_news",
    "product_price_decrease_news": "target_product_price_change_news",
    "price_decrease_news": "target_product_price_change_news",
    "product_launch": "target_product_launch_news",
    "product_launch_news": "target_product_launch_news",
    "supply_chain_disruption": "target_supply_chain_disruption_news",
    "supply_chain_disruption_news": "target_supply_chain_disruption_news",
    "regulatory_antitrust": "target_regulatory_antitrust_news",
    "regulatory_antitrust_news": "target_regulatory_antitrust_news",
    "cpi": "cpi_release",
    "consumer_price_index": "cpi_release",
    "consumer_price_index_release": "cpi_release",
    "ppi": "ppi_release",
    "producer_price_index": "ppi_release",
    "producer_price_index_release": "ppi_release",
    "market_session": "market_session_calendar_event",
    "market_calendar": "market_session_calendar_event",
    "exchange_calendar": "market_session_calendar_event",
}


@dataclass(frozen=True)
class EventFamilyModelabilityAcquisitionPlan:
    contract_type: str
    model_surface: str
    event_family_id: str
    event_family_modelability_review_gate: str
    projection_mode_review_scope: str
    probability_function_class_review_scope: str
    deterministic_control_policy: str
    agent_role_policy: str
    start_month: str
    end_month: str
    target_symbol: str
    target_cik: str
    candidate_seed_event_ref: str | None
    minimum_same_family_observations: int
    same_family_evidence_policy: str
    event_family_generalization_policy: str
    single_observation_policy: str
    required_feed_ids: tuple[str, ...]
    task_key_count: int
    write_performed: bool
    provider_calls: int
    modelability_review_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    required_next_action: str
    task_keys: tuple[EventFeedTaskKey, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["task_keys"] = [item.summary_row() for item in self.task_keys]
        return row


def canonical_event_family_id(event_family_id: str) -> str:
    normalized = event_family_id.strip().lower().replace("-", "_").replace(" ", "_")
    if not normalized:
        raise TaskSystemError("event_family_id is required")
    if normalized in COARSE_EVENT_SOURCE_CATEGORIES:
        raise TaskSystemError(
            "event_family_id must name a concrete same-family event, not a source/category bucket: "
            + COARSE_EVENT_SOURCE_CATEGORIES[normalized]
        )
    if normalized in TARGET_SPECIFIC_EVENT_FAMILY_ALIASES:
        raise TaskSystemError(
            "event_family_id must be target-agnostic; put ticker/company identity in affected_entities, target_symbol, or acquisition filters"
        )
    return EVENT_FAMILY_ALIASES.get(normalized, normalized)


def required_feeds_for_event_family(event_family_id: str) -> tuple[str, ...]:
    canonical = canonical_event_family_id(event_family_id)
    feed_ids = EVENT_FAMILY_FEED_REQUIREMENTS.get(canonical)
    if not feed_ids:
        raise TaskSystemError(f"unsupported event family modelability acquisition route: {event_family_id}")
    return feed_ids


def plan_event_family_modelability_acquisition(
    *,
    event_family_id: str,
    start_month: str,
    end_month: str,
    target_symbol: str = DEFAULT_TARGET_SYMBOL,
    target_cik: str = DEFAULT_TARGET_CIK,
    candidate_seed_event_ref: str | None = None,
    minimum_same_family_observations: int = DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    write_files: bool = False,
) -> EventFamilyModelabilityAcquisitionPlan:
    if minimum_same_family_observations < 2:
        raise TaskSystemError("M06 modelability review requires multiple same-family observations")
    canonical_family = canonical_event_family_id(event_family_id)
    required_feed_ids = required_feeds_for_event_family(canonical_family)
    feed_summary = prepare_event_feed_backfill(
        start_month=start_month,
        end_month=end_month,
        target_symbol=target_symbol,
        target_cik=target_cik,
        storage_root=storage_root,
        feed_ids=required_feed_ids,
        write_files=write_files,
    )
    return EventFamilyModelabilityAcquisitionPlan(
        contract_type=MODELABILITY_ACQUISITION_CONTRACT_TYPE,
        model_surface="model_06_residual_event_governance",
        event_family_id=canonical_family,
        event_family_modelability_review_gate="event-family-modelability-review",
        projection_mode_review_scope="impact_function_projection|conditional_effect_projection|context_only_projection|do_not_model",
        probability_function_class_review_scope="M06 selects the allowed probability-function class only after acquired same-family evidence is sufficient; M03 owns concrete parameter training.",
        deterministic_control_policy="Program gates own acquisition scope, source coverage, sample thresholds, PIT clocks, dedupe, overlap checks, stop conditions, and review readiness.",
        agent_role_policy="Codex skills are semantic reviewers only; they do not control provider dispatch, expand scope, decide readiness, train parameters, or perform actions that deterministic code can own.",
        start_month=start_month,
        end_month=end_month,
        target_symbol=target_symbol.upper(),
        target_cik=str(target_cik).zfill(10),
        candidate_seed_event_ref=candidate_seed_event_ref,
        minimum_same_family_observations=minimum_same_family_observations,
        same_family_evidence_policy="M06 modelability review must use multiple PIT-valid same-family observations with coverage, controls, and leakage evidence.",
        event_family_generalization_policy="Event families are defined by scenario/mechanism, not by ticker or company identity; AAPL/NVDA/AMD are observation entities or acquisition filters.",
        single_observation_policy="A single event is only a candidate seed; it cannot establish event-family probability-function type.",
        required_feed_ids=required_feed_ids,
        task_key_count=feed_summary.task_key_count,
        write_performed=feed_summary.write_performed,
        provider_calls=0,
        modelability_review_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        required_next_action="dispatch prepared provider task keys, materialize reviewed source artifacts, then build the same-family evidence packet before Codex modelability review",
        task_keys=feed_summary.task_keys,
    )


def write_plan(plan: EventFamilyModelabilityAcquisitionPlan, *, output: TextIO) -> None:
    json.dump(plan.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare M03 event-family modelability acquisition task keys without provider calls.")
    parser.add_argument("--event-family-id", required=True)
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--target-symbol", default=DEFAULT_TARGET_SYMBOL)
    parser.add_argument("--target-cik", default=DEFAULT_TARGET_CIK)
    parser.add_argument("--candidate-seed-event-ref")
    parser.add_argument("--minimum-same-family-observations", type=int, default=DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--write-files", action="store_true")
    args = parser.parse_args(argv)
    try:
        plan = plan_event_family_modelability_acquisition(
            event_family_id=args.event_family_id,
            start_month=args.start_month,
            end_month=args.end_month,
            target_symbol=args.target_symbol,
            target_cik=args.target_cik,
            candidate_seed_event_ref=args.candidate_seed_event_ref,
            minimum_same_family_observations=args.minimum_same_family_observations,
            storage_root=args.storage_root,
            write_files=args.write_files,
        )
    except TaskSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    write_plan(plan, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS",
    "EVENT_FAMILY_FEED_REQUIREMENTS",
    "EventFamilyModelabilityAcquisitionPlan",
    "canonical_event_family_id",
    "plan_event_family_modelability_acquisition",
    "required_feeds_for_event_family",
    "write_plan",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

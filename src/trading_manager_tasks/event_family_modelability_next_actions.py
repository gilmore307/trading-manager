"""Execute deterministic next-action routing for M06 modelability packets.

This module turns evidence-packet readiness states into program-owned follow-up
artifacts. It prepares queues and task keys only; it does not call providers,
run Codex review, train models, activate models, submit broker orders, or write
dashboard read models.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .event_family_modelability_acquisition import (
    DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
    plan_event_family_modelability_acquisition,
)
from .event_family_modelability_evidence import (
    DEFAULT_OBSERVATION_SAMPLE_LIMIT,
    DEFAULT_PACKET_ROOT,
    EventFamilyModelabilityEvidencePacket,
    MACRO_RELEASE_EVENT_TYPE_TERMS,
    build_packet_from_database,
    packet_output_path,
    persist_packet,
)
from .storage_paths import manager_storage_root

MODELABILITY_NEXT_ACTION_ROUTE_CONTRACT_TYPE = "model_06_event_family_modelability_next_action_route"
MODELABILITY_NEXT_ACTION_SUMMARY_CONTRACT_TYPE = "model_06_event_family_modelability_next_action_summary"
DEFAULT_NEXT_ACTION_ROOT = manager_storage_root() / "runtime" / "model_06_event_family_modelability" / "next_action_routes"
DEFAULT_EVENT_FAMILIES = (
    "company_earnings_or_financial_results",
    "target_product_price_change_news",
    "target_product_launch_news",
    "target_supply_chain_disruption_news",
    "target_regulatory_antitrust_news",
    "market_session_calendar_event",
    "cpi_release",
    "ppi_release",
)


@dataclass(frozen=True)
class EventFamilyModelabilityNextActionRoute:
    contract_type: str
    source_contract_type: str
    event_family_id: str
    target_symbol: str
    target_cik: str
    start_month: str
    end_month: str
    readiness_status: str
    next_action_owner: str
    required_next_action: str
    route_status: str
    route_artifact_path: str
    evidence_packet_path: str
    write_performed: bool
    provider_calls: int
    codex_review_performed: bool
    model_training_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    route_plan: dict[str, Any]

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventFamilyModelabilityNextActionSummary:
    contract_type: str
    target_symbol: str
    target_cik: str
    start_month: str
    end_month: str
    event_family_count: int
    write_performed: bool
    provider_calls: int
    codex_reviews_performed: int
    model_training_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    output_path: str
    routes: tuple[EventFamilyModelabilityNextActionRoute, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["routes"] = [route.summary_row() for route in self.routes]
        return row


def _window_id(start_month: str, end_month: str) -> str:
    return f"{start_month}_{end_month}".replace("-", "_")


def _route_dir(
    packet: EventFamilyModelabilityEvidencePacket,
    *,
    next_action_root: Path = DEFAULT_NEXT_ACTION_ROOT,
) -> Path:
    return next_action_root / packet.event_family_id / packet.target_symbol.lower() / _window_id(packet.start_month, packet.end_month)


def _write_json_if_requested(payload: Mapping[str, Any], path: Path, *, write_files: bool) -> str:
    if write_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def _structured_enrichment_payload(packet: EventFamilyModelabilityEvidencePacket) -> dict[str, Any]:
    macro_release_result_counts = _macro_release_result_counts(packet)
    if macro_release_result_counts and macro_release_result_counts["actual_value_count"] > 0:
        return {
            "contract_type": "model_06_event_family_structured_evidence_gap_receipt",
            "source_contract_type": packet.contract_type,
            "event_family_id": packet.event_family_id,
            "target_symbol": packet.target_symbol,
            "target_cik": packet.target_cik,
            "start_month": packet.start_month,
            "end_month": packet.end_month,
            "readiness_reasons": list(packet.readiness_reasons),
            "program_owner": "program_enrichment",
            "route_status": "parked_missing_expectation_baseline_source",
            "provider_dispatch_allowed": False,
            "provider_calls": 0,
            "codex_review_allowed": False,
            "macro_release_result_counts": macro_release_result_counts,
            "completion_gate": "add or materialize PIT consensus/forecast baseline source, then rebuild evidence packet",
        }
    return {
        "contract_type": "model_06_event_family_structured_evidence_enrichment_plan",
        "source_contract_type": packet.contract_type,
        "event_family_id": packet.event_family_id,
        "target_symbol": packet.target_symbol,
        "target_cik": packet.target_cik,
        "start_month": packet.start_month,
        "end_month": packet.end_month,
        "required_outputs": list(packet.next_action_plan.get("required_outputs") or ()),
        "readiness_reasons": list(packet.readiness_reasons),
        "program_owner": "program_enrichment",
        "route_status": "queued_for_program_enrichment",
        "provider_dispatch_allowed": bool(packet.next_action_plan.get("provider_dispatch_allowed")),
        "provider_calls": 0,
        "codex_review_allowed": False,
        "completion_gate": packet.next_action_plan.get("completion_gate"),
    }


def _macro_release_result_counts(packet: EventFamilyModelabilityEvidencePacket) -> dict[str, int]:
    if packet.event_family_id not in MACRO_RELEASE_EVENT_TYPE_TERMS:
        return {}
    actual_count = 0
    consensus_count = 0
    surprise_count = 0
    for observation in packet.observations:
        parameters = observation.normalized_event_parameters
        if parameters.get("actual_value") not in (None, ""):
            actual_count += 1
        if parameters.get("consensus_value") not in (None, ""):
            consensus_count += 1
        if parameters.get("surprise_value") not in (None, ""):
            surprise_count += 1
    return {
        "observation_count": len(packet.observations),
        "actual_value_count": actual_count,
        "consensus_value_count": consensus_count,
        "surprise_value_count": surprise_count,
    }


def _modelability_gate_payload(packet: EventFamilyModelabilityEvidencePacket) -> dict[str, Any]:
    missing_gates = list(packet.next_action_plan.get("missing_gates") or ())
    return {
        "contract_type": "model_06_event_family_modelability_gate_build_receipt",
        "source_contract_type": packet.contract_type,
        "event_family_id": packet.event_family_id,
        "target_symbol": packet.target_symbol,
        "target_cik": packet.target_cik,
        "start_month": packet.start_month,
        "end_month": packet.end_month,
        "missing_gates": missing_gates,
        "gate_results": {gate: "blocked_missing_gate_input_artifact" for gate in missing_gates},
        "required_outputs": list(packet.next_action_plan.get("required_outputs") or ()),
        "program_owner": "program_modelability_gate_builder",
        "route_status": "blocked_missing_modelability_gate_inputs",
        "provider_calls": 0,
        "codex_review_allowed": False,
        "completion_gate": "materialize matched controls, overlap/confounder evidence, leakage checks, horizon labels, and fold calibration before rebuilding the packet",
    }


def _semantic_review_handoff_payload(packet: EventFamilyModelabilityEvidencePacket) -> dict[str, Any]:
    review_kind = str(packet.next_action_plan.get("action_type") or "")
    required_skill = str(packet.next_action_plan.get("required_skill") or "")
    return {
        "contract_type": "model_06_event_family_semantic_review_handoff",
        "source_contract_type": packet.contract_type,
        "event_family_id": packet.event_family_id,
        "target_symbol": packet.target_symbol,
        "target_cik": packet.target_cik,
        "start_month": packet.start_month,
        "end_month": packet.end_month,
        "review_kind": review_kind,
        "required_skill": required_skill,
        "program_owner": "codex_semantic_review",
        "route_status": "queued_for_codex_semantic_review",
        "provider_calls": 0,
        "codex_review_performed": False,
        "completion_gate": packet.next_action_plan.get("completion_gate"),
    }


def route_packet_next_action(
    packet: EventFamilyModelabilityEvidencePacket,
    *,
    storage_root: Path,
    packet_root: Path = DEFAULT_PACKET_ROOT,
    next_action_root: Path = DEFAULT_NEXT_ACTION_ROOT,
    write_files: bool = False,
) -> EventFamilyModelabilityNextActionRoute:
    packet_path = packet_output_path(packet, output_root=packet_root)
    if write_files:
        packet_path = persist_packet(packet, output_root=packet_root)
    route_dir = _route_dir(packet, next_action_root=next_action_root)
    route_artifact_name = "next_action_route.json"
    route_plan: dict[str, Any]
    route_status: str

    if packet.next_action_owner == "program_acquisition":
        acquisition_plan = plan_event_family_modelability_acquisition(
            event_family_id=packet.event_family_id,
            start_month=packet.start_month,
            end_month=packet.end_month,
            target_symbol=packet.target_symbol,
            target_cik=packet.target_cik,
            minimum_same_family_observations=packet.minimum_same_family_observations,
            storage_root=storage_root,
            write_files=write_files,
        )
        route_status = "prepared_acquisition_task_keys"
        route_plan = {
            "action_artifact_type": acquisition_plan.contract_type,
            "action_artifact_path": str(route_dir / "acquisition_plan.json"),
            "task_key_count": acquisition_plan.task_key_count,
            "required_feed_ids": list(acquisition_plan.required_feed_ids),
            "provider_calls": acquisition_plan.provider_calls,
            "task_keys": [item.summary_row() for item in acquisition_plan.task_keys],
            "next_step_after_preparation": acquisition_plan.required_next_action,
        }
        _write_json_if_requested(acquisition_plan.summary_row(), route_dir / "acquisition_plan.json", write_files=write_files)
    elif packet.next_action_owner == "program_enrichment":
        payload = _structured_enrichment_payload(packet)
        route_status = str(payload["route_status"])
        artifact_name = (
            "structured_evidence_gap_receipt.json"
            if payload["contract_type"] == "model_06_event_family_structured_evidence_gap_receipt"
            else "structured_evidence_enrichment_plan.json"
        )
        route_plan = {
            "action_artifact_type": payload["contract_type"],
            "action_artifact_path": str(route_dir / artifact_name),
            **payload,
        }
        _write_json_if_requested(payload, route_dir / artifact_name, write_files=write_files)
    elif packet.next_action_owner == "program_modelability_gate_builder":
        payload = _modelability_gate_payload(packet)
        route_status = str(payload["route_status"])
        route_plan = {
            "action_artifact_type": payload["contract_type"],
            "action_artifact_path": str(route_dir / "modelability_gate_build_receipt.json"),
            **payload,
        }
        _write_json_if_requested(payload, route_dir / "modelability_gate_build_receipt.json", write_files=write_files)
    elif packet.next_action_owner == "codex_semantic_review":
        payload = _semantic_review_handoff_payload(packet)
        route_status = "queued_for_codex_semantic_review"
        route_plan = {
            "action_artifact_type": payload["contract_type"],
            "action_artifact_path": str(route_dir / "semantic_review_handoff.json"),
            **payload,
        }
        _write_json_if_requested(payload, route_dir / "semantic_review_handoff.json", write_files=write_files)
    else:
        route_status = "queued_for_program_triage"
        route_plan = {
            "action_artifact_type": "model_06_event_family_program_triage_plan",
            "action_artifact_path": str(route_dir / "program_triage_plan.json"),
            "route_status": route_status,
            "next_action_plan": dict(packet.next_action_plan),
        }
        _write_json_if_requested(route_plan, route_dir / "program_triage_plan.json", write_files=write_files)

    route = EventFamilyModelabilityNextActionRoute(
        contract_type=MODELABILITY_NEXT_ACTION_ROUTE_CONTRACT_TYPE,
        source_contract_type=packet.contract_type,
        event_family_id=packet.event_family_id,
        target_symbol=packet.target_symbol,
        target_cik=packet.target_cik,
        start_month=packet.start_month,
        end_month=packet.end_month,
        readiness_status=packet.readiness_status,
        next_action_owner=packet.next_action_owner,
        required_next_action=packet.required_next_action,
        route_status=route_status,
        route_artifact_path=str(route_dir / route_artifact_name),
        evidence_packet_path=str(packet_path),
        write_performed=write_files,
        provider_calls=0,
        codex_review_performed=False,
        model_training_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        route_plan=route_plan,
    )
    _write_json_if_requested(route.summary_row(), route_dir / route_artifact_name, write_files=write_files)
    return route


def route_event_families_from_database(
    *,
    event_family_ids: Sequence[str],
    target_symbol: str,
    target_cik: str,
    start_month: str,
    end_month: str,
    minimum_same_family_observations: int = DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS,
    observation_sample_limit: int = DEFAULT_OBSERVATION_SAMPLE_LIMIT,
    database_url: str | None = None,
    storage_root: Path,
    packet_root: Path = DEFAULT_PACKET_ROOT,
    next_action_root: Path = DEFAULT_NEXT_ACTION_ROOT,
    write_files: bool = False,
) -> EventFamilyModelabilityNextActionSummary:
    routes: list[EventFamilyModelabilityNextActionRoute] = []
    for event_family_id in event_family_ids:
        packet = build_packet_from_database(
            event_family_id=event_family_id,
            target_symbol=target_symbol,
            target_cik=target_cik,
            start_month=start_month,
            end_month=end_month,
            minimum_same_family_observations=minimum_same_family_observations,
            observation_sample_limit=observation_sample_limit,
            database_url=database_url,
        )
        routes.append(
            route_packet_next_action(
                packet,
                storage_root=storage_root,
                packet_root=packet_root,
                next_action_root=next_action_root,
                write_files=write_files,
            )
        )

    output_path = next_action_root / f"{target_symbol.lower()}_{_window_id(start_month, end_month)}_next_action_summary.json"
    summary = EventFamilyModelabilityNextActionSummary(
        contract_type=MODELABILITY_NEXT_ACTION_SUMMARY_CONTRACT_TYPE,
        target_symbol=target_symbol.upper(),
        target_cik=str(target_cik).zfill(10),
        start_month=start_month,
        end_month=end_month,
        event_family_count=len(routes),
        write_performed=write_files,
        provider_calls=0,
        codex_reviews_performed=0,
        model_training_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        output_path=str(output_path),
        routes=tuple(routes),
    )
    _write_json_if_requested(summary.summary_row(), output_path, write_files=write_files)
    return summary


def write_summary(summary: EventFamilyModelabilityNextActionSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic next-action routing for M06 modelability evidence packets.")
    parser.add_argument("--event-family-id", action="append", default=[], help="Concrete event family id. Defaults to the current trial family set.")
    parser.add_argument("--target-symbol", default="AAPL")
    parser.add_argument("--target-cik", default="0000320193")
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--minimum-same-family-observations", type=int, default=DEFAULT_MINIMUM_SAME_FAMILY_OBSERVATIONS)
    parser.add_argument("--observation-sample-limit", type=int, default=DEFAULT_OBSERVATION_SAMPLE_LIMIT)
    parser.add_argument("--database-url")
    parser.add_argument("--storage-root", type=Path, default=manager_storage_root())
    parser.add_argument("--packet-root", type=Path, default=DEFAULT_PACKET_ROOT)
    parser.add_argument("--next-action-root", type=Path, default=DEFAULT_NEXT_ACTION_ROOT)
    parser.add_argument("--write-files", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = route_event_families_from_database(
            event_family_ids=tuple(args.event_family_id or DEFAULT_EVENT_FAMILIES),
            target_symbol=args.target_symbol,
            target_cik=args.target_cik,
            start_month=args.start_month,
            end_month=args.end_month,
            minimum_same_family_observations=args.minimum_same_family_observations,
            observation_sample_limit=args.observation_sample_limit,
            database_url=args.database_url,
            storage_root=args.storage_root,
            packet_root=args.packet_root,
            next_action_root=args.next_action_root,
            write_files=args.write_files,
        )
    except TaskSystemError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "DEFAULT_EVENT_FAMILIES",
    "DEFAULT_NEXT_ACTION_ROOT",
    "EventFamilyModelabilityNextActionRoute",
    "EventFamilyModelabilityNextActionSummary",
    "MODELABILITY_NEXT_ACTION_ROUTE_CONTRACT_TYPE",
    "MODELABILITY_NEXT_ACTION_SUMMARY_CONTRACT_TYPE",
    "route_event_families_from_database",
    "route_packet_next_action",
    "write_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

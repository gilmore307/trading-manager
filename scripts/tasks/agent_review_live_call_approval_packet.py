#!/usr/bin/env python3
"""Persist an owner-observed agent review for a live-call approval packet.

This script writes local approval/validation/plan artifacts only. It does not
call providers; provider dispatch remains a separate audited command that can be
run automatically by the owner-observed controller.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.live_call_packet import inspect_live_call_approval_packet
from trading_manager_tasks.live_call_planning import validate_live_call_approval_against_proposal
from trading_manager_tasks.provider_dispatch import dispatch_layer_provider_acquisition
from trading_manager_tasks.request_payloads import DEFAULT_STORAGE_ROOT


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TaskSystemError(f"expected JSON object: {path}")
    return payload


def _resolve_packet_file(packet_or_dir: Path) -> Path:
    return packet_or_dir / "packet.json" if packet_or_dir.is_dir() else packet_or_dir


def _agent_approval(
    *,
    packet: Mapping[str, Any],
    proposal: Mapping[str, Any],
    reviewed_by: str,
    valid_hours: int,
    now: datetime,
) -> dict[str, Any]:
    template = proposal.get("approval_template")
    if not isinstance(template, Mapping):
        raise TaskSystemError("proposal.approval_template is required")
    if valid_hours <= 0:
        raise TaskSystemError("--valid-hours must be positive")
    approval = dict(template)
    approval.update(
        {
            "decision_status": "approved",
            "approved_by": reviewed_by,
            "approved_at_utc": now.isoformat().replace("+00:00", "Z"),
            "expires_at_utc": (now + timedelta(hours=valid_hours)).isoformat().replace("+00:00", "Z"),
            "request_ids": [str(item) for item in packet.get("proposal_request_ids") or proposal.get("request_ids") or []],
            "owner_observed_automation": True,
            "review_note": (
                "Agent-reviewed approval under owner-observed historical automation policy. "
                "Scope is provider_data_acquisition_only for the exact proposal request_ids; "
                "broker execution, model activation, and storage lifecycle mutation remain false."
            ),
        }
    )
    return approval


def agent_review_packet(
    *,
    packet_path: Path,
    reviewed_by: str,
    valid_hours: int,
    database_url: str | None = None,
) -> dict[str, Any]:
    packet_file = _resolve_packet_file(packet_path)
    packet = _read_json(packet_file)
    if packet.get("contract_type") != "manager_live_call_approval_packet_v1":
        raise TaskSystemError("packet contract_type must be manager_live_call_approval_packet_v1")
    proposal_path = Path(str(packet.get("proposal_path") or ""))
    proposal = _read_json(proposal_path)
    before = inspect_live_call_approval_packet(packet_path=packet_file)
    now = datetime.now(UTC).replace(microsecond=0)
    approval = _agent_approval(packet=packet, proposal=proposal, reviewed_by=reviewed_by, valid_hours=valid_hours, now=now)
    validation = validate_live_call_approval_against_proposal(proposal, approval, now_utc=now)
    approval_path = Path(str(packet.get("reviewed_approval_path") or packet_file.parent / "reviewed_approval.json"))
    validation_path = Path(str(packet.get("validation_output_path") or packet_file.parent / "proposal_validation.json"))
    dispatch_plan_path = Path(str(packet.get("dispatch_plan_output_path") or packet_file.parent / "dispatch_plan.json"))
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    dispatch_plan_path.parent.mkdir(parents=True, exist_ok=True)
    approval_path.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_path.write_text(json.dumps(validation.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    dispatch_plan = dispatch_layer_provider_acquisition(
        model_layer=str(packet.get("model_layer") or ""),
        start_month=str(packet.get("start_month") or ""),
        end_month=str(packet.get("end_month") or ""),
        storage_root=Path(str(packet.get("manager_storage_root") or DEFAULT_STORAGE_ROOT)),
        approval_path=approval_path,
        approval_validation_path=validation_path,
        request_ids=tuple(str(item) for item in packet.get("proposal_request_ids") or []),
        execute_approved_provider_calls=False,
        skip_registered_failures=True,
        database_url=database_url,
    )
    dispatch_plan_path.write_text(json.dumps(dispatch_plan.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    after = inspect_live_call_approval_packet(packet_path=packet_file)
    return {
        "contract_type": "manager_live_call_approval_packet_agent_review_v1",
        "packet_id": packet.get("packet_id"),
        "packet_dir": str(packet_file.parent),
        "model_layer": packet.get("model_layer"),
        "stage_id": packet.get("stage_id"),
        "start_month": packet.get("start_month"),
        "end_month": packet.get("end_month"),
        "request_count": packet.get("request_count"),
        "approval_id": validation.approval_id,
        "reviewed_approval_path": str(approval_path),
        "validation_output_path": str(validation_path),
        "dispatch_plan_output_path": str(dispatch_plan_path),
        "validation_count": validation.gate_validation_count,
        "dispatch_count": dispatch_plan.dispatch_count,
        "status_before": before.status,
        "status_after": after.status,
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent-review a live-call approval packet without provider calls.")
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--reviewed-by", default="openclaw_agent_under_owner_observation")
    parser.add_argument("--valid-hours", type=int, default=12)
    parser.add_argument("--database-url")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output-path", type=Path)
    args = parser.parse_args(argv)
    receipt = agent_review_packet(
        packet_path=args.packet,
        reviewed_by=args.reviewed_by,
        valid_hours=args.valid_hours,
        database_url=args.database_url,
    )
    if args.write:
        output_path = args.output_path or Path(str(receipt["packet_dir"])) / "agent_review.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.dump(receipt, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

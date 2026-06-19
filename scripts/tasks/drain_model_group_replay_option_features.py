#!/usr/bin/env python3
"""Drain replay option-feature requirements in bounded provider batches."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from trading_manager_tasks.model_group_replay import DEFAULT_REPLAY_CONTRACT_ID
from trading_manager_tasks.model_group_replay_option_features import (
    REPLAY_OPTION_FEATURE_ACQUISITION_REQUIRED,
    REPLAY_OPTION_FEATURE_BACKOFF_REASON,
    REPLAY_OPTION_FEATURE_STAGE_ID,
    run_model_group_replay_option_features_for_replay_backoff,
)
from trading_manager_tasks.scheduler import SchedulerDecision

REQUIREMENTS_ARTIFACT_REF_FIELD = "_".join(("requirements", "artifact", "ref"))
SCHEDULER_DECISION_CONTRACT_TYPE = "_".join(("manager", "scheduler", "decision"))
DRAIN_STATUS_CONTRACT_TYPE = "_".join(("manager", "model", "group", "replay", "option", "feature", "drain", "status"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements-artifact-ref", type=Path, required=True)
    parser.add_argument("--storage-root", type=Path, default=Path("/root/projects/trading-storage/storage/02_control_plane"))
    parser.add_argument("--contract-id", default=DEFAULT_REPLAY_CONTRACT_ID)
    parser.add_argument("--target-symbol")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument(
        "--feature-repair-limit",
        type=int,
        help="Maximum local feature requirements to repair per batch. Defaults to --batch-size.",
    )
    parser.add_argument("--max-batches", type=int)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--status-jsonl", type=Path)
    parser.add_argument("--latest-status-json", type=Path)
    parser.add_argument("--execute-provider-acquisition", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args(argv)

    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.feature_repair_limit is not None and args.feature_repair_limit <= 0:
        parser.error("--feature-repair-limit must be positive when provided")
    if args.max_batches is not None and args.max_batches <= 0:
        parser.error("--max-batches must be positive when provided")
    if not args.requirements_artifact_ref.exists():
        parser.error(f"--requirements-artifact-ref does not exist: {args.requirements_artifact_ref}")

    batch_index = 0
    while True:
        if args.max_batches is not None and batch_index >= args.max_batches:
            _emit(
                {
                    "event": "stopped",
                    "reason": "max_batches_reached",
                    "batch_index": batch_index,
                    "batch_size": args.batch_size,
                    REQUIREMENTS_ARTIFACT_REF_FIELD: str(args.requirements_artifact_ref),
                },
                args=args,
            )
            return 0

        batch_index += 1
        started = time.time()
        decision = run_model_group_replay_option_features_for_replay_backoff(
            _synthetic_replay_backoff(args.requirements_artifact_ref),
            storage_root=args.storage_root,
            contract_id=args.contract_id,
            execute=not args.plan_only,
            execute_provider_acquisition=args.execute_provider_acquisition,
            provider_acquisition_limit=args.batch_size,
            feature_repair_limit=args.feature_repair_limit or args.batch_size,
            selected_target_symbol=args.target_symbol,
        )
        row = decision.summary_row() if decision is not None else None
        if row is None:
            _emit(
                {
                    "event": "stopped",
                    "reason": "no_replay_option_feature_work_ready",
                    "batch_index": batch_index,
                    "elapsed_seconds": round(time.time() - started, 3),
                    REQUIREMENTS_ARTIFACT_REF_FIELD: str(args.requirements_artifact_ref),
                },
                args=args,
            )
            return 0

        status = _status_from_decision(
            row,
            batch_index=batch_index,
            batch_size=args.batch_size,
            elapsed_seconds=round(time.time() - started, 3),
            requirements_artifact_ref=str(args.requirements_artifact_ref),
        )
        _emit(status, args=args)
        reason_code = str(row.get("reason_code") or "")
        if reason_code == "model_group_replay_option_features_already_ready":
            _emit(
                {
                    "event": "completed",
                    "reason": "all_replay_option_features_ready",
                    "batch_index": batch_index,
                    REQUIREMENTS_ARTIFACT_REF_FIELD: str(args.requirements_artifact_ref),
                },
                args=args,
            )
            return 0
        if str(row.get("decision_status") or "") == "backoff":
            return 2
        if args.plan_only:
            return 0
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)


def _synthetic_replay_backoff(requirements_artifact_ref: Path) -> SchedulerDecision:
    payload = {REQUIREMENTS_ARTIFACT_REF_FIELD: str(requirements_artifact_ref)}
    reason = f"{REPLAY_OPTION_FEATURE_ACQUISITION_REQUIRED}: {json.dumps(payload, sort_keys=True)}"
    now = datetime.now(UTC).isoformat()
    return SchedulerDecision(
        contract_type=SCHEDULER_DECISION_CONTRACT_TYPE,
        now_utc=now,
        now_et=now,
        decision_status="backoff",
        reason_code=REPLAY_OPTION_FEATURE_BACKOFF_REASON,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work="model_group.replay",
        command=[],
        next_internal_stage="model_group_replay",
        execution_summary={"runner_stderr": reason},
    )


def _status_from_decision(
    row: dict[str, Any],
    *,
    batch_index: int,
    batch_size: int,
    elapsed_seconds: float,
    requirements_artifact_ref: str,
) -> dict[str, Any]:
    execution = row.get("execution_summary") or {}
    return {
        "event": "batch_complete",
        "batch_index": batch_index,
        "batch_size": batch_size,
        "elapsed_seconds": elapsed_seconds,
        REQUIREMENTS_ARTIFACT_REF_FIELD: requirements_artifact_ref,
        "decision_status": row.get("decision_status"),
        "reason_code": row.get("reason_code"),
        "provider_calls": row.get("provider_calls"),
        "batch_count": execution.get("batch_count"),
        "source_missing_count": execution.get("source_missing_count"),
        "source_ready_count": execution.get("source_ready_count"),
        "option_source_unavailable_count": execution.get("option_source_unavailable_count"),
        "resume_stage_id": execution.get("resume_stage_id"),
        "required_next_step": execution.get("required_next_step"),
        "selected_work": row.get("selected_work") or REPLAY_OPTION_FEATURE_STAGE_ID,
    }


def _emit(payload: dict[str, Any], *, args: argparse.Namespace) -> None:
    payload = dict(payload)
    payload.setdefault("contract_type", DRAIN_STATUS_CONTRACT_TYPE)
    payload["emitted_at_utc"] = datetime.now(UTC).isoformat()
    text = json.dumps(payload, sort_keys=True)
    print(text)
    sys.stdout.flush()
    if args.status_jsonl is not None:
        args.status_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.status_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    if args.latest_status_json is not None:
        args.latest_status_json.parent.mkdir(parents=True, exist_ok=True)
        args.latest_status_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

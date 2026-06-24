#!/usr/bin/env python3
"""Run replay and automatically drain emitted option-feature requirements."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from trading_manager_tasks.model_group_replay_option_features import (
    replay_option_feature_backoff_for_requirements_artifact,
    replay_option_feature_payload_from_text,
    run_model_group_replay_option_features_for_replay_backoff,
)
from trading_manager_tasks.model_group_replay_contract_paths import run_model_group_replay_contract_paths

DEFAULT_DATASET_ROOT = Path("/root/projects/trading-storage/storage/05_replay_datasets/promotion_replay_candidate_policy")
DEFAULT_RUNS_ROOT = DEFAULT_DATASET_ROOT / "replay_execution_runs"
DEFAULT_EVALUATION_RUNNER = Path("/root/projects/trading-evaluation/scripts/evaluation/run_replay_execution.py")
DEFAULT_EVALUATION_REPO_ROOT = Path("/root/projects/trading-evaluation")
DEFAULT_EXECUTION_REPO_ROOT = Path("/root/projects/trading-execution")
DEFAULT_MODEL_REPO_ROOT = Path("/root/projects/trading-model")
DEFAULT_MANAGER_SRC_ROOT = Path("/root/projects/trading-manager/src")
DEFAULT_DATABASE_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_ALPHA_MODEL_JSON = Path(
    "/root/projects/trading-storage/storage/03_model_artifacts/runtime/"
    "model_05_alpha_confidence/after_cost_alpha_model_2025-07_2025-12.json"
)
STATUS_CONTRACT_TYPE = "manager_model_group_replay_auto_option_acquisition_status"
REQUIREMENTS_ARTIFACT_REF_FIELD = "_".join(("requirements", "artifact", "ref"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--runner-path", type=Path, default=DEFAULT_EVALUATION_RUNNER)
    parser.add_argument("--evaluation-repo-root", type=Path, default=DEFAULT_EVALUATION_REPO_ROOT)
    parser.add_argument("--execution-repo-root", type=Path, default=DEFAULT_EXECUTION_REPO_ROOT)
    parser.add_argument("--model-repo-root", type=Path, default=DEFAULT_MODEL_REPO_ROOT)
    parser.add_argument("--manager-src-root", type=Path, default=DEFAULT_MANAGER_SRC_ROOT)
    parser.add_argument("--candidate-model-ref", required=True)
    parser.add_argument("--after-cost-alpha-model-json", type=Path, default=DEFAULT_ALPHA_MODEL_JSON)
    parser.add_argument("--replay-month", required=True)
    parser.add_argument("--progress-path", type=Path)
    parser.add_argument("--run-id-prefix", default="model_group_replay_auto_option")
    parser.add_argument("--exclude-crypto", action="store_true")
    parser.add_argument("--exclude-equity", action="store_true")
    parser.add_argument("--database-url")
    parser.add_argument("--database-url-file", type=Path, default=DEFAULT_DATABASE_URL_FILE)
    parser.add_argument("--batch-size", type=int, default=30)
    parser.add_argument(
        "--feature-repair-limit",
        type=int,
        help="Maximum local feature requirements to repair per drain batch. Defaults to the full emitted requirements artifact.",
    )
    parser.add_argument("--drain-batches-per-backoff", type=int, default=10)
    parser.add_argument("--max-replay-attempts", type=int, default=20)
    parser.add_argument("--max-provider-calls", type=int, default=300)
    parser.add_argument("--max-seconds", type=float, default=0.0)
    parser.add_argument("--execute-provider-acquisition", action="store_true")
    parser.add_argument("--status-jsonl", type=Path)
    parser.add_argument("--latest-status-json", type=Path)
    args = parser.parse_args(argv)

    _validate_args(parser, args)
    database_url = _database_url(args)
    started_monotonic = time.monotonic()
    provider_calls_used = 0

    for attempt in range(1, args.max_replay_attempts + 1):
        if _time_budget_expired(args, started_monotonic):
            _emit({"event": "stopped", "reason": "time_budget_exhausted", "attempt": attempt}, args=args)
            return 2

        run_id = _run_id(args.run_id_prefix, args.replay_month, attempt)
        replay_started = time.monotonic()
        replay = _run_replay(args, run_id=run_id, database_url=database_url)
        replay_elapsed = round(time.monotonic() - replay_started, 3)
        _emit(
            {
                "event": "replay_attempt_complete",
                "attempt": attempt,
                "run_id": run_id,
                "return_code": replay.returncode,
                "elapsed_seconds": replay_elapsed,
                "stdout_log": str(args.runs_root / f"{run_id}.stdout.log"),
                "stderr_log": str(args.runs_root / f"{run_id}.stderr.log"),
            },
            args=args,
        )
        if replay.returncode == 0:
            receipt = _replay_receipt(args, run_id=run_id)
            if receipt is None:
                _emit(
                    {
                        "event": "failed",
                        "reason": "replay_completed_without_receipt",
                        "attempt": attempt,
                        "run_id": run_id,
                    },
                    args=args,
                )
                return 2
            missing_contract_paths = _selected_option_path_missing_count(receipt)
            if missing_contract_paths > 0:
                decision_rows_ref = str(receipt.get("decision_rows_ref") or "").strip()
                _emit(
                    {
                        "event": "selected_contract_path_backoff_detected",
                        "attempt": attempt,
                        "run_id": run_id,
                        "missing_count": missing_contract_paths,
                        "decision_rows_ref": decision_rows_ref,
                        "required_next_step": "drain selected-contract path acquisition before accepting replay completion",
                    },
                    args=args,
                )
                if not args.execute_provider_acquisition:
                    _emit(
                        {
                            "event": "stopped",
                            "reason": "selected_contract_path_provider_required",
                            "attempt": attempt,
                            "run_id": run_id,
                            "missing_count": missing_contract_paths,
                        },
                        args=args,
                    )
                    return 2
                if not decision_rows_ref:
                    _emit(
                        {
                            "event": "failed",
                            "reason": "selected_contract_path_missing_decision_rows_ref",
                            "attempt": attempt,
                            "run_id": run_id,
                        },
                        args=args,
                    )
                    return 2
                if _provider_budget_exhausted(args, provider_calls_used):
                    _emit_provider_budget_exhausted(args=args, attempt=attempt, provider_calls_used=provider_calls_used)
                    return 2
                remaining_provider_budget = (
                    args.max_provider_calls - provider_calls_used
                    if args.max_provider_calls > 0
                    else args.batch_size
                )
                batch_size = min(args.batch_size, max(1, remaining_provider_budget))
                path_started = time.monotonic()
                path_decision = run_model_group_replay_contract_paths(
                    decision_rows_ref=Path(decision_rows_ref),
                    execute=True,
                    execute_provider_acquisition=True,
                    limit=batch_size,
                )
                path_elapsed = round(time.monotonic() - path_started, 3)
                provider_calls_used += path_decision.provider_calls
                path_row = path_decision.summary_row()
                path_summary = (
                    path_row.get("execution_summary")
                    if isinstance(path_row.get("execution_summary"), dict)
                    else {}
                )
                _emit(
                    {
                        "event": "selected_contract_path_batch_complete",
                        "attempt": attempt,
                        "run_id": run_id,
                        "elapsed_seconds": path_elapsed,
                        "decision_status": path_row.get("decision_status"),
                        "reason_code": path_row.get("reason_code"),
                        "provider_calls": path_row.get("provider_calls"),
                        "provider_calls_used": provider_calls_used,
                        "selected_contract_requirement_count": path_summary.get("selected_contract_requirement_count"),
                        "selected_contract_symbol_count": path_summary.get("selected_contract_symbol_count"),
                        "task_key_path": path_summary.get("task_key_path"),
                    },
                    args=args,
                )
                if path_row.get("decision_status") != "executed":
                    return 2
                continue
            _emit(
                {
                    "event": "completed",
                    "reason": "replay_completed",
                    "attempt": attempt,
                    "run_id": run_id,
                    "provider_calls_used": provider_calls_used,
                },
                args=args,
            )
            return 0

        payload = replay_option_feature_payload_from_text(replay.stderr)
        if not payload:
            _emit(
                {
                    "event": "failed",
                    "reason": "replay_failed_without_option_feature_backoff",
                    "attempt": attempt,
                    "run_id": run_id,
                    "return_code": replay.returncode,
                },
                args=args,
            )
            return replay.returncode or 1

        artifact_ref = str(payload.get(REQUIREMENTS_ARTIFACT_REF_FIELD) or "").strip()
        if not artifact_ref:
            _emit({"event": "failed", "reason": "option_backoff_missing_requirements_artifact_ref", "attempt": attempt}, args=args)
            return 2
        artifact = Path(artifact_ref)
        missing_count = payload.get("missing_count")
        _emit(
            {
                "event": "option_feature_backoff_detected",
                "attempt": attempt,
                "run_id": run_id,
                "missing_count": missing_count,
                REQUIREMENTS_ARTIFACT_REF_FIELD: str(artifact),
                "required_next_step": payload.get("required_next_step"),
            },
            args=args,
        )

        for drain_batch in range(1, args.drain_batches_per_backoff + 1):
            if _time_budget_expired(args, started_monotonic):
                _emit({"event": "stopped", "reason": "time_budget_exhausted", "attempt": attempt}, args=args)
                return 2
            if _provider_budget_exhausted(args, provider_calls_used):
                _emit_provider_budget_exhausted(args=args, attempt=attempt, provider_calls_used=provider_calls_used)
                return 2
            remaining_provider_budget = args.max_provider_calls - provider_calls_used if args.max_provider_calls > 0 else args.batch_size
            batch_size = min(args.batch_size, max(1, remaining_provider_budget))
            drain_started = time.monotonic()
            decision = run_model_group_replay_option_features_for_replay_backoff(
                replay_option_feature_backoff_for_requirements_artifact(artifact),
                execute=True,
                execute_provider_acquisition=args.execute_provider_acquisition,
                provider_acquisition_limit=batch_size,
                feature_repair_limit=args.feature_repair_limit,
            )
            drain_elapsed = round(time.monotonic() - drain_started, 3)
            if decision is None:
                _emit(
                    {
                        "event": "drain_stopped",
                        "reason": "no_replay_option_feature_work_ready",
                        "attempt": attempt,
                        "drain_batch": drain_batch,
                        REQUIREMENTS_ARTIFACT_REF_FIELD: str(artifact),
                    },
                    args=args,
                )
                break
            provider_calls_used += decision.provider_calls
            row = decision.summary_row()
            summary = row.get("execution_summary") if isinstance(row.get("execution_summary"), dict) else {}
            _emit(
                {
                    "event": "drain_batch_complete",
                    "attempt": attempt,
                    "drain_batch": drain_batch,
                    REQUIREMENTS_ARTIFACT_REF_FIELD: str(artifact),
                    "elapsed_seconds": drain_elapsed,
                    "decision_status": row.get("decision_status"),
                    "reason_code": row.get("reason_code"),
                    "provider_calls": row.get("provider_calls"),
                    "provider_calls_used": provider_calls_used,
                    "batch_count": summary.get("batch_count"),
                    "missing_option_feature_count": summary.get("missing_option_feature_count"),
                    "option_source_unavailable_count": summary.get("option_source_unavailable_count"),
                    "post_repair_missing_count": summary.get("post_repair_missing_count"),
                    "required_next_step": summary.get("required_next_step"),
                },
                args=args,
            )
            required_next_step = str(summary.get("required_next_step") or "").lower()
            if "continue replay option feature drain" not in required_next_step:
                if row.get("decision_status") != "executed":
                    return 2
                break
            if _provider_budget_exhausted(args, provider_calls_used):
                _emit(
                    {
                        "event": "provider_budget_reached",
                        "attempt": attempt,
                        "provider_calls_used": provider_calls_used,
                        "max_provider_calls": args.max_provider_calls,
                    },
                    args=args,
                )
                break

    _emit({"event": "stopped", "reason": "max_replay_attempts_reached"}, args=args)
    return 2


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.feature_repair_limit is not None and args.feature_repair_limit <= 0:
        parser.error("--feature-repair-limit must be positive")
    if args.drain_batches_per_backoff <= 0:
        parser.error("--drain-batches-per-backoff must be positive")
    if args.max_replay_attempts <= 0:
        parser.error("--max-replay-attempts must be positive")
    if args.max_provider_calls < 0:
        parser.error("--max-provider-calls must be non-negative")
    if not args.after_cost_alpha_model_json.exists():
        parser.error(f"--after-cost-alpha-model-json does not exist: {args.after_cost_alpha_model_json}")


def _database_url(args: argparse.Namespace) -> str | None:
    if args.database_url:
        return str(args.database_url)
    if args.database_url_file and args.database_url_file.exists():
        return args.database_url_file.read_text(encoding="utf-8").strip()
    return os.environ.get("OPENCLAW_DATABASE_URL")


def _time_budget_expired(args: argparse.Namespace, started_monotonic: float) -> bool:
    if args.max_seconds > 0 and time.monotonic() - started_monotonic >= args.max_seconds:
        return True
    return False


def _provider_budget_exhausted(args: argparse.Namespace, provider_calls_used: int) -> bool:
    return args.max_provider_calls > 0 and provider_calls_used >= args.max_provider_calls


def _emit_provider_budget_exhausted(
    *,
    args: argparse.Namespace,
    attempt: int,
    provider_calls_used: int,
) -> None:
    _emit(
        {
            "event": "provider_budget_reached",
            "attempt": attempt,
            "provider_calls_used": provider_calls_used,
            "max_provider_calls": args.max_provider_calls,
        },
        args=args,
    )
    _emit(
        {
            "event": "stopped",
            "reason": "provider_budget_exhausted",
            "attempt": attempt,
            "provider_calls_used": provider_calls_used,
            "max_provider_calls": args.max_provider_calls,
        },
        args=args,
    )


def _run_replay(args: argparse.Namespace, *, run_id: str, database_url: str | None) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(args.runner_path),
        "--dataset-root",
        str(args.dataset_root),
        "--run-id",
        run_id,
        "--candidate-model-ref",
        args.candidate_model_ref,
        "--after-cost-alpha-model-json",
        str(args.after_cost_alpha_model_json),
        "--replay-month",
        args.replay_month,
    ]
    if args.progress_path is not None:
        command.extend(["--progress-path", str(args.progress_path)])
    if args.exclude_crypto:
        command.append("--exclude-crypto")
    if args.exclude_equity:
        command.append("--exclude-equity")
    if database_url:
        command.extend(["--option-feature-database-url", database_url, "--candidate-handoff-database-url", database_url])

    args.runs_root.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(args.evaluation_repo_root / "src"),
            str(args.execution_repo_root / "src"),
            str(args.model_repo_root / "src"),
            str(args.manager_src_root),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)
    completed = subprocess.run(command, cwd=args.evaluation_repo_root, env=env, capture_output=True, text=True, check=False)
    (args.runs_root / f"{run_id}.stdout.log").write_text(completed.stdout or "", encoding="utf-8")
    (args.runs_root / f"{run_id}.stderr.log").write_text(completed.stderr or "", encoding="utf-8")
    return completed


def _replay_receipt(args: argparse.Namespace, *, run_id: str) -> dict[str, Any] | None:
    receipt_path = args.runs_root / run_id / "replay_execution_receipt.json"
    if not receipt_path.exists():
        return None
    return json.loads(receipt_path.read_text(encoding="utf-8"))


def _selected_option_path_missing_count(receipt: dict[str, Any]) -> int:
    coverage = receipt.get("option_replay_coverage")
    if not isinstance(coverage, dict):
        return 0
    try:
        return int(coverage.get("selected_option_path_missing_count") or 0)
    except (TypeError, ValueError):
        return 0


def _run_id(prefix: str, replay_month: str, attempt: int) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{timestamp}_{replay_month.replace('-', '_')}_attempt_{attempt:02d}"


def _emit(payload: dict[str, Any], *, args: argparse.Namespace) -> None:
    row = dict(payload)
    row.setdefault("contract_type", STATUS_CONTRACT_TYPE)
    row.setdefault("emitted_at_utc", datetime.now(UTC).isoformat())
    text = json.dumps(row, sort_keys=True)
    print(text)
    sys.stdout.flush()
    if args.status_jsonl is not None:
        args.status_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with args.status_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    if args.latest_status_json is not None:
        args.latest_status_json.parent.mkdir(parents=True, exist_ok=True)
        args.latest_status_json.write_text(json.dumps(row, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

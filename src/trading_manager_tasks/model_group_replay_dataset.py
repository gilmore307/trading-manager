"""Manager admission for replay dataset preparation and freeze.

The dataset implementation lives in ``trading-evaluation``. Manager owns the
historical lifecycle admission: once a pre-replay model fold is complete, it can
prepare the fold-bound base context, prepare the storage dataset bundle, run
bounded one-shot acquisition when provider acquisition is enabled, and freeze
the local replay dataset before replay execution.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from .model_group_replay import (
    DEFAULT_EVALUATION_REPO_ROOT,
    DEFAULT_PYTHON_EXECUTABLE,
    DEFAULT_REPLAY_CONTRACT_ID,
    _candidate_universe_symbols,
    _canonical_alpaca_source_symbols,
    _completed_training_fold,
    _csv_rows,
    _dataset_is_frozen_and_complete,
    _historical_candidate_universe_path,
    _load_json_object,
    _replay_dataset_root,
    _replay_dataset_scope_status,
)
from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import scheduler_lock_plan

DEFAULT_REPLAY_CONTRACT_PATH = DEFAULT_EVALUATION_REPO_ROOT / "replays" / "promotion_replay_candidate_policy.json"
DEFAULT_PREPARE_RUNNER_PATH = DEFAULT_EVALUATION_REPO_ROOT / "scripts" / "evaluation" / "prepare_replay_dataset.py"
DEFAULT_FREEZE_RUNNER_PATH = DEFAULT_EVALUATION_REPO_ROOT / "scripts" / "evaluation" / "freeze_replay_dataset.py"
DEFAULT_ACQUISITION_RUNNER_PATH = DEFAULT_EVALUATION_REPO_ROOT / "scripts" / "evaluation" / "run_replay_acquisition.py"
DEFAULT_SOURCE_DATA_ROOT = Path("/root/projects/trading-storage/storage/01_source_data")
DEFAULT_TRADING_DATA_REPO_ROOT = Path("/root/projects/trading-data")
NEW_YORK = ZoneInfo("America/New_York")


def run_model_group_replay_dataset_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    execute_provider_acquisition: bool = False,
    provider_acquisition_limit: int | None = 1,
    python_executable: str | None = None,
    evaluation_repo_root: Path = DEFAULT_EVALUATION_REPO_ROOT,
    trading_data_repo_root: Path = DEFAULT_TRADING_DATA_REPO_ROOT,
    contract_path: Path = DEFAULT_REPLAY_CONTRACT_PATH,
    prepare_runner_path: Path = DEFAULT_PREPARE_RUNNER_PATH,
    freeze_runner_path: Path = DEFAULT_FREEZE_RUNNER_PATH,
    acquisition_runner_path: Path = DEFAULT_ACQUISITION_RUNNER_PATH,
    source_data_root: Path = DEFAULT_SOURCE_DATA_ROOT,
    candidate_universe_path: Path | None = None,
    selected_target_symbol: str | None = None,
    now_utc: datetime | None = None,
) -> SchedulerDecision | None:
    """Prepare, acquire, or freeze the replay dataset for the next fold."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    manifest_path = dataset_root / "dataset_manifest.json"
    freeze_receipt_path = dataset_root / "replay_freeze_receipt.json"
    training_fold = _completed_training_fold(storage_root=storage_root, selected_target_symbol=selected_target_symbol)
    if training_fold is None:
        return None

    manifest = _load_json_object(manifest_path) if manifest_path.exists() else None
    freeze_receipt = _load_json_object(freeze_receipt_path) if freeze_receipt_path.exists() else None
    stale_dataset_scope = False
    stale_manifest = None
    stale_freeze_receipt = None
    fixed_candidate_coverage_gap = _fixed_candidate_bar_coverage_gap(
        storage_root=storage_root,
        dataset_root=dataset_root,
        candidate_universe_path=candidate_universe_path,
    )
    if manifest is not None and freeze_receipt is not None and _dataset_is_frozen_and_complete(manifest, freeze_receipt):
        replay_scope_status = _replay_dataset_scope_status(dataset_root=dataset_root, manifest=manifest, training_fold=training_fold)
        if replay_scope_status["compatible"] and fixed_candidate_coverage_gap is None:
            return None
        stale_dataset_scope = True
        stale_manifest = manifest
        stale_freeze_receipt = freeze_receipt

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    resolved_python = python_executable or _python_executable()
    contract = _load_json_object(contract_path)
    base_context_path = _base_context_path(contract=contract, dataset_root=dataset_root)
    base_context_written = False
    if stale_dataset_scope or not base_context_path.exists():
        if not execute:
            return _decision(
                now=now,
                decision_status="ready",
                reason_code="model_group_replay_dataset_base_context_ready",
                reason="model-group replay base context is ready to be written",
                selected_work="model_group.replay_dataset",
                command=[],
                provider_calls=0,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=False,
                ),
            )
        _write_base_context(base_context_path, contract=contract, training_fold=training_fold, now=now)
        base_context_written = True

    replaced_stale_dataset = False
    if stale_dataset_scope or not manifest_path.exists():
        command = [
            resolved_python,
            str(prepare_runner_path),
            "--contract",
            str(contract_path),
            "--candidate-fold-id",
            str(training_fold["fold_id"]),
            "--base-context-ref",
            str(base_context_path),
            "--output-root",
            str(dataset_root.parent),
            "--data-root",
            str(source_data_root),
        ]
        if not execute:
            return _decision(
                now=now,
                decision_status="ready",
                reason_code="model_group_replay_dataset_preparation_ready",
                reason="model-group replay dataset is ready for preparation",
                selected_work="model_group.replay_dataset",
                command=command,
                provider_calls=0,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=base_context_written,
                    stale_dataset_scope=stale_dataset_scope,
                    previous_manifest=stale_manifest,
                    previous_freeze_receipt=stale_freeze_receipt,
                ),
            )
        completed = _run(command, cwd=evaluation_repo_root, pythonpath=[evaluation_repo_root / "src"])
        if completed.returncode != 0:
            return _subprocess_backoff(
                now=now,
                reason_code="model_group_replay_dataset_preparation_failed",
                reason="model-group replay dataset preparation failed",
                selected_work="model_group.replay_dataset",
                command=command,
                completed=completed,
                provider_calls=0,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=base_context_written,
                    stale_dataset_scope=stale_dataset_scope,
                    previous_manifest=stale_manifest,
                    previous_freeze_receipt=stale_freeze_receipt,
                ),
            )
        manifest = _load_json_object(manifest_path)
        replaced_stale_dataset = stale_dataset_scope
    else:
        manifest = _load_json_object(manifest_path)

    missing_count = _int_value(manifest.get("missing_feed_acquisition_count"))
    if missing_count > 0:
        acquisition_limit = provider_acquisition_limit if provider_acquisition_limit is not None else missing_count
        command = [
            resolved_python,
            str(acquisition_runner_path),
            "--dataset-root",
            str(dataset_root),
            "--data-root",
            str(trading_data_repo_root),
            "--run-id",
            "model_group_replay_dataset_acquisition_" + now.strftime("%Y%m%dT%H%M%SZ"),
            "--limit",
            str(max(1, acquisition_limit)),
            "--stop-on-failure",
        ]
        if fixed_candidate_coverage_gap is not None:
            command.extend(
                [
                    "--include-fixed-candidate-alpaca-bars",
                    "--candidate-universe-path",
                    str(fixed_candidate_coverage_gap["candidate_universe_path"]),
                    "--storage-source-root",
                    str(source_data_root),
                ]
            )
        if execute_provider_acquisition:
            command.append("--execute")
        if not execute or not execute_provider_acquisition:
            return _decision(
                now=now,
                decision_status="backoff",
                reason_code="model_group_replay_dataset_acquisition_required",
                reason="replay dataset has missing local coverage and requires one-shot provider acquisition",
                selected_work="model_group.replay_dataset_acquisition",
                command=command,
                provider_calls=0,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=base_context_written,
                    manifest=manifest,
                    missing_feed_acquisition_count=missing_count,
                    fixed_candidate_coverage_gap=fixed_candidate_coverage_gap,
                    required_next_step="enable autonomous replay dataset provider acquisition or run the acquisition command, then retry dataset freeze",
                ),
            )
        completed = _run(
            command,
            cwd=evaluation_repo_root,
            pythonpath=[evaluation_repo_root / "src"],
        )
        if completed.returncode != 0:
            return _subprocess_backoff(
                now=now,
                reason_code="model_group_replay_dataset_acquisition_failed",
                reason="one-shot replay dataset provider acquisition failed",
                selected_work="model_group.replay_dataset_acquisition",
                command=command,
                completed=completed,
                provider_calls=1,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=base_context_written,
                    manifest=manifest,
                    missing_feed_acquisition_count=missing_count,
                    fixed_candidate_coverage_gap=fixed_candidate_coverage_gap,
                    provider_calls_performed=True,
                ),
            )
        refreshed = _refresh_preparation(
            resolved_python=resolved_python,
            prepare_runner_path=prepare_runner_path,
            contract_path=contract_path,
            base_context_path=base_context_path,
            dataset_root=dataset_root,
            source_data_root=source_data_root,
            evaluation_repo_root=evaluation_repo_root,
            training_fold=training_fold,
        )
        refreshed_manifest = _load_json_object(manifest_path) if manifest_path.exists() else manifest
        return _decision(
            now=now,
            decision_status="executed",
            reason_code="model_group_replay_dataset_acquisition_executed",
            reason="executed one-shot replay dataset acquisition and refreshed preparation coverage",
            selected_work="model_group.replay_dataset_acquisition",
            command=command,
            provider_calls=1,
            execution_summary=_summary(
                contract_id=contract_id,
                dataset_root=dataset_root,
                training_fold=training_fold,
                base_context_path=base_context_path,
                base_context_written=base_context_written,
                manifest=refreshed_manifest,
                fixed_candidate_coverage_gap=fixed_candidate_coverage_gap,
                acquisition_stdout=completed.stdout,
                acquisition_stderr=completed.stderr,
                refreshed_preparation_return_code=refreshed.returncode,
                provider_calls_performed=True,
            ),
        )

    if fixed_candidate_coverage_gap is not None:
        missing_count = _fixed_candidate_missing_acquisition_count(fixed_candidate_coverage_gap)
        acquisition_limit = provider_acquisition_limit if provider_acquisition_limit is not None else missing_count
        command = [
            resolved_python,
            str(acquisition_runner_path),
            "--dataset-root",
            str(dataset_root),
            "--data-root",
            str(trading_data_repo_root),
            "--run-id",
            "model_group_replay_dataset_acquisition_" + now.strftime("%Y%m%dT%H%M%SZ"),
            "--include-fixed-candidate-alpaca-bars",
            "--candidate-universe-path",
            str(fixed_candidate_coverage_gap["candidate_universe_path"]),
            "--storage-source-root",
            str(source_data_root),
            "--limit",
            str(max(1, acquisition_limit)),
            "--stop-on-failure",
        ]
        if execute_provider_acquisition:
            command.append("--execute")
        if not execute or not execute_provider_acquisition:
            return _decision(
                now=now,
                decision_status="backoff",
                reason_code="model_group_replay_dataset_acquisition_required",
                reason="fixed historical candidate universe has missing Alpaca bar coverage for replay",
                selected_work="model_group.replay_dataset_acquisition",
                command=command,
                provider_calls=0,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=base_context_written,
                    manifest=manifest,
                    fixed_candidate_coverage_gap=fixed_candidate_coverage_gap,
                    missing_feed_acquisition_count=missing_count,
                    required_next_step="run the gated replay candidate Alpaca bars acquisition for the fixed historical candidate universe before dataset freeze",
                ),
            )
        completed = _run(
            command,
            cwd=evaluation_repo_root,
            pythonpath=[evaluation_repo_root / "src"],
        )
        if completed.returncode != 0:
            return _subprocess_backoff(
                now=now,
                reason_code="model_group_replay_dataset_acquisition_failed",
                reason="fixed-candidate replay dataset Alpaca bar acquisition failed",
                selected_work="model_group.replay_dataset_acquisition",
                command=command,
                completed=completed,
                provider_calls=1,
                execution_summary=_summary(
                    contract_id=contract_id,
                    dataset_root=dataset_root,
                    training_fold=training_fold,
                    base_context_path=base_context_path,
                    base_context_written=base_context_written,
                    manifest=manifest,
                    fixed_candidate_coverage_gap=fixed_candidate_coverage_gap,
                    missing_feed_acquisition_count=missing_count,
                    provider_calls_performed=True,
                ),
            )
        refreshed = _refresh_preparation(
            resolved_python=resolved_python,
            prepare_runner_path=prepare_runner_path,
            contract_path=contract_path,
            base_context_path=base_context_path,
            dataset_root=dataset_root,
            source_data_root=source_data_root,
            evaluation_repo_root=evaluation_repo_root,
            training_fold=training_fold,
        )
        refreshed_manifest = _load_json_object(manifest_path) if manifest_path.exists() else manifest
        return _decision(
            now=now,
            decision_status="executed",
            reason_code="model_group_replay_dataset_acquisition_executed",
            reason="executed fixed-candidate replay dataset Alpaca bar acquisition and refreshed preparation coverage",
            selected_work="model_group.replay_dataset_acquisition",
            command=command,
            provider_calls=1,
            execution_summary=_summary(
                contract_id=contract_id,
                dataset_root=dataset_root,
                training_fold=training_fold,
                base_context_path=base_context_path,
                base_context_written=base_context_written,
                manifest=refreshed_manifest,
                fixed_candidate_coverage_gap=fixed_candidate_coverage_gap,
                acquisition_stdout=completed.stdout,
                acquisition_stderr=completed.stderr,
                refreshed_preparation_return_code=refreshed.returncode,
                provider_calls_performed=True,
            ),
        )

    if freeze_receipt_path.exists() and not replaced_stale_dataset:
        freeze_receipt = _load_json_object(freeze_receipt_path)
        if _dataset_is_frozen_and_complete(manifest, freeze_receipt):
            return None

    command = [
        resolved_python,
        str(freeze_runner_path),
        "--dataset-root",
        str(dataset_root),
    ]
    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_replay_dataset_freeze_ready",
            reason="model-group replay dataset is ready to freeze",
            selected_work="model_group.replay_dataset",
            command=command,
            provider_calls=0,
            execution_summary=_summary(
                contract_id=contract_id,
                dataset_root=dataset_root,
                training_fold=training_fold,
                base_context_path=base_context_path,
                base_context_written=base_context_written,
                manifest=manifest,
            ),
        )
    completed = _run(command, cwd=evaluation_repo_root, pythonpath=[evaluation_repo_root / "src"])
    if completed.returncode != 0:
        return _subprocess_backoff(
            now=now,
            reason_code="model_group_replay_dataset_freeze_failed",
            reason="model-group replay dataset freeze failed",
            selected_work="model_group.replay_dataset",
            command=command,
            completed=completed,
            provider_calls=0,
            execution_summary=_summary(
                contract_id=contract_id,
                dataset_root=dataset_root,
                training_fold=training_fold,
                base_context_path=base_context_path,
                base_context_written=base_context_written,
                manifest=manifest,
            ),
        )
    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_replay_dataset_frozen",
        reason="prepared and froze model-group replay dataset",
        selected_work="model_group.replay_dataset",
        command=command,
        provider_calls=0,
        execution_summary=_summary(
            contract_id=contract_id,
            dataset_root=dataset_root,
            training_fold=training_fold,
            base_context_path=base_context_path,
            base_context_written=base_context_written,
            manifest=_load_json_object(manifest_path),
            freeze_receipt=_load_json_object(freeze_receipt_path),
            stale_dataset_scope=stale_dataset_scope,
            previous_manifest=stale_manifest,
            previous_freeze_receipt=stale_freeze_receipt,
        ),
    )


def _refresh_preparation(
    *,
    resolved_python: str,
    prepare_runner_path: Path,
    contract_path: Path,
    base_context_path: Path,
    dataset_root: Path,
    source_data_root: Path,
    evaluation_repo_root: Path,
    training_fold: Mapping[str, Any],
) -> subprocess.CompletedProcess[str]:
    command = [
        resolved_python,
        str(prepare_runner_path),
        "--contract",
        str(contract_path),
        "--candidate-fold-id",
        str(training_fold["fold_id"]),
        "--base-context-ref",
        str(base_context_path),
        "--output-root",
        str(dataset_root.parent),
        "--data-root",
        str(source_data_root),
    ]
    return _run(command, cwd=evaluation_repo_root, pythonpath=[evaluation_repo_root / "src"])


def _decision(
    *,
    now: datetime,
    decision_status: str,
    reason_code: str,
    reason: str,
    selected_work: str,
    command: list[str],
    provider_calls: int,
    execution_summary: dict[str, Any],
) -> SchedulerDecision:
    now_et = now.astimezone(NEW_YORK).isoformat()
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now_et,
        decision_status=decision_status,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=command,
        next_internal_stage="model_group_replay_dataset",
        provider_calls=provider_calls,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(
            month=None,
            selected_work=selected_work,
            next_internal_stage="model_group_replay_dataset",
        ),
    )


def _subprocess_backoff(
    *,
    now: datetime,
    reason_code: str,
    reason: str,
    selected_work: str,
    command: list[str],
    completed: subprocess.CompletedProcess[str],
    provider_calls: int,
    execution_summary: dict[str, Any],
) -> SchedulerDecision:
    enriched = dict(execution_summary)
    enriched.update(
        {
            "runner_returncode": completed.returncode,
            "runner_stdout": completed.stdout,
            "runner_stderr": completed.stderr,
        }
    )
    return _decision(
        now=now,
        decision_status="backoff",
        reason_code=reason_code,
        reason=(completed.stderr or completed.stdout or reason).strip(),
        selected_work=selected_work,
        command=command,
        provider_calls=provider_calls,
        execution_summary=enriched,
    )


def _summary(
    *,
    contract_id: str,
    dataset_root: Path,
    training_fold: Mapping[str, Any],
    base_context_path: Path,
    base_context_written: bool,
    manifest: Mapping[str, Any] | None = None,
    freeze_receipt: Mapping[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    summary = {
        "contract_id": contract_id,
        "dataset_root": str(dataset_root),
        "training_fold": dict(training_fold),
        "base_context_path": str(base_context_path),
        "base_context_written": base_context_written,
        "provider_calls_performed": False,
        "sql_mutation_performed": False,
        "model_training_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "account_mutation_performed": False,
    }
    if manifest is not None:
        summary["manifest"] = dict(manifest)
    if freeze_receipt is not None:
        summary["freeze_receipt"] = dict(freeze_receipt)
    summary.update(extra)
    return summary


def _fixed_candidate_bar_coverage_gap(
    *,
    storage_root: Path,
    dataset_root: Path,
    candidate_universe_path: Path | None,
) -> dict[str, Any] | None:
    resolved_candidate_universe_path = candidate_universe_path or _historical_candidate_universe_path(storage_root)
    if not resolved_candidate_universe_path.exists():
        return None
    fixed_equity_universe_symbols = _candidate_universe_symbols(resolved_candidate_universe_path, asset_class="us_equity")
    replay_months = _replay_plan_months(dataset_root)
    if replay_months:
        materialized_by_month = {
            month: _canonical_alpaca_source_symbols(storage_root, replay_month=month)
            for month in replay_months
        }
        missing_pairs = tuple(
            (month, symbol)
            for month in replay_months
            for symbol in sorted(fixed_equity_universe_symbols - materialized_by_month[month])
        )
        if not missing_pairs:
            return None
        missing_symbols = tuple(sorted({symbol for _month, symbol in missing_pairs}))
        return {
            "candidate_universe_path": str(resolved_candidate_universe_path),
            "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
            "replay_month_count": len(replay_months),
            "materialized_equity_candidate_symbol_count": len(fixed_equity_universe_symbols) - len(missing_symbols),
            "missing_equity_candidate_symbol_count": len(missing_symbols),
            "missing_equity_candidate_symbol_month_count": len(missing_pairs),
            "missing_equity_candidate_symbols_sample": list(missing_symbols[:25]),
            "missing_equity_candidate_symbol_months_sample": [
                {"month": month, "symbol": symbol} for month, symbol in missing_pairs[:25]
            ],
        }
    materialized_equity_symbols = _canonical_alpaca_source_symbols(storage_root)
    missing_symbols = tuple(sorted(fixed_equity_universe_symbols - materialized_equity_symbols))
    if not missing_symbols:
        return None
    return {
        "candidate_universe_path": str(resolved_candidate_universe_path),
        "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
        "materialized_equity_candidate_symbol_count": len(materialized_equity_symbols & fixed_equity_universe_symbols),
        "missing_equity_candidate_symbol_count": len(missing_symbols),
        "missing_equity_candidate_symbols_sample": list(missing_symbols[:25]),
    }


def _fixed_candidate_missing_acquisition_count(fixed_candidate_coverage_gap: Mapping[str, Any]) -> int:
    return max(
        0,
        _int_value(
            fixed_candidate_coverage_gap.get("missing_equity_candidate_symbol_month_count")
            or fixed_candidate_coverage_gap.get("missing_equity_candidate_symbol_count")
        ),
    )


def _replay_plan_months(dataset_root: Path) -> tuple[str, ...]:
    months: set[str] = set()
    for row in _csv_rows(dataset_root / "feed_acquisition_plan.csv"):
        month = str(row.get("month") or "").strip()
        if len(month) == 7 and month[4] == "-":
            months.add(month)
    return tuple(sorted(months))


def _base_context_path(*, contract: Mapping[str, Any], dataset_root: Path) -> Path:
    raw = str(contract.get("base_context_ref") or "").strip()
    return Path(raw) if raw else dataset_root / "base_context.json"


def _write_base_context(
    path: Path,
    *,
    contract: Mapping[str, Any],
    training_fold: Mapping[str, Any],
    now: datetime,
) -> None:
    target_symbol = str(training_fold.get("target_symbol") or "").strip().upper()
    if not target_symbol:
        target_symbol = "AAPL"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "contract_type": "replay_base_context",
        "created_at_utc": now.isoformat(),
        "candidate_fold_id": training_fold.get("fold_id"),
        "source_fold_state_path": training_fold.get("state_path"),
        "base_context_policy_ref": contract.get("base_context_policy_ref"),
        "pre_replay_target_refs": [target_symbol],
        "safety": {
            "provider_calls_performed": False,
            "sql_mutation_performed": False,
            "model_training_performed": False,
            "model_activation_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run(command: Sequence[str], *, cwd: Path, pythonpath: Sequence[Path] = ()) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    parts = [str(path) for path in pythonpath]
    existing = env.get("PYTHONPATH")
    if existing:
        parts.append(existing)
    if parts:
        env["PYTHONPATH"] = os.pathsep.join(parts)
    return subprocess.run(list(command), cwd=cwd, env=env, capture_output=True, text=True)


def _python_executable() -> str:
    if DEFAULT_PYTHON_EXECUTABLE.exists():
        return str(DEFAULT_PYTHON_EXECUTABLE)
    return sys.executable


def _int_value(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = ["run_model_group_replay_dataset_if_ready"]

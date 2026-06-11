"""Manager-owned dispatch for model-group replay execution.

The replay itself lives in ``trading-evaluation``. Manager owns admission:
only a completed model-training fold and a frozen replay dataset may trigger
the side-effect-free evaluation runner.
"""

from __future__ import annotations

import csv
import json
import math
import os
import re
import subprocess
import sys
from datetime import UTC, datetime, time
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from .request_payloads import DEFAULT_STORAGE_ROOT
from .scheduler import SchedulerDecision
from .scheduler_locks import SchedulerLockRef, acquire_scheduler_lock, scheduler_lock_plan
from .storage_paths import projects_root
from .model_training_workflow import base_stack_model_generation_splits_complete

DEFAULT_REPLAY_CONTRACT_ID = "promotion_replay_candidate_policy"
DEFAULT_EVALUATION_REPO_ROOT = projects_root() / "trading-evaluation"
DEFAULT_EXECUTION_REPO_ROOT = projects_root() / "trading-execution"
DEFAULT_MODEL_REPO_ROOT = projects_root() / "trading-model"
DEFAULT_EVALUATION_RUNNER_PATH = DEFAULT_EVALUATION_REPO_ROOT / "scripts" / "evaluation" / "run_replay_execution.py"
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_PYTHON_EXECUTABLE = projects_root() / "trading-manager" / ".venv" / "bin" / "python"
DEFAULT_REPLAY_INITIAL_CAPITAL_USD = 25_000.0
REPLAY_OPTION_FEATURE_ACQUISITION_REQUIRED = "replay_option_feature_acquisition_required"
NEW_YORK = ZoneInfo("America/New_York")
CRYPTO_REPLAY_TARGET_REFS = {"BTC", "ETH", "SOL"}
CANDIDATE_UNIVERSE_SOURCE_POLICY = "fixed_current_snapshot_historical_candidate_universe"
REPLAY_CANDIDATE_UNIVERSE_CLOSE_READY_TIME = time(16, 15)


def run_model_group_replay_if_ready(
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    contract_id: str = DEFAULT_REPLAY_CONTRACT_ID,
    execute: bool = True,
    python_executable: str | None = None,
    evaluation_repo_root: Path = DEFAULT_EVALUATION_REPO_ROOT,
    execution_repo_root: Path = DEFAULT_EXECUTION_REPO_ROOT,
    model_repo_root: Path = DEFAULT_MODEL_REPO_ROOT,
    runner_path: Path = DEFAULT_EVALUATION_RUNNER_PATH,
    selected_target_symbol: str | None = None,
    candidate_universe_path: Path | None = None,
    max_decision_rows: int | None = None,
    initial_capital_usd: float = DEFAULT_REPLAY_INITIAL_CAPITAL_USD,
    now_utc: datetime | None = None,
) -> SchedulerDecision | None:
    """Run one model-group replay dispatch when the accepted prerequisites hold."""

    dataset_root = _replay_dataset_root(storage_root, contract_id)
    manifest_path = dataset_root / "dataset_manifest.json"
    freeze_receipt_path = dataset_root / "replay_freeze_receipt.json"
    if not dataset_root.exists() or not manifest_path.exists() or not freeze_receipt_path.exists():
        return None

    manifest = _load_json_object(manifest_path)
    freeze_receipt = _load_json_object(freeze_receipt_path)
    if not _dataset_is_frozen_and_complete(manifest, freeze_receipt):
        return None

    training_fold = _completed_training_fold(storage_root=storage_root, selected_target_symbol=selected_target_symbol)
    if training_fold is None:
        return None

    scope_status = _replay_dataset_scope_status(dataset_root=dataset_root, manifest=manifest, training_fold=training_fold)
    if not scope_status["compatible"]:
        now = (now_utc or datetime.now(UTC)).astimezone(UTC)
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_scope_mismatch",
            reason=str(scope_status["reason"]),
            selected_work="model_group.replay",
            command=[],
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "replay_scope_status": scope_status,
            },
        )

    compatible_run_ids = _compatible_replay_run_ids(dataset_root=dataset_root, training_fold=training_fold)
    expected_months = _expected_replay_months(dataset_root)
    ready_months = _ready_replay_months(dataset_root, replay_run_ids=compatible_run_ids) if compatible_run_ids else set()
    if expected_months > 0 and len(ready_months) >= expected_months:
        return None

    now = (now_utc or datetime.now(UTC)).astimezone(UTC)
    run_id = "model_group_replay_" + now.strftime("%Y%m%dT%H%M%SZ")
    progress_path = dataset_root / "replay_progress.jsonl"
    candidate_model_ref = str(training_fold.get("candidate_model_ref") or "")
    option_feature_database_url = _database_url()
    resolved_python = python_executable or _python_executable()
    after_cost_alpha_model_path = _after_cost_alpha_model_path(storage_root=storage_root, training_fold=training_fold)
    if not after_cost_alpha_model_path.exists():
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_after_cost_alpha_model_missing",
            reason="fold-scoped after-cost alpha model artifact is required for replay Layer 5 inference",
            selected_work="model_group.replay",
            command=[],
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "after_cost_alpha_model_ref": str(after_cost_alpha_model_path),
                "required_next_step": "train or restore the fold-scoped after-cost alpha model artifact before replay",
            },
        )
    replay_plan_equity_symbols = _replay_dataset_available_equity_symbols(dataset_root)
    resolved_candidate_universe_path = candidate_universe_path or _historical_candidate_universe_path(storage_root)
    fixed_candidate_universe_symbols = _fixed_historical_candidate_symbols(resolved_candidate_universe_path)
    fixed_equity_universe_symbols = _fixed_historical_candidate_symbols(resolved_candidate_universe_path, asset_class="us_equity")
    initial_capital_usd = _validated_initial_capital_usd(initial_capital_usd)
    equity_pool_symbols = _replay_equity_symbols_from_fixed_universe(
        fixed_universe_symbols=fixed_equity_universe_symbols,
        replay_plan_symbols=replay_plan_equity_symbols,
    )
    command = [
        resolved_python,
        str(runner_path),
        "--dataset-root",
        str(dataset_root),
        "--run-id",
        run_id,
        "--candidate-model-ref",
        candidate_model_ref,
        "--after-cost-alpha-model-json",
        str(after_cost_alpha_model_path),
        "--progress-path",
        str(progress_path),
        "--initial-capital-usd",
        str(initial_capital_usd),
    ]
    for symbol in equity_pool_symbols:
        command.extend(["--equity-symbol", symbol])
    if max_decision_rows is not None:
        command.extend(["--max-decision-rows", str(max_decision_rows)])

    if replay_plan_equity_symbols and not equity_pool_symbols:
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_candidate_coverage_missing",
            reason=(
                "frozen replay plan has equity instruments, but none overlap the fixed historical equity candidate universe"
            ),
            selected_work="model_group.replay",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "expected_replay_months": expected_months,
                "ready_replay_months": len(ready_months),
                "option_feature_database_configured": bool(option_feature_database_url),
                "after_cost_alpha_model_ref": str(after_cost_alpha_model_path),
                "replay_plan_equity_symbol_count": len(replay_plan_equity_symbols),
                "candidate_universe_path": str(resolved_candidate_universe_path),
                "fixed_candidate_universe_symbol_count": len(fixed_candidate_universe_symbols),
                "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
                "equity_symbol_pool_symbol_count": len(equity_pool_symbols),
                "initial_capital_usd": initial_capital_usd,
                "candidate_universe_source_policy": CANDIDATE_UNIVERSE_SOURCE_POLICY,
                "required_next_step": "refresh the frozen replay dataset with Alpaca bars for the fixed historical equity candidate universe before fold replay",
            },
        )

    if not execute:
        return _decision(
            now=now,
            decision_status="ready",
            reason_code="model_group_replay_ready",
            reason="model-group replay is ready; rerun with replay execution enabled to dispatch evaluation runner",
            selected_work="model_group.replay",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "expected_replay_months": expected_months,
                "ready_replay_months": len(ready_months),
                "option_feature_database_configured": bool(option_feature_database_url),
                "after_cost_alpha_model_ref": str(after_cost_alpha_model_path),
                "candidate_universe_path": str(resolved_candidate_universe_path),
                "fixed_candidate_universe_symbol_count": len(fixed_candidate_universe_symbols),
                "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
                "equity_symbol_pool_symbol_count": len(equity_pool_symbols),
                "initial_capital_usd": initial_capital_usd,
                "candidate_universe_source_policy": CANDIDATE_UNIVERSE_SOURCE_POLICY,
            },
        )

    candidate_universe_close_status = _candidate_universe_close_status(
        resolved_candidate_universe_path,
        now=now,
    )
    if not candidate_universe_close_status["ready_for_replay"]:
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_candidate_universe_intraday_pending_close",
            reason="fixed candidate universe was frozen during the current market day before the accepted post-close readiness time",
            selected_work="model_group.replay",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "expected_replay_months": expected_months,
                "ready_replay_months": len(ready_months),
                "candidate_universe_path": str(resolved_candidate_universe_path),
                "candidate_universe_close_status": candidate_universe_close_status,
                "fixed_candidate_universe_symbol_count": len(fixed_candidate_universe_symbols),
                "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
                "equity_symbol_pool_symbol_count": len(equity_pool_symbols),
                "initial_capital_usd": initial_capital_usd,
                "candidate_universe_source_policy": CANDIDATE_UNIVERSE_SOURCE_POLICY,
                "required_next_step": "rerun the TradingView refresh and fixed candidate-universe build after the market close before executing replay",
            },
        )

    env = dict(os.environ)
    if option_feature_database_url and not env.get("OPENCLAW_DATABASE_URL"):
        env["OPENCLAW_DATABASE_URL"] = option_feature_database_url
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(evaluation_repo_root / "src"),
            str(execution_repo_root / "src"),
            str(model_repo_root / "src"),
            env.get("PYTHONPATH", ""),
        ]
    ).rstrip(os.pathsep)

    lock_ref = SchedulerLockRef(
        contract_type="scheduler_lock",
        lock_scope="promotion",
        lock_key=f"lock:model_group_replay:{contract_id}",
        lock_path=str(storage_root / "runtime" / "locks" / "model_group" / f"{contract_id}.lock"),
        model_id="model_group",
        candidate_ref=contract_id,
    )
    with acquire_scheduler_lock(lock_ref):
        try:
            completed = subprocess.run(
                command,
                cwd=evaluation_repo_root,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            runner_error = (exc.stderr or exc.stdout or str(exc)).strip()
            option_feature_acquisition_required = REPLAY_OPTION_FEATURE_ACQUISITION_REQUIRED in runner_error
            return _decision(
                now=now,
                decision_status="backoff",
                reason_code=(
                    "model_group_replay_option_feature_acquisition_required"
                    if option_feature_acquisition_required
                    else "model_group_replay_execution_failed"
                ),
                reason=runner_error,
                selected_work="model_group.replay",
                command=command,
                execution_summary={
                    "contract_id": contract_id,
                    "dataset_root": str(dataset_root),
                    "training_fold": training_fold,
                    "expected_replay_months": expected_months,
                    "ready_replay_months_before": len(ready_months),
                    "option_feature_database_configured": bool(option_feature_database_url),
                    "candidate_universe_path": str(resolved_candidate_universe_path),
                    "fixed_candidate_universe_symbol_count": len(fixed_candidate_universe_symbols),
                    "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
                    "equity_symbol_pool_symbol_count": len(equity_pool_symbols),
                    "initial_capital_usd": initial_capital_usd,
                    "candidate_universe_source_policy": CANDIDATE_UNIVERSE_SOURCE_POLICY,
                    "runner_returncode": exc.returncode,
                    "runner_stdout": exc.stdout,
                    "runner_stderr": exc.stderr,
                    "required_next_step": (
                        "run shared option_chain_state_source acquisition under M05 with source_end no later than each missing replay decision timestamp, generate M05 option features from that shared source, then retry model_group.replay"
                        if option_feature_acquisition_required
                        else None
                    ),
                    "blocked_stage_id": (
                        "model_05_option_expression.option_chain_data_acquisition"
                        if option_feature_acquisition_required
                        else None
                    ),
                    "resume_stage_id": "model_group.replay" if option_feature_acquisition_required else None,
                },
            )
    receipt = json.loads(completed.stdout)
    receipt_scope_status = _replay_receipt_scope_status(replay_receipt=receipt, training_fold=training_fold)
    if not receipt_scope_status["compatible"]:
        return _decision(
            now=now,
            decision_status="backoff",
            reason_code="model_group_replay_receipt_scope_mismatch",
            reason=str(receipt_scope_status["reason"]),
            selected_work="model_group.replay",
            command=command,
            execution_summary={
                "contract_id": contract_id,
                "dataset_root": str(dataset_root),
                "training_fold": training_fold,
                "replay_receipt_scope_status": receipt_scope_status,
                "replay_execution_receipt": receipt,
                "candidate_universe_path": str(resolved_candidate_universe_path),
                "fixed_candidate_universe_symbol_count": len(fixed_candidate_universe_symbols),
                "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
                "equity_symbol_pool_symbol_count": len(equity_pool_symbols),
                "initial_capital_usd": initial_capital_usd,
                "candidate_universe_source_policy": CANDIDATE_UNIVERSE_SOURCE_POLICY,
            },
        )
    refreshed_ready_months = _ready_replay_months(dataset_root, replay_run_ids={str(receipt.get("replay_execution_run_id") or run_id)})
    return _decision(
        now=now,
        decision_status="executed",
        reason_code="model_group_replay_executed",
        reason="executed side-effect-free model-group replay over frozen local dataset",
        selected_work="model_group.replay",
        command=command,
        execution_summary={
            "contract_id": contract_id,
            "dataset_root": str(dataset_root),
            "training_fold": training_fold,
            "expected_replay_months": expected_months,
            "ready_replay_months_before": len(ready_months),
            "ready_replay_months_after": len(refreshed_ready_months),
            "option_feature_database_configured": bool(option_feature_database_url),
            "after_cost_alpha_model_ref": str(after_cost_alpha_model_path),
            "candidate_universe_path": str(resolved_candidate_universe_path),
            "fixed_candidate_universe_symbol_count": len(fixed_candidate_universe_symbols),
            "fixed_equity_candidate_symbol_count": len(fixed_equity_universe_symbols),
            "equity_symbol_pool_symbol_count": len(equity_pool_symbols),
            "initial_capital_usd": initial_capital_usd,
            "candidate_universe_source_policy": CANDIDATE_UNIVERSE_SOURCE_POLICY,
            "replay_execution_receipt": receipt,
        },
    )


def _decision(
    *,
    now: datetime,
    decision_status: str,
    reason_code: str,
    reason: str,
    selected_work: str,
    command: list[str],
    execution_summary: dict[str, Any],
) -> SchedulerDecision:
    now_et = now.astimezone(NEW_YORK)
    return SchedulerDecision(
        contract_type="manager_scheduler_decision",
        now_utc=now.isoformat(),
        now_et=now_et.isoformat(),
        decision_status=decision_status,  # type: ignore[arg-type]
        reason_code=reason_code,
        reason=reason,
        market_protection_active=False,
        resource_pressure_active=False,
        selected_work=selected_work,
        command=command,
        next_internal_stage="model_group_replay",
        provider_calls=0,
        dispatch_performed=False,
        model_activation_performed=False,
        broker_execution_performed=False,
        storage_lifecycle_mutation_performed=False,
        execution_summary=execution_summary,
        lock_plan=scheduler_lock_plan(
            month=None,
            selected_work=selected_work,
            next_internal_stage="model_group_replay",
        ),
    )


def _replay_dataset_root(storage_root: Path, contract_id: str) -> Path:
    return storage_root.parent / "05_replay_datasets" / contract_id


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _database_url() -> str | None:
    for env_name in ("OPENCLAW_DATABASE_URL", "DATABASE_URL"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    return None


def _after_cost_alpha_model_path(*, storage_root: Path, training_fold: Mapping[str, Any]) -> Path:
    target_symbol = str(training_fold.get("target_symbol") or "").strip().lower()
    start_month = str(training_fold.get("start_month") or "").strip()
    end_month = str(training_fold.get("end_month") or "").strip()
    filename = f"after_cost_alpha_model_{target_symbol}_{start_month}_{end_month}.json"
    return storage_root.parent / "03_model_artifacts" / "runtime" / "model_05_alpha_confidence" / filename


def _validated_initial_capital_usd(value: float) -> float:
    capital = float(value)
    if not math.isfinite(capital) or capital <= 0:
        raise ValueError("initial_capital_usd must be a positive finite number")
    return capital


def _historical_candidate_universe_path(storage_root: Path) -> Path:
    trading_storage_root = storage_root.parent.parent
    return trading_storage_root / "main" / "shared" / "historical_candidate_universe.csv"


def _fixed_historical_candidate_symbols(path: Path, *, asset_class: str | None = None) -> set[str]:
    symbols: set[str] = set()
    for row in _csv_rows(path):
        symbol = str(row.get("symbol") or "").strip().upper()
        status = str(row.get("replay_candidate_status") or row.get("pool_membership_status") or "active").strip().lower()
        if status != "active":
            continue
        if asset_class is not None and str(row.get("asset_class") or "").strip().lower() != asset_class:
            continue
        if not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", symbol):
            continue
        symbols.add(symbol)
    return symbols


def _candidate_universe_close_status(path: Path, *, now: datetime) -> dict[str, Any]:
    rows = _csv_rows(path)
    freeze_dates = sorted({str(row.get("freeze_as_of_date") or "").strip() for row in rows if str(row.get("freeze_as_of_date") or "").strip()})
    now_et = now.astimezone(NEW_YORK)
    today_et = now_et.date().isoformat()
    current_day_freeze = today_et in freeze_dates
    ready_for_replay = not current_day_freeze or now_et.time() >= REPLAY_CANDIDATE_UNIVERSE_CLOSE_READY_TIME
    return {
        "candidate_universe_path": str(path),
        "freeze_as_of_dates": freeze_dates,
        "now_et": now_et.isoformat(),
        "post_close_ready_time_et": REPLAY_CANDIDATE_UNIVERSE_CLOSE_READY_TIME.isoformat(),
        "current_day_freeze": current_day_freeze,
        "ready_for_replay": ready_for_replay,
    }


def _replay_equity_symbols_from_fixed_universe(*, fixed_universe_symbols: set[str], replay_plan_symbols: set[str]) -> tuple[str, ...]:
    symbols: list[str] = []
    seen: set[str] = set()
    if not fixed_universe_symbols:
        return ()
    for symbol in sorted(replay_plan_symbols & fixed_universe_symbols):
        if not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", symbol):
            continue
        if symbol in seen:
            continue
        symbols.append(symbol)
        seen.add(symbol)
    return tuple(symbols)


def _replay_dataset_available_equity_symbols(dataset_root: Path) -> set[str]:
    symbols: set[str] = set()
    for row in _csv_rows(dataset_root / "feed_acquisition_plan.csv"):
        if str(row.get("source_id") or "").strip() != "alpaca_bars":
            continue
        if str(row.get("coverage_status") or "").strip().lower() not in {"available", "succeeded", "complete", "completed"}:
            continue
        symbols.update(_string_set(row.get("target_ref") or row.get("target_symbol") or row.get("symbol")))
    return symbols


def _python_executable() -> str:
    if DEFAULT_PYTHON_EXECUTABLE.exists():
        return str(DEFAULT_PYTHON_EXECUTABLE)
    return sys.executable


def _dataset_is_frozen_and_complete(manifest: Mapping[str, Any], freeze_receipt: Mapping[str, Any]) -> bool:
    validation = freeze_receipt.get("validation")
    return (
        manifest.get("freeze_status") == "frozen"
        and int(manifest.get("missing_feed_acquisition_count") or 0) == 0
        and freeze_receipt.get("freeze_status") == "frozen"
        and isinstance(validation, Mapping)
        and validation.get("validation_status") == "passed"
    )


def _completed_training_fold(*, storage_root: Path, selected_target_symbol: str | None) -> dict[str, Any] | None:
    runtime_root = storage_root / "runtime"
    if not runtime_root.exists():
        return None
    selected = str(selected_target_symbol or "").strip().lower()
    candidates: list[dict[str, Any]] = []
    for path in sorted(runtime_root.glob("model_training_fold_state_*.json")):
        try:
            payload = _load_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if selected and f"_{selected}_" not in path.stem.lower():
            continue
        stages = payload.get("stages")
        if not isinstance(stages, list) or not stages:
            continue
        if not base_stack_model_generation_splits_complete(stages):
            continue
        if not all(str(stage.get("status") or "").lower() in {"succeeded", "not_applicable"} for stage in stages if isinstance(stage, Mapping)):
            continue
        start_month = str(payload.get("start_month") or "")
        end_month = str(payload.get("end_month") or "")
        if not start_month or not end_month:
            continue
        target_symbol = _fold_state_target_symbol(path, payload)
        candidates.append(
            {
                "fold_id": f"fold_{start_month}_{end_month}",
                "fold_label": _fold_label(start_month, end_month),
                "start_month": start_month,
                "end_month": end_month,
                "target_symbol": target_symbol,
                "state_path": str(path),
                "candidate_model_ref": _candidate_model_ref(
                    target_symbol=target_symbol,
                    start_month=start_month,
                    end_month=end_month,
                ),
                "fold_stack_evidence_ref": str(path),
            }
        )
    return sorted(candidates, key=lambda row: (row["start_month"], row["end_month"], row["state_path"]))[-1] if candidates else None


def _candidate_model_ref(*, target_symbol: str | None, start_month: str, end_month: str) -> str:
    target_token = str(target_symbol or "target").strip().lower().replace(".", "_")
    return f"storage://trading-manager/model_group/{target_token}/{start_month}_{end_month}"


def _fold_state_target_symbol(path: Path, payload: Mapping[str, Any]) -> str | None:
    for key in ("target_symbol", "selected_target_symbol", "target_ref"):
        value = str(payload.get(key) or "").strip().upper()
        if value:
            return value
    match = re.match(r"^model_training_fold_state_([A-Za-z0-9.-]+)_\d{4}-\d{2}_\d{4}-\d{2}$", path.stem)
    return match.group(1).upper() if match else None


def _replay_dataset_scope_status(*, dataset_root: Path, manifest: Mapping[str, Any], training_fold: Mapping[str, Any]) -> dict[str, Any]:
    fold_id = str(training_fold.get("fold_id") or "")
    manifest_fold_id = str(manifest.get("candidate_fold_id") or manifest.get("fold_id") or "").strip()
    target_refs = _replay_dataset_target_refs(dataset_root=dataset_root, manifest=manifest)
    if manifest_fold_id and fold_id and manifest_fold_id != fold_id:
        return {
            "compatible": False,
            "reason": f"replay dataset fold {manifest_fold_id} does not match completed training fold {fold_id}",
            "dataset_target_refs": sorted(target_refs),
        }
    return {
        "compatible": True,
        "reason": "replay dataset is eligible for fold-bound execution-component-graph replay",
        "dataset_target_refs": sorted(target_refs),
    }


def _replay_dataset_target_refs(*, dataset_root: Path, manifest: Mapping[str, Any]) -> set[str]:
    refs = _string_set(manifest.get("pre_replay_target_refs"))
    for row in _csv_rows(dataset_root / "feed_acquisition_plan.csv"):
        source_id = str(row.get("source_id") or "").strip()
        coverage_status = str(row.get("coverage_status") or "").strip().lower()
        if coverage_status not in {"available", "succeeded", "complete", "completed"}:
            continue
        if source_id == "okx_crypto_market_data":
            refs.update(CRYPTO_REPLAY_TARGET_REFS)
        refs.update(_string_set(row.get("target_ref") or row.get("target_symbol") or row.get("symbol")))
        params_text = str(row.get("params_json") or "").strip()
        if params_text:
            try:
                params = json.loads(params_text)
            except json.JSONDecodeError:
                params = None
            if isinstance(params, Mapping):
                refs.update(_string_set(params.get("target_refs") or params.get("symbols") or params.get("target_symbol")))
    return {ref.upper() for ref in refs if ref}


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return {stripped.upper()} if stripped else set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip().upper() for item in value if str(item).strip()}
    return set()


def _fold_label(start_month: str, end_month: str) -> str:
    try:
        start_year, start_month_number = (int(part) for part in start_month.split("-", 1))
        end_year, end_month_number = (int(part) for part in end_month.split("-", 1))
    except ValueError:
        return f"{start_month}..{end_month}"
    if start_year != end_year or (end_month_number - start_month_number) != 5:
        return f"{start_month}..{end_month}"
    fold_number = ((start_month_number - 1) // 6) + 1
    return f"{start_year:04d}-fold{fold_number}"


def _expected_replay_months(dataset_root: Path) -> int:
    months = _unique_csv_values(dataset_root / "feed_acquisition_plan.csv", "month")
    if months:
        return len(months)
    rows = _csv_rows(dataset_root / "replay_window_manifest.csv")
    if not rows:
        return 60
    try:
        start = datetime.fromisoformat(str(rows[0].get("start_date"))).date()
        end = datetime.fromisoformat(str(rows[0].get("end_date"))).date()
    except (TypeError, ValueError):
        return 60
    return max(1, (end.year - start.year) * 12 + end.month - start.month)


def _compatible_replay_run_ids(*, dataset_root: Path, training_fold: Mapping[str, Any]) -> set[str]:
    run_ids: set[str] = set()
    replay_root = dataset_root / "replay_execution_runs"
    if not replay_root.exists():
        return run_ids
    for receipt_path in sorted(replay_root.glob("*/replay_execution_receipt.json")):
        try:
            receipt = _load_json_object(receipt_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if not _replay_receipt_scope_status(replay_receipt=receipt, training_fold=training_fold)["compatible"]:
            continue
        if not _replay_receipt_decision_rows_exist(receipt):
            continue
        run_id = str(receipt.get("replay_execution_run_id") or receipt_path.parent.name).strip()
        if run_id:
            run_ids.add(run_id)
    return run_ids


def _replay_receipt_decision_rows_exist(replay_receipt: Mapping[str, Any]) -> bool:
    decision_rows_ref = str(replay_receipt.get("decision_rows_ref") or "").strip()
    return bool(decision_rows_ref) and Path(decision_rows_ref).exists()


def _replay_receipt_scope_status(*, replay_receipt: Mapping[str, Any], training_fold: Mapping[str, Any]) -> dict[str, Any]:
    candidate_model_ref = str(replay_receipt.get("candidate_model_ref") or "")
    if "current_deterministic_crypto_policy" in candidate_model_ref:
        return {"compatible": False, "reason": "deterministic crypto placeholder policy"}
    receipt_fold_id = str(replay_receipt.get("candidate_fold_id") or replay_receipt.get("fold_id") or "")
    fold_id = str(training_fold.get("fold_id") or "")
    if receipt_fold_id and fold_id and receipt_fold_id != fold_id:
        return {"compatible": False, "reason": "replay fold mismatch"}
    target_refs = _string_set(replay_receipt.get("target_refs") or replay_receipt.get("pre_replay_target_refs"))
    asset_class_counts = replay_receipt.get("asset_class_counts")
    if not isinstance(asset_class_counts, Mapping):
        asset_class_counts = {}
    has_equity_or_option_scope = (
        any(ref and ref not in CRYPTO_REPLAY_TARGET_REFS for ref in target_refs)
        or int(asset_class_counts.get("us_equity") or 0) > 0
        or int(asset_class_counts.get("us_option") or 0) > 0
    )
    if has_equity_or_option_scope:
        candidate_handoff_status = str(replay_receipt.get("candidate_handoff_status") or "")
        if candidate_handoff_status not in {"available", "override"}:
            return {
                "compatible": False,
                "reason": "equity/options replay receipt missing fixed historical candidate universe evidence",
            }
    return {"compatible": True, "reason": "compatible fold-bound execution-component-graph replay receipt"}


def _ready_replay_months(dataset_root: Path, replay_run_ids: set[str] | None = None) -> set[str]:
    ready: set[str] = set()
    paths = sorted((dataset_root / "replay_runs").glob("*.jsonl")) + [dataset_root / "replay_progress.jsonl"]
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                run_id = str(row.get("replay_execution_run_id") or "").strip()
                if replay_run_ids is not None and run_id not in replay_run_ids:
                    continue
                status = str(row.get("status") or row.get("replay_status") or "").lower()
                month = str(row.get("month") or row.get("replay_month") or "").strip()
                if month and status in {"succeeded", "completed", "complete"}:
                    ready.add(month)
    return ready


def _unique_csv_values(path: Path, field: str) -> set[str]:
    return {str(row.get(field) or "").strip() for row in _csv_rows(path) if str(row.get(field) or "").strip()}


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


__all__ = [
    "DEFAULT_REPLAY_CONTRACT_ID",
    "run_model_group_replay_if_ready",
]

"""Autonomous historical provider acquisition dispatch helpers.

Historical provider acquisition is an internal training stage. This module
prepares non-dry-run task keys and can dispatch bounded trading-data provider
commands without a per-batch manual gate. It still performs no
model activation, broker execution, order construction, or account mutation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .failure_register import accepted_failure_request_ids_from_register
from .historical_training import prepare_layer_historical_training_batch, prepare_target_local_historical_training_batch
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_THREE_TARGET_STATE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from .request_payloads import DEFAULT_STORAGE_ROOT
from .request_payloads import ALPACA_BARS_MONTHLY_MAX_PAGES
from .stage_coverage import collect_stage_coverage

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_PROVIDER_STAGE_MIN_WORKERS = 1
DEFAULT_PROVIDER_STAGE_MAX_WORKERS = 4
DEFAULT_PROVIDER_STAGE_WORKER_MEMORY_MB = 512
DEFAULT_PROVIDER_STAGE_RESERVED_MEMORY_MB = 2048
DEFAULT_PROVIDER_STAGE_LOAD_TARGET_PER_CPU = 0.70
ALPACA_BARS_PROVIDER_POLICY = {
    "allowed_providers": ["alpaca"],
    "allowed_endpoint_families": ["bars"],
    "max_symbols": 1,
    "max_requests": ALPACA_BARS_MONTHLY_MAX_PAGES,
    "max_time_window": "31d",
}


@dataclass(frozen=True)
class ProviderWorkerSelection:
    dynamic_enabled: bool
    requested_max_workers: int
    selected_worker_count: int
    request_count: int
    cpu_count: int
    load_1m: float | None
    load_target_per_cpu: float
    memory_available_mb: int | None
    worker_memory_mb: int
    reserved_memory_mb: int
    reason: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderDispatchItem:
    request_id: str
    task_key_path: str
    runtime_task_key_path: str | None
    runtime_task_key_retained: bool
    command: list[str]
    receipt_path: str
    status: str
    worker_id: str
    worker_slot: int
    return_code: int | None = None
    error_summary: str | None = None

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProviderDispatchSummary:
    contract_type: str
    stage_id: str
    request_count: int
    validation_count: int
    dispatch_count: int
    provider_calls: int
    dispatch_performed: bool
    model_activation_performed: bool
    broker_execution_performed: bool
    items: tuple[ProviderDispatchItem, ...]
    worker_selection: ProviderWorkerSelection

    def summary_row(self) -> dict[str, Any]:
        return {
            "contract_type": self.contract_type,
            "stage_id": self.stage_id,
            "request_count": self.request_count,
            "validation_count": self.validation_count,
            "dispatch_count": self.dispatch_count,
            "provider_calls": self.provider_calls,
            "dispatch_performed": self.dispatch_performed,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "worker_selection": self.worker_selection.summary_row(),
            "items": [item.summary_row() for item in self.items],
        }


def _task_key_path(storage_root: Path, request: Mapping[str, Any]) -> Path:
    parameter_ref = str(request.get("parameter_ref") or "")
    prefix = "storage://trading-manager/"
    if not parameter_ref.startswith(prefix):
        raise TaskSystemError(f"unsupported parameter_ref for provider dispatch: {parameter_ref}")
    return storage_root / parameter_ref.removeprefix(prefix)


def _autonomous_provider_task_key(task_key: Mapping[str, Any]) -> dict[str, Any]:
    runtime_key = dict(task_key)
    runtime_key["dry_run"] = False
    runtime_key["production_mode"] = "historical_provider_acquisition"
    controls = dict(runtime_key.get("manager_controls") or {})
    controls.update(ALPACA_BARS_PROVIDER_POLICY)
    controls["allow_live_provider_calls"] = True
    controls["autonomous_historical_provider_acquisition"] = True
    runtime_key["manager_controls"] = controls
    params = dict(runtime_key.get("params") or {})
    params["manager_dry_run"] = False
    runtime_key["params"] = params
    policy_refs = [str(item) for item in runtime_key.get("policy_refs") or []]
    if "autonomous_historical_provider_acquisition" not in policy_refs:
        policy_refs.append("autonomous_historical_provider_acquisition")
    runtime_key["policy_refs"] = policy_refs
    return runtime_key


def _run_id(request_id: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{request_id}_provider_{stamp}"


def _command(task_key_path: Path, request_id: str) -> list[str]:
    return [
        "python3",
        "-m",
        "data_feed.01_feed_alpaca_bars",
        str(task_key_path),
        "--run-id",
        _run_id(request_id),
    ]


def _available_memory_mb() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def select_provider_worker_count(
    *,
    request_count: int,
    execute_provider_calls: bool,
    dynamic_workers: bool = True,
    max_workers: int = DEFAULT_PROVIDER_STAGE_MAX_WORKERS,
    min_workers: int = DEFAULT_PROVIDER_STAGE_MIN_WORKERS,
    load_target_per_cpu: float = DEFAULT_PROVIDER_STAGE_LOAD_TARGET_PER_CPU,
    worker_memory_mb: int = DEFAULT_PROVIDER_STAGE_WORKER_MEMORY_MB,
    reserved_memory_mb: int = DEFAULT_PROVIDER_STAGE_RESERVED_MEMORY_MB,
) -> ProviderWorkerSelection:
    if max_workers <= 0:
        raise TaskSystemError("max_workers must be positive")
    if min_workers <= 0:
        raise TaskSystemError("min_workers must be positive")
    requested_max = max(min_workers, max_workers)
    cpu_count = os.cpu_count() or 1
    load_1m = None
    try:
        load_1m = os.getloadavg()[0]
    except (AttributeError, OSError):
        pass
    memory_available_mb = _available_memory_mb()
    if not execute_provider_calls or request_count <= 0:
        return ProviderWorkerSelection(
            dynamic_enabled=dynamic_workers,
            requested_max_workers=requested_max,
            selected_worker_count=0,
            request_count=request_count,
            cpu_count=cpu_count,
            load_1m=load_1m,
            load_target_per_cpu=load_target_per_cpu,
            memory_available_mb=memory_available_mb,
            worker_memory_mb=worker_memory_mb,
            reserved_memory_mb=reserved_memory_mb,
            reason="provider dispatch planning only; no worker slots active",
        )
    if not dynamic_workers:
        selected = min(request_count, requested_max)
        return ProviderWorkerSelection(
            dynamic_enabled=False,
            requested_max_workers=requested_max,
            selected_worker_count=selected,
            request_count=request_count,
            cpu_count=cpu_count,
            load_1m=load_1m,
            load_target_per_cpu=load_target_per_cpu,
            memory_available_mb=memory_available_mb,
            worker_memory_mb=worker_memory_mb,
            reserved_memory_mb=reserved_memory_mb,
            reason="fixed worker count bounded by request count",
        )
    load_capacity = requested_max
    if load_1m is not None:
        load_headroom = max(0.0, (cpu_count * load_target_per_cpu) - load_1m)
        load_capacity = max(min_workers, int(load_headroom // 0.5) or min_workers)
    memory_capacity = requested_max
    if memory_available_mb is not None:
        memory_headroom = max(0, memory_available_mb - reserved_memory_mb)
        memory_capacity = max(min_workers, memory_headroom // max(1, worker_memory_mb))
    selected = max(min_workers, min(request_count, requested_max, load_capacity, memory_capacity))
    reason = "dynamic worker count selected from request count, load headroom, and available memory"
    return ProviderWorkerSelection(
        dynamic_enabled=True,
        requested_max_workers=requested_max,
        selected_worker_count=selected,
        request_count=request_count,
        cpu_count=cpu_count,
        load_1m=load_1m,
        load_target_per_cpu=load_target_per_cpu,
        memory_available_mb=memory_available_mb,
        worker_memory_mb=worker_memory_mb,
        reserved_memory_mb=reserved_memory_mb,
        reason=reason,
    )


def _filter_requests(
    requests: Sequence[Mapping[str, Any]],
    *,
    symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    symbol_filter = {item.strip().upper() for item in symbols if item.strip()}
    request_filter = {item.strip() for item in request_ids if item.strip()}
    filtered = []
    for row in requests:
        symbol_ok = not symbol_filter or str(row.get("symbol") or "").upper() in symbol_filter
        request_ok = not request_filter or str(row.get("request_id") or "") in request_filter
        if symbol_ok and request_ok:
            filtered.append(dict(row))
    if symbol_filter:
        found = {str(row.get("symbol") or "").upper() for row in filtered}
        missing = sorted(symbol_filter - found)
        if missing:
            raise TaskSystemError("requested symbols are not in the planned provider batch: " + ",".join(missing))
    if request_filter:
        found_ids = {str(row.get("request_id") or "") for row in filtered}
        missing_ids = sorted(request_filter - found_ids)
        if missing_ids:
            raise TaskSystemError("requested ids are not in the planned provider batch: " + ",".join(missing_ids))
    if limit is not None:
        if limit <= 0:
            raise TaskSystemError("limit must be positive")
        filtered = filtered[:limit]
    if not filtered:
        raise TaskSystemError("provider dispatch filter selected no requests")
    return filtered



def dispatch_layer_provider_acquisition(
    *,
    model_layer: str = LAYER_ONE_MODEL_LAYER,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    symbols: Sequence[str] = (),
    target_symbols: Sequence[str] = (),
    request_ids: Sequence[str] = (),
    limit: int | None = None,
    execute_provider_calls: bool = False,
    continue_on_error: bool = False,
    skip_registered_failures: bool = False,
    reject_terminal_coverage: bool = False,
    database_url: str | None = None,
    dynamic_workers: bool = True,
    max_workers: int = DEFAULT_PROVIDER_STAGE_MAX_WORKERS,
) -> ProviderDispatchSummary:
    """Plan or dispatch a layer Alpaca-bars acquisition batch.

    Approval artifacts are not required or read.
    """

    if model_layer not in {LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, LAYER_THREE_TARGET_STATE_MODEL_LAYER}:
        raise TaskSystemError(f"unsupported provider dispatch model_layer: {model_layer}")
    if model_layer == LAYER_THREE_TARGET_STATE_MODEL_LAYER:
        selected_targets = tuple(target_symbols or symbols)
        summary, requests, _payloads, _validations = prepare_target_local_historical_training_batch(
            start_month=start_month,
            end_month=end_month,
            target_symbols=selected_targets,
            storage_root=storage_root,
            write=execute_provider_calls,
            persist_sql=False,
            validate_handoff=False,
        )
    else:
        summary, requests, _payloads, _validations = prepare_layer_historical_training_batch(
            model_layer=model_layer,
            start_month=start_month,
            end_month=end_month,
            storage_root=storage_root,
            write=execute_provider_calls,
            persist_sql=False,
            validate_handoff=False,
        )
    selected_requests = _filter_requests(requests, symbols=symbols, request_ids=request_ids, limit=limit)
    registered_skip_ids: set[str] = set()
    registered_skip_refs: tuple[str, ...] = ()
    if skip_registered_failures:
        skip_ids, registered_skip_refs = accepted_failure_request_ids_from_register(
            database_url=database_url,
            stage_id=f"{model_layer}.data_acquisition",
            start_month=start_month,
            end_month=end_month,
        )
        registered_skip_ids = set(skip_ids)
    live_requests = []
    skipped_requests = []
    for row in selected_requests:
        if str(row.get("request_id") or "") in registered_skip_ids:
            skipped_requests.append(dict(row))
            continue
        policy_refs = [str(item) for item in row.get("policy_refs") or []]
        if "autonomous_historical_provider_acquisition" not in policy_refs:
            policy_refs.append("autonomous_historical_provider_acquisition")
        live_requests.append(dict(row) | {"dry_run": False, "policy_refs": policy_refs})
    if execute_provider_calls and reject_terminal_coverage and live_requests:
        report = collect_stage_coverage(
            stage_id=f"{model_layer}.data_acquisition",
            start_month=start_month,
            end_month=end_month,
            database_url=database_url,
        )
        if report.failed_request_ids:
            raise TaskSystemError("stage has unreviewed failed requests; review/register failures before executing more live calls: " + ",".join(report.failed_request_ids))
        terminal_ids = {str(item) for item in (*report.ready_request_ids, *report.accepted_failed_request_ids)}
        repeated_ids = sorted(str(row.get("request_id") or "") for row in live_requests if str(row.get("request_id") or "") in terminal_ids)
        if repeated_ids:
            raise TaskSystemError("refusing to execute provider calls for terminal stage requests: " + ",".join(repeated_ids))
    items: list[ProviderDispatchItem] = [
        ProviderDispatchItem(
            request_id=str(request["request_id"]),
            task_key_path=str(_task_key_path(storage_root, request).resolve()),
            runtime_task_key_path=None,
            runtime_task_key_retained=False,
            command=[],
            receipt_path="",
            status="skipped_registered_accepted_failure",
            worker_id="provider-worker-skipped",
            worker_slot=0,
            return_code=None,
            error_summary=";".join(registered_skip_refs) if registered_skip_refs else "registered accepted failure",
        )
        for request in skipped_requests
    ]
    worker_selection = select_provider_worker_count(
        request_count=len(live_requests),
        execute_provider_calls=execute_provider_calls,
        dynamic_workers=dynamic_workers,
        max_workers=max_workers,
    )

    def dispatch_one(request: Mapping[str, Any], *, worker_slot: int) -> ProviderDispatchItem:
        source_path = _task_key_path(storage_root, request).resolve()
        if not source_path.exists():
            raise TaskSystemError(f"task key does not exist: {source_path}")
        task_key = json.loads(source_path.read_text(encoding="utf-8"))
        if not isinstance(task_key, Mapping):
            raise TaskSystemError(f"task key must be a JSON object: {source_path}")
        runtime_task_key = (storage_root / "runtime" / "provider_task_keys" / str(request["request_id"]) / "task_key.json").resolve()
        command_path = source_path
        runtime_task_key_retained = False
        if execute_provider_calls:
            runtime_task_key.parent.mkdir(parents=True, exist_ok=True)
            runtime_task_key.write_text(json.dumps(_autonomous_provider_task_key(task_key), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            command_path = runtime_task_key
            runtime_task_key_retained = True
        command = _command(command_path, str(request["request_id"]))
        relative_receipt_path = Path(str(task_key.get("output_root") or "storage")) / "completion_receipt.json"
        receipt_path = str((trading_data_root / relative_receipt_path).resolve()) if execute_provider_calls else str(relative_receipt_path)
        status = "validated_not_dispatched"
        return_code = None
        error_tail = None
        if execute_provider_calls:
            result = subprocess.run(
                command,
                cwd=trading_data_root,
                env={**os.environ, "PYTHONPATH": str(trading_data_root / "src")},
                check=False,
                text=True,
                capture_output=True,
            )
            return_code = result.returncode
            status = "dispatched_succeeded" if result.returncode == 0 else "dispatched_failed"
            error_tail = "\n".join(part for part in (result.stdout[-500:], result.stderr[-500:]) if part) if result.returncode != 0 else None
            if result.returncode == 0:
                try:
                    runtime_task_key.unlink()
                    runtime_task_key_retained = False
                except FileNotFoundError:
                    runtime_task_key_retained = False
            if result.returncode != 0 and not continue_on_error:
                raise TaskSystemError(f"provider dispatch failed for {request['request_id']}: {error_tail}")
        return ProviderDispatchItem(
            request_id=str(request["request_id"]),
            task_key_path=str(source_path),
            runtime_task_key_path=str(runtime_task_key) if execute_provider_calls and runtime_task_key_retained else None,
            runtime_task_key_retained=runtime_task_key_retained,
            command=command,
            receipt_path=receipt_path,
            status=status,
            worker_id=f"provider-worker-{worker_slot}",
            worker_slot=worker_slot,
            return_code=return_code,
            error_summary=error_tail,
        )

    if worker_selection.selected_worker_count > 1:
        by_id: dict[str, ProviderDispatchItem] = {}
        with ThreadPoolExecutor(max_workers=worker_selection.selected_worker_count) as executor:
            futures = {
                executor.submit(dispatch_one, request, worker_slot=(index % worker_selection.selected_worker_count) + 1): str(request["request_id"])
                for index, request in enumerate(live_requests)
            }
            for future in as_completed(futures):
                by_id[futures[future]] = future.result()
        items.extend(by_id[str(request["request_id"])] for request in live_requests)
    else:
        items.extend(dispatch_one(request, worker_slot=1) for request in live_requests)
    dispatch_count = sum(1 for item in items if item.status in {"dispatched_succeeded", "dispatched_failed"})
    return ProviderDispatchSummary(
        contract_type="manager_provider_dispatch_summary",
        stage_id=f"{model_layer}.data_acquisition",
        request_count=len(selected_requests),
        validation_count=0,
        dispatch_count=dispatch_count,
        provider_calls=dispatch_count,
        dispatch_performed=execute_provider_calls,
        model_activation_performed=False,
        broker_execution_performed=False,
        items=tuple(items),
        worker_selection=worker_selection,
    )


def dispatch_layer_one_provider_acquisition(**kwargs: Any) -> ProviderDispatchSummary:
    """M01 provider dispatch wrapper."""

    return dispatch_layer_provider_acquisition(model_layer=LAYER_ONE_MODEL_LAYER, **kwargs)


def write_dispatch_summary(summary: ProviderDispatchSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or dispatch autonomous layer provider acquisition.")
    parser.add_argument("--model", default=LAYER_ONE_MODEL_LAYER, choices=(LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, LAYER_THREE_TARGET_STATE_MODEL_LAYER))
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--symbol", action="append", default=[], help="Limit dispatch to one symbol; repeat for multiple symbols.")
    parser.add_argument("--target-symbol", action="append", default=[], help="M02 target-local symbol; repeat for multiple targets.")
    parser.add_argument("--request-id", action="append", default=[], help="Limit dispatch to one request id; repeat for multiple ids.")
    parser.add_argument("--limit", type=int, help="Limit dispatch to the first N selected requests after symbol/request filtering.")
    parser.add_argument(
        "--execute-provider-calls",
        action="store_true",
        help="Actually run trading-data historical provider commands. Omit for plan-only mode.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue the batch after an individual provider command fails, preserving per-request failure receipts for control-plane ingestion.",
    )
    parser.add_argument("--skip-registered-failures", action="store_true", help="Skip requests with accepted_skip entries in the manager failure register.")
    parser.add_argument("--database-url")
    parser.add_argument("--dynamic-workers", action=argparse.BooleanOptionalAction, default=True, help="Select provider workers dynamically from load and memory headroom.")
    parser.add_argument("--max-workers", type=int, default=DEFAULT_PROVIDER_STAGE_MAX_WORKERS, help="Maximum provider worker threads for one bounded dispatch slice.")
    parser.add_argument("--reject-terminal-coverage", action="store_true", help="When executing, reject request ids already ready or reviewed-terminal in stage coverage.")
    parser.add_argument("--write", action="store_true", help="Write dispatch summary JSON to --output-path.")
    parser.add_argument("--output-path", type=Path, help="Optional dispatch summary output path.")
    args = parser.parse_args(argv)
    summary = dispatch_layer_provider_acquisition(
        model_layer=args.model,
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        trading_data_root=args.trading_data_root,
        symbols=args.symbol,
        target_symbols=args.target_symbol,
        request_ids=args.request_id,
        limit=args.limit,
        execute_provider_calls=args.execute_provider_calls,
        continue_on_error=args.continue_on_error,
        skip_registered_failures=args.skip_registered_failures,
        reject_terminal_coverage=args.reject_terminal_coverage,
        database_url=args.database_url,
        dynamic_workers=args.dynamic_workers,
        max_workers=args.max_workers,
    )
    if args.write:
        if args.output_path is None:
            raise TaskSystemError("--write requires --output-path")
        args.output_path.parent.mkdir(parents=True, exist_ok=True)
        args.output_path.write_text(json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_dispatch_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "ProviderDispatchItem",
    "ProviderDispatchSummary",
    "ProviderWorkerSelection",
    "select_provider_worker_count",
    "dispatch_layer_provider_acquisition",
    "dispatch_layer_one_provider_acquisition",
    "write_dispatch_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

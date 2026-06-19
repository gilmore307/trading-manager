"""Manager-owned orchestration for historical model-training batches.

The helpers here prepare manager requests, task-key payloads, and handoff
validation evidence for a model. They do not call providers, dispatch
component runs, activate models, or touch broker/execution state.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError, persist_input_bindings, persist_manager_requests
from .monthly_backfill import (
    LAYER_ONE_MODEL_LAYER,
    LAYER_THREE_TARGET_STATE_MODEL_LAYER,
    LAYER_TWO_MODEL_LAYER,
    plan_monthly_backfill_requests,
    plan_target_local_alpaca_bar_requests,
)
from .request_handoff import DEFAULT_TRADING_DATA_SRC, validate_request_handoffs
from .request_payloads import DEFAULT_STORAGE_ROOT, materialize_request_payloads

LAYER_ONE_PHASE = "model_01_market_context_historical_training"
LAYER_TWO_PHASE = "model_01_sector_context_historical_training"
LAYER_THREE_TARGET_LOCAL_PHASE = "model_02_target_state_target_local_feed"
LAYER_ALPACA_BARS_COMPONENT_ID = "01_feed_alpaca_bars"
LAYER_PHASES = {
    LAYER_ONE_MODEL_LAYER: LAYER_ONE_PHASE,
    LAYER_TWO_MODEL_LAYER: LAYER_TWO_PHASE,
    LAYER_THREE_TARGET_STATE_MODEL_LAYER: LAYER_THREE_TARGET_LOCAL_PHASE,
}


@dataclass(frozen=True)
class HistoricalTrainingBatchPreparation:
    """Summary for one manager-prepared historical-training batch."""

    phase: str
    model_layer: str
    month_start: str
    month_end: str
    request_count: int
    payload_count: int
    handoff_validation_count: int
    symbols: tuple[str, ...]
    request_ids: tuple[str, ...]
    wrote_manager_sql: bool
    wrote_payload_files: bool
    persisted_input_bindings: bool
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "model_layer": self.model_layer,
            "month_start": self.month_start,
            "month_end": self.month_end,
            "request_count": self.request_count,
            "payload_count": self.payload_count,
            "handoff_validation_count": self.handoff_validation_count,
            "symbols": list(self.symbols),
            "request_ids": list(self.request_ids),
            "wrote_manager_sql": self.wrote_manager_sql,
            "wrote_payload_files": self.wrote_payload_files,
            "persisted_input_bindings": self.persisted_input_bindings,
            "provider_calls": self.provider_calls,
            "dispatch_performed": self.dispatch_performed,
            "model_activation_performed": self.model_activation_performed,
            "broker_execution_performed": self.broker_execution_performed,
            "autonomous_historical_provider_acquisition": True,
        }


def _layer_requests(*, model_layer: str, start_month: str, end_month: str) -> list[dict[str, Any]]:
    if model_layer not in {LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER}:
        raise TaskSystemError(f"unsupported historical-training model: {model_layer}")
    rows = plan_monthly_backfill_requests(
        start_month=start_month,
        end_month=end_month,
        include_crypto=False,
        model_readiness=(model_layer,),
    )
    selected = [dict(row) for row in rows if row.get("target_component_id") == LAYER_ALPACA_BARS_COMPONENT_ID]
    if not selected:
        raise TaskSystemError(f"no {model_layer} ETF bar requests were planned")
    return selected


def _target_local_requests(*, start_month: str, end_month: str, target_symbols: Sequence[str]) -> list[dict[str, Any]]:
    rows = plan_target_local_alpaca_bar_requests(
        start_month=start_month,
        end_month=end_month,
        target_symbols=target_symbols,
    )
    selected = [dict(row) for row in rows if row.get("target_component_id") == LAYER_ALPACA_BARS_COMPONENT_ID]
    if not selected:
        raise TaskSystemError("no target-local Alpaca bar requests were planned")
    return selected


def prepare_layer_historical_training_batch(
    *,
    model_layer: str,
    start_month: str,
    end_month: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    write: bool = False,
    persist_sql: bool = False,
    validate_handoff: bool = True,
    database_url: str | None = None,
) -> tuple[HistoricalTrainingBatchPreparation, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Prepare a complete layer historical-training request batch without provider dispatch."""

    requests = _layer_requests(model_layer=model_layer, start_month=start_month, end_month=end_month)
    if persist_sql:
        persist_manager_requests(requests, database_url=database_url)
    materialized = materialize_request_payloads(requests, storage_root=storage_root, write_files=write)
    bindings = [item.input_binding for item in materialized]
    if persist_sql:
        persist_input_bindings(bindings, database_url=database_url)

    validations = []
    if validate_handoff:
        if not write:
            validations = []
        else:
            validations = validate_request_handoffs(
                requests,
                storage_root=storage_root,
                component_src_root=component_src_root,
                input_bindings=bindings,
                require_input_binding=True,
            )

    summary = HistoricalTrainingBatchPreparation(
        phase=LAYER_PHASES[model_layer],
        model_layer=model_layer,
        month_start=start_month,
        month_end=end_month,
        request_count=len(requests),
        payload_count=len(materialized),
        handoff_validation_count=len(validations),
        symbols=tuple(str(row["symbol"]) for row in requests),
        request_ids=tuple(str(row["request_id"]) for row in requests),
        wrote_manager_sql=persist_sql,
        wrote_payload_files=write,
        persisted_input_bindings=persist_sql,
    )
    return summary, requests, [item.summary_row() | {"input_binding": item.input_binding} for item in materialized], [
        item.summary_row() for item in validations
    ]


def prepare_target_local_historical_training_batch(
    *,
    start_month: str,
    end_month: str,
    target_symbols: Sequence[str],
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    write: bool = False,
    persist_sql: bool = False,
    validate_handoff: bool = True,
    database_url: str | None = None,
) -> tuple[HistoricalTrainingBatchPreparation, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Prepare target-local M02 Alpaca bar requests without provider dispatch."""

    requests = _target_local_requests(start_month=start_month, end_month=end_month, target_symbols=target_symbols)
    if persist_sql:
        persist_manager_requests(requests, database_url=database_url)
    materialized = materialize_request_payloads(requests, storage_root=storage_root, write_files=write)
    bindings = [item.input_binding for item in materialized]
    if persist_sql:
        persist_input_bindings(bindings, database_url=database_url)

    validations = []
    if validate_handoff and write:
        validations = validate_request_handoffs(
            requests,
            storage_root=storage_root,
            component_src_root=component_src_root,
            input_bindings=bindings,
            require_input_binding=True,
        )

    summary = HistoricalTrainingBatchPreparation(
        phase=LAYER_THREE_TARGET_LOCAL_PHASE,
        model_layer=LAYER_THREE_TARGET_STATE_MODEL_LAYER,
        month_start=start_month,
        month_end=end_month,
        request_count=len(requests),
        payload_count=len(materialized),
        handoff_validation_count=len(validations),
        symbols=tuple(str(row["symbol"]) for row in requests),
        request_ids=tuple(str(row["request_id"]) for row in requests),
        wrote_manager_sql=persist_sql,
        wrote_payload_files=write,
        persisted_input_bindings=persist_sql,
    )
    return summary, requests, [item.summary_row() | {"input_binding": item.input_binding} for item in materialized], [
        item.summary_row() for item in validations
    ]


def prepare_layer_one_historical_training_batch(
    *,
    start_month: str,
    end_month: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    write: bool = False,
    persist_sql: bool = False,
    validate_handoff: bool = True,
    database_url: str | None = None,
) -> tuple[HistoricalTrainingBatchPreparation, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Prepare a complete M01 historical-training request batch.

    `write=True` writes task_key payload files. `persist_sql=True` also persists
    manager_request rows and request-scoped input_binding rows. No
    provider/component dispatch is performed.
    """

    return prepare_layer_historical_training_batch(
        model_layer=LAYER_ONE_MODEL_LAYER,
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        component_src_root=component_src_root,
        write=write,
        persist_sql=persist_sql,
        validate_handoff=validate_handoff,
        database_url=database_url,
    )


def prepare_layer_two_historical_training_batch(
    *,
    start_month: str,
    end_month: str,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    component_src_root: Path = DEFAULT_TRADING_DATA_SRC,
    write: bool = False,
    persist_sql: bool = False,
    validate_handoff: bool = True,
    database_url: str | None = None,
) -> tuple[HistoricalTrainingBatchPreparation, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Prepare M02 sector-context ETF bar requests without provider dispatch."""

    return prepare_layer_historical_training_batch(
        model_layer=LAYER_TWO_MODEL_LAYER,
        start_month=start_month,
        end_month=end_month,
        storage_root=storage_root,
        component_src_root=component_src_root,
        write=write,
        persist_sql=persist_sql,
        validate_handoff=validate_handoff,
        database_url=database_url,
    )


def write_batch_output(
    summary: HistoricalTrainingBatchPreparation,
    requests: Sequence[Mapping[str, Any]],
    payloads: Sequence[Mapping[str, Any]],
    validations: Sequence[Mapping[str, Any]],
    *,
    output: TextIO,
    output_format: Literal["json", "jsonl"] = "json",
) -> None:
    if output_format == "json":
        json.dump(
            {
                "summary": summary.summary_row(),
                "requests": list(requests),
                "payloads": list(payloads),
                "handoff_validations": list(validations),
            },
            output,
            indent=2,
            sort_keys=True,
        )
        output.write("\n")
        return
    output.write(json.dumps({"record_type": "summary", **summary.summary_row()}, sort_keys=True) + "\n")
    for row in requests:
        output.write(json.dumps({"record_type": "manager_request", **dict(row)}, sort_keys=True) + "\n")
    for row in payloads:
        output.write(json.dumps({"record_type": "payload", **dict(row)}, sort_keys=True) + "\n")
    for row in validations:
        output.write(json.dumps({"record_type": "handoff_validation", **dict(row)}, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a manager-owned M01 historical-training batch without provider dispatch."
    )
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--component-src-root", type=Path, default=DEFAULT_TRADING_DATA_SRC)
    parser.add_argument("--write", action="store_true", help="Persist manager requests, task payload files, and input bindings.")
    parser.add_argument("--write-files-only", action="store_true", help="Write task payload files without persisting SQL rows.")
    parser.add_argument("--no-handoff-validation", action="store_true")
    parser.add_argument("--database-url")
    parser.add_argument("--format", choices=("json", "jsonl"), default="json")
    args = parser.parse_args(argv)

    summary, requests, payloads, validations = prepare_layer_one_historical_training_batch(
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        component_src_root=args.component_src_root,
        write=args.write or args.write_files_only,
        persist_sql=args.write,
        validate_handoff=not args.no_handoff_validation,
        database_url=args.database_url,
    )
    write_batch_output(summary, requests, payloads, validations, output=sys.stdout, output_format=args.format)
    return 0


__all__ = [
    "LAYER_ONE_PHASE",
    "LAYER_TWO_PHASE",
    "LAYER_THREE_TARGET_LOCAL_PHASE",
    "HistoricalTrainingBatchPreparation",
    "prepare_layer_historical_training_batch",
    "prepare_layer_one_historical_training_batch",
    "prepare_layer_two_historical_training_batch",
    "prepare_target_local_historical_training_batch",
    "write_batch_output",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

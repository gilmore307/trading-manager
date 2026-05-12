#!/usr/bin/env python3
"""Dispatch autonomous historical provider acquisition, then reconcile coverage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from trading_manager_tasks.control_plane import TaskSystemError
from trading_manager_tasks.monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER
from trading_manager_tasks.provider_dispatch import DEFAULT_TRADING_DATA_ROOT, dispatch_layer_provider_acquisition
from trading_manager_tasks.request_payloads import DEFAULT_STORAGE_ROOT
from trading_manager_tasks.stage_reconcile import DEFAULT_COMPONENT_STORAGE_ROOT, reconcile_provider_stage


def _stage_id(model_layer: str) -> str:
    if model_layer == LAYER_ONE_MODEL_LAYER:
        return "layer_01_market_regime.data_acquisition"
    if model_layer == LAYER_TWO_MODEL_LAYER:
        return "layer_02_sector_context.data_acquisition"
    raise TaskSystemError(f"unsupported provider model layer: {model_layer}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dispatch autonomous historical provider acquisition and reconcile the provider stage.")
    parser.add_argument("--model-layer", required=True, choices=(LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER))
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--component-storage-root", type=Path, default=DEFAULT_COMPONENT_STORAGE_ROOT)
    parser.add_argument("--database-url")
    parser.add_argument("--symbol", action="append", default=[])
    parser.add_argument("--request-id", action="append", default=[])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--skip-registered-failures", action="store_true")
    parser.add_argument("--reject-terminal-coverage", action="store_true")
    parser.add_argument("--failure-proposal-path", type=Path)
    parser.add_argument("--coverage-report-path", type=Path)
    parser.add_argument("--summary-output-path", type=Path)
    args = parser.parse_args(argv)

    dispatch = dispatch_layer_provider_acquisition(
        model_layer=args.model_layer,
        start_month=args.start_month,
        end_month=args.end_month,
        storage_root=args.storage_root,
        trading_data_root=args.trading_data_root,
        symbols=args.symbol,
        request_ids=args.request_id,
        limit=args.limit,
        execute_provider_calls=True,
        continue_on_error=False,
        skip_registered_failures=args.skip_registered_failures,
        reject_terminal_coverage=args.reject_terminal_coverage,
        database_url=args.database_url,
    )
    reconcile = reconcile_provider_stage(
        stage_id=_stage_id(args.model_layer),
        start_month=args.start_month,
        end_month=args.end_month,
        component_storage_root=args.component_storage_root,
        manager_storage_root=args.storage_root,
        database_url=args.database_url,
        persist_control_plane=True,
        failure_proposal_path=args.failure_proposal_path,
        write_failure_proposal=True,
        persist_failure_register=True,
        collect_coverage=True,
        coverage_report_path=args.coverage_report_path,
        write_coverage_report=True,
        advance_workflow=True,
        write_workflow_state=True,
    )
    summary = {
        "contract_type": "manager_provider_dispatch_reconcile_summary_v1",
        "stage_id": _stage_id(args.model_layer),
        "start_month": args.start_month,
        "end_month": args.end_month,
        "dispatch": dispatch.summary_row(),
        "reconcile": reconcile.summary_row(),
        "provider_calls": dispatch.provider_calls,
        "dispatch_performed": dispatch.dispatch_performed,
        "model_activation_performed": False,
        "broker_execution_performed": False,
    }
    if args.summary_output_path is not None:
        args.summary_output_path.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

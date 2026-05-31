"""Layer 2 target-candidate holdings materialization.

This module prepares m02_sector_context_data_acquisition after Layer 2 sector
context exists. Layer 3 consumes these rows; it should not own their generation.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, TextIO

from .control_plane import TaskSystemError
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_OUTPUT_ROOT = Path("runtime/layer_02_sector_context/target_candidate_holdings")
TARGET_CANDIDATE_HOLDINGS_SOURCE = "m02_sector_context_data_acquisition"
TARGET_CANDIDATE_HOLDINGS_SOURCE_MODULE = "data_source.source_02_target_candidate_holdings"


@dataclass(frozen=True)
class TargetCandidateHoldingsMaterialization:
    """Receipt for Layer 2-owned target-candidate holdings source rows."""

    contract_type: str
    start_month: str
    end_month: str
    target_candidate_holdings_fetch_count: int
    target_candidate_holdings_row_count: int
    task_key_path: str
    trading_data_receipt_path: str | None
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _validate_month(month: str) -> tuple[int, int]:
    if len(month) != 7 or month[4] != "-":
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number < 1 or month_number > 12:
        raise TaskSystemError(f"month must use YYYY-MM format: {month}")
    return year, month_number


def _next_month(month: str) -> str:
    year, month_number = _validate_month(month)
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _month_bounds(month: str) -> tuple[str, str]:
    year, month_number = _validate_month(month)
    next_month = _next_month(month)
    next_year, next_month_number = int(next_month[:4]), int(next_month[5:])
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00", f"{next_year:04d}-{next_month_number:02d}-01T00:00:00-05:00"


def _range_bounds(start_month: str, end_month: str) -> tuple[str, str]:
    start, _ = _month_bounds(start_month)
    _, end = _month_bounds(end_month)
    return start, end


def _fold_key(start_month: str, end_month: str) -> str:
    return f"{start_month.replace('-', '_')}_{end_month.replace('-', '_')}"


def build_target_candidate_holdings_task_key(
    *,
    start_month: str,
    end_month: str,
    output_dir: Path,
    trading_data_output_root: Path,
) -> tuple[dict[str, Any], Path]:
    source_start, source_end = _range_bounds(start_month, end_month)
    fold_key = _fold_key(start_month, end_month)
    task_key_path = output_dir / "target_candidate_holdings_task_key.json"
    task_key_path.parent.mkdir(parents=True, exist_ok=True)
    task_key = {
        "task_id": f"layer_02_target_candidate_holdings_{fold_key}",
        "source": TARGET_CANDIDATE_HOLDINGS_SOURCE,
        "params": {
            "start": source_start,
            "end": source_end,
            "continue_on_error": True,
        },
        "output_root": str(trading_data_output_root),
        "manager_stage_id": "layer_02_sector_context.feature_generation",
        "source_policy": "official_issuer_holdings_fetch_with_point_in_time_window_filter",
    }
    task_key_path.write_text(json.dumps(task_key, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return task_key, task_key_path


def _run_trading_data_source(
    *,
    trading_data_root: Path,
    source_module: str,
    task_key_path: Path,
    run_id: str,
    output_dir: Path,
) -> Mapping[str, Any]:
    command = ["python3", "-m", source_module, str(task_key_path), "--run-id", run_id]
    result = subprocess.run(
        command,
        cwd=trading_data_root,
        env={**os.environ, "PYTHONPATH": "src"},
        text=True,
        capture_output=True,
        check=False,
    )
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    safe_module = source_module.replace(".", "_")
    (log_dir / f"{run_id}.{safe_module}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (log_dir / f"{run_id}.{safe_module}.stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise TaskSystemError(f"{source_module} materialization failed: {result.stderr.strip() or result.stdout.strip()}")
    parsed = json.loads(result.stdout)
    return parsed if isinstance(parsed, Mapping) else {}


def _holdings_fetch_count(receipt_path: str | None) -> int:
    if not receipt_path:
        return 0
    path = Path(receipt_path)
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    runs = [run for run in payload.get("runs") or [] if isinstance(run, Mapping)]
    if not runs:
        return 0
    latest = runs[-1]
    steps = latest.get("steps") if isinstance(latest.get("steps"), Mapping) else {}
    fetch_step = steps.get("fetch") if isinstance(steps.get("fetch"), Mapping) else {}
    details = fetch_step.get("details") if isinstance(fetch_step.get("details"), Mapping) else {}
    feeds = details.get("holding_feeds") if isinstance(details.get("holding_feeds"), list) else []
    errors = details.get("holding_feed_errors") if isinstance(details.get("holding_feed_errors"), list) else []
    return len(feeds) + len(errors)


def materialize_target_candidate_holdings(
    *,
    start_month: str,
    end_month: str,
    manager_storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    run_id: str | None = None,
    write: bool = False,
) -> TargetCandidateHoldingsMaterialization:
    if not manager_storage_root.is_absolute():
        manager_storage_root = Path.cwd() / manager_storage_root
    fold_key = _fold_key(start_month, end_month)
    output_dir = manager_storage_root / output_root / fold_key
    trading_data_output_root = data_storage_root() / "runtime" / TARGET_CANDIDATE_HOLDINGS_SOURCE / f"layer_02_sector_context_{fold_key}"
    run_id = run_id or f"layer_02_target_candidate_holdings_{fold_key}"
    _task_key, task_key_path = build_target_candidate_holdings_task_key(
        start_month=start_month,
        end_month=end_month,
        output_dir=output_dir,
        trading_data_output_root=trading_data_output_root,
    )
    receipt_path: str | None = None
    row_count = 0
    fetch_count = 0
    if write:
        payload = _run_trading_data_source(
            trading_data_root=trading_data_root,
            source_module=TARGET_CANDIDATE_HOLDINGS_SOURCE_MODULE,
            task_key_path=task_key_path,
            run_id=run_id,
            output_dir=output_dir,
        )
        row_count = int((payload.get("row_counts") or {}).get(TARGET_CANDIDATE_HOLDINGS_SOURCE) or 0)
        refs = [str(item) for item in payload.get("references") or []]
        receipt_path = next((item for item in refs if item.endswith("completion_receipt.json")), str(trading_data_output_root / "completion_receipt.json"))
        fetch_count = _holdings_fetch_count(receipt_path)
    return TargetCandidateHoldingsMaterialization(
        contract_type="manager_layer_two_target_candidate_holdings_materialization",
        start_month=start_month,
        end_month=end_month,
        target_candidate_holdings_fetch_count=fetch_count,
        target_candidate_holdings_row_count=row_count,
        task_key_path=str(task_key_path),
        trading_data_receipt_path=receipt_path,
        provider_calls=fetch_count,
    )


def write_summary(summary: TargetCandidateHoldingsMaterialization, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


__all__ = [
    "TARGET_CANDIDATE_HOLDINGS_SOURCE",
    "TARGET_CANDIDATE_HOLDINGS_SOURCE_MODULE",
    "TargetCandidateHoldingsMaterialization",
    "build_target_candidate_holdings_task_key",
    "materialize_target_candidate_holdings",
]

"""Layer 2 feature stage executor.

The Layer 2 feature stage owns both sector-context feature rows and the
source_02 target-candidate holdings source used by downstream Layer 3 input
preparation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, TextIO

from .control_plane import TaskSystemError
from .request_payloads import DEFAULT_STORAGE_ROOT
from .target_candidate_holdings import (
    DEFAULT_TRADING_DATA_ROOT,
    TargetCandidateHoldingsMaterialization,
    materialize_target_candidate_holdings,
)


@dataclass(frozen=True)
class LayerTwoFeatureStageSummary:
    """Combined Layer 2 feature/source materialization receipt."""

    contract_type: str
    month: str
    sector_feature_summary: Mapping[str, Any]
    target_candidate_holdings_summary: Mapping[str, Any]
    provider_calls: int
    model_activation_performed: bool = False
    broker_execution_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


def _run_layer_two_feature_command(
    *,
    month: str,
    trading_data_root: Path,
    output_dir: Path,
    write: bool,
) -> Mapping[str, Any]:
    command = ["python3", "-m", "data_feature.feature_02_sector_context.from_feed_artifacts", "--month", month]
    if not write:
        command.append("--dry-run")
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
    (log_dir / f"feature_02_sector_context_{month}.stdout.log").write_text(result.stdout, encoding="utf-8")
    (log_dir / f"feature_02_sector_context_{month}.stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise TaskSystemError(f"feature_02_sector_context generation failed: {result.stderr.strip() or result.stdout.strip()}")
    parsed = json.loads(result.stdout)
    return parsed if isinstance(parsed, Mapping) else {}


def execute_layer_two_feature_stage(
    *,
    month: str,
    manager_storage_root: Path = DEFAULT_STORAGE_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
    write: bool = False,
) -> LayerTwoFeatureStageSummary:
    if not manager_storage_root.is_absolute():
        manager_storage_root = Path.cwd() / manager_storage_root
    output_dir = manager_storage_root / "runtime" / "layer_02_sector_context" / "feature_generation" / month
    sector_feature_summary = _run_layer_two_feature_command(
        month=month,
        trading_data_root=trading_data_root,
        output_dir=output_dir,
        write=write,
    )
    holdings: TargetCandidateHoldingsMaterialization = materialize_target_candidate_holdings(
        start_month=month,
        end_month=month,
        manager_storage_root=manager_storage_root,
        trading_data_root=trading_data_root,
        run_id=f"layer_02_target_candidate_holdings_{month.replace('-', '_')}",
        write=write,
    )
    return LayerTwoFeatureStageSummary(
        contract_type="manager_layer_two_feature_stage",
        month=month,
        sector_feature_summary=sector_feature_summary,
        target_candidate_holdings_summary=holdings.summary_row(),
        provider_calls=holdings.provider_calls,
    )


def write_summary(summary: LayerTwoFeatureStageSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute Layer 2 feature generation and target-candidate holdings materialization.")
    parser.add_argument("--month", required=True)
    parser.add_argument("--manager-storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    parser.add_argument("--write", action="store_true", help="Persist feature_02 and source_02 outputs. Without this flag the command is a dry run.")
    args = parser.parse_args(argv)
    summary = execute_layer_two_feature_stage(
        month=args.month,
        manager_storage_root=args.manager_storage_root,
        trading_data_root=args.trading_data_root,
        write=args.write,
    )
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "LayerTwoFeatureStageSummary",
    "execute_layer_two_feature_stage",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

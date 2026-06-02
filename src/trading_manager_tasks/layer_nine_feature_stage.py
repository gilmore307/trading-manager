"""Layer 9 option-expression feature-stage adapter.

The Layer 9 option-expression feature stage has two valid paths:

* if the reviewed Layer 8 gate accepted a no-provider/no-active-target skip,
  feature generation is also a reviewed no-op because no source_05 option
  rows are required for deterministic no-option model rows;
* otherwise, after provider acquisition has populated source_05 for the current
  fold, the adapter delegates to trading-data's feature_09 SQL generator.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, TextIO

from .control_plane import TaskSystemError
from .request_payloads import DEFAULT_STORAGE_ROOT

DEFAULT_GATE_REVIEW_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "layer_09_option_expression" / "gate_review"
DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
FEATURE_STAGE_ID = "layer_09_option_expression.feature_generation"
DATA_ACQUISITION_STAGE_ID = "layer_09_option_expression.data_acquisition"


@dataclass(frozen=True)
class LayerNineFeatureStageSummary:
    """Result for the Layer 9 option-expression feature-generation adapter."""

    contract_type: str
    stage_id: str
    start_month: str
    end_month: str
    status: str
    mode: str
    receipt_path: str | None
    provider_calls: int = 0
    dispatch_performed: bool = False
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False
    command: tuple[str, ...] = ()
    return_code: int | None = None
    reason: str | None = None

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["command"] = list(self.command)
        return row


def _month_start(month: str) -> str:
    return f"{month}-01T00:00:00-05:00"


def _exclusive_month_start(month: str) -> str:
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number == 12:
        year += 1
        month_number = 1
    else:
        month_number += 1
    return f"{year:04d}-{month_number:02d}-01T00:00:00-05:00"


def _read_json(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise TaskSystemError(f"required Layer 8 gate review artifact is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TaskSystemError(f"Layer 8 gate review artifact must be a JSON object: {path}")
    return payload


def _gate_review_path(start_month: str, *, gate_review_root: Path) -> Path:
    return gate_review_root / f"layer_09_option_expression_gate_review_{start_month}.json"


def _write_skip_receipt(*, start_month: str, end_month: str, gate_review_path: Path, gate_review: Mapping[str, Any], output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    receipt_path = output_root / f"layer_09_option_expression_feature_generation_no_provider_skip_receipt_{start_month}.json"
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "contract_type": "component_completion_receipt",
        "manager_stage_id": FEATURE_STAGE_ID,
        "stage_type": "feature_generation",
        "status": "succeeded",
        "started_at": now,
        "completed_at": now,
        "runs": [
            {
                "run_id": f"layer_09_option_expression_feature_generation_no_provider_skip_{start_month}",
                "status": "succeeded",
                "output_refs": [str(gate_review_path)],
                "row_counts": {
                    "active_layer_8_request_candidates": int(gate_review.get("active_request_count") or 0),
                    "source_05_option_expression_rows_required": 0,
                    "feature_09_option_expression_rows_required": 0,
                },
            }
        ],
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "reason": (
            "Reviewed Layer 8 gate accepted no-provider/no-active-target skip; "
            "source_05 and feature_08 rows are not required before deterministic no-option model generation."
        ),
        "evidence_refs": [str(gate_review_path)],
        "start_month": start_month,
        "end_month": end_month,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path


def _write_missing_option_source_receipt(*, start_month: str, end_month: str, gate_review_path: Path, gate_review: Mapping[str, Any], output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    receipt_path = output_root / f"layer_09_option_expression_feature_generation_option_source_unavailable_receipt_{start_month}.json"
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = {
        "contract_type": "component_completion_receipt",
        "manager_stage_id": FEATURE_STAGE_ID,
        "stage_type": "feature_generation",
        "status": "failed",
        "started_at": now,
        "completed_at": now,
        "runs": [
            {
                "run_id": f"layer_09_option_expression_feature_generation_option_source_unavailable_{start_month}",
                "status": "failed",
                "output_refs": [str(gate_review_path)],
                "row_counts": {
                    "active_layer_8_request_candidates": int(gate_review.get("active_request_count") or 0),
                    "source_05_option_expression_rows_available": 0,
                    "feature_09_option_expression_rows_generated": 0,
                },
            }
        ],
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "reason": (
            "Layer 8 produced active target-chain rows, but the current fold has no "
            "source_05/m09 option-expression source rows. Layer 9 feature generation "
            "must wait for reviewed option source acquisition instead of continuing "
            "with optionable_chain_missing fallback."
        ),
        "evidence_refs": [str(gate_review_path), "sql:trading_data.m09_option_expression_data_acquisition:coverage_missing"],
        "start_month": start_month,
        "end_month": end_month,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt_path


def _database_url(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if os.environ.get("OPENCLAW_DATABASE_URL"):
        return os.environ["OPENCLAW_DATABASE_URL"]
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise TaskSystemError(f"database URL not supplied and {DEFAULT_DB_URL_FILE} does not exist")


def option_source_table_exists(*, database_url: str | None = None, source_schema: str = "trading_data", source_table: str = "m09_option_expression_data_acquisition") -> bool:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT to_regclass(%s) AS table_ref", (f"{source_schema}.{source_table}",))
            row = cursor.fetchone()
            return bool(row and row.get("table_ref"))


def option_source_row_count(
    *,
    start_month: str,
    end_month: str,
    database_url: str | None = None,
    source_schema: str = "trading_data",
    source_table: str = "m09_option_expression_data_acquisition",
) -> int:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    if not option_source_table_exists(database_url=database_url, source_schema=source_schema, source_table=source_table):
        return 0
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*) AS row_count
                FROM {source_schema}.{source_table}
                WHERE snapshot_time::timestamptz >= %s::timestamptz
                  AND snapshot_time::timestamptz < %s::timestamptz
                """,
                (_month_start(start_month), _exclusive_month_start(end_month)),
            )
            row = cursor.fetchone()
            return int((row or {}).get("row_count") or 0)


def execute_layer_nine_feature_stage(
    *,
    start_month: str,
    end_month: str,
    gate_review_root: Path = DEFAULT_GATE_REVIEW_ROOT,
    output_root: Path = DEFAULT_GATE_REVIEW_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
) -> LayerNineFeatureStageSummary:
    """Execute Layer 9 option-expression feature generation through the correct reviewed path."""

    review_path = _gate_review_path(start_month, gate_review_root=gate_review_root)
    review = _read_json(review_path)
    if review.get("contract_type") != "manager_layer_09_option_expression_gate_review":
        raise TaskSystemError(f"unsupported Layer 8 gate review contract_type: {review_path}")
    if review.get("status") == "no_provider_skip_accepted" and int(review.get("active_request_count") or 0) == 0:
        receipt_path = _write_skip_receipt(
            start_month=start_month,
            end_month=end_month,
            gate_review_path=review_path,
            gate_review=review,
            output_root=output_root,
        )
        return LayerNineFeatureStageSummary(
            contract_type="manager_layer_09_option_expression_feature_generation_stage",
            stage_id=FEATURE_STAGE_ID,
            start_month=start_month,
            end_month=end_month,
            status="succeeded",
            mode="no_provider_no_option_skip",
            receipt_path=str(receipt_path),
            reason="no active Layer 8 target chain; feature generation is a reviewed no-op",
        )
    if review.get("status") == "provider_acquisition_ready" and option_source_row_count(start_month=start_month, end_month=end_month) <= 0:
        receipt_path = _write_missing_option_source_receipt(
            start_month=start_month,
            end_month=end_month,
            gate_review_path=review_path,
            gate_review=review,
            output_root=output_root,
        )
        return LayerNineFeatureStageSummary(
            contract_type="manager_layer_09_option_expression_feature_generation_stage",
            stage_id=FEATURE_STAGE_ID,
            start_month=start_month,
            end_month=end_month,
            status="failed",
            mode="option_source_coverage_missing",
            receipt_path=str(receipt_path),
            reason="current fold option source coverage is missing; run Layer 9 source acquisition before feature generation",
        )

    command = (
        "python3",
        "-m",
        "data_feature.feature_09_option_expression",
        "--source-start",
        _month_start(start_month),
        "--source-end",
        _exclusive_month_start(end_month),
        "--run-id",
        f"feature_09_option_expression_{start_month}",
    )
    result = subprocess.run(
        list(command),
        cwd=trading_data_root,
        env={**os.environ, "PYTHONPATH": str(trading_data_root / "src")},
        text=True,
        capture_output=True,
        check=False,
    )
    status = "succeeded" if result.returncode == 0 else "failed"
    if result.stdout:
        print(result.stdout, end="", file=sys.stderr)
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return LayerNineFeatureStageSummary(
        contract_type="manager_layer_09_option_expression_feature_generation_stage",
        stage_id=FEATURE_STAGE_ID,
        start_month=start_month,
        end_month=end_month,
        status=status,
        mode="trading_data_feature_08_sql_generation",
        receipt_path=None,
        command=command,
        return_code=result.returncode,
        reason=None if result.returncode == 0 else "trading-data feature_08 generator returned non-zero status",
    )


def write_layer_nine_feature_stage_summary(summary: LayerNineFeatureStageSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute Layer 9 option-expression feature generation with reviewed no-provider skip support.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--gate-review-root", type=Path, default=DEFAULT_GATE_REVIEW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_GATE_REVIEW_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    args = parser.parse_args(argv)
    summary = execute_layer_nine_feature_stage(
        start_month=args.start_month,
        end_month=args.end_month,
        gate_review_root=args.gate_review_root,
        output_root=args.output_root,
        trading_data_root=args.trading_data_root,
    )
    write_layer_nine_feature_stage_summary(summary, output=sys.stdout)
    return 0 if summary.status == "succeeded" else 1


__all__ = [
    "FEATURE_STAGE_ID",
    "LayerNineFeatureStageSummary",
    "execute_layer_nine_feature_stage",
    "option_source_row_count",
    "option_source_table_exists",
    "write_layer_nine_feature_stage_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

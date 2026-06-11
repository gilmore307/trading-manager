"""M05 option-expression feature-stage adapter.

M05 does not own provider acquisition. It derives option-expression
features from the shared ``option_chain_state_source`` cache that is prepared
before option-expression feature generation.
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

DEFAULT_RECEIPT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_05_option_expression" / "feature_generation"
DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_PYTHON_EXECUTABLE = Path("/root/projects/trading-manager/.venv/bin/python")
FEATURE_STAGE_ID = "model_05_option_expression.feature_generation"
SOURCE_TABLE = "option_chain_state_source"
FEATURE_TABLE = "m05_option_expression_feature_generation"
FEATURE_STAGE_CONTRACT_TYPE = "manager_model_05_option_expression_feature_generation_stage"


@dataclass(frozen=True)
class M05OptionExpressionFeatureStageSummary:
    """Result for the M05 option-expression feature-generation adapter."""

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


def _write_missing_option_source_receipt(*, start_month: str, end_month: str, output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    receipt_path = output_root / f"model_05_option_expression_feature_generation_option_source_unavailable_receipt_{start_month}.json"
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
                "run_id": f"model_05_option_expression_feature_generation_option_source_unavailable_{start_month}",
                "status": "failed",
                "output_refs": ["sql:trading_data.option_chain_state_source:coverage_missing"],
                "row_counts": {
                    "option_chain_state_source_rows_available": 0,
                    "m05_option_expression_feature_generation_rows_generated": 0,
                },
            }
        ],
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "reason": (
            "The current fold has no option_chain_state_source rows. M05 feature generation "
            "must wait for shared option-chain source acquisition instead of continuing with fallback rows."
        ),
        "evidence_refs": ["sql:trading_data.option_chain_state_source:coverage_missing"],
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


def option_source_table_exists(*, database_url: str | None = None, source_schema: str = "trading_data", source_table: str = SOURCE_TABLE) -> bool:
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
    target_symbol: str | None = None,
    database_url: str | None = None,
    source_schema: str = "trading_data",
    source_table: str = SOURCE_TABLE,
) -> int:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    if not option_source_table_exists(database_url=database_url, source_schema=source_schema, source_table=source_table):
        return 0
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            where = [
                "snapshot_time >= %s",
                "snapshot_time < %s",
            ]
            params: list[str] = [_month_start(start_month), _exclusive_month_start(end_month)]
            if target_symbol:
                where.append("underlying = %s")
                params.append(target_symbol.strip().upper())
            cursor.execute(
                f"""
                SELECT COUNT(*) AS row_count
                FROM {source_schema}.{source_table}
                WHERE {" AND ".join(where)}
                """,
                params,
            )
            row = cursor.fetchone()
            return int((row or {}).get("row_count") or 0)


def feature_row_count(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str | None = None,
    database_url: str | None = None,
    target_schema: str = "trading_data",
    target_table: str = FEATURE_TABLE,
) -> int:
    import psycopg  # type: ignore
    from psycopg.rows import dict_row  # type: ignore

    if not option_source_table_exists(database_url=database_url, source_schema=target_schema, source_table=target_table):
        return 0
    with psycopg.connect(_database_url(database_url), row_factory=dict_row) as conn:
        with conn.cursor() as cursor:
            where = [
                "snapshot_time >= %s",
                "snapshot_time < %s",
            ]
            params: list[str] = [_month_start(start_month), _exclusive_month_start(end_month)]
            if target_symbol:
                where.append("underlying = %s")
                params.append(target_symbol.strip().upper())
            cursor.execute(
                f"""
                SELECT COUNT(*) AS row_count
                FROM {target_schema}.{target_table}
                WHERE {" AND ".join(where)}
                """,
                params,
            )
            row = cursor.fetchone()
            return int((row or {}).get("row_count") or 0)


def execute_m05_option_expression_feature_stage(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str | None = None,
    output_root: Path = DEFAULT_RECEIPT_ROOT,
    trading_data_root: Path = DEFAULT_TRADING_DATA_ROOT,
) -> M05OptionExpressionFeatureStageSummary:
    """Execute M05 option-expression feature generation through the reviewed path."""

    source_rows = option_source_row_count(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
    if source_rows <= 0:
        receipt_path = _write_missing_option_source_receipt(
            start_month=start_month,
            end_month=end_month,
            output_root=output_root,
        )
        return M05OptionExpressionFeatureStageSummary(
            contract_type=FEATURE_STAGE_CONTRACT_TYPE,
            stage_id=FEATURE_STAGE_ID,
            start_month=start_month,
            end_month=end_month,
            status="failed",
            mode="option_source_coverage_missing",
            receipt_path=str(receipt_path),
            reason="current fold option source coverage is missing; run shared option-chain source acquisition before feature generation",
        )
    existing_feature_rows = feature_row_count(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
    if existing_feature_rows >= source_rows:
        return M05OptionExpressionFeatureStageSummary(
            contract_type=FEATURE_STAGE_CONTRACT_TYPE,
            stage_id=FEATURE_STAGE_ID,
            start_month=start_month,
            end_month=end_month,
            status="succeeded",
            mode="existing_target_feature_coverage_reused",
            receipt_path=None,
            reason=f"existing M05 feature coverage reused: {existing_feature_rows}/{source_rows} rows",
        )

    python_executable = str(DEFAULT_PYTHON_EXECUTABLE if DEFAULT_PYTHON_EXECUTABLE.exists() else Path(sys.executable))
    command = (
        python_executable,
        "-m",
        "data_feature.m05_option_expression_feature_generation",
        "--source-table",
        SOURCE_TABLE,
        "--source-start",
        _month_start(start_month),
        "--source-end",
        _exclusive_month_start(end_month),
        "--run-id",
        f"m05_option_expression_feature_generation_{start_month}",
    )
    if target_symbol:
        command = (*command, "--underlying", target_symbol)
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
    return M05OptionExpressionFeatureStageSummary(
        contract_type=FEATURE_STAGE_CONTRACT_TYPE,
        stage_id=FEATURE_STAGE_ID,
        start_month=start_month,
        end_month=end_month,
        status=status,
        mode="trading_data_m05_sql_generation_from_shared_option_source",
        receipt_path=None,
        command=command,
        return_code=result.returncode,
        reason=None if result.returncode == 0 else "trading-data M05 feature generator returned non-zero status",
    )


def write_m05_option_expression_feature_stage_summary(summary: M05OptionExpressionFeatureStageSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute M05 option-expression feature generation with reviewed no-provider skip support.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--target-symbol")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_RECEIPT_ROOT)
    parser.add_argument("--trading-data-root", type=Path, default=DEFAULT_TRADING_DATA_ROOT)
    args = parser.parse_args(argv)
    summary = execute_m05_option_expression_feature_stage(
        start_month=args.start_month,
        end_month=args.end_month,
        target_symbol=args.target_symbol,
        output_root=args.output_root,
        trading_data_root=args.trading_data_root,
    )
    write_m05_option_expression_feature_stage_summary(summary, output=sys.stdout)
    return 0 if summary.status == "succeeded" else 1


__all__ = [
    "FEATURE_STAGE_ID",
    "FEATURE_STAGE_CONTRACT_TYPE",
    "FEATURE_TABLE",
    "M05OptionExpressionFeatureStageSummary",
    "execute_m05_option_expression_feature_stage",
    "feature_row_count",
    "option_source_row_count",
    "option_source_table_exists",
    "write_m05_option_expression_feature_stage_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

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
from typing import Any, Mapping, Sequence, TextIO

from .control_plane import TaskSystemError
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_RECEIPT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "model_05_option_expression" / "feature_generation"
DEFAULT_TRADING_DATA_ROOT = Path("/root/projects/trading-data")
DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_PYTHON_EXECUTABLE = Path("/root/projects/trading-manager/.venv/bin/python")
FEATURE_STAGE_ID = "model_05_option_expression.feature_generation"
SOURCE_TABLE = "option_chain_state_source"
FEATURE_TABLE = "model_05_option_expression_feature_generation"
FEATURE_STAGE_CONTRACT_TYPE = "manager_model_05_option_expression_feature_generation_stage"
SOURCE_UNAVAILABLE_SNAPSHOT_TYPE = "source_unavailable"
SOURCE_UNAVAILABLE_OPTION_SYMBOL = "__OPTION_SOURCE_UNAVAILABLE__"


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


def _write_source_unavailable_receipt(
    *,
    start_month: str,
    end_month: str,
    output_root: Path,
    target_symbol: str | None,
    marker_count: int,
    mode: str,
) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    receipt_path = output_root / f"model_05_option_expression_feature_generation_source_unavailable_receipt_{start_month}.json"
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
                "run_id": f"model_05_option_expression_feature_generation_source_unavailable_{start_month}",
                "status": "succeeded",
                "output_refs": [f"sql:trading_data.{FEATURE_TABLE}:source_unavailable"],
                "row_counts": {
                    "option_chain_state_source_rows_available": 0,
                    "m05_option_expression_source_unavailable_rows": marker_count,
                },
            }
        ],
        "provider_calls": 0,
        "dispatch_performed": False,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "reason": "M05 feature generation recorded source_unavailable sentinels for reviewed zero-row option-chain source signals.",
        "evidence_refs": [f"sql:trading_data.{FEATURE_TABLE}:source_unavailable"],
        "target_symbol": target_symbol.strip().upper() if target_symbol and target_symbol.strip() else None,
        "start_month": start_month,
        "end_month": end_month,
        "mode": mode,
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


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _successful_zero_row_signal_times(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str | None,
    source_root: Path | None = None,
) -> tuple[str, ...]:
    target = target_symbol.strip().upper() if target_symbol and target_symbol.strip() else None
    if not target:
        return ()
    root = (source_root or data_storage_root()) / "model_05_option_expression" / SOURCE_TABLE / start_month
    if not root.exists():
        return ()
    start = _parse_timestamp(_month_start(start_month))
    end = _parse_timestamp(_exclusive_month_start(end_month))
    if start is None or end is None:
        return ()
    signal_times: set[str] = set()
    for receipt_path in sorted(root.glob("mgrreq_option_chain_window_*/completion_receipt.json")):
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        runs = [run for run in receipt.get("runs") or [] if isinstance(run, Mapping)]
        for run in runs:
            if str(run.get("status") or "").lower() not in {"succeeded", "success", "completed", "complete", "ready"}:
                continue
            if "trading_data.option_chain_state_source" not in {str(output) for output in run.get("outputs") or []}:
                continue
            row_counts = run.get("row_counts") if isinstance(run.get("row_counts"), Mapping) else {}
            try:
                source_rows = int(row_counts.get("option_chain_state_source") or 0)
            except (TypeError, ValueError):
                source_rows = 0
            if source_rows != 0:
                continue
            fetch = (run.get("steps") or {}).get("fetch") if isinstance(run.get("steps"), Mapping) else None
            details = fetch.get("details") if isinstance(fetch, Mapping) and isinstance(fetch.get("details"), Mapping) else {}
            if str(details.get("underlying") or "").strip().upper() != target:
                continue
            snapshot = _parse_timestamp(details.get("snapshot_time"))
            if snapshot is None or not (start <= snapshot < end):
                continue
            signal_times.add(snapshot.isoformat())
    return tuple(sorted(signal_times))


def source_unavailable_marker_count(
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
                "snapshot_type = %s",
            ]
            params: list[str] = [_month_start(start_month), _exclusive_month_start(end_month), SOURCE_UNAVAILABLE_SNAPSHOT_TYPE]
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


def persist_source_unavailable_markers(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str,
    signal_times: Sequence[str],
    database_url: str | None = None,
    target_schema: str = "trading_data",
    target_table: str = FEATURE_TABLE,
) -> int:
    if not signal_times:
        return 0
    import psycopg  # type: ignore

    target = target_symbol.strip().upper()
    run_id = "model_05_option_expression_source_unavailable_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    with psycopg.connect(_database_url(database_url)) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{target_schema}"')
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS "{target_schema}"."{target_table}" (
                  "run_id" TEXT NOT NULL,
                  "source_run_ref" TEXT NOT NULL,
                  "underlying" TEXT NOT NULL,
                  "snapshot_time" TIMESTAMPTZ NOT NULL,
                  "snapshot_type" TEXT NOT NULL,
                  "option_symbol" TEXT NOT NULL,
                  "feature_payload_json" JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                  "feature_quality_diagnostics" JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                  PRIMARY KEY ("underlying", "snapshot_time", "snapshot_type", "option_symbol")
                )
                """
            )
            for signal_time in signal_times:
                cursor.execute(
                    f"""
                    INSERT INTO "{target_schema}"."{target_table}" (
                      "run_id", "source_run_ref", "underlying", "snapshot_time", "snapshot_type",
                      "option_symbol", "feature_payload_json", "feature_quality_diagnostics"
                    )
                    VALUES (%s, %s, %s, %s::timestamptz, %s, %s, %s::jsonb, %s::jsonb)
                    ON CONFLICT ("underlying", "snapshot_time", "snapshot_type", "option_symbol") DO UPDATE SET
                      "run_id" = EXCLUDED."run_id",
                      "source_run_ref" = EXCLUDED."source_run_ref",
                      "feature_payload_json" = EXCLUDED."feature_payload_json",
                      "feature_quality_diagnostics" = EXCLUDED."feature_quality_diagnostics"
                    """,
                    (
                        run_id,
                        "model_05_option_expression.option_chain_data_acquisition",
                        target,
                        signal_time,
                        SOURCE_UNAVAILABLE_SNAPSHOT_TYPE,
                        SOURCE_UNAVAILABLE_OPTION_SYMBOL,
                        json.dumps(
                            {
                                "option_surface_status": "option_source_unavailable",
                                "asset_expression_route": "option_expression_unfilled",
                                "signal_source": "model_05_option_expression.option_chain_data_acquisition",
                                "start_month": start_month,
                                "end_month": end_month,
                            },
                            sort_keys=True,
                        ),
                        json.dumps(
                            {
                                "has_required_fields": False,
                                "source_unavailable": True,
                                "point_in_time_clock": "snapshot_time",
                                "source_table": SOURCE_TABLE,
                            },
                            sort_keys=True,
                        ),
                    ),
                )
    return len(signal_times)


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
        signal_times = _successful_zero_row_signal_times(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
        existing_markers = source_unavailable_marker_count(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
        if signal_times or existing_markers:
            marker_count = existing_markers
            mode = "existing_source_unavailable_sentinels_reused"
            if signal_times and existing_markers < len(signal_times):
                marker_count = persist_source_unavailable_markers(
                    start_month=start_month,
                    end_month=end_month,
                    target_symbol=target_symbol or "",
                    signal_times=signal_times,
                )
                mode = "source_unavailable_sentinels_written"
            receipt_path = _write_source_unavailable_receipt(
                start_month=start_month,
                end_month=end_month,
                output_root=output_root,
                target_symbol=target_symbol,
                marker_count=marker_count,
                mode=mode,
            )
            return M05OptionExpressionFeatureStageSummary(
                contract_type=FEATURE_STAGE_CONTRACT_TYPE,
                stage_id=FEATURE_STAGE_ID,
                start_month=start_month,
                end_month=end_month,
                status="succeeded",
                mode=mode,
                receipt_path=str(receipt_path),
                reason=f"M05 source unavailable sentinels available: {marker_count}",
            )
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
    "persist_source_unavailable_markers",
    "source_unavailable_marker_count",
    "write_m05_option_expression_feature_stage_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

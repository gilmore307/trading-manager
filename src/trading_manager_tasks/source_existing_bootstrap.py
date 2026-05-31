"""Bootstrap workflow state from already-existing historical source data.

The historical scheduler must not confuse a missing manager request/receipt row with
missing source data. After a clean generated-state reset, durable source tables and
preserved component artifacts may still contain valid historical inputs. This module
runs at scheduler startup, inspects those source surfaces, and seeds month-scoped
workflow state so provider acquisition stages are skipped when source coverage is
already present.

It never calls providers, never activates models, and never touches broker/account
state. Its only write-mode mutation is manager runtime JSON state/report files.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence, TextIO

from .dataset_evidence import database_url as resolve_database_url
from .model_training_state import advance_workflow_state, workflow_state_path_for_month
from .monthly_backfill import LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER, Month, load_market_regime_universe
from .request_payloads import DEFAULT_STORAGE_ROOT
from .storage_paths import data_storage_root

DEFAULT_COMPONENT_STORAGE_ROOT = data_storage_root()
DEFAULT_BOOTSTRAP_REPORT_ROOT = DEFAULT_STORAGE_ROOT / "runtime" / "source_existing_bootstrap"
SOURCE_TIMEZONE = "America/New_York"

STAGE_SOURCE_TABLES: Mapping[str, str] = {
    "layer_01_market_regime.data_acquisition": "trading_data.m01_market_regime_data_acquisition",
    "layer_02_sector_context.data_acquisition": "trading_data.m01_market_regime_data_acquisition",
    "layer_03_target_state_vector.data_acquisition": "trading_data.source_03_target_state",
}


@dataclass(frozen=True)
class SourceStageCoverage:
    """Existing-source coverage for one workflow data-acquisition stage/month."""

    contract_type: str
    stage_id: str
    source_table: str
    month: str
    expected_symbols: tuple[str, ...]
    covered_symbols: tuple[str, ...]
    not_applicable_symbols: tuple[str, ...]
    row_count: int
    status: str
    reason: str

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["expected_symbols"] = list(self.expected_symbols)
        row["covered_symbols"] = list(self.covered_symbols)
        row["not_applicable_symbols"] = list(self.not_applicable_symbols)
        return row


@dataclass(frozen=True)
class EventSourceCoverage:
    """Existing Layer 9 source coverage observed at service bootstrap."""

    contract_type: str
    source_table: str
    month: str
    row_count: int
    status: str
    reason: str

    @property
    def ready(self) -> bool:
        return self.status == "ready"

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceExistingBootstrapSummary:
    """Startup bootstrap summary for existing historical source data."""

    contract_type: str
    started_utc: str
    completed_utc: str
    start_month: str
    end_month: str
    selected_target_symbol: str | None
    write: bool
    bootstrapped_months: tuple[str, ...]
    workflow_state_paths: tuple[str, ...]
    coverage_report_paths: tuple[str, ...]
    source_stage_coverages: tuple[SourceStageCoverage, ...]
    event_source_coverages: tuple[EventSourceCoverage, ...]
    warnings: tuple[str, ...]
    provider_calls: int = 0
    model_activation_performed: bool = False
    broker_execution_performed: bool = False
    storage_lifecycle_mutation_performed: bool = False

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["bootstrapped_months"] = list(self.bootstrapped_months)
        row["workflow_state_paths"] = list(self.workflow_state_paths)
        row["coverage_report_paths"] = list(self.coverage_report_paths)
        row["source_stage_coverages"] = [item.summary_row() for item in self.source_stage_coverages]
        row["event_source_coverages"] = [item.summary_row() for item in self.event_source_coverages]
        row["warnings"] = list(self.warnings)
        return row


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def iter_months(start_month: str, end_month: str) -> tuple[str, ...]:
    current = Month.parse(start_month)
    end = Month.parse(end_month)
    months: list[str] = []
    while current <= end:
        months.append(str(current))
        current = current.next()
    return tuple(months)


def _month_start_date(month: str) -> str:
    return Month.parse(month).start_date.isoformat()


def _month_end_date(month: str) -> str:
    return Month.parse(month).exclusive_end_date.isoformat()


def _symbols_for_model_layer(model_layer: str) -> tuple[str, ...]:
    return tuple(sorted(member.symbol.upper() for member in load_market_regime_universe(model_layers=(model_layer,))))


def _source_stage_coverage(
    *,
    stage_id: str,
    source_table: str,
    month: str,
    expected_symbols: Sequence[str],
    counts_by_symbol: Mapping[str, int],
    first_seen_month_by_symbol: Mapping[str, str] | None = None,
) -> SourceStageCoverage:
    expected = tuple(sorted({symbol.upper() for symbol in expected_symbols if symbol}))
    covered = tuple(symbol for symbol in expected if int(counts_by_symbol.get(symbol, 0)) > 0)
    first_seen = {symbol.upper(): value for symbol, value in dict(first_seen_month_by_symbol or {}).items()}
    not_applicable = tuple(
        symbol
        for symbol in expected
        if symbol not in covered and first_seen.get(symbol) is not None and month < str(first_seen[symbol])
    )
    row_count = sum(int(counts_by_symbol.get(symbol, 0)) for symbol in expected)
    terminal_count = len(covered) + len(not_applicable)
    if expected and terminal_count == len(expected):
        status = "ready"
        if not_applicable:
            reason = (
                f"existing source rows cover {len(covered)}/{len(expected)} required symbols and "
                f"{len(not_applicable)} symbols are before first observed source month; provider acquisition may be skipped"
            )
        else:
            reason = f"existing source rows cover {len(covered)}/{len(expected)} required symbols; provider acquisition may be skipped"
    elif covered or not_applicable:
        status = "partial"
        reason = (
            f"existing source rows cover {len(covered)}/{len(expected)} required symbols plus "
            f"{len(not_applicable)} pre-inception/not-applicable symbols; provider acquisition remains blocked"
        )
    else:
        status = "missing"
        reason = f"no existing source rows found for required symbols in {month}; provider acquisition remains eligible"
    return SourceStageCoverage(
        contract_type="manager_source_existing_stage_coverage",
        stage_id=stage_id,
        source_table=source_table,
        month=month,
        expected_symbols=expected,
        covered_symbols=covered,
        not_applicable_symbols=not_applicable,
        row_count=row_count,
        status=status,
        reason=reason,
    )


def _event_source_coverage(*, month: str, row_count: int) -> EventSourceCoverage:
    status = "ready" if row_count > 0 else "missing"
    reason = (
        f"existing m10_event_risk_governor_data_acquisition rows found for {month}; Layer 10 event-risk lane can reuse source evidence"
        if row_count > 0
        else f"no m10_event_risk_governor_data_acquisition rows found for {month}; Layer 10 event-risk lane has no existing source evidence"
    )
    return EventSourceCoverage(
        contract_type="manager_source_existing_event_coverage",
        source_table="trading_data.m10_event_risk_governor_data_acquisition",
        month=month,
        row_count=int(row_count),
        status=status,
        reason=reason,
    )


def build_source_coverages_from_counts(
    *,
    months: Sequence[str],
    m01_counts: Mapping[str, Mapping[str, int]],
    source_03_counts: Mapping[str, Mapping[str, int]],
    source_10_counts: Mapping[str, int],
    selected_target_symbol: str | None,
    m01_first_seen_month_by_symbol: Mapping[str, str] | None = None,
) -> tuple[tuple[SourceStageCoverage, ...], tuple[EventSourceCoverage, ...], tuple[str, ...]]:
    """Build stage coverage objects from already-fetched monthly source counts."""

    warnings: list[str] = []
    target_symbol = selected_target_symbol.strip().upper() if selected_target_symbol else None
    layer_one_symbols = _symbols_for_model_layer(LAYER_ONE_MODEL_LAYER)
    layer_two_symbols = _symbols_for_model_layer(LAYER_TWO_MODEL_LAYER)
    stage_coverages: list[SourceStageCoverage] = []
    event_coverages: list[EventSourceCoverage] = []
    for month in months:
        m01_month = {symbol.upper(): int(count) for symbol, count in dict(m01_counts.get(month, {})).items()}
        stage_coverages.append(
            _source_stage_coverage(
                stage_id="layer_01_market_regime.data_acquisition",
                source_table=STAGE_SOURCE_TABLES["layer_01_market_regime.data_acquisition"],
                month=month,
                expected_symbols=layer_one_symbols,
                counts_by_symbol=m01_month,
                first_seen_month_by_symbol=m01_first_seen_month_by_symbol,
            )
        )
        stage_coverages.append(
            _source_stage_coverage(
                stage_id="layer_02_sector_context.data_acquisition",
                source_table=STAGE_SOURCE_TABLES["layer_02_sector_context.data_acquisition"],
                month=month,
                expected_symbols=layer_two_symbols,
                counts_by_symbol=m01_month,
                first_seen_month_by_symbol=m01_first_seen_month_by_symbol,
            )
        )
        if target_symbol:
            source_03_month = {symbol.upper(): int(count) for symbol, count in dict(source_03_counts.get(month, {})).items()}
            stage_coverages.append(
                _source_stage_coverage(
                    stage_id="layer_03_target_state_vector.data_acquisition",
                    source_table=STAGE_SOURCE_TABLES["layer_03_target_state_vector.data_acquisition"],
                    month=month,
                    expected_symbols=(target_symbol,),
                    counts_by_symbol=source_03_month,
                )
            )
        else:
            warnings.append("selected_target_symbol missing; source_03_target_state bootstrap was skipped")
        event_coverages.append(_event_source_coverage(month=month, row_count=int(source_10_counts.get(month, 0))))
    return tuple(stage_coverages), tuple(event_coverages), tuple(dict.fromkeys(warnings))


def _fetch_source_counts_from_database(
    *,
    database_url: str,
    start_month: str,
    end_month: str,
    selected_target_symbol: str | None,
) -> tuple[dict[str, dict[str, int]], dict[str, dict[str, int]], dict[str, int], dict[str, str], tuple[str, ...]]:
    """Fetch monthly source row counts from PostgreSQL."""

    import psycopg
    from psycopg.rows import dict_row

    warnings: list[str] = []
    start_date = _month_start_date(start_month)
    end_date = _month_end_date(end_month)
    m01: dict[str, dict[str, int]] = {}
    source_03: dict[str, dict[str, int]] = {}
    source_10: dict[str, int] = {}
    m01_first_seen: dict[str, str] = {}
    target = selected_target_symbol.strip().upper() if selected_target_symbol else None

    def table_exists(cursor: Any, table_ref: str) -> bool:
        cursor.execute("SELECT to_regclass(%s) AS table_ref", [table_ref])
        return cursor.fetchone()["table_ref"] is not None

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            if table_exists(cursor, "trading_data.m01_market_regime_data_acquisition"):
                cursor.execute(
                    f"""
                    SELECT
                      to_char(date_trunc('month', timestamp AT TIME ZONE %s), 'YYYY-MM') AS month,
                      upper(symbol) AS symbol,
                      count(*)::BIGINT AS row_count
                    FROM trading_data.m01_market_regime_data_acquisition
                    WHERE timestamp >= (%s::date AT TIME ZONE %s)
                      AND timestamp < (%s::date AT TIME ZONE %s)
                    GROUP BY 1, 2
                    """,
                    [SOURCE_TIMEZONE, start_date, SOURCE_TIMEZONE, end_date, SOURCE_TIMEZONE],
                )
                for row in cursor.fetchall():
                    m01.setdefault(str(row["month"]), {})[str(row["symbol"])] = int(row["row_count"])
                cursor.execute(
                    f"""
                    SELECT
                      upper(symbol) AS symbol,
                      to_char(date_trunc('month', min(timestamp) AT TIME ZONE %s), 'YYYY-MM') AS first_month
                    FROM trading_data.m01_market_regime_data_acquisition
                    GROUP BY 1
                    """,
                    [SOURCE_TIMEZONE],
                )
                for row in cursor.fetchall():
                    m01_first_seen[str(row["symbol"])] = str(row["first_month"])
            else:
                warnings.append("missing table trading_data.m01_market_regime_data_acquisition")

            if table_exists(cursor, "trading_data.source_03_target_state") and target:
                cursor.execute(
                    f"""
                    SELECT
                      to_char(date_trunc('month', timestamp AT TIME ZONE %s), 'YYYY-MM') AS month,
                      upper(symbol) AS symbol,
                      count(*)::BIGINT AS row_count
                    FROM trading_data.source_03_target_state
                    WHERE timestamp >= (%s::date AT TIME ZONE %s)
                      AND timestamp < (%s::date AT TIME ZONE %s)
                      AND upper(symbol) = %s
                    GROUP BY 1, 2
                    """,
                    [SOURCE_TIMEZONE, start_date, SOURCE_TIMEZONE, end_date, SOURCE_TIMEZONE, target],
                )
                for row in cursor.fetchall():
                    source_03.setdefault(str(row["month"]), {})[str(row["symbol"])] = int(row["row_count"])
            elif not target:
                warnings.append("selected_target_symbol missing; source_03_target_state database scan skipped")
            else:
                warnings.append("missing table trading_data.source_03_target_state")

            if table_exists(cursor, "trading_data.m10_event_risk_governor_data_acquisition"):
                cursor.execute(
                    f"""
                    SELECT
                      to_char(date_trunc('month', event_time AT TIME ZONE %s), 'YYYY-MM') AS month,
                      count(*)::BIGINT AS row_count
                    FROM trading_data.m10_event_risk_governor_data_acquisition
                    WHERE event_time >= (%s::date AT TIME ZONE %s)
                      AND event_time < (%s::date AT TIME ZONE %s)
                    GROUP BY 1
                    """,
                    [SOURCE_TIMEZONE, start_date, SOURCE_TIMEZONE, end_date, SOURCE_TIMEZONE],
                )
                for row in cursor.fetchall():
                    source_10[str(row["month"])] = int(row["row_count"])
            else:
                warnings.append("missing table trading_data.m10_event_risk_governor_data_acquisition")
    return m01, source_03, source_10, m01_first_seen, tuple(warnings)


def _coverage_report_path(*, report_root: Path, month: str, stage_id: str) -> Path:
    return report_root / month / f"{stage_id.replace('.', '_')}.json"


def _write_stage_coverage_report(path: Path, coverage: SourceStageCoverage) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    expected_count = len(coverage.expected_symbols)
    ready_count = len(coverage.covered_symbols) if coverage.ready else 0
    accepted_not_applicable_count = len(coverage.not_applicable_symbols) if coverage.ready else 0
    pending_count = max(expected_count - ready_count - accepted_not_applicable_count, 0)
    report = {
        "contract_type": "manager_stage_coverage",
        "stage_id": coverage.stage_id,
        "start_month": coverage.month,
        "end_month": coverage.month,
        "expected_count": expected_count,
        "observed_count": len(coverage.covered_symbols) + len(coverage.not_applicable_symbols),
        "ready_count": ready_count,
        "failed_count": 0,
        "pending_count": pending_count,
        "accepted_failed_count": accepted_not_applicable_count,
        "status": "ready" if coverage.ready else "blocked",
        "can_unlock_downstream": coverage.ready,
        "ready_request_ids": [f"source_existing:{coverage.source_table}:{coverage.month}:{symbol}" for symbol in coverage.covered_symbols],
        "failed_request_ids": [],
        "accepted_failed_request_ids": [
            f"source_existing:not_applicable_before_first_seen:{coverage.source_table}:{coverage.month}:{symbol}"
            for symbol in coverage.not_applicable_symbols
        ],
        "pending_request_ids": [
            f"source_existing:{coverage.source_table}:{coverage.month}:{symbol}"
            for symbol in coverage.expected_symbols
            if symbol not in set(coverage.covered_symbols) and symbol not in set(coverage.not_applicable_symbols)
        ],
        "accepted_failure_refs": ["source_existing_bootstrap:first_observed_source_month"] if coverage.not_applicable_symbols else [],
        "reason": coverage.reason,
        "provider_calls": 0,
        "model_activation_performed": False,
        "broker_execution_performed": False,
        "storage_lifecycle_mutation_performed": False,
        "source_existing_bootstrap": coverage.summary_row(),
    }
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_source_existing_bootstrap(
    *,
    start_month: str = "2016-01",
    end_month: str = "2016-01",
    selected_target_symbol: str | None = None,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    report_root: Path | None = None,
    database_url: str | None = None,
    write: bool = False,
    m01_counts: Mapping[str, Mapping[str, int]] | None = None,
    source_03_counts: Mapping[str, Mapping[str, int]] | None = None,
    source_10_counts: Mapping[str, int] | None = None,
    m01_first_seen_month_by_symbol: Mapping[str, str] | None = None,
) -> SourceExistingBootstrapSummary:
    """Inspect existing source data and optionally seed workflow states.

    Tests may pass explicit count mappings. Production startup normally omits
    them, causing the function to inspect PostgreSQL source tables.
    """

    started = utc_now_iso()
    months = iter_months(start_month, end_month)
    warnings: list[str] = []
    if m01_counts is None or source_03_counts is None or source_10_counts is None:
        try:
            db_url = resolve_database_url(database_url)
            fetched_01, fetched_03, fetched_10, fetched_01_first_seen, fetch_warnings = _fetch_source_counts_from_database(
                database_url=db_url,
                start_month=start_month,
                end_month=end_month,
                selected_target_symbol=selected_target_symbol,
            )
            m01_counts = fetched_01
            source_03_counts = fetched_03
            source_10_counts = fetched_10
            m01_first_seen_month_by_symbol = fetched_01_first_seen
            warnings.extend(fetch_warnings)
        except Exception as exc:
            warnings.append(f"source-existing bootstrap skipped database scan: {type(exc).__name__}: {exc}")
            m01_counts = {}
            source_03_counts = {}
            source_10_counts = {}

    stage_coverages, event_coverages, coverage_warnings = build_source_coverages_from_counts(
        months=months,
        m01_counts=m01_counts,
        source_03_counts=source_03_counts,
        source_10_counts=source_10_counts,
        selected_target_symbol=selected_target_symbol,
        m01_first_seen_month_by_symbol=m01_first_seen_month_by_symbol,
    )
    warnings.extend(coverage_warnings)

    coverages_by_month: dict[str, list[SourceStageCoverage]] = {month: [] for month in months}
    for coverage in stage_coverages:
        if coverage.ready:
            coverages_by_month.setdefault(coverage.month, []).append(coverage)

    resolved_report_root = report_root or (storage_root / "runtime" / "source_existing_bootstrap")
    workflow_state_paths: list[str] = []
    coverage_report_paths: list[str] = []
    bootstrapped_months: list[str] = []
    for month in months:
        ready_coverages = [
            coverage
            for coverage in coverages_by_month.get(month, [])
            if coverage.stage_id.startswith(("layer_01_", "layer_02_"))
        ]
        if not ready_coverages:
            continue
        report_paths: list[Path] = []
        for coverage in ready_coverages:
            path = _coverage_report_path(report_root=resolved_report_root, month=month, stage_id=coverage.stage_id)
            if write:
                _write_stage_coverage_report(path, coverage)
            report_paths.append(path)
        state_path = workflow_state_path_for_month(month, root=storage_root / "runtime")
        if write:
            advance_workflow_state(
                start_month=month,
                end_month=month,
                storage_root=storage_root,
                state_path=state_path,
                stage_coverage_reports=report_paths,
                selected_target_symbol=selected_target_symbol,
                write=True,
            )
        bootstrapped_months.append(month)
        workflow_state_paths.append(str(state_path))
        coverage_report_paths.extend(str(path) for path in report_paths)

    summary = SourceExistingBootstrapSummary(
        contract_type="manager_source_existing_bootstrap",
        started_utc=started,
        completed_utc=utc_now_iso(),
        start_month=start_month,
        end_month=end_month,
        selected_target_symbol=selected_target_symbol.strip().upper() if selected_target_symbol else None,
        write=write,
        bootstrapped_months=tuple(dict.fromkeys(bootstrapped_months)),
        workflow_state_paths=tuple(dict.fromkeys(workflow_state_paths)),
        coverage_report_paths=tuple(dict.fromkeys(coverage_report_paths)),
        source_stage_coverages=stage_coverages,
        event_source_coverages=event_coverages,
        warnings=tuple(dict.fromkeys(warnings)),
    )
    if write:
        resolved_report_root.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(summary.summary_row(), indent=2, sort_keys=True) + "\n"
        (resolved_report_root / "latest.json").write_text(payload, encoding="utf-8")
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        (resolved_report_root / f"source_existing_bootstrap_{timestamp}.json").write_text(payload, encoding="utf-8")
    return summary


def write_bootstrap_summary(summary: SourceExistingBootstrapSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap historical workflow state from already-existing source data.")
    parser.add_argument("--start-month", default="2016-01")
    parser.add_argument("--end-month", default="2016-01")
    parser.add_argument("--target-symbol", help="Target symbol used to validate source_03_target_state coverage.")
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--report-root", type=Path)
    parser.add_argument("--database-url")
    parser.add_argument("--write", action="store_true", help="Write coverage reports and seed workflow states. Dry-run by default.")
    args = parser.parse_args(argv)
    summary = run_source_existing_bootstrap(
        start_month=args.start_month,
        end_month=args.end_month,
        selected_target_symbol=args.target_symbol,
        storage_root=args.storage_root,
        report_root=args.report_root,
        database_url=args.database_url,
        write=args.write,
    )
    write_bootstrap_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "EventSourceCoverage",
    "SourceExistingBootstrapSummary",
    "SourceStageCoverage",
    "build_source_coverages_from_counts",
    "run_source_existing_bootstrap",
    "write_bootstrap_summary",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

"""Build fixed-universe target-selection effectiveness diagnostics.

The output is a retrospective review input for operation-component attribution.
It never feeds model features, threshold selection, promotion, activation, or
broker authority.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

DEFAULT_CANDIDATE_UNIVERSE_PATH = Path("/root/projects/trading-storage/main/shared/historical_candidate_universe.csv")
DEFAULT_DB_URL_FILE = Path("/root/secrets/trading_storage_postgres.json")
FALLBACK_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
BAR_SOURCE_TABLE = "trading_data.model_01_market_regime_data_acquisition"

FIELDNAMES = [
    "timestamp",
    "next_timestamp",
    "target_ref",
    "symbol",
    "asset_class",
    "sector_bucket_ref",
    "tradingview_sector",
    "layer2_context_symbol",
    "optionable_underlying_status",
    "replay_candidate_reason",
    "in_dollar_volume_top300",
    "in_market_cap_top300",
    "visible_universe_membership",
    "selected_by_replay",
    "selected_sector_bucket",
    "entry_bar_date",
    "exit_bar_date",
    "entry_bar_close",
    "exit_bar_close",
    "forward_return",
    "forward_return_status",
    "forward_return_rank",
    "forward_return_percentile",
    "top_quartile_candidate",
    "opportunity_cost_to_best",
    "sector_forward_return_mean",
    "sector_forward_return_rank",
    "sector_forward_return_percentile",
    "sector_candidate_count",
    "sector_top_quartile_bucket",
    "forward_return_rank_within_sector",
    "forward_return_percentile_within_sector",
    "top_quartile_candidate_within_sector",
    "opportunity_cost_to_sector_best",
    "candidate_universe_ref",
    "bar_source_ref",
    "diagnostic_role",
    "diagnostic_only",
    "fixed_input_only",
    "threshold_selection_performed",
    "retraining_performed",
    "provider_call_performed",
]

SECTOR_OPPORTUNITY_FIELDNAMES = [
    "timestamp",
    "next_timestamp",
    "sector_bucket_ref",
    "selected_sector_bucket",
    "best_visible_sector_bucket",
    "selection_status",
    "sector_candidate_count",
    "computed_candidate_count",
    "selected_target_count",
    "selected_targets",
    "sector_forward_return_mean",
    "sector_forward_return_rank",
    "sector_forward_return_percentile",
    "sector_top_quartile_bucket",
    "best_sector_forward_return_mean",
    "sector_opportunity_cost_to_best",
    "median_sector_forward_return_mean",
    "sector_opportunity_cost_to_median",
    "optionable_underlying_status_counts",
    "replay_candidate_reason_counts",
    "not_selected_reason",
    "diagnostic_role",
    "diagnostic_only",
    "fixed_input_only",
    "threshold_selection_performed",
    "retraining_performed",
    "provider_call_performed",
]


def build_target_selection_universe_metrics(
    *,
    decision_rows_path: Path,
    output_path: Path,
    candidate_universe_path: Path = DEFAULT_CANDIDATE_UNIVERSE_PATH,
    database_url: str | None = None,
    bar_rows: Sequence[Mapping[str, Any]] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    decision_rows = _load_jsonl(decision_rows_path)
    candidate_rows = _active_equity_candidate_rows(_load_csv_rows(candidate_universe_path))
    time_windows = _decision_time_windows(decision_rows)
    selected_targets_by_timestamp = _selected_targets_by_timestamp(decision_rows)
    selected_sector_buckets_by_timestamp = _selected_sector_buckets_by_timestamp(
        candidate_rows,
        selected_targets_by_timestamp,
    )
    bar_lookup = _bar_lookup(
        _fetch_bar_rows(
            symbols=[str(row["symbol"]) for row in candidate_rows],
            dates=_required_bar_dates(time_windows),
            database_url=database_url,
            bar_rows=bar_rows,
        )
    )

    metric_rows: list[dict[str, Any]] = []
    for timestamp, next_timestamp in time_windows:
        entry_date = _timestamp_date(timestamp)
        exit_date = _timestamp_date(next_timestamp)
        selected_targets = selected_targets_by_timestamp.get(timestamp, set())
        rows_for_timestamp: list[dict[str, Any]] = []
        for candidate in candidate_rows:
            symbol = str(candidate["symbol"])
            entry_close = bar_lookup.get((symbol, entry_date))
            exit_close = bar_lookup.get((symbol, exit_date))
            status = _forward_return_status(entry_close=entry_close, exit_close=exit_close)
            forward_return = None
            if status == "computed":
                assert entry_close is not None
                assert exit_close is not None
                forward_return = (exit_close - entry_close) / entry_close
            rows_for_timestamp.append(
                {
                    "timestamp": timestamp,
                    "next_timestamp": next_timestamp,
                    "target_ref": str(candidate.get("target_ref") or symbol),
                    "symbol": symbol,
                    "asset_class": str(candidate.get("asset_class") or ""),
                    "sector_bucket_ref": _sector_bucket_ref(candidate),
                    "tradingview_sector": str(candidate.get("tradingview_sector") or ""),
                    "layer2_context_symbol": str(candidate.get("layer2_context_symbol") or ""),
                    "optionable_underlying_status": str(candidate.get("optionable_underlying_status") or ""),
                    "replay_candidate_reason": str(candidate.get("replay_candidate_reason") or ""),
                    "in_dollar_volume_top300": str(candidate.get("in_dollar_volume_top300") or ""),
                    "in_market_cap_top300": str(candidate.get("in_market_cap_top300") or ""),
                    "visible_universe_membership": True,
                    "selected_by_replay": symbol in selected_targets or str(candidate.get("target_ref") or "") in selected_targets,
                    "selected_sector_bucket": _sector_bucket_ref(candidate)
                    in selected_sector_buckets_by_timestamp.get(timestamp, set()),
                    "entry_bar_date": entry_date.isoformat(),
                    "exit_bar_date": exit_date.isoformat(),
                    "entry_bar_close": _round(entry_close),
                    "exit_bar_close": _round(exit_close),
                    "forward_return": _round(forward_return),
                    "forward_return_status": status,
                    "candidate_universe_ref": str(candidate_universe_path),
                    "bar_source_ref": BAR_SOURCE_TABLE,
                    "diagnostic_role": "component_effectiveness_label",
                    "diagnostic_only": True,
                    "fixed_input_only": True,
                    "threshold_selection_performed": False,
                    "retraining_performed": False,
                    "provider_call_performed": False,
                }
            )
        _add_forward_return_ranks(rows_for_timestamp)
        metric_rows.extend(rows_for_timestamp)

    sector_opportunity_rows = _sector_opportunity_packet_rows(metric_rows)
    sector_opportunity_packet_path = output_path.with_name("sector_opportunity_packet.csv")
    _write_csv(output_path, metric_rows, FIELDNAMES)
    _write_csv(sector_opportunity_packet_path, sector_opportunity_rows, SECTOR_OPPORTUNITY_FIELDNAMES)
    report = _report(
        decision_rows_path=decision_rows_path,
        output_path=output_path,
        sector_opportunity_packet_path=sector_opportunity_packet_path,
        candidate_universe_path=candidate_universe_path,
        metric_rows=metric_rows,
        sector_opportunity_rows=sector_opportunity_rows,
        time_windows=time_windows,
        now_utc=now_utc or datetime.now(UTC),
    )
    output_path.with_suffix(".report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sector_opportunity_packet_path.with_suffix(".json").write_text(
        json.dumps(
            _sector_opportunity_packet(
                sector_opportunity_rows=sector_opportunity_rows,
                sector_opportunity_packet_path=sector_opportunity_packet_path,
                target_selection_universe_metrics_path=output_path,
                now_utc=now_utc or datetime.now(UTC),
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def _active_equity_candidate_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        symbol = str(row.get("symbol") or row.get("target_ref") or "").strip().upper()
        if not symbol or symbol in seen:
            continue
        if str(row.get("asset_class") or "").strip().lower() != "us_equity":
            continue
        status = str(row.get("replay_candidate_status") or row.get("pool_membership_status") or "active").strip().lower()
        if status != "active":
            continue
        item = dict(row)
        item["symbol"] = symbol
        item["target_ref"] = str(row.get("target_ref") or symbol).strip().upper()
        candidates.append(item)
        seen.add(symbol)
    return candidates


def _sector_bucket_ref(row: Mapping[str, Any]) -> str:
    """Return the bucket used for sector-first target-selection review."""

    for key in ("layer2_context_symbol", "tradingview_sector", "sector", "industry"):
        value = str(row.get(key) or "").strip()
        if value:
            return value.upper()
    return "UNMAPPED"


def _decision_time_windows(rows: Sequence[Mapping[str, Any]]) -> tuple[tuple[str, str], ...]:
    windows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        timestamp = str(row.get("timestamp") or row.get("replay_time_pointer") or "").strip()
        next_timestamp = str(row.get("next_timestamp") or "").strip()
        if not timestamp or not next_timestamp:
            continue
        key = (timestamp, next_timestamp)
        if key in seen:
            continue
        seen.add(key)
        windows.append(key)
    return tuple(windows)


def _selected_targets_by_timestamp(rows: Sequence[Mapping[str, Any]]) -> dict[str, set[str]]:
    selected: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        timestamp = str(row.get("timestamp") or row.get("replay_time_pointer") or "").strip()
        target = str(row.get("target_ref") or "").strip().upper()
        if timestamp and target:
            selected[timestamp].add(target)
    return selected


def _selected_sector_buckets_by_timestamp(
    candidate_rows: Sequence[Mapping[str, Any]],
    selected_targets_by_timestamp: Mapping[str, set[str]],
) -> dict[str, set[str]]:
    buckets: dict[str, set[str]] = defaultdict(set)
    for timestamp, selected_targets in selected_targets_by_timestamp.items():
        for candidate in candidate_rows:
            symbol = str(candidate.get("symbol") or "").strip().upper()
            target_ref = str(candidate.get("target_ref") or symbol).strip().upper()
            if symbol in selected_targets or target_ref in selected_targets:
                buckets[timestamp].add(_sector_bucket_ref(candidate))
    return buckets


def _required_bar_dates(time_windows: Sequence[tuple[str, str]]) -> tuple[date, ...]:
    dates = {_timestamp_date(timestamp) for window in time_windows for timestamp in window}
    return tuple(sorted(dates))


def _fetch_bar_rows(
    *,
    symbols: Sequence[str],
    dates: Sequence[date],
    database_url: str | None,
    bar_rows: Sequence[Mapping[str, Any]] | None,
) -> list[dict[str, Any]]:
    if bar_rows is not None:
        return [dict(row) for row in bar_rows]
    if not symbols or not dates:
        return []
    url = _database_url(database_url)
    if not url:
        raise RuntimeError("database URL required to materialize target-selection universe metrics from SQL bars")
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency failure is environmental.
        raise RuntimeError("psycopg is required to read target-selection universe bars") from exc
    with psycopg.connect(url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT symbol, timestamp, bar_close
                FROM trading_data.model_01_market_regime_data_acquisition
                WHERE timeframe = '1Day'
                  AND symbol = ANY(%s)
                  AND timestamp::date = ANY(%s)
                ORDER BY symbol, timestamp
                """,
                (list(symbols), list(dates)),
            )
            return [dict(row) for row in cursor.fetchall()]


def _bar_lookup(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, date], float]:
    output: dict[tuple[str, date], float] = {}
    for row in rows:
        symbol = str(row.get("symbol") or "").strip().upper()
        timestamp = row.get("timestamp")
        close = _float(row.get("bar_close"))
        if not symbol or timestamp is None or close is None:
            continue
        output[(symbol, _timestamp_date(timestamp))] = close
    return output


def _forward_return_status(*, entry_close: float | None, exit_close: float | None) -> str:
    if entry_close is None:
        return "missing_entry_bar"
    if exit_close is None:
        return "missing_exit_bar"
    if entry_close <= 0:
        return "non_positive_entry_bar"
    return "computed"


def _add_forward_return_ranks(rows: list[dict[str, Any]]) -> None:
    computed = [row for row in rows if _float(row.get("forward_return")) is not None]
    returns = sorted({_float(row["forward_return"]) for row in computed if _float(row.get("forward_return")) is not None}, reverse=True)
    if not computed or not returns:
        for row in rows:
            row.update(
                {
                    "forward_return_rank": "",
                    "forward_return_percentile": "",
                    "top_quartile_candidate": "",
                    "opportunity_cost_to_best": "",
                    "sector_forward_return_mean": "",
                    "sector_forward_return_rank": "",
                    "sector_forward_return_percentile": "",
                    "sector_candidate_count": "",
                    "sector_top_quartile_bucket": "",
                    "forward_return_rank_within_sector": "",
                    "forward_return_percentile_within_sector": "",
                    "top_quartile_candidate_within_sector": "",
                    "opportunity_cost_to_sector_best": "",
                }
            )
        return
    best = max(float(row["forward_return"]) for row in computed)
    universe_count = len(computed)
    top_quartile_limit = max(1, (universe_count + 3) // 4)
    for row in rows:
        value = _float(row.get("forward_return"))
        if value is None:
            row.update(
                {
                    "forward_return_rank": "",
                    "forward_return_percentile": "",
                    "top_quartile_candidate": "",
                    "opportunity_cost_to_best": "",
                }
            )
            continue
        rank = 1 + sum(1 for other in computed if float(other["forward_return"]) > value)
        percentile = 1.0 if universe_count <= 1 else (universe_count - rank) / (universe_count - 1)
        row.update(
            {
                "forward_return_rank": rank,
                "forward_return_percentile": _round(percentile),
                "top_quartile_candidate": rank <= top_quartile_limit,
                "opportunity_cost_to_best": _round(best - value),
            }
        )
    _add_sector_forward_return_metrics(rows)


def _add_sector_forward_return_metrics(rows: list[dict[str, Any]]) -> None:
    empty_fields = {
        "sector_forward_return_mean": "",
        "sector_forward_return_rank": "",
        "sector_forward_return_percentile": "",
        "sector_candidate_count": "",
        "sector_top_quartile_bucket": "",
        "forward_return_rank_within_sector": "",
        "forward_return_percentile_within_sector": "",
        "top_quartile_candidate_within_sector": "",
        "opportunity_cost_to_sector_best": "",
    }
    computed_by_sector: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        value = _float(row.get("forward_return"))
        if value is None:
            row.update(empty_fields)
            continue
        computed_by_sector[str(row.get("sector_bucket_ref") or "UNMAPPED")].append(row)
    if not computed_by_sector:
        for row in rows:
            row.update(empty_fields)
        return

    sector_means = {
        sector: sum(float(row["forward_return"]) for row in sector_rows) / len(sector_rows)
        for sector, sector_rows in computed_by_sector.items()
        if sector_rows
    }
    sector_count = len(sector_means)
    sector_top_quartile_limit = max(1, (sector_count + 3) // 4)
    for sector, sector_rows in computed_by_sector.items():
        sector_mean = sector_means[sector]
        sector_rank = 1 + sum(1 for other_mean in sector_means.values() if other_mean > sector_mean)
        sector_percentile = 1.0 if sector_count <= 1 else (sector_count - sector_rank) / (sector_count - 1)
        sector_returns = [float(row["forward_return"]) for row in sector_rows]
        sector_best = max(sector_returns)
        sector_member_count = len(sector_rows)
        sector_top_quartile_limit_within = max(1, (sector_member_count + 3) // 4)
        for row in sector_rows:
            value = float(row["forward_return"])
            within_rank = 1 + sum(1 for other in sector_returns if other > value)
            within_percentile = (
                1.0 if sector_member_count <= 1 else (sector_member_count - within_rank) / (sector_member_count - 1)
            )
            row.update(
                {
                    "sector_forward_return_mean": _round(sector_mean),
                    "sector_forward_return_rank": sector_rank,
                    "sector_forward_return_percentile": _round(sector_percentile),
                    "sector_candidate_count": sector_member_count,
                    "sector_top_quartile_bucket": sector_rank <= sector_top_quartile_limit,
                    "forward_return_rank_within_sector": within_rank,
                    "forward_return_percentile_within_sector": _round(within_percentile),
                    "top_quartile_candidate_within_sector": within_rank <= sector_top_quartile_limit_within,
                    "opportunity_cost_to_sector_best": _round(sector_best - value),
                }
            )


def _sector_opportunity_packet_rows(metric_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    rows_by_timestamp: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in metric_rows:
        rows_by_timestamp[str(row.get("timestamp") or "")].append(row)

    for timestamp, rows in sorted(rows_by_timestamp.items()):
        computed_rows = [row for row in rows if _float(row.get("forward_return")) is not None]
        if not computed_rows:
            continue
        next_timestamp = str(computed_rows[0].get("next_timestamp") or "")
        rows_by_sector: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in computed_rows:
            rows_by_sector[str(row.get("sector_bucket_ref") or "UNMAPPED")].append(row)
        sector_means = {
            sector: sum(float(row["forward_return"]) for row in sector_rows) / len(sector_rows)
            for sector, sector_rows in rows_by_sector.items()
            if sector_rows
        }
        if not sector_means:
            continue
        best_sector = max(sector_means, key=lambda sector: sector_means[sector])
        best_value = sector_means[best_sector]
        median_value = _median(sector_means.values())
        sector_count = len(sector_means)
        top_quartile_limit = max(1, (sector_count + 3) // 4)
        for sector, sector_rows in sorted(rows_by_sector.items()):
            sector_mean = sector_means[sector]
            sector_rank = 1 + sum(1 for other in sector_means.values() if other > sector_mean)
            selected_rows = [
                row
                for row in sector_rows
                if str(row.get("selected_by_replay") or "").strip().lower() in {"true", "1", "yes"}
            ]
            selected_sector = any(
                str(row.get("selected_sector_bucket") or "").strip().lower() in {"true", "1", "yes"}
                for row in sector_rows
            )
            selection_status = "unselected_sector"
            if selected_sector and sector == best_sector:
                selection_status = "selected_best_visible_sector"
            elif selected_sector:
                selection_status = "selected_weaker_visible_sector"
            elif sector == best_sector:
                selection_status = "missed_best_visible_sector"
            not_selected_reason = "selected_by_replay" if selected_sector else "not_selected_reason_unavailable_in_current_inputs"
            output.append(
                {
                    "timestamp": timestamp,
                    "next_timestamp": next_timestamp,
                    "sector_bucket_ref": sector,
                    "selected_sector_bucket": selected_sector,
                    "best_visible_sector_bucket": best_sector,
                    "selection_status": selection_status,
                    "sector_candidate_count": len(sector_rows),
                    "computed_candidate_count": len(sector_rows),
                    "selected_target_count": len(selected_rows),
                    "selected_targets": ";".join(
                        sorted(str(row.get("target_ref") or row.get("symbol") or "") for row in selected_rows)
                    ),
                    "sector_forward_return_mean": _round(sector_mean),
                    "sector_forward_return_rank": sector_rank,
                    "sector_forward_return_percentile": _round(
                        1.0 if sector_count <= 1 else (sector_count - sector_rank) / (sector_count - 1)
                    ),
                    "sector_top_quartile_bucket": sector_rank <= top_quartile_limit,
                    "best_sector_forward_return_mean": _round(best_value),
                    "sector_opportunity_cost_to_best": _round(best_value - sector_mean),
                    "median_sector_forward_return_mean": _round(median_value),
                    "sector_opportunity_cost_to_median": _round((median_value or 0.0) - sector_mean),
                    "optionable_underlying_status_counts": _counter_string(
                        row.get("optionable_underlying_status") for row in sector_rows
                    ),
                    "replay_candidate_reason_counts": _counter_string(
                        row.get("replay_candidate_reason") for row in sector_rows
                    ),
                    "not_selected_reason": not_selected_reason,
                    "diagnostic_role": "sector_opportunity_review_label",
                    "diagnostic_only": True,
                    "fixed_input_only": True,
                    "threshold_selection_performed": False,
                    "retraining_performed": False,
                    "provider_call_performed": False,
                }
            )
    return output


def _sector_opportunity_packet(
    *,
    sector_opportunity_rows: Sequence[Mapping[str, Any]],
    sector_opportunity_packet_path: Path,
    target_selection_universe_metrics_path: Path,
    now_utc: datetime,
) -> dict[str, Any]:
    selected_rows = [
        row
        for row in sector_opportunity_rows
        if str(row.get("selected_sector_bucket") or "").strip().lower() in {"true", "1", "yes"}
    ]
    missed_best_rows = [
        row
        for row in sector_opportunity_rows
        if str(row.get("selection_status") or "") == "missed_best_visible_sector"
    ]
    selected_weaker_rows = [
        row
        for row in sector_opportunity_rows
        if str(row.get("selection_status") or "") == "selected_weaker_visible_sector"
    ]
    return {
        "contract_type": "target_selection_sector_opportunity_packet",
        "generated_at_utc": now_utc.astimezone(UTC).isoformat(),
        "sector_opportunity_packet_ref": str(sector_opportunity_packet_path),
        "target_selection_universe_metrics_ref": str(target_selection_universe_metrics_path),
        "summary": {
            "sector_row_count": len(sector_opportunity_rows),
            "selected_sector_row_count": len(selected_rows),
            "missed_best_visible_sector_count": len(missed_best_rows),
            "selected_weaker_visible_sector_count": len(selected_weaker_rows),
            "selected_sector_opportunity_cost_to_best_mean": _mean(
                _float(row.get("sector_opportunity_cost_to_best")) for row in selected_rows
            ),
            "selected_sector_forward_return_percentile_mean": _mean(
                _float(row.get("sector_forward_return_percentile")) for row in selected_rows
            ),
            "selected_target_weighted_sector_opportunity_cost_to_best_mean": _weighted_mean(
                (
                    _float(row.get("sector_opportunity_cost_to_best")),
                    _float(row.get("selected_target_count")),
                )
                for row in selected_rows
            ),
            "selected_target_weighted_sector_forward_return_percentile_mean": _weighted_mean(
                (
                    _float(row.get("sector_forward_return_percentile")),
                    _float(row.get("selected_target_count")),
                )
                for row in selected_rows
            ),
        },
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
        "interpretation_notes": [
            "Sector opportunity rows are ex-post diagnostic labels over a fixed point-in-time visible universe.",
            "A missed best visible sector is not automatically a model fault unless point-in-time admissibility evidence says it was tradable and in scope.",
            "not_selected_reason_unavailable_in_current_inputs means the current diagnostic lacks a decision-time exclusion reason, not that no valid reason existed.",
        ],
        "side_effects": {
            "provider_call_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
            "model_activation_performed": False,
            "retraining_performed": False,
            "sql_mutation_performed": False,
            "storage_source_mutation_performed": False,
        },
    }


def _report(
    *,
    decision_rows_path: Path,
    output_path: Path,
    sector_opportunity_packet_path: Path,
    candidate_universe_path: Path,
    metric_rows: Sequence[Mapping[str, Any]],
    sector_opportunity_rows: Sequence[Mapping[str, Any]],
    time_windows: Sequence[tuple[str, str]],
    now_utc: datetime,
) -> dict[str, Any]:
    status_counts = Counter(str(row.get("forward_return_status") or "") for row in metric_rows)
    selected_rows = [row for row in metric_rows if str(row.get("selected_by_replay") or "").lower() == "true"]
    selected_computed = [row for row in selected_rows if str(row.get("forward_return_status") or "") == "computed"]
    computed_sector_buckets = {
        str(row.get("sector_bucket_ref") or "")
        for row in metric_rows
        if str(row.get("forward_return_status") or "") == "computed"
    }
    selected_sector_buckets = {
        str(row.get("sector_bucket_ref") or "")
        for row in metric_rows
        if str(row.get("selected_sector_bucket") or "").lower() == "true"
    }
    return {
        "contract_type": "target_selection_universe_metrics_report",
        "generated_at_utc": now_utc.astimezone(UTC).isoformat(),
        "decision_rows_ref": str(decision_rows_path),
        "candidate_universe_ref": str(candidate_universe_path),
        "target_selection_universe_metrics_ref": str(output_path),
        "sector_opportunity_packet_ref": str(sector_opportunity_packet_path),
        "summary": {
            "time_window_count": len(time_windows),
            "row_count": len(metric_rows),
            "selected_row_count": len(selected_rows),
            "selected_computed_forward_return_count": len(selected_computed),
            "forward_return_status_counts": dict(status_counts),
            "computed_forward_return_coverage": (status_counts.get("computed", 0) / len(metric_rows)) if metric_rows else None,
            "selected_forward_return_coverage": (len(selected_computed) / len(selected_rows)) if selected_rows else None,
            "computed_sector_bucket_count": len(computed_sector_buckets),
            "selected_sector_bucket_count": len(selected_sector_buckets),
            "sector_opportunity_row_count": len(sector_opportunity_rows),
            "selected_weaker_visible_sector_count": sum(
                1
                for row in sector_opportunity_rows
                if str(row.get("selection_status") or "") == "selected_weaker_visible_sector"
            ),
            "missed_best_visible_sector_count": sum(
                1
                for row in sector_opportunity_rows
                if str(row.get("selection_status") or "") == "missed_best_visible_sector"
            ),
        },
        "effectiveness_role": "rank_selected_sector_buckets_then_selected_targets_within_bucket",
        "forbidden_uses": [
            "training_feature_input",
            "threshold_selection",
            "promotion_approval",
            "model_activation",
            "broker_or_account_authority",
        ],
        "side_effects": {
            "provider_call_performed": False,
            "broker_execution_performed": False,
            "account_mutation_performed": False,
            "model_activation_performed": False,
            "retraining_performed": False,
            "sql_mutation_performed": False,
            "storage_source_mutation_performed": False,
        },
    }


def _database_url(value: str | None) -> str | None:
    if value:
        return value
    env_value = os.environ.get("OPENCLAW_DATABASE_URL", "").strip() or os.environ.get("DATABASE_URL", "").strip()
    if env_value:
        return env_value
    for path in (DEFAULT_DB_URL_FILE, FALLBACK_DB_URL_FILE):
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not text:
            continue
        if text.startswith("{"):
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            dsn = str(payload.get("dsn") or "").strip()
            if dsn:
                return dsn
        else:
            return text
    return None


def _timestamp_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        raise ValueError("timestamp is required")
    return datetime.fromisoformat(text.replace("Z", "+00:00")).date()


def _float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: float | None) -> float | str:
    if value is None:
        return ""
    return round(float(value), 6)


def _mean(values: Iterable[float | None]) -> float | None:
    numeric = [float(value) for value in values if value is not None]
    if not numeric:
        return None
    return round(sum(numeric) / len(numeric), 6)


def _weighted_mean(values: Iterable[tuple[float | None, float | None]]) -> float | None:
    weighted_values = [
        (float(value), float(weight))
        for value, weight in values
        if value is not None and weight is not None and float(weight) > 0
    ]
    weight_total = sum(weight for _, weight in weighted_values)
    if weight_total <= 0:
        return None
    return round(sum(value * weight for value, weight in weighted_values) / weight_total, 6)


def _median(values: Iterable[float]) -> float | None:
    numeric = sorted(float(value) for value in values)
    if not numeric:
        return None
    midpoint = len(numeric) // 2
    if len(numeric) % 2:
        return round(numeric[midpoint], 6)
    return round((numeric[midpoint - 1] + numeric[midpoint]) / 2.0, 6)


def _counter_string(values: Iterable[Any]) -> str:
    counts = Counter(str(value or "unknown") for value in values)
    return ";".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-rows", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--candidate-universe-path", type=Path, default=DEFAULT_CANDIDATE_UNIVERSE_PATH)
    parser.add_argument("--database-url")
    args = parser.parse_args(argv)
    report = build_target_selection_universe_metrics(
        decision_rows_path=args.decision_rows,
        output_path=args.output_path,
        candidate_universe_path=args.candidate_universe_path,
        database_url=args.database_url,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

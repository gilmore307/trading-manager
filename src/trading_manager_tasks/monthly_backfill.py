"""Monthly manager-request planning for historical data backfill.

This module plans `manager_request_v1` rows only. It does not call providers,
insert SQL rows, or create data task payload bodies. Bulky task parameters live
behind later artifact refs; the request row keeps only durable control-plane
facts and a deterministic parameter reference.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Iterator, Literal, TextIO

DEFAULT_REQUESTED_BY = "openclaw"
DEFAULT_START_MONTH = "2016-01"
OKX_START_MONTH = "2018-01"
CHRONOLOGICAL_FORWARD_POLICY_REF = "chronological_forward_backfill_policy_v1"
DEFAULT_POLICY_REFS = ("monthly_backfill_v1", CHRONOLOGICAL_FORWARD_POLICY_REF, "live_call_policy_required")
DEFAULT_PROJECTS_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MARKET_REGIME_ETF_UNIVERSE_PATH = (
    DEFAULT_PROJECTS_ROOT / "trading-storage" / "main" / "shared" / "market_regime_etf_universe.csv"
)
LAYER_ONE_MODEL_LAYER = "layer_01_market_regime"
LAYER_TWO_MODEL_LAYER = "layer_02_sector_context"
SUPPORTED_MARKET_REGIME_MODEL_LAYERS = (LAYER_ONE_MODEL_LAYER, LAYER_TWO_MODEL_LAYER)
BAR_GRAIN_TO_ALPACA_TIMEFRAME = {"1m": "1Min", "30m": "30Min", "1d": "1Day"}


@dataclass(frozen=True, order=True)
class Month:
    """YYYY-MM month value with deterministic ordering."""

    year: int
    month: int

    @classmethod
    def parse(cls, value: str) -> "Month":
        try:
            year_text, month_text = value.split("-", 1)
            parsed = cls(int(year_text), int(month_text))
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("month must be YYYY-MM") from exc
        if not 1 <= parsed.month <= 12:
            raise ValueError("month must be YYYY-MM with month 01-12")
        return parsed

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def next(self) -> "Month":
        if self.month == 12:
            return Month(self.year + 1, 1)
        return Month(self.year, self.month + 1)

    @property
    def start_date(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def exclusive_end_date(self) -> date:
        return self.next().start_date


@dataclass(frozen=True)
class MonthlyWindow:
    """Inclusive/exclusive month window used by provider task keys."""

    month: str
    start_date: str
    end_date_exclusive: str


@dataclass(frozen=True)
class MarketRegimeUniverseMember:
    """One reviewed market-regime/sector-context ETF universe member."""

    symbol: str
    model_layer: str
    bar_grain: str
    timeframe: str
    exposure_type: str
    universe_type: str


@dataclass(frozen=True)
class SourceAvailability:
    """Manager-level availability stance for one accepted data feed/source."""

    source_id: str
    target_component_id: str
    target_repo_id: str
    earliest_month: str | None
    request_kind: str = "data_backfill_month_v1"
    include_by_default: bool = True
    historical_backfill_supported: bool = True
    note: str = ""

    def effective_start(self, requested_start: Month) -> Month | None:
        if not self.historical_backfill_supported or self.earliest_month is None:
            return None
        earliest = Month.parse(self.earliest_month)
        return earliest if earliest > requested_start else requested_start


DEFAULT_SOURCES: tuple[SourceAvailability, ...] = (
    SourceAvailability(
        "alpaca_bars",
        "01_feed_alpaca_bars",
        "trading-data",
        "2016-01",
        note="Alpaca SPY bar probe returned first row on 2016-01-04.",
    ),
    SourceAvailability(
        "alpaca_liquidity",
        "02_feed_alpaca_liquidity",
        "trading-data",
        "2016-01",
        note="Combined trade/quote liquidity starts at the quote-supported month 2016-01.",
    ),
    SourceAvailability(
        "alpaca_news",
        "03_feed_alpaca_news",
        "trading-data",
        "2015-01",
        note="Included from the common monthly start even though provider evidence begins earlier.",
    ),
    SourceAvailability(
        "gdelt_news",
        "05_feed_gdelt_news",
        "trading-data",
        "2015-02",
        note="GDELT 2.0 public availability begins in 2015-02; use common start 2016-01.",
    ),
    SourceAvailability(
        "sec_company_financials",
        "08_feed_sec_company_financials",
        "trading-data",
        "2009-07",
        note="SEC filed evidence predates the common start; use common start 2016-01.",
    ),
    SourceAvailability(
        "thetadata_option_primary_tracking",
        "10_feed_thetadata_option_primary_tracking",
        "trading-data",
        "2016-01",
        note="Current local ThetaData entitlement supports historical option OHLC from 2016-01.",
    ),
    SourceAvailability(
        "thetadata_option_event_timeline",
        "11_feed_thetadata_option_event_timeline",
        "trading-data",
        "2016-01",
        note="Current local ThetaData entitlement supports historical option trade/quote from 2016-01.",
    ),
    SourceAvailability(
        "okx_crypto_market_data",
        "04_feed_okx_crypto_market_data",
        "trading-data",
        OKX_START_MONTH,
        note="Crypto is intentionally allowed to join later than the common start.",
    ),
    SourceAvailability(
        "etf_holdings",
        "06_feed_etf_holdings",
        "trading-data",
        None,
        include_by_default=False,
        historical_backfill_supported=False,
        note="Current issuer holdings route is not an honest historical point-in-time backfill source.",
    ),
    SourceAvailability(
        "trading_economics_calendar_web",
        "07_feed_trading_economics_calendar_web",
        "trading-data",
        None,
        include_by_default=False,
        historical_backfill_supported=False,
        note="Accepted visible-page route is current/window oriented, not a bulk historical API route.",
    ),
    SourceAvailability(
        "thetadata_option_selection_snapshot",
        "09_feed_thetadata_option_selection_snapshot",
        "trading-data",
        None,
        include_by_default=False,
        historical_backfill_supported=False,
        note="Current snapshot endpoint is not treated as historical point-in-time chain backfill.",
    ),
)


def iter_monthly_windows(start_month: str, end_month: str) -> Iterator[MonthlyWindow]:
    """Yield inclusive monthly windows from start_month through end_month."""

    current = Month.parse(start_month)
    end = Month.parse(end_month)
    if end < current:
        raise ValueError("end_month must be >= start_month")
    while current <= end:
        yield MonthlyWindow(str(current), current.start_date.isoformat(), current.exclusive_end_date.isoformat())
        current = current.next()


def _path_token(value: str) -> str:
    return value.lower().replace("-", "_").replace("/", "_")


def _request_id(source_id: str, month: str, *, symbol: str | None = None) -> str:
    parts = ["mgrreq", "backfill", _path_token(source_id)]
    if symbol:
        parts.append(_path_token(symbol))
    parts.append(month.replace("-", "_"))
    return "_".join(parts)


def _parameter_ref(source_id: str, month: str, *, symbol: str | None = None) -> str:
    if symbol:
        return f"storage://trading-manager/monthly_backfill_v1/{source_id}/{symbol.upper()}/{month}/task_key.json"
    return f"storage://trading-manager/monthly_backfill_v1/{source_id}/{month}/task_key.json"


def _expected_outputs(source_id: str, month: str, *, symbol: str | None = None) -> list[str]:
    if symbol:
        return [f"storage://trading-data/monthly_backfill_v1/{source_id}/{symbol.upper()}/{month}/"]
    return [f"storage://trading-data/monthly_backfill_v1/{source_id}/{month}/"]


def load_market_regime_universe(
    path: Path = DEFAULT_MARKET_REGIME_ETF_UNIVERSE_PATH,
    *,
    model_layers: Iterable[str] | None = None,
) -> tuple[MarketRegimeUniverseMember, ...]:
    """Load reviewed ETF universe rows for the requested model layers."""

    layer_filter = set(model_layers or [LAYER_ONE_MODEL_LAYER])
    unsupported = sorted(layer_filter - set(SUPPORTED_MARKET_REGIME_MODEL_LAYERS))
    if unsupported:
        raise ValueError("unsupported model_layer values: " + ",".join(unsupported))
    rows: list[MarketRegimeUniverseMember] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            model_layer = str(row.get("model_layer") or "")
            if model_layer not in layer_filter:
                continue
            symbol = str(row.get("symbol") or "").upper()
            bar_grain = str(row.get("bar_grain") or "")
            timeframe = BAR_GRAIN_TO_ALPACA_TIMEFRAME.get(bar_grain)
            if not symbol or timeframe is None:
                raise ValueError(f"unsupported universe row: {row}")
            rows.append(
                MarketRegimeUniverseMember(
                    symbol=symbol,
                    model_layer=model_layer,
                    bar_grain=bar_grain,
                    timeframe=timeframe,
                    exposure_type=str(row.get("exposure_type") or ""),
                    universe_type=str(row.get("universe_type") or ""),
                )
            )
    return tuple(sorted(rows, key=lambda item: (item.model_layer, item.symbol)))


def _plan_source_window(
    *,
    source: SourceAvailability,
    window: MonthlyWindow,
    requested_by: str,
    universe_member: MarketRegimeUniverseMember | None = None,
) -> dict[str, object]:
    symbol = universe_member.symbol if universe_member else None
    request: dict[str, object] = {
        "request_id": _request_id(source.source_id, window.month, symbol=symbol),
        "contract_type": "manager_request_v1",
        "request_kind": source.request_kind,
        "status": "requested",
        "requested_by": requested_by,
        "target_component_id": source.target_component_id,
        "target_component_kind": "data_feed",
        "target_repo_id": source.target_repo_id,
        "expected_outputs": _expected_outputs(source.source_id, window.month, symbol=symbol),
        "policy_refs": list(DEFAULT_POLICY_REFS),
        "priority": "normal",
        "parameter_ref": _parameter_ref(source.source_id, window.month, symbol=symbol),
        "dry_run": True,
        "month": window.month,
        "start_date": window.start_date,
        "end_date_exclusive": window.end_date_exclusive,
        "availability_note": source.note,
    }
    if universe_member:
        request.update(
            {
                "symbol": universe_member.symbol,
                "timeframe": universe_member.timeframe,
                "bar_grain": universe_member.bar_grain,
                "model_layer": universe_member.model_layer,
                "universe_ref": "trading-storage/main/shared/market_regime_etf_universe.csv",
                "universe_type": universe_member.universe_type,
                "exposure_type": universe_member.exposure_type,
            }
        )
    return request


def plan_monthly_backfill_requests(
    *,
    start_month: str = DEFAULT_START_MONTH,
    end_month: str,
    sources: Iterable[SourceAvailability] = DEFAULT_SOURCES,
    include_crypto: bool = True,
    requested_by: str = DEFAULT_REQUESTED_BY,
    market_regime_universe_path: Path = DEFAULT_MARKET_REGIME_ETF_UNIVERSE_PATH,
    model_layers: Iterable[str] = (LAYER_ONE_MODEL_LAYER,),
) -> list[dict[str, object]]:
    """Plan deterministic `manager_request_v1` dictionaries.

    The global start is 2016-01 by accepted policy. Each source can join later
    when its own honest historical availability starts later; OKX crypto is the
    first such source and starts in 2018-01.
    """

    requested_start = Month.parse(start_month)
    accepted_start = Month.parse(DEFAULT_START_MONTH)
    effective_global_start = accepted_start if requested_start < accepted_start else requested_start
    requested_end = Month.parse(end_month)
    if requested_end < requested_start:
        raise ValueError("end_month must be >= start_month")
    if requested_end < effective_global_start:
        return []

    selected_model_layers = tuple(dict.fromkeys(model_layers))
    market_regime_universe = load_market_regime_universe(market_regime_universe_path, model_layers=selected_model_layers)
    eligible_sources: list[tuple[SourceAvailability, Month]] = []
    for source in sources:
        if not source.include_by_default:
            continue
        if source.source_id == "okx_crypto_market_data" and not include_crypto:
            continue
        source_start = source.effective_start(effective_global_start)
        if source_start is None or source_start > requested_end:
            continue
        eligible_sources.append((source, source_start))

    planned: list[dict[str, object]] = []
    for window in iter_monthly_windows(str(effective_global_start), str(requested_end)):
        window_month = Month.parse(window.month)
        for source, source_start in eligible_sources:
            if window_month < source_start:
                continue
            if source.target_component_id == "01_feed_alpaca_bars":
                for member in market_regime_universe:
                    planned.append(
                        _plan_source_window(source=source, window=window, requested_by=requested_by, universe_member=member)
                    )
            else:
                planned.append(_plan_source_window(source=source, window=window, requested_by=requested_by))
    return planned


def write_requests(requests: Iterable[dict[str, object]], *, output: TextIO, output_format: Literal["jsonl", "json", "csv"]) -> None:
    rows = list(requests)
    if output_format == "json":
        json.dump(rows, output, indent=2, sort_keys=True)
        output.write("\n")
        return
    if output_format == "jsonl":
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")
        return
    if output_format == "csv":
        fieldnames = [
            "request_id",
            "contract_type",
            "request_kind",
            "status",
            "requested_by",
            "target_component_id",
            "target_component_kind",
            "target_repo_id",
            "parameter_ref",
            "dry_run",
            "month",
            "start_date",
            "end_date_exclusive",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return
    raise ValueError(f"unsupported output_format: {output_format}")


def source_inventory() -> list[dict[str, object]]:
    return [asdict(source) for source in DEFAULT_SOURCES]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan dry-run manager_request_v1 rows for monthly data backfill.")
    parser.add_argument("--start-month", default=DEFAULT_START_MONTH, help="Inclusive YYYY-MM start month; values earlier than the accepted 2016-01 common start are clamped to 2016-01.")
    parser.add_argument("--end-month", required=True, help="Inclusive YYYY-MM end month.")
    parser.add_argument("--exclude-crypto", action="store_true", help="Skip OKX crypto; by default it joins at its later 2018-01 start.")
    parser.add_argument("--requested-by", default=DEFAULT_REQUESTED_BY)
    parser.add_argument("--model-layer", action="append", choices=SUPPORTED_MARKET_REGIME_MODEL_LAYERS, default=[], help="Universe model_layer to plan for Alpaca bars. Defaults to Layer 1 for backward compatibility; repeat for multiple layers.")
    parser.add_argument("--format", choices=("jsonl", "json", "csv"), default="jsonl")
    parser.add_argument("--inventory", action="store_true", help="Print source availability inventory instead of requests.")
    args = parser.parse_args(argv)

    if args.inventory:
        json.dump(source_inventory(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    requests = plan_monthly_backfill_requests(
        start_month=args.start_month,
        end_month=args.end_month,
        include_crypto=not args.exclude_crypto,
        requested_by=args.requested_by,
        model_layers=tuple(args.model_layer) if args.model_layer else (LAYER_ONE_MODEL_LAYER,),
    )
    write_requests(requests, output=sys.stdout, output_format=args.format)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

"""Materialize manager request parameter payloads behind `parameter_ref`.

Manager SQL stores concise request facts. Component-readable task parameters live
as storage payloads referenced by `manager_request.parameter_ref` and recorded as
`input_binding` rows when SQL persistence is requested.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence, TextIO

from .monthly_backfill import load_market_regime_universe
from .control_plane import (
    INPUT_BINDING_COLUMNS,
    TaskSystemError,
    fetch_manager_requests,
    load_json_or_jsonl,
    persist_input_bindings,
    validate_manager_request,
)

REQUEST_KIND = "data_backfill_month"
PARAMETER_SCHEMA_REF = "manager_request_parameter_payload"
DEFAULT_STORAGE_ROOT = Path("storage")
ALPACA_BARS_MONTHLY_MAX_PAGES = 30


@dataclass(frozen=True)
class FeedTaskDefaults:
    """Default dry-run-safe task parameters for one historical feed."""

    source_id: str
    feed_id: str
    params: Mapping[str, Any]


FEED_TASK_DEFAULTS: dict[str, FeedTaskDefaults] = {
    "01_feed_alpaca_bars": FeedTaskDefaults(
        source_id="alpaca_bars",
        feed_id="01_feed_alpaca_bars",
        params={
            "symbol": "SPY",
            "timeframe": "1Day",
            "adjustment": "raw",
            "limit": 1000,
            "max_pages": ALPACA_BARS_MONTHLY_MAX_PAGES,
        },
    ),
    "02_feed_alpaca_liquidity": FeedTaskDefaults(
        source_id="alpaca_liquidity",
        feed_id="02_feed_alpaca_liquidity",
        params={"symbol": "SPY", "timeframe": "1Min", "limit": 1000, "max_pages": 1},
    ),
    "03_feed_alpaca_news": FeedTaskDefaults(
        source_id="alpaca_news",
        feed_id="03_feed_alpaca_news",
        params={"symbols": ["SPY"], "limit": 50, "max_pages": 1},
    ),
    "04_feed_okx_crypto_market_data": FeedTaskDefaults(
        source_id="okx_crypto_market_data",
        feed_id="04_feed_okx_crypto_market_data",
        params={"inst_id": "BTC-USDT", "bar": "1D", "limit": 100},
    ),
    "05_feed_gdelt_news": FeedTaskDefaults(
        source_id="gdelt_news",
        feed_id="05_feed_gdelt_news",
        params={"topic_categories": ["politics", "economy", "technology"], "focus": "us_market", "max_rows": 100, "dry_run": True},
    ),
    "07_feed_trading_economics_calendar_web": FeedTaskDefaults(
        source_id="trading_economics_calendar_web",
        feed_id="07_feed_trading_economics_calendar_web",
        params={"country": "United States", "importance": "3", "allow_live_fetch": False},
    ),
    "08_feed_sec_company_financials": FeedTaskDefaults(
        source_id="sec_company_financials",
        feed_id="08_feed_sec_company_financials",
        params={"data_kind": "sec_company_fact", "cik": "0000320193", "taxonomy": "us-gaap", "tag": "Revenues", "unit": "USD"},
    ),
    "10_feed_thetadata_option_primary_tracking": FeedTaskDefaults(
        source_id="thetadata_option_primary_tracking",
        feed_id="10_feed_thetadata_option_primary_tracking",
        params={"underlying": "AAPL", "expiration": "2016-01-15", "right": "CALL", "strike": "100", "timeframe": "1Day"},
    ),
    "11_feed_thetadata_option_event_timeline": FeedTaskDefaults(
        source_id="thetadata_option_event_timeline",
        feed_id="11_feed_thetadata_option_event_timeline",
        params={
            "underlying": "AAPL",
            "expiration": "2016-01-15",
            "right": "CALL",
            "strike": "100",
            "timeframe": "1Day",
            "max_events": 100,
            "current_standard": {
                "standard_context": {"label": "manager_monthly_backfill_dry_run"},
                "trade_at_ask": {"min_size": 1},
            },
        },
    ),
}


@dataclass(frozen=True)
class MaterializedRequestPayload:
    """Filesystem and SQL-binding metadata for one materialized payload."""

    request_id: str
    parameter_ref: str
    local_path: Path
    content_hash: str
    byte_size: int
    payload: dict[str, Any]
    input_binding: dict[str, Any]

    def summary_row(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "parameter_ref": self.parameter_ref,
            "local_path": str(self.local_path),
            "content_hash": self.content_hash,
            "byte_size": self.byte_size,
            "binding_id": self.input_binding["binding_id"],
            "schema_ref": self.input_binding["schema_ref"],
        }


def _parameter_ref_parts(parameter_ref: str) -> list[str]:
    marker = "storage://trading-manager/monthly_backfill/"
    if not parameter_ref.startswith(marker):
        return []
    return parameter_ref[len(marker) :].split("/")


def _source_from_parameter_ref(parameter_ref: str) -> str | None:
    parts = _parameter_ref_parts(parameter_ref)
    return parts[0] if len(parts) >= 3 else None


def _symbol_from_parameter_ref(parameter_ref: str) -> str | None:
    parts = _parameter_ref_parts(parameter_ref)
    if len(parts) >= 4 and parts[0] == "alpaca_bars" and parts[-1] == "task_key.json":
        return parts[1].upper()
    return None


def _market_regime_timeframe(symbol: str, *, model_layer: str | None = None) -> str | None:
    layers = [model_layer] if model_layer else None
    for member in load_market_regime_universe(model_layers=layers):
        if member.symbol == symbol.upper():
            return member.timeframe
    return None


def _month_from_request(row: Mapping[str, Any]) -> str:
    month = row.get("month")
    if month:
        return str(month)
    parameter_ref = str(row.get("parameter_ref") or "")
    parts = parameter_ref.split("/")
    if len(parts) >= 2 and parts[-1] == "task_key.json":
        return parts[-2]
    raise TaskSystemError(f"request {row.get('request_id')} missing month and parseable parameter_ref")


def _window_from_request(row: Mapping[str, Any], month: str) -> tuple[str, str]:
    start = row.get("start_date")
    end = row.get("end_date_exclusive")
    if start and end:
        return str(start), str(end)
    year_text, month_text = month.split("-", 1)
    year = int(year_text)
    month_number = int(month_text)
    if not 1 <= month_number <= 12:
        raise TaskSystemError(f"invalid request month: {month}")
    next_year = year + 1 if month_number == 12 else year
    next_month = 1 if month_number == 12 else month_number + 1
    return f"{year:04d}-{month_number:02d}-01", f"{next_year:04d}-{next_month:02d}-01"


def storage_uri_to_local_path(uri: str, *, storage_root: Path = DEFAULT_STORAGE_ROOT) -> Path:
    """Map a trading-manager storage URI to a local storage-root path."""

    prefix = "storage://trading-manager/"
    if not uri.startswith(prefix):
        raise TaskSystemError("parameter_ref must start with storage://trading-manager/")
    relative = uri[len(prefix) :]
    if not relative or relative.startswith("/") or ".." in Path(relative).parts:
        raise TaskSystemError("parameter_ref contains an unsafe storage path")
    return storage_root / relative


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _task_params(row: Mapping[str, Any], defaults: FeedTaskDefaults, start_date: str, end_date_exclusive: str) -> dict[str, Any]:
    params = dict(defaults.params)
    feed_id = defaults.feed_id
    if feed_id == "01_feed_alpaca_bars":
        if row.get("symbol"):
            params["symbol"] = str(row["symbol"]).upper()
        if row.get("timeframe"):
            params["timeframe"] = str(row["timeframe"])
    if feed_id in {"01_feed_alpaca_bars", "02_feed_alpaca_liquidity", "03_feed_alpaca_news"}:
        params.setdefault("start", start_date)
        params.setdefault("end", end_date_exclusive)
    elif feed_id == "05_feed_gdelt_news":
        params.setdefault("start_date", start_date)
        params.setdefault("end_date", end_date_exclusive)
    elif feed_id == "07_feed_trading_economics_calendar_web":
        params.setdefault("start_date", start_date)
        params.setdefault("end_date", end_date_exclusive)
    elif feed_id in {"10_feed_thetadata_option_primary_tracking", "11_feed_thetadata_option_event_timeline"}:
        params.setdefault("start_date", start_date)
        params.setdefault("end_date", end_date_exclusive)
    params.setdefault("manager_request_id", row["request_id"])
    params.setdefault("manager_dry_run", bool(row.get("dry_run", True)))
    return params


def build_request_task_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    """Build the component-readable task_key payload for one request row."""

    request = validate_manager_request(row)
    if request["request_kind"] != REQUEST_KIND:
        raise TaskSystemError(f"request_kind must be {REQUEST_KIND}")
    feed_id = str(request["target_component_id"])
    defaults = FEED_TASK_DEFAULTS.get(feed_id)
    if defaults is None:
        raise TaskSystemError(f"unsupported monthly backfill target_component_id: {feed_id}")
    parameter_ref = str(request.get("parameter_ref") or "")
    if not parameter_ref:
        raise TaskSystemError(f"request {request['request_id']} missing parameter_ref")
    ref_source = _source_from_parameter_ref(parameter_ref)
    if ref_source and ref_source != defaults.source_id:
        raise TaskSystemError(f"parameter_ref source {ref_source!r} does not match component {feed_id!r}")
    month = _month_from_request(row)
    start_date, end_date_exclusive = _window_from_request(row, month)
    expected_outputs = list(request.get("expected_outputs") or [])
    symbol = row.get("symbol") or _symbol_from_parameter_ref(parameter_ref)
    enriched_row = dict(request)
    enriched_row.update(dict(row))
    if symbol:
        enriched_row["symbol"] = str(symbol).upper()
        enriched_row.setdefault("timeframe", _market_regime_timeframe(str(symbol), model_layer=str(row.get("model_layer") or "") or None) or defaults.params.get("timeframe"))
    output_root = (
        f"storage/monthly_backfill/{defaults.source_id}/{str(symbol).upper()}/{month}"
        if symbol and feed_id == "01_feed_alpaca_bars"
        else f"storage/monthly_backfill/{defaults.source_id}/{month}"
    )
    manager_controls: dict[str, Any] = {
        "parameter_ref": parameter_ref,
        "allow_live_provider_calls": not bool(request.get("dry_run", True)),
        "autonomous_historical_provider_acquisition": not bool(request.get("dry_run", True)),
        "secrets_policy": "secret_aliases_only",
    }
    if feed_id == "01_feed_alpaca_bars":
        manager_controls.update(
            {
                "allowed_providers": ["alpaca"],
                "allowed_endpoint_families": ["bars"],
                "max_symbols": 1,
                "max_requests": ALPACA_BARS_MONTHLY_MAX_PAGES,
                "max_time_window": "31d",
            }
        )
    return {
        "contract_type": PARAMETER_SCHEMA_REF,
        "task_id": request["request_id"],
        "request_id": request["request_id"],
        "request_kind": request["request_kind"],
        "feed": feed_id,
        "source_id": defaults.source_id,
        "target_repo_id": request["target_repo_id"],
        "target_component_kind": request["target_component_kind"],
        "production_mode": "dry_run" if request.get("dry_run", True) else "historical_provider_acquisition",
        "dry_run": bool(request.get("dry_run", True)),
        "month": month,
        "window": {"start_date": start_date, "end_date_exclusive": end_date_exclusive},
        "params": _task_params(enriched_row, defaults, start_date, end_date_exclusive),
        "output_root": output_root,
        "expected_outputs": expected_outputs,
        "policy_refs": list(request.get("policy_refs") or []),
        "manager_controls": manager_controls,
    }


def build_input_binding(row: Mapping[str, Any], *, content_hash: str, byte_size: int) -> dict[str, Any]:
    """Build the request-scoped `input_binding` row for a parameter payload."""

    request = validate_manager_request(row)
    parameter_ref = str(request.get("parameter_ref") or "")
    month = _month_from_request(row)
    start_date, end_date_exclusive = _window_from_request(row, month)
    return {
        "binding_id": f"bind_param_{request['request_id']}",
        "contract_type": "input_binding",
        "request_id": request["request_id"],
        "run_id": None,
        "input_role": "parameter_payload",
        "input_ref": parameter_ref,
        "available_at_utc": None,
        "as_of_utc": None,
        "version_ref": content_hash,
        "entity_scope": str(request["target_component_id"]),
        "time_window": f"{start_date}/{end_date_exclusive}",
        "schema_ref": PARAMETER_SCHEMA_REF,
        "quality_ref": f"byte_size={byte_size};canonical_json_sha256",
        "lineage_ref": f"trading_manager.manager_request:{request['request_id']}",
    }


def materialize_request_payload(
    row: Mapping[str, Any],
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    write_file: bool = False,
) -> MaterializedRequestPayload:
    """Build and optionally write one request parameter payload."""

    payload = build_request_task_payload(row)
    content = _canonical_bytes(payload)
    content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
    parameter_ref = str(validate_manager_request(row).get("parameter_ref") or "")
    local_path = storage_uri_to_local_path(parameter_ref, storage_root=storage_root)
    binding = build_input_binding(row, content_hash=content_hash, byte_size=len(content))
    if write_file:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content)
    return MaterializedRequestPayload(
        request_id=str(payload["request_id"]),
        parameter_ref=parameter_ref,
        local_path=local_path,
        content_hash=content_hash,
        byte_size=len(content),
        payload=payload,
        input_binding=binding,
    )


def materialize_request_payloads(
    rows: Iterable[Mapping[str, Any]],
    *,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    write_files: bool = False,
) -> list[MaterializedRequestPayload]:
    return [materialize_request_payload(row, storage_root=storage_root, write_file=write_files) for row in rows]


def write_materialization_output(
    materialized: Sequence[MaterializedRequestPayload],
    *,
    output: TextIO,
    output_format: Literal["jsonl", "json"] = "jsonl",
    include_payload: bool = False,
) -> None:
    rows = []
    for item in materialized:
        row = item.summary_row()
        row["input_binding"] = item.input_binding
        if include_payload:
            row["payload"] = item.payload
        rows.append(row)
    if output_format == "json":
        json.dump(rows, output, indent=2, sort_keys=True)
        output.write("\n")
        return
    for row in rows:
        output.write(json.dumps(row, sort_keys=True) + "\n")


def _load_rows_from_args(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.from_db:
        if args.path is not None:
            raise TaskSystemError("pass either path or --from-db, not both")
        return fetch_manager_requests(
            database_url=args.database_url,
            request_kind=args.request_kind,
            status=args.status,
            request_ids=args.request_id,
            limit=args.limit,
            include_rehearsals=args.include_rehearsals,
        )
    if args.path is None:
        raise TaskSystemError("path is required unless --from-db is set")
    return [validate_manager_request(row) for row in load_json_or_jsonl(args.path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Materialize manager request parameter payloads behind parameter_ref.")
    parser.add_argument("path", nargs="?", type=Path, help="JSON, JSON array, or JSONL manager_request rows.")
    parser.add_argument("--from-db", action="store_true", help="Fetch request rows from trading_manager.manager_request.")
    parser.add_argument("--database-url")
    parser.add_argument("--request-kind", default=REQUEST_KIND)
    parser.add_argument("--status", default="requested")
    parser.add_argument("--request-id", action="append", help="Limit SQL fetch to one request id; repeatable.")
    parser.add_argument("--include-rehearsals", action="store_true", help="Include mgrreq_rehearsal_* rows when fetching from SQL.")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--write-files", action="store_true", help="Write task_key.json files under --storage-root.")
    parser.add_argument("--write-bindings", action="store_true", help="Persist input_binding rows for materialized payloads.")
    parser.add_argument("--format", choices=("jsonl", "json"), default="jsonl")
    parser.add_argument("--include-payload", action="store_true", help="Include full payload bodies in stdout.")
    args = parser.parse_args(argv)

    if args.write_bindings and not args.write_files:
        raise TaskSystemError("--write-bindings requires --write-files so SQL does not point at missing payloads")
    rows = _load_rows_from_args(args)
    materialized = materialize_request_payloads(rows, storage_root=args.storage_root, write_files=args.write_files)
    if args.write_bindings:
        persist_input_bindings([item.input_binding for item in materialized], database_url=args.database_url)
    write_materialization_output(materialized, output=sys.stdout, output_format=args.format, include_payload=args.include_payload)
    return 0


__all__ = [
    "ALPACA_BARS_MONTHLY_MAX_PAGES",
    "FEED_TASK_DEFAULTS",
    "PARAMETER_SCHEMA_REF",
    "REQUEST_KIND",
    "MaterializedRequestPayload",
    "build_input_binding",
    "build_request_task_payload",
    "materialize_request_payload",
    "materialize_request_payloads",
    "storage_uri_to_local_path",
    "write_materialization_output",
]


if __name__ == "__main__":  # pragma: no cover - exercised through script wrapper.
    raise SystemExit(main())

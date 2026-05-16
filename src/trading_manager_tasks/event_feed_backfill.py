"""Layer 8 event-feed backfill preparation helpers.

This module prepares the reviewed local feed artifacts required by the Layer 8
`source_08_event_risk_governor` coverage gate. It only writes manager task-key files;
it does not call providers, activate models, submit broker orders, mutate
accounts, or write dashboard read models.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, TextIO

from .control_plane import TaskSystemError
from .monthly_backfill import MonthlyWindow, iter_monthly_windows
from .request_payloads import DEFAULT_STORAGE_ROOT, build_request_task_payload, storage_uri_to_local_path

DEFAULT_TARGET_SYMBOL = "AAPL"
DEFAULT_TARGET_CIK = "0000320193"
DEFAULT_REQUESTED_BY = "trading-manager.layer_eight_event_feed_backfill"
REQUIRED_EVENT_FEED_IDS = (
    "03_feed_alpaca_news",
    "05_feed_gdelt_news",
    "07_feed_trading_economics_calendar_web",
    "08_feed_sec_company_financials",
)
SOURCE_BY_FEED_ID = {
    "03_feed_alpaca_news": "alpaca_news",
    "05_feed_gdelt_news": "gdelt_news",
    "07_feed_trading_economics_calendar_web": "trading_economics_calendar_web",
    "08_feed_sec_company_financials": "sec_company_financials",
}


@dataclass(frozen=True)
class EventFeedTaskKey:
    request_id: str
    feed_id: str
    source_id: str
    month: str
    parameter_ref: str
    local_path: str
    byte_size: int
    content_hash: str

    def summary_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventFeedBackfillSummary:
    contract_type: str
    start_month: str
    end_month: str
    target_symbol: str
    target_cik: str
    request_count: int
    task_key_count: int
    write_performed: bool
    provider_calls: int
    model_activation_performed: bool
    broker_execution_performed: bool
    dashboard_read_model_writes: int
    task_keys: tuple[EventFeedTaskKey, ...]

    def summary_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["task_keys"] = [item.summary_row() for item in self.task_keys]
        return row


def _request_id(feed_id: str, month: str, target_symbol: str) -> str:
    source_id = SOURCE_BY_FEED_ID[feed_id]
    return f"mgrreq_event_backfill_{source_id}_{target_symbol.lower()}_{month.replace('-', '_')}"


def _parameter_ref(feed_id: str, month: str, target_symbol: str) -> str:
    source_id = SOURCE_BY_FEED_ID[feed_id]
    return f"storage://trading-manager/monthly_backfill/{source_id}/{month}/task_key.json"


def _base_request(feed_id: str, window: MonthlyWindow, *, target_symbol: str) -> dict[str, Any]:
    source_id = SOURCE_BY_FEED_ID[feed_id]
    return {
        "request_id": _request_id(feed_id, window.month, target_symbol),
        "contract_type": "manager_request",
        "request_kind": "data_backfill_month",
        "status": "requested",
        "requested_by": DEFAULT_REQUESTED_BY,
        "target_component_id": feed_id,
        "target_component_kind": "data_feed",
        "target_repo_id": "trading-data",
        "expected_outputs": [f"storage://trading-data/monthly_backfill/{source_id}/{window.month}/"],
        "policy_refs": ["read_only_provider_acquisition", "secret_aliases_only", "no_model_activation", "no_broker_execution"],
        "priority": "high",
        "parameter_ref": _parameter_ref(feed_id, window.month, target_symbol),
        "dry_run": True,
        "month": window.month,
        "start_date": window.start_date,
        "end_date_exclusive": window.end_date_exclusive,
        "symbol": target_symbol.upper(),
        "availability_note": "Layer 8 event-risk source coverage repair; reviewed artifact required before downstream rebuild.",
    }


def _enrich_payload(payload: dict[str, Any], *, target_symbol: str, target_cik: str) -> dict[str, Any]:
    feed_id = str(payload["feed"])
    params = dict(payload.get("params") or {})
    if feed_id == "03_feed_alpaca_news":
        params.update({"symbols": [target_symbol.upper()], "limit": 50, "max_pages": 10})
    elif feed_id == "05_feed_gdelt_news":
        params.update(
            {
                "topic_categories": ["politics", "economy", "technology"],
                "focus": "us_market",
                "impact_scope": "market;sector;symbol",
                "max_rows": 250,
                "dry_run": True,
                "query_terms": [
                    target_symbol.upper(),
                    "earnings",
                    "revenue",
                    "guidance",
                    "federal reserve",
                    "inflation",
                    "jobs",
                    "payrolls",
                    "gdp",
                    "interest rates",
                ],
            }
        )
    elif feed_id == "07_feed_trading_economics_calendar_web":
        params.update({"country": "United States", "importance": "3", "allow_live_fetch": False})
    elif feed_id == "08_feed_sec_company_financials":
        params.update({"data_kind": "sec_company_fact", "cik": str(target_cik).zfill(10), "taxonomy": "us-gaap"})
        params.pop("tag", None)
        params.pop("unit", None)
    payload["params"] = params
    return payload


def plan_event_feed_requests(*, start_month: str, end_month: str, target_symbol: str = DEFAULT_TARGET_SYMBOL) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for window in iter_monthly_windows(start_month, end_month):
        for feed_id in REQUIRED_EVENT_FEED_IDS:
            requests.append(_base_request(feed_id, window, target_symbol=target_symbol))
    return requests


def prepare_event_feed_backfill(
    *,
    start_month: str,
    end_month: str,
    target_symbol: str = DEFAULT_TARGET_SYMBOL,
    target_cik: str = DEFAULT_TARGET_CIK,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
    write_files: bool = False,
) -> EventFeedBackfillSummary:
    requests = plan_event_feed_requests(start_month=start_month, end_month=end_month, target_symbol=target_symbol)
    task_keys: list[EventFeedTaskKey] = []
    for request in requests:
        payload = _enrich_payload(build_request_task_payload(request), target_symbol=target_symbol, target_cik=target_cik)
        content = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        # Reuse the canonical materializer path convention while preserving the enriched payload.
        local_path = storage_uri_to_local_path(str(request["parameter_ref"]), storage_root=storage_root)
        import hashlib

        content_hash = "sha256:" + hashlib.sha256(content).hexdigest()
        if write_files:
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)
        task_keys.append(
            EventFeedTaskKey(
                request_id=str(request["request_id"]),
                feed_id=str(request["target_component_id"]),
                source_id=SOURCE_BY_FEED_ID[str(request["target_component_id"])],
                month=str(request["month"]),
                parameter_ref=str(request["parameter_ref"]),
                local_path=str(local_path),
                byte_size=len(content),
                content_hash=content_hash,
            )
        )
    return EventFeedBackfillSummary(
        contract_type="manager_layer_eight_event_feed_backfill_preparation",
        start_month=start_month,
        end_month=end_month,
        target_symbol=target_symbol.upper(),
        target_cik=str(target_cik).zfill(10),
        request_count=len(requests),
        task_key_count=len(task_keys),
        write_performed=write_files,
        provider_calls=0,
        model_activation_performed=False,
        broker_execution_performed=False,
        dashboard_read_model_writes=0,
        task_keys=tuple(task_keys),
    )


def write_summary(summary: EventFeedBackfillSummary, *, output: TextIO) -> None:
    json.dump(summary.summary_row(), output, indent=2, sort_keys=True)
    output.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare Layer 8 event-feed backfill task keys without provider calls.")
    parser.add_argument("--start-month", required=True)
    parser.add_argument("--end-month", required=True)
    parser.add_argument("--target-symbol", default=DEFAULT_TARGET_SYMBOL)
    parser.add_argument("--target-cik", default=DEFAULT_TARGET_CIK)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE_ROOT)
    parser.add_argument("--write-files", action="store_true")
    args = parser.parse_args(argv)
    summary = prepare_event_feed_backfill(
        start_month=args.start_month,
        end_month=args.end_month,
        target_symbol=args.target_symbol,
        target_cik=args.target_cik,
        storage_root=args.storage_root,
        write_files=args.write_files,
    )
    write_summary(summary, output=sys.stdout)
    return 0


__all__ = [
    "EventFeedBackfillSummary",
    "EventFeedTaskKey",
    "REQUIRED_EVENT_FEED_IDS",
    "plan_event_feed_requests",
    "prepare_event_feed_backfill",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

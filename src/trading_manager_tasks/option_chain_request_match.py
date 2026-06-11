"""Request matching for the current shared option-chain source route."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

OPTION_CHAIN_SOURCE_ID = "option_chain_state_source"
OPTION_CHAIN_REQUEST_KIND = "option_chain_snapshot"
OPTION_CHAIN_TARGET_COMPONENT_ID = OPTION_CHAIN_SOURCE_ID


def _add_month(month: str) -> str:
    year = int(month[:4])
    month_number = int(month[5:])
    if month_number == 12:
        return f"{year + 1:04d}-01"
    return f"{year:04d}-{month_number + 1:02d}"


def _iter_months(start_month: str, end_month: str) -> Iterable[str]:
    month = start_month
    while month <= end_month:
        yield month
        month = _add_month(month)


def is_current_option_chain_request(row: Mapping[str, Any], *, start_month: str, end_month: str) -> bool:
    """Return whether a manager request belongs to the accepted option-source fold route."""

    if row.get("target_component_id") != OPTION_CHAIN_TARGET_COMPONENT_ID or row.get("request_kind") != OPTION_CHAIN_REQUEST_KIND:
        return False
    request_id = str(row.get("request_id") or "")
    if not request_id.startswith("mgrreq_option_chain_window_"):
        return False
    parameter_ref = str(row.get("parameter_ref") or "")
    current_prefix = f"storage://trading-manager/runtime/model_05_option_expression/{OPTION_CHAIN_SOURCE_ID}/"
    months = tuple(_iter_months(start_month, end_month))
    if parameter_ref:
        return parameter_ref.startswith(current_prefix) and any(f"/{month}/" in parameter_ref for month in months)
    month_tokens = tuple(month.replace("-", "_") for month in months)
    return any(f"_{token}_" in request_id for token in month_tokens)

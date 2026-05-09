"""Manager-owned task planning helpers."""

from .control_plane import (
    CompletionReceiptRows,
    normalize_completion_receipt,
    validate_manager_request,
)
from .monthly_backfill import (
    DEFAULT_SOURCES,
    MonthlyWindow,
    SourceAvailability,
    iter_monthly_windows,
    plan_monthly_backfill_requests,
)

__all__ = [
    "CompletionReceiptRows",
    "DEFAULT_SOURCES",
    "MonthlyWindow",
    "SourceAvailability",
    "iter_monthly_windows",
    "normalize_completion_receipt",
    "plan_monthly_backfill_requests",
    "validate_manager_request",
]

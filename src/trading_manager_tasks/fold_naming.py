"""Naming helpers for target-scoped cumulative walk-forward folds."""

from __future__ import annotations

import re


def safe_target_token(target_symbol: str | None) -> str | None:
    """Return the stable lowercase token used in target-scoped fold names."""

    if not target_symbol:
        return None
    token = "".join(char.lower() if char.isalnum() else "_" for char in target_symbol.strip().upper())
    token = "_".join(part for part in token.split("_") if part)
    return token or None


def training_year_from_start_month(start_month: str) -> str:
    """Return the training-year token from a YYYY-MM fold start month."""

    if not re.fullmatch(r"\d{4}-\d{2}", start_month):
        raise ValueError(f"invalid fold start month: {start_month}")
    return start_month[:4]


def model_worker_fold_id(*, target_symbol: str | None, start_month: str) -> str:
    """Return the current business fold id, e.g. ``fold_aapl_2016``."""

    target = safe_target_token(target_symbol) or "unscoped"
    return f"fold_{target}_{training_year_from_start_month(start_month)}"


def date_range_fold_id(*, start_month: str, end_month: str) -> str:
    """Return the legacy date-range fold id for compatibility checks."""

    return f"fold_{start_month}_{end_month}"


def parse_model_worker_fold_id(fold_id: str) -> tuple[str, str] | None:
    """Parse ``fold_<target>_<year>`` into ``(target_token, year)``."""

    match = re.fullmatch(r"fold_([a-z0-9]+)_(\d{4})", fold_id.strip().lower())
    if not match:
        return None
    return match.group(1), match.group(2)


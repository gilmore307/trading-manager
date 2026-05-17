#!/usr/bin/env python3
"""Verify manager-facing layer names and tokens stay aligned."""

from __future__ import annotations

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

LAYERS = (
    (1, ("MarketRegimeModel",), "layer_01_market_regime", "model_01_market_regime", "market_context_state"),
    (2, ("SectorContextModel",), "layer_02_sector_context", "model_02_sector_context", "sector_context_state"),
    (3, ("TargetStateVectorModel",), "layer_03_target_state_vector", "model_03_target_state_vector", "target_context_state"),
    (4, ("EventFailureRiskModel",), "layer_04_event_failure_risk", "model_04_event_failure_risk", "event_failure_risk_vector"),
    (5, ("AlphaConfidenceModel",), "layer_05_alpha_confidence", "model_05_alpha_confidence", "alpha_confidence_vector"),
    (6, ("PositionProjectionModel",), "layer_06_position_projection", "model_06_position_projection", "position_projection_vector"),
    (7, ("UnderlyingActionModel",), "layer_07_underlying_action", "model_07_underlying_action", "underlying_action_plan"),
    (8, ("TradingGuidanceModel", "OptionExpressionModel"), "layer_08_option_expression", "model_08_option_expression", "option_expression_plan"),
    (9, ("EventRiskGovernor", "EventIntelligenceOverlay"), "layer_09_event_risk_governor", "model_09_event_risk_governor", "event_risk_intervention"),
)

FILES_TO_CHECK = (
    "docs/02_architecture.md",
    "docs/28_numbering_physical_contract.md",
    "src/trading_manager_tasks/model_promotion.py",
)

APPEND_ONLY_PREFIXES = (
    "scripts/registry/sql/schema_migrations/",
)

STALE_LAYER_DOC_RE = re.compile(r"docs/(?:8\d|1\d\d)_")


def fail(message: str) -> None:
    raise SystemExit(f"layer token check failed: {message}")


def read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def current_registry_text() -> str:
    path = REPO_ROOT / "scripts/registry/current.csv"
    with path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        fail("scripts/registry/current.csv has no rows")
    return "\n".join(
        "\t".join(str(row.get(column, "")) for column in row.keys())
        for row in rows
    )


def main() -> int:
    texts = {rel: read(rel) for rel in FILES_TO_CHECK}
    registry = current_registry_text()

    for number, boundaries, layer_token, model_token, handoff in LAYERS:
        architecture = texts["docs/02_architecture.md"]
        numbering = texts["docs/28_numbering_physical_contract.md"]
        promotion = texts["src/trading_manager_tasks/model_promotion.py"]
        for rel, text in texts.items():
            for token in (layer_token, model_token):
                if token not in text:
                    fail(f"{rel} missing {token}")
        for value in (*boundaries, handoff):
            if value not in architecture:
                fail(f"docs/02_architecture.md missing {value}")
        if not all(boundary in numbering for boundary in boundaries):
            fail(f"docs/28_numbering_physical_contract.md missing one of {boundaries}")
        if not any(boundary in promotion for boundary in boundaries):
            fail(f"model_promotion.py missing one of {boundaries}")
        for token in (layer_token, model_token):
            if token not in registry:
                fail(f"scripts/registry/current.csv missing {token}")

    scanned_roots = ["README.md", "docs", "src", "scripts", "tests"]
    stale_refs: list[str] = []
    for root in scanned_roots:
        start = REPO_ROOT / root
        paths = [start] if start.is_file() else sorted(start.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            rel = str(path.relative_to(REPO_ROOT))
            if any(rel.startswith(prefix) for prefix in APPEND_ONLY_PREFIXES):
                continue
            if rel == "scripts/registry/current.csv":
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if STALE_LAYER_DOC_RE.search(text):
                stale_refs.append(rel)
    if stale_refs:
        fail(f"active surfaces reference stale 80+/100+ docs numbering: {sorted(set(stale_refs))}")

    print(f"layer tokens OK ({len(LAYERS)} layers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

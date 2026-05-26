#!/usr/bin/env python3
"""Verify manager-facing layer names and tokens stay aligned."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from trading_manager_tasks.registry_values import registry_payload

LAYER_REGISTRY_IDS = (
    (1, ("MarketRegimeModel",), "mlv_L1MR001", "trm_MRM001", "dki_MRMV001", "trm_MCS001"),
    (2, ("SectorContextModel",), "mlv_L2SC001", "trm_SCM001", "trm_M2S001", "trm_SCS001"),
    (3, ("TargetStateVectorModel",), "mlv_L3TSV01", "trm_TSVMI01", "trm_M3TSV01", "trm_TSV001"),
    (4, ("EventFailureRiskModel",), "mlv_L4EFR001", "trm_EFRM001", "trm_MEFR001", "trm_EFRV001"),
    (5, ("AlphaConfidenceModel",), "mlv_L5AC001", "trm_ACM001", "trm_MAC001", "trm_ASV001"),
    (6, ("DynamicRiskPolicyModel",), "mlv_L6DRP001", "trm_DRPM001", "trm_M6DRP01", "trm_DRPS001"),
    (7, ("PositionProjectionModel",), "mlv_L7PP001", "trm_TPM001", "trm_MTP001", "trm_TSVEC01"),
    (8, ("UnderlyingActionModel",), "mlv_L8UA001", "trm_UAM001", "trm_M7UAM01", "trm_UAP001"),
    (9, ("TradingGuidanceModel", "OptionExpressionModel"), "mlv_L9OE001", "trm_OEM001", "trm_M7OEM01", "trm_OEP001"),
    (10, ("EventRiskGovernor", "EventIntelligenceOverlay"), "mlv_L10ERG001", "trm_ERG001", "trm_M9ERG01", "trm_ERI001"),
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


def layers() -> tuple[tuple[int, tuple[str, ...], str, str, str, str], ...]:
    return tuple(
        (
            number,
            boundaries,
            registry_payload(layer_id),
            registry_payload(stable_model_id),
            registry_payload(model_token_id),
            registry_payload(handoff_id),
        )
        for number, boundaries, layer_id, stable_model_id, model_token_id, handoff_id in LAYER_REGISTRY_IDS
    )


def main() -> int:
    texts = {rel: read(rel) for rel in FILES_TO_CHECK}
    registry = current_registry_text()

    layer_rows = layers()
    for number, boundaries, layer_token, stable_model_id, model_token, handoff in layer_rows:
        architecture = texts["docs/02_architecture.md"]
        numbering = texts["docs/28_numbering_physical_contract.md"]
        promotion = texts["src/trading_manager_tasks/model_promotion.py"]
        for rel, text in texts.items():
            required_tokens = (layer_token, stable_model_id) if rel == "src/trading_manager_tasks/model_promotion.py" else (layer_token, model_token)
            for token in required_tokens:
                if token not in text:
                    fail(f"{rel} missing {token}")
        for value in (*boundaries, handoff):
            if value not in architecture:
                fail(f"docs/02_architecture.md missing {value}")
        if not all(boundary in numbering for boundary in boundaries):
            fail(f"docs/28_numbering_physical_contract.md missing one of {boundaries}")
        if not any(boundary in promotion for boundary in boundaries):
            fail(f"model_promotion.py missing one of {boundaries}")
        for token in (layer_token, stable_model_id, model_token):
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

    print(f"layer tokens OK ({len(layer_rows)} layers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

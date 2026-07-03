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

MODEL_REGISTRY_IDS = (
    (1, ("BackgroundContextModel",), "trm_M1BC001", "trm_BCM001", "trm_BCS001"),
    (2, ("TargetStateModel",), "trm_M2TS001", "trm_TSM002", "trm_TSV001"),
    (3, ("EventStateModel",), "trm_M3ES001", "trm_ESM001", "trm_ESV001"),
    (4, ("UnifiedDecisionModel",), "trm_M4UD001", "trm_UDM001", "trm_UDV001"),
    (5, ("OptionExpressionModel",), "trm_M5OE002", "trm_OEM001", "trm_OEP001"),
)

FILES_TO_CHECK = (
    "docs/02_architecture.md",
    "docs/28_numbering_physical_contract.md",
    "src/trading_manager_tasks/model_promotion.py",
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


def layers() -> tuple[tuple[int, tuple[str, ...], str, str, str], ...]:
    return tuple(
        (
            number,
            boundaries,
            registry_payload(physical_model_id),
            registry_payload(stable_model_id),
            registry_payload(output_id),
        )
        for number, boundaries, physical_model_id, stable_model_id, output_id in MODEL_REGISTRY_IDS
    )


def main() -> int:
    texts = {rel: read(rel) for rel in FILES_TO_CHECK}
    registry = current_registry_text()

    layer_rows = layers()
    for number, boundaries, physical_model_id, stable_model_id, output_contract in layer_rows:
        architecture = texts["docs/02_architecture.md"]
        numbering = texts["docs/28_numbering_physical_contract.md"]
        promotion = texts["src/trading_manager_tasks/model_promotion.py"]
        for rel, text in texts.items():
            required_tokens = (
                (physical_model_id, stable_model_id)
                if rel == "src/trading_manager_tasks/model_promotion.py"
                else (physical_model_id, stable_model_id, output_contract)
            )
            for token in required_tokens:
                if token not in text:
                    fail(f"{rel} missing {token}")
        for value in (*boundaries, output_contract):
            if value not in architecture:
                fail(f"docs/02_architecture.md missing {value}")
        if not all(boundary in numbering for boundary in boundaries):
            fail(f"docs/28_numbering_physical_contract.md missing one of {boundaries}")
        if not any(boundary in promotion for boundary in boundaries):
            fail(f"model_promotion.py missing one of {boundaries}")
        for token in (physical_model_id, stable_model_id, output_contract):
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

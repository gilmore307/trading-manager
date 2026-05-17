#!/usr/bin/env python3
"""Verify the manager documentation spine is current and complete."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
DOCS_DIR = REPO_ROOT / "docs"

EXPECTED_DOCS = (
    "docs/00_scope.md",
    "docs/01_context.md",
    "docs/02_architecture.md",
    "docs/03_contracts.md",
    "docs/04_task.md",
    "docs/05_decision.md",
    "docs/06_memory.md",
    "docs/10_registry.md",
    "docs/11_templates.md",
    "docs/20_task_system.md",
    "docs/21_monthly_backfill.md",
    "docs/22_dataset_expansion.md",
    "docs/23_controlled_information_pass.md",
    "docs/24_model_promotion.md",
    "docs/25_automation_scheduler.md",
    "docs/26_historical_scheduler_runtime.md",
    "docs/27_control_plane_acceptance.md",
    "docs/28_numbering_physical_contract.md",
    "docs/30_helpers.md",
)

DOC_REF_RE = re.compile(r"docs/\d{2}_[A-Za-z0-9_.-]+\.md")
DOC_FILE_RE = re.compile(r"^(\d{2})_[A-Za-z0-9_.-]+\.md$")


def fail(message: str) -> None:
    raise SystemExit(f"docs spine check failed: {message}")


def main() -> int:
    if not README.exists():
        fail("README.md is missing")
    readme_text = README.read_text(encoding="utf-8")
    readme_docs = tuple(dict.fromkeys(DOC_REF_RE.findall(readme_text)))
    if readme_docs != EXPECTED_DOCS:
        missing = [item for item in EXPECTED_DOCS if item not in readme_docs]
        extra = [item for item in readme_docs if item not in EXPECTED_DOCS]
        fail(f"README documentation spine drifted; missing={missing}; extra={extra}; found={list(readme_docs)}")

    missing_files = [item for item in EXPECTED_DOCS if not (REPO_ROOT / item).is_file()]
    if missing_files:
        fail(f"README lists missing docs: {missing_files}")

    active_docs: list[str] = []
    invalid_docs: list[str] = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        match = DOC_FILE_RE.match(path.name)
        if not match:
            invalid_docs.append(str(path.relative_to(REPO_ROOT)))
            continue
        number = int(match.group(1))
        rel = str(path.relative_to(REPO_ROOT))
        if 0 <= number <= 79:
            active_docs.append(rel)
        elif 90 <= number <= 99:
            continue
        else:
            invalid_docs.append(rel)
    if invalid_docs:
        fail(f"docs files must use 00-79 active or 90-99 appendix numbering: {invalid_docs}")
    if tuple(active_docs) != EXPECTED_DOCS:
        fail(f"active docs files drifted; expected={list(EXPECTED_DOCS)}; found={active_docs}")

    print(f"docs spine OK ({len(EXPECTED_DOCS)} active docs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

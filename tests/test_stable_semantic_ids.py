from __future__ import annotations

import ast
import csv
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PATHS = ("src", "tests", "docs", "README.md")
SCRIPT_CHECK_PATHS = ("scripts/tasks", "scripts/docs", "scripts/contracts")
FORBIDDEN_ACTIVE_TOKENS = ("_".join(("monthly", "backfill", "v1")),)
VERSIONED_SEMANTIC_PATTERN = re.compile(r"\\b[a-z0-9]+(?:_[a-z0-9]+)*_v[0-9]+\\b")
VERSIONED_KEY_PATTERN = re.compile(r"\\b[A-Z0-9]+(?:_[A-Z0-9]+)*_V[0-9]+\\b")


def _iter_active_text_files() -> list[Path]:
    paths: list[Path] = []
    for active_path in ACTIVE_PATHS:
        root = REPO_ROOT / active_path
        if not root.exists():
            continue
        if root.is_file():
            paths.append(root)
            continue
        for path in root.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.name == "test_stable_semantic_ids.py":
                continue
            if path.suffix in {".py", ".md", ".txt", ".json", ".csv", ".toml", ".yaml", ".yml"}:
                paths.append(path)
    return paths


def _registry_versioned_tokens() -> set[str]:
    current = REPO_ROOT / "scripts" / "registry" / "current.csv"
    text = current.read_text(encoding="utf-8")
    return set(VERSIONED_SEMANTIC_PATTERN.findall(text)) | set(VERSIONED_KEY_PATTERN.findall(text))


def _script_registry_body_literals() -> list[str]:
    with (REPO_ROOT / "scripts" / "registry" / "current.csv").open(newline="", encoding="utf-8") as handle:
        registry_rows = list(csv.DictReader(handle))
    registry_payloads = {
        row["payload"]
        for row in registry_rows
        if len(row["payload"]) >= 8
        and not row["payload"].startswith("/")
        and not row["payload"].startswith("PYTHONPATH=")
        and not row["payload"].endswith((".csv", ".md", ".py", ".service"))
        and ";" not in row["payload"]
        and "${" not in row["payload"]
    }
    registry_keys = {row["key"] for row in registry_rows}
    offenders: list[str] = []
    for root in SCRIPT_CHECK_PATHS:
        for path in sorted((REPO_ROOT / root).glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                    continue
                if node.value in registry_payloads or node.value in registry_keys:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno} hard-codes registry body {node.value}")
    return offenders


class StableSemanticIdTests(unittest.TestCase):
    def test_active_code_uses_stable_monthly_backfill_id(self) -> None:
        offenders: list[str] = []
        for path in _iter_active_text_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_ACTIVE_TOKENS:
                if token in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} contains {token}")
        self.assertEqual(offenders, [])

    def test_registry_current_has_no_versioned_semantic_tokens(self) -> None:
        self.assertEqual(sorted(_registry_versioned_tokens()), [])

    def test_global_scripts_use_registry_ids_not_registry_bodies(self) -> None:
        self.assertEqual(_script_registry_body_literals(), [])


if __name__ == "__main__":
    unittest.main()

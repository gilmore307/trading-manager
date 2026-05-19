from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PATHS = ("src", "tests", "docs", "README.md")
LEGACY_VERSIONED_TOKENS_PATH = REPO_ROOT / "tests" / "fixtures" / "allowed_versioned_semantic_tokens.txt"
FORBIDDEN_ACTIVE_TOKENS = ("_".join(("monthly", "backfill", "v1")),)
FORBIDDEN_NEW_MODEL_OUTPUT_TOKENS = (
    "_".join(("model", "output", "table", "quality", "audit", "v1")),
    "_".join(("model", "output", "quality", "gate", "v1")),
)


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
    pattern = re.compile(r"\\b[a-z0-9]+(?:_[a-z0-9]+)*_v[0-9]+\\b")
    return set(pattern.findall(current.read_text(encoding="utf-8")))


def _allowed_versioned_tokens() -> set[str]:
    return {
        line.strip()
        for line in LEGACY_VERSIONED_TOKENS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


class StableSemanticIdTests(unittest.TestCase):
    def test_active_code_uses_stable_monthly_backfill_id(self) -> None:
        offenders: list[str] = []
        for path in _iter_active_text_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_ACTIVE_TOKENS:
                if token in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} contains {token}")
        self.assertEqual(offenders, [])

    def test_model_output_quality_contracts_are_unversioned(self) -> None:
        offenders: list[str] = []
        for path in _iter_active_text_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_NEW_MODEL_OUTPUT_TOKENS:
                if token in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} contains {token}")
        self.assertEqual(offenders, [])

    def test_registry_does_not_add_unreviewed_versioned_semantic_tokens(self) -> None:
        unexpected = sorted(_registry_versioned_tokens() - _allowed_versioned_tokens())
        self.assertEqual(unexpected, [])


if __name__ == "__main__":
    unittest.main()

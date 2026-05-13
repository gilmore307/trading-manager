from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_PATHS = ("src", "tests", "docs", "README.md")
FORBIDDEN_ACTIVE_TOKENS = ("monthly_backfill_v1",)


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


class StableSemanticIdTests(unittest.TestCase):
    def test_active_code_uses_stable_monthly_backfill_id(self) -> None:
        offenders: list[str] = []
        for path in _iter_active_text_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in FORBIDDEN_ACTIVE_TOKENS:
                if token in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} contains {token}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()

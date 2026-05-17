from __future__ import annotations

import subprocess
import sys
import unittest


class GovernanceChecksTest(unittest.TestCase):
    def run_script(self, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, *args],
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout

    def test_docs_spine_check_passes(self) -> None:
        output = self.run_script("scripts/docs/check_docs_spine.py")
        self.assertIn("docs spine OK", output)

    def test_layer_token_check_passes(self) -> None:
        output = self.run_script("scripts/docs/check_layer_tokens.py")
        self.assertIn("layer tokens OK", output)

    def test_contract_examples_validate_against_schemas(self) -> None:
        output = self.run_script("scripts/contracts/validate_contract_examples.py")
        self.assertIn("contract examples OK", output)


if __name__ == "__main__":
    unittest.main()

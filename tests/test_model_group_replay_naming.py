from __future__ import annotations

import unittest
from datetime import UTC, datetime

from trading_manager_tasks.model_group_replay import _model_group_replay_run_id


class ModelGroupReplayNamingTests(unittest.TestCase):
    def test_replay_run_id_includes_current_target_fold_id(self) -> None:
        run_id = _model_group_replay_run_id(
            training_fold={"fold_id": "fold_aapl_2016"},
            now=datetime(2026, 6, 29, 12, 0, tzinfo=UTC),
        )

        self.assertEqual(run_id, "model_group_replay_fold_aapl_2016_20260629T120000Z")


if __name__ == "__main__":
    unittest.main()

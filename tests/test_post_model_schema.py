import tempfile
import unittest
from pathlib import Path

from trading_manager_tasks.post_model_schema import (
    _create_table_sql,
    registered_post_model_tables,
)


class PostModelSchemaTests(unittest.TestCase):
    def test_registered_post_model_tables_are_loaded_from_registry(self):
        tables = registered_post_model_tables()

        self.assertIn("trading_evaluation.replay_execution_run", tables)
        self.assertIn("trading_execution.c01_intake_snapshot", tables)
        self.assertEqual(tables, sorted(set(tables)))

    def test_registered_post_model_tables_filter_to_evaluation_and_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "current.csv"
            path.write_text(
                "\n".join(
                    [
                        "id,kind,key,payload_format,payload,path,applies_to,artifact_sync_policy,note,created_at,updated_at",
                        "a,sql_table,A,text,trading_evaluation.replay_contract,,,,,,",
                        "b,sql_table,B,text,trading_execution.c01_intake_snapshot,,,,,,",
                        "c,sql_table,C,text,trading_model.model_01_background_context,,,,,,",
                        "d,term,D,text,trading_execution.not_a_sql_table,,,,,,",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                registered_post_model_tables(path),
                ["trading_evaluation.replay_contract", "trading_execution.c01_intake_snapshot"],
            )

    def test_create_table_sql_uses_post_model_evidence_envelope(self):
        sql = _create_table_sql("trading_evaluation", "replay_execution_run")

        self.assertIn('CREATE TABLE IF NOT EXISTS "trading_evaluation"."replay_execution_run"', sql)
        self.assertIn("payload JSONB NOT NULL", sql)
        self.assertIn("generated_at_utc TIMESTAMPTZ", sql)


if __name__ == "__main__":
    unittest.main()

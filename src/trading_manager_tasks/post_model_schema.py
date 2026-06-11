"""Ensure SQL tables registered for post-model evaluation/execution evidence."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Iterable

DEFAULT_DB_URL_FILE = Path("/root/secrets/openclaw/database-url")
DEFAULT_REGISTRY_CSV = Path(__file__).resolve().parents[2] / "scripts" / "registry" / "current.csv"
POST_MODEL_SCHEMAS = ("trading_evaluation", "trading_execution")
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def database_url(explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    env_value = os.environ.get("OPENCLAW_DATABASE_URL", "").strip()
    if env_value:
        return env_value
    if DEFAULT_DB_URL_FILE.exists():
        return DEFAULT_DB_URL_FILE.read_text(encoding="utf-8").strip()
    raise RuntimeError(f"database URL required: pass --database-url or create {DEFAULT_DB_URL_FILE}")


def registered_post_model_tables(registry_csv: Path = DEFAULT_REGISTRY_CSV) -> list[str]:
    with registry_csv.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        tables = [
            str(row["payload"]).strip()
            for row in rows
            if row.get("kind") == "sql_table"
            and any(str(row.get("payload") or "").startswith(f"{schema}.") for schema in POST_MODEL_SCHEMAS)
        ]
    return sorted(set(tables))


def ensure_post_model_tables(
    *,
    database_url_value: str | None = None,
    registry_csv: Path = DEFAULT_REGISTRY_CSV,
    tables: Iterable[str] | None = None,
) -> dict[str, object]:
    selected_tables = tuple(tables if tables is not None else registered_post_model_tables(registry_csv))
    db_url = database_url(database_url_value)
    try:
        import psycopg  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("psycopg is required to ensure post-model SQL tables") from exc

    created_or_existing: list[str] = []
    with psycopg.connect(db_url) as connection:
        with connection.cursor() as cursor:
            for schema in POST_MODEL_SCHEMAS:
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            for table_ref in selected_tables:
                schema, table = _split_table_ref(table_ref)
                cursor.execute(_create_table_sql(schema, table))
                created_or_existing.append(table_ref)
        connection.commit()
    missing = verify_post_model_tables(database_url_value=db_url, tables=selected_tables)
    return {
        "ensured_table_count": len(created_or_existing),
        "ensured_tables": created_or_existing,
        "missing_tables": missing,
        "verification_status": "passed" if not missing else "failed",
    }


def verify_post_model_tables(*, database_url_value: str | None = None, tables: Iterable[str] | None = None) -> list[str]:
    selected_tables = tuple(tables if tables is not None else registered_post_model_tables())
    db_url = database_url(database_url_value)
    try:
        import psycopg  # type: ignore
        from psycopg.rows import dict_row  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("psycopg is required to verify post-model SQL tables") from exc

    missing: list[str] = []
    with psycopg.connect(db_url, row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            for table_ref in selected_tables:
                cursor.execute("SELECT to_regclass(%s) AS table_ref", (table_ref,))
                row = cursor.fetchone()
                if not row or row.get("table_ref") is None:
                    missing.append(table_ref)
    return missing


def _split_table_ref(table_ref: str) -> tuple[str, str]:
    parts = table_ref.split(".", 1)
    if len(parts) != 2:
        raise ValueError(f"expected schema-qualified table ref: {table_ref!r}")
    schema, table = parts
    if schema not in POST_MODEL_SCHEMAS:
        raise ValueError(f"unsupported post-model schema: {schema!r}")
    _validate_identifier(schema)
    _validate_identifier(table)
    return schema, table


def _validate_identifier(identifier: str) -> None:
    if not IDENTIFIER_RE.fullmatch(identifier):
        raise ValueError(f"unsafe SQL identifier: {identifier!r}")


def _create_table_sql(schema: str, table: str) -> str:
    _validate_identifier(schema)
    _validate_identifier(table)
    return f'''
CREATE TABLE IF NOT EXISTS "{schema}"."{table}" (
  id TEXT PRIMARY KEY,
  contract_type TEXT,
  artifact_ref TEXT,
  target_ref TEXT,
  generated_at_utc TIMESTAMPTZ,
  payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
'''


__all__ = [
    "ensure_post_model_tables",
    "registered_post_model_tables",
    "verify_post_model_tables",
]

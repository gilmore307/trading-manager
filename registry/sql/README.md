# Registry SQL

This directory owns the SQL-backed concrete registry entries for `trading-main`.

Markdown files in `registry/` define kind boundaries. SQL migrations define the actual active entries and schema.

## Layout

```text
registry/sql/
  README.md
  apply-migrations.py
  schema_migrations/
    001_create_trading_registry.sql
    002_bootstrap_trading_registry.sql
    ...
```

## Rules

- Treat migrations as append-only after commit.
- Do not list concrete row inventories in kind Markdown files.
- Do not store secrets in SQL payloads. Use secret aliases for `config` entries.
- If a new `kind` is introduced, update both the SQL kind check and the corresponding Markdown kind boundary file.

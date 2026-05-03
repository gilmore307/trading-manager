# Registry SQL

This directory owns the SQL-backed concrete registry entries for `trading-manager`.

Markdown files in `../kinds/` define kind boundaries. SQL migrations define the actual active entries and schema.

## Layout

```text
scripts/registry/sql/
  README.md
  schema_migrations/
    001_create_trading_registry.sql
    002_bootstrap_trading_registry.sql
    ...
```

## Rules

- Treat migrations as append-only after commit.
- Do not list concrete row inventories in kind Markdown files.
- Do not store secrets in SQL payloads. Use secret aliases for `config` entries.
- If a new `kind` is introduced, update both the SQL kind check and the corresponding `scripts/registry/kinds/<kind>.md` boundary file. The SQL kind check must stay aligned with `scripts/registry/kinds/*.md`; tests enforce this.

## CSV Snapshot

`scripts/registry/apply_registry_migrations.py` exports the active `trading_registry` table to `../current.csv` after every non-dry-run migration pass.

Use `--export-only` to refresh the CSV without applying migrations.

Use `--no-export` only for exceptional debugging; normal registry updates should leave GitHub with a current CSV snapshot.

## Path Column

`trading_registry.path` is nullable. Use it for direct locators or addresses when a registry item points to a concrete entity, such as a repository root or helper source file.

Do not create a separate `path` kind. Registry id remains the stable automation reference; key lookups are for human/debug convenience only.

## Payload Format Constraint

`trading_registry.payload_format` is constrained to registered value-format markers. When adding a new payload format, update the SQL check constraint, add the matching `kind=payload_format` registry row, update docs/tests, and regenerate `scripts/registry/current.csv` together.

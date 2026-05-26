# Registry SQL

This directory owns the current SQL table shape for `trading-manager` registry.

Markdown files in `../kinds/` define kind boundaries. `../current.csv` defines the actual active entries.

## Layout

```text
scripts/registry/sql/
  README.md
  trading_registry.sql
```

## Rules

- Keep this file as the current table definition, not a migration ledger.
- Do not list concrete row inventories in kind Markdown files.
- Do not store secrets in SQL or CSV payloads. Use secret aliases for `config` entries.
- If a new `kind` is introduced, update both the SQL kind check and the corresponding `scripts/registry/kinds/<kind>.md` boundary file. The SQL kind check must stay aligned with `scripts/registry/kinds/*.md`; tests enforce this.

## CSV Snapshot

`scripts/registry/sync_registry.py` syncs `../current.csv` into the active `trading_registry` table.

Use `--export-only` to refresh the CSV from the live DB after an operator-side inspection or repair.

Use `--no-export` only for exceptional debugging; normal registry updates should leave GitHub with current CSV rows.

## Path Column

`trading_registry.path` is nullable. Use it for direct locators or addresses when a registry item points to a concrete entity, such as a repository root or helper source file.

Do not create a separate `path` kind. Registry id remains the stable automation reference; key lookups are for human/debug convenience only.

## Payload Format Constraint

`trading_registry.payload_format` is constrained to registered value-format markers. When adding a new payload format, update the SQL check constraint, add the matching `kind=payload_format` registry row, update docs/tests, and regenerate `scripts/registry/current.csv` together.

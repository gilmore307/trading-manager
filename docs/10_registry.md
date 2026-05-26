# Registry

The registry is the reviewed shared vocabulary and locator table for the trading system.

## Source of Truth

```text
scripts/registry/sql/trading_registry.sql Current table definition.
scripts/registry/current.csv              Reviewed current row inventory and DB sync source.
scripts/registry/kinds/*.md              Kind boundaries and rejection rules.
scripts/registry/rules/*.md              Cross-kind naming/routing rules.
```

## Entry Model

A registry row has a stable `id`, a `kind`, a human-readable `key`, a typed `payload`, an optional `path`, an `applies_to` scope, an artifact-sync policy, and a note.

- Use `id` for automation.
- Use `key` for display and search.
- Use `path` for direct locators when the row names an entity-like thing.
- Use the narrowest valid `kind`.
- Do not register ordinary implementation files as scripts.

## Workflow

Clean local/CI verification without DB credentials:

```bash
python3 scripts/registry/check_registry_current_matches_db.py --allow-missing-db
```

Operator/server verification with DB access:

```bash
python3 scripts/registry/sync_registry.py --dry-run
python3 scripts/registry/check_registry_current_matches_db.py
```

Registry mutation/export on the operator server:

```bash
python3 scripts/registry/sync_registry.py
python3 scripts/registry/sync_registry.py --export-only
```

A registry-changing commit normally includes:

1. Updated `scripts/registry/current.csv`.
2. Updated `scripts/registry/sql/trading_registry.sql` if the table shape changes.
3. Any affected kind/rule docs.
4. Tests or dry-run evidence.

## Rejection Rules

- No secret values.
- No generated payload blobs.
- No temporary experiment labels as stable ids.
- No duplicate semantic rows under different names.
- No broad kind when a narrower field/status/path/request/artifact kind fits.

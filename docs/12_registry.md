# Registry

The registry is the reviewed shared vocabulary and locator table for the trading system.

## Source of Truth

```text
scripts/registry/sql/schema_migrations/  Append-only schema/data changes.
scripts/registry/current.csv             Generated active snapshot; do not edit by hand.
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

```bash
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 scripts/registry/apply_registry_migrations.py
python3 scripts/registry/apply_registry_migrations.py --export-only
```

A registry-changing commit normally includes:

1. SQL migration.
2. Regenerated `scripts/registry/current.csv`.
3. Any affected kind/rule docs.
4. Tests or dry-run evidence.

## Rejection Rules

- No secret values.
- No generated payload blobs.
- No temporary experiment labels as stable ids.
- No duplicate semantic rows under different names.
- No broad kind when a narrower field/status/path/request/artifact kind fits.

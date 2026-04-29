# Scripts

`scripts/` stores executable maintenance and operational entrypoints for `trading-main`, plus the SQL-backed registry maintenance files those entrypoints own.

For the docs-level registry guide, see [`docs/08_registry.md`](../docs/08_registry.md).

## Boundary

- Scripts may import reusable implementation from `src/`.
- `src/` must not import `scripts/`.
- Scripts are callable entrypoints, not ordinary package source files.
- Stable cross-repository or automation-facing commands should be registered as `kind=script` rows in the registry.
- Registry maintenance files live directly under `scripts/`; do not reintroduce a nested `scripts/` boundary.

## Inventory

- `apply_registry_migrations.py` — applies pending SQL registry migrations exactly once and exports `scripts/current.csv` unless `--no-export` is used.
- `current.csv` — generated GitHub-visible snapshot of the active `trading_registry` table; do not hand-edit it.
- `kinds/` — one Markdown boundary file per registry kind. These files define scope/range/rejection boundaries only, not concrete active row lists.
- `reviews/` — registry review notes and boundary assessments.
- `sql/schema_migrations/` — append-only SQL migrations for registry schema and active row changes.

## Run

```bash
python3 scripts/apply_registry_migrations.py
python3 scripts/apply_registry_migrations.py --dry-run
python3 scripts/apply_registry_migrations.py --export-only
```

The SQL `trading_registry.kind` constraint and `scripts/kinds/*.md` files must stay aligned. Tests compare those sources directly.

Registry `id` is the stable automation reference. Registry `key` is a human-readable output/display label and may be renamed by reviewed migration. Helper APIs must not take key as input.

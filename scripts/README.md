# Scripts

`scripts/` stores executable maintenance and operational entrypoints for `trading-manager`.

Registry maintenance is intentionally grouped under `scripts/registry/` so future non-registry maintenance commands can be added under `scripts/` without mixing boundaries.

For the docs-level registry guide, see [`docs/91_registry.md`](../docs/91_registry.md).

## Boundary

- Scripts may import reusable implementation from `src/`.
- `src/` must not import `scripts/`.
- Scripts are callable entrypoints, not ordinary package source files.
- Stable cross-repository or automation-facing commands should be registered as `kind=script` rows in the registry.
- Registry SQL, generated CSV snapshots, kind boundaries, and registry rules live under `scripts/registry/`.

## Inventory

- `registry/apply_registry_migrations.py` — applies pending SQL registry migrations exactly once and exports `scripts/registry/current.csv` unless `--no-export` is used.
- `registry/current.csv` — generated GitHub-visible snapshot of the active `trading_registry` table; do not hand-edit it.
- `registry/kinds/` — one Markdown boundary file per registry kind. These files define scope/range/rejection boundaries only, not concrete active row lists.
- `registry/rules/` — normative registry table, kind-routing, and naming rules that constrain SQL row shape.
- `registry/sql/schema_migrations/` — append-only SQL migrations for registry schema and active row changes.

## Run

```bash
python3 scripts/registry/apply_registry_migrations.py
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 scripts/registry/apply_registry_migrations.py --export-only
```

The SQL `trading_registry.kind` constraint and `scripts/registry/kinds/*.md` files must stay aligned. Tests compare those sources directly.

Registry `id` is the stable automation reference. Registry `key` is a human-readable output/display label and may be renamed by reviewed migration. Helper APIs must not take key as input.

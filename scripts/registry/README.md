# Registry Maintenance

This directory owns the SQL-backed trading registry maintenance surface.

## Inventory

- `apply_registry_migrations.py` — applies append-only SQL migrations and exports `current.csv`.
- `current.csv` — generated GitHub-visible snapshot of the active `trading_registry` table; do not hand-edit.
- `kinds/` — one Markdown boundary file per allowed registry `kind`.
- `rules/` — normative cross-kind, table-shape, and naming rules.
- `sql/schema_migrations/` — append-only SQL migrations for schema and active registry row changes.

## Run

```bash
python3 scripts/registry/apply_registry_migrations.py
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 scripts/registry/apply_registry_migrations.py --export-only
```

## Boundaries

- SQL migrations own concrete row changes.
- `current.csv` is generated from SQL and must not be edited by hand.
- Kind files define per-kind boundaries only, not concrete row inventories.
- Rule files define reusable constraints that affect SQL row shape or routing.

# Registry Maintenance

This directory owns the SQL-backed trading registry maintenance surface.

## Inventory

- `sync_registry.py` — applies the current table schema, syncs `current.csv` into the DB, and exports DB state when needed.
- `check_registry_current_matches_db.py` — compares `current.csv` with a live DB export when DB access is available.
- `current.csv` — reviewed current row inventory and DB sync source.
- `kinds/` — one Markdown boundary file per allowed registry `kind`.
- `rules/` — normative cross-kind, table-shape, and naming rules.
- `sql/trading_registry.sql` — current `trading_registry` table definition.

## Run

Clean local/CI verification without DB credentials:

```bash
python3 scripts/registry/check_registry_current_matches_db.py --allow-missing-db
```

Operator/server verification and mutation with DB access:

```bash
python3 scripts/registry/sync_registry.py --dry-run
python3 scripts/registry/check_registry_current_matches_db.py
python3 scripts/registry/sync_registry.py
python3 scripts/registry/sync_registry.py --export-only
```

## Boundaries

- `current.csv` owns concrete row changes.
- `sync_registry.py` owns DB synchronization and DB export.
- Kind files define per-kind boundaries only, not concrete row inventories.
- Rule files define reusable constraints that affect SQL row shape or routing.

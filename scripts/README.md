# Scripts

`scripts/` stores executable maintenance and operational entrypoints for `trading-main`.

## Boundary

- Scripts may import reusable implementation from `src/`.
- `src/` must not import `scripts/`.
- Scripts are callable entrypoints, not ordinary package source files.
- Stable cross-repository or automation-facing commands should be registered as `kind=script` rows in the registry.

## Inventory

- `registry/apply_registry_migrations.py` — applies pending SQL registry migrations exactly once and exports `scripts/registry/current.csv` unless `--no-export` is used.

## Run

```bash
python3 scripts/registry/apply_registry_migrations.py
python3 scripts/registry/apply_registry_migrations.py --dry-run
python3 scripts/registry/apply_registry_migrations.py --export-only
```

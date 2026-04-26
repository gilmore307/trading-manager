# Registry Helpers

These helpers provide the starting point for trading registry access.

They should read from the SQL-backed `trading_registry` table and support CSV snapshot generation/inspection helpers where appropriate.

Do not treat registry helpers as a place for component runtime behavior.

## Package Status

These JavaScript helpers are not currently a formal package interface for component repositories.

There is no `package.json`, package version, Node engine requirement, install command, or cross-repository import contract. Treat this directory as internal `trading-main` maintenance/test code until a helper distribution decision is accepted.

Run tests directly from `trading-main` when changing this helper code:

```bash
node --test helpers/registry/registry-reader.test.js
```

## Public Helper Surface

The registered public helper surface is id-only:

- `getKeyById(id)` returns a registry item key or `null`.
- `getPayloadById(id)` returns a registry item payload or `null`.
- `getPathById(id)` returns a registry item path or `null`.
- `loadSecretTextByConfigId(id)` resolves a config item payload as a secret alias and returns trimmed secret text.

Registry keys are output/display values, not helper inputs. If a human needs key-based debugging, query SQL directly instead of adding key-input helper APIs.

## CSV Snapshot Helper

`registry/sql/apply-migrations.py --export-only` regenerates `registry/current.csv` from the active SQL table.

This is a registry maintenance helper, not a lookup helper. It is registered separately as `REGISTRY_EXPORT_CURRENT_CSV_HELPER`.

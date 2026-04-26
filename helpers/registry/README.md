# Registry Helpers

These JavaScript helpers are internal `trading-main` maintenance/test code for trading registry access.

The formal cross-repository runtime helper surface is the Python package under `helpers/python/trading_registry/`.

Do not treat this JavaScript directory as a component runtime dependency.

## Package Status

These JavaScript helpers are not the formal package interface for component repositories. There is no `package.json`, package version, Node engine requirement, install command, or cross-repository import contract.

Run tests directly from `trading-main` when changing this internal helper code:

```bash
node --test helpers/registry/registry-reader.test.js
```

## Public Helper Surface

The official registered Python helper surface is id-only:

- `RegistryReader.get_key_by_id(id)` returns a registry item key or `None`.
- `RegistryReader.get_payload_by_id(id)` returns a registry item payload or `None`.
- `RegistryReader.get_path_by_id(id)` returns a registry item path or `None`.
- `SecretResolver.load_secret_text_by_config_id(id)` resolves a config item payload as a secret alias and returns trimmed secret text.

This JavaScript directory retains analogous internal helper behavior for maintenance/tests only.

Registry keys are output/display values, not helper inputs. If a human needs key-based debugging, query SQL directly instead of adding key-input helper APIs.

## CSV Snapshot Helper

`registry/sql/apply-migrations.py --export-only` regenerates `registry/current.csv` from the active SQL table.

This is a registry maintenance helper, not a lookup helper. It is registered separately as `REGISTRY_EXPORT_CURRENT_CSV_HELPER`.

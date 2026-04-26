# Registry Helpers

These helpers provide the starting point for trading registry access.

They should read from the SQL-backed `trading_registry` table and support CSV snapshot generation/inspection helpers where appropriate.

Do not treat registry helpers as a place for component runtime behavior.

## Public Helper Surface

The registered public helper surface is id-only:

- `getKeyById(id)` returns a registry item key or `null`.
- `getPayloadById(id)` returns a registry item payload or `null`.
- `getPathById(id)` returns a registry item path or `null`.
- `loadSecretTextByConfigId(id)` resolves a config item payload as a secret alias and returns trimmed secret text.

Registry keys are output/display values, not helper inputs. If a human needs key-based debugging, query SQL directly instead of adding key-input helper APIs.

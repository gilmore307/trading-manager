# Registry Helpers

These helpers provide the starting point for trading registry access.

They should read from the SQL-backed `trading_registry` table and support CSV snapshot generation/inspection helpers where appropriate.

Do not treat registry helpers as a place for component runtime behavior.

## Stable Lookup Rule

Use registry `id` for automation. Registry `key` is a human-readable label and may be renamed by reviewed migration.

Path helpers follow that rule:

- `getItemPathById(id)` returns a path or `null`.
- `requireItemPathById(id)` returns a path or throws.
- `getItemPathByKeyUnsafe(key)` is for human/debug convenience and returns a path or `null`.
- `requireItemPathByKeyUnsafe(key)` is for human/debug convenience and returns a path or throws.

The `Unsafe` suffix means the lookup uses a renameable key rather than a stable id.

## Secret Resolver Helpers

Use config-id helpers for automation. Key-based config helpers carry the `Unsafe` suffix because registry keys are renameable.

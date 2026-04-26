# Script

## Kind Boundary

Canonical helper or automation entrypoint records. The row payload should describe the usable helper/export; the optional `path` column should hold the concrete source-file locator.

## Range

Register helper or automation entrypoints only. Use payload for the usable helper/export description and `path` column for the concrete source-file locator. Do not register generated files or broad directories.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- directories;
- generated files;
- runtime artifact paths;
- generic terms;

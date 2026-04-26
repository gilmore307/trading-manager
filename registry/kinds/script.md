# Script

## Kind Boundary

Canonical callable helper or automation export records. The row payload should describe the usable helper/export; the optional `path` column should hold the concrete source-file locator.

## Range

Register stable callable helper or automation exports only. Use payload for the usable helper/export description and `path` column for the concrete source-file locator. Do not register package constants, generated files, or broad directories.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- directories;
- generated files;
- runtime artifact paths;
- generic terms;

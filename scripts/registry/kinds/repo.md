# Repo

## Kind Boundary

Canonical repository identifiers. The row payload owns the repository name; the optional `path` column may hold the repository root path.

## Range

Register repository entries only. Use payload for the repository name, `path` column for the repository root path, and `term` for conceptual definitions.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- standalone repository root path rows;
- concept definitions;
- package/module names that are not repositories;

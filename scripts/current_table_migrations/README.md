# Current Table Migrations

This directory holds one-off SQL migrations for live/current PostgreSQL tables outside the registry migration ledger.

## Use Only When

- A current live table needs physical-name or stored-value alignment.
- The change is not a registry row/schema migration.
- The operation has an external backup and an explicit application plan.

## Rules

- Do not rewrite historical registry migrations or historical artifact paths here.
- Keep scripts idempotent enough for verification reruns.
- Record evidence before and after application.
- Do not perform destructive data mutation without explicit operator approval.

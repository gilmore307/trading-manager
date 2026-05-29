# Current Table Migrations

This directory holds one-off SQL migrations for live/current PostgreSQL tables outside the registry migration ledger.

There is currently no pending live/current table migration script.

## Applied Cleanup Scripts

- `drop_stale_model_numbering_tables_20260529.sql` — removes empty pre-renumbering model/feature relations after the 10-layer physical contract became canonical. The script refuses to drop any table or materialized view that still contains rows.

## Use Only When

- A current live table needs physical-name or stored-value alignment.
- The change is not a registry row/schema migration.
- The operation has an external backup and an explicit application plan.

## Rules

- Do not rewrite historical registry migrations or historical artifact paths here.
- Keep scripts idempotent enough for verification reruns.
- Record evidence before and after application.
- Do not perform destructive data mutation without explicit operator approval.

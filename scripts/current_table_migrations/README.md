# Current Table Migrations

This directory contains one-off SQL migrations for live/current PostgreSQL tables whose physical names or stored values must be aligned outside the registry migration ledger.

- Historical registry migrations and historical artifact paths are not rewritten here.
- Take and record an external backup before applying any script.
- Keep scripts idempotent enough to tolerate a second verification run after the intended application.

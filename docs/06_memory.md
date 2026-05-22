# Memory

This file records how durable project memory should be handled for `trading-manager`.

## Durable Homes

- Current operating rules: docs in this repository.
- Shared project-development rules: `/root/.openclaw/workspace/skills/openclaw/project_development/SKILL.md`.
- Active tasks: `docs/04_task.md`.
- Active decisions: `docs/05_decision.md`.
- Durable project notes: `docs/06_memory.md`.
- Registry vocabulary: SQL migrations and generated `scripts/registry/current.csv`.
- Runtime state: `trading-storage/storage/02_control_plane/runtime/` files.
- Audit history: Git history and append-only SQL migrations.

## Rule

Active docs state current operational rules. Audit-only details stay in Git history or append-only SQL migrations.

## Not Stored Here

- Secrets or credentials.
- Generated provider data.
- Model artifacts and large payloads.
- Broker/account state.
- Dashboard build outputs.

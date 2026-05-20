# Memory

This file records how durable project memory should be handled for `trading-manager`.

## Durable Homes

- Current operating rules: docs in this repository.
- Shared project-development rules: `/root/.openclaw/workspace/skills/openclaw/project_development/SKILL.md`.
- Active tasks: `docs/04_task.md`.
- Active decisions: `docs/05_decision.md`.
- Durable project notes: `docs/06_memory.md`.
- Registry vocabulary: SQL migrations and generated `scripts/registry/current.csv`.
- Runtime state: `trading-storage/storage/manager/runtime/` files.
- Historical path: Git history and append-only SQL migrations.

## Rule

Do not keep route-change narrative in active docs once the current contract is clear. If a fact matters operationally, write the current rule. If only history matters, rely on Git or migration history.

## Not Stored Here

- Secrets or credentials.
- Generated provider data.
- Model artifacts and large payloads.
- Broker/account state.
- Dashboard build outputs.

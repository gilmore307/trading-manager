# Memory

This file records how durable project memory should be handled for `trading-manager`.

## Durable Homes

- Current operating rules: docs in this repository.
- Current reading-path docs: `docs/00_*` through `docs/69_*`.
- Reserved reference docs: `docs/70_*` through `docs/79_*`.
- Active tasks: `docs/80_task.md`.
- Active decisions: `docs/81_decision.md`.
- Durable project notes: `docs/82_memory.md`.
- Appendix/compatibility docs, only when needed: `docs/90_*` through `docs/99_*`.
- Registry vocabulary: SQL migrations and generated `scripts/registry/current.csv`.
- Runtime state: ignored `storage/runtime/` files.
- Historical path: Git history and append-only SQL migrations.

## Rule

Do not keep route-change narrative in active docs once the current contract is clear. If a fact matters operationally, write the current rule. If only history matters, rely on Git or migration history.

## Not Stored Here

- Secrets or credentials.
- Generated provider data.
- Model artifacts and large payloads.
- Broker/account state.
- Dashboard build outputs.

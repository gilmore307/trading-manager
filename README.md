# trading-manager

`trading-manager` is the system-level platform repository for the trading project.

It owns global architecture, cross-repository workflow, control-plane orchestration contracts, shared contracts, field/status registries, shared helper code, system-level decisions, and global planning context.

It does not own component runtime implementations, market data, generated artifacts, secrets, or component-local task state. Control-plane request generation, readiness review, lifecycle routing, and promotion policy belong here; data, model, execution, storage, and dashboard implementation remain in their component repositories.

This repository also anchors the shared local trading development environment at `.venv/`. The `.venv/` directory is local runtime infrastructure and must remain ignored by Git.

## Top-Level Structure

```text
docs/             System-level docs spine: 00-06 project-wide docs plus 07-09 platform guides.
src/              Importable shared helper packages used across trading repositories.
scripts/          Executable maintenance/operational commands.
  registry/       Registry maintenance surface: migration/export entrypoint, generated CSV, kind boundaries, rules, and SQL migrations.
tests/            First-party tests for source packages and repository governance checks.
pyproject.toml   Python helper package metadata for `trading-manager-helpers`.
requirements.txt  Shared Python environment dependency ledger.
```

## Docs Spine

```text
docs/
  00_scope.md
  01_context.md
  02_workflow.md
  03_acceptance.md
  04_task.md
  05_decision.md
  06_memory.md
  07_helpers.md
  08_registry.md
  09_templates.md
  91_layer_01_market_regime.md
  92_layer_02_sector_context.md
```

Component repositories keep their own docs spine. In `trading-manager`, `00_scope.md` through `06_memory.md` remain the project-wide platform docs, while `07_helpers.md`, `08_registry.md`, and `09_templates.md` explain the three platform functions this repository owns. Layer-specific `91_`/`92_` docs record current cross-repository naming and control-plane boundaries while the lower-number docs spine is being evaluated.

## Registry Rule

Concrete registry entries live in the SQL-backed `trading_registry` table. The nullable `path` column stores direct locators/addresses for entity-like entries.

- Kind Markdown files define kind boundaries and rejection rules only.
- SQL migrations under `scripts/registry/sql/schema_migrations/` define concrete entries.
- `scripts/registry/current.csv` is generated from SQL for GitHub visibility and must not be edited by hand.

Registry ids are stable automation references. Registry keys are human-readable labels and may be renamed by reviewed migrations. Use id-based helpers in code.

See `docs/07_helpers.md`, `docs/08_registry.md`, and `docs/09_templates.md` for platform-function guides.

## Shared Environment Rule

The shared trading Python environment is anchored at `/root/projects/trading-manager/.venv` and currently uses Python 3.12 with `pip`. Dependencies must be added to `requirements.txt` through reviewed commits before installation into the shared environment.

The formal runtime helper package is Python (`trading-manager-helpers`, import package `trading_registry`). Component repositories should use this Python package for shared helper access.

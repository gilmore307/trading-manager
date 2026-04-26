# trading-main

`trading-main` is the system-level platform repository for the trading project.

It owns global architecture, cross-repository workflow, shared contracts, field/status registries, project templates, shared helper code, system-level decisions, and global planning context.

It does not own component runtime implementations, market data, generated artifacts, secrets, or component-local task state.

This repository also anchors the shared local trading development environment at `.venv/`. The `.venv/` directory is local runtime infrastructure and must remain ignored by Git.

## Top-Level Structure

```text
docs/             System-level docs spine: 00-06 project-wide docs plus 07-09 platform guides.
helpers/          Shared helper code used across trading repositories.
registry/         Trading-wide registry kind boundaries, SQL migrations, and generated current.csv snapshot.
templates/        Trading-wide project, contract, task, and implementation templates, including contract drafting templates.
pyproject.toml    Python helper package metadata for `trading-main-helpers`.
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
```

Component repositories keep their own docs spine. In `trading-main`, `00_scope.md` through `06_memory.md` remain the project-wide platform docs, while `07_helpers.md`, `08_registry.md`, and `09_templates.md` explain the three platform functions this repository owns.

## Registry Rule

Concrete registry entries live in the SQL-backed `trading_registry` table. The nullable `path` column stores direct locators/addresses for entity-like entries.

- Kind Markdown files define kind boundaries and rejection rules only.
- SQL migrations under `registry/sql/schema_migrations/` define concrete entries.
- `registry/current.csv` is generated from SQL for GitHub visibility and must not be edited by hand.

Registry ids are stable automation references. Registry keys are human-readable labels and may be renamed by reviewed migrations. Use id-based helpers in code.

See `docs/07_helpers.md`, `docs/08_registry.md`, and `docs/09_templates.md` for platform-function guides.

## Shared Environment Rule

The shared trading Python environment is anchored at `/root/projects/trading-main/.venv` and currently uses Python 3.12 with `pip`. Dependencies must be added to `requirements.txt` through reviewed commits before installation into the shared environment.

The formal runtime helper package is Python (`trading-main-helpers`, import package `trading_registry`). Current JavaScript registry helpers are internal maintenance/test helpers only; component repositories must not import those JavaScript files at runtime.

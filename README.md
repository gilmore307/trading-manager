# trading-manager

`trading-manager` is the system-level platform repository for the trading project.

It owns global architecture, cross-repository workflow, control-plane orchestration contracts, shared contracts, field/status registries, shared helper code, system-level decisions, and global planning context.

It does not own component runtime implementations, market data, generated artifacts, secrets, or component-local task state. Control-plane request generation, readiness review, lifecycle routing, and promotion policy belong here; data, model, execution, storage, and dashboard implementation remain in their component repositories.

This repository also anchors the shared local trading development environment at `.venv/`. The `.venv/` directory is local runtime infrastructure and must remain ignored by Git.

## Top-Level Structure

```text
docs/             System-level docs spine: 00/01 platform boundary, 02+ layer workflow/acceptance docs, 80+ governance docs, 90+ platform guides.
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
  02_layer_01_market_regime.md
  03_layer_02_sector_context.md
  04_model_stack_control_plane.md
  80_task.md
  81_decision.md
  82_memory.md
  90_helpers.md
  91_registry.md
  92_templates.md
  93_contracts.md
  94_monthly_backfill.md
  95_task_system.md
  96_model_promotion.md
  97_manager_control_plane_closeout.md
```

Component repositories keep their own docs spine. In `trading-manager`, `00_scope.md` and `01_context.md` own the platform boundary, `02_`/`03_` layer docs own retained Layer 1/2 cross-repository naming/control-plane workflows plus acceptance gates, `04_model_stack_control_plane.md` owns the concise manager-side Layer 1-8 control-plane overview, `80_`/`81_`/`82_` own task/decision/memory, and `90_helpers.md`, `91_registry.md`, `92_templates.md`, `93_contracts.md`, `94_monthly_backfill.md`, `95_task_system.md`, and `96_model_promotion.md` explain the platform functions this repository owns.

## Registry Rule

Concrete registry entries live in the SQL-backed `trading_registry` table. The nullable `path` column stores direct locators/addresses for entity-like entries.

- Kind Markdown files define kind boundaries and rejection rules only.
- SQL migrations under `scripts/registry/sql/schema_migrations/` define concrete entries.
- `scripts/registry/current.csv` is generated from SQL for GitHub visibility and must not be edited by hand.

Registry ids are stable automation references. Registry keys are human-readable labels and may be renamed by reviewed migrations. Use id-based helpers in code.

See `docs/04_model_stack_control_plane.md`, `docs/90_helpers.md`, `docs/91_registry.md`, `docs/92_templates.md`, `docs/93_contracts.md`, `docs/94_monthly_backfill.md`, `docs/95_task_system.md`, `docs/96_model_promotion.md`, and `docs/97_manager_control_plane_closeout.md` for platform-function guides and closeout status. Use `PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py --end-month 2016-01 --limit 3 --scenario mixed --format jsonl` for a safe request/receipt/summary rehearsal before live component dispatch; add `--write` only for rehearsal-prefixed SQL rows.

## Shared Environment Rule

The shared trading Python environment is anchored at `/root/projects/trading-manager/.venv` and currently uses Python 3.12 with `pip`. Dependencies must be added to `requirements.txt` through reviewed commits before installation into the shared environment.

The formal runtime helper package is Python (`trading-manager-helpers`, import package `trading_registry`). Component repositories should use this Python package for shared helper access.

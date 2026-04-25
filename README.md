# trading-main

`trading-main` is the system-level platform repository for the trading project.

It owns global architecture, cross-repository workflow, shared contracts, field/status registries, project templates, shared helper code, system-level decisions, and global planning context.

It does not own component runtime implementations, market data, generated artifacts, secrets, or component-local task state.

This repository also anchors the shared local trading development environment at `.venv/`. The `.venv/` directory is local runtime infrastructure and must remain ignored by Git.

## Top-Level Structure

```text
docs/        System-level docs spine and numbered contracts.
registry/    Trading-wide registered fields, identifiers, statuses, artifact types, and request types.
templates/   Trading-wide project, contract, task, and implementation templates.
helpers/     Shared helper code used across trading repositories.
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
  07_artifact.md
  08_manifest.md
  09_ready_signal.md
  10_request.md
```

Component repositories keep their own docs spine. `trading-main` records system-level facts, contracts, registries, templates, and shared helper boundaries.

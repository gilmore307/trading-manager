# trading-main

`trading-main` is the system-level documentation and contract repository for the trading project.

It owns global architecture, cross-repository workflow, shared contracts, system-level decisions, and global planning context. It does not own runtime trading code, market data, generated artifacts, secrets, or component-local implementation details.

This repository also anchors the shared local trading development environment at `.venv/`. The `.venv/` directory is local runtime infrastructure and must remain ignored by Git.

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

Component repositories keep their own docs spine. `trading-main` records only system-level facts and contracts.

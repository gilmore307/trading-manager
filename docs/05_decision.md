# Decision

## D001 - Use a multi-repository trading architecture

Date: 2026-04-25

### Decision

The trading system will be split across multiple repositories rather than implemented as one monorepo.

### Rationale

The system has distinct control-plane, data, storage, strategy, model, execution, and dashboard responsibilities. Separate repositories help preserve ownership boundaries and acceptance clarity.

## D002 - Create `trading-main` as the system-level documentation and contract repository

Date: 2026-04-25

### Decision

`trading-main` will own global documentation, cross-repository workflow, shared contracts, and system-level decisions.

### Rationale

A global docs/contracts repository prevents component repositories from inventing incompatible interfaces and drifting in responsibility.

## D003 - Keep component-local details in component repositories

Date: 2026-04-25

### Decision

`trading-main` records system-level collaboration only. Component-local scope, workflow, acceptance, task state, and implementation detail belong in each component repository's docs spine.

### Rationale

Global docs should coordinate repositories without replacing their local project boundaries.

## D004 - Use `trading-data` rather than `trading-fetcher`

Date: 2026-04-25

### Decision

The data upstream repository will be named `trading-data`.

### Rationale

The repository is responsible for data source access, fetching, normalization, storage writes, and ready signals. `trading-fetcher` is too narrow.

## D005 - Market-state discovery must be market-only

Date: 2026-04-25

### Decision

Market-state discovery must not use strategy returns or strategy performance as input. Strategy results may only be attached after market states already exist.

### Rationale

Using strategy performance to define market states would contaminate downstream claims that states can guide strategy selection.

## D006 - `trading-main` anchors the shared trading development environment

Date: 2026-04-25

### Decision

`trading-main` will anchor the shared local development environment at:

```text
/root/projects/trading-main/.venv
```

The `.venv/` directory is local runtime infrastructure and must be ignored by Git.

### Rationale

This gives all trading repositories a single predictable environment location while keeping implementation code, generated artifacts, and component-specific logic out of `trading-main`.

### Consequences

- Component repositories should use `/root/projects/trading-main/.venv`.
- Component repositories should not create independent virtual environments unless an exception is documented.
- `trading-main` remains documentation/contract-only except for the local gitignored `.venv/` anchor.
- The `.venv/` directory is not reviewable repository content.

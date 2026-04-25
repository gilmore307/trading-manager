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

## D007 - Expand `trading-main` into the trading platform main repository

Date: 2026-04-25

### Context

The server's project work is centered on the trading system. The owner wants one canonical home for global planning, field registration, templates, and shared helpers instead of splitting small shared pieces across additional repositories.

### Decision

`trading-main` will own:

- trading-wide planning and architecture;
- trading-wide registered fields, identifiers, statuses, artifact types, request types, and related names;
- trading-wide templates;
- shared helper code used by component repositories;
- the shared local `.venv/` anchor.

### Rationale

Keeping these shared assets together reduces repository sprawl and gives the trading system one obvious coordination point.

### Consequences

- `trading-main` is no longer docs-only.
- Component runtime implementations still remain outside `trading-main`.
- Shared helpers in `trading-main` must stay generic and reusable.
- Trading-specific registry responsibilities move from `universal-catalog` into `trading-main/registry/`.

## D008 - Registry Markdown defines kind boundaries while SQL owns concrete entries

Date: 2026-04-25

### Context

The initial registry migration converted active SQL rows into Markdown tables. That made the kind files too noisy and blurred their purpose.

### Decision

`registry/<kind>.md` files define kind boundaries, ranges, and rejection rules only. Concrete registered items live in the SQL-backed `trading_registry` table and append-only migrations under `registry/sql/schema_migrations/`.

### Rationale

Kind documentation should explain what belongs in a registry kind. Concrete entries need database semantics, uniqueness, migration history, and helper access rather than large Markdown inventories.

### Consequences

- Do not list active registry rows in Markdown kind files.
- Add one Markdown file per formal kind.
- Add or update SQL migrations for concrete item changes.
- If a new kind is introduced, update both the SQL kind constraint and the Markdown boundary file.

## D009 - Export the active SQL registry as a CSV snapshot

Date: 2026-04-25

### Context

Concrete registry entries belong in SQL for queryability, constraints, and helper access. The owner still wants GitHub to show the current registry contents without requiring a database query.

### Decision

After SQL registry updates, `registry/sql/apply-migrations.py` exports the active `trading_registry` table to:

```text
registry/current.csv
```

The CSV is a generated snapshot and must not be edited by hand.

### Rationale

This keeps SQL as the source of truth while preserving a simple GitHub-readable view of the active registry.

### Consequences

- Registry data changes require SQL migration review.
- Registry CSV changes are expected after SQL registry changes.
- Markdown kind files remain boundary documentation only.

## D010 - Keep current registry kinds with documented tie-breakers

Date: 2026-04-25

### Context

Some registry kinds are easy to confuse, especially `field` vs status-value kinds, `repo` vs `path`, `path` vs `script`, and `config` vs `term`.

### Decision

Keep the current kind set and document tie-breaker rules in `registry/reviews/kind-boundary.md`.

### Rationale

The apparent overlap is mostly semantic. Keeping specific kinds improves query convenience and validation clarity.

### Consequences

- Use `field` for slot names and specific status kinds for allowed values.
- Use `repo` for repository names and `path` for filesystem locations.
- Use `script` for source-file entrypoint locators.
- Use `config` for machine-consumed settings and `term` for human-facing definitions.

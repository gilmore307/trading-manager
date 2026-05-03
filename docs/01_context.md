# Context

## Why This Project Exists

The trading project is a core multi-repository system for building, evaluating, selecting, executing, and observing trading workflows.

The system needs a stable global coordination layer because its responsibilities are intentionally split across multiple repositories. Without a shared architecture and contract repository, each component could invent incompatible artifact layouts, request formats, manifest schemas, ready-signal conventions, and responsibility boundaries.

`trading-manager` exists to keep those global relationships explicit and reviewable, to own control-plane request/lifecycle policy, and to provide the trading-wide registry, templates, and shared helpers that all component repositories can use.

## Related Systems

### Component Repositories

| Repository | System-Level Role | Summary |
|---|---|---|
| `trading-manager` | Global platform and control plane | Owns system architecture, global workflow, shared contracts, registries, templates, shared helpers, system-level decisions, cross-repository planning, request generation, readiness checks, retries/recovery policy, manual override rules, lifecycle routing, and promotion coordination. It does not store data, generated artifacts, secrets, or component runtime implementations. |
| `trading-data` | Feed/source/feature data production | Owns provider feed adapters, approved web/file ingestion, model-scoped source construction, deterministic point-in-time feature tables, and data-production evidence. |
| `trading-storage` | Shared persistence contract | Defines persistent storage layout, artifact placement, partitioning, retention, archive, rehydrate, backup, and restore expectations. |
| `trading-model` | Offline modeling and market-state research | Consumes the `trading-data` feature/data foundation for training, research, evaluation, mappings, confidence, and verdicts. |
| `trading-execution` | Live/paper execution runtime | Runs trading daemons, creates execution plans, places broker/exchange orders, records positions/orders, reconciles state, and emits execution artifacts. |
| `trading-dashboard` | Downstream UI and visualization | Displays already-produced trading outputs through dashboard pages, server endpoints, and visualization adapters. |

The repository map is intentionally high-level. Detailed repository scope, local workflow, acceptance rules, implementation notes, and task state belong in each component repository's own docs spine.

### External Services and Interfaces

Current expected external interfaces include:

- market data APIs;
- macroeconomic and calendar data sources;
- broker or exchange APIs, including OKX or Alpaca;
- local or shared filesystem storage used by the trading repositories;
- `trading-manager/scripts/` and `docs/91_registry.md` for trading-wide registered names, status vocabularies, and registrable fields;
- OpenClaw/Codex execution surfaces for planning, implementation, review, and acceptance.

Specific providers, credentials, quotas, and environments are not defined in this file unless they become system-level assumptions.

## Shared Programming Environment

`trading-manager` is also the local anchor for the shared trading programming environment.

All trading repositories use one shared virtual environment located at:

```text
/root/projects/trading-manager/.venv
```

The `.venv/` directory is local runtime infrastructure. It must be ignored by Git and must not be treated as source, documentation, contract content, or reviewable project output.

Component repositories should not create independent virtual environments unless a documented exception is approved.

The accepted shared environment baseline is:

- Python runtime: Python 3.12.
- Environment anchor: `/root/projects/trading-manager/.venv`.
- Package installer: `python -m pip` inside the shared environment.
- Dependency ledger: `requirements.txt` at the `trading-manager` root.
- Installation command: `/root/projects/trading-manager/.venv/bin/python -m pip install -r /root/projects/trading-manager/requirements.txt`.
- Component repositories should not create independent virtual environments unless a documented exception is accepted.
- Dependencies are added only through reviewed commits; no ad hoc package installs become project state.

`trading-manager` may document and anchor the shared environment, but it must not become a runtime implementation repository.

## Trading Registry, Templates, and Helpers

Because this server's project work is centered on the trading system, `trading-manager` is the canonical home for trading-wide shared assets:

- `src/` stores shared helper code used by component repositories; `docs/90_helpers.md` explains the helper boundary.
- `scripts/` maintains the SQL-backed registration system; `docs/91_registry.md` explains the registry operating model.
- `trading-storage/main/templates/` stores reusable trading project, contract, task, and implementation templates; `docs/92_templates.md` explains the template boundary.

Shared helpers are allowed in `trading-manager`, but they must remain generic trading infrastructure. Component-specific runtime behavior still belongs in the owning component repository.

## Environment

Current assumed environment:

- server-hosted multi-repository development;
- repositories stored under `/root/projects/`;
- OpenClaw-managed planning, review, acceptance, and documentation stewardship;
- Codex-assisted implementation for bounded component-repository tasks;
- US Eastern time as the default project time basis unless a contract specifies UTC timestamps.

Runtime deployment environments, production hosts, storage volumes, broker credentials, API quotas, and scheduler details remain open until explicitly defined.

## Dependencies

System-level dependencies currently assumed:

- `trading-manager/scripts/` and `docs/91_registry.md` for registered names, shared status vocabularies, and registrable fields;
- `requirements.txt` in `trading-manager` for reviewed shared Python dependencies;
- OpenClaw project-development process for docs spine, task boundaries, acceptance, and review;
- component repositories for concrete implementation;
- shared storage accessible to the trading repositories;
- external market data, macro data, broker, and exchange services once provider choices are made.

This repository should not pin provider SDKs, runtime packages, or implementation dependencies for component repositories.

## OpenClaw / Codex Setup

OpenClaw owns:

- project shape;
- repository boundary discipline;
- docs spine creation and maintenance;
- contract drafting;
- task sizing;
- Codex dispatch;
- completion review;
- acceptance;
- final documentation alignment;
- commits and pushes unless explicitly told otherwise.

Codex owns:

- bounded implementation tasks inside component repositories after OpenClaw defines the acceptance path.

For `trading-manager`, Codex should normally not be needed unless there is a bulk documentation transformation or validation script explicitly delegated. This repository is primarily OpenClaw-authored.

## Important Constraints

- `trading-manager` owns docs, contracts, control-plane orchestration policy, registries, templates, shared helpers, and the gitignored shared environment anchor.
- Cross-repository behavior must be described through explicit contracts before implementation depends on it.
- Component repositories must not silently fork global contracts.
- Trading-wide status vocabularies and registrable fields belong in `trading-manager/scripts/`; registry operating details belong in `docs/91_registry.md`.
- Component-specific details belong in the component repository docs, not in `trading-manager`.
- Market-state discovery must not be contaminated by strategy performance.
- Execution-related code must treat broker and exchange operations as safety-sensitive external actions.
- Secrets and credentials must stay outside project repositories.
- Acceptance must be evidence-based; unsupported narrative completion is not enough.

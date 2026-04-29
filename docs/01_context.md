# Context

## Why This Project Exists

The trading project is a core multi-repository system for building, evaluating, selecting, executing, and observing trading workflows.

The system needs a stable global coordination layer because its responsibilities are intentionally split across multiple repositories. Without a shared architecture and contract repository, each component could invent incompatible artifact layouts, request formats, manifest schemas, ready-signal conventions, and responsibility boundaries.

`trading-main` exists to keep those global relationships explicit and reviewable, and to provide the trading-wide registry, templates, and shared helpers that all component repositories can use.

## Related Systems

### Component Repositories

| Repository | System-Level Role | Summary |
|---|---|---|
| `trading-main` | Global platform layer | Owns system architecture, global workflow, shared contracts, registries, templates, shared helpers, system-level decisions, and cross-repository planning. It does not store data, generated artifacts, secrets, or component runtime implementations. |
| `trading-manager` | Control plane | Coordinates workflow sequencing, schedules, queues, readiness checks, retries, recovery, manual override, lifecycle policy, request generation, and watchlist coordination. |
| `trading-source` | External/source-backed observations | Connects to providers and approved web/file sources, fetches observed market/options/issuer/filing/news/calendar data, normalizes rows, writes source-backed outputs, and emits ready signals. |
| `trading-storage` | Shared persistence contract | Defines persistent storage layout, artifact placement, partitioning, retention, archive, rehydrate, backup, and restore expectations. |
| `trading-derived` | Internally generated datasets | Consumes approved source observations and produces labels, samples, signals, candidates, oracle outcomes, backtest/evaluation outputs, manifests, and ready signals. |
| `trading-model` | Offline modeling and market-state research | Consumes the `trading-source` + `trading-derived` dataset foundation for training, research, evaluation, mappings, confidence, and verdicts. |
| `trading-execution` | Live/paper execution runtime | Runs trading daemons, creates execution plans, places broker/exchange orders, records positions/orders, reconciles state, and emits execution artifacts. |
| `trading-dashboard` | Downstream UI and visualization | Displays already-produced trading outputs through dashboard pages, server endpoints, and visualization adapters. |

The repository map is intentionally high-level. Detailed repository scope, local workflow, acceptance rules, implementation notes, and task state belong in each component repository's own docs spine.

### External Services and Interfaces

Current expected external interfaces include:

- market data APIs;
- macroeconomic and calendar data sources;
- broker or exchange APIs, including OKX or Alpaca;
- local or shared filesystem storage used by the trading repositories;
- `trading-main/scripts/` and `docs/08_registry.md` for trading-wide registered names, status vocabularies, and registrable fields;
- OpenClaw/Codex execution surfaces for planning, implementation, review, and acceptance.

Specific providers, credentials, quotas, and environments are not defined in this file unless they become system-level assumptions.

## Shared Programming Environment

`trading-main` is also the local anchor for the shared trading programming environment.

All trading repositories use one shared virtual environment located at:

```text
/root/projects/trading-main/.venv
```

The `.venv/` directory is local runtime infrastructure. It must be ignored by Git and must not be treated as source, documentation, contract content, or reviewable project output.

Component repositories should not create independent virtual environments unless a documented exception is approved.

The accepted shared environment baseline is:

- Python runtime: Python 3.12.
- Environment anchor: `/root/projects/trading-main/.venv`.
- Package installer: `python -m pip` inside the shared environment.
- Dependency ledger: `requirements.txt` at the `trading-main` root.
- Installation command: `/root/projects/trading-main/.venv/bin/python -m pip install -r /root/projects/trading-main/requirements.txt`.
- Component repositories should not create independent virtual environments unless a documented exception is accepted.
- Dependencies are added only through reviewed commits; no ad hoc package installs become project state.

`trading-main` may document and anchor the shared environment, but it must not become a runtime implementation repository.

## Trading Registry, Templates, and Helpers

Because this server's project work is centered on the trading system, `trading-main` is the canonical home for trading-wide shared assets:

- `src/` stores shared helper code used by component repositories; `docs/07_helpers.md` explains the helper boundary.
- `scripts/` maintains the SQL-backed registration system; `docs/08_registry.md` explains the registry operating model.
- `storage/templates/` stores reusable trading project, contract, task, and implementation templates; `docs/09_templates.md` explains the template boundary.

Shared helpers are allowed in `trading-main`, but they must remain generic trading infrastructure. Component-specific runtime behavior still belongs in the owning component repository.

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

- `trading-main/scripts/` and `docs/08_registry.md` for registered names, shared status vocabularies, and registrable fields;
- `requirements.txt` in `trading-main` for reviewed shared Python dependencies;
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

For `trading-main`, Codex should normally not be needed unless there is a bulk documentation transformation or validation script explicitly delegated. This repository is primarily OpenClaw-authored.

## Important Constraints

- `trading-main` owns docs, contracts, registries, templates, shared helpers, and the gitignored shared environment anchor.
- Cross-repository behavior must be described through explicit contracts before implementation depends on it.
- Component repositories must not silently fork global contracts.
- Trading-wide status vocabularies and registrable fields belong in `trading-main/scripts/`; registry operating details belong in `docs/08_registry.md`.
- Component-specific details belong in the component repository docs, not in `trading-main`.
- Market-state discovery must not be contaminated by strategy performance.
- Execution-related code must treat broker and exchange operations as safety-sensitive external actions.
- Secrets and credentials must stay outside project repositories.
- Acceptance must be evidence-based; unsupported narrative completion is not enough.

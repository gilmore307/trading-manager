# Context

## Why This Project Exists

The trading project is a core multi-repository system for building, evaluating, selecting, executing, and observing trading workflows.

The system needs a stable global coordination layer because its responsibilities are intentionally split across multiple repositories. Without a shared architecture and contract repository, each component could invent incompatible artifact layouts, request formats, manifest schemas, ready-signal conventions, and responsibility boundaries.

`trading-main` exists to keep those global relationships explicit and reviewable.

## Related Systems

### Component Repositories

| Repository | System-Level Role | Summary |
|---|---|---|
| `trading-main` | Global documentation and contract layer | Owns system architecture, global workflow, shared contracts, system-level decisions, and cross-repository planning. It does not store data or runtime code. |
| `trading-manager` | Control plane | Coordinates workflow sequencing, schedules, queues, readiness checks, retries, recovery, manual override, lifecycle policy, request generation, and watchlist coordination. |
| `trading-data` | Data upstream | Connects to data sources, fetches market/regime/options data, normalizes rows, writes data outputs, and emits ready signals. |
| `trading-storage` | Shared persistence contract | Defines persistent storage layout, artifact placement, partitioning, retention, archive, rehydrate, backup, and restore expectations. |
| `trading-strategy` | Strategy research and backtest runtime | Runs strategy families and variants against historical data and produces standardized trades, returns, equity curves, summaries, manifests, and oracle outputs. |
| `trading-model` | Offline modeling and market-state research | Discovers market states from market-only features, evaluates state usefulness after attaching strategy results, and outputs mappings, confidence, and research verdicts. |
| `trading-execution` | Live/paper execution runtime | Runs trading daemons, creates execution plans, places broker/exchange orders, records positions/orders, reconciles state, and emits execution artifacts. |
| `trading-dashboard` | Downstream UI and visualization | Displays already-produced trading outputs through dashboard pages, server endpoints, and visualization adapters. |

The repository map is intentionally high-level. Detailed repository scope, local workflow, acceptance rules, implementation notes, and task state belong in each component repository's own docs spine.

### External Services and Interfaces

Current expected external interfaces include:

- market data APIs;
- macroeconomic and calendar data sources;
- broker or exchange APIs, including OKX or Alpaca;
- local or shared filesystem storage used by the trading repositories;
- `universal-catalog` for shared registered names, status vocabularies, and registrable fields;
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

The shared environment contract should define:

- Python/runtime versions;
- package manager;
- dependency installation policy;
- test/lint/format command conventions;
- CPU/GPU assumptions;
- timezone and timestamp conventions;
- local secrets policy;
- how component repositories declare additional dependencies;
- when a component repository may request an environment exception.

`trading-main` may document and anchor the shared environment, but it must not become a runtime implementation repository.

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

- `universal-catalog` for registered names, shared status vocabularies, and registrable fields;
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

- `trading-main` must remain documentation-only and contract-only, except for the gitignored shared environment anchor.
- Cross-repository behavior must be described through explicit contracts before implementation depends on it.
- Component repositories must not silently fork global contracts.
- Shared status vocabularies and registrable fields belong in `universal-catalog`.
- Component-specific details belong in the component repository docs, not in `trading-main`.
- Market-state discovery must not be contaminated by strategy performance.
- Execution-related code must treat broker and exchange operations as safety-sensitive external actions.
- Secrets and credentials must stay outside project repositories.
- Acceptance must be evidence-based; unsupported narrative completion is not enough.

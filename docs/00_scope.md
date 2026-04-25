# Scope

## Purpose

`trading-main` is the system-level documentation and contract repository for the full trading project.

It defines the global architecture, repository relationships, cross-repository workflow, shared artifact contracts, manifest contracts, ready-signal contracts, request contracts, and project-level governance rules for the trading system.

This repository exists to keep the multi-repository trading system coherent. It does not implement trading logic, store market data, run models, execute trades, or host dashboard code.

## In Scope

- Define the global trading-system architecture.
- Define the official trading repository map.
- Define cross-repository workflow and handoff rules.
- Define shared artifact contracts.
- Define shared manifest contracts.
- Define shared ready-signal contracts.
- Define shared request contracts.
- Reference shared status vocabularies and registered fields maintained in `universal-catalog`.
- Record system-level acceptance rules.
- Record system-level architectural decisions.
- Track system-level planning tasks before they are delegated to component repositories.
- Preserve durable system-level memory that does not belong to a single component repository.
- Anchor the shared local trading development environment through a gitignored `.venv/` directory.

## Out of Scope

- Market data collection.
- Market data normalization.
- Persistent market-data storage.
- Strategy backtesting or simulation.
- Strategy-family implementation.
- Model training.
- Market-state discovery implementation.
- Strategy selection implementation.
- Live or paper trade execution.
- Broker or exchange order placement.
- Dashboard frontend implementation.
- Dashboard backend/server implementation.
- Component-repository task queues once work has moved into that component repo.
- Raw data, generated artifacts, notebooks, logs, or research outputs.
- Secrets, credentials, API tokens, brokerage credentials, or exchange keys.
- Source code for runtime trading components.

## Owner Intent

The owner intends the trading project to be a large, core multi-repository system on this server.

`trading-main` should act as the stable global coordination layer for that system. It should keep project shape, repository relationships, shared contracts, and architecture decisions explicit before implementation work spreads across component repositories.

The project should prefer strict boundaries, durable contracts, and evidence-based acceptance over fast but vague implementation.

## Boundary Rules

- `trading-main` is documentation-only and contract-only, except for the local shared environment anchor.
- `trading-main` must not contain runtime source code.
- `trading-main` must not contain market data or generated trading artifacts.
- `trading-main` must not contain secrets or credentials.
- `trading-main` may contain a local gitignored `.venv/` directory as the shared trading development environment anchor.
- The `.venv/` directory is runtime infrastructure, not repository content.
- Component repositories may implement or consume contracts defined here, but they must not redefine incompatible local versions of global contracts.
- Each component repository must keep its own docs spine; `trading-main` does not replace component-level documentation.
- Global status vocabularies and registrable fields are maintained in `universal-catalog`; this repository may reference them but should not fork them.
- A fact should live in the narrowest authoritative home:
  - system-wide facts live here;
  - component-specific facts live in the relevant component repository;
  - shared registered names and vocabularies live in `universal-catalog`.
- Market-state discovery must not use strategy returns or strategy performance as input. Strategy results may only be attached after market states have already been discovered.
- `trading-storage` owns shared persistent storage contracts for trading artifacts; `trading-main` defines the system-level relationship to those contracts.

## Out-of-Scope Signals

A request should be rejected or re-scoped if it asks `trading-main` to:

- implement trading runtime code;
- fetch or normalize market data;
- run backtests;
- train models;
- execute orders;
- store generated data or artifacts;
- become a dumping ground for component-specific implementation notes;
- duplicate status vocabulary that should be maintained in `universal-catalog`;
- override a component repo's local docs instead of referencing them;
- accept a cross-repository behavior without a documented contract;
- define market states using strategy returns or strategy profitability.

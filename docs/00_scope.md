# Scope

`trading-manager` is the trading system's control-plane and shared-contract repository.

## In Scope

- Repository map and cross-repository responsibility boundaries.
- Trading-wide registry, registry rules, and generated registry snapshot.
- Shared Python helper packages used by manager scripts and component repos.
- Control-plane contracts: requests, input bindings, run manifests, run steps, artifact references, ready signals, task summaries, review decisions, promotion decisions, and scheduler state.
- Manager-owned task planning and component handoff validation.
- Historical-modeling scheduler policy and resident-service state.
- Dataset expansion policy, evidence collection, and safe information-pass planning.
- Promotion-review and activation-gate policy.
- System-level task, decision, and memory records.

## Out of Scope

- Provider/feed adapter implementation.
- Data cleaning, feature construction, and data-production runtime.
- Model training algorithms and model package implementation.
- Broker, exchange, order, fill, account, or position mutation.
- Persistent market-data storage layout and retention execution.
- Dashboard application code.
- Generated artifacts, caches, logs, local runtime state, and secrets.

## Authority Rule

Manager may plan, gate, route, validate, summarize, and record evidence. Manager may not silently take over component responsibilities. If work requires data production, modeling, storage mutation, execution, or UI implementation, manager must issue a contract or handoff instead of embedding that runtime locally.

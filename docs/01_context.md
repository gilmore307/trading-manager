# Context

The trading system is split into focused repositories so each boundary can stay testable and auditable.

## Repository Map

| Repository | Primary role | Manager relationship |
|---|---|---|
| `trading-manager` | Control plane, registry, contracts, workflow, review gates, shared helpers | Owns global routing and evidence policy. |
| `trading-data` | Provider feeds, ingestion, source rows, feature rows | Receives manager requests and emits receipts/artifact refs. |
| `trading-model` | Model design, training, evaluation, diagnostics, promotion candidates | Consumes point-in-time inputs and emits model/evaluation/promotion evidence. |
| `trading-evaluation` | Frozen benchmarks, fold settlement, promotion eligibility, promotion readiness | Judges completed folds independently and admits candidates to execution shadow review; manager records status but does not own model-quality judgment or activation. |
| `trading-execution` | Runtime active/shadow model lifecycle | Runs the active model plus promoted shadow candidates and owns post-cycle active/realtime/eliminate roster selection. |
| `trading-storage` | Durable storage layout, lifecycle, archive/rehydrate, dashboard read models | Stores large payloads and executes lifecycle policy with receipts. |
| `trading-execution` | Paper/live execution, broker interfaces, orders, fills, account/position reconciliation | Owns all broker/account mutation. Manager can validate handoffs but cannot execute. |
| `trading-dashboard` | UI and visualization | Reads published status and dashboard payloads. |

## Operating Assumptions

- US Eastern time is the default human planning timezone unless a contract states otherwise.
- Point-in-time availability is mandatory for historical modeling and promotion evidence.
- Generated payloads should be referenced by URI/hash/metadata instead of copied into SQL rows.
- Provider calls, storage lifecycle mutation, benchmark judgment/model activation, and broker/account actions are separate gates.
- Runtime state lives under `trading-storage/storage/control_plane/runtime/`; component-local `storage/` directories are not part of the active manager shape.

## Normal Direction of Work

```text
manager request -> component execution -> completion receipt -> run/artifact/ready rows -> summary/review/evaluation/promotion gate
```

A component may own implementation details, but manager owns whether the output is accepted for the declared downstream purpose.

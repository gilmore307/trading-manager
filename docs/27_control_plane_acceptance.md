# Manager Control-Plane Acceptance

The manager control-plane MVP is accepted when it can plan work, validate inputs, record component results, summarize state, and enforce gates without taking over component runtimes.

## Accepted Scope

- SQL-backed request/run/artifact/ready contracts.
- Request validation and payload materialization.
- Completion receipt normalization.
- Priority task summary.
- Monthly backfill planning.
- Dataset evidence collection and expansion planning.
- Promotion-review request planning.
- Historical scheduler state, lock, decisions, status, and progress summary.
- Failure register and safe repair surfaces.

## Still Component-Owned

- Provider adapter behavior and data production.
- Model implementation and training algorithms.
- Durable storage lifecycle execution.
- Broker/order/fill/account mutation.
- Dashboard app implementation.

## Acceptance Rule

Manager control-plane acceptance does not imply production readiness for any model, event family, storage policy, provider volume, or execution path. Each downstream boundary keeps its own evidence gate.

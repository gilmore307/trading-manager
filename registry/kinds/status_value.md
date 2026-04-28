# status_value

Registered status or policy values consumed by task records, review queues, acceptance receipts, tests, maintenance outputs, documentation checks, and registry row review policy columns.

Use this kind for allowed state-like values such as lifecycle states, review readiness, acceptance outcomes, test status, maintenance status, docs status, and artifact sync policies.

The status domain belongs in `applies_to`, for example:

- `task_lifecycle_status`
- `review_readiness`
- `acceptance_outcome`
- `test_status`
- `maintenance_status`
- `docs_status`
- `trading_registry.artifact_sync_policy`

Rules:

- Keep the status slot name itself registered as a `field` row when it appears in records or templates.
- Keep the status value registered here when code, receipts, or docs need a shared allowed value.
- Do not create a separate kind for each status domain.
- Do not use this kind for entity categories such as request types, ready-signal types, manifest types, artifact types, payload formats, data kinds, data sources, or data bundles.

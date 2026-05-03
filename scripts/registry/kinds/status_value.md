# status_value

Registered status or policy values consumed by task records, review queues, acceptance receipts, tests, maintenance outputs, documentation checks, and registry row review policy columns.

Use this kind for allowed state-like values such as lifecycle statuses, review statuses, acceptance statuses, test statuses, maintenance statuses, docs statuses, and artifact sync policy type values.

The status domain belongs in `applies_to`, for example:

- `task_lifecycle_status`
- `review_status`
- `acceptance_status`
- `test_status`
- `maintenance_status`
- `docs_status`
- `artifact_sync_policy_type`

Rules:

- Keep the status or policy-type slot name itself registered as a `classification_field` row when it appears in records or templates.
- Keep the status value registered here when code, receipts, or docs need a shared allowed value.
- Do not create a separate kind for each status domain.
- Do not use this kind for entity categories such as request types, ready-signal types, manifest types, artifact types, payload formats, data kinds, data feeds, or data sources.

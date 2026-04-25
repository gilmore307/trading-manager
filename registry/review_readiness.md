# Review Readiness

## Kind Boundary

Default review-readiness values for completion receipts and review queues.

## Range

Use for review-readiness vocabulary only.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `rrd_V9H5C2KR` | `REVIEW_READINESS_BLOCKED` | `text` | `blocked` | default shared review readiness value for work that is blocked from review | `002_bootstrap_universal_catalog.sql` |
| `rrd_W6P3N1TX` | `REVIEW_READINESS_NOT_READY` | `text` | `not_ready` | default shared review readiness value for work that is not ready for review | `002_bootstrap_universal_catalog.sql` |
| `rrd_L2F8Q4MA` | `REVIEW_READINESS_READY` | `text` | `ready` | default shared review readiness value for work that is ready for review | `002_bootstrap_universal_catalog.sql` |

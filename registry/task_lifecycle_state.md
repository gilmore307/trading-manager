# Task Lifecycle State

## Kind Boundary

Default task lifecycle state values for planning and execution records.

## Range

Use for task lifecycle vocabulary only.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `tls_H1V8L4TE` | `TASK_LIFECYCLE_STATE_ACCEPTED` | `text` | `accepted` | default shared task lifecycle state value for work that has been accepted | `002_bootstrap_universal_catalog.sql` |
| `tls_K5Q7F2MD` | `TASK_LIFECYCLE_STATE_BLOCKED` | `text` | `blocked` | default shared task lifecycle state value for work that is blocked | `002_bootstrap_universal_catalog.sql` |
| `tls_C9T1G7WF` | `TASK_LIFECYCLE_STATE_CANCELLED` | `text` | `cancelled` | default shared task lifecycle state value for work that has been cancelled | `002_bootstrap_universal_catalog.sql` |
| `tls_M4D6R8QJ` | `TASK_LIFECYCLE_STATE_CLOSED` | `text` | `closed` | default shared task lifecycle state value for work that is closed | `002_bootstrap_universal_catalog.sql` |
| `tls_D4N8K2QW` | `TASK_LIFECYCLE_STATE_DESIGNING` | `text` | `designing` | default shared task lifecycle state value for work that is still being designed | `002_bootstrap_universal_catalog.sql` |
| `tls_B6X2H5RA` | `TASK_LIFECYCLE_STATE_DISPATCHED` | `text` | `dispatched` | default shared task lifecycle state value for work that has been dispatched | `002_bootstrap_universal_catalog.sql` |
| `tls_T8J4W1NP` | `TASK_LIFECYCLE_STATE_EXECUTING` | `text` | `executing` | default shared task lifecycle state value for work in active execution | `002_bootstrap_universal_catalog.sql` |
| `tls_R3C9Y6UA` | `TASK_LIFECYCLE_STATE_READY_FOR_ACCEPTANCE` | `text` | `ready_for_acceptance` | default shared task lifecycle state value for work waiting for acceptance review | `002_bootstrap_universal_catalog.sql` |
| `tls_P7M3V9LC` | `TASK_LIFECYCLE_STATE_READY_TO_DISPATCH` | `text` | `ready_to_dispatch` | default shared task lifecycle state value for work ready to hand to an executor | `002_bootstrap_universal_catalog.sql` |
| `tls_N7B2P5XK` | `TASK_LIFECYCLE_STATE_REJECTED` | `text` | `rejected` | default shared task lifecycle state value for work that has been rejected | `002_bootstrap_universal_catalog.sql` |

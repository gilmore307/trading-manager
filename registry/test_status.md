# Test Status

## Kind Boundary

Default test/verification status values.

## Range

Use for verification status vocabulary only.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `tst_F6V1M5RA` | `TEST_STATUS_FAILED` | `text` | `failed` | default shared test status value for failing verification | `002_bootstrap_universal_catalog.sql` |
| `tst_X5N1B4QJ` | `TEST_STATUS_NOT_REQUIRED` | `text` | `not_required` | default shared test status value when verification was not required | `002_bootstrap_universal_catalog.sql` |
| `tst_P9C4T7XH` | `TEST_STATUS_NOT_RUN` | `text` | `not_run` | default shared test status value when verification did not run | `002_bootstrap_universal_catalog.sql` |
| `tst_R2D6K8YL` | `TEST_STATUS_PARTIALLY_RUN` | `text` | `partially_run` | default shared test status value when verification ran only partially | `002_bootstrap_universal_catalog.sql` |
| `tst_J3Q8L2NW` | `TEST_STATUS_PASSED` | `text` | `passed` | default shared test status value for passing verification | `002_bootstrap_universal_catalog.sql` |

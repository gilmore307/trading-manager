# Maintenance Status

## Kind Boundary

Default maintenance pass status values.

## Range

Use for maintenance result vocabulary only.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `mns_B5N1K6XD` | `MAINTENANCE_STATUS_BLOCKED` | `text` | `blocked` | default shared maintenance status value when maintenance is blocked by a real constraint | `002_bootstrap_universal_catalog.sql` |
| `mns_L4T8Q2WP` | `MAINTENANCE_STATUS_HEALTHY` | `text` | `healthy` | default shared maintenance status value when the project is in healthy maintained shape | `002_bootstrap_universal_catalog.sql` |
| `mns_P7C3V9RA` | `MAINTENANCE_STATUS_NEEDS_ATTENTION` | `text` | `needs_attention` | default shared maintenance status value when maintenance found issues that need attention | `002_bootstrap_universal_catalog.sql` |

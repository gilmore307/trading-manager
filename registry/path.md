# Path

## Kind Boundary

Canonical filesystem path values. Use only for stable reviewed paths that should be referenced consistently.

## Range

Use for reviewed path values only. Do not store secrets or disposable artifact paths.

## Entries

| id | key | payload_format | payload | note | source_migration |
|---|---|---|---|---|---|
| `pth_R6V1C9TE` | `NETWORK_FRAMEWORK_ROOT_PATH` | `text` | `/root/projects/network-framework` | repository root path for the network-framework checkout | `002_bootstrap_universal_catalog.sql` |
| `pth_C4X8N2ME` | `TRADING_MAIN_ROOT_PATH` | `text` | `/root/projects/trading-main` | repository root path for the trading-main checkout | `002_bootstrap_universal_catalog.sql` |

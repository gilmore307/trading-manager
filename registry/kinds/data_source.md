# Data Source

## Kind Boundary

Implemented source-interface or source-adapter identifiers that fetch, parse, probe, or normalize data from an external provider, official website, exchange, issuer file, or source system.

A data source is not a manager-facing bundle and is not a final saved data shape. It names the implemented source boundary that pipelines or source-interface probes call.

## Range

Register data sources when they have an implemented source directory, source-interface catalog entry, or execution-owned source discovery adapter.

Use `payload` for the stable snake_case source adapter key. Use `path` for the implementation directory or source-interface owner path.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- manager-facing runnable bundles, which belong in `data_bundle`;
- final saved output/data shapes, which belong in `data_kind`;
- provider/company names, which belong in `term`;
- credentials or source aliases, which belong in `config`;
- callable helper exports, which belong in `script`.

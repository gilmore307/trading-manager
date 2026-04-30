# Data Source

## Kind Boundary

Manager-facing `trading-source` source-output identifiers accepted for task routing, runner dispatch, model-input source tables, and completion receipts.

A data source is a source-backed output boundary that a manager can request directly. Provider/API/web/file connectors are not data sources; they belong in `data_feed`.

## Range

Register data sources when they may appear in manager-facing task keys, runner routing, source READMEs, completion receipts, or model-input planning docs.

Use `payload` for the concrete `source_NN_<layer>` source key. Use `path` for the canonical manager-facing implementation directory, normally under `trading-source/src/data_sources/source_NN_<layer>`.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- provider/API/web/file feeds, which belong in `data_feed`;
- manager-facing generated-data outputs, which belong in `data_derived`;
- final saved dataset shapes independent of the producing source, which belong in `data_kind`;
- provider/company names, which belong in `provider`;
- credentials or secret aliases, which belong in `config`;
- runtime JSON fields, which belong in `field`;
- scripts or Python symbols, which belong in `script`;
- template files, which belong in `template`;
- shared checked-in data/config artifacts, which belong in `shared_artifact`.

## Naming Rule

Source keys should be stable snake_case and use the accepted `source_NN_<layer>` pattern, such as `source_01_market_regime`. Source-specific task/run IDs should use the source key as their prefix.

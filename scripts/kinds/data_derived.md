# Data Derived

## Kind Boundary

Manager-facing `trading-derived` derived-output identifiers accepted for derived-data routing, model-input planning, storage contracts, and completion receipts.

A data-derived boundary is an internally generated output surface that a manager or model pipeline can request directly. External/source-backed acquisition outputs belong in `data_source`; provider/API/web/file connectors belong in `data_feed`.

## Range

Register data-derived rows when they may appear in derived task keys, derived runner routing, model-input planning docs, storage contracts, completion receipts, or cross-repository handoffs.

Use `payload` for the concrete `NN_derived_<layer>` derived key. Use `path` for the canonical implementation directory when accepted, normally under `trading-derived/src/data_derived/NN_derived_<layer>`.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- provider/API/web/file feeds, which belong in `data_feed`;
- source-backed acquisition outputs, which belong in `data_source`;
- shared checked-in data/config artifacts, which belong in `shared_artifact`;
- runtime fields, which belong in field-like kinds;
- scripts or Python symbols, which belong in `script`;
- provider/company names, which belong in `provider`;
- credentials or secret aliases, which belong in `config`.

## Naming Rule

Derived keys should be stable snake_case and use the accepted `NN_derived_<layer>` pattern, such as `01_derived_market_regime`, mirroring the `NN_source_<layer>` source naming pattern.

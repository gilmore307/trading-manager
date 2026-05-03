# Data Feature

## Kind Boundary

Manager-facing `trading-data` deterministic feature-output identifiers accepted for feature routing, model-input planning, storage contracts, and completion receipts.

A data-feature boundary is a point-in-time feature surface produced from accepted feed/source data for direct model consumption. Provider/API/web/file connectors belong in `data_feed`; model-scoped observed-data tables belong in `data_source`; model outputs and evaluation artifacts belong in `trading-model` contracts.

## Range

Register data-feature rows when they may appear in data/feature task keys, feature runner routing, model-input planning docs, storage contracts, completion receipts, or cross-repository handoffs.

Use `payload` for the concrete `feature_NN_<layer>` feature key. Use `path` for the canonical implementation directory when accepted, normally under `trading-data/src/data_feature/feature_NN_<layer>`.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- provider/API/web/file feeds, which belong in `data_feed`;
- source-backed observed-data outputs, which belong in `data_source`;
- model outputs, evaluation labels, evaluation runs, or metrics, which belong in model-owned contracts;
- shared checked-in data/config artifacts, which belong in `shared_artifact`;
- runtime fields, which belong in field-like kinds;
- scripts or Python symbols, which belong in `script`;
- provider/company names, which belong in `provider`;
- credentials or secret aliases, which belong in `config`.

## Naming Rule

Feature keys should be stable snake_case and use the accepted `feature_NN_<layer>` pattern, such as `feature_01_market_regime`, mirroring the `source_NN_<layer>` source naming pattern.

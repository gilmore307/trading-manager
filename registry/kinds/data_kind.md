# Data Kind

## Kind Boundary

Canonical data-kind identifiers for source-provided or derived data categories that `trading-data` can acquire, clean, validate, or route through task parameters.

A data kind is narrower than a `data_bundle` and usually names the actual obtainable dataset family or output class, such as bars, quotes, option Greeks, SEC company facts, CPI, GDP, or Treasury debt datasets.

## Range

Register data kinds when they are useful for:

- `macro_data.params` source/dataset/release/series validation;
- bundle-specific accepted dataset choices;
- output routing and table/partition planning;
- avoiding duplicate names for the same obtainable data category;
- documenting source-of-truth ownership for a data category.

Use `payload` for a stable snake_case data-kind key. For final saved data kinds with accepted templates, use `path` for the canonical source-specific `trading-data/storage/templates/data_kinds/<source>/*.preview.csv` template/preview file. For source-only or transient data kinds without accepted final templates, leave `path` null until a final template exists. Provider/source documentation URLs belong on provider/source `term` rows, not on final `data_kind` rows. Use `applies_to` for the owning source, bundle, or component scope.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- acquisition bundle names, which belong in `data_bundle`;
- provider/source names, which belong in `term`;
- credential aliases, which belong in `config`;
- runtime JSON fields, which belong in `field`;
- saved artifacts or template outputs, which belong in `output` or future storage contracts.

## Source Consistency Rule

The same economic measure should have one canonical acquisition source. FRED data kinds should be limited to FRED/St. Louis Fed/ALFRED-unique data or explicitly approved FRED-native research series/groups; official BLS, BEA, Census, Treasury, and other agency measures should use their official sources as canonical unless an exception is explicitly reviewed.

## Derived and Raw High-Volume Data

`data_kind` may name both source-provided categories and derived categories. For very high-volume source rows such as equity trades and quotes, source data kinds remain request/validation inputs, but default persistence should target registered final aggregate kinds such as `equity_liquidity_bar`. Raw rows may be streamed or temporarily segmented during a run and discarded after aggregation unless an explicit bounded debug or audit artifact is approved. Final saved data kinds should have a CSV preview/template under a source-specific `trading-data/storage/templates/data_kinds/<source>/` folder, and the registry `path` should point to that template file.

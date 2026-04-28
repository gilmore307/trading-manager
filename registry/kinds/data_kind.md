# Data Kind

## Kind Boundary

Canonical final saved or durable derived data-shape identifiers that have accepted templates and can be consumed across trading repositories.

A data kind names the saved/output shape, not every provider endpoint, transient source input, entitlement-blocked interface, or source-interface catalog item.

## Range

Register active data kinds only when the data kind has an accepted preview/template file under `trading-data/storage/templates/data_kinds/<source>/*.preview.csv`, and `path` points to that file.

Use `payload` for a stable snake_case data-kind key. Use `path` for the canonical source-specific preview/template file. Provider/source documentation URLs belong on provider/source `term` rows, not on `data_kind` rows.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- acquisition bundle names, which belong in `data_bundle`;
- provider/source names, which belong in `term`;
- provider endpoint names or source-interface catalog items, which belong in `data_source`/source-interface code;
- transient source inputs such as trades, quotes, order books, raw Greeks, or entitlement-blocked endpoint families unless and until they become accepted saved templates;
- broad wishlist concepts or deprecated concepts with no current consumer;
- credential aliases, which belong in `config`;
- runtime JSON fields, which belong in `field`;
- template artifacts, which belong in `template`;
- live shared checked-in artifacts, which belong in `shared_artifact`.

## Source Consistency Rule

The same economic measure should have one canonical acquisition source. FRED data kinds should be limited to FRED/St. Louis Fed/ALFRED-unique data or explicitly approved FRED-native research series/groups; official BLS, BEA, Census, Treasury, and other agency measures should use their official sources as canonical unless an exception is explicitly reviewed.

## Derived and Raw High-Volume Data

`data_kind` may name durable derived categories such as model input products or event factors when they have accepted saved templates. High-volume raw/source rows such as trades, quotes, order books, raw Greeks, SEC endpoint payloads, or calendar scraping inputs are not `data_kind` rows unless they become accepted final saved shapes. They may exist as run-local evidence, transient cleaned files, source-interface catalog entries, or implementation details without registry `data_kind` status.

# Data Kind

## Kind Boundary

Canonical final saved data-shape identifiers that have accepted reviewed storage contracts and can be consumed across trading repositories. Manager-facing `trading-derived` generated-output boundaries belong in `data_derived`.

A data kind names the saved/output shape, not every provider endpoint, transient source input, entitlement-blocked interface, feed-interface catalog item, or retired preview/template file.

## Range

Register active data kinds only when the data kind has an accepted, current storage contract. Retired preview/template files under `trading-source/storage/templates/data_kinds/` are not evidence for active `data_kind` status.

Use `payload` for a stable snake_case data-kind key. Use `path` only for the canonical current contract artifact when one exists; provider/feed documentation URLs belong on provider/feed `term` or `feed_capability` rows, not on `data_kind` rows.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- manager-facing acquisition source names, which belong in `data_source`;
- manager-facing derived output boundaries, which belong in `data_derived`;
- provider/feed-owner names, which belong in `provider`;
- provider endpoint names or feed-interface catalog items, which belong in `data_feed`/feed-interface code;
- transient source inputs such as trades, quotes, order books, raw Greeks, or entitlement-blocked endpoint families unless and until they become accepted saved templates;
- broad wishlist concepts or deprecated concepts with no current consumer;
- credential aliases, which belong in `config`;
- runtime JSON fields, which belong in `field`;
- retired preview/template artifacts, which should be deleted rather than preserved as active data kinds;
- reusable template artifacts, which belong in `template`;
- live shared checked-in artifacts, which belong in `shared_artifact`.

## Source Consistency Rule

The same economic measure should have one canonical acquisition source. FRED data kinds should be limited to FRED/St. Louis Fed/ALFRED-unique data or explicitly approved FRED-native research series/groups; official BLS, BEA, Census, Treasury, and other agency measures should use their official sources as canonical unless an exception is explicitly reviewed.

## Derived and Raw High-Volume Data

`data_kind` may name durable derived categories such as model input products or event factors when they have accepted current storage contracts. High-volume raw/source rows such as trades, quotes, order books, raw Greeks, SEC endpoint payloads, or calendar scraping inputs are not `data_kind` rows unless they become accepted final saved shapes. They may exist as run-local evidence, transient cleaned files, feed-interface catalog entries, or implementation details without registry `data_kind` status.

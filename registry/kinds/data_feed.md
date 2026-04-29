# Data Feed

## Kind Boundary

Implemented provider/API/web/file feed identifiers that fetch, parse, probe, or normalize the smallest external data-access surface owned by `trading-source`.

A data feed is not a manager-facing source output and is not a final saved data shape. It names the provider-facing boundary that source pipelines, feed-interface probes, or availability checks call.

## Range

Register data feeds when they have an implemented feed directory, feed-interface catalog entry, or execution-owned feed discovery adapter.

Use `payload` for the stable snake_case feed key. Use `path` for the implementation directory or feed-interface owner path, normally under `trading-source/src/data_feed/NN_feed_<surface>`.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- manager-facing runnable source outputs, which belong in `data_source`;
- final saved output/data shapes, which belong in `data_kind`;
- provider/company names, which belong in `provider`;
- credentials or secret aliases, which belong in `config`;
- callable helper exports, which belong in `script`.

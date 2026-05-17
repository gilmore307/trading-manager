# Data Source

## Meaning

`data_source` names manager-facing trading-data source-output boundaries.

## Register Here

Register source_NN_* outputs that manager can request directly and that can appear in task keys, runner routing, receipts, or model-input planning.

## Do Not Register Here

- provider feed adapters;
- feature outputs;
- final data shapes;
- provider names;
- credentials;
- runtime fields;
- scripts;
- templates;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

# Data Feature

## Meaning

`data_feature` names deterministic model-facing feature surfaces produced by trading-data.

## Register Here

Register feature_NN_* outputs that can appear in feature routing, model-input planning, receipts, or storage contracts.

## Do Not Register Here

- provider feeds;
- source-backed observed outputs;
- model outputs;
- final saved data shapes;
- runtime fields;
- scripts;
- credentials;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

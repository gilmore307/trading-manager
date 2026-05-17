# Data Feed

## Meaning

`data_feed` names implemented provider/API/web/file feed interfaces.

## Register Here

Register smallest implemented external data-access surfaces used by trading-data feed adapters or availability checks.

## Do Not Register Here

- control-plane source outputs;
- final data shapes;
- provider organizations;
- credentials;
- helper functions;
- model outputs;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

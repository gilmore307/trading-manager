# Shared Artifact

## Meaning

`shared_artifact` names durable checked-in shared data/config assets.

## Register Here

Register stable files intentionally consumed by multiple repositories and useful to expose through a registry locator.

## Do Not Register Here

- templates;
- runtime output instances;
- provider adapters;
- feature outputs;
- final data kinds;
- non-secret config defaults;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

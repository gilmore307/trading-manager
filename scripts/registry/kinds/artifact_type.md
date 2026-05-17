# Artifact Type

## Meaning

`artifact_type` classifies durable artifact categories produced or consumed across repositories.

## Register Here

Register artifact category values such as model outputs, receipts, reports, logs, manifests, dashboard payloads, and evidence bundles.

## Do Not Register Here

- artifact instance paths;
- filesystem locators;
- manifest schemas;
- request types;
- template files;
- status values;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

# Request Type

## Meaning

`request_type` classifies cross-repository manager work requests.

## Register Here

Register request type values only.

## Do Not Register Here

- request instances;
- workflow names;
- task lifecycle statuses;
- component-local queue names;
- script names;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

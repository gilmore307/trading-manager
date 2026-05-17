# Parameter Field

## Meaning

`parameter_field` names fields that carry task/request parameter objects or parameter collections.

## Register Here

Register fields such as params, request_parameters, and parameter bundles accepted by task/source/template contracts.

## Do Not Register Here

- single identity fields;
- single temporal fields;
- single classification axes;
- free-text explanations;
- ordinary output measurements;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

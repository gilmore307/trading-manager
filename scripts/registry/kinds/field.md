# Field

## Meaning

`field` names shared non-identity, non-temporal, non-classification, non-path, non-text, non-parameter schema slots.

## Register Here

Register metrics, counts, booleans, structured JSON slots, numeric values, and generic contract fields used in shared records.

## Do Not Register Here

- status values;
- repository names;
- identity/name fields;
- temporal fields;
- classification axes;
- paths/URLs/refs;
- free-text notes;
- parameter objects;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

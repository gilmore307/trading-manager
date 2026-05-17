# Text Field

## Meaning

`text_field` names fields whose values are human-readable text.

## Register Here

Register summaries, explanations, caveats, diagnostics, errors, notes, known issues, acceptance text, and documentation-oriented text columns.

## Do Not Register Here

- numeric metrics;
- identifiers;
- paths/URLs/refs;
- temporal values;
- classification axes;
- status values;
- parameter objects;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

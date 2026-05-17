# Payload Format

## Meaning

`payload_format` names values allowed in the trading_registry.payload_format column.

## Register Here

Register format tokens that tell consumers how to interpret registry row payload text.

## Do Not Register Here

- field names;
- status values;
- helper functions;
- source files;
- component-local parsing notes;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

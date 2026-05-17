# Ready Signal Type

## Meaning

`ready_signal_type` classifies downstream consumability signals.

## Register Here

Register ready-signal type values only.

## Do Not Register Here

- readiness statuses;
- manifest types;
- request types;
- alert schemas;
- field names;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

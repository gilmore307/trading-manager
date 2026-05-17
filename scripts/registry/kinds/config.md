# Config

## Meaning

`config` names non-secret configuration values and secret-alias references.

## Register Here

Register non-secret defaults, config keys, provider/source secret aliases, and local environment knobs that are safe to register.

## Do Not Register Here

- raw API keys;
- passwords;
- tokens;
- broker credentials;
- connection strings;
- source-file locators;
- status values;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

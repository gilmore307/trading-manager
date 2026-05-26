# Term

## Meaning

`term` is the system dictionary for approved shared concepts and definitions.

## Register Here

Register durable glossary terms that help cross-repository contracts use the same language. A term row explains what a system-defined noun means; it is not a bucket for concrete implementation values.

## Do Not Register Here

- task state;
- component-local notes;
- config values;
- policy values;
- SQL table names;
- artifact, request, manifest, ready-signal, receipt, report, or contract categories;
- enum/status/reason values;
- field names;
- provider identities;
- feed endpoint capabilities;
- implementation files;

## Row Rules

- `payload` must hold the stable dictionary token, not prose.
- `note` must define the term in human-readable language.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

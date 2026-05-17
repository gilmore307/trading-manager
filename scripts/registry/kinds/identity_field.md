# Identity Field

## Meaning

`identity_field` names fields whose values identify or name an entity, artifact, source, instrument, task, report, or row.

## Register Here

Register ids, symbols, names, titles, headlines, contract symbols, CUSIPs, SEDOLs, and stable entity identifiers.

## Do Not Register Here

- measurements;
- scores;
- counts;
- timestamps;
- status values;
- classification axes;
- paths/URLs/refs;
- free-text summaries;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

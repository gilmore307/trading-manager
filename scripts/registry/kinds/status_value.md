# Status Value

## Meaning

`status_value` names allowed status or policy values.

## Register Here

Register shared lifecycle, review, acceptance, test, maintenance, docs, artifact-sync-policy, and task-status values.

## Do Not Register Here

- the field slot carrying the status;
- entity categories;
- request types;
- manifest types;
- artifact types;
- payload formats;
- data kinds;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

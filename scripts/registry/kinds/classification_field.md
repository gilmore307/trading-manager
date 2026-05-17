# Classification Field

## Meaning

`classification_field` names fields whose values classify, bucket, type, tag, scope, or categorize a row.

## Register Here

Register field names such as event_type, source_type, impact_scope, universe_type, asset_class, option_right_type, policy_type, and tags.

## Do Not Register Here

- status values themselves;
- identity/name fields;
- temporal fields;
- path/reference fields;
- free-text summaries;
- numeric measurements;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

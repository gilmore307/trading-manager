# Path Field

## Meaning

`path_field` names fields whose values locate or reference artifacts, files, URLs, repositories, source refs, or output refs.

## Register Here

Register locator/reference field names such as repository_path, artifact_uri, output_ref, source_reference, and changed_file_paths.

## Do Not Register Here

- entity names/ids;
- timestamps;
- status values;
- classification axes;
- numeric metrics;
- free-text descriptions;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

# Repo

## Meaning

`repo` names canonical trading repository identifiers.

## Register Here

Register repository entries with payload as repository name and optional path as repository root.

## Do Not Register Here

- standalone path rows;
- concept definitions;
- packages/modules that are not repositories;
- component runtime names;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

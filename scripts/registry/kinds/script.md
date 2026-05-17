# Script

## Meaning

`script` names stable callable commands or automation exports.

## Register Here

Register executable entrypoints under scripts/ or stable helper exports intended for automation.

## Do Not Register Here

- directories;
- ordinary source files;
- generated files;
- test scripts;
- fixtures;
- runtime artifact paths;
- generic terms;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

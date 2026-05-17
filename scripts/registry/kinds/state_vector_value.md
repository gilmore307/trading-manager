# State Vector Value

## Meaning

`state_vector_value` names reviewed core scalar score tokens in accepted model state/context/vector contracts.

## Register Here

Register compact numeric score families such as 1_*, 2_*, 3_*, 5_*, 6_*, 7_*, 8_*, and 9_* when they are cross-repository model contract tokens.

## Do Not Register Here

- storage-only columns;
- request parameters;
- ids;
- timestamps;
- paths;
- free-text fields;
- block/group names;
- diagnostics;
- routing enums;
- research payloads;
- model ids;
- scripts;
- templates;
- execution instructions;

## Row Rules

- `payload` must hold the stable registered value, not prose.
- `path` is optional and should point only to the canonical locator when the row names a locateable thing.
- `applies_to` should name the first real consumer scope when the value is not global.
- Use the narrowest valid kind; if another kind is more precise, use that kind instead.
- Never register secrets, generated blobs, local scratch files, or unreviewed experiment labels.

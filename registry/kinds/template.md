# Template

## Kind Boundary

Reusable checked-in template identifiers for task keys, receipts, source-scaffold files, and other stable template artifacts. Retired data-kind preview shapes should not be registered.

## Range

Register templates only when the row points to a durable template file or template generator surface that other repositories may reference.

Use `payload` for the workspace-relative template path or callable template export name. Use `path` for the canonical local checkout path when useful for automation/review.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- runtime artifact instances;
- live shared data files;
- helper functions, which belong in `script`;
- provider/source implementations, which belong in `data_source`;
- final saved data categories, which belong in `data_kind`.

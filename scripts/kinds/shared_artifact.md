# Shared Artifact

## Kind Boundary

Durable checked-in shared artifacts that are data/config assets rather than templates, scripts, terms, or final data-kind categories.

## Range

Register shared artifacts when multiple repositories intentionally consume one stable checked-in file and the registry needs to expose its canonical locator.

Use `payload` for the workspace-relative artifact path or stable artifact key. Use `path` for the canonical local checkout path when useful for automation/review.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- template files, which belong in `template`;
- runtime output instances;
- provider/source adapters, which belong in `data_source`;
- manager-facing deterministic feature output boundaries, which belong in `data_feature`;
- final saved dataset categories, which belong in `data_kind`;
- non-secret config defaults, which belong in `config`.

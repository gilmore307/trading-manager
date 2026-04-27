# Artifact Sync Policy

## Kind Boundary

Registered values allowed in `trading_registry.artifact_sync_policy`.

This policy tells reviewers whether a normal semantic edit to a registry row should trigger follow-up edits in concrete code, template, documentation, or other artifact files.

## Range

Use this kind only for the allowed artifact sync policy values used by the registry table.

Current policy meanings:

- `registry_only` — registry row edits normally do not require artifact follow-up when durable consumers use stable ids and the row is not merged, deleted, or semantically repurposed.
- `sync_artifact` — registry row edits must be followed by matching artifact updates before acceptance.
- `review_on_merge` — simple label edits may be registry-only, but merges, deletes, or semantic repurposing require downstream review before acceptance.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- payload formats;
- task lifecycle states;
- review, acceptance, test, maintenance, or docs status values;
- component-local migration states;
- free-form review notes.

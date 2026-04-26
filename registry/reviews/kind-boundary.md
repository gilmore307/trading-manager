# Registry Kind Boundary Review

## Purpose

This file evaluates whether the current registry kinds overlap and records the boundary rule to use when an entry could plausibly fit multiple kinds.

## Summary

The current kind set is acceptable, but several pairs are easy to confuse. Keep the current split because it preserves query convenience and validation clarity. Use the tie-breaker rules below instead of merging kinds prematurely.

## Pairwise Boundary Assessment

| Potential Overlap | Risk | Boundary Rule | Current Action |
|---|---|---|---|
| `field` vs status kinds | A status field such as `task_lifecycle_state` has both a field name and allowed values. | `field` registers the slot name; status kinds register allowed values for that slot. | Keep separate. |
| `path` column vs registry kind | Direct locators are needed for repos/scripts, but a separate kind splits one entity across rows. | Use nullable `path` column on the entity row; do not use `path` as a kind. | Keep as column only. |
| `config` vs `term` | Config keys can look like named concepts. | Use `config` for machine-consumed values; use `term` for human-facing definitions. | Keep separate. |
| `artifact_type` vs `output` | Artifact types and output templates can sound similar. | `artifact_type` classifies durable system artifacts; `output` names reusable output/template shapes. | Keep separate. |
| `manifest_type` vs `artifact_type` | Manifests can be stored as artifacts. | `manifest_type` classifies evidence documents; `artifact_type` classifies durable output payloads. | Keep separate. |
| `ready_signal_type` vs status kinds | Signals often contain readiness/status values. | `ready_signal_type` classifies the signal; status kinds classify allowed state values. | Keep separate. |
| `request_type` vs task lifecycle state | Requests initiate work; task states track lifecycle. | `request_type` classifies requested work; `task_lifecycle_state` tracks execution state. | Keep separate. |
| status kinds vs generic status | Many status kinds share values like `blocked` or `accepted`. | Keep separate status kinds when lifecycle semantics differ. Do not merge just because payload strings overlap. | Keep separate. |
| `term` vs every other kind | Any registered key may also need a definition. | `term` defines vocabulary; other kinds register machine-consumed values. Use `term` only when no machine-consumed registry kind fits. | Keep separate. |

## Recommendation

Keep the current kind set with the added contract type kinds. The apparent overlap is mostly semantic, not structural.

The most important rule is:

```text
field names go in `field`; allowed values go in the specific value kind.
```

The second most important rule is:

```text
entity locators go in the nullable `path` column; do not create `path` rows.
```

The third most important rule is:

```text
if code consumes it as a setting, use `config`; if humans consume it as a definition, use `term`.
```

## Watch List

Revisit the kind set if any of these happen:

- `output` starts carrying concrete trading artifact classes that should be `artifact_type`;
- scripts, repos, and configs start duplicating the same locator instead of using the entity row `path`;
- status vocabularies multiply beyond task/review/acceptance/test/maintenance/docs;
- component repositories start adding local registries because the central kind set is unclear.

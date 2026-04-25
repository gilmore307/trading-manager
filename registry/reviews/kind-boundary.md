# Registry Kind Boundary Review

## Purpose

This file evaluates whether the current registry kinds overlap and records the boundary rule to use when an entry could plausibly fit multiple kinds.

## Summary

The current kind set is acceptable, but several pairs are easy to confuse. Keep the current split because it preserves query convenience and validation clarity. Use the tie-breaker rules below instead of merging kinds prematurely.

## Pairwise Boundary Assessment

| Potential Overlap | Risk | Boundary Rule | Current Action |
|---|---|---|---|
| `field` vs status kinds | A status field such as `task_lifecycle_state` has both a field name and allowed values. | `field` registers the slot name; status kinds register allowed values for that slot. | Keep separate. |
| `repo` vs `path` | A repository has both a name and a root path. | `repo` registers the repository name; `path` registers filesystem locations. | Keep separate. |
| `path` vs `script` | A script locator is also a path. | `script` is for executable/source entrypoint locators; `path` is for general stable filesystem paths. | Keep separate. |
| `config` vs `path` | Some config values are paths. | Use `config` when the value is a tunable setting; use `path` when the path itself is the stable referenced object. | Keep separate; document intent in the entry note. |
| `config` vs `term` | Config keys can look like named concepts. | Use `config` for machine-consumed values; use `term` for human-facing definitions. | Keep separate. |
| `output` vs future artifact kinds | Outputs and artifacts can both name produced things. | `output` is for reusable output shapes/templates; future artifact kinds should name durable trading artifact classes or instances only if explicitly introduced. | Keep `output`; do not add artifact kinds until `docs/07_artifact.md` needs them. |
| status kinds vs generic status | Many status kinds share values like `blocked` or `accepted`. | Keep separate status kinds when lifecycle semantics differ. Do not merge just because payload strings overlap. | Keep separate. |
| `term` vs every other kind | Any registered key may also need a definition. | `term` defines vocabulary; other kinds register machine-consumed values. Use `term` only when no machine-consumed registry kind fits. | Keep separate. |

## Recommendation

Keep the current kind set. The apparent overlap is mostly semantic, not structural.

The most important rule is:

```text
field names go in `field`; allowed values go in the specific value kind.
```

The second most important rule is:

```text
if code consumes it as a setting, use `config`; if humans consume it as a definition, use `term`.
```

## Watch List

Revisit the kind set if any of these happen:

- `output` starts carrying concrete trading artifact classes;
- more than one script/path/config entry is created for the same value;
- status vocabularies multiply beyond task/review/acceptance/test/maintenance/docs;
- component repositories start adding local registries because the central kind set is unclear.

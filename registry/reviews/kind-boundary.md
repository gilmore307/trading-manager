# Registry Kind Boundary Review

## Purpose

This file evaluates whether the current registry kinds overlap and records the boundary rule to use when an entry could plausibly fit multiple kinds.

## Summary

The status-like kinds have been merged into one `status_value` kind because their structural role is identical: each row registers an allowed state/policy value. Other entity and classifier kinds remain separate where they represent materially different contracts.

## Pairwise Boundary Assessment

| Potential Overlap | Risk | Boundary Rule | Current Action |
|---|---|---|---|
| `field` vs `status_value` | A status field such as `task_lifecycle_state` has both a field name and allowed values. | `field` registers the slot name; `status_value` registers allowed values for that slot, with the slot/domain in `applies_to`. | Keep separate. |
| `field` vs `temporal_field` | Time/date field names are structurally fields, but their value-format contract must be stricter and never overlaps ordinary categorical/numeric/text fields. | Use `temporal_field` for date/time/datetime/timestamp/availability/effective-time slots; use `field` for non-temporal slots. | Split temporal fields. |
| `path` column vs registry kind | Direct locators are needed for repos/scripts, but a separate kind splits one entity across rows. | Use nullable `path` column on the entity row; do not use `path` as a kind. | Keep as column only. |
| `config` vs `term` | Config keys can look like named concepts. | Use `config` for machine-consumed values; use `term` for human-facing definitions. | Keep separate. |
| `artifact_type` vs `output` | Artifact types and output templates can sound similar. | `artifact_type` classifies durable system artifacts; `output` names reusable output/template shapes. | Keep separate. |
| `manifest_type` vs `artifact_type` | Manifests can be stored as artifacts. | `manifest_type` classifies evidence documents; `artifact_type` classifies durable output payloads. | Keep separate. |
| `ready_signal_type` vs `status_value` | Signals often contain readiness/status values. | `ready_signal_type` classifies the signal; `status_value` classifies allowed state/policy values. | Keep separate. |
| `request_type` vs `status_value` | Requests initiate work; task states track lifecycle. | `request_type` classifies requested work; `status_value` rows with `applies_to = task_lifecycle_state` track execution state values. | Keep separate. |
| prior status-specific kinds vs `status_value` | Many status domains share the same row structure and values like `blocked` or `accepted`. | Use one `status_value` kind and keep lifecycle/readiness/test/docs/etc. semantics in `applies_to` and key naming. | Merged. |
| `term` vs every other kind | Any registered key may also need a definition. | `term` defines vocabulary; other kinds register machine-consumed values. Use `term` only when no machine-consumed registry kind fits. | Keep separate. |

## Recommendation

Keep the current kind set after merging status-specific kinds into `status_value`. The remaining apparent overlap is mostly semantic, not structural.

The most important rule is:

```text
non-temporal field names go in `field`; date/time field names go in `temporal_field`; allowed status/policy values go in `status_value` with the domain in `applies_to`.
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
- status values lose clear domain scoping in `applies_to`;
- temporal fields start using locale-dependent date formats instead of ISO-8601 semantics;
- component repositories start adding local registries because the central kind set is unclear.

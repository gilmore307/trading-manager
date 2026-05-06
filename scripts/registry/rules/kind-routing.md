# Registry Kind Routing Rules

## Purpose

This file owns cross-kind tie-breakers for `trading_registry.kind`. Use it when a proposed row could plausibly fit multiple kinds.

Per-kind scope/range/rejection definitions still live in `../kinds/<kind>.md`.

## Field-Like Kinds

Use the narrowest true field kind:

| Row role | Registry kind |
|---|---|
| Non-identity, non-temporal, non-classification scalar or structured slot | `field` |
| Entity id, symbol, name, title, headline, or other identity/name slot | `identity_field` |
| File path, URL, source reference, output reference, repository path, or artifact locator slot | `path_field` |
| Date, time, datetime, timestamp, availability, effective-time, or window-bound slot | `temporal_field` |
| Categorical/type/status/scope/tags semantic axis slot | `classification_field` |
| Free-text summary, explanation, caveat, diagnostic, error, or note slot | `text_field` |
| Request/task parameter object or parameter collection slot | `parameter_field` |

Rules:

- `field` is the fallback only after identity/path/temporal/classification/text/parameter meanings are ruled out.
- Allowed values for a status or policy axis are `status_value`; the slot that carries those values is `classification_field`.
- Every field-like row must populate `applies_to` with its first concrete table, template, receipt, or contract scope.

## Status And Type Values

- Use `status_value` for allowed state or policy values such as lifecycle, review, test, docs, maintenance, acceptance, readiness, and artifact-sync values.
- Put the status domain in `applies_to`, for example `task_lifecycle_status` or `artifact_sync_policy_type`.
- Do not create one registry kind per status domain.
- Use `state_vector_value` only for reviewed value tokens inside an accepted model state-vector contract, such as state-vector block/group names, score-family names, diagnostic payload names, window values, or enum values.
- Prefix every `state_vector_value.payload` with the owning model number, for example `3_market_state_features`; reject bare vector payloads that hide model ownership.
- Keep the physical table column that carries a state vector in the narrowest field-like kind; keep the semantic token inside the vector as `state_vector_value`.
- Use `artifact_type`, `manifest_type`, `ready_signal_type`, `request_type`, and `payload_format` only for values whose structural role is materially different from a generic status/policy value.

## Data Production Kinds

| Row role | Registry kind |
|---|---|
| Current provider/source owner identity | `provider` |
| Implemented provider/API/web/file feed connector | `data_feed` |
| Feed-level record family, raw input, endpoint family, transient evidence, or entitlement-gated category | `feed_capability` |
| Control-plane-facing runnable source output | `data_source` |
| Deterministic model-facing feature output produced by `trading-data` | `data_feature` |
| Accepted final saved data shape with a current storage contract | `data_kind` |

Rules:

- Provider documentation URLs belong on `provider`, `feed_capability`, or glossary `term` rows, not on `data_kind` rows unless the URL is the accepted final data-shape contract.
- Feed connectors and source outputs are not final data shapes by default.
- Model outputs, evaluation tables, promotion tables, and diagnostics belong to model-owned contracts unless separately registered as shared terms/fields/statuses.

## Locators And Config

- Direct locators belong in the nullable `path` column on the entity row. Do not add a `path` kind.
- Use `config` for machine-consumed non-secret config values and secret aliases.
- Use `term` for human-facing definitions when no machine-consumed kind fits.
- Never store raw secrets in SQL payloads, paths, notes, or generated CSV snapshots.

## Scripts, Templates, And Artifacts

- Use `script` for stable callable helper or automation surfaces, not ordinary source files, packages, test helpers, generated snapshots, or broad directories.
- Use `template` for reusable checked-in templates or template generator surfaces.
- Use `shared_artifact` for durable checked-in shared data/config assets that are not templates.
- Use `artifact_type` for allowed artifact classification values, not artifact instances.

## Review Trigger

If a proposed row does not fit these rules cleanly, update this file or the relevant `../kinds/<kind>.md` before adding SQL rows. Do not encode unresolved ambiguity only in `note`.

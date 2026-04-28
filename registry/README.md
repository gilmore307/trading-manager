# Registry

`registry/` is the canonical home for trading-wide registered names and shared vocabulary.

For the docs-level registry guide, see [`docs/08_registry.md`](../docs/08_registry.md).

The registry has two layers:

1. **Kind boundary docs** — one Markdown file per `kind` under `registry/kinds/`, defining what that kind means and what belongs in it.
2. **SQL-backed entries** — concrete registered items live in the active `trading_registry` table and its migrations under `registry/sql/schema_migrations/`.

`registry/kinds/*.md` files must not list concrete active rows. They define scope, range, and rejection boundaries only.

The SQL `trading_registry.kind` constraint and `registry/kinds/*.md` files must stay aligned. Tests compare those two sources directly.

`registry/current.csv` is the GitHub-visible snapshot of the active SQL table. It is generated from the database and must not be edited by hand.

Registry `id` is the stable automation reference. Registry `key` is a human-readable output/display label and may be renamed by reviewed migration. Helper APIs must not take key as input.

## SQL Entry Schema

Concrete entries use this shape:

| Field | Meaning |
|---|---|
| `id` | Stable random identifier. |
| `kind` | Registry kind. Must match one kind boundary file. |
| `key` | Human-readable symbolic label for display/review; renameable and not a durable automation input. |
| `payload_format` | Payload value format. See Payload Formats below. |
| `payload` | Registered value or file reference. |
| `path` | Optional direct locator/address for entries that point to concrete entities, including repo roots, script sources, source-secret JSON files, and provider documentation URLs. |
| `applies_to` | Optional for most kinds; required for `field` entries. Records the table, file, contract, template, or data shape where the field is used. |
| `artifact_sync_policy` | Review policy for whether registry row edits require follow-up changes in concrete code, template, docs, or other artifact files. See Artifact Sync Policy below. |
| `note` | Human-readable review note. |
| `created_at` | Database insertion timestamp. |
| `updated_at` | Database update timestamp. |


## Payload Formats

`payload_format` describes how to interpret the string stored in `payload`. Legal values are first-class registry entries with `kind = payload_format`; `registry/current.csv` is the reviewable snapshot.

The SQL `trading_registry_payload_format_check` constraint and the registered `payload_format` rows must stay aligned. Tests compare those two sources directly.

Use the narrowest registered format that matches the value. Keep `text` as the fallback only when no narrower registered format applies.

Do not add a new payload format when an existing one precisely describes the value. If a new format is needed, update the SQL constraint, add the `payload_format` row, update registry docs/tests, and regenerate `registry/current.csv` in one reviewed change.

## Artifact Sync Policy

`artifact_sync_policy` tells reviewers whether a normal semantic edit to a registry row requires follow-up changes in concrete artifacts.

Allowed values are registered as rows with `kind = status_value` and `applies_to = artifact_sync_policy_type`; they must stay aligned with the SQL `trading_registry_artifact_sync_policy_check` constraint.

Use:

- `registry_only` when registry row edits normally do not require artifact follow-up because durable consumers use stable ids and the row is not merged, deleted, or semantically repurposed.
- `sync_artifact` when registry edits must be propagated into code, templates, docs, or other artifact files before acceptance.
- `review_on_merge` when simple label edits may be registry-only, but merges, deletes, or semantic repurposing require downstream review.

Key-only label renames can still be safe for id-based consumers, but payload/name changes for fields that appear in plain-text templates or code must be synchronized with those artifacts.

## CSV Snapshot

The current registry table is exported to:

```text
registry/current.csv
```

Run this after SQL registry updates:

```bash
scripts/apply_registry_migrations.py
```

For export only:

```bash
scripts/apply_registry_migrations.py --export-only
```

This export-only command is registered as `REGISTRY_EXPORT_CURRENT_CSV_HELPER`.

The migration helper applies pending SQL migrations and exports `registry/current.csv` after every non-dry-run migration pass unless `--no-export` is used.

## Kind Files

- [`artifact_type`](./kinds/artifact_type.md) — Registered artifact type values used to classify durable outputs produced and consumed across trading repositories.
- [`classification_field`](./kinds/classification_field.md) — Canonical categorical/classification field names whose values assign rows to semantic classes.
- [`config`](./kinds/config.md) — Non-secret configuration keys and secret-alias references. Payloads may contain secret aliases but must never contain secret values.
- [`data_bundle`](./kinds/data_bundle.md) — Manager-facing runnable bundle keys accepted for task routing and receipts.
- [`data_source`](./kinds/data_source.md) — Implemented source-interface or source-adapter identifiers.
- [`data_kind`](./kinds/data_kind.md) — Canonical final saved or durable derived data-shape identifiers with accepted templates.
- [`field`](./kinds/field.md) — Canonical shared non-identity, non-temporal, non-classification field names used in task records, receipts, manifests, requests, review artifacts, maintenance outputs, and helper-facing schemas.
- [`identity_field`](./kinds/identity_field.md) — Canonical field names whose values identify or name entities, artifacts, sources, instruments, tasks, reports, or rows.
- [`manifest_type`](./kinds/manifest_type.md) — Registered manifest type values used to classify run evidence documents across trading repositories.
- [`path_field`](./kinds/path_field.md) — Canonical field names whose values locate or reference artifacts, files, URLs, repository paths, source references, or output references.
- [`payload_format`](./kinds/payload_format.md) — Registered values allowed in the `trading_registry.payload_format` column.
- [`ready_signal_type`](./kinds/ready_signal_type.md) — Registered ready-signal type values used to classify downstream consumability signals.
- [`repo`](./kinds/repo.md) — Canonical repository identifiers. Use for repository names, not filesystem paths.
- [`request_type`](./kinds/request_type.md) — Registered request type values used to classify cross-repository work requests.
- [`script`](./kinds/script.md) — Canonical callable helper or automation export records, with source locators in `path`.
- [`shared_artifact`](./kinds/shared_artifact.md) — Durable checked-in shared artifacts that are not templates, scripts, terms, or data-kind categories.
- [`source_capability`](./kinds/source_capability.md) — Source-level record families, endpoint families, raw inputs, transient evidence, or entitlement-gated provider capabilities that are not final saved data shapes.
- [`status_value`](./kinds/status_value.md) — Registered status or policy values; `applies_to` identifies the value domain such as `task_lifecycle_status`, `review_status`, `acceptance_status`, `test_status`, or `artifact_sync_policy_type`.
- [`template`](./kinds/template.md) — Reusable checked-in template identifiers.
- [`temporal_field`](./kinds/temporal_field.md) — Canonical date/time/datetime field names with ISO-8601 value semantics.
- [`term`](./kinds/term.md) — Approved shared terminology and definitions.

## Review Files

`registry/reviews/` holds review notes and boundary assessments, not kind source-of-truth files.

## Rules

- Do not define the same kind in multiple Markdown files.
- Do not store concrete active row lists in `registry/kinds/*.md`.
- Do not store secrets. Store source-level secret aliases only; one provider/source should normally map to one JSON secret file.
- Do not mix component-local implementation details into trading-wide registry entries.
- New fields, identity fields, path fields, temporal fields, classification fields, statuses, payload formats, config keys, data bundles, data sources, data kinds, templates, shared artifacts, script locators, and stable names should be registered in SQL before component repositories depend on them.
- `registry/current.csv` must be regenerated after SQL registry changes.
- `registry/current.csv` is a generated snapshot; do not hand-edit it.
- Test scripts must stay out of registry `script` rows and be documented in their test-directory README.
- Registered registry item lookup APIs must take registry ids as input, not keys.
- `script` rows are for stable callable helper/automation exports, not package constants or test scripts.
- Repository rows should include the repository name in `payload` and the local checkout root in `path` when the checkout path is an approved shared fact.
- Use the `path` column for direct locators/addresses on entity-like entries such as repos, scripts, source-secret JSON config rows, and provider documentation term rows.
- Every `field` entry must populate `applies_to`; use semicolon-separated scopes when a field belongs to multiple tables, files, contracts, templates, or data shapes. Source secret JSON field names use `applies_to=source_secret_json`.
- Do not reintroduce `path` as a registry kind; path is a nullable column.
- If a new kind is needed, add its `registry/kinds/<kind>.md` boundary file, update the SQL kind check, update registry tests/docs, and regenerate `registry/current.csv` in the same reviewed change.

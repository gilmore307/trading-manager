# Registry

`registry/` is the canonical home for trading-wide registered names and shared vocabulary.

The registry has two layers:

1. **Kind boundary docs** — one Markdown file per `kind`, defining what that kind means and what belongs in it.
2. **SQL-backed entries** — concrete registered items live in the active `trading_registry` table and its migrations under `registry/sql/schema_migrations/`.

Markdown kind files must not list concrete active rows. They define scope, range, and rejection boundaries only.

`registry/current.csv` is the GitHub-visible snapshot of the active SQL table. It is generated from the database and must not be edited by hand.

Registry `id` is the stable automation reference. Registry `key` is a human-readable output/display label and may be renamed by reviewed migration. Helper APIs must not take key as input.

## SQL Entry Schema

Concrete entries use this shape:

| Field | Meaning |
|---|---|
| `id` | Stable random identifier. |
| `kind` | Registry kind. Must match one kind boundary file. |
| `key` | Stable symbolic key. |
| `payload_format` | Payload storage format, currently `text` or `file`. |
| `payload` | Registered value or file reference. |
| `path` | Optional direct locator/address for entries that point to concrete entities. |
| `applies_to` | Optional for most kinds; required for `field` entries. Records the table, file, contract, template, or data shape where the field is used. |
| `note` | Human-readable review note. |
| `created_at` | Database insertion timestamp. |
| `updated_at` | Database update timestamp. |

## CSV Snapshot

The current registry table is exported to:

```text
registry/current.csv
```

Run this after SQL registry updates:

```bash
registry/sql/apply-migrations.py
```

For export only:

```bash
registry/sql/apply-migrations.py --export-only
```

The migration helper applies pending SQL migrations and exports `registry/current.csv` after every non-dry-run migration pass unless `--no-export` is used.

## Kind Files

- [`acceptance_outcome`](./acceptance_outcome.md) — Default acceptance outcome values for OpenClaw acceptance records.
- [`artifact_type`](./artifact_type.md) — Registered artifact type values used to classify durable outputs produced and consumed across trading repositories.
- [`config`](./config.md) — Non-secret configuration keys and secret-alias references. Payloads may contain secret aliases but must never contain secret values.
- [`docs_status`](./docs_status.md) — Default documentation alignment status values.
- [`field`](./field.md) — Canonical shared field names used in task records, receipts, manifests, requests, review artifacts, maintenance outputs, and helper-facing schemas.
- [`maintenance_status`](./maintenance_status.md) — Default maintenance pass status values.
- [`manifest_type`](./manifest_type.md) — Registered manifest type values used to classify run evidence documents across trading repositories.
- [`output`](./output.md) — Reusable output/template identifiers. Use only for stable output shapes that multiple workflows may reference.
- [`ready_signal_type`](./ready_signal_type.md) — Registered ready-signal type values used to classify downstream consumability signals.
- [`repo`](./repo.md) — Canonical repository identifiers. Use for repository names, not filesystem paths.
- [`request_type`](./request_type.md) — Registered request type values used to classify cross-repository work requests.
- [`review_readiness`](./review_readiness.md) — Default review-readiness values for completion receipts and review queues.
- [`script`](./script.md) — Canonical helper or automation method/entrypoint records, with source locators in `path`.
- [`task_lifecycle_state`](./task_lifecycle_state.md) — Default task lifecycle state values for planning and execution records.
- [`term`](./term.md) — Approved shared terminology and definitions.
- [`test_status`](./test_status.md) — Default test/verification status values.

## Rules

- Do not define the same kind in multiple Markdown files.
- Do not store concrete active row lists in Markdown kind files.
- Do not store secrets. Store secret aliases only.
- Do not mix component-local implementation details into trading-wide registry entries.
- New fields, statuses, config keys, script locators, and stable names should be registered in SQL before component repositories depend on them.
- `registry/current.csv` must be regenerated after SQL registry changes.
- `registry/current.csv` is a generated snapshot; do not hand-edit it.
- Registered helper APIs must take registry ids as input, not keys.
- Use the `path` column for direct locators/addresses on entity-like entries such as repos and scripts.
- Every `field` entry must populate `applies_to`; use semicolon-separated scopes when a field belongs to multiple tables, files, contracts, templates, or data shapes.
- Do not reintroduce `path` as a registry kind; path is a nullable column.
- If a new kind is needed, add its Markdown boundary file, update helper kind lists, update the SQL kind check, and regenerate `registry/current.csv` in the same reviewed change.

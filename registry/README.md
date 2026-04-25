# Registry

`registry/` is the canonical home for trading-wide registered names and shared vocabulary.

The registry uses one Markdown file per `kind`. Each file owns exactly one registration kind and must define the kind boundary before listing entries.

## Schema

Each entry has:

| Field | Meaning |
|---|---|
| `id` | Stable random identifier. |
| `kind` | Registry kind. Must match the owning file. |
| `key` | Stable symbolic key. |
| `payload_format` | Payload storage format, currently `text` or `file`. |
| `payload` | Registered value or file reference. |
| `note` | Human-readable review note. |
| `source_migration` | Historical migration file this entry came from during universal-catalog migration. |

## Kind Files

- [`acceptance_outcome`](./acceptance_outcome.md) — Default acceptance outcome values for OpenClaw acceptance records.
- [`config`](./config.md) — Non-secret configuration keys and secret-alias references. Payloads may contain secret aliases but must never contain secret values.
- [`docs_status`](./docs_status.md) — Default documentation alignment status values.
- [`field`](./field.md) — Canonical shared field names used in task records, receipts, manifests, requests, review artifacts, maintenance outputs, and helper-facing schemas.
- [`maintenance_status`](./maintenance_status.md) — Default maintenance pass status values.
- [`output`](./output.md) — Reusable output/template identifiers. Use only for stable output shapes that multiple workflows may reference.
- [`path`](./path.md) — Canonical filesystem path values. Use only for stable reviewed paths that should be referenced consistently.
- [`repo`](./repo.md) — Canonical repository identifiers. Use for repository names, not filesystem paths.
- [`review_readiness`](./review_readiness.md) — Default review-readiness values for completion receipts and review queues.
- [`script`](./script.md) — Canonical source-file locators for helper or automation entry points.
- [`task_lifecycle_state`](./task_lifecycle_state.md) — Default task lifecycle state values for planning and execution records.
- [`term`](./term.md) — Approved shared terminology and definitions.
- [`test_status`](./test_status.md) — Default test/verification status values.

## Rules

- Do not define the same kind in multiple files.
- Do not store secrets. Store secret aliases only.
- Do not mix component-local implementation details into trading-wide registry entries.
- New fields, statuses, config keys, script locators, and stable names should be registered here before component repositories depend on them.

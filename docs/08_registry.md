# Registry

## Purpose

`trading-main` owns the trading registry: the shared registration system for trading-wide names, vocabulary, status values, repository identifiers, helper surfaces, and other stable values that multiple repositories may consume.

The earlier docs stay project-wide:

- `00_scope.md` through `06_memory.md` describe the whole trading platform repository and its governance.
- This file describes the `registry/` platform function specifically.

The registry exists to prevent each component repository from inventing incompatible names, fields, statuses, helper references, or repository identifiers.

## What The Registry Owns

The registry owns trading-wide facts that need one canonical name or identifier, including:

- repository identifiers;
- shared field names;
- lifecycle, review, acceptance, test, maintenance, and docs status vocabularies;
- artifact, manifest, ready-signal, and request type values;
- shared terminology;
- non-secret config keys and secret-alias references;
- public helper or automation method entries;
- generated GitHub-visible registry snapshots.

The registry does not own component-local implementation details, runtime data, generated trading artifacts, credentials, secrets, notebooks, logs, or provider-specific private configuration.

## Directory Layout

```text
registry/
  README.md                 Registry index and operating rules.
  current.csv               Generated SQL snapshot for GitHub visibility.
  kinds/                    One Markdown boundary file per registry kind.
  reviews/                  Review notes and boundary assessments.
  sql/                      Migration tooling and SQL schema migrations.
```

Supporting helper code lives outside `registry/`:

```text
helpers/trading_registry/    Shared Python registry reader and secret-resolution helpers.
```

## Entry Model

Concrete registry entries live in the SQL-backed `trading_registry` table and are exported to `registry/current.csv`.

| Field | Registry Meaning |
|---|---|
| `id` | Stable automation reference. Use this in durable automation. |
| `kind` | Registry category. Must have a matching `registry/kinds/<kind>.md` boundary file. |
| `key` | Human-readable symbolic label. Useful for display and review, but renameable. |
| `payload_format` | Payload value format. See Payload Formats below. |
| `payload` | Registered value or file reference. |
| `path` | Optional direct locator/address for entity-like rows such as repos or scripts. |
| `applies_to` | Usage scope. Required for `field` rows. |
| `note` | Human-readable review note. |
| `created_at` / `updated_at` | SQL-managed timestamps exported in the snapshot. |

The key rule is:

```text
id is the stable input; key is display output.
```

Helper APIs must not take registry `key` as input.


## Payload Formats

`payload_format` describes how to interpret the string stored in `payload`. It is not a registry kind. Use the narrowest accepted format that matches the value.

Accepted formats:

| Format | Meaning |
|---|---|
| `text` | General text fallback when no narrower format applies. |
| `file` | File reference stored in `payload`. |
| `json` | JSON-encoded value. |
| `integer` | Base-10 integer encoded as text. |
| `decimal` | Decimal numeric value encoded as text. |
| `boolean` | Boolean encoded as `true` or `false`. |
| `iso_date` | ISO 8601 calendar date, such as `2026-04-25`. |
| `iso_time` | ISO 8601 time-of-day value. |
| `iso_datetime` | ISO 8601 date-time value; include timezone when the value is absolute. |
| `iso_duration` | ISO 8601 duration value. |
| `timezone` | IANA timezone name. |
| `secret_alias` | Local secret alias reference, never the secret value. |
| `repo_name` | Git repository name. |
| `field_name` | Canonical field name. |
| `status_value` | Registered status/outcome value. |
| `command` | Command or command fragment. |
| `python_symbol` | Python import/member symbol. |

Do not add a new payload format when an existing one precisely describes the value. If a new format is needed, update the SQL check constraint, Python helper validation, registry docs, and generated CSV in one reviewed change.

## Kind Boundaries

Kind source-of-truth files live under `registry/kinds/`.

Each kind file defines:

- what the kind means;
- what belongs in the kind;
- what should be rejected or re-scoped.

Kind files must not list concrete active rows. Concrete rows belong in SQL migrations and `registry/current.csv`.

`registry/reviews/` is for review records and boundary assessments, not normative kind definitions.

## SQL And Snapshot Workflow

Use SQL migrations for concrete registry entries.

Normal registry update flow:

1. Classify the entry's kind.
2. If the kind boundary is unclear, update or review `registry/kinds/<kind>.md` first.
3. Add a SQL migration under `registry/sql/schema_migrations/`.
4. Run the migration helper:

   ```bash
   registry/sql/apply-migrations.py
   ```

5. Confirm `registry/current.csv` was regenerated.
6. Run a dry-run check:

   ```bash
   registry/sql/apply-migrations.py --dry-run
   ```

7. Run registry helper tests when helper behavior or registry reader behavior changed:

   ```bash
   /root/projects/trading-main/.venv/bin/python -m unittest discover -s helpers/tests
   ```

For snapshot export only:

```bash
registry/sql/apply-migrations.py --export-only
```

That export command is registered as `REGISTRY_EXPORT_CURRENT_CSV_HELPER`.

Do not hand-edit `registry/current.csv`.

## Helper Surface

The registered official Python id-only lookup and secret helper surface is:

- `RegistryReader.get_key_by_id(id)`
- `RegistryReader.get_payload_by_id(id)`
- `RegistryReader.get_path_by_id(id)`
- `SecretResolver.load_secret_text_by_config_id(config_id)`

Payload-format validation utilities live in the Python package to mirror the SQL constraint. They are not registered registry `script` rows.

The CSV export maintenance helper is separate from lookup helpers:

- `registry/sql/apply-migrations.py --export-only`

Registry `script` rows identify approved helper/automation surfaces and source locators; they do not by themselves define package installation or cross-repository runtime dependency contracts.

Key-input helper APIs are intentionally not part of the public helper surface. Component runtime code should consume the Python helper package (`trading_registry`). If a human needs key-based debugging, use direct SQL inspection instead of adding key-input helpers.

## Registration Rules

- Register shared names before component repositories depend on them.
- New shared fields discovered in component work must be registered here before other repositories depend on them.
- New global helper surfaces and reusable templates must be recorded in `trading-main` and linked to registry entries when they expose stable automation names.
- Prefer existing entries over inventing near-duplicates.
- Use stable `id` values for automation and durable references.
- Treat `key` values as renameable labels.
- Store secret aliases only; never store secret values.
- Use nullable `path` for direct locators; do not create a `path` kind.
- Every `field` row must have non-empty `applies_to`.
- Repository rows should carry repository name in `payload` and local checkout root in `path` when the checkout path is an approved shared fact.
- Script rows should represent stable callable helper/automation exports, not every helper source file or package constant.
- Record review rationale in `note` or `registry/reviews/` when a boundary choice could be confused.

## Acceptance Checklist

A registry change is acceptable when:

- SQL migrations own concrete row changes;
- `registry/current.csv` is regenerated from SQL;
- kind boundary docs remain row-free;
- no secrets are added;
- no component-local implementation details are centralized;
- registry item lookup and secret helper APIs remain id-input only;
- every `field` row has non-empty `applies_to`;
- migration dry-run reports no pending migrations after application;
- relevant helper tests pass when helper behavior changed.

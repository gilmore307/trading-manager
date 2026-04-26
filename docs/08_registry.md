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
| `path` | Optional direct locator/address for entity-like rows such as repos, scripts, or provider documentation pages. |
| `applies_to` | Usage scope. Required for `field` rows. |
| `note` | Human-readable review note. |
| `created_at` / `updated_at` | SQL-managed timestamps exported in the snapshot. |

The key rule is:

```text
id is the stable input; key is display output.
```

Helper APIs must not take registry `key` as input.


## Payload Formats

`payload_format` describes how to interpret the string stored in `payload`. Legal values are first-class registry entries with `kind = payload_format`; `registry/current.csv` is the reviewable snapshot.

The SQL `trading_registry_payload_format_check` constraint and the registered `payload_format` rows must stay aligned. Tests compare those two sources directly.

Use the narrowest registered format that matches the value. Keep `text` as the fallback only when no narrower registered format applies.

Do not add a new payload format when an existing one precisely describes the value. If a new format is needed, update the SQL constraint, add the `payload_format` row, update registry docs/tests, and regenerate `registry/current.csv` in one reviewed change.

## Kind Boundaries

Kind source-of-truth files live under `registry/kinds/`.

Each kind file defines:

- what the kind means;
- what belongs in the kind;
- what should be rejected or re-scoped.

Kind files must not list concrete active rows. Concrete rows belong in SQL migrations and `registry/current.csv`.

The SQL `trading_registry.kind` constraint and `registry/kinds/*.md` files must stay aligned. Tests compare those two sources directly.

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
- `SecretResolver.load_secret_text_by_config_id(config_id, field_name=None)`

Registry kind and payload-format vocabularies are checked against SQL constraints by tests, not by public runtime helper exports.

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

Source-level secret JSON config rows should use `payload_format=secret_alias`, store the source alias in `payload`, and may mirror the JSON file path in `path`. Provider `term` rows may use `path` for the canonical public documentation URL. JSON field names such as `api_key`, `secret_key`, `passphrase`, `endpoint`, and `pat` are registered as `field` rows with `applies_to=source_secret_json`.
- Use nullable `path` for direct locators such as local repo roots, helper source files, source-secret JSON files, and provider documentation URLs; do not create a `path` kind.
- Every `field` row must have non-empty `applies_to`.
- Repository rows should carry repository name in `payload` and local checkout root in `path` when the checkout path is an approved shared fact.
- Script rows should represent stable callable helper/automation exports, not every helper source file, package constant, or test script.
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
- relevant helper tests pass when helper behavior changed;
- test scripts remain out of registry `script` rows and are documented in their test-directory README.

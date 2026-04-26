# Templates

## Purpose

`trading-main` owns reusable trading-wide templates for drafting contracts, tasks, prompts, and other repeatable project surfaces.

The earlier docs stay project-wide:

- `00_scope.md` through `06_memory.md` describe the whole trading platform repository and its governance.
- This file describes the `templates/` platform function specifically.

Templates exist to keep drafting consistent without mistaking drafts for accepted contracts or concrete registry entries.

## What Templates Own

Templates may own reusable drafting surfaces for:

- artifact contracts;
- manifest contracts;
- ready-signal contracts;
- request contracts;
- task prompts;
- implementation prompts;
- review/acceptance receipt shapes;
- other trading-wide repeatable documentation or workflow surfaces.

Templates must not own:

- concrete active registry rows;
- normative kind definitions;
- generated artifacts;
- component runtime implementations;
- secrets or credentials;
- component-local task state unless explicitly labeled as an example.

## Directory Layout

```text
templates/
  README.md                 Template boundary summary.
  contracts/                Contract drafting templates.
  data_tasks/               Historical data task drafting templates.
```

Current contract drafting templates:

- `templates/contracts/artifact.md`
- `templates/contracts/manifest.md`
- `templates/contracts/ready_signal.md`
- `templates/contracts/request.md`

Current data task drafting templates:

- `templates/data_tasks/task_key.json`
- `templates/data_tasks/bundle_readme.md`
- `templates/data_tasks/pipeline.py`
- `templates/data_tasks/fetch_spec.md`
- `templates/data_tasks/clean_spec.md`
- `templates/data_tasks/save_spec.md`
- `templates/data_tasks/completion_receipt.json`
- `templates/data_tasks/fixture_policy.md`

## Draft vs Contract

Templates are drafting surfaces. They are not automatically binding contracts.

A template becomes part of an accepted contract only when the relevant project docs, registry entries, and acceptance criteria identify the concrete contract shape.

Rules:

- Keep templates reusable across repositories unless explicitly labeled component-specific.
- Label examples as examples.
- Do not hide unresolved schema choices inside template prose.
- Promote stable type values through SQL registry migrations when a contract type becomes shared vocabulary.
- Keep concrete active entries in SQL registry migrations, not in templates.

## Contract Template Flow

Normal flow for a shared contract shape:

1. Draft the shape in `templates/contracts/`.
2. Identify fields, type values, and status values that need registry entries.
3. Register shared names through SQL migrations under `registry/sql/schema_migrations/`.
4. Regenerate `registry/current.csv`.
5. Update workflow and acceptance docs if the contract becomes binding.
6. Route implementation work to the owning component repositories.

## Data Task Template Flow

Normal flow for a historical data acquisition bundle:

1. Start from `templates/data_tasks/task_key.json` for manager/data handoff shape.
2. Start from `templates/data_tasks/bundle_readme.md` for the bundle boundary.
3. Use `pipeline.py` as the default single-file implementation shape with internal `fetch`, `clean`, `save`, and `write_receipt` step functions.
4. Fill API-specific requirements using `fetch_spec.md`, `clean_spec.md`, `save_spec.md`, and `fixture_policy.md`.
5. Use `completion_receipt.json` as the draft evidence shape for development receipts under `TRADING_DATA_DEVELOPMENT_STORAGE_ROOT`.
5. Register any stable field/type/status names before implementation treats them as contracts.

These data task templates are draft surfaces. They do not by themselves create accepted task-key, receipt, storage, or API schemas. Keep task keys and receipts minimal: only include fields used by manager, runner, bundle execution, storage output, or receipt evidence. Provider documentation URLs and similar lookup metadata belong in registry/provider docs, not runtime task keys.

## Recording Duty

When component work creates a reusable template shape, move or copy the reusable version into `trading-main/templates/` before other repositories depend on it.

If a template introduces shared fields, statuses, artifact types, manifest types, ready-signal types, request types, or config keys, route those names through the SQL registry and regenerate `registry/current.csv`.

Temporary template fields must be called out during review instead of silently becoming local conventions.

## Acceptance Checklist

A template change is acceptable when:

- the template remains reusable or clearly labels its component-specific scope;
- the template does not claim to be a concrete accepted contract unless docs and registry entries support that;
- examples are clearly non-binding unless explicitly accepted;
- new shared field/type/status vocabulary is routed to the registry;
- templates stay under `templates/`, not under `docs/` or `registry/`;
- unresolved schema choices are recorded as gaps rather than hidden assumptions.

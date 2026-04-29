# Templates

## Purpose

`trading-main` owns reusable trading-wide templates for drafting contracts, tasks, prompts, and other repeatable project surfaces.

The earlier docs stay project-wide:

- `00_scope.md` through `06_memory.md` describe the whole trading platform repository and its governance.
- This file describes the `storage/templates/` platform function specifically.

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
storage/templates/
  README.md                 Template boundary summary.
  contracts/                Contract drafting templates.
  data_tasks/               Parked historical data task drafts; not active contracts.
  project_development/      Parked project-development slot drafts; not active contracts.
```

Current contract drafting templates:

- `storage/templates/contracts/artifact.md`
- `storage/templates/contracts/manifest.md`
- `storage/templates/contracts/ready_signal.md`
- `storage/templates/contracts/request.md`

Current parked project-development drafts:

- `storage/templates/project_development/acceptance_receipt_slots.md`
- `storage/templates/project_development/completion_receipt_slots.md`
- `storage/templates/project_development/execution_key_slots.md`
- `storage/templates/project_development/maintenance_output_slots.md`
- `storage/templates/project_development/task_register_slots.md`

These project-development slot drafts are not active registry contracts. They were moved out of the OpenClaw skill so they can be reviewed one by one before any future registration.

Parked data task drafting templates:

- `storage/templates/data_tasks/task_key.json`
- `storage/templates/data_tasks/source_readme.md`
- `storage/templates/data_tasks/pipeline.py`
- `storage/templates/data_tasks/fetch_spec.md`
- `storage/templates/data_tasks/clean_spec.md`
- `storage/templates/data_tasks/save_spec.md`
- `storage/templates/data_tasks/completion_receipt.json`
- `storage/templates/data_tasks/fixture_policy.md`

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

1. Draft the shape in `storage/templates/contracts/`.
2. Identify fields, type values, and status values that need registry entries.
3. Register shared names through SQL migrations under `registry/sql/schema_migrations/`.
4. Regenerate `registry/current.csv`.
5. Update workflow and acceptance docs if the contract becomes binding.
6. Route implementation work to the owning component repositories.

## Data Task Template Status

The files under `storage/templates/data_tasks/` are parked drafts, not active registry contracts. The task architecture will be redesigned after model and source contracts settle.

Do not register `data_task_key`, `data_task_completion_receipt`, or `data_task_completion_receipt_run` fields from these drafts until the task architecture is reviewed and accepted one contract at a time.

## Recording Duty

When component work creates a reusable template shape, move or copy the reusable version into `trading-main/storage/templates/` before other repositories depend on it.

If a template introduces shared fields, statuses, artifact types, manifest types, ready-signal types, request types, or config keys, route those names through the SQL registry and regenerate `registry/current.csv`.

Temporary template fields must be called out during review instead of silently becoming local conventions.

## Acceptance Checklist

A template change is acceptable when:

- the template remains reusable or clearly labels its component-specific scope;
- the template does not claim to be a concrete accepted contract unless docs and registry entries support that;
- examples are clearly non-binding unless explicitly accepted;
- new shared field/type/status vocabulary is routed to the registry;
- templates stay under `storage/templates/`, not under `docs/` or `registry/`;
- unresolved schema choices are recorded as gaps rather than hidden assumptions.

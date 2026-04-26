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
```

Current contract drafting templates:

- `templates/contracts/artifact.md`
- `templates/contracts/manifest.md`
- `templates/contracts/ready_signal.md`
- `templates/contracts/request.md`

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

## Acceptance Checklist

A template change is acceptable when:

- the template remains reusable or clearly labels its component-specific scope;
- the template does not claim to be a concrete accepted contract unless docs and registry entries support that;
- examples are clearly non-binding unless explicitly accepted;
- new shared field/type/status vocabulary is routed to the registry;
- templates stay under `templates/`, not under `docs/` or `registry/`;
- unresolved schema choices are recorded as gaps rather than hidden assumptions.

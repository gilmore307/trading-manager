# Acceptance

## Acceptance Summary

`trading-main` is accepted when it provides a coherent, reviewable, documentation-only system layer for the trading project.

Acceptance for this repository focuses on:

- docs spine completeness;
- repository boundary clarity;
- cross-repository workflow clarity;
- shared contract clarity;
- registry clarity;
- template clarity;
- shared helper boundary clarity;
- absence of component runtime code, data, artifacts, and secrets;
- evidence that component repositories can use these documents without conflicting interpretations.

This repository does not accept trading runtime behavior. Runtime behavior is accepted in the relevant component repository.

## Acceptance Rules

### For `trading-main`

A change to `trading-main` can be accepted only if:

- the docs spine remains complete;
- `README.md` accurately describes the repository boundary;
- repository purpose remains system docs, contracts, registries, templates, shared helpers, and shared environment anchoring;
- `.venv/`, if present, is ignored by Git and treated as local runtime infrastructure;
- no component runtime trading source code is introduced;
- no market data, generated artifacts, logs, notebooks, credentials, or secrets are introduced;
- trading-wide statuses and registrable fields are maintained under `registry/` rather than duplicated elsewhere;
- component-specific scope, implementation details, and task state are routed to the owning component repository.

### For documentation-only changes

Documentation-only changes are acceptable when they:

- update the narrowest authoritative file;
- avoid duplicating durable facts across neighboring docs;
- preserve the separation between scope, context, workflow, acceptance, task, decision, memory, and contracts;
- mark unresolved items as explicit open gaps rather than pretending they are settled;
- add or update decisions when a choice changes architecture, naming, contract shape, acceptance criteria, or repository boundaries;
- keep examples clearly labeled as examples when they are not binding contracts;
- keep diagrams aligned with the surrounding prose;
- do not silently change component responsibilities without recording a decision.

### For contract changes

Contract changes are acceptable when they:

- define the contract's purpose and ownership;
- specify required and optional fields where applicable;
- identify producing and consuming repositories;
- describe lifecycle expectations;
- describe compatibility expectations;
- reference `trading-main/registry/` for registered fields, identifiers, and status vocabularies;
- include enough examples for implementation without making examples the only definition;
- document migration or compatibility impact when changing an existing contract;
- update affected workflow and decision docs when contract shape changes.

### For registry and template changes

Registry and template changes are acceptable when they:

- keep trading-wide registered names in the SQL-backed `trading_registry`;
- keep kind boundary/range rules in `registry/<kind>.md`;
- regenerate `registry/current.csv` after SQL registry changes;
- avoid scattering field/status definitions across docs;
- document compatibility impact when renaming or removing registered fields;
- keep templates reusable and not tied to one component unless clearly labeled;
- update affected docs and contracts when registry meaning changes.

### For shared helper changes

Shared helper changes are acceptable when they:

- provide reusable trading infrastructure rather than component-specific runtime behavior;
- include or declare appropriate tests once helper behavior exists;
- avoid embedding secrets, provider credentials, or local-only paths;
- keep public interfaces explicit and stable enough for component repositories;
- update templates or contracts when helper behavior encodes a shared convention.

### For shared environment changes

Shared environment changes are acceptable when they:

- keep the environment anchored at the documented location unless a decision changes it;
- keep `.venv/` out of Git;
- document runtime version and package-management expectations;
- document how component repositories should use the shared environment;
- document exceptions explicitly instead of allowing silent local environment drift;
- avoid storing secrets, credentials, dependency caches, or generated artifacts as repository content.

## Verification Commands

Because `trading-main` is primarily documentation and contracts, required verification is inspection-based until tooling exists.

Current required checks before acceptance:

```bash
git status --short
find docs -maxdepth 1 -type f | sort
find . -maxdepth 2 -type f | sort
```

Manual review must confirm:

- required docs files exist;
- contract drafting templates live under `templates/contracts/`, not `docs/`;
- registry kind Markdown files do not list concrete active rows;
- `registry/current.csv` is present and generated from SQL when registry entries changed;
- `.venv/` is not tracked;
- no source-code directories were introduced;
- no data/artifact/log/notebook directories were introduced unless explicitly documented as ignored local infrastructure;
- no obvious secrets are present;
- docs do not duplicate canonical facts unnecessarily;
- open gaps are tracked in `docs/04_task.md`.

Future tooling may add markdown linting, link checks, schema validation, catalog validation, and contract example validation. New tooling should extend the acceptance path rather than replacing manual boundary review.

## Required Review Evidence

OpenClaw acceptance requires:

- list of changed files;
- summary of boundary impact;
- summary of contract impact;
- summary of registry impact;
- confirmation that no runtime code/data/secrets were added;
- confirmation that `.venv/` is ignored if present;
- confirmation that component-specific details were not incorrectly centralized;
- decision record references for architectural or contract-changing choices;
- explicit unresolved gaps routed to `docs/04_task.md`.

## Rejection Reasons

A change must be rejected or returned for revision if it:

- adds component runtime trading code to `trading-main`;
- adds market data, generated artifacts, logs, notebooks, or research outputs to `trading-main`;
- adds secrets or credentials;
- tracks `.venv/` contents in Git;
- duplicates registry status vocabularies or registrable fields as a competing source of truth outside `registry/`;
- moves component-local implementation details into global docs;
- changes repository responsibilities without a decision record;
- changes cross-repository contracts without updating affected docs;
- leaves dependent contract fields ambiguous;
- uses examples as the only contract definition;
- allows market-state discovery to depend on strategy returns or strategy performance;
- allows execution to bypass external promotion;
- allows dashboard to recompute upstream source-of-truth outputs;
- claims acceptance without evidence.

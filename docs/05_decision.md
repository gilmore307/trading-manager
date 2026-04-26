# Decision

## D001 - Use a multi-repository trading architecture

Date: 2026-04-25

### Decision

The trading system will be split across multiple repositories rather than implemented as one monorepo.

### Rationale

The system has distinct control-plane, data, storage, strategy, model, execution, and dashboard responsibilities. Separate repositories help preserve ownership boundaries and acceptance clarity.

## D002 - Create `trading-main` as the system-level documentation and contract repository

Date: 2026-04-25

### Decision

`trading-main` will own global documentation, cross-repository workflow, shared contracts, and system-level decisions.

### Rationale

A global docs/contracts repository prevents component repositories from inventing incompatible interfaces and drifting in responsibility.

## D003 - Keep component-local details in component repositories

Date: 2026-04-25

### Decision

`trading-main` records system-level collaboration only. Component-local scope, workflow, acceptance, task state, and implementation detail belong in each component repository's docs spine.

### Rationale

Global docs should coordinate repositories without replacing their local project boundaries.

## D004 - Use `trading-data` rather than `trading-fetcher`

Date: 2026-04-25

### Decision

The data upstream repository will be named `trading-data`.

### Rationale

The repository is responsible for data source access, fetching, normalization, storage writes, and ready signals. `trading-fetcher` is too narrow.

## D005 - Market-state discovery must be market-only

Date: 2026-04-25

### Decision

Market-state discovery must not use strategy returns or strategy performance as input. Strategy results may only be attached after market states already exist.

### Rationale

Using strategy performance to define market states would contaminate downstream claims that states can guide strategy selection.

## D006 - `trading-main` anchors the shared trading development environment

Date: 2026-04-25

### Decision

`trading-main` will anchor the shared local development environment at:

```text
/root/projects/trading-main/.venv
```

The `.venv/` directory is local runtime infrastructure and must be ignored by Git.

### Rationale

This gives all trading repositories a single predictable environment location while keeping implementation code, generated artifacts, and component-specific logic out of `trading-main`.

### Consequences

- Component repositories should use `/root/projects/trading-main/.venv`.
- Component repositories should not create independent virtual environments unless an exception is documented.
- `trading-main` remains documentation/contract-only except for the local gitignored `.venv/` anchor.
- The `.venv/` directory is not reviewable repository content.

## D007 - Expand `trading-main` into the trading platform main repository

Date: 2026-04-25

### Context

The server's project work is centered on the trading system. The owner wants one canonical home for global planning, field registration, templates, and shared helpers instead of splitting small shared pieces across additional repositories.

### Decision

`trading-main` will own:

- trading-wide planning and architecture;
- trading-wide registered fields, identifiers, statuses, artifact types, request types, and related names;
- trading-wide templates;
- shared helper code used by component repositories;
- the shared local `.venv/` anchor.

### Rationale

Keeping these shared assets together reduces repository sprawl and gives the trading system one obvious coordination point.

### Consequences

- `trading-main` is no longer docs-only.
- Component runtime implementations still remain outside `trading-main`.
- Shared helpers in `trading-main` must stay generic and reusable.
- Trading-specific registry responsibilities move from `universal-catalog` into `trading-main/registry/`.

## D008 - Registry Markdown defines kind boundaries while SQL owns concrete entries

Date: 2026-04-25

### Context

The initial registry migration converted active SQL rows into Markdown tables. That made the kind files too noisy and blurred their purpose.

### Decision

`registry/kinds/<kind>.md` files define kind boundaries, ranges, and rejection rules only. Concrete registered items live in the SQL-backed `trading_registry` table and append-only migrations under `registry/sql/schema_migrations/`.

### Rationale

Kind documentation should explain what belongs in a registry kind. Concrete entries need database semantics, uniqueness, migration history, and helper access rather than large Markdown inventories.

### Consequences

- Do not list active registry rows in Markdown kind files.
- Add one Markdown file per formal kind.
- Add or update SQL migrations for concrete item changes.
- If a new kind is introduced, update both the SQL kind constraint and the Markdown boundary file.

## D009 - Export the active SQL registry as a CSV snapshot

Date: 2026-04-25

### Context

Concrete registry entries belong in SQL for queryability, constraints, and helper access. The owner still wants GitHub to show the current registry contents without requiring a database query.

### Decision

After SQL registry updates, `registry/sql/apply-migrations.py` exports the active `trading_registry` table to:

```text
registry/current.csv
```

The CSV is a generated snapshot and must not be edited by hand.

### Rationale

This keeps SQL as the source of truth while preserving a simple GitHub-readable view of the active registry.

### Consequences

- Registry data changes require SQL migration review.
- Registry CSV changes are expected after SQL registry changes.
- Markdown kind files remain boundary documentation only.

## D010 - Keep current registry kinds with documented tie-breakers

Date: 2026-04-25

### Context

Some registry kinds are easy to confuse, especially `field` vs status-value kinds, entity locators vs entity rows, and `config` vs `term`.

### Decision

Keep the current kind set and document tie-breaker rules in `registry/reviews/kind-boundary.md`.

### Rationale

The apparent overlap is mostly semantic. Keeping specific kinds improves query convenience and validation clarity.

### Consequences

- Use `field` for slot names and specific status kinds for allowed values.
- Use `repo` for repository names and `path` for filesystem locations.
- Use `script` for source-file entrypoint locators.
- Use `config` for machine-consumed settings and `term` for human-facing definitions.

## D011 - Keep contract drafting templates out of the docs spine

Date: 2026-04-25

### Context

The initial artifact, manifest, ready-signal, and request contract placeholders were drafting surfaces for future contract shapes, not stable system docs.

### Decision

Move artifact, manifest, ready-signal, and request drafting surfaces to `templates/contracts/`. Keep `docs/` focused on project governance plus any approved project-specific guide docs.

### Rationale

The docs spine should contain ratified project context and governance. Drafting templates belong under `templates/`. Registry type vocabularies belong under `registry/`; registry operating guidance may live in an approved docs guide.

### Consequences

- Do not add numbered docs beyond `06_memory.md` for reusable drafting templates.
- Use `templates/contracts/` for reusable contract drafting surfaces.
- Use `registry/kinds/*_type.md` and SQL migrations for registered type vocabularies.
- Use `docs/08_registry.md` for the approved `trading-main` registry operating guide.

## D012 - Remove canceled-project registry entries

Date: 2026-04-25

### Context

The trading project is now the central project boundary for this server. Old project-specific registry entries should not remain active when they are no longer useful.

### Decision

Remove active registry entries for canceled project-specific defaults from the trading registry.

### Rationale

The registry should reflect active trading-system vocabulary and shared infrastructure. Stale project-specific defaults create noise and increase the chance of reusing invalid names.

### Consequences

- GitHub history remains the restore path if old entries are ever needed again.
- Active `registry/current.csv` should contain only current registry entries.
- Future registry entries should be trading-relevant or generally useful to the active server project boundary.

## D013 - Registry path is a nullable column, not a kind

Date: 2026-04-25

### Context

Some registry entries point to concrete entities such as repositories or helper source files. A separate `path` kind forced entries like repository name and repository root path to be split across two rows.

### Decision

Use a nullable `path` column on `trading_registry` for direct locators and addresses. Remove `path` as a registry kind.

### Rationale

This keeps the stable entity entry and its direct locator together. For example, `TRADING_MAIN_REPO` can carry both `payload = trading-main` and `path = /root/projects/trading-main`.

### Consequences

- Entity-like entries may populate `path`.
- Non-entity entries leave `path` empty.
- Do not reintroduce a `path` kind.
- Script entries use `payload` for a meaningful helper/export description and `path` for the source locator.

## D014 - Registry automation dereferences stable ids by default

Date: 2026-04-25

### Context

Registry `key` values are human-readable labels and may be renamed by reviewed migrations. Registry `id` values are the stable automation references.

### Decision

Automation should dereference registry entries by `id`. Registered helper APIs must not take registry key as input; key is an output/display label only.

### Rationale

Using ids avoids silent breakage when a key is renamed for clarity.

### Consequences

- Prefer id-input helpers such as `getKeyById`, `getPayloadById`, `getPathById`, and `loadSecretTextByConfigId`.
- Do not add key-input helper APIs to the public helper surface.
- Documentation should warn against storing keys as stable automation references.

## D015 - Tailscale and SMB remain infrastructure terms

Date: 2026-04-25

### Context

Old project-specific entries were removed from the registry, but Tailscale and SMB remain relevant infrastructure concepts on this server.

### Decision

Keep `TAILSCALE` and `SMB` as active `term` entries. Do not restore canceled project-specific configuration entries for them.

### Rationale

The concepts are still useful as shared vocabulary, while stale project-specific defaults should stay out of the active registry.

### Consequences

- `TAILSCALE` and `SMB` are available as terms.
- Project-specific VPN/SMB defaults require fresh registry review before reintroduction.

## D016 - Field entries can record usage scope with `applies_to`

Date: 2026-04-25

### Context

Field entries need more than a canonical field name. During review, it is useful to know which table, file, contract, template, or data shape a field is used in.

### Decision

Add nullable `trading_registry.applies_to`. For `field` entries, use it to record the field's known usage/source scope.

### Rationale

This avoids overloading `note` and makes field usage visible in `registry/current.csv`.

### Consequences

- Known field usage should be recorded in `applies_to`.
- Empty `applies_to` means broad, unsettled, or not-yet-reviewed usage.
- `applies_to` is especially important for fields tied to SQL tables, file schemas, manifests, requests, signals, templates, or task receipts.

## D017 - Helper methods are registered method-level surfaces

Date: 2026-04-25

### Context

The shared registry helper surface should expose callable methods, not generic helper source files.

### Decision

Register callable helper methods as `script` entries with method names in `payload` and source locators in `path`.

### Rationale

The registry should expose reusable helper surfaces, not every helper source file. Method-level entries make the approved helper API visible in `registry/current.csv`.

### Consequences

- Registered helper rows represent callable methods.
- Helper methods use registry id as input.
- Multiple helper rows may share the same source path when they live in the same file.

## D018 - Secret resolver config lookup is id-first

Date: 2026-04-25

### Context

Secret resolver helpers previously used config keys, but registry keys are renameable labels.

### Decision

Expose `loadSecretTextByConfigId` as the id-first config secret helper.

### Rationale

Secrets are sensitive enough that automation should not depend on renameable registry keys.

### Consequences

- Prefer `loadSecretTextByConfigId`.
- Do not add key-input config secret helpers to the public helper surface.

## D019 - Every field registry entry requires `applies_to`

Date: 2026-04-25

### Context

The registry added `applies_to` for field usage/source scope. Leaving this blank for most field rows would make the column unreliable and force reviewers to infer where each field is used.

### Decision

Every `field` registry entry must have non-empty `applies_to`. Multiple usage surfaces are recorded as semicolon-separated scopes.

### Rationale

Field names are only useful if their valid usage surface is visible. A required `applies_to` column makes `registry/current.csv` useful for review and prevents broad, ambiguous field registrations.

### Consequences

- New `field` rows must include `applies_to` at registration time.
- A SQL check constraint rejects blank `applies_to` for `kind = field`.
- If a field belongs to multiple surfaces, use a semicolon-separated list.

## D020 - Registered helper surface is id-only

Date: 2026-04-25

### Context

Registry keys are useful labels but are renameable. The helper surface briefly included key-input helpers and both file-level and method-level script entries, which made the registry noisy and risked normalizing key-based automation.

### Decision

Register only four id-input helper methods as the public registry helper surface:

- `getKeyById`
- `getPayloadById`
- `getPathById`
- `loadSecretTextByConfigId`

Do not register key-input helper APIs. Do not register generic helper files as script entries when method-level helper entries are the intended public surface.

### Rationale

This keeps registry automation stable and simple: id in, approved value out. Key remains an output/display value, not an input contract.

### Consequences

- Key-based helper APIs are removed from the public helper surface.
- Script registry rows represent callable helper methods, not every helper source file.
- Human debugging can use SQL queries directly instead of key-input helper APIs.

## D021 - Current CSV export is a registered maintenance helper

Date: 2026-04-25

### Context

`registry/current.csv` is generated from SQL and should be refreshed after registry changes. The helper command itself should be discoverable from the registry.

### Decision

Register `registry/sql/apply-migrations.py --export-only` as `REGISTRY_EXPORT_CURRENT_CSV_HELPER`.

### Rationale

This keeps the CSV generation command visible without mixing it into the id-only lookup helper surface.

### Consequences

- Lookup helpers remain id-only.
- CSV generation is registered as a maintenance helper.
- The helper row points to `registry/sql/apply-migrations.py` and applies to `registry/current.csv`.

## D022 - All trading repositories are registry entries

Date: 2026-04-25

### Context

The trading platform is split across `trading-main` plus seven component repositories. Only registering `trading-main` would make cross-repository automation depend on unstated repository names and paths.

### Decision

Register every trading repository as a `repo` row with its stable registry id, repository key, repository name in `payload`, local checkout path in `path`, and component-repository context in `applies_to`.

### Rationale

The registry is the shared naming authority. Component repository names and checkout paths are shared infrastructure facts and should be discoverable through the registry instead of being re-invented in scripts or docs.

### Consequences

- All eight trading repositories are visible in `registry/current.csv`.
- Automation should use repo row ids to retrieve repository names and paths.
- Repository remotes are recorded in repo-row notes for review visibility.

## D023 - Registry kind boundaries live under registry/kinds

Date: 2026-04-25

### Context

Registry root was mixing generated snapshots, SQL tooling, review notes, and kind boundary files such as `acceptance_outcome.md`. Moving those files into `registry/reviews/` would confuse source-of-truth definitions with review artifacts.

### Decision

Move all registry kind boundary files into `registry/kinds/`. Keep `registry/reviews/` for review notes and boundary assessments only.

### Rationale

Kind files are normative boundary documentation. Review files are commentary and assessment records. Separating the directories keeps authority clear while reducing root clutter.

### Consequences

- New registry kinds must add `registry/kinds/<kind>.md`.
- `registry/reviews/` must not own kind source-of-truth files.
- `registry/README.md` remains the index for both SQL entries and kind boundary files.

## D024 - Add a registry-specific docs guide

Date: 2026-04-25

### Context

`trading-main` has grown from a docs-only coordination repository into the platform repository that also owns the SQL-backed registry, generated registry snapshot, registry helper surface, and registry maintenance workflow. Keeping all registry operating detail inside `00_scope.md` through `06_memory.md` would blur the project-wide docs with the registration subsystem guide.

### Decision

Keep `00_scope.md` through `06_memory.md` focused on the whole trading platform repository. Add `docs/08_registry.md` as the registry-specific operating guide.

### Rationale

The registry is now a first-class function of `trading-main`, not just a passing project context note. It needs a stable guide that explains ownership, entry model, SQL workflow, helper surface, and acceptance checks without overloading the general project docs.

### Consequences

- `docs/08_registry.md` is part of the accepted `trading-main` docs set.
- `00_scope.md` through `06_memory.md` remain project-wide platform docs.
- Registry kind source-of-truth files remain under `registry/kinds/`, not under `docs/`.
- Contract drafting templates remain under `templates/contracts/`, not under `docs/`.

## D025 - Split platform-function guides into helpers registry and templates

Date: 2026-04-25

### Context

`trading-main` owns three first-class platform functions beyond project-wide governance: shared helpers, the SQL-backed registry, and reusable templates. A single registry-specific guide did not capture the shape of the repository now that helpers and templates also have meaningful ownership boundaries.

### Decision

Use three numbered platform-function guide docs after the project-wide spine:

- `docs/07_helpers.md`
- `docs/08_registry.md`
- `docs/09_templates.md`

Keep `00_scope.md` through `06_memory.md` focused on the whole trading platform repository.

### Rationale

This mirrors the actual top-level structure of `trading-main` and gives each owned platform function a clear operating guide without crowding the project-wide docs.

### Consequences

- Helpers, registry, and templates each have a dedicated docs guide.
- Registry kind source-of-truth files still live under `registry/kinds/`.
- Template drafts still live under `templates/`.
- Helper code still lives under `helpers/`.

## D026 - Current JavaScript registry helpers are internal until packaging is accepted

Date: 2026-04-25

### Context

`helpers/registry/` contains tested JavaScript helper code for id-based registry lookups and config-id secret loading. However, `trading-main` does not yet define a formal helper package: there is no `package.json`, version policy, Node engine requirement, installation command, or cross-repository import contract. At the same time, the shared development environment is currently Python-centered through the `.venv` anchor.

### Decision

Treat the current JavaScript registry helpers as internal `trading-main` maintenance/test helpers, not as component-repository runtime dependencies. Before any component imports shared helper code at runtime, make an explicit distribution decision: Node package, Python package, or internal-only tool.

### Rationale

A tested helper file is not enough to be a stable package interface. Components need a clear language/runtime, versioning, installation, and import contract before depending on shared helper code.

### Consequences

- Component repositories must not directly import `helpers/registry/` as a runtime dependency yet.
- Registry `script` entries remain useful as approved helper/automation surface records, but they are not package contracts.
- If the helper becomes a Node package, add package metadata, Node engine, version policy, test command, install method, and import examples.
- If the helper becomes a Python package, align it with the shared `.venv` environment and define package metadata, tests, install method, and import examples.
- If the helper stays internal-only, keep docs explicit so component repositories do not rely on it.

## D027 - Shared environment baseline uses Python 3.12 pip and requirements.txt

Date: 2026-04-25

### Context

`trading-main` anchors the shared local trading development environment, but the runtime and dependency policy needed to be explicit before component repositories start adding dependencies.

### Decision

Use Python 3.12 in `/root/projects/trading-main/.venv` as the shared environment baseline. Use `python -m pip` as the installer and `requirements.txt` at the `trading-main` root as the reviewed dependency ledger.

### Rationale

This matches the current working environment and gives component repositories one simple, reviewable dependency path while the platform is still early.

### Consequences

- Component repositories should use `/root/projects/trading-main/.venv` by default.
- Dependencies must be added to `requirements.txt` through reviewed commits before installation.
- Component-local virtual environments require an explicit exception.
- The baseline can be revisited if packaging, GPU, or dependency isolation needs become real.

## D028 - Helper distribution strategy is internal-only until a package is accepted

Date: 2026-04-25

### Context

The existing JavaScript registry helpers are useful for `trading-main` maintenance and tests, but there is still no formal package metadata, version policy, runtime engine contract, installation command, or import contract for component repositories.

### Decision

The current helper distribution strategy is internal-only. Cross-repository runtime helper consumption is prohibited until a package strategy is accepted. If runtime helper consumption becomes necessary, prefer a Python package aligned with the shared `.venv` unless there is a concrete reason to package a Node helper.

### Rationale

This resolves the ambiguity now without forcing premature packaging. It also aligns future component runtime helpers with the current Python-centered environment unless a different runtime is justified.

### Consequences

- Components must not import loose files from `trading-main/helpers/`.
- Current JavaScript helper tests may continue to run inside `trading-main`.
- A future package decision must define runtime version, package metadata, version policy, install method, tests, and import/call examples.

## D029 - Trading repositories remain private by default

Date: 2026-04-25

### Context

The initial GitHub repositories were created for private project work. Visibility changes can expose project structure, future provider choices, operational assumptions, or accidental sensitive material.

### Decision

Keep all trading repositories private by default. Do not change repository visibility without explicit owner approval and a brief pre-change review for secrets, generated artifacts, credentials, and local operational assumptions.

### Rationale

Private-by-default avoids accidental disclosure while the platform is still forming. A deliberate visibility review is cheap compared with exposing sensitive or unstable project material.

### Consequences

- Visibility changes are external/public actions and require explicit approval.
- Before public release, review tracked files for secrets, generated data, local paths, and incomplete boundary docs.
- GitHub history remains the restore path; no separate docs archive is needed for visibility policy.

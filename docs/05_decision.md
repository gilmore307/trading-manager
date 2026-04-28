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

After SQL registry updates, `scripts/apply_registry_migrations.py` exports the active `trading_registry` table to:

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

Move artifact, manifest, ready-signal, and request drafting surfaces to `storage/templates/contracts/`. Keep `docs/` focused on project governance plus any approved project-specific guide docs.

### Rationale

The docs spine should contain ratified project context and governance. Drafting templates belong under `storage/templates/`. Registry type vocabularies belong under `registry/`; registry operating guidance may live in an approved docs guide.

### Consequences

- Do not add numbered docs beyond `06_memory.md` for reusable drafting templates.
- Use `storage/templates/contracts/` for reusable contract drafting surfaces.
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

- Prefer id-input helpers such as `RegistryReader.get_key_by_id`, `RegistryReader.get_payload_by_id`, `RegistryReader.get_path_by_id`, and `SecretResolver.load_secret_text_by_config_id`.
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

The shared registry helper surface should expose stable method or constant exports, not generic helper source files.

### Decision

Register stable callable helper exports as `script` entries with the exported name in `payload` and source locators in `path`. Constants and passive vocabularies should stay in docs, SQL constraints, or package internals unless a dedicated registry contract is accepted.

### Rationale

The registry should expose reusable callable helper surfaces, not every helper source file or package constant. Export-level entries make the approved helper API visible in `registry/current.csv`.

### Consequences

- Registered helper rows represent stable callable helper exports.
- Registry item lookup and secret helper methods use registry id as input.
- Multiple helper rows may share the same source path when they live in the same file.

## D018 - Secret resolver config lookup is id-first

Date: 2026-04-25

### Context

Secret resolver helpers previously used config keys, but registry keys are renameable labels.

### Decision

Expose `SecretResolver.load_secret_text_by_config_id` as the id-first config secret helper in the official Python runtime helper surface. It resolves source-level JSON secret aliases and may return either raw JSON text or a named JSON string field.

### Rationale

Secrets are sensitive enough that automation should not depend on renameable registry keys.

### Consequences

- Prefer `SecretResolver.load_secret_text_by_config_id(config_id, field_name=None)` for source-level secret JSON.
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

For registry item lookup and secret resolution, register only four id-input helper methods in the public registry helper surface. Earlier camelCase helper names were superseded by the official Python helper surface in D030:

- `RegistryReader.get_key_by_id`
- `RegistryReader.get_payload_by_id`
- `RegistryReader.get_path_by_id`
- `SecretResolver.load_secret_text_by_config_id`

Do not register key-input helper APIs. Do not register generic helper files as script entries when export-level helper entries are the intended public surface.

### Rationale

This keeps registry automation stable and simple: id in, approved value out. Key remains an output/display value, not an input contract.

### Consequences

- Key-based helper APIs are removed from the public helper surface.
- Script registry rows represent stable helper exports, not every helper source file.
- Human debugging can use SQL queries directly instead of key-input helper APIs.

## D021 - Current CSV export is a registered maintenance helper

Date: 2026-04-25

### Context

`registry/current.csv` is generated from SQL and should be refreshed after registry changes. The helper command itself should be discoverable from the registry.

### Decision

Register `scripts/apply_registry_migrations.py --export-only` as `REGISTRY_EXPORT_CURRENT_CSV_HELPER`.

### Rationale

This keeps the CSV generation command visible without mixing it into the id-only lookup helper surface.

### Consequences

- Lookup helpers remain id-only.
- CSV generation is registered as a maintenance helper.
- The helper row points to `scripts/apply_registry_migrations.py` and applies to `registry/current.csv`.

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
- Contract drafting templates remain under `storage/templates/contracts/`, not under `docs/`.

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
- Template drafts still live under `storage/templates/`.
- Helper code still lives under `src/`.

## D026 - Loose helper files are not package contracts

Date: 2026-04-25

### Context

`src/` can contain tested helper code before it is safe for component repositories to consume that code at runtime. A helper file alone does not define package metadata, version policy, runtime version, installation method, or import/call examples.

### Decision

Component repositories must not depend on loose helper files from `trading-main/src/`. Cross-repository runtime helper consumption requires an accepted package strategy.

### Rationale

A tested helper file is not enough to be a stable package interface. Components need a clear language/runtime, versioning, installation, and import contract before depending on shared helper code.

### Consequences

- Helper implementation and package readiness are separate acceptance concerns.
- Registry `script` entries remain useful as approved helper/automation surface records, but they are not package contracts.
- Packaged helpers must define runtime version, package metadata, version policy, install method, tests, and import/call examples.

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

## D028 - Runtime helper distribution uses the Python package

Date: 2026-04-25

### Context

Trading component repositories are expected to use Python through the shared `.venv` environment. Registry helper lookups are simple runtime infrastructure and should not require a separate helper runtime.

### Decision

Use the Python package rooted at `src/trading_registry/` as the cross-repository runtime helper distribution strategy. Component repositories should consume the installed `trading_registry` package rather than loose source files.

### Rationale

This aligns helper consumption with the shared environment and gives component repositories a normal Python import path.

### Consequences

- Components should import from `trading_registry` after installing `trading-main` editable into the shared environment.
- Loose files under `trading-main/src/` are not runtime dependency contracts.
- New runtime helpers should normally be added to the Python helper package with tests and docs.

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

## D030 - Official registry helper runtime surface is Python

Date: 2026-04-25

### Context

Future trading component repositories are expected to use Python through the shared `.venv` environment. Registry helper calls should be available through a normal Python import path.

### Decision

Make the official cross-repository registry helper runtime surface a Python package. Package metadata lives in root `pyproject.toml`, source lives under `src/trading_registry/`, and the install path is editable installation into `/root/projects/trading-main/.venv`.

### Rationale

Python aligns with the shared environment and avoids adding another runtime dependency for component repositories.

### Consequences

- Component repositories should import `trading_registry` from the Python package after the shared environment installs `trading-main` editable.
- Registry script rows point to the Python helper method surfaces and source files.
- Python helper package changes must include `unittest` coverage and update helper docs.

## D031 - Registry helpers are Python-only

Date: 2026-04-25

### Context

After the official Python registry helper package was added, keeping a parallel non-Python registry helper implementation would create drift and make future reviewers wonder which helper surface was authoritative.

### Decision

Remove the older non-Python registry helper implementation and keep registry helper implementation Python-only.

### Rationale

One implementation is easier to test, document, package, and consume. Since component repositories will use Python, the Python package is the correct single runtime surface.

### Consequences

- `src/trading_registry/` is the only registry helper implementation.
- The registry helper test command is `PYTHONPATH=src python3 -m unittest discover -s tests`.
- Registry script rows remain pointed at Python helper methods and source files.

## D032 - Registry payload_format records value format

Date: 2026-04-25

### Context

The registry initially allowed only `text` and `file` payload formats, so every active row used `text` even when the payload had a narrower interpretation such as repository name, field name, status value, secret alias, command, Python symbol, or timezone. Future contracts will also need date/time formats.

### Decision

Expand `payload_format` into an explicit payload value-format marker. Keep `text` as a fallback, but use narrower formats when they apply. Add date/time-capable formats such as `iso_date`, `iso_time`, `iso_datetime`, and `iso_duration`.

### Rationale

A more precise payload format makes registry review and automation safer without adding separate columns for every scalar type. The payload remains stored as text, while `payload_format` describes how consumers should interpret it.

### Consequences

- Current rows are backfilled to narrower formats where obvious: `field_name`, `status_value`, `repo_name`, `timezone`, `secret_alias`, `command`, and `python_symbol`.
- Payload-format values should be registered as registry rows, not hidden only in helper code or SQL constraints.
- Future rows should use the narrowest registered payload format.
- New payload formats require SQL constraint, `kind=payload_format` row, docs/tests, and CSV updates in the same reviewed change.

## D033 - Payload formats are registered vocabulary rows

Date: 2026-04-25

### Context

After expanding `payload_format`, the legal values were constrained in SQL and mirrored by Python package validation helpers. That made the vocabulary less reviewable than other shared names and put passive validation helpers in the runtime helper surface without a real component-consumer need.

### Decision

Register every legal `payload_format` value as a concrete row with `kind = payload_format`. Keep SQL constraint values and registered rows aligned. Do not expose `is_payload_format`, `assert_payload_format`, or `PAYLOAD_FORMATS` from the runtime helper package; tests may inspect SQL and CSV directly.

### Rationale

Legal registry vocabulary belongs in the registry. Runtime helpers should stay focused on id-based registry lookup and secret resolution instead of exporting passive vocabulary constants.

### Consequences

- `payload_format` is now a registry kind with a boundary file.
- Legal payload-format values are visible in `registry/current.csv`.
- The Python package no longer exports payload-format validator helpers.
- Tests compare registered payload-format rows with the SQL check constraint.

## D034 - Registry kind vocabulary is not a runtime helper export

Date: 2026-04-25

### Context

After moving payload-format vocabulary out of runtime helper exports, the Python package still exposed `REGISTRY_KINDS`, `is_registry_kind`, and `assert_registry_kind`. That repeated the same passive-vocabulary problem in a different file.

### Decision

Remove registry kind vocabulary validators from the runtime helper package. Treat legal registry kinds as a schema and registry-docs boundary: the SQL kind constraint and `registry/kinds/*.md` files must stay aligned, and tests enforce that alignment.

### Rationale

Runtime helpers should expose behavior needed by component consumers, not passive copies of registry/schema vocabulary. Keeping the vocabulary in SQL and boundary docs avoids drift and makes review happen in the registry surfaces.

### Consequences

- `src/trading_registry/registry_types.py` is removed.
- The Python package no longer exports `REGISTRY_KINDS`, `is_registry_kind`, or `assert_registry_kind`.
- `RegistryReader.list_items_by_kind` only validates that kind input is non-empty; SQL/current-registry tests own legal-kind alignment.
- Tests compare the latest SQL kind constraint with `registry/kinds/*.md` and ensure current rows use constrained kinds.

## D035 - Test scripts are documented locally, not registered

Date: 2026-04-25

### Context

The registry `script` kind is for stable callable helper or automation exports. Test scripts are verification assets, and registering them would blur the difference between public automation surfaces and local test coverage.

### Decision

Do not register test scripts as registry `script` rows. Each test directory owns a README inventory that lists every first-party test script and explains what it verifies.

### Rationale

A local test inventory keeps coverage discoverable without polluting the registry with non-runtime verification files. The registry stays focused on shared names and stable callable surfaces.

### Consequences

- `tests/README.md` inventories each helper test script.
- Tests enforce that first-party `tests/test_*.py` scripts are documented and absent from registry `script` rows.
- New or renamed test scripts require the owning tests README to be updated in the same change.

## D036 - Source secrets use one JSON file per source

Date: 2026-04-26

### Context

OKX credentials were initially split into separate aliases/files for API key, secret key, and passphrase. The user clarified that source credentials should not be scattered: one source should use one JSON secret file, and the helper should own parsing named fields.

### Decision

Use one JSON secret file per source/provider under `/root/secrets/<source>.json`. Registry config rows should point to the source-level alias, such as `okx` or `github`, and may mirror the JSON file path in `path`. Register reusable JSON key names, such as `api_key`, `secret_key`, `passphrase`, `endpoint`, `allowed_ip_address`, `api_key_remark_name`, and `pat`, as `field` rows with `applies_to=source_secret_json`.

### Rationale

A source-level JSON file keeps related credentials together, prevents config-row sprawl, and gives the resolver one consistent parsing model for OKX, GitHub, and future providers.

### Consequences

- Replace split OKX credential config rows with `OKX_SECRET_ALIAS`.
- Add `GITHUB_SECRET_ALIAS` for the GitHub source-level JSON file.
- `SecretResolver.load_secret_text_by_config_id(config_id, field_name=None)` returns raw JSON text or one named string field.
- Credential metadata that belongs to the source credential, such as allowlisted IP and key remark/name, stays in the source JSON rather than separate config rows.
- Secret values remain outside Git and outside registry rows.

## D037 - OKX credential metadata lives in the source JSON

Date: 2026-04-26

### Context

After consolidating OKX credentials into one source-level JSON file, the allowlisted IP address and API key remark/name were still separate config rows because they are non-secret. The user clarified that they are still part of the OKX credential bundle and should live in the same source JSON.

### Decision

Move OKX `allowed_ip_address` and `api_key_remark_name` into `/root/secrets/okx.json`. Remove standalone registry config rows for `OKX_ALLOWED_IP_ADDRESS` and `OKX_API_KEY_REMARK_NAME`. Register the JSON key names as source-secret fields.

### Rationale

The registry should expose one source-level alias for OKX, not split credential metadata across multiple config rows. One source JSON keeps the complete API-key bundle together while preserving the no-secret-values-in-Git rule.

### Consequences

- `OKX_SECRET_ALIAS` remains the single OKX credential/config entry.
- JSON keys now include `api_key`, `secret_key`, `passphrase`, `allowed_ip_address`, and `api_key_remark_name`.
- `SOURCE_SECRET_ALLOWED_IP_ADDRESS` and `SOURCE_SECRET_API_KEY_REMARK_NAME` are registered field rows with `applies_to=source_secret_json`.

## D038 - Alpaca is a registered stock and ETF data provider config surface

Date: 2026-04-26

### Context

The user provided Alpaca paper API credentials and endpoint for acquiring stock and ETF bars, quotes, trades, and news. Source credentials now use one JSON file per source.

### Decision

Register Alpaca as a provider term and add `ALPACA_SECRET_ALIAS` pointing to source alias `alpaca` and `/root/secrets/alpaca.json`. Register `endpoint` as a reusable source-secret JSON field.

### Rationale

Alpaca is a data-source connector dependency for `trading-data`; credentials and endpoint should be available through the same source-level JSON secret pattern as OKX and GitHub.

### Consequences

- Alpaca JSON fields are `api_key`, `secret_key`, and `endpoint`.
- `trading-data` may plan an Alpaca source connector using `ALPACA_SECRET_ALIAS` once implementation begins.
- Default tests still must not require live Alpaca credentials or network calls.

## D039 - ThetaData is registered as options-data provider terminology only

Date: 2026-04-26

### Context

The user identified ThetaData as the intended options-data provider for chain timeline, quote, trade, OHLC, Greeks, and related options datasets. ThetaData credential handling is special: credentials must be stored in a `creds.txt` file beside `ThetaTerminalv3.jar`.

### Decision

Register ThetaData as provider terminology now, but do not create secret aliases or source connector paths yet. Defer `creds.txt` and ThetaTerminal JAR placement until the source connector boundary is designed.

### Rationale

ThetaData is relevant to the options data domain, but its runtime credential/JAR layout needs a deliberate local-source design rather than being forced into the generic source JSON pattern prematurely.

### Consequences

- `THETADATA` is registered as a `term` row.
- No ThetaData secret alias is registered yet.
- `trading-data` may document ThetaData as the intended options-data provider, with implementation blocked on connector/JAR/credential layout decisions.

## D040 - Economic data providers use source-level API key aliases

Date: 2026-04-26

### Context

The user provided API keys for FRED, Census, BEA, and BLS. These sources support macroeconomic, demographic, labor, and market-context data acquisition for `trading-data`.

### Decision

Register FRED, Census, BEA, and BLS as provider terms and source-level secret aliases. Store each key in `/root/secrets/<source>.json` using the registered JSON key `api_key`.

### Rationale

These providers fit the standard source-level JSON secret pattern and are data-source connector dependencies, not source code or registry secret values.

### Consequences

- Config aliases are `FRED_SECRET_ALIAS`, `CENSUS_SECRET_ALIAS`, `BEA_SECRET_ALIAS`, and `BLS_SECRET_ALIAS`.
- Source aliases are `fred`, `census`, `bea`, and `bls`.
- Default tests must not require live provider credentials or network calls.

## D041 - Provider term paths may hold official documentation URLs

Date: 2026-04-26

### Context

Provider documentation will be consulted frequently while implementing data-source connectors. The registry already has a nullable `path` column for direct locators, while source-secret config rows use `path` for local secret JSON files.

### Decision

Use provider `term` row `path` values for canonical public documentation URLs. Keep source-secret `config` row `path` values pointed at local `/root/secrets/<source>.json` files.

### Rationale

This preserves a clean locator split: provider rows point to public docs, and credential config rows point to local secret material.

### Consequences

- Provider documentation URLs are available through the registry.
- Secret alias rows remain safe and unambiguous for credential resolution.
- Component repos should treat provider documentation URLs as registry metadata, not credentials.

## D042 - U.S. Treasury Fiscal Data is an open provider term without a secret alias

Date: 2026-04-26

### Context

The user identified the U.S. Treasury Fiscal Data API documentation as a useful source for federal finance datasets and noted that it may not require an API key. The official documentation describes the API as open and not requiring a user account or token.

### Decision

Register U.S. Treasury Fiscal Data as provider terminology with its documentation URL in the provider term `path`. Do not create a source-secret alias unless future implementation discovers a credential requirement.

### Rationale

This keeps documentation discoverable through the registry while avoiding unnecessary secret/config rows for a public no-key API.

### Consequences

- Provider key is `US_TREASURY_FISCAL_DATA`.
- Registry path points to `https://fiscaldata.treasury.gov/api-documentation/`.
- Connector implementation must still document endpoint coverage, pagination, rate/usage behavior, and fixture policy before acceptance.

## D043 - Calendar and ETF holdings sources use official web sources

Date: 2026-04-26

### Context

The user identified three non-credential data-source needs: FOMC calendar, official macro release calendars, and ETF holdings constituents/weights. These are not all conventional API credential surfaces; some require web discovery and issuer-site sourcing.

### Decision

Register shared source terms for FOMC calendar, official macro release calendar discovery, and ETF issuer holdings. Use the official Federal Reserve FOMC calendar URL for `FOMC_CALENDAR`; use web search to locate current official agency macro-release calendars; use issuer websites or issuer-published holdings files as the source of truth for ETF holdings and weights.

### Rationale

These source-of-truth rules should be explicit before connector or scraper work begins, especially where no credentialed provider API is involved.

### Consequences

- Third-party macro calendars and ETF aggregators are not source of truth unless explicitly approved as secondary references.
- Connectors must preserve source URL, retrieval timestamp, and publication/effective date where available.
- Default tests must use fixtures or mocks, not live web calls.

## D044 - Data acquisition is manager-driven and historical-only

Date: 2026-04-26

### Context

The user clarified that current `trading-data` acquisition work concerns historical data. Realtime data and execution-time feeds belong to `trading-execution` later. Data tasks should be initiated by `trading-manager` and completed by `trading-data` with durable evidence in `trading-storage`.

### Decision

Register shared workflow terms for historical data acquisition, manager-issued data task key files, and data task completion receipts. Treat the exact schema and storage placement as pending cross-repository contract work; development receipts use local `storage/` before durable storage contracts exist.

### Rationale

The boundary keeps orchestration, data acquisition, storage, and execution responsibilities separate while preserving a named contract surface for implementation planning.

### Consequences

- `trading-data` remains historical-only for now.
- `trading-manager` owns task-key creation and lifecycle orchestration.
- Development-stage outputs and receipts use local `storage/`; `trading-storage` owns durable SQL output placement and completion receipt storage once schemas are accepted.
- Registry terms exist before component implementation depends on the names.

## D045 - Trading-data development outputs use local file storage before SQL

Date: 2026-04-26

### Context

The user clarified that during development, `trading-data` outputs should not be written to SQL. Local files are easier to inspect and delete and avoid polluting a database while schemas are still changing.

### Decision

Register `TRADING_DATA_DEVELOPMENT_STORAGE_ROOT` as the development-stage output root for `trading-data`, with relative path `storage` and local path `/root/projects/trading-data/storage`. Use this root for development task outputs and completion receipts until durable `trading-storage` contracts are accepted.

### Rationale

This preserves clean databases during development while keeping a shared, registered locator for task-key and connector planning.

### Consequences

- Default development tasks must not write to SQL.
- Generated contents under `storage/` remain ignored by Git.
- Durable SQL table/partition and receipt storage contracts remain future `trading-storage` work.

## D046 - Data task API templates live in trading-main templates

Date: 2026-04-26

### Context

The user approved designing templates around provider/API requirements for `trading-data` bundles. These shapes affect `trading-manager` task keys, `trading-data` bundle implementation, and later `trading-storage` receipt/output contracts.

### Decision

Create reusable draft data task templates under `storage/templates/data_tasks/` in `trading-main`. Cover task keys, per-bundle README documentation, fetch requirements, clean/normalization requirements, save/output requirements, completion receipts, and fixture/live-call policy.

### Rationale

The template shapes are cross-repository planning surfaces, so they belong in `trading-main/storage/templates/` rather than being hidden as component-local docs or implementation files.

### Consequences

- `trading-data` can reference these templates when designing API-specific bundles.
- The templates remain drafts until schemas are accepted through docs, registry, and tests.
- Stable fields/type/status values discovered while filling templates must be routed through registry migrations.

## D047 - Data source bundles default to one pipeline module

Date: 2026-04-26

### Context

The earlier data task template shape described separate `fetch.py`, `clean.py`, `save.py`, and `receipt.py` modules. The user asked why those steps could not be combined, and approved a simpler default shape.

### Decision

Default each data source bundle to one `pipeline.py` file with one public `run(...)` entry point and internal `fetch`, `clean`, `save`, and `write_receipt` step functions. Keep API-specific details in the bundle README and spec templates. Split step functions into separate files only when bundle complexity justifies it.

### Rationale

This keeps manager invocation simple and avoids premature file sprawl while preserving testable/replayable boundaries inside the pipeline.

### Consequences

- `storage/templates/data_tasks/pipeline.py` is the default implementation template.
- Bundle READMEs own bundle-specific API details.
- Existing fetch/clean/save/receipt spec templates remain design documents, not required separate code files.

## D048 - Data task JSON templates stay minimal

Date: 2026-04-26

### Context

The initial `task_key.json` and `completion_receipt.json` templates included metadata such as provider documentation URLs and future durable references. The user pushed back that templates should serve real usage instead of accumulating fields that will not be consumed.

### Decision

Keep data task key and completion receipt JSON templates minimal. Include only fields used by manager handoff, bundle execution, development output location, and completion evidence. Put provider documentation URLs and other lookup metadata in registry/provider docs or bundle READMEs instead of runtime JSON.

### Rationale

Smaller runtime templates are easier for manager to generate, easier for data pipelines to validate, and less likely to ossify unused conventions.

### Consequences

- `task_key.json` now contains only `task_id`, `bundle`, optional `credential_config_id`, `params`, and `output_dir`.
- `completion_receipt.json` now contains only task identity, bundle, status/timestamps, output directory, output references, row counts, and error.
- Additional fields require a demonstrated consumer or execution need.

## D049 - Data task keys are stable across runs

Date: 2026-04-26

### Context

The user clarified that one task may have multiple runs, such as periodic or scheduled tasks. The task key should remain stable, while per-run data should be recorded in completion receipts.

### Decision

Treat `task_key.json` as the stable task definition. Do not place run-specific values in the task key. Use task-level `completion_receipt.json` with a `runs[]` array, where each run entry records run id, status, timestamps, output directory, outputs, row counts, and error.

### Rationale

This keeps scheduled tasks replayable and comparable across invocations without mutating the task definition for every run.

### Consequences

- `task_key.json` uses `output_root`, not per-run `output_dir`.
- `completion_receipt.json` contains `runs[]`.
- Run outputs should live under `storage/<task-id>/runs/<run-id>/`.
- `pipeline.py` takes `run_id` separately from the task key.

## D050 - Data task JSON fields are registered

Date: 2026-04-26

### Context

The user asked whether the fields in `task_key.json` and `completion_receipt.json` had been registered. They had not yet been registered as `field` rows.

### Decision

Register every current minimal task key, completion receipt, and per-run receipt field as `kind=field` rows with explicit `applies_to` scopes.

### Rationale

These JSON templates are cross-repository handoff surfaces. Their field names should be registered before implementation depends on them.

### Consequences

- Task key fields are registered under `data_task_key`.
- Task-level receipt fields are registered under `data_task_completion_receipt`.
- Per-run receipt fields are registered under `data_task_completion_receipt_run`.
- Any future runtime JSON field requires registry review before adoption.

## D051 - Registry rows declare artifact sync policy

Date: 2026-04-27

### Context

Registry keys are renameable display labels, while stable ids are the durable automation inputs. Some registry edits therefore remain registry-only. Other rows describe fields or templates whose payloads appear directly in code, CSV/JSON previews, Markdown templates, or other plain-text artifacts and must be kept synchronized.

### Decision

Add `artifact_sync_policy` to `trading_registry` and register the allowed values. Initially these used `kind = artifact_sync_policy`; after D054-style registry normalization they are represented as `kind = status_value` with `applies_to = trading_registry.artifact_sync_policy`. Use `registry_only`, `sync_artifact`, and `review_on_merge` to make follow-up expectations visible in `registry/current.csv`.

### Rationale

Reviewers need to know whether a registry edit is only a registry-label/schema change or whether it requires matching artifact edits. Making this explicit prevents silent drift between registry rows and the files they describe.

### Consequences

- `registry/current.csv` exports `artifact_sync_policy` for every row.
- Legal artifact-sync policy values are registered rows and constrained in SQL.
- Rows that point to concrete code/templates/docs should normally use `sync_artifact`.
- Key-only renames can be artifact-neutral for id-based consumers, but merges, deletes, payload changes, or semantic repurposing require review or artifact synchronization.

## D052 - Source and scripts directories are separated

Date: 2026-04-27

### Context

The user clarified that `source` and `script` should not be treated as interchangeable concepts. Across trading repositories, source code directories should be distinguishable from executable maintenance or operational entrypoints, and `source` should not conflict with provider/data-source meaning.

### Decision

Use `src/` for importable, reusable implementation code and `scripts/` for executable maintenance or operational entrypoints. `scripts/` may import `src/`; `src/` must not import `scripts/`. Avoid creating `source/` directories. Use `provider` or `data_source` for external data origins, and use `implementation_path`, `source_file`, or `source_dir` only when referring to code locations.

### Rationale

This keeps package code, operational commands, and provider/source terminology from drifting into ambiguous names. It also makes registry `kind=script` rows easier to review because scripts are stable callable entrypoints rather than ordinary implementation files.

### Consequences

- The registry helper package moved from `helpers/trading_registry/` to `src/trading_registry/`.
- Helper tests moved from `helpers/tests/` to `tests/`.
- The registry migration/export command moved from `registry/sql/apply-migrations.py` to `scripts/apply_registry_migrations.py`.
- Registry script rows now point to stable callable entrypoints or Python helper symbols under the new paths.

## D053 - Trading-main reusable assets live under storage

Date: 2026-04-28

Status: Accepted

Decision:
Move trading-wide reusable template assets from top-level `templates/` into `storage/templates/`, and create `storage/shared/` for reviewed cross-project static files that are not templates.

Rationale:
`trading-main` now needs a broader tracked non-code asset boundary than templates alone. Keeping templates and shared static files under `storage/` makes the repository shape clearer while preserving the distinction from generated runtime outputs, secrets, caches, and component-owned implementation files.

Consequences:
- Reusable templates live under `storage/templates/`.
- Cross-project static/shared files live under `storage/shared/`.
- Registry paths for trading-main-owned templates must point to `storage/templates/...`.
- Generated artifacts and local runtime state still do not belong in `trading-main/storage/`.


## D054 - Status registry values use one kind

Date: 2026-04-28

Status: Accepted

Decision:
Merge status-like registry kinds into `status_value`. The previous kind names (`task_lifecycle_state`, `review_readiness`, `acceptance_outcome`, `test_status`, `maintenance_status`, `docs_status`, and `artifact_sync_policy`) become status domains recorded in `applies_to`, not separate registry kinds.

Rationale:
These rows all have the same structural role: they register allowed state/policy values. Separate kinds made the registry kind system wider without adding a real contract boundary. The field rows still register slot names such as `TASK_LIFECYCLE_STATE`; `status_value` rows register allowed values for those slots.

Consequences:
- `registry/kinds/status_value.md` owns the status-value boundary.
- Status rows must carry their domain in `applies_to`.
- Artifact sync policy values remain constrained in SQL but are registered as `kind=status_value` with `applies_to=trading_registry.artifact_sync_policy`.


## D055 - Temporal fields use their own kind

Date: 2026-04-28

Status: Accepted

Decision:
Move date/time/datetime/timestamp field-name rows from `field` to `temporal_field`. Merge duplicate `status_value` rows when the payload is the same and the row can carry multiple domains in `applies_to`.

Rationale:
Temporal fields such as `created_at`, `event_time_et`, `available_time_et`, and `as_of_date` never overlap ordinary categorical/numeric/text fields, and they need a stricter value-format contract. Status rows with the same payload are also one concept reused by multiple status domains, not separate kinds or separate values.

Consequences:
- Temporal field values must use ISO-8601 semantics; date-only values use `YYYY-MM-DD`, and datetime/timestamp values must carry explicit timezone semantics.
- Locale-dependent date strings such as `YY/MM/DD`, `MM/DD/YY`, or `DD/MM/YY` are not accepted for temporal fields.
- Duplicate status payload rows such as `blocked`, `accepted`, and `rejected` should be merged into one `status_value` row with all applicable domains in `applies_to`.

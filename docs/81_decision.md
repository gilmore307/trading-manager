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

## D004 - Use `trading-source` rather than `trading-fetcher`

Date: 2026-04-25

### Decision

The data upstream repository will be named `trading-source`.

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
- Trading-specific registry responsibilities move from `universal-catalog` into `trading-main/scripts/`.

## D008 - Registry Markdown defines kind boundaries while SQL owns concrete entries

Date: 2026-04-25

### Context

The initial registry migration converted active SQL rows into Markdown tables. That made the kind files too noisy and blurred their purpose.

### Decision

`scripts/registry/kinds/<kind>.md` files define kind boundaries, ranges, and rejection rules only. Concrete registered items live in the SQL-backed `trading_registry` table and append-only migrations under `scripts/registry/sql/schema_migrations/`.

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

After SQL registry updates, `scripts/registry/apply_registry_migrations.py` exports the active `trading_registry` table to:

```text
scripts/registry/current.csv
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

Keep the current kind set and document tie-breaker rules in `scripts/registry/rules/kind-boundary.md`.

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

Move artifact, manifest, ready-signal, and request drafting surfaces to `trading-storage/main/templates/contracts/`. Keep `docs/` focused on project governance plus any approved project-specific guide docs.

### Rationale

The docs spine should contain ratified project context and governance. Drafting templates belong under `trading-storage/main/templates/`. Registry type vocabularies belong under `scripts/`; registry operating guidance may live in an approved docs guide.

### Consequences

- Do not add numbered docs beyond `82_memory.md` for reusable drafting templates.
- Use `trading-storage/main/templates/contracts/` for reusable contract drafting surfaces.
- Use `scripts/registry/kinds/*_type.md` and SQL migrations for registered type vocabularies.
- Use `docs/91_registry.md` for the approved `trading-main` registry operating guide.

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
- Active `scripts/registry/current.csv` should contain only current registry entries.
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

This avoids overloading `note` and makes field usage visible in `scripts/registry/current.csv`.

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

The registry should expose reusable callable helper surfaces, not every helper source file or package constant. Export-level entries make the approved helper API visible in `scripts/registry/current.csv`.

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

Field names are only useful if their valid usage surface is visible. A required `applies_to` column makes `scripts/registry/current.csv` useful for review and prevents broad, ambiguous field registrations.

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

`scripts/registry/current.csv` is generated from SQL and should be refreshed after registry changes. The helper command itself should be discoverable from the registry.

### Decision

Register `scripts/registry/apply_registry_migrations.py --export-only` as `HELPER_REGISTRY_EXPORT_CURRENT_CSV`.

### Rationale

This keeps the CSV generation command visible without mixing it into the id-only lookup helper surface.

### Consequences

- Lookup helpers remain id-only.
- CSV generation is registered as a maintenance helper.
- The helper row points to `scripts/registry/apply_registry_migrations.py` and applies to `scripts/registry/current.csv`.

## D022 - All trading repositories are registry entries

Date: 2026-04-25

### Context

The trading platform is split across `trading-main` plus seven component repositories. Only registering `trading-main` would make cross-repository automation depend on unstated repository names and paths.

### Decision

Register every trading repository as a `repo` row with its stable registry id, repository key, repository name in `payload`, local checkout path in `path`, and component-repository context in `applies_to`.

### Rationale

The registry is the shared naming authority. Component repository names and checkout paths are shared infrastructure facts and should be discoverable through the registry instead of being re-invented in scripts or docs.

### Consequences

- All eight trading repositories are visible in `scripts/registry/current.csv`.
- Automation should use repo row ids to retrieve repository names and paths.
- Repository remotes are recorded in repo-row notes for review visibility.

## D023 - Registry kind boundaries live under scripts/registry/kinds

Date: 2026-04-25

### Context

Registry root was mixing generated snapshots, SQL tooling, review notes, and kind boundary files such as `acceptance_outcome.md`. Moving those files into `scripts/registry/rules/` would confuse source-of-truth definitions with review artifacts.

### Decision

Move all registry kind boundary files into `scripts/registry/kinds/`. Keep `scripts/registry/rules/` for review notes and boundary assessments only.

### Rationale

Kind files are normative boundary documentation. Review files are commentary and assessment records. Separating the directories keeps authority clear while reducing root clutter.

### Consequences

- New registry kinds must add `scripts/registry/kinds/<kind>.md`.
- `scripts/registry/rules/` must not own kind source-of-truth files.
- `scripts/README.md` remains the index for both SQL entries and kind boundary files.

## D024 - Add a registry-specific docs guide

Date: 2026-04-25

### Context

`trading-main` has grown from a docs-only coordination repository into the platform repository that also owns the SQL-backed registry, generated registry snapshot, registry helper surface, and registry maintenance workflow. Keeping all registry operating detail inside the core governance docs would blur the project-wide docs with the registration subsystem guide.

### Decision

Keep the core governance docs focused on the whole trading platform repository. Add `docs/91_registry.md` as the registry-specific operating guide.

### Rationale

The registry is now a first-class function of `trading-main`, not just a passing project context note. It needs a stable guide that explains ownership, entry model, SQL workflow, helper surface, and acceptance checks without overloading the general project docs.

### Consequences

- `docs/91_registry.md` is part of the accepted `trading-main` docs set.
- core governance docs remain project-wide platform docs.
- Registry kind source-of-truth files remain under `scripts/registry/kinds/`, not under `docs/`.
- Contract drafting templates remain under `trading-storage/main/templates/contracts/`, not under `docs/`.

## D025 - Split platform-function guides into helpers registry and templates

Date: 2026-04-25

### Context

`trading-main` owns three first-class platform functions beyond project-wide governance: shared helpers, the SQL-backed registry, and reusable templates. A single registry-specific guide did not capture the shape of the repository now that helpers and templates also have meaningful ownership boundaries.

### Decision

Use three numbered platform-function guide docs after the project-wide spine:

- `docs/90_helpers.md`
- `docs/91_registry.md`
- `docs/92_templates.md`

Keep the core governance docs focused on the whole trading platform repository.

### Rationale

This mirrors the actual top-level structure of `trading-main` and gives each owned platform function a clear operating guide without crowding the project-wide docs.

### Consequences

- Helpers, registry, and templates each have a dedicated docs guide.
- Registry kind source-of-truth files still live under `scripts/registry/kinds/`.
- Template drafts still live under `trading-storage/main/templates/`.
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

Use the Python package rooted at `src/trading_scripts/` as the cross-repository runtime helper distribution strategy. Component repositories should consume the installed `trading_registry` package rather than loose source files.

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

Make the official cross-repository registry helper runtime surface a Python package. Package metadata lives in root `pyproject.toml`, source lives under `src/trading_scripts/`, and the install path is editable installation into `/root/projects/trading-main/.venv`.

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

- `src/trading_scripts/` is the only registry helper implementation.
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
- Legal payload-format values are visible in `scripts/registry/current.csv`.
- The Python package no longer exports payload-format validator helpers.
- Tests compare registered payload-format rows with the SQL check constraint.

## D034 - Registry kind vocabulary is not a runtime helper export

Date: 2026-04-25

### Context

After moving payload-format vocabulary out of runtime helper exports, the Python package still exposed `REGISTRY_KINDS`, `is_registry_kind`, and `assert_registry_kind`. That repeated the same passive-vocabulary problem in a different file.

### Decision

Remove registry kind vocabulary validators from the runtime helper package. Treat legal registry kinds as a schema and registry-docs boundary: the SQL kind constraint and `scripts/registry/kinds/*.md` files must stay aligned, and tests enforce that alignment.

### Rationale

Runtime helpers should expose behavior needed by component consumers, not passive copies of scripts/schema vocabulary. Keeping the vocabulary in SQL and boundary docs avoids drift and makes review happen in the registry surfaces.

### Consequences

- `src/trading_scripts/registry_types.py` is removed.
- The Python package no longer exports `REGISTRY_KINDS`, `is_registry_kind`, or `assert_registry_kind`.
- `RegistryReader.list_items_by_kind` only validates that kind input is non-empty; SQL/current-registry tests own legal-kind alignment.
- Tests compare the latest SQL kind constraint with `scripts/registry/kinds/*.md` and ensure current rows use constrained kinds.

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

Use one JSON secret file per source/provider under `/root/secrets/<source>.json`. Registry config rows should point to the source-level alias, such as `okx` or `github`, and may mirror the JSON file path in `path`. Register reusable JSON key names, such as `api_key`, `secret_key`, `passphrase`, `endpoint`, `allowed_ip_address`, `api_key_remark_name`, and `pat`, as `field` rows with `applies_to=source_secret_file_schema`.

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
- `SOURCE_SECRET_ALLOWED_IP_ADDRESS` and `SOURCE_SECRET_API_KEY_REMARK_NAME` are registered field rows with `applies_to=source_secret_file_schema`.

## D038 - Alpaca is a registered stock and ETF data provider config surface

Date: 2026-04-26

### Context

The user provided Alpaca paper API credentials and endpoint for acquiring stock and ETF bars, quotes, trades, and news. Source credentials now use one JSON file per source.

### Decision

Register Alpaca as a provider term and add `ALPACA_SECRET_ALIAS` pointing to source alias `alpaca` and `/root/secrets/alpaca.json`. Register `endpoint` as a reusable source-secret JSON field.

### Rationale

Alpaca is a data-source connector dependency for `trading-source`; credentials and endpoint should be available through the same source-level JSON secret pattern as OKX and GitHub.

### Consequences

- Alpaca JSON fields are `api_key`, `secret_key`, and `endpoint`.
- `trading-source` may plan an Alpaca source connector using `ALPACA_SECRET_ALIAS` once implementation begins.
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
- `trading-source` may document ThetaData as the intended options-data provider, with implementation blocked on connector/JAR/credential layout decisions.

## D040 - Economic data providers use source-level API key aliases

Date: 2026-04-26

### Context

The user provided API keys for FRED, Census, BEA, and BLS. These sources support macroeconomic, demographic, labor, and market-context data acquisition for `trading-source`.

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

## D044 - Data acquisition is control-plane-driven and historical-only

Date: 2026-04-26

### Context

The user clarified that current `trading-source` acquisition work concerns historical data. Realtime data and execution-time feeds belong to `trading-execution` later. Data tasks should be initiated by `trading-manager` and completed by `trading-source` with durable evidence in `trading-storage`.

### Decision

Register shared workflow terms for historical data acquisition, manager-issued data task key files, and data task completion receipts. Treat the exact schema and storage placement as pending cross-repository contract work; development receipts use local `storage/` before durable storage contracts exist.

### Rationale

The boundary keeps orchestration, data acquisition, storage, and execution responsibilities separate while preserving a named contract surface for implementation planning.

### Consequences

- `trading-source` remains historical-only for now.
- `trading-manager` owns task-key creation and lifecycle orchestration.
- Development-stage outputs and receipts use local `storage/`; `trading-storage` owns durable SQL output placement and completion receipt storage once schemas are accepted.
- Registry terms exist before component implementation depends on the names.

## D045 - Trading-data development outputs use local file storage before SQL

Date: 2026-04-26

### Context

The user clarified that during development, `trading-source` outputs should not be written to SQL. Local files are easier to inspect and delete and avoid polluting a database while schemas are still changing.

### Decision

Register `TRADING_SOURCE_DEVELOPMENT_STORAGE_ROOT` as the development-stage output root for `trading-source`, with relative path `storage` and local path `/root/projects/trading-source/storage`. Use this root for development task outputs and completion receipts until durable `trading-storage` contracts are accepted.

### Rationale

This preserves clean databases during development while keeping a shared, registered locator for task-key and connector planning.

### Consequences

- Default development tasks must not write to SQL.
- Generated contents under `storage/` remain ignored by Git.
- Durable SQL table/partition and receipt storage contracts remain future `trading-storage` work.

## D046 - Data task API templates live in trading-main templates

Date: 2026-04-26

### Context

The user approved designing templates around provider/API requirements for `trading-source` bundles. These shapes affect `trading-manager` task keys, `trading-source` bundle implementation, and later `trading-storage` receipt/output contracts.

### Decision

Create reusable draft data task templates under `trading-storage/main/templates/data_tasks/`. Cover task keys, per-bundle README documentation, fetch requirements, clean/normalization requirements, save/output requirements, completion receipts, and fixture/provider-dispatch policy.

### Rationale

The template shapes are cross-repository planning surfaces, so they belong in `trading-storage/main/templates/` rather than being hidden as component-local docs or implementation files.

### Consequences

- `trading-source` can reference these templates when designing API-specific bundles.
- The templates remain drafts until schemas are accepted through docs, registry, and tests.
- Stable fields/type/status values discovered while filling templates must be routed through registry migrations.

## D047 - Data source bundles default to one pipeline module

Date: 2026-04-26

### Context

The earlier data task template shape described separate `fetch.py`, `clean.py`, `save.py`, and `receipt.py` modules. The user asked why those steps could not be combined, and approved a simpler default shape.

### Decision

Default each data source bundle to one `pipeline.py` file with one public `run(...)` entry point and internal `fetch`, `clean`, `save`, and `write_receipt` step functions. Keep API-specific details in the bundle README and spec templates. Split step functions into separate files only when bundle complexity justifies it.

### Rationale

This keeps control-plane invocation simple and avoids premature file sprawl while preserving testable/replayable boundaries inside the pipeline.

### Consequences

- `trading-storage/main/templates/data_tasks/pipeline.py` is the default implementation template.
- Bundle READMEs own bundle-specific API details.
- Existing fetch/clean/save/receipt spec templates remain design documents, not required separate code files.

## D048 - Data task JSON templates stay minimal

Date: 2026-04-26

### Context

The initial `task_key.json` and `completion_receipt.json` templates included metadata such as provider documentation URLs and future durable references. The user pushed back that templates should serve real usage instead of accumulating fields that will not be consumed.

### Decision

Keep data task key and completion receipt JSON templates minimal. Include only fields used by control-plane handoff, bundle execution, development output location, and completion evidence. Put provider documentation URLs and other lookup metadata in scripts/provider docs or bundle READMEs instead of runtime JSON.

### Rationale

Smaller runtime templates are easier for control plane to generate, easier for data pipelines to validate, and less likely to ossify unused conventions.

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

Add `artifact_sync_policy` to `trading_registry` and register the allowed values. Initially these used `kind = artifact_sync_policy`; after D054-style registry normalization they are represented as `kind = status_value` with `applies_to = trading_registry.artifact_sync_policy`. Use `registry_only`, `sync_artifact`, and `review_on_merge` to make follow-up expectations visible in `scripts/registry/current.csv`.

### Rationale

Reviewers need to know whether a registry edit is only a registry-label/schema change or whether it requires matching artifact edits. Making this explicit prevents silent drift between registry rows and the files they describe.

### Consequences

- `scripts/registry/current.csv` exports `artifact_sync_policy` for every row.
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

- The registry helper package moved from `helpers/trading_scripts/` to `src/trading_scripts/`.
- Helper tests moved from `helpers/tests/` to `tests/`.
- The registry migration/export command moved from `scripts/registry/sql/apply-migrations.py` to `scripts/registry/apply_registry_migrations.py`.
- Registry script rows now point to stable callable entrypoints or Python helper symbols under the new paths.

## D053 - Trading-main reusable assets live under storage

Date: 2026-04-28

Status: Accepted

Decision:
Move trading-wide reusable template assets from top-level `templates/` into `trading-storage/main/templates/`, and create `trading-storage/main/shared/` for reviewed cross-project static files that are not templates.

Rationale:
`trading-main` now needs a broader tracked non-code asset boundary than templates alone. Keeping templates and shared static files under `storage/` makes the repository shape clearer while preserving the distinction from generated runtime outputs, secrets, caches, and component-owned implementation files.

Consequences:
- Reusable templates live under `trading-storage/main/templates/`.
- Cross-project static/shared files live under `trading-storage/main/shared/`.
- Registry paths for trading-main-owned templates must point to `trading-storage/main/templates/...`.
- Generated artifacts and local runtime state do not belong in checked-in shared asset directories.


## D054 - Status registry values use one kind

Date: 2026-04-28

Status: Accepted

Decision:
Merge status-like registry kinds into `status_value`. The previous kind names (`task_lifecycle_state`, `review_readiness`, `acceptance_outcome`, `test_status`, `maintenance_status`, `docs_status`, and `artifact_sync_policy`) become status domains recorded in `applies_to`, not separate registry kinds.

Rationale:
These rows all have the same structural role: they register allowed state/policy values. Separate kinds made the registry kind system wider without adding a real contract boundary. The field rows still register slot names such as `TASK_LIFECYCLE_STATUS`; `status_value` rows register allowed values for those slots.

Consequences:
- `scripts/registry/kinds/status_value.md` owns the status-value boundary.
- Status rows must carry their domain in `applies_to`.
- Artifact sync policy values remain constrained in SQL but are registered as `kind=status_value` with `applies_to=trading_registry.artifact_sync_policy`.


## D055 - Temporal fields use their own kind

Date: 2026-04-28

Status: Accepted

Decision:
Move date/time/datetime/timestamp field-name rows from `field` to `temporal_field`. Merge duplicate `status_value` rows when the payload is the same and the row can carry multiple domains in `applies_to`.

Rationale:
Temporal fields such as `created_at`, `event_time`, `available_time`, and `as_of_date` never overlap ordinary categorical/numeric/text fields, and they need a stricter value-format contract. Status rows with the same payload are also one concept reused by multiple status domains, not separate kinds or separate values.

Consequences:
- Temporal field values must use ISO-8601 semantics; date-only values use `YYYY-MM-DD`, and datetime/timestamp values must carry explicit timezone semantics.
- Locale-dependent date strings such as `YY/MM/DD`, `MM/DD/YY`, or `DD/MM/YY` are not accepted for temporal fields.
- Duplicate status payload rows such as `blocked`, `accepted`, and `rejected` should be merged into one `status_value` row with all applicable domains in `applies_to`.


## D056 - Registry fields are semantic axes, not usage-specific spellings

Date: 2026-04-28

Status: Accepted

Decision:
Merge temporal field rows that only differ by usage-specific suffixes, such as `updated_at` and `updated_at_et`, into one semantic field row. Add `classification_field` for categorical field axes and classify type/kind/status/scope/category/sector/side-style fields there.

Rationale:
The registry records shared semantic contracts, not every spelling variant used by a single template. If the same concept is used in multiple places, those scopes belong in `applies_to`. Timezone and serialization rules belong in the temporal field contract and template documentation, not in duplicate field rows. Categorical axes likewise deserve explicit review and semantic de-duplication.

Consequences:
- `created_at_et` and `updated_at_et` are replaced by canonical `created_at` and `updated_at` field payloads with event/detail template scopes added to `applies_to`.
- Downstream templates and pipelines should use canonical field payloads from registry ids rather than component-specific duplicate names.
- Classification field values should use stable lowercase token vocabularies unless a source contract explicitly requires a reviewed alternate encoding.


## D057 - Classification fields name semantic axes

Date: 2026-04-28

Status: Accepted

Decision:
Classification field payloads name the semantic classification axis, not the source/template-specific spelling. Merge hint/source variants into the canonical axis when the meaning is the same.

Rationale:
Rows such as `impact_scope_hint` and `impact_scope` described the same classification axis at different pipeline stages. Similarly, vague names such as `category` and `side_hint` do not say what is being classified. Registry fields should make the semantic distinction explicit.

Consequences:
- GDELT impact-scope hint uses canonical `impact_scope`; `GDELT_IMPACT_SCOPE_HINT` is removed and `EVENT_IMPACT_SCOPE` applies to `gdelt_article_template`.
- Trading Economics source category becomes `source_event_type`.
- Option event side hint becomes `trade_side_type`.
- Future classification fields should prefer explicit suffixes such as `*_type`, `*_status`, `*_scope`, `*_policy`, `*_outcome`, `*_readiness`, or `*_tags` according to the actual semantic domain.


## D058 - Field registry is a semantic vocabulary

Date: 2026-04-28

Status: Accepted

Decision:
Treat field rows as semantic vocabulary entries: same word means same concept, different words mean different concepts. Do not duplicate field rows only because the same semantic value appears in a different output template or pipeline stage.

Rationale:
The registry is a semantic table, not a usage-location table. Usage belongs in `applies_to`. Rows such as bar `open` and liquidity `trade_open` described the same open-price concept, while `count` was too vague for the trade-count concept already used elsewhere.

Consequences:
- OHLCV fields use canonical `open`, `high`, `low`, `close`, `volume`, and `vwap` across bars and trade-derived liquidity intervals.
- Trade-count uses canonical payload `trade_count` across market bars, option bars, and liquidity intervals.
- Template-specific duplicates with prefixes such as `trade_open`, `trade_high`, `trade_low`, `trade_close`, `trade_volume`, and `trade_vwap` are removed.
- Generated artifact timestamps use canonical `generated_at`; context-specific spellings such as `analysis_generated_at` and `standard_generated_at` are removed.
- Timestamp fields that were still registered as ordinary `field` rows, such as `interval_start` and `seen_at`, are reclassified as `temporal_field`.

## D059 - Classification words name the axis, not the source context

Date: 2026-04-28

Status: Accepted

Decision:
Normalize remaining classification field names so the word identifies the semantic axis. Use `*_status` for lifecycle/status slots, `*_type` for taxonomy labels, and `*_tags` for multi-label tag sets. Do not preserve vague source words such as `themes` when the field is really a source-provided theme/tag set.

Rationale:
`task_lifecycle_state` and `analysis_status` were the same kind of status slot expressed with different nouns. `themes`, `style_tags`, `sector`, and `exposure_type` were not all the same concept, but several names hid the axis distinction: GDELT themes are source-provided evidence tags, ETF holding sector is an issuer sector taxonomy label, market ETF exposure type is a curated universe role/type, and stock ETF exposure tags are derived model-facing labels.

Consequences:
- Task lifecycle field/domain uses `task_lifecycle_status`; corresponding status-value rows use that domain.
- GDELT article source tags use `source_theme_tags`.
- ETF holding sector taxonomy uses `sector_type`.
- Stock ETF exposure multi-label output uses `exposure_tags`.
- `exposure_type` remains separate because it classifies the curated ETF universe exposure role, not a sector/theme value itself.

## D060 - Default timezone is not encoded in temporal field names

Date: 2026-04-28

Status: Accepted

Decision:
Remove default timezone suffixes such as `_et` and `_utc` from normalized temporal field payloads and keys. The `temporal_field` contract and template documentation own timezone semantics; normalized final outputs default to America/New_York unless a reviewed source contract explicitly says otherwise.

Rationale:
The registry is a semantic vocabulary. If all normalized model-facing timestamps use the same project timezone, encoding `ET` in each field name adds noise and makes keys/payloads less regular. The field word should identify the time concept (`event_time`, `window_start`, `generated_at`), not repeat the default timezone.

Consequences:
- `timestamp_et`, `event_time_et`, `effective_time_et`, `interval_start_et`, `available_time_et`, `window_start_et`, and similar payloads become `timestamp`, `event_time`, `effective_time`, `interval_start`, `available_time`, and `window_start`.
- Registry keys drop matching `_ET` / `_UTC` suffixes.
- GDELT `seen_at` is normalized to America/New_York for final saved output.
- Internal fetch manifests may still use explicitly UTC operational fields such as `fetched_at_utc`; those are not normalized model-facing temporal registry fields.

## D061 - Identity fields have their own kind

Date: 2026-04-28

Status: Accepted

Decision:
Add `identity_field` for field names whose values identify, name, or label an entity/artifact/source/instrument/task/report/row. Later D062 moved locator/reference fields into `path_field`. Keep `field` for non-identity, non-path, non-temporal, non-classification values.

Rationale:
Identifier and naming fields such as `id`, `event_id`, `symbol`, `title`, `headline`, `issuer`, and `contract_symbol` have a distinct semantic role from ordinary numeric/text measures. They should not be mixed with metrics or free-text payload slots. D062 later split path/URL/reference locators into `path_field`.

Consequences:
- Registry resolvers that consume field-name rows must accept `field`, `identity_field`, `temporal_field`, and `classification_field`.
- Classification axes keep strict suffix semantics: `*_status` for status/lifecycle states, `*_type` for taxonomy/type axes, `*_scope` for coverage/scope, `*_tags` for multi-label sets, and `kind` only for registry-native terms such as `data_kind` or `registry_item_kind`. Generic `status` is not a valid semantic field when separate domains such as `data_kind_template_status` and `data_task_run_status` have different vocabularies.
- `OPTION_RIGHT / right` becomes `OPTION_RIGHT_TYPE / option_right_type` because CALL/PUT is a tiny categorical type axis, not a clear standalone field word.

## D062 - Locator fields and status/policy classification axes

Date: 2026-04-28

Status: Accepted

Decision:
Split locator/reference fields into `path_field`, keep `identity_field` for identity/naming only, and normalize classification-axis wording so acceptance/review concepts are statuses while artifact sync policy is a policy type.

Rationale:
`identity_field` was too broad when it included URLs, paths, references, output dirs, and file lists. Those values locate artifacts or evidence; they do not name the entity itself. Likewise, `acceptance_outcome` and `review_readiness` are status axes in practice, while `artifact_sync_policy` is a policy-type axis rather than a status.

Consequences:
- `path_field` owns locator/reference slots such as `registry_item_path`, `event_link_url`, `source_url`, `event_report_url`, `source_reference`, `source_references`, `repository_path`, `data_task_run_output_directory`, `data_task_run_output_references`, `data_kind_template_preview_file_path`, `execution_allowed_paths`, and similar scoped path/reference fields.
- `identity_field` owns only ids, names, symbols, tickers, issuers, titles/headlines, contract symbols, and similar identity/naming slots.
- `ACCEPTANCE_OUTCOME / acceptance_outcome` becomes `ACCEPTANCE_STATUS / acceptance_status`.
- `REVIEW_READINESS / review_readiness` becomes `REVIEW_STATUS / review_status`.
- `REGISTRY_ITEM_ARTIFACT_SYNC_POLICY / artifact_sync_policy` becomes the semantic classification field `REGISTRY_ITEM_ARTIFACT_SYNC_POLICY_TYPE / artifact_sync_policy_type`; the physical registry column may remain `artifact_sync_policy` as existing schema storage.

## D063 - Scoped identity and path field names use prefix plus suffix

Date: 2026-04-28

Status: Accepted

Decision:
Reserve single-name identity/path payloads for genuinely generic shared semantics. Scoped identity and locator fields must use prefix + semantic suffix.

Rationale:
After splitting `identity_field` and `path_field`, rows still mixed generic words such as `issuer`, `provider`, `headline`, `url`, `path`, `reference`, `source_ref`, and `outputs` with scoped fields. That recreated ambiguity inside the new kinds. A semantic vocabulary needs the word itself to communicate whether it is generic or context-scoped.

Consequences:
- Scoped identity fields use names such as `issuer_name`, `source_provider_name`, `source_name`, `timeline_headline`, `data_task_run_id`, and `option_event_detail_standard_id`.
- Scoped locator fields use names such as `registry_item_path`, `event_link_url`, `event_analysis_report_url`, `event_report_url`, `event_report_json_url`, `source_reference`, `source_references`, `source_snapshot_references`, `data_kind_template_preview_file_path`, `data_task_run_output_directory`, and `data_task_run_output_references`.
- `TRADING_ECONOMICS_REFERENCE / reference` is not a locator and becomes ordinary `field` `TRADING_ECONOMICS_REFERENCE_PERIOD / reference_period`.
- Downstream final saved templates and pipelines must use the normalized payloads; raw provider/API payload names may remain unchanged at ingestion boundaries.

## D064 - Normalized tradable identifiers use symbol, not ticker

Date: 2026-04-28

Status: Accepted

Decision:
Use `symbol` as the normalized project-facing word for tradable instrument identifiers. Reserve `ticker` for source/provider prose or raw ingestion aliases when an external source uses that word.

Rationale:
The registry had both `symbol` and `ticker` for the same normalized semantic axis. That violated the semantic-vocabulary rule: same meaning should use the same word. In final saved schemas, ETF and ETF-holding identifiers are tradable symbols, so scoped columns become `etf_symbol` and `holding_symbol`.

Consequences:
- `ETF_TICKER / etf_ticker` becomes `ETF_SYMBOL / etf_symbol`.
- `ETF_HOLDING_TICKER / holding_ticker` becomes `ETF_HOLDING_SYMBOL / holding_symbol`.
- Ingestion may temporarily accept legacy `etf_ticker` / `holding_ticker` aliases at provider/task boundaries, but final saved templates use `*_symbol`.
- `EVENT_SECURITY_ID / security_id` is removed from active final event templates because no canonical security-master identifier exists yet and current sample usage duplicated `symbol`. If a true security master is introduced later, it should register a precise scoped identifier such as `security_master_id`, not a vague duplicate of `symbol`.

## D065 - Narrative and error columns are not ordinary fields

Date: 2026-04-28

Status: Accepted

Decision:
Split human-readable narrative/explanatory columns, including error-detail columns, out of ordinary `field` rows.

Rationale:
The plain `field` kind was still carrying notes, summaries, caveats, request-parameter descriptions, coverage reasons, and error payloads. These are qualitatively different from scalar model/input fields: they explain or diagnose rather than measure, identify, locate, classify, or timestamp. Keeping them in `field` makes the kind boundary too broad.

Consequences:
- Add `text_field` for narrative/explanatory columns such as `summary`, `coverage_reason`, `known_caveats`, `acceptance_summary`, `change_summary`, `maintenance_summary`, `task_status_summary`, `error`, and registry `note`.
- Failure/diagnostic payloads such as `error` are `text_field` because they explain failures.
- Downstream registry field resolvers must accept `text_field` wherever they materialize final template columns.
- Structured context/object fields remain ordinary `field` unless their primary role is explanation or error reporting.


## D066 - Parameter collections are parameter fields

Date: 2026-04-28

Status: Accepted

Decision:
Split request/task parameter collections out of both ordinary `field` and `text_field` into `parameter_field`.

Rationale:
`request_parameters` is not a prose note; it represents the parameter collection accepted by a data-kind/source request contract. Likewise task `params` is a bundle-specific parameter object. Treating these as text hides that they are structured input knobs rather than narrative explanation.

Consequences:
- `DATA_KIND_TEMPLATE_REQUEST_PARAMETERS / request_parameters` is `parameter_field`, not `text_field`.
- `DATA_TASK_PARAMS / params` is `parameter_field`, not ordinary `field`.
- Downstream registry field resolvers must accept `parameter_field` wherever they materialize template/task columns.
- Prose explanations about parameters remain `text_field`; the parameter collection itself is `parameter_field`.

## D067 - Reorder execution and event overlay bundles

Accepted: 2026-04-28

Layer 06 is now the position/execution model-input bundle and Layer 07 is now the event overlay model-input bundle.

Registry changes:

- `06_EVENT_OVERLAY_MODEL_INPUTS` became `06_BUNDLE_POSITION_EXECUTION` with payload `06_bundle_position_execution`.
- `07_PORTFOLIO_RISK_MODEL_INPUTS` became `07_BUNDLE_EVENT_OVERLAY` with payload `07_bundle_event_overlay`.
- The old 06/07 bundle config rows were removed because those manifest-style configs were obsolete.
- Event overlay references, including equity abnormal activity, now apply to `07_bundle_event_overlay`.

Rationale: Layer 05 chooses option contracts; Layer 06 needs selected-contract option time series to study execution. Event overlay should remain a later one-row-per-event context layer, not the sixth layer.

## D068 - Register model-input SQL output fields as business fields

Accepted: 2026-04-28

Current accepted model-input SQL outputs now have registry field coverage. Shared semantic fields such as `symbol`, `timestamp`, OHLCV, ETF holding columns, option contract identity columns, and event identity/title/source columns were attached to the relevant SQL table contracts via `applies_to`. New fields were added only where no canonical semantic field existed:

- `option_symbol`
- `dollar_volume`
- `avg_bid_size`
- `avg_ask_size`
- `spread_bps`
- `snapshot_type`
- `information_role_type`
- `event_category_type`
- `scope_type`
- `reference_type`
- `reference`

The registry should describe business output fields, not old manifest/config mechanics. Task/run lineage fields such as `run_id` and `task_id` remain receipt/run metadata rather than new business-output fields.

## D069 - Prune obsolete preview/template-only field semantics

Accepted: 2026-04-28

The registry no longer keeps field-like rows that only described retired `trading-source/storage/templates/data_kinds/*.preview.csv` files. Accepted model-input outputs now use dedicated SQL contracts, so field rows survive only when they apply to a current SQL business table or a still-valid shared, registry, task, receipt, execution, acceptance, or maintenance artifact.

Consequences:

- Field-like kinds (`field`, `identity_field`, `path_field`, `temporal_field`, `classification_field`, `text_field`, and `parameter_field`) must not carry obsolete `*_template`, `option_template`, or `data_kind_template` `applies_to` values.
- Retained final-SQL fields have `applies_to` values such as `bundle_01_market_regime`, `bundle_02_security_selection`, `bundle_03_strategy_selection`, `bundle_05_option_expression`, `bundle_06_position_execution`, or `bundle_07_event_overlay`.
- Preview/template file paths are not evidence for retaining field rows. If a field is not part of a current SQL contract or valid non-template artifact, it should be removed instead of preserved as vocabulary clutter.

## D070 - Retired data-kind previews are not active registry items

Accepted: 2026-04-28

The old `trading-source/storage/templates/data_kinds/*.preview.csv` and preview JSON files are no longer active contracts. Dedicated SQL storage contracts now own accepted model-input/business data shapes, and current SQL business fields are registered directly against those tables.

Consequences:

- Remove active `data_kind` rows whose only contract evidence was a retired preview/template file.
- Remove the old data-kind preview generator script registration.
- Keep `source_capability` and `term` rows for source/provider concepts that are still useful for adapter planning, entitlement review, or glossary reference, but do not promote them to `data_kind` without a current accepted storage contract.
- Do not recreate preview/template-only field rows or `applies_to` values. Registry retention is based on final SQL tables and still-valid shared/task/receipt/registry artifacts, not historical preview files.

## D071 - Numbered trading-source package names are data bundles, not model-input universes

Date: 2026-04-28
Status: Accepted

### Context

The numbered `trading-source` packages were named `*_model_inputs`, which made them sound like the complete input universe for each model layer. Chentong clarified that these packages only fetch and prepare the data that must come from data sources; the full model-input set also includes upstream model outputs, candidate artifacts, portfolio/execution state, and feature construction outside these data bundles.

### Decision

Rename active numbered data-bundle registry rows to `NN_BUNDLE_<LAYER>` with payloads `NN_bundle_<layer>` and paths under the then-current bundle package path. Later D077 moved active paths to `trading-source/src/data_bundles/NN_bundle_<layer>`.

Prune obsolete numbered bundle-local config rows that pointed to removed `config.json` files. Stable defaults for accepted numbered bundles live in reviewed pipeline code unless operators/researchers intentionally need a bundle-local config surface.

### Consequences

- `data_bundle` rows describe control-plane-facing data acquisition/preparation bundles, not complete model-input universes.
- SQL output tables live under the `trading_source` schema because they are source-backed trading-source bundle outputs, not complete model inputs.
- Do not introduce new active package paths named `*_model_inputs` under `src/trading_source/data_bundles/`.

## D072 - Bundle SQL tables use trading-source bundle names

Date: 2026-04-28
Status: Accepted

### Context

The accepted numbered data bundles wrote SQL tables with model-layer business names such as `market_regime_etf_bar` and `event_overlay_event`. Chentong clarified that these names will collide semantically once downstream training-data tables exist: these tables are the source-backed outputs of `trading-source` bundles, not the complete model/training data universe.

### Decision

Name accepted numbered bundle SQL tables after the writing bundle, using portable SQL snake_case:

- `trading_source.bundle_01_market_regime`
- `trading_source.bundle_02_security_selection`
- `trading_source.bundle_03_strategy_selection`
- `trading_source.bundle_05_option_expression`
- `trading_source.bundle_06_position_execution`
- `trading_source.bundle_07_event_overlay`

CLI/package names may use hyphens where appropriate, but SQL identifiers use underscores.

### Consequences

- Do not name `trading-source` bundle output tables as if they are complete model-input or training-data tables.
- Downstream training/model repositories can later create their own derived/training tables without colliding with source-backed bundle outputs.

## D073 - Bundle SQL outputs use trading_source schema, not model_inputs

Date: 2026-04-28
Status: Accepted

### Context

After bundle table names were changed to follow the producing `trading-source` bundle, Chentong clarified that the SQL schema name `model_inputs` is still wrong. A bundle output is not the model's full input set; models also consume upstream model outputs, candidate artifacts, feature tables, portfolio/execution state, and later training-data tables.

### Decision

Accepted numbered `trading-source` bundle SQL outputs live under schema `trading_source`, not `model_inputs`:

- `trading_source.bundle_01_market_regime`
- `trading_source.bundle_02_security_selection`
- `trading_source.bundle_03_strategy_selection`
- `trading_source.bundle_05_option_expression`
- `trading_source.bundle_06_position_execution`
- `trading_source.bundle_07_event_overlay`

### Consequences

- `model_inputs` must not be used for source-backed `trading-source` bundle outputs.
- Future model/training repositories can own their own model-input or training-data schemas without semantic collision.

## D074 - Complete implemented source-capability coverage

Date: 2026-04-28
Status: Accepted

### Context

`source_capability` is useful as the registry vocabulary for source/provider endpoint families and raw/transient record families, but coverage was incomplete. Some ThetaData, SEC, calendar, and raw quote/trade concepts existed while implemented Alpaca, GDELT, ETF holdings, OKX candle, and Trading Economics visible-page capabilities were missing or left as terms.

### Decision

Register source capabilities for currently implemented `trading-source` source-interface capabilities:

- Alpaca historical equity bars, news, latest snapshots, trades, and quotes.
- OKX crypto candles, trades, quotes, and order books.
- GDELT GKG BigQuery records.
- Official ETF issuer holdings publications across CSV/XLSX/JSON/HTML issuer surfaces.
- Trading Economics visible calendar web pages.
- Existing ThetaData option, SEC EDGAR, FOMC/calendar, and raw market-data capabilities remain `source_capability` where they describe source/provider record families rather than accepted final data shapes.

### Consequences

- Use `source_capability` for source availability, entitlement review, adapter planning, and transient/raw input documentation.
- Do not promote source capabilities to `data_kind` without a current accepted storage contract.
- Keep implemented adapters in `data_source`; keep control-plane-facing tasks in `data_bundle`.

## D075 - Split provider identities out of generic terms

Date: 2026-04-28
Status: Accepted

### Context

After `source_capability` became the registry kind for provider/source endpoint families and raw record families, provider identities themselves were still stored as generic `term` rows. That made the source vocabulary uneven: provider/source owners, provider capabilities, implemented adapters, and control-plane-facing bundles were no longer equally explicit.

### Decision

Add `provider` as the registry kind for external data/provider organizations, platforms, exchanges, official agencies, code hosts, and authoritative source surfaces. Reclassify provider/source-owner rows such as Alpaca, OKX, ThetaData, GDELT, SEC EDGAR, Trading Economics, FRED, BEA, BLS, Census, GitHub, and U.S. Treasury Fiscal Data from `term` to `provider`.

Use `term` only for ordinary glossary/reference concepts. Use `source_capability` for endpoint families, raw/transient record families, or entitlement-gated capabilities owned by a provider. Use `data_source` for implemented adapters/interfaces.

### Consequences

- Provider documentation URLs now belong on `provider.path` rather than provider `term` rows.
- Provider capability coverage can be reviewed without promoting capabilities to final `data_kind` status.
- The registry kind split is now: `provider` owns who publishes it; `source_capability` owns what the provider exposes; `data_source` owns our adapter; `data_bundle` owns control-plane-facing runs.

## D076 - Provider rows are limited to current source-interface providers

Date: 2026-04-28
Status: Accepted

### Context

Splitting `provider` out of `term` made the provider/source-owner boundary clearer, but the first split promoted historical, fallback, secret-only, and non-data-source platform references into `provider`. That overstated current provider status and blurred active source-interface planning.

### Decision

Limit `provider` rows to current source-interface providers. Current providers are source owners actively used by implemented source interfaces or accepted active source workflows.

Keep historical, fallback, documentation-only, or secret-alias-only references as `term` or `config` rows until a current source interface routes through them again.

Current provider rows are:

- `ALPACA`
- `GDELT`
- `OKX`
- `SEC_EDGAR`
- `THETADATA`
- `TRADING_ECONOMICS`

Reclassify `BEA`, `BLS`, `CENSUS`, `FRED`, `GITHUB`, and `US_TREASURY_FISCAL_DATA` back to `term` because they are not current trading-source source-interface providers.

### Consequences

- `provider` now means active current provider/source owner, not merely known possible source or stored secret alias.
- Historical macro provider references can still exist as `term` rows for documentation and future revival.
- Source-secret config rows may remain even when the provider is not current.

## D077 - trading-source source packages live directly under src

Date: 2026-04-28
Status: Accepted

### Context

`trading-source` removed its redundant `src/trading_source/` package wrapper. The repository boundary already identifies the component, and the meaningful importable boundaries are data bundles, data sources, source interfaces, source availability probes, and storage helpers.

### Decision

Registry paths for active `trading-source` data bundles, data sources, and helpers use `trading-source/src/<package>/...` instead of `trading-source/src/trading_source/<package>/...`.

### Consequences

- Do not register new active paths under `trading-source/src/trading_source/`.
- Current implementation paths should point directly to `src/data_bundles`, `src/data_sources`, `src/source_interfaces`, `src/source_availability`, or `src/storage`.

## D078 - Park unaccepted project-development slot drafts outside the skill

Date: 2026-04-29
Status: Accepted

### Context

The OpenClaw project-development skill contained both true skill scaffolding templates and broader slot-draft files such as acceptance receipt slots, completion receipt slots, execution key slots, maintenance output slots, and task register slots. Those slot scopes had also leaked into registry `applies_to` values even though they did not have accepted current contract files.

### Decision

Keep only the docs scaffolding, root README template, and Codex task prompt template in `skills/openclaw/project_development/templates/`.

Move the unaccepted slot drafts into `trading-storage/main/templates/project_development/` as parked drafts:

- `acceptance_receipt_slots.md`
- `completion_receipt_slots.md`
- `execution_key_slots.md`
- `maintenance_output_slots.md`
- `task_register_slots.md`

Remove their registry field/status rows for now. Re-register only after each contract is redesigned and accepted one by one.

### Consequences

- The parked slot drafts are not active registry contracts.
- Do not use `maintenance_output_slots`, `acceptance_receipt_slots`, `completion_receipt_slots`, `execution_key_slots`, or `task_register_slots` as active registry scopes until accepted again.
- Current accepted data-task contracts remain under `data_task_key`, `data_task_completion_receipt`, and `data_task_completion_receipt_run`.

## D079 - Remove unaccepted data-task architecture registry rows

Date: 2026-04-29
Status: Accepted

### Context

The data-task key and completion-receipt templates were early task-architecture drafts. Their registry rows made fields such as `data_task_run_status`, `data_task_run_id`, output references, row counts, and completion timestamps look accepted even though the task architecture should wait until model and bundle contracts are settled.

### Decision

Remove registry rows tied to unaccepted data-task architecture scopes and templates:

- `data_task_key`
- `data_task_completion_receipt`
- `data_task_completion_receipt_run`
- data-task template rows under `trading-storage/main/templates/data_tasks/`
- `TRADING_SOURCE_DEVELOPMENT_STORAGE_ROOT`
- data-task workflow terms for task key files, completion receipts, and task runs

Leave the files under `trading-storage/main/templates/data_tasks/` as parked drafts only. Re-register fields/templates/terms later one by one after the task architecture is redesigned and accepted.

### Consequences

- The active registry no longer claims data-task key or completion-receipt contracts are final.
- `trading-storage/main/templates/data_tasks/` is draft reference material, not a registered contract surface.
- Future task architecture work must create fresh reviewed migrations instead of relying on these removed rows.

## D080 - Data source interfaces use type-first source names

Date: 2026-04-29
Status: Accepted

### Context

Numbered data bundles already use number-first package and registry payload names such as `01_bundle_market_regime`. Trading-data source interfaces still used unscoped names such as `alpaca_bars`, which made source-interface directories less explicit than bundle directories.

### Decision

Use type-first source-interface names for active trading-source source directories and registry payloads: `NN_source_<semantic>`.

Current source-interface names are:

- `01_source_alpaca_bars`
- `02_source_alpaca_liquidity`
- `03_source_alpaca_news`
- `04_source_okx_crypto_market_data`
- `05_source_gdelt_news`
- `06_source_etf_holdings`
- `07_source_trading_economics_calendar_web`
- `08_source_sec_company_financials`
- `09_source_thetadata_option_selection_snapshot`
- `10_source_thetadata_option_primary_tracking`
- `11_source_thetadata_option_event_timeline`

### Consequences

- `trading-source/src/data_sources/` directories use number-first `NN_source_*` names.
- `trading-main` data-source registry payload/path values use the same names.
- Source-interface numbering is inventory/order clarity, not model-layer ownership; control-plane-facing model layers remain `data_bundle` rows.

## D081 - Rename source secret schema scope

Date: 2026-04-29
Status: Accepted

### Context

The registry used `source_secret_json` as an `applies_to` scope for canonical JSON keys in source-level secret files. That name sounded like a file kind or concrete JSON object rather than the schema scope for fields inside `/root/secrets/<source>.json` files.

### Decision

Rename the registry field scope from `source_secret_json` to `source_secret_file_schema`.

Use `source_secret_file_schema` for canonical secret-file key names such as `api_key`, `secret_key`, `passphrase`, `endpoint`, `pat`, `allowed_ip_address`, and `api_key_remark_name`.

Secret registry entries may describe actual local secret files as `source_secret_file`; the registry field scope remains `source_secret_file_schema`.

### Consequences

- Do not add new active registry rows with `applies_to=source_secret_json`.
- `source_secret_file_schema` names schema slots only; secret values remain outside Git under `/root/secrets/`.

## D082 - Helper script keys use helper-first naming

Date: 2026-04-29
Status: Accepted

### Context

Helper registry keys such as `BRAVE_SEARCH_HELPER` and `REGISTRY_EXPORT_CURRENT_CSV_HELPER` put the role token at the end, making helper rows less sortable and harder to scan as a group.

### Decision

Use helper-first script keys: `HELPER_<domain>_<action>`.

Examples:

- `HELPER_BRAVE_SEARCH`
- `HELPER_BIGQUERY_REST_QUERY`
- `HELPER_REGISTRY_EXPORT_CURRENT_CSV`
- `HELPER_REGISTRY_GET_KEY_BY_ID`
- `HELPER_REGISTRY_LOAD_SECRET_TEXT_BY_CONFIG_ID`

Use `helper_<domain>` for helper-oriented `applies_to` scopes, such as `helper_web_search`.

### Consequences

- Do not add new helper script keys ending in `_HELPER`.
- Helper script rows sort together by key.

## D083 - Prune retired calendar discovery and inactive macro references

Date: 2026-04-29
Status: Accepted

### Context

`calendar_discovery` was an older execution/web-discovery route. Current event/calendar acquisition should be represented by accepted source interfaces, especially `07_source_trading_economics_calendar_web`, not by retired discovery rows.

Inactive official macro references such as BEA, BLS, Census, FRED, and U.S. Treasury Fiscal Data also remained as `term`/secret-alias rows after provider narrowing. Keeping them active made the registry look like it still endorsed those sources.

### Decision

Remove retired `calendar_discovery` rows and inactive macro-provider references from active registry vocabulary.

Deleted active rows include:

- `CALENDAR_DISCOVERY`
- `ECONOMIC_RELEASE_CALENDAR`
- `EQUITY_EARNINGS_CALENDAR`
- `FOMC_MEETING`
- `FOMC_MINUTES`
- `FOMC_SEP`
- `FOMC_STATEMENT`
- `MACRO_RELEASE_CALENDAR`
- `ECONOMIC_RELEASE_EVENT`
- `FOMC_CALENDAR`
- `NASDAQ_EARNINGS_CALENDAR`
- `BEA`, `BLS`, `CENSUS`, `FRED`, `US_TREASURY_FISCAL_DATA`
- `BEA_SECRET_ALIAS`, `BLS_SECRET_ALIAS`, `CENSUS_SECRET_ALIAS`, `FRED_SECRET_ALIAS`

### Consequences

- Re-add any removed macro/calendar provider only through a current accepted source-interface design.
- `source_capability` rows should describe capabilities of active/current source interfaces or accepted raw-provider surfaces, not retired discovery routes.

## D084 - Layer 05 uses contract-level option snapshot rows

Date: 2026-04-29
Status: Accepted

### Context

`trading-source` Layer 05 previously wrote one option-chain snapshot row containing nested `contracts` JSON plus `contract_count`. That made the final business table a transport envelope instead of the model-facing contract comparison surface.

### Decision

`bundle_05_option_expression` is a contract-level SQL table: one row per option contract per snapshot.

The natural key is:

```text
underlying + snapshot_time + snapshot_type + option_symbol
```

The table includes `snapshot_type` (`entry`/`exit`) and explicit quote, implied-volatility, Greeks, underlying-context, expiration, right, strike, and option-symbol columns. It does not include nested `contracts` JSON or `contract_count` as active business fields.

### Consequences

- Remove active registry rows `OPTION_CONTRACT_COUNT` and `OPTION_CONTRACTS`.
- Register explicit Layer 05 timestamp/code fields such as `QUOTE_TIMESTAMP`, `IV_TIMESTAMP`, `GREEKS_TIMESTAMP`, `QUOTE_BID_EXCHANGE`, `QUOTE_ASK_EXCHANGE`, `QUOTE_BID_CONDITION`, and `QUOTE_ASK_CONDITION`.
- `run_id`, `task_id`, and write/audit timestamps remain receipt/run metadata, not accepted business-table columns.

## D085 - Rename data/strategy repositories to source/derived

Date: 2026-04-29
Status: Accepted

### Context

Chentong clarified that the former `trading-data` and `trading-strategy` names did not describe the intended dataset boundary precisely enough. The first repository is external/source-backed observed data from providers such as Alpaca, ThetaData, OKX, SEC, GDELT, issuer files, and approved web sources. The second repository is internally generated data.

### Decision

Rename and redefine the component repositories:

- `trading-data` -> `trading-source`
- `trading-strategy` -> `trading-derived`

`trading-source` owns source-backed acquisition, cleaning, normalization, validation, and source-output publication. `trading-derived` owns generated labels, samples, signals, candidates, oracle outcomes, backtest/evaluation outputs, and related derived datasets. Strategy/backtest/oracle logic may exist in `trading-derived` only as data-generation logic.

Together, `trading-source` and `trading-derived` form the training-dataset foundation for downstream `trading-model` work.

### Consequences

- Active registry repository rows, paths, `applies_to` scopes, and notes use `trading-source` and `trading-derived`.
- Source-backed bundle SQL output contracts use the `trading_source` schema.
- `trading-model` should treat training data as a composition of source observations plus derived generated rows, not as a single repository's responsibility.
- Future docs and tasks should avoid using strategy/backtest runtime as the repo-level boundary.

## D086 - Registry lives under scripts

Date: 2026-04-29
Status: Accepted

### Context

The registry is maintained by migration/export tooling and generated snapshots. Keeping `registry/` at the repository root made it look like a top-level business domain next to `docs/`, `src/`, `tests/`, and `storage/`.

### Decision

Move the registry maintenance surface under `scripts/`.

This originally included:

- `scripts/current.csv`
- `scripts/kinds/`
- `scripts/reviews/`
- `scripts/sql/schema_migrations/`
- `scripts/apply_registry_migrations.py`

The stable callable migration/export entrypoint was originally `scripts/apply_registry_migrations.py`. This flat layout was later superseded by D096.

### Consequences

- `registry/` is no longer a top-level repository directory.
- Registry docs, tests, helper defaults, and cross-repository references used flat `scripts/` paths after this decision.
- SQL migration `150_update_flattened_registry_export_helper.sql` updated the active script registry row for `HELPER_REGISTRY_EXPORT_CURRENT_CSV` after the temporary `scripts/registry/` layout was rejected as one level too deep.
- D096 later reintroduced `scripts/registry/` because `scripts/` needed room for non-registry maintenance code.

## D087 - Shared storage assets move to trading-storage main

Date: 2026-04-29
Status: Accepted

### Context

`trading-main/storage/` had become a mixed repository boundary: it held reusable templates and reviewed shared static files while `trading-main` also owned registry, helper, and governance rules. Chentong clarified that this directory can move directly to `trading-storage/main/` instead of keeping storage assets in `trading-main`.

### Decision

Retire `trading-main/storage/` and move the checked-in reusable non-code assets to `trading-storage/main/`.

Canonical paths are now:

- `trading-storage/main/templates/` for reusable drafting and implementation templates.
- `trading-storage/main/shared/` for reviewed shared static files such as `market_regime_etf_universe.csv`.

`trading-main` keeps the registry and template operating rules; `trading-storage` owns the checked-in asset location.

### Consequences

- No top-level `storage/` directory remains in `trading-main`.
- Registry rows for shared storage assets use `trading-storage/main/...` payloads and `/root/projects/trading-storage/main/...` absolute paths where direct local locators are required.
- Cross-repository code and docs should reference `trading-storage/main/shared/market_regime_etf_universe.csv` for the reviewed ETF universe CSV.
- New shared fields, statuses, type values, helpers, or vocabulary introduced by templates still route through `trading-main` SQL registry migrations.

## D088 - Register market-regime derived output as data_derived

Date: 2026-04-29
Status: Accepted

### Context

Layer 1 `MarketRegimeModel` V1 derived output was simplified to a fixed-width point-in-time table: one row every 30 minutes, containing every feature available at that snapshot time. Chentong confirmed that non-feature structural columns should be registered, while concrete generated feature columns such as `spy_return_30m` should not become individual registry rows. He also clarified that derived outputs should have their own registry kind and use the same reviewed naming pattern as `trading-source` source boundaries.

### Decision

Register `DERIVED_01_MARKET_REGIME` as an active `data_derived` row with payload `derived_01_market_regime`.

Register the only non-feature business column through the existing `SNAPSHOT_TIME` temporal field by adding the `derived_01_market_regime` scope.

Do not register concrete generated feature columns such as `spy_return_30m`, `spy_return_1d`, or future per-symbol/per-horizon expansions as individual registry rows. Govern those columns through reviewed feature-family rules/catalogs and storage contracts.

### Consequences

- The V1 derived-output boundary and `snapshot_time` column are visible in `scripts/registry/current.csv`.
- `data_derived` rows use `derived_NN_<layer>` payloads, mirroring `data_source` rows such as `source_01_market_regime`.
- For Layer 1 V1, `derived_01_market_regime` is both the derived-output boundary and the total wide table name.
- Concrete generated feature columns remain reviewed through feature-family definitions and storage contracts, not individual registry rows.
- The snapshot table does not carry row-level `feature_version`, `available_time`, `lookback_start_time`, `decision_start_time`, `decision_end_time`, `source_table`, or `source_row_count` columns.

## D089 - Source and derived boundaries use type-first names

Date: 2026-04-29
Status: Accepted

### Context

Number-first source and derived payloads such as `01_source_market_regime` mirrored earlier package naming, but physical SQL tables were already source-first, for example `source_01_market_regime`. Keeping both shapes created unnecessary translation and made SQL-safe names diverge from registry/package names.

### Decision

Use type-first names for control-plane-facing source and derived boundaries:

- `source_NN_<layer>` for `data_source` package/payload/table scopes, for example `source_01_market_regime`.
- `derived_NN_<layer>` for `data_derived` package/payload/table scopes, for example `derived_01_market_regime`.

Registry keys use the same order in uppercase, for example `SOURCE_01_MARKET_REGIME` and `DERIVED_01_MARKET_REGIME`.

### Consequences

- Active `scripts/registry/current.csv` source and derived rows use type-first keys, payloads, paths, and `applies_to` scopes.
- Historical SQL migrations remain append-only; migrations 164 and 165 record the active naming change.
- Feeds keep their existing `NN_feed_*` names unless separately reviewed.

## D090 - Merge source and derived data production into trading-data

Date: 2026-04-30
Status: Accepted

### Context

The earlier split between `trading-source` and `trading-derived` clarified a source-backed versus generated-data distinction, but the active implementation made the feed → source → feature path one continuous data-production line. Keeping separate repositories and registry kinds forced unnecessary handoff vocabulary between source construction and deterministic feature construction.

Layer 1 also clarified the preferred model-facing term: deterministic point-in-time model inputs should be called features, not derived outputs.

### Decision

Use `trading-data` as the canonical data-production repository.

`trading-data` owns:

- provider/API/web/file feed adapters (`feed_*` implementation packages);
- model-scoped source construction (`source_NN_<layer>` tables and packages);
- deterministic point-in-time feature construction (`feature_NN_<layer>` tables and packages).

`trading-model` owns model outputs, evaluation, config proposals, promotion, and rollback. The canonical Layer 1 SQL chain is:

```text
trading_data.source_01_market_regime
  -> trading_data.feature_01_market_regime
  -> trading_model.model_01_market_regime
```

The active registry uses `TRADING_DATA_REPO`, `data_feature`, and `FEATURE_01_MARKET_REGIME`. The active `data_derived` kind is retired.

### Consequences

- The old `trading-source` and `trading-derived` repositories are merged into `trading-data` and should not receive new active contracts.
- `feature_NN_<layer>` replaces `derived_NN_<layer>` for deterministic model-facing data surfaces.
- Historical migrations and older decisions remain append-only records, but active docs, registry exports, and new implementation paths should use `trading-data`, `data_source`, and `data_feature` terminology.
- Remote repository rename/deletion is an operational follow-up to align GitHub with the accepted repository boundary.


## D091 - Merge manager control plane into trading-main

Date: 2026-04-30
Status: Accepted

### Context

`trading-manager` was created as a planned control-plane repository, but it had no implementation scripts yet. Its useful content was documentation about orchestration, structured requests, lifecycle evidence, retries, recovery, manual override, and promotion routing.

Keeping that as a separate repository now adds another boundary without enough implementation weight. `trading-main` already owns global contracts, repository relationships, templates, registry names, and system-level workflow decisions, so the control-plane responsibility is more naturally part of the main platform layer until there is a concrete need to split it again.

### Decision

Merge the former `trading-manager` responsibility into `trading-main`.

`trading-main` now owns the control-plane boundary for:

- structured cross-repository request generation;
- readiness checks and dependency review;
- lifecycle routing, retries, recovery, archive/rehydrate policy, and manual override rules;
- promotion coordination from model/data evidence toward execution;
- control-plane task-key and completion-receipt contracts.

This does not make `trading-main` a component runtime repository. Data production remains in `trading-data`; storage contracts remain in `trading-storage`; model outputs/evaluation remain in `trading-model`; execution remains in `trading-execution`; dashboard rendering remains in `trading-dashboard`.

### Consequences

- Retire the active `TRADING_MANAGER_REPO` registry row.
- Active docs should refer to the `trading-main` control plane instead of a standalone `trading-manager` repository.
- Historical decisions and migrations may continue to mention `trading-manager` as append-only history.
- The remote/local `trading-manager` repository can be deleted after documentation and registry changes are pushed.
- If a future scheduler/control-plane implementation grows large enough to deserve its own repository, that split requires a new decision and registry migration.


## D092 - Rename trading-main repository to trading-manager

Date: 2026-04-30
Status: Accepted

### Context

After the unimplemented standalone `trading-manager` repository was merged into `trading-main`, the surviving repository became both the platform contract repository and the control plane. The name `trading-main` no longer described the active responsibility as directly as `trading-manager`.

The old `trading-manager` repository had already been deleted after its documentation responsibility was merged, so the repository name was available for the surviving platform/control-plane repository.

### Decision

Rename canonical `trading-main` to `trading-manager`.

The renamed `trading-manager` owns the same platform/control-plane responsibilities that were accepted in D091:

- global architecture and repository relationships;
- shared contracts, registry, templates, and helper surfaces;
- shared Python environment anchoring;
- structured request generation;
- readiness checks and lifecycle routing;
- retry/recovery/manual override policy;
- promotion coordination.

The importable helper package remains `trading_registry`; the distribution package name becomes `trading-manager-helpers`.

### Consequences

- Rename the active repo registry key from `TRADING_MAIN_REPO` to `TRADING_MANAGER_REPO`.
- Rename the registry term from `TRADING_MAIN_REGISTRY` to `TRADING_MANAGER_REGISTRY`.
- Update active docs, helper package metadata, absolute local paths, and cross-repository references from `/root/projects/trading-main` to `/root/projects/trading-manager`.
- Rename the GitHub repository `gilmore307/trading-main` to `gilmore307/trading-manager` and move the local checkout accordingly.
- Historical decisions and migrations may continue to mention `trading-main` as append-only history.

## D093 - Register generic model promotion table names

Date: 2026-04-30
Status: Accepted

### Context

`trading-model` added promotion infrastructure after the first generic governance/evaluation schema. The new promotion tables are generic across model layers and should be globally named before other repositories refer to them.

### Decision

Register the following generic `trading_model` table names as registry terms:

- `MODEL_CONFIG_VERSION_TABLE` → `model_config_version`
- `MODEL_PROMOTION_CANDIDATE_TABLE` → `model_promotion_candidate`
- `MODEL_PROMOTION_DECISION_TABLE` → `model_promotion_decision`
- `MODEL_PROMOTION_ROLLBACK_TABLE` → `model_promotion_rollback`

Concrete column registration remains deferred until real evaluation/promotion flows prove the schema stable.

### Consequences

- Promotion table names are globally stable without implying that any model has been promoted.
- Promotion candidates remain evidence-backed by `model_eval_run` in the `trading-model` schema.

## D094 - Store generated market-regime features as JSONB payload

Date: 2026-04-30
Status: Accepted

### Context

The development DB smoke test for `feature_01_market_regime` found that materializing all generated feature keys as physical PostgreSQL `DOUBLE PRECISION` columns can exceed the PostgreSQL tuple-size limit once rows become dense.

### Decision

Keep the registered table name `FEATURE_01_MARKET_REGIME` → `feature_01_market_regime`, but clarify the registry note: the table is keyed by `snapshot_time`, while generated feature values live in `feature_payload_json` JSONB and remain model-local generated keys unless separately promoted.

### Consequences

- The registry still owns the feature boundary/table name.
- Generated feature keys are not silently turned into global registry fields.
- PostgreSQL row-size limits no longer force a table-name change.


## D095 - Layer artifact names and fields use compact numeric layer prefixes

Date: 2026-05-03
Status: Accepted

The trading system has explicit model layers, and layer ownership should be visible in shared artifact and field names without maintaining separate docs/model/SQL aliases.

Accepted artifact chain pattern:

```text
source_NN_<layer_slug>
feature_NN_<layer_slug>
model_NN_<layer_slug>
model_NN_<layer_slug>_explainability
model_NN_<layer_slug>_diagnostics
```

`source` and `feature` artifacts belong to the data-production boundary. The primary `model` artifact is the narrow downstream contract. `model_explainability` owns human-review details that should not become hard downstream dependencies. `model_diagnostics` owns acceptance, monitoring, gating, freshness, missingness, baseline, refit, and no-future-leak evidence.

Layer-owned fields use compact numeric prefixes as the canonical names in docs, model-facing payloads, and SQL physical columns:

```text
1_*
2_*
```

Do not create semantic physical-column aliases such as `layer01_*` or `layer02_*`. If SQL requires quoting because a column starts with a digit, quote the compact canonical name. Generic identity, lineage, timestamp, and receipt/run metadata fields do not need a layer prefix.

Concrete shared name changes still require reviewed SQL registry migrations before other repositories hard-depend on them; this documentation clarification alone does not migrate existing registry rows.

## D096 - Group registry maintenance under scripts/registry

Date: 2026-05-03
Status: Accepted

### Context

The flat `scripts/` registry layout mixed the migration/export entrypoint, generated CSV, kind boundary files, SQL migrations, and review notes directly with the general scripts boundary. Chentong clarified that future non-registry functionality will also live under `scripts/`, so registry files need their own nested boundary.

The old `scripts/reviews/` files were also dated investigation notes. They should become durable rule files rather than growing as loose review artifacts.

### Decision

Move the registry maintenance surface under `scripts/registry/`:

- `scripts/registry/apply_registry_migrations.py`
- `scripts/registry/current.csv`
- `scripts/registry/kinds/`
- `scripts/registry/rules/`
- `scripts/registry/sql/schema_migrations/`

Rename the former review-note boundary to `rules/` and promote the active notes into one-file-per-aspect rule files:

- `kind-routing.md`
- `data-kind-contract.md`
- `model-layer-naming.md`

Per-kind boundary files remain under `scripts/registry/kinds/`; cross-kind and table-shape constraints live under `scripts/registry/rules/`.

### Consequences

- `scripts/` is available for future non-registry maintenance features without mixing registry internals into the top-level inventory.
- Registry docs, tests, helper defaults, and the registered CSV export helper use `scripts/registry/` paths.
- The SQL `kind` constraint and `scripts/registry/kinds/*.md` files remain aligned by tests.
- Rule files are normative; dated watch-list prose should be promoted, resolved, or removed instead of accumulating as ad hoc review notes.

## D097 - Layer workflow and acceptance live in layer docs

Date: 2026-05-03
Status: Accepted

### Context

The previous docs spine kept `02_workflow.md` and `03_acceptance.md` as repository-wide files while layer-specific files lived under high-number `91_` / `92_` names. That caused duplication: workflow, handoff, evidence, and acceptance are not separate from a layer's contract; they are part of the layer boundary itself.

### Decision

Use layer-first docs numbering in layer-aware trading repositories:

```text
00_scope.md
01_context.md
02_layer_01_market_regime.md
03_layer_02_sector_context.md
04_layer_03_...                 # future layer
...
80_task.md
81_decision.md
82_memory.md
90+ reference / platform guide docs
```

Delete standalone `02_workflow.md` and `03_acceptance.md` where layer files exist. Each layer file owns its workflow diagram, input/output boundary, handoff rules, diagnostics/evidence surfaces, and acceptance gates.

This pattern applies across `trading-model`, `trading-data`, `trading-storage`, and `trading-manager` for the currently accepted Layer 1 and Layer 2 boundaries. Repositories without layer-specific docs may keep component-wide workflow/acceptance files until their layer/stage boundaries are accepted.

### Consequences

- Workflow and acceptance are reviewed where the layer contract is reviewed.
- Future Layer 3+ docs can take the next numeric slots without colliding with task/decision/memory files.
- `80_`+ files own task, decision, and memory continuity.
- `90_`+ files own reference guides, architecture references, registry/helpers/templates, and similar non-layer material.
- Registry path rows that point to renamed docs require reviewed registry migrations and regenerated `scripts/registry/current.csv`.

## D098 - Durable contract promotion waits for the manager phase

Date: 2026-05-06
Status: Accepted

### Context

The model stack is still being designed layer by layer. Promoting artifact, manifest, ready-signal, request, durable receipt, shared storage root, and SQL destination contracts too early would freeze manager/storage interfaces before Layers 4-7 are understood.

### Decision

Do not promote final durable manager/storage interface contracts until all model layers are designed and the `trading-manager` development phase begins.

Current registry state-vector rows remain the reviewed naming and semantics authority for model work, but they are not a commitment that durable manager/storage request, artifact, manifest, ready-signal, receipt, or storage contracts are final.

### Consequences

- Model work continues with local/offline evidence and reviewed state-vector semantics.
- `trading-data` and `trading-storage` may keep minimal development-mode receipts and local ignored staging, but must not present them as final durable cross-repository contracts.
- When manager development begins, contract promotion should review the complete model stack at once instead of backfilling premature layer-local assumptions.

## D099 - Registry state-vector values stay limited to core scores

Date: 2026-05-06
Status: Accepted

### Context

The model state-vector contracts contain more than downstream score semantics: diagnostics, block/group names, windows, enum values, handoff/routing states, embeddings, clusters, evidence counts, and unresolved source-mapping placeholders. Registering all of those as `state_vector_value` rows made the registry look like a full model-local schema mirror instead of a shared naming authority.

### Decision

Keep `state_vector_value` registry rows limited to reviewed core scalar score tokens only.

Diagnostics, coverage/data-quality/state-quality/evidence-count fields, block/group names, window/enum values, routing/handoff/eligibility fields, embeddings, clusters, and unresolved source-mapping placeholders stay in model-local docs/contracts unless later promoted through a manager-phase durable interface review and assigned a narrower registry kind.

### Consequences

- Registry state-vector rows remain compact and focused on cross-repository score naming.
- Model-local contracts can continue documenting diagnostics and auxiliary payload structure without forcing every internal value into the registry.
- Manager-phase interface promotion can still register non-score payloads later when there is a concrete durable storage/request/API need.

## D100 - Promotion readiness and trade-risk-cap contracts start the manager phase

Date: 2026-05-07
Status: Accepted

### Context

The `trading-model` stack is now closed for Layers 1-8 model design. The next boundary is production hardening and manager/control-plane integration, not another model layer.

### Decision

Register the shared governance terms for Layer 1-8 production-promotion readiness and mandatory execution-side trade-risk caps.

Production-promotion readiness requires the full evidence package: dataset snapshot, chronological split, labels, eval run, promotion metrics, promotion candidate, thresholds, baseline comparison, split stability, leakage/no-future checks, calibration report, and decision receipt. Missing evidence or failed gates require a deferred promotion decision.

Every executable trade must include a valid `trade_risk_cap` before order construction or placement. Missing or invalid caps must reject the order; warn-only behavior is not accepted.

### Consequences

- The registry may expose the shared checklist and risk-cap vocabulary without implying any model is production-approved or any live execution is enabled.
- Model evidence remains model-owned until promoted through reviewed manager/control-plane contracts.
- Execution implementation must call equivalent risk-cap validation before broker/account mutation.

## D101 - Register trading-data closeout readiness policies

Date: 2026-05-08
Status: Accepted

### Context

`trading-data` has closed the current feed/source/feature model-input design phase, while production orchestration and durable storage contracts remain separate manager/storage work.

### Decision

Register the data closeout status, ETF holdings availability-time policy, and equity abnormal activity conservative model-standard/calibration status.

Without explicit source/task `available_time`, ETF holdings candidate-preparation rows become visible at the next regular US session open after `as_of_date`. `equity_abnormal_activity_conservative` is accepted as a conservative local standard, not as production-calibrated label evidence.

### Consequences

- Data closeout does not approve unattended production orchestration or final storage contracts.
- Production labels or promoted gates must cite reviewed calibration evidence before relying on equity abnormal activity thresholds.
- Manager/storage implementation still owns durable task, manifest, ready-signal, and storage contracts.

## D102 - Register promotion closeout decision receipts

Date: 2026-05-08
Status: Accepted

### Context

The model-design closeout and readiness checklist were not sufficient as a promotion closeout. The control-plane registry needs to expose the actual current promotion disposition.

### Decision

Register the current production-promotion closeout state:

- Layer 1 has real PostgreSQL evaluation evidence and persisted deferred decision `mpdec_d743cb5dbc8159f2`.
- Layer 2 has real PostgreSQL evaluation evidence and persisted deferred decision `mpdec_3ab83ea1f423326d`.
- Layers 3-8 have persisted blocked eval runs, `production_eval_run_available = 0` metrics, candidates, and reviewer-agent deferred decisions for missing production evaluation substrate: `mpdec_d8e027dd9b5aa939`, `mpdec_76b07ea01a3f525b`, `mpdec_9c3e19d6559ef55b`, `mpdec_b118232e76fae092`, `mpdec_fabc9c709149a698`, and `mpdec_e7448aaab1334345`.
- No production activation is approved by these rows.

### Consequences

Promotion work is no longer described as merely pending in generic terms. Every Layer 1-8 model now has a durable deferred decision receipt; Layers 3-8 receipts identify missing production evaluation substrate as the blocker.

## D103 - Register Layer 3-8 agent-reviewed promotion closeout entrypoint

Date: 2026-05-08
Status: Accepted

### Context

Layers 3-8 originally had formal blocked receipts, but Chentong clarified that they should follow the same promotion principle as Layers 1-2: the script must call the reviewer agent for the final audit before persisting the closeout decision.

### Decision

Register `REVIEW_LAYERS_03_08_PROMOTION_CLOSEOUT` as the stable callable script for Layer 3-8 promotion closeout. The script builds blocked evaluation artifacts when production eval substrate is missing, creates candidates, calls the reviewer agent, persists deferred decisions, and does not activate configs.

### Consequences

- Layers 3-8 closeout is now explicitly agent-reviewed instead of only mechanically deferred.
- The registry points to the callable script path and current reviewed decision receipts.
- Missing production eval substrate still blocks agent promotion approval; the new entrypoint changes the review path, not the outcome.

## D104 - Register Layer 3 real production-evaluation substrate without approval

Date: 2026-05-08
Status: Accepted

### Context

Layer 3 was originally grouped with Layers 4-8 as missing production-evaluation substrate. A follow-up run built real Layer 3 PostgreSQL feature/model rows, labels, metrics, and a reviewer-agent decision.

### Decision

Register `REVIEW_LAYER_03_TARGET_STATE_VECTOR_PRODUCTION_SUBSTRATE` as the stable callable Layer 3 substrate/review entrypoint and update the promotion closeout receipts so Layer 3 points to eval run `mdevrun_327616bb447ceb5b`, candidate `mpcand_1b077bca49a18dbf`, and decision `mpdec_70fef0f31847cc1c`.

This registration does not approve Layer 3 production use. The decision remains deferred because Layer 1 and Layer 2 are not production-approved/active and Layer 3 calibration evidence is missing.

### Consequences

- Layer 3 is no longer blocked for missing evaluation substrate; it is blocked for upstream agent decisions and calibration.
- Layers 4-8 remain blocked for missing production eval runs, labels, and metrics.
- No deferred decision may create a production activation row or active config pointer.

## D105 - Register manager/storage V1 handoff contracts

Date: 2026-05-08
Status: Accepted

### Context

Some remaining work does not depend on accumulated production trading data: request shape, manifest evidence, artifact references, ready signals, provider-call guardrails, and checkpoint/resume evidence can be defined now.

### Decision

Register the storage-owned V1 logical handoff contracts and hardening policies:

- `manager_request`
- `run_manifest`
- `artifact_ref`
- `ready_signal`
- provider-call guardrails policy
- checkpoint/resume policy
- data-production hardening policy

Register initial request, manifest, artifact, and ready-signal type vocabulary for data-source, data-feature, model-generate, model-evaluate, model-review, registry-snapshot, and promotion-review handoffs.

This decision defines shared vocabulary and contract shape. It does not implement physical SQL queues/storage, authorize unattended live provider calls, approve model promotion, or enable broker execution.

### Consequences

- Future manager/storage implementation must follow these V1 contract names instead of reviving local-only completion receipt drafts as final interfaces.
- `trading-data` production hardening can refer to the same request/manifest/artifact/ready-signal vocabulary without waiting for model promotion.
- `trading-model` production artifacts remain model-owned until manager/storage persistence and ready-signal implementation are accepted.

## D106 - Split durable SQL facts from retention-managed payloads

Date: 2026-05-08
Status: Accepted

### Context

The first-principles manager contract inventory includes more contract names than should become immediate first-class SQL tables. Some contracts describe durable control-plane facts that must be queryable and auditable. Others are references, payloads, or temporary evidence that can live in storage with retention rules.

### Decision

Use SQL for durable control-plane facts and audit state. Use storage for bulky payloads, transient evidence, and retention-managed files. Use pure temp scratch for run-local material that never becomes contract evidence.

The MVP SQL implementation should start with tables for:

- `manager_request`
- `input_binding`
- `run_manifest`
- `run_step`
- `artifact_ref`
- `ready_signal`

`component_ref` should initially be registry-backed fields on those SQL rows, not a separate component catalog table. Add a component catalog only when real query or lifecycle needs require it.

If a storage payload participates in a formal request, run, evaluation, review, activation, or handoff, SQL must retain durable reference metadata such as artifact id, URI, hash/fingerprint, producer run, schema reference, retention policy, and lifecycle state. Payload cleanup must not erase the audit trail that the artifact existed and was used.

### Consequences

- Contract names do not automatically imply one SQL table per contract.
- Large logs, raw provider bodies, model vector payloads, diagnostics reports, and replay bundles stay out of manager SQL and are referenced through artifact metadata.
- Storage cleanup can delete or archive payloads without breaking manager audit history.
- Later evaluation/promotion SQL tables should follow the same rule: make first-class tables only for facts with lifecycle, query, relationship, retention, or audit obligations.

## D107 - Retired provider approval gate is replaced by autonomous provider dispatch

Date: 2026-05-09
Status: Superseded by autonomous historical provider acquisition

### Context

The manager task system can plan monthly backfill requests, materialize component-readable payloads, and validate dry-run handoff shape. The first implementation introduced a reviewed provider-decision artifact before non-dry-run historical provider calls. Chentong later clarified that this contradicted the automation goal for historical/data acquisition.

### Decision

Retire the per-batch provider decision artifact for historical provider acquisition. Non-dry-run historical provider calls now move through bounded autonomous manager dispatch with explicit request ids, provider/resource controls, terminal-coverage rejection, receipts, reconcile coverage, and failure registration.

This retirement does not weaken broker/order/fill/account mutation gates, production model activation gates, or storage lifecycle mutation gates.

### Consequences

- Dry-run planning, payload materialization, and handoff validation remain safe preparation steps.
- Historical provider acquisition can progress automatically under manager controls.
- Broker/order/fill/account lifecycle remains execution-owned and cannot be enabled through provider dispatch.

## D108 - Current manager/control-plane phase is closed

Date: 2026-05-09
Status: Accepted

### Context

The manager repository now has the shared registry, MVP control-plane SQL contracts, request/receipt/task summary lifecycle, monthly backfill planning, request payload materialization, dry-run handoff validation, unified model-promotion review route, review decision/activation artifact builders, storage receipt payload reference flow, and autonomous provider dispatch gate.

### Decision

Close the current manager/control-plane design-and-MVP phase. `docs/97_manager_control_plane_closeout.md` is the authoritative closeout receipt.

No active manager-phase tasks remain. Future work is deferred until a concrete component production consumer requires it: live provider dispatch workers, durable object-store/SQL partitioning details, execution-owned broker/order/fill/account lifecycle, dashboard implementation, extra SQL tables, or a component catalog.

### Consequences

- `trading-manager` remains the control-plane owner, but it must not pretend to own component runtime implementation.
- The closeout does not approve production model activation, live broker execution, or unattended provider orchestration.
- New manager work should start from a specific consumer and acceptance gate, not from broad cleanup.

## D109 - Register price-action event overlay contract

Date: 2026-05-09
Status: Accepted

The registry owns the shared Layer 4 price-action vocabulary: `price_action` as an `event_category_type` value and canonical event tokens `false_breakout`, `false_breakdown`, `liquidity_sweep_high`, `liquidity_sweep_low`, `bull_trap`, and `bear_trap`.

The registry policy is explicit: price-action evidence is Layer 4 event-overlay evidence and optional Layer 3/5 context. It is not a new model layer, not an action signal, and not execution permission.

## D110 - Manager scheduler should automate historical training while protecting live capacity

Date: 2026-05-10
Status: Accepted

### Context

The manager should not remain a passive collection of scripts that waits for manual prompting after each step. The intended platform needs historical data acquisition, feature generation, model training, evaluation, promotion-review preparation, and maintenance to progress continuously, while future live trading monitoring and realtime order systems retain priority.

### Decision

Adopt the always-on automation scheduler policy in `docs/98_automation_scheduler.md`.

Manager-owned scheduler automation should keep safe historical work moving whenever dependencies, approvals, resource budgets, and market-hours policy allow. Historical work may use concurrency, but only after reserving capacity for live monitoring and execution. During the `09:20-16:10 ET` protection window on actual regular US equity trading days, default behavior is to pause or heavily throttle historical provider acquisition and CPU-heavy modeling work. Non-trading days must not trigger this pause merely because the wall clock is inside that time range.

Hard gates remain where they belong: historical provider acquisition runs autonomously through bounded manager dispatch, model activation is approved/deferred by an agent decision artifact, storage lifecycle mutation follows accepted lifecycle policy/protected-set checks, and broker/order/fill/account mutation remains execution-owned.

### Consequences

- The next manager phase is scheduler implementation, not manual one-task-at-a-time prompting.
- Historical training becomes background automation relative to live monitoring and execution.
- Scheduler pauses/backoff reasons must be explicit: provider wait, regular-trading-day market-hours protection, resource pressure, dependency block, provider quota, or promotion review.
- Automation authorizes only bounded historical provider calls through manager dispatch; it does not authorize model activation or broker execution by implication.

## D111 - Implement scheduler tick before live dispatch

Date: 2026-05-10
Status: Accepted

### Context

The accepted scheduler direction needs implementation without prematurely enabling provider dispatch, production model activation, or broker execution. The safest first step is a scheduler tick that proves gate behavior and executes only already-safe preparation while still treating provider acquisition as the next internal historical-training stage.

### Decision

Implement `scripts/tasks/run_automation_scheduler.py` backed by `trading_manager_tasks.scheduler` as the first scheduler work-loop increment.

The tick evaluates regular-US-equity-trading-day market-hours protection, resource pressure, and the next safe work item. In plan-only mode, it emits `manager_scheduler_decision` with explicit ready/backoff reason codes. With `--execute-safe-preparation`, it executes task-key payload materialization and handoff validation through the existing preparation path, then reports autonomous historical provider acquisition as the next internal stage. With `--execute-autonomous-provider-stages`, it may execute one bounded provider-dispatch/reconcile slice per tick while preserving model activation, storage lifecycle, and broker/account gates.

The tick must emit safety counters on every path. Safe preparation/offline paths must prove `provider_calls=0` and `dispatch_performed=false`; autonomous provider-stage paths may report bounded `provider_calls>0`, but must still prove `model_activation_performed=false`, `broker_execution_performed=false`, and storage lifecycle mutation remains false.

### Consequences

- Scheduler automation is now implemented enough to decide and perform safe offline preparation.
- Autonomous provider acquisition, receipt-driven progression, feature/model/evaluation runners, and promotion-review automation remain the next scheduler increments.
- Historical provider dispatch runs through the manager adapter; production activation still requires an approving decision artifact; broker execution remains execution-owned.

## D112 - Treat provider acquisition as an internal historical-training stage

Date: 2026-05-10
Status: Accepted

### Context

Layer 1 historical model training cannot honestly begin at feature/model code alone; it includes acquiring the required historical Alpaca bar inputs for the reviewed ETF universe. Treating those provider pulls as an external dependency would make manager passive and would contradict the accepted scheduler responsibility.

### Decision

Historical provider acquisition is part of the historical-data model-training lifecycle. `trading-manager` must plan and advance it as an internal scheduler stage: prepare requests, prepare bounded requests, dispatch provider acquisition through `trading-data`, and then continue through receipts, feature generation, model training, evaluation, and promotion-review preparation.

The manager dispatch path is mandatory for non-dry-run historical provider/API calls, but it is an autonomous workflow control, not a reason to classify data acquisition as an external requirement or manual operator task.

### Consequences

- Scheduler decisions should expose the next internal stage and required provider guardrail instead of stopping at preparation.
- Layer 1 Alpaca bar acquisition is tracked as historical-training work, while provider calls remain bounded and reviewable.
- Offline preparation, feature generation, training, and evaluation continue automatically whenever their inputs and gates are satisfied.

## D113 - Historical scheduler runtime must be resident and resumable

Date: 2026-05-10
Status: Accepted

### Context

Historical-data model training is not a chat-session task or a one-shot maintenance script. It needs production-like operational behavior: long-running background residency, restart tolerance, checkpointed continuation, single-instance safety, boot integration, logs, and explicit maintenance surfaces.

### Decision

Add a persistent historical-training scheduler runtime around the existing scheduler tick. The runtime must persist `manager_scheduler_daemon_state` after every tick, append scheduler decisions to JSONL, enforce a single-instance lock, and expose a service-manager-compatible entrypoint for always-on operation.

Host autostart is supported through reviewed templates under `deploy/`, but installing/enabling those templates is an operator action. The repository owns the runtime capability and documentation; the host owner controls activation.

### Consequences

- The historical model-training scheduler can run as a resident background daemon and resume after process restart or host reboot.
- State, lock, and decision logs live under ignored `storage/runtime/` by default and must not rely on OpenClaw chat memory.
- Duplicate daemon instances over the same state path are rejected.
- Provider calls, model activation, and broker execution remain gated exactly as before; residency does not imply permission escalation.

## D114 - Manager owns the full Layer 1-8 historical-training workflow graph

Date: 2026-05-10
Status: Accepted

### Context

The historical scheduler daemon must not remain a Layer 1-only loop. The current phase requires all eight models to be automatically orchestrable by manager for data/input preparation, training/generation, evaluation, review preparation, and maintenance, while preserving provider, activation, and broker gates.

### Decision

Add `manager_model_training_workflow_plan` as the manager-owned full-stack workflow graph. The graph covers Layers 1-8 and defines six stages per layer: data acquisition, feature/input generation, model generation, model evaluation, promotion-review preparation, and maintenance.

Layer-specific data surfaces remain honest: Layers 5-7 do not invent trading-data feature surfaces; they consume upstream model/control-plane/position-risk artifacts. Provider-backed stages run through autonomous manager dispatch; model activation remains blocked behind an approving decision artifact; broker execution remains outside manager.

### Consequences

- Scheduler decisions now carry the full eight-layer workflow plan instead of only a Layer 1 preparation summary.
- Once Layer 1 task keys exist, the scheduler advances to the internal stage `layer_01_market_regime.data_acquisition` and reports autonomous historical provider acquisition as the next guarded stage.
- The next implementation boundary is durable stage completion from provider dispatch and component receipts, not more ad hoc layer-specific scripting.

## D115 - Historical workflow progression is durable and receipt-driven

Date: 2026-05-10
Status: Accepted

### Context

A full Layer 1-8 graph is not enough by itself; the manager needs a durable checkpoint that can survive resident-daemon restarts, consume component receipts, and resume at the next safe or gated stage without human prompting.

### Decision

Add `manager_model_training_workflow_state` as the durable state checkpoint for the Layer 1-8 historical-training workflow. The state records every stage status, command, blockers, review refs, receipt refs, and artifact refs. `advance_model_training_workflow.py` refreshes the checkpoint, ingests receipts containing `manager_stage_id` / `stage_id`, records review references, and selects the next ready or guarded stage.

### Consequences

- The resident scheduler can report both the static workflow graph and current resumable progress.
- Component receipts are the accepted evidence for marking workflow stages complete.
- Review/receipt satisfaction is recorded as an artifact reference on the guarded stage; it does not itself perform provider dispatch.
- The remaining implementation boundary is an provider dispatch adapter that validates `autonomous_historical_provider_acquisition`, performs the allowed provider work, and emits receipts for this state machine.

## D116 - Provider acquisition dispatch requires explicit approved execution

Date: 2026-05-10
Status: Accepted

### Context

The manager must be able to move from safe preparation into historical provider acquisition, but provider calls remain live external calls and must not happen from ordinary scheduler planning.

### Decision

Add a narrow Layer 1 provider-dispatch adapter. `dispatch_provider_acquisition.py` validates `autonomous_historical_provider_acquisition` against the prepared Alpaca bars request set and defaults to plan-only validation. It performs provider calls only when `--execute-provider-calls` is present, and it still performs no model activation or broker execution.

### Consequences

- The scheduler can point the Layer 1 data-acquisition stage at a concrete manager script instead of a placeholder.
- Plan-only preview, provider execution, receipt capture, and reconciliation remain separate, inspectable steps.
- Downstream workflow progression remains receipt-driven through `manager_model_training_workflow_state`.

## D117 - Ready offline stages may be executed one-at-a-time after scheduler gates

Date: 2026-05-10
Status: Accepted

### Context

After provider-backed acquisition receipts unlock downstream work, feature generation, model generation, model evaluation, promotion-review preparation, and maintenance are local/offline stages. They still need controlled admission, receipts, and checkpointing; they must not share the provider-dispatch path.

### Decision

Add `execute_model_training_stage.py` and `manager_stage_execution_summary`. The executor runs only `ready` stages of safe offline types, refuses guarded stages, writes stdout/stderr logs plus a `component_completion_receipt`, and can persist successful stage progress to `manager_model_training_workflow_state`. The scheduler and daemon accept `--execute-safe-offline-stages` to admit at most one non-provider safe offline stage per tick after market/resource gates pass; Layer 1/2 provider stages are admitted separately by `--execute-autonomous-provider-stages`.

### Consequences

- Offline work can progress automatically once durable receipts make a stage ready.
- Provider calls remain isolated in guarded dispatch adapters.
- Model activation and broker execution remain outside this executor.

## D118 - Manager decides and prepares dataset expansion

Date: 2026-05-10
Status: Accepted

### Context

Historical model-training expansion should not require an operator to manually choose whether the next batch expands training, calibration, validation, test, forward holdout, or shadow-monitoring evidence. The manager already owns the Layer 1-8 training workflow, scheduler, state checkpoint, and promotion-review routing; dataset expansion selection belongs in the same control plane.

### Decision

Add `manager_dataset_expansion_plan` and `scripts/tasks/plan_dataset_expansion.py`. The planner walks model layers in dependency order, fills train -> calibration -> validation -> test minimums first, expands forward holdout when promotion evidence shows coverage/drift/split-stability/regime/baseline gaps, and selects shadow monitoring only after production approval. With `--write`, manager prepares the selected safe artifacts/payloads. For Layer 1 this means writing Alpaca ETF task-key payloads and handoff validation evidence only; provider dispatch requires explicit execution through the manager adapter.

### Consequences

- Manager now owns the decision about which dataset role/layer to expand next.
- Dataset expansion plans remain evidence artifacts, not promotion approval and not provider-call approval.
- Provider calls, model activation, and broker execution remain gated exactly as before.
- The next improvement is to feed real dataset snapshot/split/label/evaluation evidence into the planner instead of relying on absent-evidence defaults.

## D119 - Dataset expansion planning uses collected evidence

Date: 2026-05-10
Status: Accepted

### Context

The dataset expansion planner can choose the next layer/role, but absent an evidence input it conservatively defaults to missing Layer 1 train evidence. That is safe, but it is not sufficient for a resident manager: manager should inventory the actual dataset snapshot, split, label, evaluation, artifact, and ready-signal evidence before deciding which dataset role is missing.

### Decision

Add `manager_dataset_evidence` and `scripts/tasks/collect_dataset_evidence.py`. The collector reads existing model-governance and manager-control-plane evidence, summarizes per-layer/per-role coverage, records promotion gaps, and feeds the existing dataset expansion planner.

This is an evidence collection layer, not a second decision-rule system. The planner remains responsible for selecting the next expansion target from the evidence. Collection is read-only and performs no provider calls, model activation, or broker execution.

### Consequences

- Manager can determine missing train/calibration/validation/test/forward-holdout evidence from durable records instead of relying on absent-evidence defaults.
- `plan_dataset_expansion.py --collect-evidence-from-db` can collect evidence and plan in one run.
- Provider calls remain gated by `autonomous_historical_provider_acquisition`; model activation remains gated by approving `review_decision`; broker/order/fill/account mutation remains execution-owned.

## D120 - Historical sampling universe can be broader than live routing

Date: 2026-05-10
Status: Accepted

### Context

The dataset expansion planner and evidence collector should not mistake live inference routing constraints for historical-training sampling constraints. A live route may narrow candidates through upstream model gates, but historical model construction may need broader samples to learn contrast and avoid overfitting to already-selected candidates.

### Decision

Adopt the `historical training sampling universe != live inference routing universe` rule for manager-owned dataset expansion.

Manager may expand historical datasets using broader point-in-time samples than the live route would pass downstream, provided the rows preserve `available_time`/`tradeable_time`, no-future leakage, identity-safety where required, and layer-boundary constraints. Layer 3 historical expansion may sample anonymous targets outside Layer 2 selected/prioritized sector baskets while keeping Layer 2 context attached to each row.

### Consequences

- Dataset expansion planning may include broad historical samples and live-route simulation as separate evidence views.
- Layer 3 target data collection is not limited to the sectors that Layer 2 would select in live routing.
- Broader historical sampling does not authorize live routing bypass, provider-call bypass, model activation, or broker execution.

## D121 - Formal workflow progression is segmented by layer space

Date: 2026-05-10
Status: Accepted

### Context

Layers 1-2 have finite, controlled panel spaces: Layer 1 is a fixed broad-market/cross-asset panel and Layer 2 is a fixed sector/industry panel. Layers 3-7 operate over an open target-candidate space, and Layer 8 expands into an even larger option-contract/expression space. Treating all layers as a synchronized all-models-per-month loop would either block finite background panels behind downstream work or explode the open candidate space.

### Decision

Use segmented workflow progression:

- Layer 1 continues chronological month-by-month after its own month-level receipts are ready; it does not wait for downstream layers.
- Layer 2 continues chronological month-by-month once Layer 1 context exists; it does not wait for Layers 3-8.
- Layers 3-7 run target-major by default: select one target candidate and complete Layers 3 -> 4 -> 5 -> 6 -> 7 before admitting the next target candidate, unless a reviewed coverage exception is recorded.
- Layer 8 starts option-expression contract/bucket expansion only after the selected target's upstream Layer 1-7 context/target chain is complete.

### Consequences

- Finite background panels can keep accumulating historical depth.
- Open target and option spaces are controlled by serial candidate completion rather than unbounded fan-out.
- Scheduler metadata must expose each layer's progression mode and candidate axis so future admission logic can enforce the policy.
- This policy does not weaken provider-call, model-activation, or broker-execution gates.

## D122 - 2016-01 controlled information pass before widening defaults

Date: 2026-05-10
Status: Accepted

### Context

The remaining scheduler defaults need measured evidence rather than guesswork. Provider dispatch coverage, concurrency defaults, L3-L7 target queue ordering, dataset thresholds, artifact discovery, and storage lifecycle implementation all depend on real 2016-01 request/receipt/artifact behavior.

### Decision

Add `manager_controlled_information_pass` and `scripts/tasks/plan_controlled_information_pass.py` as the safe first-month information-gathering report for formal historical operation from `2016-01`.

The pass may write a report and safe preparation artifacts, including Layer 1 task-key payloads and plan-only approval validation. It must not call providers, activate models, mutate broker/execution state, or execute storage cleanup/compression/archive/delete/restore. It names the evidence required to close six open areas: provider dispatch expansion, concurrency defaults, L3-L7 target queue rules, dataset thresholds, artifact discovery, and storage lifecycle implementation.

### Consequences

- The next phase is evidence collection, not broad default hardening.
- Provider calls remain outside the information-pass boundary and still require validated `autonomous_historical_provider_acquisition` plus explicit provider-dispatch execution.
- Storage lifecycle remains dry-run/protected-set-first until artifact index and restore/protection evidence exists.

## D123 - 2016-01 Layer 1-8 safe workflow is closed without provider expansion

Date: 2026-05-11
Status: Accepted

### Context

The formal historical workflow began at `2016-01` under the no-provider continuation rule: ordinary continuation may prepare, validate, reconcile, and run local/offline stages, but provider execution runs only through explicit manager provider dispatch. Layers 1-7 reached safe/offline completion for the month. Layer 8 was blocked by the option-expression acquisition gate until the completed Layer 7 target chain could be reviewed.

### Decision

Close the current `2016-01` Layer 1-8 safe workflow section as complete for mechanism validation.

Layer 8 option-expression acquisition is closed by reviewed no-provider skip for this month because every Layer 7 row resolved to `no_trade` / `none`; there were no active target chains and therefore no warranted option-chain provider request. Layer 8 generated 279 deterministic `no_option_expression` rows from completed Layer 7 database rows. The run made zero provider calls, performed no dispatch, did not activate a model, did not perform broker/order/account mutation, and did not mutate storage lifecycle state.

Promotion decisions for Layers 1-8 remain deferred. This closeout validates workflow mechanics and safe offline progression only; it is not production model activation and not authorization to bypass manager provider-dispatch controls.

### Consequences

- The next chronological month can start from safe internal preparation and provider-dispatch review.
- If a future month has active Layer 7 target chains, Layer 8 must stop at provider-dispatch review unless manager provider dispatch is executed.
- Deferred promotion evidence remains a separate production-readiness track.
- Runtime workflow checkpoints should be treated as month-scoped evidence when moving chronologically, so a later month should use an explicit month-specific state path unless/until the scheduler owns month checkpoint rotation.

## D124 - 2016-02 workflow closeout and mechanism-hardening pass

Date: 2026-05-11
Status: Accepted

### Context

The `2016-02` historical workflow completed Layers 1-8 through safe/offline maintenance. Layer 1 and Layer 2 provider acquisition used bounded autonomous dispatch before execution; downstream Layers 3-8 advanced without additional provider calls, broker/account mutation, model activation, or storage lifecycle mutation. During the run, Layer 4 exposed a zero-row bar artifact handling gap and Layer 8 exposed a no-provider feature-stage skip gap.

### Decision

Close `2016-02` as complete for safe workflow mechanics. The final month-scoped state has no next stage, with all required stages succeeded or not applicable. Layer 7 produced only `no_trade` rows, and Layer 8 correctly produced deterministic `no_option_expression` rows without ThetaData/provider acquisition.

Accept the accompanying mechanism-hardening changes before starting `2016-03`:

- Layer 8 feature generation is mediated by `scripts/tasks/execute_layer_eight_option_feature_generation.py`, which writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data `feature_08_option_expression` after completed active-path acquisition.
- Workflow CLIs default to scheduler-owned month-scoped checkpoints: `storage/runtime/model_training_workflow_state_YYYY-MM.json`.
- Workflow state records `provider_calls_observed` separately from safe/offline `provider_calls`, so provider acquisition calls are visible without misclassifying offline stages as provider-calling stages.
- Autonomous provider dispatch no longer creates provider-dispatch reviews; bounded request ids, terminal-coverage rejection, receipts, and reconcile coverage are the control surface.

### Consequences

- `2016-03` may begin from safe internal preparation after this hardening is committed and verified.
- Production promotion remains deferred until reviewed evidence proves sufficient rows/labels, baseline improvement, split stability, no leakage, and an agent-approved promotion decision.
- Active Layer 8 provider acquisition remains guarded by bounded provider-dispatch review, terminal coverage, receipts, and reconcile coverage.
- Storage lifecycle mutation remains outside this closeout and requires lifecycle policy/protected-set execution surfaces.

## D125 - Owner-observed agent automation replaces routine manual provider guardrails

Date: 2026-05-11
Status: Accepted

### Context

Routine historical backfill work was too manually gated: provider calls still waited for a human approval step plus an explicit execution instruction, production promotion was phrased ambiguously as user approval rather than an agent evidence decision, and storage lifecycle mutation was phrased as requiring a separate approval rather than rule/policy execution. Chentong clarified the intended operating model: OpenClaw/agent automation should make bounded decisions and execute them while the owner observes and intervenes if needed. Broker/order/fill/account mutation is execution-library scope and is not part of the current historical modeling workflow.

### Decision

Adopt autonomous historical provider acquisition for the current historical modeling control plane:

- Provider data acquisition may be automatically agent-reviewed, dispatched, and reconciled when it is bounded to historical provider acquisition scope and keeps broker execution, model activation, and storage lifecycle mutation false.
- Model activation / production promotion must be decided by a script-called agent decision artifact (`agent_model_promotion_decision`) rather than a routine manual provider guardrail. The agent, not the owner, performs the approval/defer/reject decision from evidence.
- Storage lifecycle mutation must follow accepted lifecycle rules, protected-set checks, quarantine/recheck rules where applicable, and storage receipts before storage executes archive/delete/compress/restore mutation. `agent_storage_lifecycle_decision` is a policy/agent decision artifact, not a human approval prompt.
- Broker/order/fill/account mutation remains out of scope here and belongs to execution-library work.

### Consequences

- Historical provider acquisition preserves exact request-id scope, terminal-coverage rejection, dispatch receipts, and reconcile coverage, and runs autonomously while the owner can observe/intervene.
- Existing provider “manual approval required” language should be replaced in active docs/code with autonomous historical provider-acquisition language.
- Promotion decision paths remain blocked only until their script-called agent decision surfaces exist; storage lifecycle paths remain blocked only until lifecycle policy/protected-set execution surfaces exist. Neither is blocked on routine manual approval.

## D126 - 2016-03 Layer 1-8 historical workflow closed

Date: 2026-05-11
Status: Accepted

### Context

The March 2016 chronological historical workflow continued after January and February closeouts. Layer 1 and Layer 2 provider acquisition now use autonomous historical provider acquisition: bounded provider-data acquisition only, terminal-coverage rejection, reconcile coverage, and no broker/order/account mutation, model activation, or storage lifecycle mutation.

### Evidence

- Layer 1 coverage report: `storage/runtime/stage_coverage/layer_01_market_regime_data_acquisition_2016-03.json` has expected 22, ready 22, failed 0, pending 0.
- Layer 2 coverage report: `storage/runtime/stage_coverage/layer_02_sector_context_data_acquisition_2016-03.json` has expected 25, ready 25, failed 0, pending 0.
- Workflow checkpoint: `storage/runtime/model_training_workflow_state_2016-03.json` has `next_stage: null`, 42 succeeded stages, and 6 not-applicable stages.
- Layer 8 gate review: `storage/runtime/layer_08_option_expression/gate_review/layer_08_option_expression_gate_review_2016-03.json` has `status: no_provider_skip_accepted`, `total_layer_7_rows: 318`, `active_request_count: 0`, and `active_target_chain_count: 0`.
- Layer 8 feature generation has a no-provider/no-feature skip receipt at `storage/runtime/layer_08_option_expression/gate_review/layer_08_option_expression_feature_generation_no_provider_skip_receipt_2016-03.json`.

### Decision

Close the 2016-03 Layer 1-8 safe historical workflow section. March 2016 is complete for current no-broker historical modeling scope. Promotion/activation remains deferred to the script-called agent promotion decision path; storage lifecycle mutation remains deferred to the script-called agent lifecycle decision path.

## D127 - Historical modeling is system-service managed

Date: 2026-05-11
Status: Accepted

### Context

The completed 2016-01 through 2016-03 historical workflow proved the Layer 1-8 mechanics, but the operating posture was still too script-by-script. Chentong clarified that historical data/modeling should be managed by an automatic resident system service, with owner observation and intervention, rather than by chat-driven manual command chaining.

### Decision

Make the historical scheduler daemon the canonical owner of the historical data/modeling runtime. The service owns the scheduler loop, checkpoint/resume state, single-instance lock, decision log, safe preparation, safe/offline stage execution, and chronological month-cursor advancement. Manual CLI/script invocation remains available only for inspection, repair, smoke testing, or emergency intervention.

The service may continue safe/offline work automatically and may advance from one completed YYYY-MM month to the next under the chronological-forward policy. Provider acquisition now runs autonomously with terminal-coverage guards, dispatch receipts, and reconcile coverage. Model activation is decided by `agent_model_promotion_decision`; storage lifecycle mutation follows lifecycle policy/protected-set checks with decision/receipt evidence; broker/order/fill/account mutation remains out of scope.

### Consequences

- The default runtime is `trading-manager-historical-scheduler.service` / `run_automation_scheduler_daemon.py`, not ad hoc script sequencing.
- Runtime state includes service-management markers and a durable month cursor.
- A terminal month workflow emits `month_workflow_complete`; the daemon may then advance the cursor to the next chronological month.
- Manual commands should be documented and treated as fallback/debug surfaces.

## D128 - Service selects next historical work without owner continuation prompts

Date: 2026-05-11
Status: Accepted

### Context

After accepting the system-service runtime posture, Chentong clarified that service startup should not wait for the owner to say where to continue. The service should review completed work, inspect planned/open workflow state, determine the next safe task, and begin it under existing gates.

### Decision

The historical scheduler daemon must automatically select its next historical work item at service start. It reviews month-scoped `manager_model_training_workflow_state` checkpoints, resumes the earliest open month if one exists, otherwise advances to the next chronological month after the latest completed checkpoint, and falls back to the configured bootstrap month only when no checkpoint evidence exists.

The selected month is then evaluated against the maintained Layer 1-8 workflow plan and normal scheduler gates. This does not authorize provider calls, model activation, storage lifecycle mutation, or broker/account mutation outside their accepted agent-decision boundaries.

### Consequences

- Operators enable the service; they do not tell it whether to continue at 2016-04 or another month.
- Runtime state records automatic work-selection evidence: completed months, open months, and the selection reason.
- Manual month arguments remain bootstrap/fallback defaults, not routine continuation instructions.

## D129 - Historical scheduler system hardening status surface

### Context
After accepting the service-owned runtime and automatic next-work selection, Chentong asked whether system-level todos were gone and then requested that the remaining system-level items be solved in one pass. The remaining risk was not another manual workflow step; it was lack of a single read-only surface that proves service readiness, selected work, current stage/blocker, latest decision, provider posture, failure evidence, and deferred mutation boundaries.

### Decision
Add `manager_historical_scheduler_status` as the canonical read-only status surface for the historical scheduler service. The status command inspects daemon state, decision logs, workflow checkpoints, lock state, deployment templates, local failure evidence, and explicit gated-scope states without mutating runtime state.

`inspect_historical_scheduler_status.py` is the normal operator inspection command after host activation. It reports the next selected month when daemon state does not exist yet, confirms required systemd/runtime flags, surfaces stale locks, summarizes the latest scheduler decision and provider gate posture, and makes model activation, storage lifecycle mutation, and broker/order/account mutation visible as explicitly gated or out-of-scope states rather than hidden todos.

### Implications
- System-level service-control and observability work is closed for supervised historical operation.
- Host-level install/enable remains an explicit operator action; committed code/templates/status checks do not install or start services.
- Provider expansion beyond current adapters remains future source-specific extension work, not a missing generic scheduler mechanism.
- Production model activation still requires an agent-authored `agent_model_promotion_decision`; storage lifecycle mutation still requires accepted lifecycle rules, storage-owned protected checks, and receipts, with `agent_storage_lifecycle_decision` serving as policy/agent decision evidence rather than owner approval; broker/order/fill/account mutation remains outside historical modeling.

## D130 - Realtime shadow handoff receipts are manager-visible but non-mutating

Date: 2026-05-11
Status: Accepted

### Context

`trading-execution` can now build realtime feature/model-input snapshots, and `trading-model` can build fixture/shadow route plans from those inputs. Manager needs visibility into that cross-repository handoff without treating it as production model activation or execution authority.

### Decision

Add `manager_realtime_shadow_handoff_control_plane_bundle` as the manager-visible receipt/normalization surface for realtime shadow decision handoffs. It validates the paired `execution_model_decision_input_snapshot` and `model_realtime_decision_route_plan`, emits a standard component completion receipt, and normalizes that receipt into run/artifact/ready rows for task-summary consumers.

Add a full rehearsal path that can build execution-side realtime adapter/capture/feature/model-input fixture artifacts, route them through the model-side realtime decision route planner, and normalize the manager receipt in one command.

The handoff remains fixture/shadow only. It performs no provider calls, model activation, production decision activation, broker calls, order construction, persistence by default, or account mutation.

### Consequences

- Realtime shadow handoff progress can be observed through manager control-plane rows once a durable receipt URI is accepted.
- The receipt does not bypass promotion review, production activation, or execution gates.
- Generic receipt persistence remains an explicit follow-up action, not an automatic side effect of validation.

## D131 - Formal realtime integration separates provider observe, manager persistence, model activation, and execution mutation

Date: 2026-05-11
Status: Accepted

### Context

Fixture-only realtime scaffolds are not enough for formal integration. At the same time, a single live switch would be unsafe because read-only provider observation, manager SQL persistence, model/production activation, order construction, broker execution, and account mutation have different review and rollback requirements.

### Decision

Formal realtime integration begins with two explicit live paths:

- `realtime_live_observe_approval` permits bounded read-only provider market-data observation in `trading-execution`.
- `record_realtime_shadow_handoff.py --persist-normalized-rows` permits explicit manager SQL persistence of normalized realtime shadow handoff run/artifact/ready rows when a reviewed durable receipt/database context exists.

These paths do not imply model activation or broker authority. Production model activation still requires the accepted model-promotion decision path. Broker order construction, execution, fill/reconcile, and account mutation require separate execution-owned risk, idempotency, receipt, and reconcile gates.

### Consequences

- Provider observation and manager visibility are no longer fixture-only when their explicit gates are supplied.
- Manager persistence is opt-in and reviewable instead of hidden behind validation.
- Model activation and broker/account mutation remain separate formal integration stages, not accidental consequences of realtime observation.

## D132 - Realtime monitoring runtime is execution-owned, not manager-controlled

Date: 2026-05-11
Status: Accepted

### Context

The realtime market monitor and the historical modeling scheduler have different safety and availability requirements. Chentong clarified that realtime monitoring should be isolated from the historical modeling system and should not be controlled by `trading-manager`.

### Decision

Realtime monitoring runtime control belongs to `trading-execution`. This includes live observe process lifecycle, provider stream/session lifecycle, subscriptions, throttling, reconnect/backoff, runtime health, and monitoring-specific capacity policy.

`trading-manager` remains the owner of historical modeling orchestration and shared registry/contract naming. It may consume execution-produced append-only realtime receipts, coverage summaries, shadow handoff artifacts, and mature validation evidence, including explicit manager persistence of normalized receipt rows when reviewed. It must not start, stop, schedule, throttle, reconnect, or otherwise control realtime provider monitoring processes.

### Consequences

- Historical scheduler pauses/restarts/backlogs must not interrupt live monitoring.
- Manager may reserve capacity for realtime systems and back off historical work, but that is priority protection, not runtime ownership.
- Realtime monitor operational health belongs in execution-owned status/heartbeat surfaces.
- Shared contracts can still be registered through `trading-manager`; registration and receipt visibility do not imply manager runtime control.

## D133 - Realtime monitoring measures decision correctness, not historical test rows

Date: 2026-05-11
Status: Accepted

### Context

Realtime monitoring can generate a large volume of market observations. Chentong clarified that using those rows to build historical test/holdout datasets is unnecessary because historical backfill will eventually advance to the same calendar period, and heavy realtime-side dataset processing would increase monitoring burden.

### Decision

Realtime monitoring should measure model decision effectiveness with lightweight online metrics. The accepted monitoring evidence is the model decision/output made at a point in time, the relevant model/config refs, the evaluation horizon, the matured outcome label/ref, correctness status, and aggregate accuracy/hit-rate/error metrics.

Realtime monitor output must not be treated as the default source for historical test rows, historical forward-holdout rows, or training rows. Historical train/calibration/validation/test/forward-holdout splits remain owned by the historical data/modeling pipeline as backfill catches up.

### Consequences

- Realtime monitoring stays operationally light and focused on live/shadow decision quality.
- Historical modeling remains responsible for reviewed dataset snapshots/splits.
- Manager may consume realtime accuracy/effectiveness summaries for promotion review, drift review, trust reduction, or retraining planning.
- Realtime effectiveness metrics do not authorize model activation, order construction, broker submission, account mutation, or historical dataset rewrites.


## D134 - Model promotion is agent-approved; storage lifecycle is rule-executed

Date: 2026-05-11
Status: Accepted

### Context

Chentong clarified that the remaining historical-system boundaries should not regress into owner approval prompts. `agent_model_promotion_decision` exists so the agent can approve, defer, reject, revoke, or supersede model activation from evidence. Storage lifecycle already has accepted lifecycle policy, protected-set rules, quarantine/recheck expectations, and storage receipts, so routine lifecycle work should execute by those rules rather than wait for owner approval.

### Decision

Production model activation remains blocked until the agent emits `agent_model_promotion_decision` and only an agent-approved decision can produce `activation_record`. The owner observes and can intervene, but the normal approval actor is the agent decision surface.

Storage lifecycle mutation is rule-executed: manager may schedule `storage_lifecycle_request`; lifecycle policy, protected-set checks, quarantine/recheck rules where applicable, and storage receipts decide whether `trading-storage` may compress, archive, restore, detach/drop, or delete. `agent_storage_lifecycle_decision` remains useful as policy/agent decision evidence when a lifecycle request is evaluated, but it is not a human approval prompt. Ambiguous, policy-missing, protected-set-failing, or high-risk destructive cases must defer/escalate instead of executing.

### Consequences

- Historical automation can keep moving without asking Chentong to approve routine promotion-review or lifecycle plumbing.
- Model activation still cannot happen from a generic review, metric, ready signal, or scheduler tick; it needs the agent promotion decision plus activation record.
- Storage lifecycle execution remains protected by deterministic rules, protected-set clearance, receipts, tombstones/manifests, and restore evidence rather than chat approval.
- Broker/order/fill/account mutation remains execution-owned and outside historical modeling automation.

## D130 - Route server-wide errors through a unified agent error handoff

Date: 2026-05-13

### Decision

All server-side workflows that need automated diagnosis or repair should call the manager-owned `call_agent_for_error.py` entrypoint rather than inventing local error-agent paths. The contract is server-wide, not model-training-specific: callers provide component/repo/scope, command, exit code, bounded stdout/stderr refs or excerpts, and evidence refs.

The entrypoint produces `server_error_agent_request` and `agent_error_diagnosis` artifacts. It may call an agent runner only when a reviewed runner command is explicitly configured; otherwise it queues durable request/diagnosis artifacts for the operator/agent runtime to consume.

### Rationale

A single error-agent boundary prevents each component from building inconsistent diagnosis/repair behavior, preserves evidence shape, and keeps safety restrictions centralized.

### Consequences

- Model training, provider acquisition, storage refresh, dashboard refresh, realtime evidence ingestion, service scripts, and future server jobs should use this entrypoint when they want agent diagnosis/repair.
- Agent-assisted repair remains bounded to internal reversible work unless a separate provider, storage lifecycle, service-control, package-change, or broker/account approval path exists.
- Failure registration and dashboard surfaces may link to these artifacts as diagnosis evidence instead of embedding ad hoc logs.

## D131 - Notify the reviewed Discord channel for server error handoffs

Date: 2026-05-13

### Decision

The unified server-wide error handoff should notify the owner-facing Discord channel when an error request is created. The reviewed destination for this host is Discord server `1480186849241731084`, channel `1504100135200620665`, addressed through OpenClaw message delivery as `channel:1504100135200620665`.

### Rationale

Error artifacts alone are too passive for unattended server operation. Discord alerting gives the owner immediate visibility while preserving durable diagnosis evidence in storage.

### Consequences

- `call_agent_for_error.py` supports `--notify-discord` and Discord target overrides.
- Resident services can enable notifications with `MANAGER_AGENT_ERROR_NOTIFY_DISCORD=true` and `MANAGER_AGENT_ERROR_DISCORD_TARGET=channel:1504100135200620665`.
- The historical scheduler daemon wrapper routes fatal service-level exceptions through the same handoff before exiting non-zero.
- Discord notification is best-effort and must not block artifact creation, diagnosis queuing, or safe failure handling.

## D132 - Assign human-facing numbers to server errors

Date: 2026-05-13

### Decision

Every error routed through the unified server-wide handoff receives a monotonic human-facing reference such as `ERR-000001`. The durable source is `storage/runtime/agent_error_handling/server_error_catalog.jsonl`; `request_id` remains the machine-stable artifact id.

### Rationale

Long hashed request ids are unsuitable for Discord/chat follow-up. A compact error number lets the owner say "ERR-000123" and have the manager, dashboard, and assistant resolve the exact request, diagnosis, logs, and evidence refs.

### Consequences

- `server_error_catalog.jsonl` is append-only and protected by a local lock during assignment.
- Discord alerts include `Error No: ERR-......`.
- Stage execution summaries carry `agent_error_number` and `agent_error_ref` when a failed stage creates an error handoff.
- `scripts/tasks/list_agent_errors.py` lists recent catalog rows or filters by `--error-ref`.

## D133 - Recover dead-PID scheduler locks immediately

Date: 2026-05-13

### Decision

The historical scheduler daemon may immediately replace a lock file when the lock records a PID and that process no longer exists. The stale-age threshold remains only for malformed locks that do not identify a dead owner.

### Rationale

Dashboard status already classifies a lock with a non-running PID as stale. Keeping that lock until the generic age threshold expires prevents systemd recovery and creates repeated error notifications without protecting an active daemon.

### Consequences

- Duplicate daemon protection remains strict when the recorded PID is still running.
- Recent malformed locks still require the stale-age threshold before replacement.
- Dead-PID locks no longer block normal service restart/recovery.

## D134 - Enable bounded auto-repair, timestamps, and deduplication for server errors

Date: 2026-05-13

### Decision

The server-wide error handoff should run a reviewed deterministic safe-repair runner when configured. The initial allowed repair class is scheduler dead-PID lock removal only. Alerts must include occurrence/record timestamps, and duplicate errors with the same fingerprint inside the dedup window reuse the same `ERR-......` number and suppress repeated Discord notifications by default.

### Rationale

Notification without repair is not enough for unattended operation. At the same time, automatic repair must stay bounded: no provider calls, broker/account mutation, secret exposure, package changes, or arbitrary shell execution. Deduplication prevents restart loops from producing alert spam and excessive error numbers.

### Consequences

- `MANAGER_AGENT_ERROR_AUTOCALL=true` enables the reviewed runner for service errors.
- `MANAGER_AGENT_ERROR_RUNNER_COMMAND=/usr/bin/python3 /root/projects/trading-manager/scripts/tasks/run_safe_error_repair.py` is the configured runner.
- `MANAGER_AGENT_ERROR_DEDUP_SECONDS=3600` is the default dedup window.
- Duplicate catalog rows use `server_error_catalog_occurrence` and preserve the original owner-facing error ref.
- Unknown errors still create numbered artifacts and notifications but do not perform automated mutation.

## D135 - Publish sanitized historical task timeline for dashboard Tasks

Date: 2026-05-13

### Decision

`historical_task_progress_summary.chart_payload` includes a sanitized `task_timeline` derived by the manager semantic producer from the active workflow checkpoint. The dashboard Tasks page consumes that list to show past, current, and future operational stages.

### Rationale

The dashboard must remain read-only and storage-hosted; it should not parse raw workflow checkpoint files directly. A manager-owned summary can expose owner-facing stage facts while preserving internal evidence boundaries.

### Consequences

- Tasks can show data-acquisition/feature-generation/model-generation/evaluation-level progress.
- Model-specific aggregate progress and coverage cards can move to Models.
- Raw command arrays, full receipt refs, and internal workflow state remain hidden unless surfaced through diagnostics.

## D136 - Timeline rows include month grouping and compact details

Date: 2026-05-13

### Decision

Each `historical_task_progress_summary.chart_payload.task_timeline` row represents the finest dashboard task unit: historical month plus layer plus operational stage/work type. Rows include a `month` field for grouping and a compact `detail` object for expandable dashboard display. The detail object may include blockers, receipt references/counts, safe-execution posture, matching stage-coverage progress, and the latest execution result when it belongs to that row.

### Rationale

Chentong clarified that 2016-01 and 2016-02 should be understood as separate month groupings/batches under the same broader historical workflow, while the visible task rows should be the finest child tasks that can be completed, blocked, current, failed, skipped, or future. The dashboard also needs a read-only way to expand the current task and inspect progress without turning into a raw workflow/checkpoint browser.

### Consequences

- The dashboard can group task rows by month while preserving row-level completion state.
- Expandable details remain sanitized and manager-owned; the dashboard does not query raw workflow checkpoint internals.
- The current task can show concrete progress details when stage coverage is attached to the read model.

## D137 - Dashboard task timeline includes completed historical months

Date: 2026-05-13
Status: Accepted

### Context

The first month-grouped task timeline emitted only the active scheduler month. That made the dashboard show only the current month even though the daemon records completed historical months and the runtime keeps month-specific workflow-state files.

### Decision

The manager dashboard read model must include completed month workflow states from the daemon `last_completed_months` list before adding the active/current month. The current month remains the only month that can expose the `current` task state, latest execution attachment, or current stage-coverage progress.

### Consequences

- Dashboard consumers can show past/current/future child tasks across historical months without reading raw runtime files directly.
- Missing completed-month state files are skipped rather than fabricating completed rows.
- The active month remains visually distinct and operationally current.

## D138 - Dashboard task rows expose lifecycle timestamps

Date: 2026-05-13
Status: Accepted

### Context

Chentong asked to see each task's generated time, start time, end time, and status update time so the dashboard can show whether a task is actively moving or has been sitting unchanged.

### Decision

`historical_task_progress_summary.chart_payload.task_timeline` rows expose sanitized lifecycle timestamps when available: `created_at_utc`, `started_at_utc`, `ended_at_utc`, and `status_updated_at_utc`. The manager read-model producer derives these from workflow stage metadata and attached manager-owned receipt timing metadata without making the dashboard read raw workflow or receipt files directly. Existing `updated_at_utc` remains for compatibility.

### Consequences

- Dashboard task detail panels can show generated, started, ended, and status-updated timestamps per child task.
- Missing timestamps are rendered as not recorded rather than inferred. Past terminal rows without recorded lifecycle metadata are not backfilled from status-update timestamps; future rows must record lifecycle metadata as scheduler/workflow state changes happen.
- Dashboard remains read-only and storage-hosted; timestamp enrichment stays in the manager semantic producer.

## D139 - Use bounded dynamic provider worker threads for historical acquisition

Date: 2026-05-13
Status: Accepted

### Context

Server load and memory usage stayed very low while historical acquisition work remained queued. Chentong asked to increase utilization with direct multithreading and to choose the thread count dynamically from load and memory.

### Decision

Historical provider data-acquisition slices may execute multiple provider request commands concurrently through bounded worker threads. The scheduler still selects one workflow stage per tick, but provider-stage execution can process a configured request batch with a dynamic worker count selected from request count, configured max workers, current 1-minute load, CPU count, available memory, per-worker memory budget, and reserved memory. The initial service defaults are a 60-second tick, next-request limit 12, and maximum 4 provider worker threads.

### Consequences

- Provider acquisition can better use the host when load and memory headroom are available.
- Existing hard boundaries remain: no broker/account mutation, no model activation, no unbounded provider dispatch, no duplicate terminal request execution, and failures still flow through receipts, coverage, and failure registration.
- Current Status exposes a scheduler parallelism/thread card so the owner can see selected workers, max workers, request batch size, tick interval, load target, and memory budget.

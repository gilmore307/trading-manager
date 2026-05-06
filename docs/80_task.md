# Task

## Active Tasks

- None.

## Queued Tasks

- None that should be started before the remaining model layers are designed.

## Deferred Until Manager Phase

- Define data task key/request schemas, completion-receipt schemas, artifact references, manifests, ready signals, request schemas, shared storage root, and migration criteria from legacy local data-production staging files into durable `trading-storage` SQL/artifact contracts.
- Promote concrete templates from `trading-storage/main/templates/contracts/` only after all model layers are designed and the `trading-manager` development phase begins.
- Until then, keep current registry rows as reviewed naming/state-vector semantics, not as final durable manager/storage interface contracts.

## Open Gaps

- None for the current model-design phase; durable manager/storage interface gaps are intentionally deferred above.

## Recently Accepted

- Registered all current `task_key.json` and `completion_receipt.json` field names as `kind=field` rows.
- Updated task key/receipt templates so stable task keys can have multiple run entries in completion receipts.
- Simplified `task_key.json` and `completion_receipt.json` to minimal operational fields.
- Updated data task templates so sources default to one `pipeline.py` with fetch/clean/save/receipt step functions.
- Added data task templates for task keys, source docs, fetch/clean/save specs, completion receipts, and fixture policy.
- Registered the earlier draft development-storage-root contract, later pruned it from active registry rows, and kept local `storage/` as an ignored legacy runtime path for unmigrated source sources.
- Registered control-plane-driven historical data task workflow terms for task key files and completion receipts.
- Registered FOMC calendar, official macro release calendar discovery, and ETF issuer holdings source terms.
- Registered U.S. Treasury Fiscal Data as an open/no-key provider term with official documentation path.
- Added official documentation URLs to registered provider term paths while keeping secret config paths pointed at local JSON files.
- Registered FRED, Census, BEA, and BLS source-level secret aliases for macro/economic data acquisition.
- Registered ThetaData provider terminology for options data; credentials/JAR placement deferred.
- Registered Alpaca source-level secret alias for stock/ETF bars, quotes, trades, and news data acquisition.
- Consolidated OKX and GitHub secret handling to one JSON secret file per source and registered source-secret JSON field names.
- Moved OKX allowlisted IPv4 and API key remark into the source-level OKX JSON secret file contract.
- Defined test-script boundary: test scripts stay out of registry `script` rows and are inventoried in their test-directory README.
- Removed registry kind vocabulary validators from the runtime helper package; tests now compare SQL kind constraints with `scripts/registry/kinds/*.md`.
- Registered legal `payload_format` values as `payload_format` registry rows and removed payload-format validators from the runtime helper surface.
- Expanded registry `payload_format` beyond `text`/`file` and backfilled current rows with narrower formats.
- Removed the old non-Python registry helper implementation; helper code is now Python-only.
- Added formal Python registry helper package and pointed registry script rows at Python helper methods.
- Created initial docs spines for component repositories including the now-merged manager, storage, derived, model, execution, and dashboard repositories.
- Defined repository visibility policy: trading repositories stay private unless the owner explicitly approves a visibility change.
- Defined helper distribution boundary: cross-repository runtime helpers use the Python helper package.
- Defined shared environment baseline: Python 3.12, `.venv`, `pip`, and reviewed `requirements.txt`.
- Split `trading-manager` platform-function guides into `docs/90_helpers.md`, `docs/91_registry.md`, and `docs/92_templates.md`.
- Added scripts/platform guide docs so platform-specific rules have focused guides separate from task/decision/memory and layer workflow docs.
- Moved registry kind boundary files into `scripts/registry/kinds/`; `scripts/registry/rules/` remains for review artifacts.
- Registered the active trading repositories as `repo` rows in `scripts/registry/current.csv`; later merged source/derived data-production boundaries back into `trading-data`.
- Registered `HELPER_REGISTRY_EXPORT_CURRENT_CSV` for regenerating `scripts/registry/current.csv`.
- Standardized registered helper surface to four id-only helpers: key, payload, path, and secret text by config id.
- Backfilled `applies_to` for every active field registry entry and added a SQL check constraint to prevent blank field scopes.
- Registered id-first path helper methods in the SQL registry.
- Added nullable registry `applies_to` column for field usage/source scope.
- Updated secret resolver helper to prefer config ids; later standardized the public helper surface to id-input only.
- Added nullable registry `path` column and id-first path helper APIs.
- Removed `path` as a registry kind and merged standalone root-path entries into their owning entity rows.
- Restored `TAILSCALE` and `SMB` as active `term` entries.
- Moved artifact/manifest/ready-signal/request contract placeholders from `docs/` to `trading-storage/main/templates/contracts/`.
- Added registry kind boundaries for `artifact_type`, `manifest_type`, `ready_signal_type`, and `request_type`.
- Removed canceled-project registry entries and regenerated `scripts/registry/current.csv`.
- Corrected registry shape so Markdown kind files define kind boundaries while SQL migrations own concrete entries.
- Added SQL-to-CSV registry snapshot generation at `scripts/registry/current.csv`.
- Added registry kind boundary overlap review.
- Migrated former standalone registry into `trading-manager`: SQL migrations own concrete entries, Markdown kind files own boundaries.

- Defined initial `trading-manager` docs spine and pushed initial trading repositories to GitHub.
- Initial repository list approved:
  - `trading-manager`
  - `trading-data`
  - `trading-storage`
  - `trading-model`
  - `trading-execution`
  - `trading-dashboard`

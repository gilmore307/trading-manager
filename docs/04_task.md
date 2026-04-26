# Task

## Active Tasks

- None.

## Queued Tasks

- None that can be completed safely without cross-repository contract coordination.

## Waiting On Cross-Repository Coordination

- Define concrete artifact, manifest, ready-signal, and request schemas from `templates/contracts/`.
- Promote concrete template schemas after artifact, manifest, ready-signal, and request contracts are accepted.
- Define shared storage root with `trading-storage`.

## Open Gaps

- Exact artifact reference format.
- Exact manifest schema.
- Exact ready-signal schema.
- Exact request schema.
- Exact shared storage root.

## Recently Accepted

- Created initial docs spines for remaining component repositories: manager, storage, strategy, model, execution, and dashboard.
- Defined repository visibility policy: trading repositories stay private unless the owner explicitly approves a visibility change.
- Defined helper distribution boundary: current JS helpers are internal-only; cross-repository runtime helpers need an accepted package strategy.
- Defined shared environment baseline: Python 3.12, `.venv`, `pip`, and reviewed `requirements.txt`.
- Clarified that current JS registry helpers are internal `trading-main` maintenance/test helpers, not a formal cross-repository runtime package.
- Split `trading-main` platform-function guides into `docs/07_helpers.md`, `docs/08_registry.md`, and `docs/09_templates.md`.
- Added registry/platform guide docs so `00_scope.md` through `06_memory.md` remain project-wide while platform-specific rules have focused guides.
- Moved registry kind boundary files into `registry/kinds/`; `registry/reviews/` remains for review artifacts.
- Registered all eight trading repositories as `repo` rows in `registry/current.csv`.
- Registered `REGISTRY_EXPORT_CURRENT_CSV_HELPER` for regenerating `registry/current.csv`.
- Standardized registered helper surface to four id-only helpers: key, payload, path, and secret text by config id.
- Backfilled `applies_to` for every active field registry entry and added a SQL check constraint to prevent blank field scopes.
- Registered id-first path helper methods in the SQL registry.
- Added nullable registry `applies_to` column for field usage/source scope.
- Updated secret resolver helper to prefer config ids; later standardized the public helper surface to id-input only.
- Added nullable registry `path` column and id-first path helper APIs.
- Removed `path` as a registry kind and merged standalone root-path entries into their owning entity rows.
- Restored `TAILSCALE` and `SMB` as active `term` entries.
- Moved artifact/manifest/ready-signal/request contract placeholders from `docs/` to `templates/contracts/`.
- Added registry kind boundaries for `artifact_type`, `manifest_type`, `ready_signal_type`, and `request_type`.
- Removed canceled-project registry entries and regenerated `registry/current.csv`.
- Corrected registry shape so Markdown kind files define kind boundaries while SQL migrations own concrete entries.
- Added SQL-to-CSV registry snapshot generation at `registry/current.csv`.
- Added registry kind boundary overlap review.
- Migrated former standalone registry into `trading-main`: SQL migrations own concrete entries, Markdown kind files own boundaries.

- Defined initial `trading-main` docs spine and pushed initial trading repositories to GitHub.
- Initial repository list approved:
  - `trading-main`
  - `trading-manager`
  - `trading-data`
  - `trading-storage`
  - `trading-strategy`
  - `trading-model`
  - `trading-execution`
  - `trading-dashboard`

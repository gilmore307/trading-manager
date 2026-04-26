# Task

## Active Tasks

- None.

## Queued Tasks

- Define concrete artifact, manifest, ready-signal, and request schemas from `templates/contracts/`.
- Define shared environment runtime version and package manager.
- Define initial `templates/` files.
- Define initial `helpers/` package boundary.
- Create component repository docs spines.

## Open Gaps

- Exact artifact reference format.
- Exact manifest schema.
- Exact ready-signal schema.
- Exact request schema.
- Exact shared storage root.
- Exact shared environment dependency policy.
- GitHub repository visibility policy after initial private creation.

## Recently Accepted

- Registered all eight trading repositories as `repo` rows in `registry/current.csv`.
- Registered `REGISTRY_EXPORT_CURRENT_CSV_HELPER` for regenerating `registry/current.csv`.
- Standardized registered helper surface to four id-only helpers: key, payload, path, and secret text by config id.
- Backfilled `applies_to` for every active field registry entry and added a SQL check constraint to prevent blank field scopes.
- Registered id-first path helper methods in the SQL registry.
- Added nullable registry `applies_to` column for field usage/source scope.
- Updated secret resolver helper to prefer config ids and mark config-key lookups unsafe.
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

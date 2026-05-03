# Registry Rules

This directory owns normative registry rules that constrain SQL row shape, kind routing, and shared naming decisions.

Rules here are not loose review notes. Each Markdown file should own one aspect of registry governance and should be kept current when the SQL table, allowed kinds, or cross-repository naming contract changes.

## Files

- `kind-routing.md` — cross-kind tie-breakers when a row could plausibly fit more than one `kind`.
- `data-kind-contract.md` — requirements for active `data_kind` rows and source/feed/final-shape separation.
- `model-layer-naming.md` — registry naming rules for model-layer source, feature, and model surfaces.

## Boundary

- Per-kind scope/range/rejection definitions live in `../kinds/<kind>.md`.
- Concrete rows live in SQL migrations under `../sql/schema_migrations/` and the generated snapshot `../current.csv`.
- Historical investigation evidence may be summarized here only when it supports a continuing rule; dated watch-list prose should be promoted, resolved, or deleted.

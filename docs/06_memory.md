# Memory

## Durable Local Notes

- `trading-main` should stay strict: global docs, contracts, registry, templates, shared helpers, plus the gitignored shared environment anchor.
- Do not let `trading-main` become a dumping ground for component-local implementation detail.
- Keep trading statuses and registrable fields in `trading-main/registry/`, not scattered through docs.
- The market-state contamination rule is a core system invariant.

- Registry Markdown kind files under `registry/kinds/` define boundaries only; concrete entries live in SQL, GitHub visibility comes from generated `registry/current.csv`, and registry operating rules live in `docs/08_registry.md`.
- Contract drafting templates belong under `templates/contracts/`, not as numbered docs after `06_memory.md`; `07_helpers.md`, `08_registry.md`, and `09_templates.md` are approved platform-function guides after the project-wide docs.
- Stale canceled-project registry entries were removed because GitHub history is the restore path.
- Registry ids are stable automation references; keys are human-readable and unsafe for durable automation dereferencing.
- Registry `path` is a nullable column for direct locators, not a registry kind.
- Every field registry entry must have non-empty `applies_to`; multiple scopes use semicolon-separated values.
- Public helper methods are individually registered as script entries when they are part of the approved shared helper surface.
- Registered helper APIs are id-only: get key, payload, path, or secret text by stable registry id.
- Registry keys are output/display labels, not helper inputs.

- `docs/07_helpers.md`, `docs/08_registry.md`, and `docs/09_templates.md` are platform-function guides for `trading-main`; `00_scope.md` through `06_memory.md` remain project-wide.
- Future global helpers, reusable templates, and shared fields/status/type values discovered in component work must be recorded through `trading-main` before they become cross-repository contracts.
- Official registry helper runtime surface is the Python `trading_registry` package under `helpers/python/`; the older non-Python helper implementation was removed.
- Shared environment baseline is Python 3.12 at `/root/projects/trading-main/.venv`, installed with `pip` from root `requirements.txt`.
- Trading repositories are private by default; visibility changes need explicit owner approval and a pre-change review.
- Component runtime helpers should align with the Python `.venv` unless a future explicit decision accepts another runtime.

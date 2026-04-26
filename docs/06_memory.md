# Memory

## Durable Local Notes

- `trading-main` should stay strict: global docs, contracts, registry, templates, shared helpers, plus the gitignored shared environment anchor.
- Do not let `trading-main` become a dumping ground for component-local implementation detail.
- Keep trading statuses and registrable fields in `trading-main/registry/`, not scattered through docs.
- The market-state contamination rule is a core system invariant.

- Registry Markdown kind files under `registry/kinds/` define boundaries only; concrete entries live in SQL, GitHub visibility comes from generated `registry/current.csv`, and registry operating rules live in `docs/07_registry.md`.
- Contract drafting templates belong under `templates/contracts/`, not as numbered docs after `06_memory.md`; `07_registry.md` is the approved registry operating-guide exception.
- Stale canceled-project registry entries were removed because GitHub history is the restore path.
- Registry ids are stable automation references; keys are human-readable and unsafe for durable automation dereferencing.
- Registry `path` is a nullable column for direct locators, not a registry kind.
- Every field registry entry must have non-empty `applies_to`; multiple scopes use semicolon-separated values.
- Path helper methods are individually registered as script entries even though they share `registry-reader.js`.
- Registered helper APIs are id-only: get key, payload, path, or secret text by stable registry id.
- Registry keys are output/display labels, not helper inputs.

# Memory

## Durable Local Notes

- `trading-main` should stay strict: global docs, contracts, registry, templates, shared helpers, plus the gitignored shared environment anchor.
- Do not let `trading-main` become a dumping ground for component-local implementation detail.
- Keep trading statuses and registrable fields in `trading-main/registry/`, not scattered through docs.
- The market-state contamination rule is a core system invariant.

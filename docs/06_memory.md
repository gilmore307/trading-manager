# Memory

## Durable Local Notes

- `trading-main` should stay strict: global docs and contracts only, plus the gitignored shared environment anchor.
- Do not let `trading-main` become a dumping ground for component-local implementation detail.
- Keep statuses and registrable fields in `universal-catalog`, not duplicated here.
- The market-state contamination rule is a core system invariant.

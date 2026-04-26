# Data Task Templates

Reusable draft templates for manager-driven `trading-data` historical acquisition tasks.

These templates are cross-repository planning surfaces:

- `trading-manager` uses the task-key shape to request work;
- `trading-data` uses bundle templates to implement fetch, clean, save, and receipt steps;
- `trading-storage` uses receipt/output references later when durable contracts are accepted.

Development-stage outputs should target `TRADING_DATA_DEVELOPMENT_STORAGE_ROOT` (`trading-data/data/storage/`) and not SQL by default.

## Templates

- `task_key.json` — draft manager-issued historical data task key.
- `bundle_readme.md` — per-bundle documentation template.
- `fetch_spec.md` — provider/API fetch requirement template.
- `clean_spec.md` — normalization and validation preparation template.
- `save_spec.md` — development-save and future durable-save template.
- `completion_receipt.json` — draft task completion receipt shape.
- `fixture_policy.md` — per-bundle fixture and live-call guardrail template.

## Boundary

These are templates, not accepted concrete schemas. Stable schema fields, status values, request types, artifact types, and storage contracts still require registry/docs review before implementation treats them as durable contracts.

No template may contain provider secret values, raw credentials, generated data, or account-specific private configuration.

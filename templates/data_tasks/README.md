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
- `pipeline.py` — default single-file bundle implementation template with four step functions.
- `fetch_spec.md` — provider/API fetch requirement template.
- `clean_spec.md` — normalization and validation preparation template.
- `save_spec.md` — development-save and future durable-save template.
- `completion_receipt.json` — draft task completion receipt shape.
- `fixture_policy.md` — per-bundle fixture and live-call guardrail template.

## Minimalism Rule

Task key and completion receipt templates should contain only fields the runner, bundle, manager, or development evidence path will actually use. Do not add lookup/reference metadata such as provider documentation URLs when those values already live in the registry or bundle README.

## Boundary

These are templates, not accepted concrete schemas. Stable schema fields, status values, request types, artifact types, and storage contracts still require registry/docs review before implementation treats them as durable contracts.

No template may contain provider secret values, raw credentials, generated data, or account-specific private configuration.

## Implementation Shape

By default, a bundle should start as one `pipeline.py` file exposing one `run(...)` entry point and internal `fetch`, `clean`, `save`, and `write_receipt` functions. Split those functions into separate modules only when the bundle becomes large enough to justify the extra structure.

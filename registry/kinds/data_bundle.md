# Data Bundle

## Kind Boundary

Manager-facing runnable bundle names accepted for task keys, runner dispatch, model-input manifests, and completion receipts.

A data bundle is a task boundary that a manager can request directly. Source adapters and provider interfaces are not data bundles; they belong in `data_source`.

## Range

Register bundle keys that may appear in manager-facing `task_key.bundle`, runner routing, bundle READMEs, completion receipts, or model-input planning docs.

Use `payload` for the concrete bundle key. Use `path` for the canonical manager-facing bundle implementation directory or runner script when implemented. Source adapter directories under `data_sources/` belong in `data_source`, not `data_bundle`.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- provider/source names, which belong in `term`;
- source adapters or provider interfaces, which belong in `data_source`;
- credential aliases, which belong in `config`;
- runtime JSON fields, which belong in `field`;
- scripts or Python symbols, which belong in `script`;
- template files, which belong in `template`;
- shared checked-in data/config artifacts, which belong in `shared_artifact`;
- saved dataset shapes, which belong in `data_kind`.

## Naming Rule

Bundle keys should be stable snake_case and should name the accepted final acquisition boundary. Bundle-specific task/run IDs should use the bundle key as their prefix, such as `alpaca_news_task_...` and `alpaca_news_run_...`. If a bundle is narrowed from raw source mechanics to a final output family, prefer the final output family name, e.g. `alpaca_liquidity` instead of `alpaca_quotes_trades`.

# Data Bundle

## Kind Boundary

Historical data acquisition bundle names accepted for `trading-data` task keys, runner dispatch, and completion receipts.

A data bundle is a runnable or planned acquisition boundary such as bars, news, quotes/trades, SEC company financials, ETF holdings, or a release-event pattern. It is narrower than a provider/source term and broader than one internal function.

## Range

Register bundle keys that may appear in `task_key.bundle`, runner routing, bundle READMEs, completion receipts, or cross-repository planning docs.

Use `payload` for the concrete bundle key or pattern, for example `alpaca_news` or `macro_data`. Use `path` for the canonical bundle implementation directory or runner script when implemented. Provider/source documentation URLs belong on provider/source `term` rows, not on implemented `data_bundle` rows.

## Reject Or Re-scope

Reject or re-scope entries that are actually:

- provider/source names, which belong in `term`;
- credential aliases, which belong in `config`;
- runtime JSON fields, which belong in `field`;
- scripts or Python symbols, which belong in `script`;
- output artifacts or saved datasets, which belong in `output` or future storage contracts.

## Naming Rule

Bundle keys should be stable snake_case and should name the accepted final acquisition boundary. Bundle-specific task/run IDs should use the bundle key as their prefix, such as `alpaca_news_task_...` and `alpaca_news_run_...`. If a bundle is narrowed from raw source mechanics to a final output family, prefer the final output family name, e.g. `alpaca_liquidity` instead of `alpaca_quotes_trades`.

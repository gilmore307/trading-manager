# Memory

## Durable Local Notes

- `trading-main` should stay strict: global docs, contracts, registry, templates, shared helpers, plus the gitignored shared environment anchor.
- Do not let `trading-main` become a dumping ground for component-local implementation detail.
- Keep trading statuses and registrable fields in `trading-main/scripts/`, not scattered through docs.
- The market-state contamination rule is a core system invariant.

- Registry Markdown kind files under `scripts/kinds/` define boundaries only; concrete entries live in SQL, GitHub visibility comes from generated `scripts/current.csv`, and registry operating rules live in `docs/08_registry.md`.
- Contract drafting templates belong under `storage/templates/contracts/`, not as numbered docs after `06_memory.md`; `07_helpers.md`, `08_registry.md`, and `09_templates.md` are approved platform-function guides after the project-wide docs.
- Stale canceled-project registry entries were removed because GitHub history is the restore path.
- Registry ids are stable automation references; keys are human-readable and unsafe for durable automation dereferencing.
- Registry `path` is a nullable column for direct locators, not a registry kind.
- Every field registry entry must have non-empty `applies_to`; multiple scopes use semicolon-separated values.
- Public helper methods are individually registered as script entries when they are part of the approved shared helper surface.
- Registered helper APIs are id-only: get key, payload, path, or secret text by stable registry id.
- Registry keys are output/display labels, not helper inputs.

- `docs/07_helpers.md`, `docs/08_registry.md`, and `docs/09_templates.md` are platform-function guides for `trading-main`; `00_scope.md` through `06_memory.md` remain project-wide.
- Future global helpers, reusable templates, and shared fields/status/type values discovered in component work must be recorded through `trading-main` before they become cross-repository contracts.
- Official registry helper runtime surface is the Python `trading_registry` package under `src/`; the older non-Python helper implementation was removed.
- Shared environment baseline is Python 3.12 at `/root/projects/trading-main/.venv`, installed with `pip` from root `requirements.txt`.
- Trading repositories are private by default; visibility changes need explicit owner approval and a pre-change review.
- Component runtime helpers should align with the Python `.venv` unless a future explicit decision accepts another runtime.
- Registry `payload_format` is a registered value-format vocabulary, not just text/file storage; use the narrowest registered format and keep SQL constraint values aligned with `kind=payload_format` rows.
- Registry kind vocabulary belongs to the SQL kind constraint and `scripts/kinds/*.md`; do not mirror it as runtime package validators unless a real runtime consumer requires it.
- Test scripts are repository-local verification assets, not registry `script` rows; each test directory README must inventory every first-party test script and what it verifies.
- OKX is registered as a provider term for crypto data acquisition and trading. Registry config row `OKX_SECRET_ALIAS` points to source-level alias `okx` and path `/root/secrets/okx.json`; JSON fields are `api_key`, `secret_key`, `passphrase`, `allowed_ip_address`, and `api_key_remark_name`.
- Source secrets use one JSON file per feed/provider under `/root/secrets/<source>.json`; reusable JSON key names such as `api_key`, `secret_key`, `passphrase`, `endpoint`, `allowed_ip_address`, `api_key_remark_name`, and `pat` are registered as `field` rows with `applies_to=source_secret_file_schema`.
- Alpaca is registered as a provider term for stock/ETF bars, quotes, trades, and news data acquisition. Registry config row `ALPACA_SECRET_ALIAS` points to source-level alias `alpaca` and path `/root/secrets/alpaca.json`; JSON fields are `api_key`, `secret_key`, and `endpoint`.
- ThetaData is registered as an options-data provider term for chain timeline, quote, trade, OHLC, Greeks, and related options datasets. Credentials and ThetaTerminal `creds.txt`/JAR placement are intentionally deferred until the source connector boundary is designed.
- Obsolete macro-provider references and secret aliases for FRED, Census, BEA, BLS, and U.S. Treasury Fiscal Data are not active registry rows; re-add any of them only through a current accepted feed interface.
- Provider `term` rows can use `path` for official documentation URLs only when the reference remains current and useful; source-secret `config` rows keep `path` pointed at local `/root/secrets/<source>.json` files.
- Retired `calendar_discovery` rows and FOMC/Nasdaq earnings calendar discovery terms are not active registry vocabulary; current event/calendar acquisition routes through accepted `trading-source` sources such as Trading Economics calendar web.
- Registered workflow terms for `trading-source`: `HISTORICAL_DATA_ACQUISITION`, `DATA_TASK_KEY_FILE`, and `DATA_TASK_COMPLETION_RECEIPT`. Manager issues task key files; source sources execute historical acquisition/cleaning scripts; development outputs/receipts use local `storage/`; storage owns durable SQL outputs and completion receipts once contracts are accepted.
- The earlier `TRADING_SOURCE_DEVELOPMENT_STORAGE_ROOT` draft config was pruned from active registry rows; unmigrated `trading-source` development outputs still use ignored local `storage/` paths until durable storage contracts are accepted.
- Added reusable draft data task templates under `storage/templates/data_tasks/`: task key, source README, fetch spec, clean spec, save spec, completion receipt, and fixture policy. These support API-specific `trading-source` source design but are not accepted concrete schemas yet.
- Data source sources should default to one `pipeline.py` with `fetch`, `clean`, `save`, and `write_receipt` functions; split into separate modules only when complexity justifies it. Source README files carry API-specific details.
- Data task key and completion receipt templates should stay minimal and operational. Removed unused metadata such as provider documentation URL from runtime JSON templates; provider docs belong in scripts/source README.
- A data task key is stable across periodic/scheduled runs. Per-run details belong in the task-level completion receipt under `runs[]`; run output directories should use `storage/<task-id>/runs/<run-id>/`.
- Registered all current minimal data task JSON fields as registry `field` rows: task key fields `task_id`, `source`, `credential_config_id`, `params`, `output_root`; receipt fields `task_id`, `source`, `runs`; run fields `run_id`, `status`, `started_at`, `completed_at`, `output_dir`, `outputs`, `row_counts`, `error`.

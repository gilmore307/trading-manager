# Data Kind Cleanup Review - 2026-04-28

## Trigger

The registry has accumulated broad source concepts as `data_kind` rows. Several rows do not have a final template, a subordinate field/schema shape, or an active routing consumer. That makes `data_kind` too vague to act as a registry contract.

## Current Evidence

From `scripts/current.csv` after reverting the erroneous field-category change:

- Total `data_kind` rows: 84
- Rows with a registry `path`: 68
- Rows whose `path` resolves to an existing local template/artifact: 18
- Rows with registered field scopes directly tied to the data-kind payload/template name: 13
- Rows with neither `path` nor directly scoped fields: 14
- Rows with no direct code/doc references outside registry migrations/current snapshot: 34

Existing local data-kind preview templates under `trading-source/storage/templates/data_kinds/` support these active final saved shapes:

- `crypto_bar`
- `crypto_liquidity_bar`
- `equity_abnormal_activity_event`
- `equity_bar`
- `equity_liquidity_bar`
- `equity_news`
- `etf_holdings_snapshot`
- `event_analysis_report`
- `event_factor`
- `gdelt_article`
- `macro_release_event`
- `option_activity_event`
- `option_activity_event_detail`
- `option_bar`
- `option_chain_snapshot`
- `stock_etf_exposure`
- `trading_economics_calendar_event`
- `trading_event`

Two rows have directly scoped field shapes but no active final template path:

- `etf_holding`
- `macro_release`

These should be reviewed as either legacy/transient shapes or converted into real final templates before being treated as active data kinds.

## Problem Rows: No Path And No Direct Field Shape

These rows are not currently strong enough to justify active `data_kind` status without an explicit consumer contract:

- `crypto_order_book`
- `crypto_quote`
- `crypto_trade`
- `economic_release_calendar`
- `economic_release_event`
- `equity_quote`
- `equity_snapshot`
- `equity_trade`
- `etf_constituent_weight`
- `etf_fund_metadata`
- `macro_release_calendar`
- `option_nbbo`
- `option_quote`
- `option_trade`

Some may remain useful as source-input terminology, but then they should be represented as terms/source capabilities, not active final data kinds.

## Problem Rows: Provider Documentation URL In `data_kind.path`

`data_kind.path` is supposed to point to a final saved template/preview file when one exists. Provider documentation URLs belong on provider/source `term` rows. Current rows using provider documentation URLs as data-kind paths include:

- calendar/FOMC/event source concepts such as `equity_earnings_calendar`, `fomc_meeting`, `fomc_minutes`, `fomc_sep`, `fomc_statement`
- many deprecated macro source concepts under BEA, BLS, Census, FRED/ALFRED, and Treasury
- ThetaData raw/source endpoint concepts such as `option_contract`, `option_eod`, `option_greeks_*`, `option_implied_volatility`, `option_open_interest`, `option_snapshot`, and `option_trade_greeks`
- SEC raw/source endpoint concepts such as `sec_company_fact`, `sec_company_concept`, `sec_submission`, `sec_xbrl_frame`, and `sec_filing_document`

These should not stay as active final data kinds unless each gets an accepted final saved template or an explicit routeable source-input contract.

## Proposed New Boundary

A `data_kind` row should be active only if it satisfies at least one of these mutually clear conditions:

1. **Final saved shape** — has an existing canonical preview/template path under `trading-source/storage/templates/data_kinds/<source>/`.
2. **Routeable source-input contract** — is accepted by a named active `data_bundle`/pipeline as an input selector and documents persistence behavior as transient, raw, or final.
3. **Derived model/input product** — is a durable derived product with a documented owner and output contract.

Rows that are merely provider endpoint names, broad source concepts, future wishlist items, or abandoned/deprecated concepts should be moved out of active `data_kind` semantics. They can become `term` rows, be folded into `data_bundle` notes, or be removed/deprecated by migration depending on whether anything still references them.

## Proposed Cleanup Phases

1. Tighten `scripts/kinds/data_kind.md` to require one active contract class: final template, routeable source-input contract, or durable derived output.
2. Add an audit test that flags active `data_kind` rows without one of those evidence anchors.
3. Create a migration that marks non-contract rows as deprecated or moves them to `term` where they are only terminology/source concepts.
4. Prune duplicate macro/source endpoint rows that are not active task parameters or final outputs.
5. Regenerate `scripts/current.csv` and verify downstream references before removing any row entirely.

## Cleanup Applied

Migrations `092_prune_obsolete_data_kinds.sql`, `093_prune_remaining_deprecated_macro_kinds.sql`, `094_merge_duplicate_field_rows.sql`, and `095_merge_remaining_duplicate_field_payloads.sql` applied the first cleanup pass.

Result after first cleanup:

- Total registry rows: 474
- `data_kind` rows: 45, down from 84
- `field` rows: 283, down from 303
- `data_kind` rows with no external reference outside registry migrations/current snapshot: 0
- duplicate `field` payloads: 0
- remaining duplicate payloads are only bundle-local `config` rows whose payload is intentionally the same marker while each row has a distinct config path/owner.

Second cleanup after kind-boundary review:

- Total registry rows: 445
- `data_kind` rows: 18, restricted to accepted final saved/template-backed shapes only
- `data_bundle` rows: 8, restricted to manager-facing bundle boundaries under `data_bundles/`
- `data_source` rows: 12, reclassified from source-adapter rows that were incorrectly registered as bundles
- `template` rows: 8, reclassified from former output rows that were actually templates
- `shared_artifact` rows: 1, for `MARKET_ETF_UNIVERSE_SHARED_CSV`
- `output` kind removed from the active kind constraint and kind files

Follow-up corrections:

- `EQUITY_ABNORMAL_ACTIVITY_BUNDLE` was removed from `data_bundle`; equity abnormal activity is an event-overlay detector path, not a standalone manager-facing bundle.
- `EQUITY_ABNORMAL_ACTIVITY_BUNDLE_CONFIG` was removed from registry config for the same reason; the config remains implementation-local under the event overlay detector code.
- `data_bundle` rows are now 7: only the numbered model-input bundles remain.
- `data_kind` keeps `EQUITY_ABNORMAL_ACTIVITY_EVENT` because it has subordinate registered fields and an accepted final preview template.
- Deleted historical `data_kind` rows were restored when they still represented source capability or terminology. They were not restored as active `data_kind` rows.
- Added `source_capability` for source-level record families, endpoint families, raw inputs, transient evidence, and entitlement-gated provider capabilities that may inform adapters but are not accepted final saved shapes.

Result after restoration and obsolete macro-reference pruning:

- Total registry rows: 478
- `data_kind` rows: 18, still restricted to accepted final saved/template-backed shapes only
- `source_capability` rows: 31, restored from deleted source/interface-capability history
- `term` rows: 31, after deleting deprecated macro_data-era official-source references such as `MACRO_BLS_CPI` that are unused by the current Trading Economics/event-overlay plan
- `data_bundle` rows: 7, only numbered model-input bundles

Removed or merged categories:

- rows with no current source/interface/term role after review;
- deprecated macro_data-era official-source references with `deprecated_macro_data_source_reference` or `deprecated_macro_data_transient_evidence` scope;
- the erroneous leftover `REGISTRY_ITEM_FIELD_CATEGORY` row from the reverted field-category attempt;
- duplicate scenario-specific field rows for `symbol`, `source_url`, `title`, `event_time`, `source_type`, `summary`, `url`, `event_id`, `evidence_window`, `source_refs`, `as_of_date`, `bundle`, `status`, and `id`.

Source-input concepts are no longer allowed as `data_kind`. They must be `source_capability` when they describe source availability/raw input/entitlement capability, or `term` when they are glossary/provider/source-reference concepts.

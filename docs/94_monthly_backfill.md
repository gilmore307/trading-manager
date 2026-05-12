# Monthly Backfill Planning

`trading-manager` plans historical data acquisition as dry-run `manager_request_v1` rows before any provider call is made. The planner is monthly because source availability, retry, and storage readiness should be reviewed one bounded month at a time.

## Accepted Start Policy

The common historical start month is `2016-01`.

Formal historical operation is chronological-forward: start at the accepted earliest common month (`2016-01`) and advance month by month from old to new. Do not run nearer months ahead of older eligible months unless a reviewed operator exception is recorded. Request planning clamps any earlier requested month to `2016-01`, even when a provider has older raw availability, so formal evidence begins from the reviewed common start.

Crypto is allowed to join later. The current OKX BTC/USDT evidence supports starting OKX monthly backfill at `2018-01`; this does not block the equity/news/SEC/options route from beginning at `2016-01`.

## Default Historical Sources

| Source | Component | Effective month | Stance |
|---|---:|---:|---|
| Alpaca bars | `01_feed_alpaca_bars` | `2016-01` | included as one request per selected reviewed ETF universe symbol; defaults to Layer 1 and can explicitly plan Layer 2 sector-context rows |
| Alpaca liquidity | `02_feed_alpaca_liquidity` | `2016-01` | included |
| Alpaca news | `03_feed_alpaca_news` | `2016-01` | included from common start |
| GDELT news | `05_feed_gdelt_news` | `2016-01` | included from common start |
| SEC company financials | `08_feed_sec_company_financials` | `2016-01` | included from common start |
| ThetaData option primary tracking | `10_feed_thetadata_option_primary_tracking` | `2016-01` | included |
| ThetaData option event timeline | `11_feed_thetadata_option_event_timeline` | `2016-01` | included |
| OKX crypto market data | `04_feed_okx_crypto_market_data` | `2018-01` | joins later |

## Excluded From Historical Backfill

These sources remain valid active feeds, but they are not honest historical point-in-time backfill sources under the current route:

| Source | Component | Reason |
|---|---:|---|
| ETF holdings | `06_feed_etf_holdings` | Current issuer file/page route; no accepted historical point-in-time archive. |
| Trading Economics calendar web | `07_feed_trading_economics_calendar_web` | Visible-page route is current/window oriented, not a bulk historical API route. |
| ThetaData option selection snapshot | `09_feed_thetadata_option_selection_snapshot` | Current snapshot route is not accepted as historical point-in-time chain backfill. |

Do not mix these into historical model evidence without a new source route or explicit leakage review.

## Planner Command

```bash
PYTHONPATH=src python3 scripts/tasks/plan_monthly_backfill.py \
  --start-month 2016-01 \
  --end-month 2016-03 \
  --format jsonl
```

The planner emits deterministic dry-run `manager_request_v1` dictionaries. It does not insert SQL rows, call providers, or persist task payload bodies.

For Layer 1 `MarketRegimeModel` training, `01_feed_alpaca_bars` expands over every `model_layer = layer_01_market_regime` row in `trading-storage/main/shared/market_regime_etf_universe.csv`. Each ETF symbol gets its own monthly request and storage path so missing history, provider errors, and receipts stay isolated by symbol. The current reviewed Layer 1 universe has 22 market-state ETFs.

For Layer 2 `SectorContextModel` training, pass `--model-layer layer_02_sector_context` to the planner or use the dedicated Layer 2 preparation command below. Layer 2 expands over the reviewed sector/industry ETF rows from the same shared universe file. The current reviewed Layer 2 universe has 25 sector/industry ETFs and uses autonomous historical provider dispatch under manager request, resource, receipt, and terminal-coverage controls.

Each planned request keeps only concise control-plane facts:

- `request_id`
- `contract_type = manager_request_v1`
- `request_kind = data_backfill_month_v1`
- `status = requested`
- target component/repo fields
- selected ETF symbol/timeframe/universe metadata for `01_feed_alpaca_bars`
- `expected_outputs`
- `policy_refs`
- `parameter_ref`
- month window fields
- `dry_run = true`

Provider task-key bodies and bulky runtime evidence belong behind storage refs, not inside manager request rows.

## Layer 1 and Layer 2 Historical-Training Preparation

Layer 1 and Layer 2 training should be prepared by manager as complete batches, not as individual operator-prompted ETF tasks. Layer 1 prepares the market-regime ETF universe:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_layer_one_historical_training.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write-files-only \
  --format json
```

Layer 2 prepares the sector-context ETF universe with the same no-provider safety boundary:

```bash
PYTHONPATH=src python3 scripts/tasks/prepare_layer_two_historical_training.py \
  --start-month 2016-01 \
  --end-month 2016-01 \
  --write-files-only \
  --format json
```

The batch preparation performs these manager-owned steps together:

1. plan `01_feed_alpaca_bars` requests for every reviewed symbol in the selected model layer universe;
2. build component-readable `task_key.json` payloads behind each `parameter_ref`;
3. validate the payload handoff against the `trading-data` feed `build_context` boundary;
4. report a batch summary showing zero provider calls, zero dispatch, zero model activation, and zero broker execution.

Use `--write` only when the reviewed batch should be persisted to manager SQL as active control-plane requests and request-scoped input bindings. Even then, provider dispatch still requires a validated `autonomous_historical_provider_acquisition_v1`.

## Payload Materialization

After request rows are reviewed or persisted, materialize the component-readable `task_key.json` bodies behind each `parameter_ref`:

```bash
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py requests.jsonl \
  --write-files
```

For SQL-backed request rows, fetch and materialize directly from `trading_manager.manager_request`:

```bash
PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py \
  --from-db \
  --request-kind data_backfill_month_v1 \
  --status requested \
  --write-files \
  --write-bindings
```

The materializer writes local development payloads under `storage/monthly_backfill_v1/.../task_key.json` by resolving `storage://trading-manager/...` URIs. Layer 1 and Layer 2 Alpaca bar payloads use `storage/monthly_backfill_v1/alpaca_bars/<SYMBOL>/<MONTH>/task_key.json` and set the component `params.symbol` / `params.timeframe` from the reviewed ETF universe row for the request model layer. It also emits or persists request-scoped `input_binding_v1` rows with the payload URI, schema ref, byte size summary, and canonical SHA-256 hash.

This still does not dispatch components or call providers. It only makes the request package concrete enough for a later component-facing dry-run handoff.

## Guardrail

A generated request or materialized task key is not by itself provider execution. Provider calls run only through bounded manager dispatch with request ids, resource controls, receipts, and terminal-coverage checks. The dispatch path is data-acquisition-only and must not enable broker execution, model activation, or account mutation.

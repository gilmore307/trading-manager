# Monthly Backfill Planning

`trading-manager` plans historical data acquisition as dry-run `manager_request_v1` rows before any provider call is made. The planner is monthly because source availability, retry, and storage readiness should be reviewed one bounded month at a time.

## Accepted Start Policy

The common historical start month is `2016-01`.

Crypto is allowed to join later. The current OKX BTC/USDT evidence supports starting OKX monthly backfill at `2018-01`; this does not block the equity/news/SEC/options route from beginning at `2016-01`.

## Default Historical Sources

| Source | Component | Effective month | Stance |
|---|---:|---:|---|
| Alpaca bars | `01_feed_alpaca_bars` | `2016-01` | included |
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

Each planned request keeps only concise control-plane facts:

- `request_id`
- `contract_type = manager_request_v1`
- `request_kind = data_backfill_month_v1`
- `status = requested`
- target component/repo fields
- `expected_outputs`
- `policy_refs`
- `parameter_ref`
- month window fields
- `dry_run = true`

Provider task-key bodies and bulky runtime evidence belong behind storage refs, not inside manager request rows.

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

The materializer writes local development payloads under `storage/monthly_backfill_v1/.../task_key.json` by resolving `storage://trading-manager/...` URIs. It also emits or persists request-scoped `input_binding_v1` rows with the payload URI, schema ref, byte size summary, and canonical SHA-256 hash.

This still does not dispatch components or call providers. It only makes the request package concrete enough for a later component-facing dry-run handoff.

## Guardrail

A generated request or materialized task key is not approval to run live acquisition. Provider calls still require the live-call policy from `docs/93_contracts.md` and `trading-data/docs/96_production_hardening.md`.

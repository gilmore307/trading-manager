-- Register accepted monthly backfill planning policy and callable planner.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'req_MBF001',
    'request_type',
    'DATA_BACKFILL_MONTH_V1',
    'text',
    'data_backfill_month_v1',
    'trading-manager/docs/94_monthly_backfill.md',
    'manager_request_v1;monthly_backfill_v1;trading-data',
    'registry_only',
    'One-month historical data backfill request. The request is a control-plane fact, not approval to call a live provider.'
  ),
  (
    'cfg_MBF001',
    'config',
    'MONTHLY_BACKFILL_COMMON_START_MONTH',
    'text',
    '2016-01',
    'trading-manager/docs/94_monthly_backfill.md',
    'monthly_backfill_v1;historical_data_backfill;manager_request_v1',
    'sync_artifact',
    'Accepted common historical start month for equity/news/SEC/ThetaData historical sources.'
  ),
  (
    'cfg_MBF002',
    'config',
    'MONTHLY_BACKFILL_CRYPTO_START_MONTH',
    'text',
    '2018-01',
    'trading-manager/docs/94_monthly_backfill.md',
    'monthly_backfill_v1;okx_crypto_market_data;historical_data_backfill',
    'sync_artifact',
    'OKX crypto joins the monthly backfill plan later than the common start and does not block the 2016-01 historical route.'
  ),
  (
    'cfg_MBF003',
    'config',
    'MONTHLY_BACKFILL_INCLUDED_HISTORICAL_FEEDS',
    'text',
    '01_feed_alpaca_bars;02_feed_alpaca_liquidity;03_feed_alpaca_news;05_feed_gdelt_news;08_feed_sec_company_financials;10_feed_thetadata_option_primary_tracking;11_feed_thetadata_option_event_timeline;04_feed_okx_crypto_market_data@2018-01',
    'trading-manager/docs/94_monthly_backfill.md',
    'monthly_backfill_v1;historical_data_backfill;trading-data',
    'sync_artifact',
    'Default monthly historical backfill feeds. OKX is included with its later effective start month.'
  ),
  (
    'cfg_MBF004',
    'config',
    'MONTHLY_BACKFILL_EXCLUDED_CURRENT_ONLY_FEEDS',
    'text',
    '06_feed_etf_holdings;07_feed_trading_economics_calendar_web;09_feed_thetadata_option_selection_snapshot',
    'trading-manager/docs/94_monthly_backfill.md',
    'monthly_backfill_v1;current_only_feed;point_in_time_leakage_guard',
    'sync_artifact',
    'Active feeds excluded from historical point-in-time backfill until a new historical route or leakage review is accepted.'
  ),
  (
    'scr_MBF001',
    'script',
    'MANAGER_MONTHLY_BACKFILL_PLAN',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/plan_monthly_backfill.py',
    '/root/projects/trading-manager/scripts/tasks/plan_monthly_backfill.py',
    'monthly_backfill_v1;manager_request_v1;dry_run_planning',
    'sync_artifact',
    'Callable planner that emits deterministic dry-run manager_request_v1 rows for monthly historical backfill without calling providers or inserting SQL rows.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

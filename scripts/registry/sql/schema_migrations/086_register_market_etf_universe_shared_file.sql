-- Register shared market ETF universe CSV and its canonical columns.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('out_MKTETFUNI', 'output', 'MARKET_ETF_UNIVERSE_SHARED_CSV', 'file', 'storage/shared/market_etf_universe.csv', '/root/projects/trading-main/storage/shared/market_etf_universe.csv', 'trading-main;trading-data;trading-model;market_regime_model;security_selection_model', 'sync_artifact', 'Shared curated ETF universe used for market-state and sector/industry/theme observation. The bar_grain column is the intended observation granularity.'),
  ('fld_MEU001', 'field', 'MARKET_ETF_UNIVERSE_TICKER', 'field_name', 'ticker', 'storage/shared/market_etf_universe.csv', 'market_etf_universe', 'sync_artifact', 'ETF ticker symbol in the shared market ETF universe'),
  ('fld_MEU002', 'field', 'MARKET_ETF_UNIVERSE_ROLE', 'field_name', 'universe_role', 'storage/shared/market_etf_universe.csv', 'market_etf_universe', 'sync_artifact', 'ETF universe role such as market_state_etf or sector_observation_etf'),
  ('fld_MEU003', 'field', 'MARKET_ETF_EXPOSURE_CATEGORY', 'field_name', 'exposure_category', 'storage/shared/market_etf_universe.csv', 'market_etf_universe', 'sync_artifact', 'ETF market/sector/theme exposure category such as us_equity_core, sp500_sector, industry_chain, thematic_growth, crypto_beta, commodities, credit, rates_curve, or usd_volatility'),
  ('fld_MEU004', 'field', 'MARKET_ETF_BAR_GRAIN', 'field_name', 'bar_grain', 'storage/shared/market_etf_universe.csv', 'market_etf_universe', 'sync_artifact', 'Intended observation bar granularity for this ETF, e.g. 1m, 30m, or 1d'),
  ('fld_MEU005', 'field', 'MARKET_ETF_FUND_NAME', 'field_name', 'fund_name', 'storage/shared/market_etf_universe.csv', 'market_etf_universe', 'sync_artifact', 'Human-readable ETF fund name'),
  ('fld_MEU006', 'field', 'MARKET_ETF_ISSUER', 'field_name', 'issuer', 'storage/shared/market_etf_universe.csv', 'market_etf_universe', 'sync_artifact', 'ETF issuer or sponsor display name')
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note;

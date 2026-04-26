-- Add data_bundle as the registry kind for accepted trading-data acquisition bundle keys.
-- Target engine: PostgreSQL.

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'output',
  'repo',
  'config',
  'term',
  'data_bundle',
  'script',
  'payload_format',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type',
  'task_lifecycle_state',
  'review_readiness',
  'acceptance_outcome',
  'test_status',
  'maintenance_status',
  'docs_status'
));

DELETE FROM trading_registry
WHERE id IN ('trm_20PZRDY8', 'trm_HSVF3M02', 'trm_FXFQVK64')
   OR key IN ('SEC_COMPANY_FINANCIALS', 'ALPACA_QUOTES_TRADES', 'ALPACA_NEWS');

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dbu_MMC41ETB', 'data_bundle', 'ALPACA_BARS', 'text', 'alpaca_bars', 'https://docs.alpaca.markets/', 'trading-data', 'historical stock/ETF bars bundle; task/run IDs should use alpaca_bars-specific prefixes'),
  ('dbu_BR96XL13', 'data_bundle', 'ALPACA_QUOTES_TRADES', 'text', 'alpaca_quotes_trades', 'https://docs.alpaca.markets/', 'trading-data', 'historical Alpaca quote/trade bundle excluding news; news is intentionally split into ALPACA_NEWS'),
  ('dbu_UF1ZH2YB', 'data_bundle', 'ALPACA_NEWS', 'text', 'alpaca_news', 'https://docs.alpaca.markets/', 'trading-data', 'historical Alpaca stock/ETF news bundle; task/run IDs should use alpaca_news-specific prefixes'),
  ('dbu_9O1A3ATK', 'data_bundle', 'THETADATA_OPTION_1M_BUNDLE', 'text', 'thetadata_option_1m_bundle', 'https://http-docs.thetadata.us/', 'trading-data', 'historical ThetaData option 1-minute bundle for chain timeline, quote, trade, OHLC, Greeks, and open interest'),
  ('dbu_GI7N2MIP', 'data_bundle', 'THETADATA_OPTION_SNAPSHOT_BUNDLE', 'text', 'thetadata_option_snapshot_bundle', 'https://http-docs.thetadata.us/', 'trading-data', 'historical ThetaData option snapshot bundle for requested-time snapshot, open interest, and Greeks'),
  ('dbu_W59XPQBY', 'data_bundle', 'OKX_BARS', 'text', 'okx_bars', 'https://www.okx.com/docs-v5/en/', 'trading-data', 'historical OKX crypto bars bundle'),
  ('dbu_1J9Y65GU', 'data_bundle', 'MACRO_RELEASE_BUNDLE_PATTERN', 'text', 'macro_release_<release_key>', NULL, 'trading-data', 'bundle naming pattern for one official macro release event or publication set sharing release time, cadence, and downstream use'),
  ('dbu_RFFVOPC8', 'data_bundle', 'CALENDAR_DISCOVERY', 'text', 'calendar_discovery', NULL, 'trading-data', 'web-search-backed bundle for FOMC and official macro release calendar source discovery'),
  ('dbu_ZTQFKICI', 'data_bundle', 'ETF_HOLDINGS', 'text', 'etf_holdings', NULL, 'trading-data', 'issuer-site/source-file bundle for ETF constituents and portfolio weights'),
  ('dbu_5HPPSAMV', 'data_bundle', 'SEC_COMPANY_FINANCIALS', 'text', 'sec_company_financials', 'https://www.sec.gov/search-filings/edgar-application-programming-interfaces', 'trading-data', 'historical SEC EDGAR company financial report bundle; task/run IDs should use sec_company_financials-specific prefixes')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

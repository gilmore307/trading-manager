-- Rename active trading-data source interfaces to number-first source names,
-- matching the data-bundle naming pattern: NN_source_<semantic>.

UPDATE trading_registry
SET payload = CASE payload
  WHEN 'alpaca_bars' THEN '01_source_alpaca_bars'
  WHEN 'alpaca_liquidity' THEN '02_source_alpaca_liquidity'
  WHEN 'alpaca_news' THEN '03_source_alpaca_news'
  WHEN 'okx_crypto_market_data' THEN '04_source_okx_crypto_market_data'
  WHEN 'gdelt_news' THEN '05_source_gdelt_news'
  WHEN 'etf_holdings' THEN '06_source_etf_holdings'
  WHEN 'trading_economics_calendar_web' THEN '07_source_trading_economics_calendar_web'
  WHEN 'sec_company_financials' THEN '08_source_sec_company_financials'
  WHEN 'thetadata_option_selection_snapshot' THEN '09_source_thetadata_option_selection_snapshot'
  WHEN 'thetadata_option_primary_tracking' THEN '10_source_thetadata_option_primary_tracking'
  WHEN 'thetadata_option_event_timeline' THEN '11_source_thetadata_option_event_timeline'
  ELSE payload
END,
path = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(path,
  'data_sources/alpaca_bars', 'data_sources/01_source_alpaca_bars'),
  'data_sources/alpaca_liquidity', 'data_sources/02_source_alpaca_liquidity'),
  'data_sources/alpaca_news', 'data_sources/03_source_alpaca_news'),
  'data_sources/okx_crypto_market_data', 'data_sources/04_source_okx_crypto_market_data'),
  'data_sources/gdelt_news', 'data_sources/05_source_gdelt_news'),
  'data_sources/etf_holdings', 'data_sources/06_source_etf_holdings'),
  'data_sources/trading_economics_calendar_web', 'data_sources/07_source_trading_economics_calendar_web'),
  'data_sources/sec_company_financials', 'data_sources/08_source_sec_company_financials'),
  'data_sources/thetadata_option_selection_snapshot', 'data_sources/09_source_thetadata_option_selection_snapshot'),
  'data_sources/thetadata_option_primary_tracking', 'data_sources/10_source_thetadata_option_primary_tracking'),
  'data_sources/thetadata_option_event_timeline', 'data_sources/11_source_thetadata_option_event_timeline'),
note = note || ' Source interface renamed 2026-04-29 to number-first NN_source_<semantic> form.'
WHERE kind = 'data_source'
AND payload IN (
  'alpaca_bars',
  'alpaca_liquidity',
  'alpaca_news',
  'okx_crypto_market_data',
  'gdelt_news',
  'etf_holdings',
  'trading_economics_calendar_web',
  'sec_company_financials',
  'thetadata_option_selection_snapshot',
  'thetadata_option_primary_tracking',
  'thetadata_option_event_timeline'
);

UPDATE trading_registry
SET applies_to = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(applies_to,
  'alpaca_bars', '01_source_alpaca_bars'),
  'alpaca_liquidity', '02_source_alpaca_liquidity'),
  'alpaca_news', '03_source_alpaca_news'),
  'okx_crypto_market_data', '04_source_okx_crypto_market_data'),
  'gdelt_news', '05_source_gdelt_news'),
  'etf_holdings', '06_source_etf_holdings'),
  'trading_economics_calendar_web', '07_source_trading_economics_calendar_web'),
  'sec_company_financials', '08_source_sec_company_financials'),
  'thetadata_option_selection_snapshot', '09_source_thetadata_option_selection_snapshot'),
  'thetadata_option_primary_tracking', '10_source_thetadata_option_primary_tracking'),
  'thetadata_option_event_timeline', '11_source_thetadata_option_event_timeline')
WHERE applies_to IS NOT NULL;

UPDATE trading_registry
SET note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
  'alpaca_bars', '01_source_alpaca_bars'),
  'alpaca_liquidity', '02_source_alpaca_liquidity'),
  'alpaca_news', '03_source_alpaca_news'),
  'okx_crypto_market_data', '04_source_okx_crypto_market_data'),
  'gdelt_news', '05_source_gdelt_news'),
  'etf_holdings', '06_source_etf_holdings'),
  'trading_economics_calendar_web', '07_source_trading_economics_calendar_web'),
  'sec_company_financials', '08_source_sec_company_financials'),
  'thetadata_option_selection_snapshot', '09_source_thetadata_option_selection_snapshot'),
  'thetadata_option_primary_tracking', '10_source_thetadata_option_primary_tracking'),
  'thetadata_option_event_timeline', '11_source_thetadata_option_event_timeline')
WHERE note IS NOT NULL;

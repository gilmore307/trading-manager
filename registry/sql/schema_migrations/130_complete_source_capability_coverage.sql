-- Complete source_capability coverage for currently implemented trading-data
-- source interfaces. These rows describe source/provider record families and
-- endpoint/page capabilities, not accepted final storage contracts.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('scp_ALPBAR1', 'source_capability', 'ALPACA_EQUITY_BAR', 'text', 'alpaca_equity_bar', 'https://docs.alpaca.markets/reference/stockbars', 'alpaca_bars;alpaca', 'registry_only', 'Alpaca market-data stock/ETF historical bar endpoint capability used transiently by alpaca_bars and numbered trading-data bundles; not a final data_kind'),
  ('scp_ALPNEWS1', 'source_capability', 'ALPACA_EQUITY_NEWS', 'text', 'alpaca_equity_news', 'https://docs.alpaca.markets/reference/news-3', 'alpaca_news;alpaca', 'registry_only', 'Alpaca news endpoint capability for source article metadata used by alpaca_news; not a final canonical event data_kind'),
  ('scp_ALPSNAP1', 'source_capability', 'ALPACA_EQUITY_LATEST_SNAPSHOT', 'text', 'alpaca_equity_latest_snapshot', 'https://docs.alpaca.markets/reference/stocksnapshots', 'alpaca_liquidity;alpaca', 'registry_only', 'Alpaca latest stock snapshot capability; useful for availability/planning around quote/trade/bar state, not currently a final saved data shape'),
  ('scp_OKXCNDL1', 'source_capability', 'OKX_CRYPTO_CANDLE', 'text', 'okx_crypto_candle', 'https://www.okx.com/docs-v5/en/#order-book-trading-market-data-get-candlesticks', 'okx_crypto_market_data;okx', 'registry_only', 'OKX candlestick endpoint capability used by okx_crypto_market_data for crypto bar construction; not a standalone final data_kind'),
  ('scp_GDELTGKG1', 'source_capability', 'GDELT_GKG_RECORD', 'text', 'gdelt_gkg_record', 'https://www.gdeltproject.org/data.html', 'gdelt_news;gdelt_bigquery', 'registry_only', 'GDELT GKG BigQuery record capability used for pre-filtered broad news/source evidence; not a final canonical event data_kind'),
  ('trm_LKP3RR2V', 'source_capability', 'ETF_ISSUER_HOLDINGS', 'text', 'etf_issuer_holdings', '', 'etf_holdings;official_issuer_holdings', 'registry_only', 'Official ETF issuer holdings publication capability across CSV, XLSX, JSON, and HTML issuer surfaces; adapter-normalized evidence, not a provider-independent final data_kind'),
  ('scp_TECALPG1', 'source_capability', 'TRADING_ECONOMICS_CALENDAR_PAGE', 'text', 'trading_economics_calendar_page', 'https://tradingeconomics.com/united-states/calendar', 'trading_economics_calendar_web;trading_economics', 'registry_only', 'Trading Economics visible calendar web-page capability; intentionally excludes API/download endpoints and is not itself a final data_kind')
ON CONFLICT (key) DO UPDATE SET
  kind = EXCLUDED.kind,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = now();

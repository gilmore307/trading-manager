-- Correct feed implementation paths after the source/feed terminology split and
-- replace stale bundle/source-interface prose in active registry notes.

UPDATE trading_registry
SET path = replace(path, 'trading-source/src/data_sources/', 'trading-source/src/data_feed/')
WHERE kind = 'data_feed'
  AND path LIKE 'trading-source/src/data_sources/%';

UPDATE trading_registry
SET note = CASE key
  WHEN 'ALPACA_BARS' THEN '01 data feed for Alpaca stock/ETF historical bars; task/run IDs use 01_feed_alpaca_bars prefixes.'
  WHEN 'ALPACA_LIQUIDITY' THEN '02 data feed for Alpaca liquidity bars built from transient trades and quotes; task/run IDs use 02_feed_alpaca_liquidity prefixes.'
  WHEN 'ALPACA_NEWS' THEN '03 data feed for Alpaca stock/ETF news metadata; task/run IDs use 03_feed_alpaca_news prefixes.'
  WHEN 'OKX_CRYPTO_MARKET_DATA' THEN '04 data feed for OKX crypto bars, normalized trades, and trade-derived liquidity bars; sampled order-book fields may be blank when unavailable.'
  WHEN 'GDELT_NEWS' THEN '05 data feed for GDELT BigQuery-backed global news evidence used by event discovery.'
  WHEN 'ETF_HOLDINGS' THEN '06 data feed for ETF issuer holdings files across CSV, XLSX, JSON, and HTML surfaces.'
  WHEN 'TRADING_ECONOMICS_CALENDAR_WEB' THEN '07 data feed for conservative Trading Economics visible-page U.S. high-impact macro calendar rows; no bulk backfill yet.'
  WHEN 'SEC_COMPANY_FINANCIALS' THEN '08 data feed for SEC EDGAR submissions, companyfacts, companyconcept, and XBRL frames with compact normalized outputs.'
  WHEN 'THETADATA_OPTION_SELECTION_SNAPSHOT' THEN '09 data feed for explicit-time point-in-time ThetaData option-chain snapshots used to simulate visible contract-selection information.'
  WHEN 'THETADATA_OPTION_PRIMARY_TRACKING' THEN '10 data feed for ThetaData specified-contract primary tracking from entry through exit horizons.'
  WHEN 'THETADATA_OPTION_EVENT_TIMELINE' THEN '11 data feed for ThetaData option event-only activity timeline evidence rows and per-event detail artifacts.'
  ELSE note
END
WHERE kind = 'data_feed';

UPDATE trading_registry
SET note = CASE key
  WHEN '01_SOURCE_MARKET_REGIME' THEN '01 manager-facing MarketRegimeModel data source; fetches ETF bars from data feeds and writes trading_source.source_01_market_regime.'
  WHEN '02_SOURCE_SECURITY_SELECTION' THEN '02 manager-facing SecuritySelectionModel data source; fetches ETF holdings from data feeds and writes trading_source.source_02_security_selection.'
  WHEN '03_SOURCE_STRATEGY_SELECTION' THEN '03 manager-facing StrategySelectionModel data source; fetches bars and liquidity from data feeds and writes trading_source.source_03_strategy_selection.'
  WHEN '05_SOURCE_OPTION_EXPRESSION' THEN '05 manager-facing OptionExpressionModel data source; fetches option snapshots from data feeds and writes the option-expression SQL contract.'
  WHEN '06_SOURCE_POSITION_EXECUTION' THEN '06 manager-facing PositionExecutionModel data source; fetches selected-contract option time series from data feeds and writes trading_source.source_06_position_execution.'
  WHEN '07_SOURCE_EVENT_OVERLAY' THEN '07 manager-facing EventOverlayModel data source; prepares one SQL event overview row per required event with details behind references.'
  ELSE replace(note, 'data bundle', 'data source')
END
WHERE kind = 'data_source';

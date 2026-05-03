UPDATE trading_registry
SET note = '02 manager-facing SecuritySelectionModel data source; fetches ETF holdings only for market_etf_universe rows with universe_type = sector_observation_etf and writes trading_source.source_02_security_selection.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = '02_SOURCE_SECURITY_SELECTION';

UPDATE trading_registry
SET note = 'Shared curated ETF universe used for market-state and sector/industry/theme observation. market_state_etf rows are Layer 1 regime/bar instruments; only sector_observation_etf rows require holdings analysis for Layer 2 security-selection exposure. The bar_grain column is the intended observation granularity.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_ETF_UNIVERSE_SHARED_CSV';

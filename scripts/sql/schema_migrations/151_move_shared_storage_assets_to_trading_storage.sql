UPDATE trading_registry
SET path = '/root/projects/trading-storage/main/shared/market_etf_universe.csv',
    applies_to = 'trading-storage;trading-source;trading-model;market_regime_model;security_selection_model',
    note = 'Shared curated ETF universe used for market-state and sector/industry/theme observation. The bar_grain column is the intended observation granularity. Storage migration 2026-04-29: moved from trading-main/storage/shared/ to trading-storage/main/shared/.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_ETF_UNIVERSE_SHARED_CSV';

UPDATE trading_registry
SET path = 'trading-storage/main/shared/market_etf_universe.csv',
    updated_at = CURRENT_TIMESTAMP
WHERE key IN ('EXPOSURE_TYPE', 'UNIVERSE_TYPE', 'BAR_GRAIN', 'FUND_NAME')
  AND path = 'storage/shared/market_etf_universe.csv';

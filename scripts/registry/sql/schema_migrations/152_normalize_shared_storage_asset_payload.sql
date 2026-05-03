UPDATE trading_registry
SET payload = 'trading-storage/main/shared/market_etf_universe.csv',
    note = 'Shared curated ETF universe used for market-state and sector/industry/theme observation. The bar_grain column is the intended observation granularity. Storage boundary migration accepted 2026-04-29: this reviewed shared CSV now lives under trading-storage/main/shared/.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_ETF_UNIVERSE_SHARED_CSV';

UPDATE trading_registry
SET key = 'MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV',
    payload = 'trading-storage/main/shared/market_regime_etf_universe.csv',
    path = '/root/projects/trading-storage/main/shared/market_regime_etf_universe.csv',
    applies_to = 'trading-storage;trading-source;trading-model;market_regime_model;security_selection_model',
    note = 'Shared curated ETF universe used for market-regime state, sector/industry/theme observation, and security-selection holdings scope. market_state_etf rows are Layer 1 regime/bar instruments; only sector_observation_etf rows require holdings analysis for Layer 2 security-selection exposure. The bar_grain column is the intended source observation granularity.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'out_MKTETFUNI';

UPDATE trading_registry
SET path = REPLACE(path, 'trading-storage/main/shared/market_etf_universe.csv', 'trading-storage/main/shared/market_regime_etf_universe.csv'),
    updated_at = CURRENT_TIMESTAMP
WHERE path LIKE '%trading-storage/main/shared/market_etf_universe.csv%';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'market_etf_universe', 'market_regime_etf_universe'),
    note = REPLACE(note, 'market_etf_universe', 'market_regime_etf_universe'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%market_etf_universe%'
   OR note LIKE '%market_etf_universe%';

UPDATE trading_registry
SET applies_to = CASE
        WHEN applies_to LIKE '%market_regime_etf_universe%' THEN applies_to
        ELSE applies_to || ';market_regime_etf_universe'
    END,
    path = NULL,
    note = 'Human-readable interpretation of what a reviewed market-regime ETF universe row or relative-strength combination row measures.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'INTERPRETATION';

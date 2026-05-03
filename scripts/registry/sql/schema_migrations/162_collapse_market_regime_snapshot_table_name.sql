UPDATE trading_registry
SET applies_to = 'trading-derived;trading-model;market_regime_model;01_source_market_regime',
    note = 'Layer 1 MarketRegimeModel derived-output boundary and total V1 wide table. Each row is one 30-minute point-in-time market-regime snapshot keyed by snapshot_time; feature columns cover returns, relative strength, volatility, trend/momentum, and correlation/market breadth, and are reviewed separately as they are accepted.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = '01_DERIVED_MARKET_REGIME';

UPDATE trading_registry
SET applies_to = '05_source_option_expression;01_derived_market_regime;trading-derived;market_regime_model',
    note = 'Point-in-time snapshot timestamp. Used by option-expression source snapshots and by the Layer 1 MarketRegimeModel derived table. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SNAPSHOT_TIME';

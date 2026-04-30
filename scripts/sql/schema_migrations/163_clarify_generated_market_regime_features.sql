UPDATE trading_registry
SET note = 'Layer 1 MarketRegimeModel derived-output boundary and total V1 wide table. Each row is one 30-minute point-in-time market-regime snapshot keyed by snapshot_time; generated feature columns cover returns, relative strength, volatility, trend/momentum, and correlation/market breadth. Concrete generated feature columns such as spy_return_30m are governed by reviewed feature-family rules/catalogs and are not individually registered as registry rows.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = '01_DERIVED_MARKET_REGIME';

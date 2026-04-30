UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'derived_01_market_regime_feature_snapshots', '01_derived_market_regime_feature_snapshots'),
    note = 'Layer 1 MarketRegimeModel derived-output boundary. Produces the accepted V1 30-minute point-in-time market-regime feature snapshot shape at 01_derived_market_regime_feature_snapshots; feature columns are reviewed separately as they are accepted.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = '01_DERIVED_MARKET_REGIME';

UPDATE trading_registry
SET applies_to = REPLACE(applies_to, 'derived_01_market_regime_feature_snapshots', '01_derived_market_regime_feature_snapshots'),
    note = 'Point-in-time snapshot timestamp. Used by option-expression source snapshots and by the Layer 1 MarketRegimeModel derived feature snapshot output. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SNAPSHOT_TIME';

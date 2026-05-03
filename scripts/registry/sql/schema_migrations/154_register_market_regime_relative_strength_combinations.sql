INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
    'out_MRRS001',
    'shared_artifact',
    'MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV',
    'file',
    'trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
    '/root/projects/trading-storage/main/shared/market_regime_relative_strength_combinations.csv',
    'trading-storage;trading-derived;trading-model;market_regime_model;01_source_market_regime',
    'sync_artifact',
    'Curated Layer 1 V1 relative-strength combination table for MarketRegimeModel derived features. Rows define numerator/denominator ETF pairs, source grains, feature cadence, group, and interpretation.'
)
ON CONFLICT (id) DO UPDATE SET
    kind = excluded.kind,
    key = excluded.key,
    payload_format = excluded.payload_format,
    payload = excluded.payload,
    path = excluded.path,
    applies_to = excluded.applies_to,
    artifact_sync_policy = excluded.artifact_sync_policy,
    note = excluded.note,
    updated_at = CURRENT_TIMESTAMP;

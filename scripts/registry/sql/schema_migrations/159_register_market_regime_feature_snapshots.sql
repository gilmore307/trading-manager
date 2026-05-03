INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
    'dki_MRFS001',
    'data_kind',
    'MARKET_REGIME_FEATURE_SNAPSHOTS',
    'text',
    'derived_01_market_regime_feature_snapshots',
    NULL,
    'trading-derived;trading-model;market_regime_model',
    'registry_only',
    'Accepted Layer 1 V1 MarketRegimeModel derived feature snapshot shape. Each row is one 30-minute point-in-time market-regime feature vector keyed by snapshot_time; feature columns are reviewed separately as they are accepted.'
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

UPDATE trading_registry
SET applies_to = CASE
        WHEN applies_to LIKE '%derived_01_market_regime_feature_snapshots%' THEN applies_to
        ELSE applies_to || ';derived_01_market_regime_feature_snapshots;trading-derived;market_regime_model'
    END,
    note = 'Point-in-time snapshot timestamp. Used by option-expression source snapshots and by the Layer 1 MarketRegimeModel derived feature snapshot table. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SNAPSHOT_TIME';

-- Register the reviewed model_layer classification values used by shared
-- market-context CSV assets. The field row was added in migration 200; these
-- rows make the cross-repository token vocabulary explicit.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'mlv_L1MR001',
    'status_value',
    'MODEL_LAYER_LAYER_01_MARKET_REGIME',
    'status_value',
    'layer_01_market_regime',
    'trading-storage/main/shared/market_regime_etf_universe.csv',
    'model_layer;market_regime_etf_universe;market_regime_relative_strength_combinations;market_regime_model;feature_01_market_regime',
    'sync_artifact',
    'Reviewed model_layer value for rows consumed by Layer 1 MarketRegimeModel market-context source/feature construction.'
  ),
  (
    'mlv_L2SC001',
    'status_value',
    'MODEL_LAYER_LAYER_02_SECTOR_CONTEXT',
    'status_value',
    'layer_02_sector_context',
    'trading-storage/main/shared/market_regime_etf_universe.csv',
    'model_layer;market_regime_etf_universe;market_regime_relative_strength_combinations;sector_context_model;feature_02_sector_context',
    'sync_artifact',
    'Reviewed model_layer value for rows consumed by Layer 2 SectorContextModel sector/industry context construction.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

-- Finalize Layer 1 V2.2 shared-scope and model-output registry surfaces.
-- The old market-property factor fields are no longer active model output rows;
-- implementation may still use internal signal groups, but the shared contract is
-- the direction-neutral market-context state vector registered in 197/198.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'fld_MODLAY001',
  'classification_field',
  'MODEL_LAYER',
  'field_name',
  'model_layer',
  'trading-storage/main/shared/market_regime_etf_universe.csv',
  'market_regime_etf_universe;market_regime_relative_strength_combinations;shared_market_context_static_assets',
  'sync_artifact',
  'Shared CSV classification field that explicitly assigns each reviewed row to layer_01_market_regime or layer_02_sector_context so Layer 1 market-state construction and Layer 2 sector-context observation do not depend on implicit combination or universe type semantics.'
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

UPDATE trading_registry
SET note = 'Accepted Layer 1 MarketRegimeModel V2.2 model-output term for the direction-neutral market-context state vector written to trading_model.model_01_market_regime. It does not rank sectors, ETFs, stocks, strategies, option contracts, position sizes, or final actions and does not require clustering or human-readable regime labels.',
    path = 'trading-model/docs/02_layer_01_market_regime.md',
    applies_to = 'trading-model;trading-data;market_regime_model;feature_01_market_regime;direction_neutral_tradability',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MODEL_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Shared curated ETF universe for Layer 1 market-state instruments and Layer 2 sector/industry/theme observation instruments. The model_layer column is the authoritative Layer 1/Layer 2 scope discriminator; universe_type remains descriptive row classification. bar_grain is source acquisition/detail granularity, not necessarily downstream feature cadence.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_REGIME_ETF_UNIVERSE_SHARED_CSV';

UPDATE trading_registry
SET note = 'Shared curated relative-strength combination table for market-context feature generation. The model_layer column is the authoritative Layer 1/Layer 2 scope discriminator; Layer 1 consumes layer_01_market_regime rows and Layer 2 consumes layer_02_sector_context rows.',
    applies_to = 'trading-storage;trading-data;trading-model;market_regime_model;sector_context_model;source_01_market_regime',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MARKET_REGIME_RELATIVE_STRENGTH_COMBINATIONS_SHARED_CSV';

DELETE FROM trading_registry
WHERE id IN (
  'fld_MRM012',
  'fld_MRM013',
  'fld_MRM014',
  'fld_MRM015',
  'fld_MRM016',
  'fld_MRM017',
  'fld_MRM018',
  'fld_MRM019',
  'fld_MRM020',
  'fld_MRM021',
  'fld_MRM022'
);

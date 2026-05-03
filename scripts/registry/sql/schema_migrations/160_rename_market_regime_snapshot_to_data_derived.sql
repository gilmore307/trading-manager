ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET kind = 'data_derived',
    key = '01_DERIVED_MARKET_REGIME',
    payload = '01_derived_market_regime',
    path = 'trading-derived/src/data_derived/01_derived_market_regime',
    applies_to = 'trading-derived;trading-model;market_regime_model;derived_01_market_regime_feature_snapshots',
    artifact_sync_policy = 'registry_only',
    note = 'Layer 1 MarketRegimeModel derived-output boundary. Produces the accepted V1 30-minute point-in-time market-regime feature snapshot shape; feature columns are reviewed separately as they are accepted.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'dki_MRFS001';

UPDATE trading_registry
SET applies_to = '05_source_option_expression;01_derived_market_regime;derived_01_market_regime_feature_snapshots;trading-derived;market_regime_model',
    note = 'Point-in-time snapshot timestamp. Used by option-expression source snapshots and by the Layer 1 MarketRegimeModel derived feature snapshot output. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'SNAPSHOT_TIME';

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'identity_field',
  'path_field',
  'temporal_field',
  'classification_field',
  'text_field',
  'parameter_field',
  'repo',
  'config',
  'term',
  'provider',
  'data_feed',
  'data_source',
  'data_derived',
  'feed_capability',
  'data_kind',
  'template',
  'shared_artifact',
  'script',
  'payload_format',
  'status_value',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type'
));

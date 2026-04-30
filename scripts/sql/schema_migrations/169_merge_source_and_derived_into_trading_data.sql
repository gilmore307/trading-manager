-- Merge the active source/derived data-production repositories into trading-data
-- and rename the deterministic Layer 1 derived surface to a feature surface.

ALTER TABLE trading_registry DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET
    key = 'TRADING_DATA_REPO',
    payload = 'trading-data',
    path = '/root/projects/trading-data',
    note = 'Canonical repository entry for the unified trading data-production component. Owns provider feed adapters, model-scoped source tables, and deterministic point-in-time feature tables; remote: https://github.com/gilmore307/trading-data.git',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'TRADING_SOURCE_REPO';

DELETE FROM trading_registry
WHERE key = 'TRADING_DERIVED_REPO';

UPDATE trading_registry
SET
    kind = 'data_feature',
    key = 'FEATURE_01_MARKET_REGIME',
    payload = 'feature_01_market_regime',
    path = 'trading-data/src/data_feature/feature_01_market_regime',
    applies_to = 'trading-data;trading-model;market_regime_model;source_01_market_regime',
    artifact_sync_policy = 'registry_only',
    note = 'Layer 1 MarketRegimeModel deterministic feature-output boundary and total V1 wide table. Each row is one 30-minute point-in-time market-regime feature snapshot keyed by snapshot_time; generated feature columns cover returns, relative strength, volatility, trend/momentum, and correlation/market breadth. Concrete generated feature columns such as spy_return_30m are governed by reviewed feature-family rules/catalogs and are not individually registered as registry rows.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'DERIVED_01_MARKET_REGIME';

UPDATE trading_registry
SET
    path = replace(replace(replace(replace(path,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'data_sources', 'data_source'),
        'data_derived/derived_01_market_regime', 'data_feature/feature_01_market_regime'),
    applies_to = replace(replace(replace(replace(applies_to,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'derived_01_market_regime', 'feature_01_market_regime'),
        'DERIVED_01_MARKET_REGIME', 'FEATURE_01_MARKET_REGIME'),
    note = replace(replace(replace(replace(replace(replace(note,
        'trading-source', 'trading-data'),
        'trading-derived', 'trading-data'),
        'trading_source.source_01_market_regime', 'trading_data.source_01_market_regime'),
        'trading_derived.derived_01_market_regime', 'trading_data.feature_01_market_regime'),
        'derived_01_market_regime', 'feature_01_market_regime'),
        'derived-output', 'feature-output'),
    updated_at = CURRENT_TIMESTAMP
WHERE path LIKE '%trading-source%'
   OR path LIKE '%trading-derived%'
   OR path LIKE '%data_sources%'
   OR path LIKE '%data_derived/derived_01_market_regime%'
   OR applies_to LIKE '%trading-source%'
   OR applies_to LIKE '%trading-derived%'
   OR applies_to LIKE '%derived_01_market_regime%'
   OR note LIKE '%trading-source%'
   OR note LIKE '%trading-derived%'
   OR note LIKE '%trading_source.source_01_market_regime%'
   OR note LIKE '%trading_derived.derived_01_market_regime%'
   OR note LIKE '%derived_01_market_regime%';

UPDATE trading_registry
SET
    applies_to = replace(applies_to, 'data_sources', 'data_source'),
    note = replace(note, 'data_sources', 'data_source'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%data_sources%'
   OR note LIKE '%data_sources%';

UPDATE trading_registry
SET
    applies_to = replace(applies_to, 'trading_data;trading_data', 'trading-data'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%trading_data;trading_data%';

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
  'data_feature',
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

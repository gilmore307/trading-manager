-- Register the Layer 1 frame/horizon row identity now owned by source, feature,
-- model, support artifact, and evaluation surfaces.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_MRMFRAME',
    'classification_field',
    'INPUT_FRAME',
    'field_name',
    'input_frame',
    'trading-data/docs/10_layer_01_market_regime.md;trading-model/docs/10_layer_01_market_regime.md',
    'feature_01_market_regime;model_01_market_regime;model_01_market_regime_explainability;model_01_market_regime_diagnostics;market_regime_model',
    'registry_only',
    'Layer 1 row-identity field for the point-in-time input frame used to build market-state evidence, such as 1min, 5min, 30min, or 1d.'
  ),
  (
    'fld_MRMHORIZ',
    'classification_field',
    'PREDICTION_HORIZON',
    'field_name',
    'prediction_horizon',
    'trading-data/docs/10_layer_01_market_regime.md;trading-model/docs/10_layer_01_market_regime.md',
    'feature_01_market_regime;model_01_market_regime;model_01_market_regime_explainability;model_01_market_regime_diagnostics;market_regime_model',
    'registry_only',
    'Layer 1 row-identity field for the forecast horizon evaluated from the current input frame, such as 5min, 30min, 1d, 5d, or 20d.'
  ),
  (
    'fld_MRMUNIV',
    'classification_field',
    'MARKET_UNIVERSE_REF',
    'field_name',
    'market_universe_ref',
    'trading-data/docs/10_layer_01_market_regime.md;trading-model/docs/10_layer_01_market_regime.md',
    'feature_01_market_regime;model_01_market_regime;model_01_market_regime_explainability;model_01_market_regime_diagnostics;market_regime_model',
    'registry_only',
    'Layer 1 row-identity field for the reviewed market universe/config reference used to build the market-state row.'
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
SET note = 'Layer 1 MarketRegimeModel deterministic feature-output boundary. Each row is one point-in-time market-regime feature snapshot keyed by snapshot_time, input_frame, prediction_horizon, and market_universe_ref; generated feature values are stored as model-local keys in feature_payload_json JSONB to avoid PostgreSQL row-size limits. Future return, volatility, drawdown, transition, and tradability outcomes are labels/evaluation evidence only, not same-row construction input.',
    applies_to = 'trading-data;trading-model;market_regime_model;source_01_market_regime;input_frame;prediction_horizon;market_universe_ref',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'FEATURE_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Accepted Layer 1 MarketRegimeModel output table for direction-neutral market-context state vectors keyed by available_time, input_frame, prediction_horizon, and market_universe_ref. Public 1_* state columns remain unsuffixed; row identity carries the frame/horizon contract.',
    applies_to = 'trading-model;trading-data;market_regime_model;feature_01_market_regime;input_frame;prediction_horizon;market_universe_ref;direction_neutral_tradability',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MODEL_01_MARKET_REGIME';

UPDATE trading_registry
SET note = 'Accepted Layer 1 MarketRegimeModel explainability artifact/table name. Rows use the same available_time, input_frame, prediction_horizon, and market_universe_ref identity as model_01_market_regime plus factor_name.',
    applies_to = 'trading-model;market_regime_model;model_01_market_regime;input_frame;prediction_horizon;market_universe_ref',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MODEL_01_MARKET_REGIME_EXPLAINABILITY';

UPDATE trading_registry
SET note = 'Accepted Layer 1 MarketRegimeModel diagnostics artifact/table name. Rows use the same available_time, input_frame, prediction_horizon, and market_universe_ref identity as model_01_market_regime and own freshness, missingness, coverage, and leakage diagnostics.',
    applies_to = 'trading-model;market_regime_model;model_01_market_regime;input_frame;prediction_horizon;market_universe_ref',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'MODEL_01_MARKET_REGIME_DIAGNOSTICS';

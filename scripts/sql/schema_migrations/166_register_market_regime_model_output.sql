INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
    'dki_MRMV001',
    'data_kind',
    'MODEL_01_MARKET_REGIME',
    'text',
    'model_01_market_regime',
    'trading-model/src/model_outputs/model_01_market_regime',
    'trading-model;trading-derived;market_regime_model;derived_01_market_regime',
    'registry_only',
    'Layer 1 MarketRegimeModel V1 model-output boundary. Each row is one point-in-time continuous market-state vector keyed by available_time and written to trading_model.model_01_market_regime. V1 does not require clustering, hard state ids, state probabilities, or human-readable regime labels.'
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

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_MRM001', 'temporal_field', 'AVAILABLE_TIME', 'field_name', 'available_time', NULL, 'model_01_market_regime;source_02_security_selection;source_07_event_overlay', 'sync_artifact', 'Timestamp when evidence or model output became visible to the system for point-in-time use. Temporal value format: ISO 8601; normalized final outputs use America/New_York semantics unless explicitly reviewed otherwise.'),
  ('fld_MRM002', 'field', 'TREND_FACTOR', 'field_name', 'trend_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing broad risk-asset trend strength.'),
  ('fld_MRM003', 'field', 'VOLATILITY_STRESS_FACTOR', 'field_name', 'volatility_stress_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing realized-volatility and VIXY-proxy stress.'),
  ('fld_MRM004', 'field', 'CORRELATION_STRESS_FACTOR', 'field_name', 'correlation_stress_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing market-state cross-asset correlation stress.'),
  ('fld_MRM005', 'field', 'CREDIT_STRESS_FACTOR', 'field_name', 'credit_stress_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing credit-risk pressure using reviewed HYG/LQD signals.'),
  ('fld_MRM006', 'field', 'RATE_PRESSURE_FACTOR', 'field_name', 'rate_pressure_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing duration/rate pressure using reviewed Treasury ETF relative-strength signals.'),
  ('fld_MRM007', 'field', 'DOLLAR_PRESSURE_FACTOR', 'field_name', 'dollar_pressure_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing UUP/dollar pressure.'),
  ('fld_MRM008', 'field', 'COMMODITY_PRESSURE_FACTOR', 'field_name', 'commodity_pressure_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing commodity and commodity-relative pressure.'),
  ('fld_MRM009', 'field', 'SECTOR_ROTATION_FACTOR', 'field_name', 'sector_rotation_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing sector-rotation intensity and dispersion.'),
  ('fld_MRM010', 'field', 'BREADTH_FACTOR', 'field_name', 'breadth_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing sector-observation breadth and equal-weight participation.'),
  ('fld_MRM011', 'field', 'RISK_APPETITE_FACTOR', 'field_name', 'risk_appetite_factor', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 factor summarizing risk appetite across relative-strength and safe-haven signals.'),
  ('fld_MRM012', 'field', 'TRANSITION_PRESSURE', 'field_name', 'transition_pressure', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 metric summarizing recent state-vector movement between adjacent model rows.'),
  ('fld_MRM013', 'field', 'DATA_QUALITY_SCORE', 'field_name', 'data_quality_score', NULL, 'model_01_market_regime', 'sync_artifact', 'Continuous MarketRegimeModel V1 metric summarizing observed signal-column coverage for the row.')
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

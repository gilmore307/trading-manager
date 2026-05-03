-- Align model registry terms with the current trading-model route.
-- Layer 1 now exposes market-property factors and a conceptual
-- market_context_state, not the older proxy-dashboard factor set.

UPDATE trading_registry
SET
    path = 'trading-model/docs/07_system_model_architecture_rfc.md',
    applies_to = 'trading-model;trading-data;market_regime_model;feature_01_market_regime',
    note = 'Accepted Layer 1 MarketRegimeModel V1 model-output term for the continuous market-property vector written to trading_model.model_01_market_regime and consumed conceptually as market_context_state. V1 does not rank sectors, ETFs, stocks, or strategies and does not require clustering or hard regime labels.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'dki_MRMV001';

DELETE FROM trading_registry
WHERE id IN (
    'fld_MRM002', -- TREND_FACTOR
    'fld_MRM003', -- VOLATILITY_STRESS_FACTOR
    'fld_MRM004', -- CORRELATION_STRESS_FACTOR
    'fld_MRM005', -- CREDIT_STRESS_FACTOR
    'fld_MRM006', -- RATE_PRESSURE_FACTOR
    'fld_MRM007', -- DOLLAR_PRESSURE_FACTOR
    'fld_MRM008', -- COMMODITY_PRESSURE_FACTOR
    'fld_MRM009', -- SECTOR_ROTATION_FACTOR
    'fld_MRM010', -- BREADTH_FACTOR
    'fld_MRM011'  -- RISK_APPETITE_FACTOR
);

UPDATE trading_registry
SET
    note = 'Continuous MarketRegimeModel V1 metric summarizing adjacent-row movement in the current market-property vector.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_MRM012';

UPDATE trading_registry
SET
    note = 'Continuous MarketRegimeModel V1 metric summarizing observed signal coverage and reliability for the row.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'fld_MRM013';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_MRM014', 'field', 'PRICE_BEHAVIOR_FACTOR', 'field_name', 'price_behavior_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing broad price behavior.'),
  ('fld_MRM015', 'field', 'TREND_CERTAINTY_FACTOR', 'field_name', 'trend_certainty_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing broad trend certainty and persistence.'),
  ('fld_MRM016', 'field', 'CAPITAL_FLOW_FACTOR', 'field_name', 'capital_flow_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing broad capital-flow, funding, and liquidity pressure.'),
  ('fld_MRM017', 'field', 'SENTIMENT_FACTOR', 'field_name', 'sentiment_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing broad sentiment and risk appetite.'),
  ('fld_MRM018', 'field', 'VALUATION_PRESSURE_FACTOR', 'field_name', 'valuation_pressure_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing valuation and discount-rate pressure.'),
  ('fld_MRM019', 'field', 'FUNDAMENTAL_STRENGTH_FACTOR', 'field_name', 'fundamental_strength_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing broad fundamental strength or its current reviewed proxy.'),
  ('fld_MRM020', 'field', 'MACRO_ENVIRONMENT_FACTOR', 'field_name', 'macro_environment_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing macro and policy environment pressure.'),
  ('fld_MRM021', 'field', 'MARKET_STRUCTURE_FACTOR', 'field_name', 'market_structure_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing market-wide structure, breadth, concentration, crowding, and correlation.'),
  ('fld_MRM022', 'field', 'RISK_STRESS_FACTOR', 'field_name', 'risk_stress_factor', NULL, 'model_01_market_regime;market_context_state', 'sync_artifact', 'Layer 1 MarketRegimeModel V1 market-property factor summarizing risk stress, tail pressure, and fragility.')
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

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_MCS001', 'term', 'MARKET_CONTEXT_STATE', 'text', 'market_context_state', 'trading-model/docs/07_system_model_architecture_rfc.md', 'trading-model;market_regime_model;model_01_market_regime', 'registry_only', 'Conceptual Layer 1 downstream state wrapping the current MarketRegimeModel market-property factors. It is context only, not sector/ETF/stock ranking.'),
  ('trm_M2S001', 'term', 'MODEL_02_SECURITY_SELECTION', 'text', 'model_02_security_selection', 'trading-model/docs/07_system_model_architecture_rfc.md', 'trading-model;security_selection_model;feature_02_security_selection', 'registry_only', 'Planned Layer 2 SecuritySelectionModel model-output term for sector/industry context state; physical table/artifact contract remains pending implementation.'),
  ('trm_SCS001', 'term', 'SECTOR_CONTEXT_STATE', 'text', 'sector_context_state', 'trading-model/docs/07_system_model_architecture_rfc.md', 'trading-model;security_selection_model;model_02_security_selection', 'registry_only', 'Conceptual Layer 2 sector/industry state: inferred sector attributes, market-condition profile, trend stability, composition, tradability, risk context, and eligibility.'),
  ('trm_TCI001', 'term', 'TARGET_CANDIDATE_ID', 'text', 'target_candidate_id', 'trading-model/docs/07_system_model_architecture_rfc.md', 'trading-model;strategy_selection_model;anonymous_target_candidate_builder', 'registry_only', 'Stable anonymous identifier for a strategy-aware target candidate. Real symbols remain audit/routing metadata outside model-facing fitting vectors.'),
  ('trm_ATF001', 'term', 'ANONYMOUS_TARGET_FEATURE_VECTOR', 'text', 'anonymous_target_feature_vector', 'trading-model/docs/07_system_model_architecture_rfc.md', 'trading-model;strategy_selection_model;anonymous_target_candidate_builder', 'registry_only', 'Model-facing target candidate feature vector that excludes ticker/company identity and carries behavior, liquidity, market, sector, event, risk, and cost context.')
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

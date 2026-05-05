-- Register V2.2 direction-neutral tradability taxonomy names introduced by
-- trading-model d5e71b3. These are registry-level shared names; physical
-- implementations may still carry compatibility fields until reviewed migrations.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_VTAX001',
    'term',
    'MODEL_VECTOR_TAXONOMY',
    'text',
    'trading-model/docs/92_vector_taxonomy.md',
    'trading-model/docs/92_vector_taxonomy.md',
    'trading-model;trading-manager;model_layer_naming;direction_neutral_tradability',
    'registry_only',
    'Accepted V2.2 vector/state taxonomy reference for feature/vector/state/score/diagnostics/explainability/label naming discipline across model layers.'
  ),
  (
    'trm_ACM001',
    'term',
    'ALPHA_CONFIDENCE_MODEL',
    'text',
    'alpha_confidence_model',
    'trading-model/docs/90_system_model_architecture_rfc.md',
    'trading-model;target_state_vector;model_04_alpha_confidence',
    'registry_only',
    'Accepted canonical Layer 4 model id. AlphaConfidenceModel maps target_state_vector outputs to long/short alpha or direction confidence, expected value, risk, and uncertainty; it is separate from Layer 3 direction evidence.'
  ),
  (
    'trm_MAC001',
    'term',
    'MODEL_04_ALPHA_CONFIDENCE',
    'text',
    'model_04_alpha_confidence',
    'trading-model/docs/90_system_model_architecture_rfc.md',
    'trading-model;alpha_confidence_model;target_state_vector',
    'registry_only',
    'Accepted Layer 4 AlphaConfidenceModel model-output surface name for future promoted confidence/expected-value outputs.'
  ),
  (
    'trm_TPM001',
    'term',
    'TRADING_PROJECTION_MODEL',
    'text',
    'trading_projection_model',
    'trading-model/docs/90_system_model_architecture_rfc.md',
    'trading-model;alpha_confidence_model;model_05_trading_projection',
    'registry_only',
    'Accepted canonical Layer 5 model id. TradingProjectionModel maps confidence plus position/cost/risk context to offline target actions and target exposure; it is not live execution.'
  ),
  (
    'trm_MTP001',
    'term',
    'MODEL_05_TRADING_PROJECTION',
    'text',
    'model_05_trading_projection',
    'trading-model/docs/90_system_model_architecture_rfc.md',
    'trading-model;trading_projection_model;alpha_confidence_model',
    'registry_only',
    'Accepted Layer 5 TradingProjectionModel model-output surface name for future promoted offline trading projection outputs.'
  ),
  (
    'fld_MRMV22001',
    'field',
    'MARKET_DIRECTION_SCORE',
    'field_name',
    '1_market_direction_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for signed broad market direction evidence. The sign is not a trade instruction or quality score.'
  ),
  (
    'fld_MRMV22002',
    'field',
    'MARKET_DIRECTION_STRENGTH_SCORE',
    'field_name',
    '1_market_direction_strength_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for broad market direction-evidence magnitude, separated from signed direction and trend quality.'
  ),
  (
    'fld_MRMV22003',
    'field',
    'MARKET_TREND_QUALITY_SCORE',
    'field_name',
    '1_market_trend_quality_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for structural clarity of the broad market trend independent of long/short sign.'
  ),
  (
    'fld_MRMV22004',
    'field',
    'MARKET_STABILITY_SCORE',
    'field_name',
    '1_market_stability_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for broad market persistence/smoothness and resistance to whipsaw.'
  ),
  (
    'fld_MRMV22005',
    'field',
    'MARKET_RISK_STRESS_SCORE',
    'field_name',
    '1_market_risk_stress_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for broad market risk/stress pressure; higher values indicate more stress.'
  ),
  (
    'fld_MRMV22006',
    'field',
    'MARKET_TRANSITION_RISK_SCORE',
    'field_name',
    '1_market_transition_risk_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for state-switch/decay/fragility risk in broad market context.'
  ),
  (
    'fld_MRMV22007',
    'field',
    'BREADTH_PARTICIPATION_SCORE',
    'field_name',
    '1_breadth_participation_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for broad market participation/breadth support.'
  ),
  (
    'fld_MRMV22008',
    'field',
    'CORRELATION_CROWDING_SCORE',
    'field_name',
    '1_correlation_crowding_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for broad market correlation/crowding pressure.'
  ),
  (
    'fld_MRMV22009',
    'field',
    'DISPERSION_OPPORTUNITY_SCORE',
    'field_name',
    '1_dispersion_opportunity_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for dispersion/opportunity context in broad market state.'
  ),
  (
    'fld_MRMV22010',
    'field',
    'MARKET_LIQUIDITY_PRESSURE_SCORE',
    'field_name',
    '1_market_liquidity_pressure_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for broad market liquidity stress/cost pressure.'
  ),
  (
    'fld_MRMV22011',
    'field',
    'MARKET_LIQUIDITY_SUPPORT_SCORE',
    'field_name',
    '1_market_liquidity_support_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for liquidity/depth/capacity support in broad market state.'
  ),
  (
    'fld_MRMV22012',
    'field',
    'MARKET_COVERAGE_SCORE',
    'field_name',
    '1_coverage_score',
    NULL,
    'model_01_market_regime;market_context_state;direction_neutral_tradability',
    'registry_only',
    'V2.2 Layer 1 target field for evidence completeness. This is not trend certainty or opportunity.'
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
SET path = 'trading-model/docs/92_vector_taxonomy.md',
    applies_to = 'trading-model;model_03_target_state_vector;target_state_vector_model;anonymous_target_candidate_builder;direction_neutral_tradability',
    note = 'Layer 3 preprocessing/input feature vector consumed by TargetStateVectorModel. It excludes ticker/company identity and is not the model output state vector; target_state_vector remains the Layer 3 output.',
    updated_at = CURRENT_TIMESTAMP
WHERE key = 'ANONYMOUS_TARGET_FEATURE_VECTOR';

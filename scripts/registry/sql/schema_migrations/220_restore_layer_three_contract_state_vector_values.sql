-- Restore Layer 3 TargetStateVector payload names to the reviewed contracts.
-- Migration 219 over-prefixed every state_vector_value, but trading-data and
-- trading-model still consume bare TargetStateVector block/group/window/enum tokens.
-- Keep compact 3_* only where the reviewed Layer 3 scalar score fields use it.

WITH restored_values(id, restored_key, restored_payload, restored_applies_to) AS (
  VALUES
    ('fld_TSV007', 'MARKET_STATE_FEATURES', 'market_state_features', 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV008', 'SECTOR_STATE_FEATURES', 'sector_state_features', 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV009', 'TARGET_STATE_FEATURES', 'target_state_features', 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV010', 'CROSS_STATE_FEATURES', 'cross_state_features', 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV011', 'STATE_OBSERVATION_WINDOWS', 'state_observation_windows', 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;market_state_features;sector_state_features;target_state_features;cross_state_features'),
    ('fld_TSV012', 'STATE_WINDOW_SYNC_POLICY', 'state_window_sync_policy', 'model_03_target_state_vector;feature_03_target_state_vector;target_state_vector_model;market_state_features;sector_state_features;target_state_features;cross_state_features'),
    ('fld_TSV013', 'FEATURE_QUALITY_DIAGNOSTICS', 'feature_quality_diagnostics', 'feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV015', 'SECTOR_RELATIVE_DIRECTION_STATE', 'sector_relative_direction_state', 'sector_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context'),
    ('fld_TSV016', 'SECTOR_TREND_QUALITY_STABILITY_STATE', 'sector_trend_quality_stability_state', 'sector_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context'),
    ('fld_TSV017', 'TARGET_DIRECTION_RETURN_SHAPE', 'target_direction_return_shape', 'target_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV018', 'TARGET_TREND_QUALITY_STATE', 'target_trend_quality_state', 'target_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV019', 'TARGET_LIQUIDITY_TRADABILITY_STATE', 'target_liquidity_tradability_state', 'target_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV020', 'TARGET_VS_MARKET_RESIDUAL_DIRECTION', 'target_vs_market_residual_direction', 'cross_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV021', 'TARGET_VS_SECTOR_RESIDUAL_DIRECTION', 'target_vs_sector_residual_direction', 'cross_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV022', 'RELATIVE_LIQUIDITY_TRADABILITY_STATE', 'relative_liquidity_tradability_state', 'cross_state_features;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV023', 'MARKET_REGIME_STATE', 'market_regime_state', 'market_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_01_market_regime'),
    ('fld_TSV024', 'MARKET_TREND_STATE', 'market_trend_state', 'market_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_01_market_regime'),
    ('fld_TSV025', 'MARKET_VOLATILITY_STATE', 'market_volatility_state', 'market_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_01_market_regime'),
    ('fld_TSV026', 'MARKET_BREADTH_STATE', 'market_breadth_state', 'market_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_01_market_regime'),
    ('fld_TSV027', 'MARKET_LIQUIDITY_STRESS_STATE', 'market_liquidity_stress_state', 'market_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_01_market_regime'),
    ('fld_TSV028', 'MARKET_CORRELATION_STATE', 'market_correlation_state', 'market_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_01_market_regime'),
    ('fld_TSV029', 'SECTOR_VOLATILITY_STATE', 'sector_volatility_state', 'sector_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context'),
    ('fld_TSV030', 'SECTOR_BREADTH_DISPERSION_STATE', 'sector_breadth_dispersion_state', 'sector_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context'),
    ('fld_TSV031', 'SECTOR_LIQUIDITY_TRADABILITY_STATE', 'sector_liquidity_tradability_state', 'sector_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model;model_02_sector_context'),
    ('fld_TSV032', 'TARGET_VOLATILITY_RANGE_STATE', 'target_volatility_range_state', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV033', 'TARGET_GAP_JUMP_STATE', 'target_gap_jump_state', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV034', 'TARGET_VOLUME_ACTIVITY_STATE', 'target_volume_activity_state', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV035', 'TARGET_VWAP_LOCATION_STATE', 'target_vwap_location_state', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV036', 'TARGET_SESSION_POSITION_STATE', 'target_session_position_state', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV037', 'TARGET_DATA_QUALITY_STATE', 'target_data_quality_state', 'target_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV038', 'TARGET_VS_MARKET_VOLATILITY', 'target_vs_market_volatility', 'cross_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV039', 'TARGET_VS_SECTOR_VOLATILITY', 'target_vs_sector_volatility', 'cross_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV040', 'TARGET_MARKET_BETA_CORRELATION', 'target_market_beta_correlation', 'cross_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV041', 'TARGET_SECTOR_BETA_CORRELATION', 'target_sector_beta_correlation', 'cross_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV042', 'SECTOR_CONFIRMATION_STATE', 'sector_confirmation_state', 'cross_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV043', 'IDIOSYNCRATIC_RESIDUAL_STATE', 'idiosyncratic_residual_state', 'cross_state_features;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV044', 'TARGET_DIRECTION_SCORE_BY_WINDOW', '3_target_direction_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV045', 'TARGET_TREND_QUALITY_SCORE_BY_WINDOW', '3_target_trend_quality_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV046', 'TARGET_PATH_STABILITY_SCORE_BY_WINDOW', '3_target_path_stability_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV047', 'TARGET_NOISE_SCORE_BY_WINDOW', '3_target_noise_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV048', 'TARGET_TRANSITION_RISK_SCORE_BY_WINDOW', '3_target_transition_risk_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV049', 'TARGET_LIQUIDITY_TRADABILITY_SCORE', '3_target_liquidity_tradability_score', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV050', 'CONTEXT_DIRECTION_ALIGNMENT_SCORE_BY_WINDOW', '3_context_direction_alignment_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV051', 'CONTEXT_SUPPORT_QUALITY_SCORE_BY_WINDOW', '3_context_support_quality_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV052', 'TARGET_STATE_TRADABILITY_SCORE_BY_WINDOW', '3_tradability_score_<window>', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV053', 'TARGET_STATE_QUALITY_SCORE', '3_state_quality_score', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV054', 'TARGET_STATE_EVIDENCE_COUNT', '3_evidence_count', 'score_payload;target_state_vector;model_03_target_state_vector;target_state_vector_model;model_evaluation;promotion_evidence'),
    ('fld_TSV055', 'TARGET_STATE_VECTOR_PAYLOAD', 'target_state_vector', 'target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV056', 'TARGET_STATE_SCORE_PAYLOAD', 'score_payload', 'target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV057', 'TARGET_STATE_EMBEDDING', 'target_state_embedding', 'target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV058', 'STATE_CLUSTER_ID', 'state_cluster_id', 'target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('fld_TSV059', 'STATE_QUALITY_DIAGNOSTICS', 'state_quality_diagnostics', 'target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('trm_TSVSC001', 'SECTOR_CONFIRMATION_STATE_CONFIRMED', 'sector_confirmed', 'sector_confirmation_state;cross_state_features;target_state_vector;target_state_vector_model'),
    ('trm_TSVSC002', 'SECTOR_CONFIRMATION_STATE_DIVERGENT', 'sector_divergent', 'sector_confirmation_state;cross_state_features;target_state_vector;target_state_vector_model'),
    ('trm_TSVSC003', 'SECTOR_CONFIRMATION_STATE_FLAT_OR_MIXED', 'flat_or_mixed', 'sector_confirmation_state;cross_state_features;target_state_vector;target_state_vector_model'),
    ('trm_TSVWIN001', 'TARGET_STATE_WINDOW_5MIN', '5min', 'state_observation_windows;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('trm_TSVWIN002', 'TARGET_STATE_WINDOW_15MIN', '15min', 'state_observation_windows;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('trm_TSVWIN003', 'TARGET_STATE_WINDOW_60MIN', '60min', 'state_observation_windows;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('trm_TSVWIN004', 'TARGET_STATE_WINDOW_390MIN', '390min', 'state_observation_windows;target_state_vector;feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model'),
    ('trm_TSVWP001', 'TARGET_SESSION_WINDOW_POLICY_COMPLETED_1MIN_BARS', 'completed_1min_bars', 'target_session_position_state;target_state_features;feature_03_target_state_vector;target_state_vector_model')
)
UPDATE trading_registry r
SET key = restored_values.restored_key,
    payload = restored_values.restored_payload,
    applies_to = restored_values.restored_applies_to,
    updated_at = CURRENT_TIMESTAMP
FROM restored_values
WHERE r.id = restored_values.id
  AND r.kind = 'state_vector_value'
  AND (r.key IS DISTINCT FROM restored_values.restored_key
       OR r.payload IS DISTINCT FROM restored_values.restored_payload
       OR r.applies_to IS DISTINCT FROM restored_values.restored_applies_to);

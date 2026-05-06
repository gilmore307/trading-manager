-- Restore Layer 1/2 state-vector keys after migration 219.
-- The payloads already keep reviewed compact 1_* and 2_* names, but registry
-- keys should preserve the accepted contract rows rather than inventing
-- MODEL_NN_*_VALUE aliases for existing state-vector values.

WITH restored_values(id, restored_key, restored_payload, restored_applies_to) AS (
  VALUES
    ('fld_MRMV22001', 'MARKET_DIRECTION_SCORE', '1_market_direction_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22002', 'MARKET_DIRECTION_STRENGTH_SCORE', '1_market_direction_strength_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22003', 'MARKET_TREND_QUALITY_SCORE', '1_market_trend_quality_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22004', 'MARKET_STABILITY_SCORE', '1_market_stability_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22005', 'MARKET_RISK_STRESS_SCORE', '1_market_risk_stress_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22006', 'MARKET_TRANSITION_RISK_SCORE', '1_market_transition_risk_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22007', 'BREADTH_PARTICIPATION_SCORE', '1_breadth_participation_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22008', 'CORRELATION_CROWDING_SCORE', '1_correlation_crowding_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22009', 'DISPERSION_OPPORTUNITY_SCORE', '1_dispersion_opportunity_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22010', 'MARKET_LIQUIDITY_PRESSURE_SCORE', '1_market_liquidity_pressure_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22011', 'MARKET_LIQUIDITY_SUPPORT_SCORE', '1_market_liquidity_support_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22012', 'MARKET_COVERAGE_SCORE', '1_coverage_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_MRMV22013', 'MARKET_DATA_QUALITY_SCORE', '1_data_quality_score', 'model_01_market_regime;market_context_state;direction_neutral_tradability'),
    ('fld_SCMV22001', 'SECTOR_RELATIVE_DIRECTION_SCORE', '2_sector_relative_direction_score', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22002', 'SECTOR_TREND_QUALITY_SCORE', '2_sector_trend_quality_score', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22003', 'SECTOR_TREND_STABILITY_SCORE', '2_sector_trend_stability_score', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22004', 'SECTOR_TRANSITION_RISK_SCORE', '2_sector_transition_risk_score', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22005', 'MARKET_CONTEXT_SUPPORT_SCORE', '2_market_context_support_score', 'model_02_sector_context;sector_context_state;sector_context_model;model_01_market_regime'),
    ('fld_SCMV22006', 'SECTOR_BREADTH_CONFIRMATION_SCORE', '2_sector_breadth_confirmation_score', 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context'),
    ('fld_SCMV22007', 'SECTOR_DISPERSION_CROWDING_SCORE', '2_sector_dispersion_crowding_score', 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context'),
    ('fld_SCMV22008', 'SECTOR_LIQUIDITY_TRADABILITY_SCORE', '2_sector_liquidity_tradability_score', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22009', 'SECTOR_TRADABILITY_SCORE', '2_sector_tradability_score', 'model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder'),
    ('fld_SCMV22010', 'SECTOR_HANDOFF_STATE', '2_sector_handoff_state', 'model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder'),
    ('fld_SCMV22011', 'SECTOR_HANDOFF_BIAS', '2_sector_handoff_bias', 'model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder'),
    ('fld_SCMV22012', 'SECTOR_HANDOFF_RANK', '2_sector_handoff_rank', 'model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder'),
    ('fld_SCMV22013', 'SECTOR_HANDOFF_REASON_CODES', '2_sector_handoff_reason_codes', 'model_02_sector_context;sector_context_state;sector_context_model;anonymous_target_candidate_builder'),
    ('fld_SCMV22014', 'SECTOR_ELIGIBILITY_STATE', '2_eligibility_state', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22015', 'SECTOR_ELIGIBILITY_REASON_CODES', '2_eligibility_reason_codes', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22016', 'SECTOR_STATE_QUALITY_SCORE', '2_state_quality_score', 'model_02_sector_context;sector_context_state;sector_context_model'),
    ('fld_SCMV22017', 'SECTOR_COVERAGE_SCORE', '2_coverage_score', 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context'),
    ('fld_SCMV22018', 'SECTOR_DATA_QUALITY_SCORE', '2_data_quality_score', 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context'),
    ('fld_SCMV22019', 'SECTOR_EVIDENCE_COUNT', '2_evidence_count', 'model_02_sector_context;sector_context_state;sector_context_model;feature_02_sector_context'),
    ('svv_SCME001', 'SECTOR_ELIGIBILITY_STATE_ELIGIBLE', 'eligible', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model'),
    ('svv_SCME002', 'SECTOR_ELIGIBILITY_STATE_WATCH', 'watch', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model'),
    ('svv_SCME003', 'SECTOR_ELIGIBILITY_STATE_EXCLUDED', 'excluded', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model'),
    ('svv_SCME004', 'SECTOR_ELIGIBILITY_STATE_INSUFFICIENT_DATA', 'insufficient_data', '2_eligibility_state;model_02_sector_context;sector_context_state;sector_context_model'),
    ('trm_SCMB001', 'SECTOR_HANDOFF_BIAS_LONG_BIAS', 'long_bias', '2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMB002', 'SECTOR_HANDOFF_BIAS_SHORT_BIAS', 'short_bias', '2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMB003', 'SECTOR_HANDOFF_BIAS_NEUTRAL', 'neutral', '2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMB004', 'SECTOR_HANDOFF_BIAS_MIXED', 'mixed', '2_sector_handoff_bias;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMHS001', 'SECTOR_HANDOFF_STATE_SELECTED', 'selected', '2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMHS002', 'SECTOR_HANDOFF_STATE_WATCH', 'watch', '2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMHS003', 'SECTOR_HANDOFF_STATE_BLOCKED', 'blocked', '2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model'),
    ('trm_SCMHS004', 'SECTOR_HANDOFF_STATE_INSUFFICIENT_DATA', 'insufficient_data', '2_sector_handoff_state;model_02_sector_context;anonymous_target_candidate_builder;sector_context_state;sector_context_model')
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

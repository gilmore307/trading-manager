-- Restore TargetStateVector semantic payloads to the contract-owned tokens used by
-- trading-data and trading-model. Numeric prefixes remain only on compact Layer 3
-- scalar score field families such as 3_target_direction_score_<window>.

WITH restore_tokens(prefixed, bare) AS (
  VALUES
    ('3_cross_state_features', 'cross_state_features'),
    ('3_feature_quality_diagnostics', 'feature_quality_diagnostics'),
    ('3_idiosyncratic_residual_state', 'idiosyncratic_residual_state'),
    ('3_market_breadth_state', 'market_breadth_state'),
    ('3_market_correlation_state', 'market_correlation_state'),
    ('3_market_liquidity_stress_state', 'market_liquidity_stress_state'),
    ('3_market_regime_state', 'market_regime_state'),
    ('3_market_state_features', 'market_state_features'),
    ('3_market_trend_state', 'market_trend_state'),
    ('3_market_volatility_state', 'market_volatility_state'),
    ('3_relative_liquidity_tradability_state', 'relative_liquidity_tradability_state'),
    ('3_sector_breadth_dispersion_state', 'sector_breadth_dispersion_state'),
    ('3_sector_confirmation_state', 'sector_confirmation_state'),
    ('3_sector_confirmed', 'sector_confirmed'),
    ('3_sector_divergent', 'sector_divergent'),
    ('3_flat_or_mixed', 'flat_or_mixed'),
    ('3_sector_liquidity_tradability_state', 'sector_liquidity_tradability_state'),
    ('3_sector_relative_direction_state', 'sector_relative_direction_state'),
    ('3_sector_state_features', 'sector_state_features'),
    ('3_sector_trend_quality_stability_state', 'sector_trend_quality_stability_state'),
    ('3_sector_volatility_state', 'sector_volatility_state'),
    ('3_state_cluster_id', 'state_cluster_id'),
    ('3_state_observation_windows', 'state_observation_windows'),
    ('3_state_quality_diagnostics', 'state_quality_diagnostics'),
    ('3_state_window_sync_policy', 'state_window_sync_policy'),
    ('3_target_data_quality_state', 'target_data_quality_state'),
    ('3_target_direction_return_shape', 'target_direction_return_shape'),
    ('3_target_gap_jump_state', 'target_gap_jump_state'),
    ('3_target_liquidity_tradability_state', 'target_liquidity_tradability_state'),
    ('3_target_market_beta_correlation', 'target_market_beta_correlation'),
    ('3_target_sector_beta_correlation', 'target_sector_beta_correlation'),
    ('3_target_session_position_state', 'target_session_position_state'),
    ('3_completed_1min_bars', 'completed_1min_bars'),
    ('3_target_state_embedding', 'target_state_embedding'),
    ('3_target_state_features', 'target_state_features'),
    ('3_score_payload', 'score_payload'),
    ('3_target_state_vector', 'target_state_vector'),
    ('3_15min', '15min'),
    ('3_390min', '390min'),
    ('3_5min', '5min'),
    ('3_60min', '60min'),
    ('3_target_trend_quality_state', 'target_trend_quality_state'),
    ('3_target_volatility_range_state', 'target_volatility_range_state'),
    ('3_target_volume_activity_state', 'target_volume_activity_state'),
    ('3_target_vs_market_residual_direction', 'target_vs_market_residual_direction'),
    ('3_target_vs_market_volatility', 'target_vs_market_volatility'),
    ('3_target_vs_sector_residual_direction', 'target_vs_sector_residual_direction'),
    ('3_target_vs_sector_volatility', 'target_vs_sector_volatility'),
    ('3_target_vwap_location_state', 'target_vwap_location_state')
), updated_scopes AS (
  SELECT r.id,
         STRING_AGG(COALESCE(t.bare, token.value), ';' ORDER BY token.ordinality) AS applies_to
  FROM trading_registry r
  CROSS JOIN LATERAL UNNEST(STRING_TO_ARRAY(r.applies_to, ';')) WITH ORDINALITY AS token(value, ordinality)
  LEFT JOIN restore_tokens t ON token.value = t.prefixed
  WHERE r.applies_to IS NOT NULL
  GROUP BY r.id
)
UPDATE trading_registry r
SET applies_to = updated_scopes.applies_to,
    updated_at = CURRENT_TIMESTAMP
FROM updated_scopes
WHERE r.id = updated_scopes.id
  AND r.applies_to IS DISTINCT FROM updated_scopes.applies_to;

WITH restore_tokens(prefixed, bare) AS (
  VALUES
    ('3_cross_state_features', 'cross_state_features'),
    ('3_feature_quality_diagnostics', 'feature_quality_diagnostics'),
    ('3_idiosyncratic_residual_state', 'idiosyncratic_residual_state'),
    ('3_market_breadth_state', 'market_breadth_state'),
    ('3_market_correlation_state', 'market_correlation_state'),
    ('3_market_liquidity_stress_state', 'market_liquidity_stress_state'),
    ('3_market_regime_state', 'market_regime_state'),
    ('3_market_state_features', 'market_state_features'),
    ('3_market_trend_state', 'market_trend_state'),
    ('3_market_volatility_state', 'market_volatility_state'),
    ('3_relative_liquidity_tradability_state', 'relative_liquidity_tradability_state'),
    ('3_sector_breadth_dispersion_state', 'sector_breadth_dispersion_state'),
    ('3_sector_confirmation_state', 'sector_confirmation_state'),
    ('3_sector_confirmed', 'sector_confirmed'),
    ('3_sector_divergent', 'sector_divergent'),
    ('3_flat_or_mixed', 'flat_or_mixed'),
    ('3_sector_liquidity_tradability_state', 'sector_liquidity_tradability_state'),
    ('3_sector_relative_direction_state', 'sector_relative_direction_state'),
    ('3_sector_state_features', 'sector_state_features'),
    ('3_sector_trend_quality_stability_state', 'sector_trend_quality_stability_state'),
    ('3_sector_volatility_state', 'sector_volatility_state'),
    ('3_state_cluster_id', 'state_cluster_id'),
    ('3_state_observation_windows', 'state_observation_windows'),
    ('3_state_quality_diagnostics', 'state_quality_diagnostics'),
    ('3_state_window_sync_policy', 'state_window_sync_policy'),
    ('3_target_data_quality_state', 'target_data_quality_state'),
    ('3_target_direction_return_shape', 'target_direction_return_shape'),
    ('3_target_gap_jump_state', 'target_gap_jump_state'),
    ('3_target_liquidity_tradability_state', 'target_liquidity_tradability_state'),
    ('3_target_market_beta_correlation', 'target_market_beta_correlation'),
    ('3_target_sector_beta_correlation', 'target_sector_beta_correlation'),
    ('3_target_session_position_state', 'target_session_position_state'),
    ('3_completed_1min_bars', 'completed_1min_bars'),
    ('3_target_state_embedding', 'target_state_embedding'),
    ('3_target_state_features', 'target_state_features'),
    ('3_score_payload', 'score_payload'),
    ('3_target_state_vector', 'target_state_vector'),
    ('3_15min', '15min'),
    ('3_390min', '390min'),
    ('3_5min', '5min'),
    ('3_60min', '60min'),
    ('3_target_trend_quality_state', 'target_trend_quality_state'),
    ('3_target_volatility_range_state', 'target_volatility_range_state'),
    ('3_target_volume_activity_state', 'target_volume_activity_state'),
    ('3_target_vs_market_residual_direction', 'target_vs_market_residual_direction'),
    ('3_target_vs_market_volatility', 'target_vs_market_volatility'),
    ('3_target_vs_sector_residual_direction', 'target_vs_sector_residual_direction'),
    ('3_target_vs_sector_volatility', 'target_vs_sector_volatility'),
    ('3_target_vwap_location_state', 'target_vwap_location_state')
)
UPDATE trading_registry r
SET payload = restore_tokens.bare,
    updated_at = CURRENT_TIMESTAMP
FROM restore_tokens
WHERE r.kind = 'state_vector_value'
  AND r.payload = restore_tokens.prefixed;

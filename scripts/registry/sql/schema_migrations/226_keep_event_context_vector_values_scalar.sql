-- Keep Layer 4 state_vector_value rows limited to reviewed core scalar score tokens.
-- Dominant impact scope is a useful horizon-aware audit/debug/routing field, but it is
-- enum-like rather than scalar, so it stays in the model-local contract instead of
-- the state_vector_value registry kind.

UPDATE trading_registry
SET
  payload = '4_event_presence_score_<horizon>;4_event_timing_proximity_score_<horizon>;4_event_intensity_score_<horizon>;4_event_direction_bias_score_<horizon>;4_event_context_alignment_score_<horizon>;4_event_uncertainty_score_<horizon>;4_event_gap_risk_score_<horizon>;4_event_reversal_risk_score_<horizon>;4_event_liquidity_disruption_score_<horizon>;4_event_contagion_risk_score_<horizon>;4_event_context_quality_score_<horizon>;4_event_market_impact_score_<horizon>;4_event_sector_impact_score_<horizon>;4_event_industry_impact_score_<horizon>;4_event_theme_factor_impact_score_<horizon>;4_event_peer_group_impact_score_<horizon>;4_event_symbol_impact_score_<horizon>;4_event_microstructure_impact_score_<horizon>;4_event_scope_confidence_score_<horizon>;4_event_scope_escalation_risk_score_<horizon>;4_event_target_relevance_score_<horizon>',
  note = 'Accepted Layer 4 EventOverlayModel V1 event-context scalar score-family tokens. These families separate event presence, timing, intensity, direction bias, alignment, risks, quality, impact scope, scope confidence, escalation risk, and target relevance; enum-like audit fields remain model-local.',
  updated_at = NOW()
WHERE kind = 'config'
  AND key = 'EVENT_CONTEXT_VECTOR_SCORE_FAMILIES';

DELETE FROM trading_registry
WHERE kind = 'state_vector_value'
  AND key = 'EVENT_DOMINANT_IMPACT_SCOPE_BY_HORIZON';

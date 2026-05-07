-- Align Layer 6 with the accepted PositionProjectionModel boundary.
-- Layer 6 maps final adjusted alpha plus current/pending position, position-level
-- friction, portfolio exposure, and risk-budget context to projected target
-- holding state. It does not emit buy/sell/hold operations or choose expression
-- instruments.

UPDATE trading_registry
SET
  key = 'POSITION_PROJECTION_MODEL',
  payload = 'position_projection_model',
  path = 'trading-model/docs/07_layer_06_position_projection.md',
  applies_to = 'trading-model;alpha_confidence_model;alpha_confidence_vector;model_06_position_projection;position_projection_vector',
  note = 'Accepted canonical Layer 6 model id. PositionProjectionModel maps final adjusted alpha confidence plus current/pending position, position-level friction, portfolio exposure, and risk-budget context to projected target holding state; it is not buy/sell/hold, expression selection, or live execution.',
  updated_at = NOW()
WHERE id = 'trm_TPM001';

UPDATE trading_registry
SET
  key = 'MODEL_06_POSITION_PROJECTION',
  payload = 'model_06_position_projection',
  path = 'trading-model/docs/07_layer_06_position_projection.md',
  applies_to = 'trading-model;position_projection_model;alpha_confidence_model;alpha_confidence_vector;position_projection_vector',
  note = 'Accepted Layer 6 PositionProjectionModel model-output surface name for future promoted position_projection_vector outputs.',
  updated_at = NOW()
WHERE id = 'trm_MTP001';

UPDATE trading_registry
SET
  key = 'POSITION_PROJECTION_VECTOR',
  payload = 'position_projection_vector',
  path = 'trading-model/docs/07_layer_06_position_projection.md',
  applies_to = 'trading-model;position_projection_model;model_06_position_projection;alpha_confidence_vector;option_expression_model;final_action_boundary',
  note = 'Layer 6 PositionProjectionModel output vector for projected target holding state before expression/final-action selection. It carries target exposure, position gap, utility, cost/risk fit, stability, and projection confidence; it is not an order instruction or final action.',
  updated_at = NOW()
WHERE id = 'trm_TSVEC01';

UPDATE trading_registry
SET
  applies_to = REPLACE(REPLACE(REPLACE(applies_to, 'model_06_trading_projection', 'model_06_position_projection'), 'trading_projection_model', 'position_projection_model'), 'trading_signal_vector', 'position_projection_vector'),
  note = REPLACE(REPLACE(REPLACE(note, 'TradingProjectionModel', 'PositionProjectionModel'), 'trading signal', 'position projection'), 'trading projection', 'position projection'),
  updated_at = NOW()
WHERE COALESCE(applies_to, '') LIKE '%trading_projection%'
   OR COALESCE(applies_to, '') LIKE '%trading_signal%'
   OR COALESCE(applies_to, '') LIKE '%model_06_trading%'
   OR COALESCE(note, '') LIKE '%TradingProjectionModel%'
   OR COALESCE(note, '') LIKE '%trading signal%'
   OR COALESCE(note, '') LIKE '%trading projection%';

UPDATE trading_registry
SET
  path = 'trading-model/docs/06_layer_05_alpha_confidence.md',
  applies_to = 'alpha_confidence_model;alpha_confidence_vector;base_alpha_vector;model_06_position_projection;position_projection_vector',
  note = 'Layer 5 output-tier policy: base/unadjusted alpha from Layer 1/2/3 is diagnostic-only, while final adjusted alpha_confidence_vector is the default Layer 6-facing output for PositionProjectionModel.',
  updated_at = NOW()
WHERE key = 'ALPHA_CONFIDENCE_VECTOR_OUTPUT_TIER_POLICY';

UPDATE trading_registry
SET
  applies_to = 'alpha_confidence_vector;model_05_alpha_confidence;alpha_confidence_model;model_06_position_projection;position_projection_model;model_evaluation;promotion_evidence',
  note = 'Layer 5 AlphaConfidence final adjusted alpha-level suitability score for Layer 6 position projection by horizon; this is not target exposure, position gap, an order instruction, or final action.',
  updated_at = NOW()
WHERE key = 'ALPHA_TRADABILITY_SCORE_BY_HORIZON';

UPDATE trading_registry
SET
  applies_to = 'trading-model;source_05_option_expression;model_07_option_expression;position_projection_vector',
  note = 'Accepted Layer 7 expression model id for comparing stock/ETF expression against long call/long put option expression after Layer 6 position_projection_vector and before final action boundaries.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_CPS001', 'term', 'CURRENT_POSITION_STATE', 'text', 'current_position_state', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_model;position_projection_vector;point_in_time_position_context', 'registry_only', 'Layer 6 point-in-time current position state input. It describes current abstract exposure, direction, age, liquidity, and risk/concentration context; it is not an order or execution record.'),
  ('trm_PPS001', 'term', 'PENDING_POSITION_STATE', 'text', 'pending_position_state', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_model;position_projection_vector;point_in_time_position_context', 'registry_only', 'Layer 6 point-in-time pending position state input. Pending exposure is adjusted by fill probability to calculate effective current exposure and avoid repeated projection.'),
  ('trm_ECE001', 'term', 'EFFECTIVE_CURRENT_EXPOSURE', 'text', 'effective_current_exposure', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_model;current_position_state;pending_position_state;position_projection_vector;diagnostics', 'registry_only', 'Layer 6 model-local exposure construct: current_position_exposure plus pending_exposure_size times pending_order_fill_probability_estimate. Used to compute position gap; not an execution instruction.'),
  ('cfg_PPVH001', 'config', 'POSITION_PROJECTION_VECTOR_HORIZONS', 'text', '5min;15min;60min;390min', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;model_06_position_projection', 'registry_only', 'Accepted PositionProjectionModel V1 projection horizons. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.'),
  ('cfg_PPVS001', 'config', 'POSITION_PROJECTION_VECTOR_SCORE_FAMILIES', 'text', '6_target_position_bias_score_<horizon>;6_target_exposure_score_<horizon>;6_current_position_alignment_score_<horizon>;6_position_gap_score_<horizon>;6_position_gap_magnitude_score_<horizon>;6_expected_position_utility_score_<horizon>;6_cost_to_adjust_position_score_<horizon>;6_risk_budget_fit_score_<horizon>;6_position_state_stability_score_<horizon>;6_projection_confidence_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;model_06_position_projection;state_vector_value', 'registry_only', 'Accepted Layer 6 PositionProjectionModel V1 scalar score-family tokens for target holding-state projection. These 10 families separate target bias, target exposure, current-position alignment, position gap, utility, cost pressure, risk fit, stability, and projection confidence.'),
  ('cfg_PPVHS001', 'config', 'POSITION_PROJECTION_HANDOFF_SUMMARY_FIELD_FAMILIES', 'text', '6_dominant_projection_horizon;6_horizon_conflict_state;6_resolved_target_exposure_score;6_resolved_position_gap_score;6_projection_resolution_confidence_score;6_horizon_resolution_reason_codes', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;model_06_position_projection;option_expression_model;final_action_boundary', 'registry_only', 'Reviewed Layer 6 handoff summary field-family tokens for communicating resolved target holding state to Layer 7. These are not buy/sell/hold or order instructions.'),
  ('cfg_PPVD001', 'config', 'POSITION_PROJECTION_DIAGNOSTIC_FIELD_FAMILIES', 'text', '6_raw_target_position_bias_score_<horizon>;6_raw_target_exposure_prior_score_<horizon>;6_alpha_position_conversion_score_<horizon>;6_effective_current_exposure_score;6_pending_adjusted_exposure_score;6_cost_adjustment_reason_codes;6_risk_budget_reason_codes;6_projection_reason_codes', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_model;position_projection_vector;diagnostics;explainability', 'registry_only', 'Reviewed Layer 6 diagnostic field-family tokens for raw alpha-to-position priors, effective exposure calculations, and risk/cost reason-code attribution. Diagnostics are not default Layer 7-facing state_vector_value rows.'),
  ('cfg_PPVBP001', 'config', 'POSITION_PROJECTION_BOUNDARY_POLICY', 'text', 'target_exposure_not_order_quantity;position_gap_not_execution_instruction;no_buy_sell_hold;no_instrument_selection;no_option_chain_features;point_in_time_position_cost_risk_only;final_adjusted_alpha_default', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_model;position_projection_vector;model_06_position_projection;option_expression_model;final_action_boundary', 'registry_only', 'Layer 6 boundary policy: target exposure is abstract risk exposure, position gap is not an execution instruction, and PositionProjectionModel does not emit buy/sell/hold, choose instruments, read option chains, or mutate broker/account state.')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_PPV1001', 'state_vector_value', 'POSITION_TARGET_POSITION_BIAS_SCORE_BY_HORIZON', 'field_name', '6_target_position_bias_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;model_06_position_projection;alpha_confidence_vector;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 signed target holding-direction bias by horizon. Positive is long exposure bias and negative is short exposure bias; this is not buy/sell/hold.'),
  ('fld_PPV1002', 'state_vector_value', 'POSITION_TARGET_EXPOSURE_SCORE_BY_HORIZON', 'field_name', '6_target_exposure_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;model_06_position_projection;risk_budget_context;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 signed normalized abstract target risk exposure by horizon. This is not shares, contracts, position size, order quantity, or final action.'),
  ('fld_PPV1003', 'state_vector_value', 'CURRENT_POSITION_ALIGNMENT_SCORE_BY_HORIZON', 'field_name', '6_current_position_alignment_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;current_position_state;pending_position_state;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 high-is-good score family for how closely current plus pending exposure already matches projected target exposure by horizon.'),
  ('fld_PPV1004', 'state_vector_value', 'POSITION_GAP_SCORE_BY_HORIZON', 'field_name', '6_position_gap_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;effective_current_exposure;current_position_state;pending_position_state;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 signed score family for target exposure minus effective current exposure by horizon. This is a state gap, not an execution instruction.'),
  ('fld_PPV1005', 'state_vector_value', 'POSITION_GAP_MAGNITUDE_SCORE_BY_HORIZON', 'field_name', '6_position_gap_magnitude_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;effective_current_exposure;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 high-is-large score family for absolute normalized distance between target exposure and effective current exposure by horizon.'),
  ('fld_PPV1006', 'state_vector_value', 'EXPECTED_POSITION_UTILITY_SCORE_BY_HORIZON', 'field_name', '6_expected_position_utility_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;position_level_friction_context;risk_budget_context;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 signed score family for expected risk-adjusted net utility of the projected target holding state after position-level friction and risk penalties.'),
  ('fld_PPV1007', 'state_vector_value', 'COST_TO_ADJUST_POSITION_SCORE_BY_HORIZON', 'field_name', '6_cost_to_adjust_position_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;position_level_friction_context;position_gap;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 high-is-bad score family for relative cost pressure required to close the position gap by horizon. It is not a no-trade action.'),
  ('fld_PPV1008', 'state_vector_value', 'RISK_BUDGET_FIT_SCORE_BY_HORIZON', 'field_name', '6_risk_budget_fit_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;risk_budget_context;portfolio_exposure_context;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 high-is-good score family for target exposure compatibility with current risk budget, drawdown, concentration, and portfolio exposure constraints.'),
  ('fld_PPV1009', 'state_vector_value', 'POSITION_STATE_STABILITY_SCORE_BY_HORIZON', 'field_name', '6_position_state_stability_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;alpha_confidence_vector;current_position_state;pending_position_state;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 high-is-good score family for stability of the projected target holding state across alpha, horizon, cost, risk-budget, and pending-order uncertainty.'),
  ('fld_PPV1010', 'state_vector_value', 'POSITION_PROJECTION_CONFIDENCE_SCORE_BY_HORIZON', 'field_name', '6_projection_confidence_score_<horizon>', 'trading-model/docs/07_layer_06_position_projection.md', 'position_projection_vector;position_projection_model;model_06_position_projection;model_evaluation;promotion_evidence', 'registry_only', 'Layer 6 high-is-good score family for confidence in mapping alpha confidence plus position/cost/risk state into target holding-state projection. This is separate from Layer 5 alpha confidence.')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

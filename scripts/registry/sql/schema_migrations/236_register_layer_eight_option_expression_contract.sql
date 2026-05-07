-- Register the accepted Layer 8 OptionExpressionModel boundary.
-- Layer 8 maps the Layer 7 underlying path thesis plus point-in-time option-chain
-- context into an offline option-expression plan. It does not place broker
-- orders, route orders, or mutate accounts.

UPDATE trading_registry
SET
  path = 'trading-model/docs/09_layer_08_option_expression.md',
  applies_to = 'trading-model;source_05_option_expression;model_08_option_expression;underlying_action_plan;underlying_action_vector;option_expression_plan;expression_vector',
  note = 'Accepted Layer 8 option-expression model id. OptionExpressionModel consumes Layer 7 underlying path assumptions plus point-in-time option-chain context and emits offline option_expression_plan / expression_vector rows; it does not place orders, route orders, or mutate broker/account state.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL';

UPDATE trading_registry
SET
  path = 'trading-model/docs/09_layer_08_option_expression.md',
  applies_to = 'trading-model;option_expression_model;source_05_option_expression;underlying_action_plan;underlying_action_vector;option_expression_plan;expression_vector',
  note = 'Accepted Layer 8 OptionExpressionModel model-output surface name for promoted option_expression_plan and expression_vector outputs. This is not live execution.',
  updated_at = NOW()
WHERE key = 'MODEL_08_OPTION_EXPRESSION';

UPDATE trading_registry
SET
  path = 'trading-model/docs/09_layer_08_option_expression.md',
  applies_to = 'option_expression_model;model_08_option_expression;underlying_action_plan;underlying_action_vector;option_expression_plan;expression_vector',
  note = 'Layer policy for OptionExpressionModel: option expression is Layer 8, consumes Layer 7 underlying path assumptions plus option-chain context, and remains offline without broker mutation.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL_LAYER_POLICY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_OEP001', 'term', 'OPTION_EXPRESSION_PLAN', 'text', 'option_expression_plan', 'trading-model/docs/09_layer_08_option_expression.md', 'trading-model;option_expression_model;model_08_option_expression;underlying_action_plan;expression_vector;trading-execution', 'registry_only', 'Layer 8 primary offline option-expression output. It includes selected expression type, selected option right, point-in-time selected contract reference, contract constraints, premium-risk plan, Layer 7 thesis reference, reason codes, and diagnostics; it is not a broker order or account mutation.'),
  ('trm_EXV001', 'term', 'EXPRESSION_VECTOR', 'text', 'expression_vector', 'trading-model/docs/09_layer_08_option_expression.md', 'trading-model;option_expression_model;model_08_option_expression;option_expression_plan;underlying_action_plan;model_evaluation', 'registry_only', 'Layer 8 scalar/vector output for option-expression quality by horizon. It carries eligibility, signed expression direction, contract fit, liquidity fit, IV fit, Greek fit, reward/risk, theta risk, fill quality, and expression confidence; it is not an order instruction.'),
  ('cfg_OEVH001', 'config', 'OPTION_EXPRESSION_VECTOR_HORIZONS', 'text', '5min;15min;60min;390min', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan', 'registry_only', 'Accepted OptionExpressionModel V1 horizons. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.'),
  ('cfg_OEVS001', 'config', 'OPTION_EXPRESSION_VECTOR_SCORE_FAMILIES', 'text', '8_option_expression_eligibility_score_<horizon>;8_option_expression_direction_score_<horizon>;8_option_contract_fit_score_<horizon>;8_option_liquidity_fit_score_<horizon>;8_option_iv_fit_score_<horizon>;8_option_greek_fit_score_<horizon>;8_option_reward_risk_score_<horizon>;8_option_theta_risk_score_<horizon>;8_option_fill_quality_score_<horizon>;8_option_expression_confidence_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;state_vector_value;option_expression_plan', 'registry_only', 'Accepted Layer 8 OptionExpressionModel V1 scalar score-family tokens. These 10 families separate option-expression eligibility, signed expression direction, contract fit, liquidity fit, IV fit, Greek fit, reward/risk, theta risk, fill quality, and expression confidence.'),
  ('cfg_OEPR001', 'config', 'OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES', 'text', '8_resolved_expression_type;8_resolved_option_right;8_resolved_dominant_horizon;8_resolved_contract_ref;8_resolved_expression_confidence_score;8_resolved_reason_codes', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_plan;expression_vector;option_expression_model;model_08_option_expression;underlying_action_plan', 'registry_only', 'Reviewed Layer 8 resolved expression field-family tokens for communicating the chosen option expression and selected point-in-time contract reference. These are not broker order fields.'),
  ('cfg_OEPT001', 'config', 'OPTION_EXPRESSION_TYPES', 'text', 'long_call;long_put;no_option_expression', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_plan;option_expression_model;model_08_option_expression;expression_type_policy', 'registry_only', 'Accepted Layer 8 V1 option-expression type vocabulary. V1 supports single-leg long call, single-leg long put, and no-option-expression outcomes only.'),
  ('cfg_OEPB001', 'config', 'OPTION_EXPRESSION_BOUNDARY_POLICY', 'text', 'option_expression_not_broker_order;contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;expression_confidence_not_final_approval;no_broker_mutation;single_leg_long_options_v1', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;expression_vector;model_08_option_expression;underlying_action_plan;trading-execution', 'registry_only', 'Layer 8 boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, or mutate broker/account state.'),
  ('cfg_OEPD001', 'config', 'OPTION_EXPRESSION_DIAGNOSTIC_FIELD_FAMILIES', 'text', '8_candidate_count;8_eligible_candidate_count;8_contract_dte_fit_score;8_contract_spread_pct;8_contract_iv_rank;8_premium_risk_reason_codes;8_option_expression_reason_codes', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;expression_vector;diagnostics;explainability', 'registry_only', 'Reviewed Layer 8 diagnostic field-family tokens for candidate counts, contract fit attribution, premium-risk attribution, and expression reason codes. Diagnostics are not default scalar score-family rows.')
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
  ('fld_OEV1001', 'state_vector_value', 'OPTION_EXPRESSION_ELIGIBILITY_SCORE_BY_HORIZON', 'field_name', '8_option_expression_eligibility_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for option-expression admissibility after Layer 7 thesis, policy, option-chain, liquidity, IV, and risk constraints by horizon. This is not final approval.'),
  ('fld_OEV1002', 'state_vector_value', 'OPTION_EXPRESSION_DIRECTION_SCORE_BY_HORIZON', 'field_name', '8_option_expression_direction_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 signed score family for option-expression direction by horizon. Positive is call-side/bullish expression, negative is put-side/bearish expression, near zero is no-option expression; this is not order routing.'),
  ('fld_OEV1003', 'state_vector_value', 'OPTION_CONTRACT_FIT_SCORE_BY_HORIZON', 'field_name', '8_option_contract_fit_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for selected contract fit to the Layer 7 path thesis and option-expression constraints by horizon.'),
  ('fld_OEV1004', 'state_vector_value', 'OPTION_LIQUIDITY_FIT_SCORE_BY_HORIZON', 'field_name', '8_option_liquidity_fit_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for option bid/ask, volume, and open-interest fit by horizon.'),
  ('fld_OEV1005', 'state_vector_value', 'OPTION_IV_FIT_SCORE_BY_HORIZON', 'field_name', '8_option_iv_fit_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for implied-volatility and IV-rank fit by horizon.'),
  ('fld_OEV1006', 'state_vector_value', 'OPTION_GREEK_FIT_SCORE_BY_HORIZON', 'field_name', '8_option_greek_fit_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for delta/Greek fit by horizon.'),
  ('fld_OEV1007', 'state_vector_value', 'OPTION_REWARD_RISK_SCORE_BY_HORIZON', 'field_name', '8_option_reward_risk_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for premium-adjusted reward/risk quality by horizon.'),
  ('fld_OEV1008', 'state_vector_value', 'OPTION_THETA_RISK_SCORE_BY_HORIZON', 'field_name', '8_option_theta_risk_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-bad score family for theta-decay pressure by horizon.'),
  ('fld_OEV1009', 'state_vector_value', 'OPTION_FILL_QUALITY_SCORE_BY_HORIZON', 'field_name', '8_option_fill_quality_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for conservative fill-quality estimate by horizon. This is not route or order type.'),
  ('fld_OEV1010', 'state_vector_value', 'OPTION_EXPRESSION_CONFIDENCE_SCORE_BY_HORIZON', 'field_name', '8_option_expression_confidence_score_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'expression_vector;option_expression_model;model_08_option_expression;option_expression_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 8 high-is-good score family for calibrated confidence in the complete offline option-expression plan by horizon. This is not final approval or execution authorization.')
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

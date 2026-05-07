-- Register the accepted Layer 7 UnderlyingActionModel boundary.
-- Layer 7 maps Layer 6 target holding-state projection into an offline
-- direct stock/ETF planned action thesis. It does not place broker orders and
-- does not choose option contracts; option expression is moved to Layer 8.

UPDATE trading_registry
SET
  applies_to = 'trading-model;position_projection_model;model_06_position_projection;alpha_confidence_vector;underlying_action_model;underlying_action_plan;underlying_action_vector',
  note = 'Layer 6 PositionProjectionModel output vector for projected target holding state before Layer 7 direct-underlying action planning. It carries target exposure, position gap, utility, cost/risk fit, stability, and projection confidence; it is not an order instruction, planned action, option expression, or final action.',
  updated_at = NOW()
WHERE key = 'POSITION_PROJECTION_VECTOR';

UPDATE trading_registry
SET
  applies_to = 'position_projection_vector;position_projection_model;model_06_position_projection;underlying_action_model;underlying_action_plan;underlying_action_vector',
  note = 'Reviewed Layer 6 handoff summary field-family tokens for communicating resolved target holding state to Layer 7 UnderlyingActionModel. These are not buy/sell/hold, planned quantities, order instructions, or option-expression fields.',
  updated_at = NOW()
WHERE key = 'POSITION_PROJECTION_HANDOFF_SUMMARY_FIELD_FAMILIES';

UPDATE trading_registry
SET
  applies_to = 'position_projection_model;position_projection_vector;model_06_position_projection;underlying_action_model;underlying_action_plan;option_expression_model;model_08_option_expression',
  note = 'Layer 6 boundary policy: target exposure is abstract risk exposure, position gap is not an execution instruction, and PositionProjectionModel does not emit buy/sell/hold/open/close/reverse, choose instruments, read option chains, or mutate broker/account state. Layer 7 owns planned direct-underlying action; Layer 8 owns option expression.',
  updated_at = NOW()
WHERE key = 'POSITION_PROJECTION_BOUNDARY_POLICY';

UPDATE trading_registry
SET
  path = 'trading-model/docs/08_layer_07_underlying_action.md',
  applies_to = 'alpha_confidence_model;alpha_confidence_vector;model_06_position_projection;position_projection_model;position_projection_vector;model_07_underlying_action;underlying_action_model;underlying_action_plan;underlying_action_vector',
  note = 'Layer 5 AlphaConfidence final adjusted alpha-level suitability score for Layer 6 position projection and Layer 7 underlying-action planning by horizon; this is not target exposure, planned quantity, an order instruction, option expression, or final action.',
  updated_at = NOW()
WHERE key = 'ALPHA_TRADABILITY_SCORE_BY_HORIZON';

UPDATE trading_registry
SET
  path = 'trading-model/docs/08_layer_07_underlying_action.md',
  applies_to = 'trading-model;source_05_option_expression;model_08_option_expression;underlying_action_plan;underlying_action_vector;position_projection_vector',
  note = 'Accepted option-expression model id after Layer 7 UnderlyingActionModel. OptionExpressionModel should compare direct stock/ETF thesis against option expression using Layer 7 underlying-path assumptions plus option-chain context; it remains offline and does not place orders.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL';

UPDATE trading_registry
SET
  key = 'MODEL_08_OPTION_EXPRESSION',
  payload = 'model_08_option_expression',
  path = 'trading-model/docs/90_system_model_architecture_rfc.md',
  applies_to = 'trading-model;option_expression_model;source_05_option_expression;underlying_action_plan;underlying_action_vector',
  note = 'Accepted Layer 8 OptionExpressionModel model-output surface name for future promoted option-expression outputs after Layer 7 underlying_action_plan. This is not live execution.',
  updated_at = NOW()
WHERE key = 'MODEL_07_OPTION_EXPRESSION';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_UAM001', 'term', 'UNDERLYING_ACTION_MODEL', 'text', 'underlying_action_model', 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model;alpha_confidence_model;alpha_confidence_vector;position_projection_model;position_projection_vector;model_07_underlying_action;underlying_action_plan;underlying_action_vector;option_expression_model;model_08_option_expression', 'registry_only', 'Accepted canonical Layer 7 model id. UnderlyingActionModel maps Layer 5/6 state plus point-in-time current/pending underlying exposure, quote/liquidity/borrow state, risk-budget state, and policy gates into an offline direct stock/ETF planned action thesis; it is not option expression or live execution.'),
  ('trm_M7UAM01', 'term', 'MODEL_07_UNDERLYING_ACTION', 'text', 'model_07_underlying_action', 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model;underlying_action_model;underlying_action_plan;underlying_action_vector;position_projection_vector;option_expression_model;model_08_option_expression', 'registry_only', 'Accepted Layer 7 UnderlyingActionModel model-output surface name for future promoted underlying_action_plan and underlying_action_vector outputs.'),
  ('trm_UAP001', 'term', 'UNDERLYING_ACTION_PLAN', 'text', 'underlying_action_plan', 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model;underlying_action_model;model_07_underlying_action;position_projection_vector;option_expression_model;model_08_option_expression;trading-execution', 'registry_only', 'Layer 7 primary offline direct stock/ETF planned action output. It includes planned action type, effective exposure gap, planned incremental exposure, entry/target/stop/time-stop thesis, risk plan, Layer 8 handoff, and reason codes; it is not a broker order, final order quantity, option contract, or execution instruction.'),
  ('trm_UAV001', 'term', 'UNDERLYING_ACTION_VECTOR', 'text', 'underlying_action_vector', 'trading-model/docs/08_layer_07_underlying_action.md', 'trading-model;underlying_action_model;model_07_underlying_action;position_projection_vector;underlying_action_plan;option_expression_model;model_08_option_expression', 'registry_only', 'Layer 7 score/vector output for direct stock/ETF planned action quality by horizon. It carries eligibility, signed action direction, intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence; it is not a broker order or option-expression vector.'),
  ('trm_CUPS01', 'term', 'CURRENT_UNDERLYING_POSITION_STATE', 'text', 'current_underlying_position_state', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_model;underlying_action_plan;underlying_action_vector;point_in_time_underlying_position_context', 'registry_only', 'Layer 7 point-in-time current direct-underlying position state input. It describes current stock/ETF exposure state for action planning; it is not an order or execution record.'),
  ('trm_PUOS01', 'term', 'PENDING_UNDERLYING_ORDER_STATE', 'text', 'pending_underlying_order_state', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_model;underlying_action_plan;underlying_action_vector;point_in_time_underlying_position_context', 'registry_only', 'Layer 7 point-in-time pending direct-underlying order/exposure state input. Pending exposure is adjusted by fill probability to avoid duplicate planned adjustments; it is not a new order instruction.'),
  ('trm_ECUE01', 'term', 'EFFECTIVE_CURRENT_UNDERLYING_EXPOSURE', 'text', 'effective_current_underlying_exposure', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_model;current_underlying_position_state;pending_underlying_order_state;underlying_action_plan;underlying_action_vector;diagnostics', 'registry_only', 'Layer 7 model-local exposure construct: current direct-underlying exposure plus pending underlying exposure times pending fill probability estimate. Used to compute underlying exposure gap and avoid duplicate plans; not an execution instruction.'),
  ('cfg_UAVH001', 'config', 'UNDERLYING_ACTION_VECTOR_HORIZONS', 'text', '5min;15min;60min;390min', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan', 'registry_only', 'Accepted UnderlyingActionModel V1 horizons. 390min means one regular US equity session-equivalent horizon measured in tradable minutes; label builders must document same-session vs next-session-close resolution and use purge/embargo controls.'),
  ('cfg_UAVS001', 'config', 'UNDERLYING_ACTION_VECTOR_SCORE_FAMILIES', 'text', '7_underlying_trade_eligibility_score_<horizon>;7_underlying_action_direction_score_<horizon>;7_underlying_trade_intensity_score_<horizon>;7_underlying_entry_quality_score_<horizon>;7_underlying_expected_return_score_<horizon>;7_underlying_adverse_risk_score_<horizon>;7_underlying_reward_risk_score_<horizon>;7_underlying_liquidity_fit_score_<horizon>;7_underlying_holding_time_fit_score_<horizon>;7_underlying_action_confidence_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;state_vector_value;underlying_action_plan', 'registry_only', 'Accepted Layer 7 UnderlyingActionModel V1 scalar score-family tokens. These 10 families separate trade eligibility, signed action direction, action intensity, entry quality, expected return, adverse risk, reward/risk, liquidity fit, holding-time fit, and action confidence.'),
  ('cfg_UAPR001', 'config', 'UNDERLYING_ACTION_RESOLVED_FIELD_FAMILIES', 'text', '7_resolved_underlying_action_type;7_resolved_action_side;7_resolved_dominant_horizon;7_resolved_trade_eligibility_score;7_resolved_trade_intensity_score;7_resolved_entry_quality_score;7_resolved_action_confidence_score;7_resolved_reason_codes', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_plan;underlying_action_vector;underlying_action_model;model_07_underlying_action;option_expression_model;model_08_option_expression', 'registry_only', 'Reviewed Layer 7 resolved plan/handoff field-family tokens for communicating the chosen direct-underlying action thesis to Layer 8 and execution-side review. These are not broker order fields.'),
  ('cfg_UAPT001', 'config', 'UNDERLYING_ACTION_PLANNED_ACTION_TYPES', 'text', 'open_long;increase_long;reduce_long;close_long;open_short;increase_short;reduce_short;cover_short;maintain;no_trade;bearish_underlying_path_but_no_short_allowed', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_plan;underlying_action_model;model_07_underlying_action;action_type_policy', 'registry_only', 'Accepted Layer 7 V1 planned direct-underlying action type vocabulary. maintain means an existing state remains aligned or not worth adjusting; no_trade means no new direct-underlying operation should be initiated.'),
  ('cfg_UAPB001', 'config', 'UNDERLYING_ACTION_BOUNDARY_POLICY', 'text', 'planned_underlying_action_not_broker_order;planned_quantity_not_final_order_quantity;entry_plan_not_order_type;stop_loss_price_not_broker_stop_order;take_profit_price_not_broker_limit_order;underlying_path_thesis_not_option_contract;no_option_contract_selection;no_broker_mutation', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_model;underlying_action_plan;underlying_action_vector;model_07_underlying_action;option_expression_model;model_08_option_expression;trading-execution', 'registry_only', 'Layer 7 boundary policy: UnderlyingActionModel produces an offline direct stock/ETF action thesis and Layer 8 handoff. It must not place orders, emit broker order fields, choose option contracts, or mutate broker/account state.'),
  ('cfg_UAPD001', 'config', 'UNDERLYING_ACTION_DIAGNOSTIC_FIELD_FAMILIES', 'text', '7_effective_current_underlying_exposure_score;7_pending_adjusted_underlying_exposure_score;7_underlying_exposure_gap_score;7_hard_gate_reason_codes;7_soft_gate_reason_codes;7_risk_plan_reason_codes;7_layer_8_handoff_reason_codes', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_model;underlying_action_plan;underlying_action_vector;diagnostics;explainability', 'registry_only', 'Reviewed Layer 7 diagnostic field-family tokens for effective exposure calculations, gate decisions, risk-plan attribution, and Layer 8 handoff attribution. Diagnostics are not default scalar score-family rows.'),
  ('cfg_OEML001', 'config', 'OPTION_EXPRESSION_MODEL_LAYER_POLICY', 'text', 'layer_08_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context;no_broker_mutation', 'trading-model/docs/08_layer_07_underlying_action.md', 'option_expression_model;model_08_option_expression;underlying_action_plan;underlying_action_vector', 'registry_only', 'Layer policy for OptionExpressionModel after accepting Layer 7 UnderlyingActionModel: option expression is Layer 8, consumes Layer 7 underlying path assumptions plus option-chain context, and remains offline.' )
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
  ('fld_UAV1001', 'state_vector_value', 'UNDERLYING_TRADE_ELIGIBILITY_SCORE_BY_HORIZON', 'field_name', '7_underlying_trade_eligibility_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-good score family for direct-underlying trade eligibility after point-in-time hard/soft gates by horizon. This is not final approval or a broker order.'),
  ('fld_UAV1002', 'state_vector_value', 'UNDERLYING_ACTION_DIRECTION_SCORE_BY_HORIZON', 'field_name', '7_underlying_action_direction_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 signed score family for planned direct-underlying side by horizon. Positive is long-side plan, negative is short-side plan, near zero is maintain/no_trade; this is not buy/sell order routing.'),
  ('fld_UAV1003', 'state_vector_value', 'UNDERLYING_TRADE_INTENSITY_SCORE_BY_HORIZON', 'field_name', '7_underlying_trade_intensity_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-more score family for planned adjustment intensity after confidence, risk, cost, stability, and liquidity compression by horizon. This is not final order quantity.'),
  ('fld_UAV1004', 'state_vector_value', 'UNDERLYING_ENTRY_QUALITY_SCORE_BY_HORIZON', 'field_name', '7_underlying_entry_quality_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-good score family for side-neutral planned entry quality by horizon. Entry plan fields are not broker order types.'),
  ('fld_UAV1005', 'state_vector_value', 'UNDERLYING_EXPECTED_RETURN_SCORE_BY_HORIZON', 'field_name', '7_underlying_expected_return_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 signed score family for expected direct-underlying favorable return quality by horizon after context adjustment.'),
  ('fld_UAV1006', 'state_vector_value', 'UNDERLYING_ADVERSE_RISK_SCORE_BY_HORIZON', 'field_name', '7_underlying_adverse_risk_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-bad score family for expected adverse move / stop-risk pressure in the planned direct-underlying action by horizon.'),
  ('fld_UAV1007', 'state_vector_value', 'UNDERLYING_REWARD_RISK_SCORE_BY_HORIZON', 'field_name', '7_underlying_reward_risk_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-good score family for planned reward/risk quality of the direct-underlying thesis by horizon.'),
  ('fld_UAV1008', 'state_vector_value', 'UNDERLYING_LIQUIDITY_FIT_SCORE_BY_HORIZON', 'field_name', '7_underlying_liquidity_fit_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-good score family for direct-underlying liquidity/spread fit by horizon.'),
  ('fld_UAV1009', 'state_vector_value', 'UNDERLYING_HOLDING_TIME_FIT_SCORE_BY_HORIZON', 'field_name', '7_underlying_holding_time_fit_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-good score family for compatibility between planned holding time and the alpha/projection/path evidence by horizon.'),
  ('fld_UAV1010', 'state_vector_value', 'UNDERLYING_ACTION_CONFIDENCE_SCORE_BY_HORIZON', 'field_name', '7_underlying_action_confidence_score_<horizon>', 'trading-model/docs/08_layer_07_underlying_action.md', 'underlying_action_vector;underlying_action_model;model_07_underlying_action;underlying_action_plan;model_evaluation;promotion_evidence', 'registry_only', 'Layer 7 high-is-good score family for calibrated confidence in the complete offline direct-underlying action plan by horizon.')
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

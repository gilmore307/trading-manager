-- Refine Layer 8 OptionExpressionModel to the accepted detailed outline.
-- Adds snapshot replay, pending option exposure, no-option reason-code, and
-- conservative V1 DTE / single-leg-long-option policies.

UPDATE trading_registry
SET
  payload = '8_resolved_expression_type;8_resolved_option_right;8_resolved_dominant_horizon;8_resolved_selected_contract_ref;8_resolved_contract_fit_score;8_resolved_expression_confidence_score;8_resolved_no_option_reason_codes;8_resolved_reason_codes',
  note = 'Reviewed Layer 8 resolved expression field-family tokens for communicating the chosen option expression, selected point-in-time contract reference, fit/confidence, and no-option reason codes. These are not broker order fields.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_RESOLVED_FIELD_FAMILIES';

UPDATE trading_registry
SET
  payload = 'option_expression_not_broker_order;selected_contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;planned_premium_budget_not_final_order_quantity;expression_confidence_not_final_approval;no_broker_mutation;single_leg_long_options_v1;no_0dte_v1;no_adjusted_contracts_v1;maintain_or_no_trade_means_no_option_expression_v1',
  note = 'Layer 8 boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, mutate broker/account state, create maintain/no-trade overlays in V1, use 0DTE in V1, or use adjusted contracts in V1.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_BOUNDARY_POLICY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('trm_OQSR001', 'term', 'OPTION_CHAIN_SNAPSHOT_REF', 'text', 'option_chain_snapshot_ref', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;model_08_option_expression;option_chain_snapshot;replay_audit', 'registry_only', 'Layer 8 point-in-time option-chain snapshot reference used to replay why a selected contract was chosen. This is not a broker order id.'),
  ('trm_UQSR001', 'term', 'UNDERLYING_QUOTE_SNAPSHOT_REF', 'text', 'underlying_quote_snapshot_ref', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;underlying_action_plan;replay_audit', 'registry_only', 'Layer 8 point-in-time underlying quote snapshot reference paired with the option-chain snapshot for moneyness and path replay.'),
  ('trm_POEC001', 'term', 'PENDING_OPTION_EXPOSURE_CONTEXT', 'text', 'pending_option_exposure_context', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;pending_option_orders;premium_risk_context', 'registry_only', 'Layer 8 point-in-time pending option exposure context used to avoid duplicate option-expression plans. It is not a new order instruction.'),
  ('cfg_OEDTE001', 'config', 'OPTION_EXPRESSION_V1_DTE_POLICY', 'text', '5min_15min:3-7_no_0dte;60min:7-14;390min:7-21;multi_day:21-45', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;contract_constraints;dte_policy', 'registry_only', 'Accepted conservative Layer 8 V1 DTE policy. DTE is a range tied to Layer 7 holding-time assumptions; V1 avoids 0DTE and extreme short-DTE lottery contracts.'),
  ('cfg_OEDLT001', 'config', 'OPTION_EXPRESSION_V1_DELTA_POLICY', 'text', 'preferred_abs_delta_range=0.35-0.65;avoid_deep_otm_lottery_contracts', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;contract_constraints;delta_policy', 'registry_only', 'Accepted conservative Layer 8 V1 delta policy for single-leg long call/put expression. Future learned fit models may adjust by path quality, expected move, IV, liquidity, and theta pressure.'),
  ('cfg_OERB001', 'config', 'OPTION_EXPRESSION_BASELINE_LADDER', 'text', 'no_option_expression;underlying_only_expression;naive_atm_nearest_expiration_call_put;fixed_delta_fixed_dte_option;layer_8_full_contract_fit_model', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;model_evaluation;promotion_evidence;baseline_ladder', 'registry_only', 'Accepted Layer 8 evaluation baseline ladder. Layer 8 must prove value versus no option, underlying-only Layer 7 expression, naive ATM option, fixed delta/DTE option, and full contract-fit model.'),
  ('cfg_OELBL001', 'config', 'OPTION_EXPRESSION_EVALUATION_LABEL_FAMILIES', 'text', 'realized_option_return_<horizon>;realized_option_mid_return_<horizon>;realized_option_bid_exit_return_<horizon>;realized_option_spread_cost_<horizon>;realized_iv_change_<horizon>;realized_theta_decay_<horizon>;realized_delta_path_exposure_<horizon>;underlying_target_hit_but_option_lost_label_<horizon>;option_no_expression_opportunity_cost_<horizon>;option_expression_avoided_loss_value_<horizon>;candidate_contract_utility_curve_<horizon>', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;model_evaluation;labels;leakage_controls', 'registry_only', 'Reviewed Layer 8 offline evaluation label-family tokens. These labels must not be joined into inference rows.')
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

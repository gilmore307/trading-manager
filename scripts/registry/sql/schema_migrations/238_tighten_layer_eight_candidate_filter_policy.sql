-- Tighten accepted Layer 8 OptionExpressionModel V1 candidate filter policy.
-- Adds explicit hard-filter diagnostics and target-range moneyness guardrails.

UPDATE trading_registry
SET
  payload = 'option_expression_not_broker_order;selected_contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;planned_premium_budget_not_final_order_quantity;expression_confidence_not_final_approval;no_broker_mutation;single_leg_long_options_v1;no_0dte_v1;no_adjusted_contracts_v1;maintain_or_no_trade_means_no_option_expression_v1;preferred_delta_range_hard_filter_v1;target_range_moneyness_guardrail_v1',
  note = 'Layer 8 boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, mutate broker/account state, create maintain/no-trade overlays in V1, use 0DTE in V1, use adjusted contracts in V1, select contracts outside the preferred delta policy, or select strikes outside coherent Layer 7 target-range guardrails.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_BOUNDARY_POLICY';

UPDATE trading_registry
SET
  payload = '8_candidate_count;8_eligible_candidate_count;8_candidate_hard_filter_fail_reason_codes;8_contract_dte_fit_score;8_contract_spread_pct;8_contract_iv_rank;8_premium_risk_reason_codes;8_option_expression_reason_codes',
  note = 'Reviewed Layer 8 diagnostic field-family tokens for candidate counts, per-candidate hard-filter reason codes, contract fit attribution, premium-risk attribution, and expression reason codes. Diagnostics are not default scalar score-family rows.',
  updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_DIAGNOSTIC_FIELD_FAMILIES';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_OEMG001', 'config', 'OPTION_EXPRESSION_V1_MONEYNESS_GUARDRAIL', 'text', 'bullish_call_strike_not_above_target_price_high;bearish_put_strike_not_below_target_price_low;apply_only_when_layer_7_target_range_is_directionally_coherent', 'trading-model/docs/09_layer_08_option_expression.md', 'option_expression_model;option_expression_plan;contract_constraints;moneyness_policy;underlying_action_plan', 'registry_only', 'Accepted Layer 8 V1 moneyness guardrail. Layer 8 uses Layer 7 target range to prevent lottery-like call strikes above coherent bullish target highs and put strikes below coherent bearish target lows. This is still offline contract selection, not execution.')
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

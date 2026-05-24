-- Register Layer 9 option-surface status and non-optionable bypass semantics.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_OESS001',
  'config',
  'OPTION_EXPRESSION_OPTION_SURFACE_STATUS',
  'text',
  'optionable_chain_available;optionable_chain_missing;non_optionable_underlying',
  'trading-model/docs/18_layer_09_trading_guidance.md',
  'option_expression_model;option_expression_plan;expression_vector;model_09_option_expression;underlying_action_plan;crypto_spot;direct_underlying_route',
  'registry_only',
  'Accepted Layer 9 option-surface status vocabulary. non_optionable_underlying applies to direct-underlying or spot routes such as BTC where option-expression scoring is bypassed but a minute-level Layer 9 status row may still be retained for training, audit, and downstream handoff.'
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
SET payload = '9_resolved_expression_type;9_resolved_option_right;9_resolved_option_surface_status;9_resolved_dominant_horizon;9_resolved_selected_contract_ref;9_resolved_contract_fit_score;9_resolved_expression_confidence_score;9_resolved_no_option_reason_codes;9_resolved_reason_codes',
    note = 'Reviewed current 9_* resolved expression field-family tokens for Layer 9 option-expression. They communicate chosen option expression, option-surface status, selected point-in-time contract reference, fit/confidence, and no-option reason codes; they are not broker order fields.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_OEPR001';

UPDATE trading_registry
SET payload = 'option_expression_not_broker_order;selected_contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;planned_premium_budget_not_final_order_quantity;expression_confidence_not_final_approval;underlying_only_expression_not_broker_order;underlying_only_expression_allowed_when_options_unsuitable;non_optionable_underlying_bypasses_option_scoring;no_broker_mutation;single_leg_long_options;no_0dte;no_adjusted_contracts;maintain_or_no_trade_means_no_option_expression;preferred_delta_range_hard_filter;target_range_moneyness_guardrail',
    note = 'Layer 9 option-expression boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. Current physical model_09/9_* names are active. It may resolve to underlying-only expression when the Layer 8 thesis remains usable without an option contract, including non-optionable direct-underlying routes. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, or mutate broker/account state.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_OEPB001';

UPDATE trading_registry
SET payload = 'layer_09_after_underlying_action;uses_underlying_action_plan;uses_option_chain_context_when_available;non_optionable_underlying_bypass_status;no_broker_mutation;model_09_physical_surface',
    note = 'Layer policy for OptionExpressionModel: option expression is Layer 9 optional expression context, consumes Layer 8 underlying path assumptions plus option-chain context when available, keeps explicit status rows for missing/non-optionable option surfaces, and remains offline without broker mutation. Current physical names use model_09/9_*.',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 'cfg_OEML001';

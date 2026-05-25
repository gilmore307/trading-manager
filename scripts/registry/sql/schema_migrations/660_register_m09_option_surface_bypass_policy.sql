-- Clarify that live C04 invokes M09 only when a usable option chain exists.

UPDATE trading_registry
SET payload = 'translate_underlying_thesis_to_expression;consume_c02_c03_underlying_intent;call_model_09_only_when_optionable_chain_available;bypass_model_09_when_chain_missing_or_non_optionable;single_leg_long_call_put_v1;underlying_only_fallback;no_valid_expression_status;no_position_sizing;no_broker_order;roll_only_when_materially_better',
    note = 'C04 Option Review translates an accepted C02 entry thesis or C03 lifecycle intent into the best expression: long call, long put, underlying-only expression, or no valid option expression. C04 calls Model 09 only when the target is optionable and a usable current option chain exists. If this minute has no usable option chain, or the underlying is non-optionable such as BTC, C04 bypasses M09 and carries an underlying-only/no-option expression decision without asking M09 to score missing contracts. C04 does not decide whether the underlying thesis is valid, does not size positions, does not build broker orders, and does not mutate accounts. For held options, roll/re-expression requires the replacement contract to be materially better after liquidity, Greek, DTE, IV, and risk checks.',
    updated_at = NOW()
WHERE key = 'C04_OPTION_EXPRESSION_REVIEW_POLICY';

UPDATE trading_registry
SET payload = 'option_expression_not_broker_order;selected_contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;planned_premium_budget_not_final_order_quantity;expression_confidence_not_final_approval;underlying_only_expression_not_broker_order;underlying_only_expression_allowed_when_options_unsuitable;live_m09_invocation_requires_optionable_chain_available;missing_chain_or_non_optionable_bypasses_m09;no_broker_mutation;single_leg_long_options;no_0dte;no_adjusted_contracts;maintain_or_no_trade_means_no_option_expression;preferred_delta_range_hard_filter;target_range_moneyness_guardrail',
    note = 'Layer 9 option-expression boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector only when optionable-chain evidence exists. Runtime C04 invokes M09 only for optionable targets with usable point-in-time option-chain candidates. Missing-chain and non-optionable routes bypass M09 in live operation and may retain only status/audit evidence. M09 must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, or mutate broker/account state.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_BOUNDARY_POLICY';

UPDATE trading_registry
SET payload = 'layer_09_after_underlying_action;uses_underlying_action_plan;live_invocation_requires_optionable_chain_available;uses_option_chain_context_when_available;missing_chain_or_non_optionable_bypasses_model_09;non_optionable_underlying_bypass_status;no_broker_mutation;model_09_physical_surface',
    note = 'Layer policy for OptionExpressionModel: option expression is Layer 9 optional expression context. It consumes Layer 8 underlying path assumptions plus option-chain context only when a usable option chain is available. Missing-chain and non-optionable statuses are offline dataset/audit coverage and live C04 bypass markers, not M09 contract-scoring invocations. The layer remains offline without broker mutation. Current physical names use model_09/9_*.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_MODEL_LAYER_POLICY';

UPDATE trading_registry
SET note = 'Accepted Layer 9 option-surface status vocabulary. optionable_chain_available is the only status that permits live C04 to call M09 and create per-contract candidate scoring. optionable_chain_missing and non_optionable_underlying bypass M09 in live operation; they may still be retained as underlying-minute status rows for training coverage, audit, and downstream handoff. non_optionable_underlying applies to direct-underlying or spot routes such as BTC.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_OPTION_SURFACE_STATUS';

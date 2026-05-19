-- Register stock-first benchmark composition and Layer 8 underlying-only expression fallback.

UPDATE trading_registry
SET payload = 'one_frozen_benchmark_episode_panel;fixed_component_weights;asset_class_and_theme_bucket_required;component_role_required;single_name_optionable_majority_required;etf_backbone_minor_context_only;large_same_background_overlap_restrained;hot_thematic_single_name_coverage_required;crypto_minority_sleeve_required;controlled_data_stress_sleeve_allowed;critical_data_stress_tags_require_stress_role;missing_crypto_quote_order_book_context_allowed;missing_layer2_stress_component_allowed;stress_exception_ref_required;stress_sleeve_weight_cap_15_percent;non_etf_targets_require_target_context_review;formal_run_once_after_training;benchmark_data_evaluation_only;target_window_training_exclusion_required;same_target_overlapping_folds_blocked;fixed_data_snapshot;fixed_cost_model;fixed_baselines;guardrails_do_not_replace_primary;new_benchmark_requires_new_contract',
    note = 'Primary evaluation benchmark policy. Fold-to-fold comparison uses one frozen episode panel with fixed target/window components, asset-class and theme-bucket metadata, component roles, a stock-first optionable single-name majority, restrained same-background event overlap, controlled hot thematic single-name coverage, a minor ETF background sleeve, a small crypto sleeve, and fixed weights. A capped stress sleeve may model critical data-edge cases such as crypto missing quote/order-book context or missing Layer 2 context only with explicit stress role, data-availability tags, and stress-exception refs. OKX crypto trades are transient inputs for trade-derived liquidity bars, not default standalone final saved outputs. Non-ETF targets require reviewed target-context/proxy refs unless an accepted stress exception applies. Benchmark data is evaluation-only and any same-target training fold that overlaps a benchmark component window is blocked.',
    updated_at = NOW()
WHERE key = 'EVALUATION_PRIMARY_BENCHMARK_POLICY';

UPDATE trading_registry
SET payload = 'long_call;long_put;underlying_only_expression;no_option_expression',
    note = 'Accepted Layer 8 V1 option-expression type vocabulary. Current physical model_08/8_* names are active. V1 supports single-leg long call, single-leg long put, underlying-only expression fallback, and no-option-expression outcomes.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_TYPES';

UPDATE trading_registry
SET payload = 'option_expression_not_broker_order;selected_contract_ref_not_broker_order_id;selected_contract_not_send_order;contract_constraints_not_route_or_time_in_force;premium_risk_plan_not_account_mutation;planned_premium_budget_not_final_order_quantity;expression_confidence_not_final_approval;underlying_only_expression_not_broker_order;underlying_only_expression_allowed_when_options_unsuitable;no_broker_mutation;single_leg_long_options;no_0dte;no_adjusted_contracts;maintain_or_no_trade_means_no_option_expression;preferred_delta_range_hard_filter;target_range_moneyness_guardrail',
    note = 'Layer 8 option-expression boundary policy: OptionExpressionModel produces an offline option-expression plan and expression vector. Current physical model_08/8_* names are active. It may resolve to underlying-only expression when the Layer 7 thesis remains usable but option contracts are unsuitable because of policy, liquidity, IV, Greek, DTE, quote freshness, or missing-contract evidence. It must not place orders, emit broker order fields, choose route/time-in-force, emit final order quantity, mutate broker/account state, create maintain/no-trade overlays in V1, use 0DTE in V1, use adjusted contracts in V1, select contracts outside the preferred delta policy, or select strikes outside coherent underlying-action target-range guardrails.',
    updated_at = NOW()
WHERE key = 'OPTION_EXPRESSION_BOUNDARY_POLICY';

UPDATE trading_registry
SET payload = 'single_leg_only;long_call;long_put;underlying_only_expression_non_option_fallback;no_option_expression;multi_leg_spreads_deferred',
    note = 'Layer 8 option-expression V1 coverage is single-leg option expression only for option contracts: long call or long put. Underlying-only expression and no-option expression are non-option fallbacks. Multi-leg spreads are deferred beyond V1.',
    updated_at = NOW()
WHERE key = 'LAYER_08_OPTION_EXPRESSION_SINGLE_LEG_POLICY';

-- Register accepted promotion/storage lifecycle boundary and Layer 8 option bucket defaults.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_PLB001',
    'config',
    'PROMOTION_STORAGE_LIFECYCLE_BOUNDARY_POLICY',
    'text',
    'promotion_classifies_artifacts;manager_schedules_lifecycle;storage_executes_lifecycle;promotion_must_not_call_cleanup_compression_archive_delete_executors_directly',
    'trading-manager/docs/96_model_promotion.md',
    'model_promotion_review_v1;review_decision_v1;activation_record_v1;storage_lifecycle_request_v1;trading-manager;trading-model;trading-storage',
    'sync_artifact',
    'Promotion may classify retention intent and mark promoted model bodies/lineage keep-forever. Manager schedules lifecycle through storage_lifecycle_request_v1; trading-storage executes protected-set checked physical lifecycle actions.'
  ),
  (
    'cfg_L8OPT001',
    'config',
    'LAYER_08_OPTION_BUCKET_EXPIRATION_POLICY',
    'text',
    'near_to_far_listed_expirations;current_week;next_week;following_week;continue_outward_only_when_coverage_policy_requires',
    'trading-model/docs/09_layer_08_option_expression.md',
    'layer_08_option_expression;OptionExpressionModel;option_contract_bucket;manager_model_training_workflow_plan_v1',
    'sync_artifact',
    'Layer 8 option-expression contract bucket expansion scans listed expirations from near to far: current week, next week, following week, then farther only by reviewed coverage policy.'
  ),
  (
    'cfg_L8OPT002',
    'config',
    'LAYER_08_OPTION_BUCKET_STRIKE_POLICY',
    'text',
    'current_to_target_listed_strike_corridor;three_listed_strike_levels_below;three_listed_strike_levels_above;use_actual_listed_strikes_not_fixed_dollars;example_95_to_100_one_dollar_strikes_92_to_103',
    'trading-model/docs/09_layer_08_option_expression.md',
    'layer_08_option_expression;OptionExpressionModel;option_contract_bucket;strike_selection;manager_model_training_workflow_plan_v1',
    'sync_artifact',
    'Layer 8 option bucket strikes cover the current-price to target-price listed-strike corridor plus three actual listed strike levels on each side.'
  ),
  (
    'cfg_L8OPT003',
    'config',
    'LAYER_08_OPTION_BUCKET_PREFILTER_POLICY',
    'text',
    'no_acquisition_time_prefilter_for_model_construction;retain_illiquid_wide_spread_low_oi_high_iv_deep_itm_otm_stale_and_extreme_contracts_as_features_labels_reason_codes',
    'trading-model/docs/09_layer_08_option_expression.md',
    'layer_08_option_expression;OptionExpressionModel;option_contract_bucket;historical_model_construction;robustness_coverage',
    'sync_artifact',
    'Historical Layer 8 model-construction buckets intentionally retain extreme/illiquid contracts for robustness instead of filtering them out at acquisition time.'
  ),
  (
    'cfg_L8OPT004',
    'config',
    'LAYER_08_OPTION_EXPRESSION_V1_SINGLE_LEG_POLICY',
    'text',
    'single_leg_only;long_call;long_put;no_option_expression;multi_leg_spreads_deferred',
    'trading-model/docs/09_layer_08_option_expression.md',
    'layer_08_option_expression;OptionExpressionModel;option_expression_plan;expression_vector',
    'sync_artifact',
    'Layer 8 V1 option-expression coverage is single-leg only: long call, long put, or no-option expression. Multi-leg spreads are deferred beyond V1.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

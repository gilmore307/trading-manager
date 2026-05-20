-- Refresh layer-scope registry notes after DynamicRiskPolicyModel insertion.

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layers_1_9', 'layers_1_10'),
    note = replace(note, 'accepted nine-layer conceptual map', 'accepted ten-layer conceptual map'),
    updated_at = NOW()
WHERE key = 'MODEL_LAYER_READINESS_SUMMARY';

UPDATE trading_registry
SET payload = 'layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;layer_05_alpha_confidence;layer_06_dynamic_risk_policy;layer_07_position_projection;layer_08_underlying_action;layer_09_trading_guidance;layer_10_event_risk_governor',
    applies_to = 'trading-model;trading-data;trading-manager;model_training_workflow;dynamic_risk_policy_model;event_failure_risk_model;event_risk_governor;trading_guidance;current_physical_names',
    note = 'Active layer order after the accepted route update: Layer 6 is DynamicRiskPolicyModel; Layer 9 is TradingGuidance / OptionExpression optional expression context; Layer 10 is EventRiskGovernor / EventIntelligenceOverlay for event-risk governance of the Layer 8 direct-underlying thesis. Downstream physical script/package/table names may retain older Layer 6-9 numbering until dedicated renumbering; historical/applied migration records may retain prior names.',
    updated_at = NOW()
WHERE key = 'MODEL_LAYER_CONCEPTUAL_REORDER_POLICY';

UPDATE trading_registry
SET payload = 'layer_1_failed_baseline_leakage_alignment_model_row_count_stability;layer_2_failed_baseline_improvement_split_stability;layer_3_real_eval_deferred_upstream_layer_1_2_not_active_and_calibration_missing;layers_4_10_missing_production_eval_run_labels_metrics;layer_6_dynamic_risk_policy_physical_implementation_pending',
    applies_to = 'model_governance;model_promotion;promotion_blockers;layers_1_10',
    note = 'Current blocker summary from the production-promotion acceptance pass after DynamicRiskPolicyModel insertion. Layer 3 has real production-evaluation substrate but is still deferred; Layers 4-10 require production evaluation substrate, and Layer 6 DynamicRiskPolicyModel additionally needs a dedicated physical implementation slice before promotion eligibility.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_ACCEPTANCE_BLOCKERS';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layers_1_9', 'layers_1_10'),
    note = 'Accepted production-promotion readiness checklist for Layers 1-10. Missing evidence or failed gates require a deferred promotion decision; this row does not approve any production promotion.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_READINESS_CHECKLIST';

UPDATE trading_registry
SET payload = 'layer_1_deferred_after_real_evaluation;layer_2_deferred_after_real_evaluation;layer_3_real_production_eval_substrate_deferred_upstream_dependencies_and_calibration;layer_4_agent_reviewed_deferred_no_production_eval_substrate;layer_5_agent_reviewed_deferred_no_production_eval_substrate;layer_6_dynamic_risk_policy_pending_physical_implementation_and_eval_substrate;layer_7_agent_reviewed_deferred_no_production_eval_substrate;layer_8_agent_reviewed_deferred_no_production_eval_substrate;layer_9_agent_reviewed_deferred_no_production_eval_substrate;layer_10_agent_reviewed_deferred_no_production_eval_substrate',
    applies_to = 'model_governance;model_promotion;production_hardening;layers_1_10',
    note = 'Current production-promotion acceptance status for the Layer 1-10 stack. Layers 1-2 deferred after real database evaluation; Layer 3 deferred after real production-evaluation substrate because upstream dependencies and calibration are missing; Layer 6 DynamicRiskPolicyModel is pending physical implementation and evaluation substrate; the remaining downstream layers remain deferred until production evaluation substrate exists. No production activation is approved.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_READINESS_STATUS_MATRIX';

UPDATE trading_registry
SET applies_to = replace(applies_to, 'layers_1_9', 'layers_1_10'),
    updated_at = NOW()
WHERE key IN (
  'MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS',
  'MODEL_PROMOTION_UNIFIED_TARGETS',
  'MANAGER_MODEL_PROMOTION_REVIEW_PLAN',
  'EXECUTION_MODEL_DECISION_INPUT_SNAPSHOT',
  'EXECUTION_MODEL_DECISION_INPUT_VALIDATION',
  'MODEL_REALTIME_DECISION_INPUT_VALIDATION',
  'MODEL_REALTIME_DECISION_ROUTE_PLAN',
  'MODEL_REALTIME_DECISION_ROUTE_PLAN_VALIDATION',
  'REALTIME_FEATURE_SNAPSHOT',
  'REALTIME_FEATURE_SNAPSHOT_VALIDATION'
);

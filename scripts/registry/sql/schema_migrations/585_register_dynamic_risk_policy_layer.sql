-- Insert DynamicRiskPolicyModel as Layer 6 and shift downstream promotion bundle to Layer 1-10.

UPDATE trading_registry
SET payload = 'candidate_ref_required;evaluation_run_refs_optional;evidence_refs_optional;fold_layers_01_10_model_evaluation_complete_required;pinned_layer_01_10_bundle_required;bundle_acceptance_all_or_nothing;manager_schedules_only;evaluation_owns_benchmark_settlement_eligibility_readiness;execution_owns_shadow_cycle_activation',
    note = 'Manager prepares and schedules model promotion/evaluation/execution-review requests. Promotion review is fold-stack scoped and evaluates one pinned Layer 1-10 version bundle. Acceptance is all-or-nothing for that bundle: layer-local fold evaluation is diagnostic and supports failure attribution, but no single layer or partial substack can be promoted independently. Benchmark judgment and promotion readiness belong to trading-evaluation; live/shadow runtime active selection belongs to trading-execution.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_REVIEW_POLICY';

UPDATE trading_registry
SET payload = 'pinned_layer_01_10_bundle_all_or_nothing_after_fold_evaluation_complete',
    applies_to = 'historical_scheduler;model_training_workflow;fold_settlement;promotion_review;layers_1_10',
    note = 'Promotion review is not triggered by one model completing one fold. It opens only after Layer 1 through Layer 10 model_evaluation stages have completed for the same fold, then evaluates one pinned Layer 1-10 version bundle. Acceptance is all-or-nothing: the bundle is accepted or rejected as a whole; layer-local results remain diagnostic and cannot promote a single layer or partial substack independently.',
    updated_at = NOW()
WHERE key = 'FOLD_STACK_PROMOTION_GATE_POLICY';

UPDATE trading_registry
SET payload = 'data_acquisition_and_feature_generation_are_month_scoped;model_generation_and_model_evaluation_are_fold_scoped;promotion_review_waits_for_fold_layers_01_10_model_evaluation_complete',
    note = 'Month Ingest Workers own single-month substrate stages: data_acquisition and feature_generation/input preparation. Model Worker 1 owns fold-scoped model_generation and model_evaluation. Promotion review is blocked until the same fold has completed Layer 1 through Layer 10 model_evaluation; single-layer fold results are diagnostic until the full stack closes.',
    updated_at = NOW()
WHERE key = 'MONTHLY_SUBSTRATE_FOLD_MODEL_STAGE_BOUNDARY';

UPDATE trading_registry
SET payload = 'market_regime_model;sector_context_model;target_state_vector_model;event_failure_risk_model;alpha_confidence_model;dynamic_risk_policy_model;position_projection_model;underlying_action_model;option_expression_model;event_risk_governor',
    note = 'Canonical stable model ids for the current Layer 1-10 promotion bundle. DynamicRiskPolicyModel is Layer 6; downstream implementation packages may retain older physical numbering until dedicated renumbering.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_UNIFIED_TARGETS';

UPDATE trading_registry
SET payload = 'layer_1:market_regime_model:no_persisted_decision_receipt;layer_2:sector_context_model:no_persisted_decision_receipt;layer_3:target_state_vector_model:no_persisted_decision_receipt;layer_4:event_failure_risk_model:no_persisted_decision_receipt;layer_5:alpha_confidence_model:no_persisted_decision_receipt;layer_6:dynamic_risk_policy_model:no_persisted_decision_receipt;layer_7:position_projection_model:no_persisted_decision_receipt;layer_8:underlying_action_model:no_persisted_decision_receipt;layer_9:option_expression_model:no_persisted_decision_receipt;layer_10:event_risk_governor:no_persisted_decision_receipt',
    note = 'Current Layer 1-10 promotion acceptance receipt coverage by stable model id; missing persisted decision receipts are explicit blockers, not implicit acceptance.',
    updated_at = NOW()
WHERE key = 'MODEL_PROMOTION_ACCEPTANCE_DECISION_RECEIPTS';

UPDATE trading_registry
SET payload = 'layers_01_02_six_month_panel;layers_03_10_target_symbol_six_month;layer_10_event_risk_governor_uses_physical_layer_09_event_source_overlay_until_renumbering',
    note = 'Accepted dataset-unit policy inside the resident Layer 1-10 historical-modeling system service: Layers 1-2 use one six-month panel; Layers 3-10 use one selected target symbol over one six-month window. DynamicRiskPolicyModel is Layer 6; EventRiskGovernor is conceptual Layer 10 while current source_09/model_09 physical surfaces remain until implementation renumbering.',
    updated_at = NOW()
WHERE key = 'HISTORICAL_DATASET_UNIT_POLICY';

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_05_alpha_confidence;layer_06_dynamic_risk_policy;model_06_position_projection;model_07_underlying_action;model_08_option_expression;model_09_event_risk_governor;current_physical_names;layer_01_02_foundation_catch_up;post_model_artifact_rebuild_boundary;rolling_fold_promotion;four_one_one_split',
    note = 'Manager-owned base Layer 1-10 workflow plan within the resident historical-modeling system service. DynamicRiskPolicyModel is conceptual Layer 6. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-2 before target-specific work; base model generation/evaluation/promotion review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist. Current source_09_event_risk_governor / physical model_09 EventRiskGovernor remains the conceptual Layer 10 implementation surface until dedicated renumbering.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';

UPDATE trading_registry
SET note = 'Manager-owned durable base Layer 1-10 workflow state within the resident historical-modeling system service. Month-scoped checkpoints count foundation catch-up progress from reusable Layer 1/2 data acquisition and feature generation substrate, allowing chronological advancement before target-specific Layers 3-10 scheduling. EventRiskGovernor is conceptual Layer 10 while current physical Layer 9 source/model surfaces remain until dedicated renumbering.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_STATE';

UPDATE trading_registry
SET note = 'Historical data/modeling workflow is owned by a resident system service covering the full Layer 1-10 stack. DynamicRiskPolicyModel is Layer 6. EventRiskGovernor is conceptual Layer 10 and remains the service-owned residual/risk overlay lane; chat/manual CLI runs are fallback inspection, repair, smoke-test, or emergency-intervention tools, not the normal operating path.',
    updated_at = NOW()
WHERE key = 'HISTORICAL_MODELING_SYSTEM_SERVICE_RUNTIME';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DYNRISK001',
    'config',
    'DYNAMIC_RISK_POLICY_MODEL_LAYER',
    'text',
    'layer_06_dynamic_risk_policy_model_global_market_driven_premium_risk_budget_state',
    'trading-model/docs/02_architecture.md;trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    'layer_06_dynamic_risk_policy;position_projection;option_expression;event_risk_governor;portfolio_context_state',
    'sync_artifact',
    'DynamicRiskPolicyModel is inserted as conceptual Layer 6. It learns dynamic premium/risk-budget policy mainly from Layer 1 global market regime plus systemic/broad event risk and portfolio context. Target-specific evidence can cap the current target but must not distort global risk budget. Execution hard order gates remain outside the model stack.'
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

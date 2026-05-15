-- Align manager runtime workflow registry rows with the accepted base Layer 1-7 stack.
-- Event intelligence remains the conceptual Layer 8 risk-governor overlay and is no
-- longer a hard dependency for base workflow progression. Legacy physical model and
-- feature script names remain referenced where they still own implementation.

UPDATE trading_registry
SET applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_alpha_confidence;layer_05_position_projection;layer_06_underlying_action;layer_07_trading_guidance;layer_01_02_03_foundation_catch_up;post_model_artifact_rebuild_boundary;rolling_fold_promotion;four_one_one_split;legacy_physical_model_layer_name_policy',
    note = 'Manager-owned base Layer 1-7 workflow plan. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-3; base model generation/evaluation/Promotion Review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist. Event intelligence / legacy source_04_event_overlay is excluded from this base graph and belongs to the separate conceptual Layer 8 risk-governor overlay.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT';

UPDATE trading_registry
SET note = 'Manager-owned durable base Layer 1-7 workflow state. Month-scoped checkpoints count a foundation catch-up month complete once reusable substrate Layers 1-3 data acquisition and feature generation are succeeded/not_applicable, allowing chronological advancement before target-specific base Layer 4-7 scheduling. Event-risk-governor state is separate.',
    applies_to = 'trading-manager;scheduler;historical_training;manager_model_training_workflow_plan;component_completion_receipt;layer_01_02_03_foundation_catch_up;historical_substrate_reuse;event_risk_governor_separate',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_STATE';

UPDATE trading_registry
SET note = 'Refreshes the durable base Layer 1-7 workflow checkpoint, ingests component receipts, records review refs, and selects the next safe or guarded stage without provider calls, model activation, broker execution, or event-overlay gating.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_ADVANCE';

UPDATE trading_registry
SET note = 'Prints the current base Layer 1-7 manager historical-training workflow graph and next gated stage without provider calls, model activation, broker execution, or event-overlay gating.',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN';

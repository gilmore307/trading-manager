-- Clarify that Layer 9 is part of the resident historical-modeling system service.
-- Layer 9 remains a residual/risk overlay lane rather than a hard prerequisite for
-- base Layers 1-8 progression, but it is not an external/manual side project.

UPDATE trading_registry
SET note = 'Manager-owned base Layer 1-8 workflow plan within the resident Layer 1-9 historical-modeling system service. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-2 before target-specific work; base model generation/evaluation/Promotion Review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist. Current source_09_event_risk_governor / Layer 9 EventRiskGovernor remains a service-owned residual/risk overlay lane rather than a hard prerequisite in this base graph.',
    updated_at = NOW()
WHERE id = 'art_MMTW001';

UPDATE trading_registry
SET note = 'Manager-owned durable base Layer 1-8 workflow state within the resident Layer 1-9 historical-modeling system service. Month-scoped checkpoints count foundation catch-up progress from reusable Layer 1/2 data acquisition and feature generation substrate, allowing chronological advancement before target-specific Layers 3-8 scheduling. Event-risk-governor state is a service-owned Layer 9 overlay state, not an external/manual side project.',
    updated_at = NOW()
WHERE id = 'art_MMTW002';

UPDATE trading_registry
SET note = 'Formal workflow progression is segmented by dataset unit inside the same historical-modeling system service: Layers 1-2 use one six-month panel; Layers 3-8 run one selected target symbol over one six-month unit; Layer 9 EventRiskGovernor runs as the service-owned event-risk overlay lane. Current layer_08_option_expression remains the option-expression stage token.',
    updated_at = NOW()
WHERE id = 'cfg_MWFP002';

UPDATE trading_registry
SET note = 'Accepted dataset-unit policy inside the resident Layer 1-9 historical-modeling system service: Layers 1-2 use one six-month panel; Layers 3-8 use one selected target symbol over one six-month window; Layer 9 EventRiskGovernor uses the six-month overlay unit. Current physical stage tokens use the nine-layer numbering.',
    updated_at = NOW()
WHERE id = 'term_DU001';

UPDATE trading_registry
SET applies_to = 'historical_backfill;model_training_workflow;automation_scheduler;systemd;manager_scheduler_daemon_state;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_05_alpha_confidence;model_06_position_projection;model_07_underlying_action;model_08_option_expression;model_09_event_risk_governor;layer_09_event_risk_governor;current_physical_names',
    note = 'Historical data/modeling workflow is owned by a resident system service covering the full Layer 1-9 stack. Layer 9 EventRiskGovernor is the service-owned residual/risk overlay lane; chat/manual CLI runs are fallback inspection, repair, smoke-test, or emergency-intervention tools, not the normal operating path.',
    updated_at = NOW()
WHERE id = 'trm_HMSR001';

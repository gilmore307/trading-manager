-- Keep remaining Layer 10 input-materialization registry terms out of the
-- active pre-replay model-training workflow.

UPDATE trading_registry
SET applies_to = 'manager_layer_ten_event_risk_governor_input_materialization;layer_10_event_risk_governor;source_10_event_risk_governor;legacy_regeneration_diagnostic',
    note = 'Legacy receipt for building source_10 / Layer 10 event-risk overview rows from local source-detector outputs. Active training no longer uses this as a pre-replay model_training_workflow input; current Layer 10 starts after concentrated replay from failure/residual attribution evidence.',
    updated_at = NOW()
WHERE id = 'trm_L9ERGMAT001';

UPDATE trading_registry
SET note = 'Layer 3+ base-stack Model Worker stages run against the complete six-month rolling fold. Local input materializers must accept start_month/end_month ranges and must not assume one chronological month per run. Layer 10 starts after concentrated replay; old source_10 materialization is a legacy diagnostic surface only.',
    updated_at = NOW()
WHERE id = 'cfg_FOLDMAT001';

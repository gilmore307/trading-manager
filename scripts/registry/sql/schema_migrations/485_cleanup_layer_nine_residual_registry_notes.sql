-- Clean remaining registry notes after conceptual Layer 04 insertion / Layer 09 EventRiskGovernor shift.
-- Registry text only; physical script/package/table names remain legacy until a reviewed renumbering migration.

UPDATE trading_registry
SET note = 'Builds the non-mutating EventRiskGovernor regeneration plan: preserve persistent Layer 1/2 data and valid base Layer 3-8 outputs where applicable, supersede old event-overlay or abnormal-activity-only legacy Layer 8 / conceptual Layer 9 artifacts, rebuild legacy event-risk surfaces only after reviewed event-feed coverage, and keep deletion dry-run-only until reviewed closeout.',
    applies_to = 'manager_event_model_regeneration_plan_v1;legacy_layer_08_event_risk_governor;conceptual_layer_09_event_risk_governor;source_08_event_risk_governor;feature_08_event_risk_governor;model_08_event_risk_governor;storage_lifecycle_hold;legacy_physical_names',
    updated_at = NOW()
WHERE id = 'scr_L8ERGREG001';

UPDATE trading_registry
SET note = 'Builds the EventRiskGovernor residual-anomaly event discovery artifact from Layers 1-8 base-stack evaluation residuals. The builder searches nearby PIT event families for explanations, observation-pool candidates, and Layer 4 event-failure-risk promotion review packets. It is a registered callable integration surface under the legacy MODEL_08 physical namespace only: no provider calls, daemon start, model activation, broker/account mutation, destructive SQL, artifact deletion, or automatic event-family promotion.',
    applies_to = 'residual_anomaly_event_discovery_v1;residual_anomaly_event_discovery_summary_v1;event_family_strategy_promotion_review_packet_v1;model_08_event_risk_governor;event_observation_pool;event_strategy_promotion_review;event_failure_risk_model;legacy_physical_names',
    updated_at = NOW()
WHERE id = 'scr_M8ERGRD001';

UPDATE trading_registry
SET     applies_to = 'trading-manager;scheduler;historical_training;layer_01_market_regime;layer_02_sector_context;layer_03_target_state_vector;layer_04_event_failure_risk;model_04_alpha_confidence;model_05_position_projection;model_06_underlying_action;model_07_option_expression;legacy_physical_names;layer_01_02_foundation_catch_up;post_model_artifact_rebuild_boundary;rolling_fold_promotion;four_one_one_split',
    note = 'Manager-owned base Layer 1-8 workflow plan. During foundation catch-up, month-scoped workflow states expose only reusable substrate data_acquisition and feature_generation for Layers 1-2 before target-specific work; base model generation/evaluation/Promotion Review belong to fold-scoped model/promotion work after frozen 4+1+1 manifests exist. Event intelligence / legacy source_08_event_risk_governor is excluded from this base graph and belongs to the separate conceptual Layer 9 risk-governor overlay.',
    updated_at = NOW()
WHERE id = 'art_MMTW001';

UPDATE trading_registry
SET     applies_to = 'trading-manager;scheduler;historical_training;manager_model_training_workflow_plan;component_completion_receipt;layer_01_02_foundation_catch_up;historical_substrate_reuse;event_risk_governor_separate;legacy_physical_names',
    note = 'Manager-owned durable base Layer 1-8 workflow state. Month-scoped checkpoints count foundation catch-up progress from reusable Layer 1/2 data acquisition and feature generation substrate, allowing chronological advancement before target-specific Layers 3-8 scheduling. Event-risk-governor state is separate conceptual Layer 9 overlay state.',
    updated_at = NOW()
WHERE id = 'art_MMTW002';

UPDATE trading_registry
SET     note = 'Accepted conceptual Layer 9 event-risk intervention severity ladder. Flatten/halt candidates require high-confidence high-severity evidence plus accepted execution risk policy or human review path.',
    updated_at = NOW()
WHERE id = 'cfg_ERIS001';

UPDATE trading_registry
SET     note = 'Required reviewed saved feed artifacts for a complete legacy source_08 / conceptual Layer 9 event-risk-governor rebuild. Missing artifacts or zero requested-window row coverage block write-mode materialization.',
    updated_at = NOW()
WHERE id = 'cfg_L8EVTCOV001';

UPDATE trading_registry
SET     note = 'Summary field reporting requested-window row counts by required event feed source for the legacy layer_eight_event_risk_governor / conceptual Layer 9 coverage gate.',
    updated_at = NOW()
WHERE id = 'fld_L4EVTCOV002';

UPDATE trading_registry
SET     note = 'Validates or explicitly dispatches bounded legacy Layer 8 / conceptual Layer 9 event-risk-feed provider acquisition from prepared task keys. Provider calls require --execute-provider-calls; model activation, broker execution, account mutation, and dashboard read-model writes remain forbidden.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTDIS001';

UPDATE trading_registry
SET     applies_to = 'historical_modeling;legacy_layer_08_event_risk_governor;conceptual_layer_09_event_risk_governor;model_04_alpha_confidence;model_05_position_projection;model_06_underlying_action;model_07_option_expression;stale_output_invalidation;legacy_physical_names',
    note = 'State-only helper that marks stale legacy event-governor-dependent workflow stages rebuild-required after event-source contract repair. It does not delete artifacts, call providers, activate models, submit broker orders, mutate accounts, or write dashboard read models.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTINV001';

UPDATE trading_registry
SET     note = 'Refreshes the durable base Layer 1-8 workflow checkpoint, ingests component receipts, records review refs, and selects the next safe or guarded stage without provider calls, model activation, broker execution, or event-overlay gating.',
    updated_at = NOW()
WHERE id = 'scr_MMTW002';

UPDATE trading_registry
SET     note = 'Prints the current base Layer 1-8 manager historical-training workflow graph and next gated stage without provider calls, model activation, broker execution, or event-overlay gating.',
    updated_at = NOW()
WHERE id = 'scr_MMTW001';

UPDATE trading_registry
SET     note = 'Legacy source_08 / conceptual Layer 9 event-risk-governor materialization accepts six-month folds, prepares detector task keys per symbol-month, and writes one fold-scoped source_08 task key for the event index.',
    updated_at = NOW()
WHERE id = 'term_FOLDMAT002';

UPDATE trading_registry
SET     note = 'Legacy source_08 / conceptual Layer 9 event-risk write-mode materialization requires each required reviewed event-feed artifact family to contain at least one row in the requested [start_month, end_month_next) window. Artifact presence alone is not sufficient.',
    updated_at = NOW()
WHERE id = 'term_L8EVTCOV002';

UPDATE trading_registry
SET     note = 'Manager receipt for building legacy source_08 / conceptual Layer 9 event-risk overview rows from local source-detector outputs over already-reviewed Layer 2 bar artifacts. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'trm_L8ERGMAT001';

-- Clean active registry locators after the Layer 10 event-risk and Layer 9 option cutover.

UPDATE trading_registry
SET key = 'LAYER_TEN_REQUIRED_EVENT_FEED_ARTIFACTS',
    path = 'trading-manager/src/trading_manager_tasks/layer_ten_event_risk_governor.py;trading-data/src/data_source/source_10_event_risk_governor/README.md',
    note = 'Required reviewed saved feed artifacts for a complete current source_10 / Layer 10 event-risk-governor rebuild. Missing artifacts or zero requested-window row coverage block write-mode materialization.',
    updated_at = NOW()
WHERE id = 'cfg_L9EVTCOV001';

UPDATE trading_registry
SET path = 'trading-manager/src/trading_manager_tasks/layer_three_target_state.py;trading-manager/src/trading_manager_tasks/layer_ten_event_risk_governor.py;trading-manager/src/trading_manager_tasks/model_training_workflow.py',
    applies_to = 'model_worker_1;layer_03_target_state_vector;layers_03_10_stack;layer_10_event_risk_governor',
    updated_at = NOW()
WHERE id = 'cfg_FOLDMAT001';

UPDATE trading_registry
SET path = 'trading-manager/src/trading_manager_tasks/layer_ten_event_risk_governor.py',
    applies_to = 'manager_layer_ten_event_risk_governor_input_materialization;event_source_coverage;requested_window',
    note = 'Summary field reporting requested-window row counts by required event feed source for the current layer_10_event_risk_governor / Layer 10 coverage gate.',
    updated_at = NOW()
WHERE id = 'fld_L4EVTCOV002';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/execute_layer_nine_option_feature_generation.py --start-month ${START_MONTH} --end-month ${END_MONTH}',
    path = '/root/projects/trading-manager/scripts/tasks/execute_layer_nine_option_feature_generation.py',
    note = 'Manager-owned current layer_09_option_expression feature-stage adapter for Layer 9 option-expression. It writes a first-class no-provider/no-feature skip receipt when the reviewed gate has zero active target chains, or delegates to trading-data feature_09 option-expression generation after approved active-path acquisition.',
    updated_at = NOW()
WHERE id = 'scr_L8FEAT001';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/review_layer_nine_option_expression_gate.py --start-month ${START_MONTH} --end-month ${END_MONTH} --write',
    path = '/root/projects/trading-manager/scripts/tasks/review_layer_nine_option_expression_gate.py',
    updated_at = NOW()
WHERE id = 'scr_L8GATE001';

UPDATE trading_registry
SET path = 'trading-manager/scripts/tasks/invalidate_layer_ten_event_downstream_outputs.py;trading-manager/src/trading_manager_tasks/model_training_invalidation.py',
    applies_to = 'historical_modeling;layer_10_event_risk_governor;model_05_alpha_confidence;model_07_position_projection;model_08_underlying_action;model_09_option_expression;stale_output_invalidation',
    updated_at = NOW()
WHERE id = 'scr_L9EVTINV001';

UPDATE trading_registry
SET path = '/root/projects/trading-manager/scripts/tasks/materialize_layer_ten_event_risk_governor_inputs.py',
    applies_to = 'manager_layer_ten_event_risk_governor_input_materialization;layer_10_event_risk_governor;source_10_event_risk_governor;model_training_workflow',
    note = 'Callable manager entrypoint that materializes current source_10 / Layer 10 event-risk-governor rows from local detector outputs over existing reviewed Layer 2 feed artifacts without provider dispatch.',
    updated_at = NOW()
WHERE id = 'scr_L9ERGMAT001';

UPDATE trading_registry
SET applies_to = 'manager_event_model_regeneration_plan;layer_10_event_risk_governor;source_10_event_risk_governor;feature_10_event_risk_governor;model_10_event_risk_governor;storage_lifecycle_hold',
    note = 'Builds the non-mutating EventRiskGovernor regeneration plan: preserve persistent Layer 1/2 data and valid base Layer 3-8 outputs where applicable, supersede old event-overlay or abnormal-activity-only artifacts, rebuild current Layer 10 event-risk surfaces only after reviewed event-feed coverage, and keep deletion dry-run-only until reviewed acceptance.',
    updated_at = NOW()
WHERE id = 'scr_L9ERGREG001';

UPDATE trading_registry
SET path = 'trading-manager/scripts/tasks/prepare_layer_ten_event_feed_backfill.py;trading-manager/src/trading_manager_tasks/event_feed_backfill.py',
    updated_at = NOW()
WHERE id = 'scr_L9EVTBF001';

UPDATE trading_registry
SET applies_to = 'event_risk_governor;layer_10_event_risk_governor;trading_guidance_record;execution_risk_control',
    note = 'Layer 10 output that modifies the decision/risk record consumed by execution risk-control. It is not a broker order, route, time-in-force, or account mutation.',
    updated_at = NOW()
WHERE id = 'trm_ERI001';

UPDATE trading_registry
SET key = 'FOLD_SCOPED_LAYER_10_EVENT_RISK_GOVERNOR_INPUTS',
    path = 'trading-manager/src/trading_manager_tasks/layer_ten_event_risk_governor.py;trading-manager/tests/test_layer_ten_event_risk_governor.py',
    note = 'Current source_10 / Layer 10 event-risk-governor materialization accepts six-month folds, prepares detector task keys per symbol-month, and writes one fold-scoped source_10 task key for the event index.',
    updated_at = NOW()
WHERE id = 'term_FOLDMAT002';

UPDATE trading_registry
SET note = 'Component completion receipt proving Layer 9 option-expression feature generation is a reviewed no-op when the Layer 9 gate accepted no active target chain and therefore no source_05/feature_09 rows are required before deterministic no-option model generation.',
    updated_at = NOW()
WHERE id = 'term_L8FEATSKIP001';

UPDATE trading_registry
SET path = 'trading-manager/src/trading_manager_tasks/layer_ten_event_risk_governor.py;trading-manager/docs/05_decision.md;trading-manager/docs/20_task_system.md',
    note = 'Current source_10 / Layer 10 event-risk write-mode materialization requires each required reviewed event-feed artifact family to contain at least one row in the requested [start_month, end_month_next) window. Artifact presence alone is not sufficient.',
    updated_at = NOW()
WHERE id = 'term_L9EVTCOV002';

UPDATE trading_registry
SET path = 'trading-manager/src/trading_manager_tasks/layer_ten_event_risk_governor.py;trading-data/src/data_source/source_10_event_risk_governor/feed_event_extraction.py;trading-manager/docs/05_decision.md',
    applies_to = 'source_10_event_risk_governor;historical_modeling;event_source_coverage;layer_10_event_risk_governor',
    note = 'Current source_10 / Layer 10 event-source coverage requires reviewed local artifacts with requested-window row coverage for Alpaca news, GDELT news, SEC company financials, and Trading Economics calendar rows before event-governor-dependent outputs may advance.',
    updated_at = NOW()
WHERE id = 'term_L9EVTCOV001';

UPDATE trading_registry
SET note = 'Manager receipt for building current source_10 / Layer 10 event-risk overview rows from local source-detector outputs over already-reviewed Layer 2 bar artifacts. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'trm_L9ERGMAT001';

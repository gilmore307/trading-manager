-- Clean remaining active current-registry references that still described Layer 9 event-risk surfaces as legacy Layer 8.
-- Historical migration files and old artifact paths remain unchanged.

UPDATE trading_registry
SET
  key = replace(replace(replace(key,
    'LAYER_08_EVENT', 'LAYER_09_EVENT'),
    'LAYER_EIGHT_EVENT', 'LAYER_NINE_EVENT'),
    'MODEL_08_EVENT', 'MODEL_09_EVENT'),
  payload = replace(replace(replace(replace(replace(replace(replace(payload,
    'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
    'legacy_layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
    'conceptual_layer_09_event_risk_governor', 'layer_09_event_risk_governor'),
    'layer_eight_event_risk_governor', 'layer_nine_event_risk_governor'),
    'layer_eight_event_feed', 'layer_nine_event_feed'),
    'invalidate_layer_eight_event_downstream_outputs.py', 'invalidate_layer_nine_event_downstream_outputs.py'),
    'materialize_layer_eight_event_risk_governor_inputs.py', 'materialize_layer_nine_event_risk_governor_inputs.py'),
  path = replace(replace(replace(replace(replace(path,
    'layer_eight_event_risk_governor', 'layer_nine_event_risk_governor'),
    'layer_eight_event_feed', 'layer_nine_event_feed'),
    'test_layer_eight_event_risk_governor.py', 'test_layer_nine_event_risk_governor.py'),
    'invalidate_layer_eight_event_downstream_outputs.py', 'invalidate_layer_nine_event_downstream_outputs.py'),
    'materialize_layer_eight_event_risk_governor_inputs.py', 'materialize_layer_nine_event_risk_governor_inputs.py'),
  applies_to = replace(replace(replace(replace(applies_to,
    'layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
    'legacy_layer_08_event_risk_governor', 'layer_09_event_risk_governor'),
    'conceptual_layer_09_event_risk_governor', 'layer_09_event_risk_governor'),
    'legacy_source_08_event_risk_governor', 'source_09_event_risk_governor'),
  note = replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(note,
    'Legacy source_08 / conceptual Layer 9', 'Current source_09 / Layer 9'),
    'legacy source_08 / conceptual Layer 9', 'current source_09 / Layer 9'),
    'legacy Layer 8 / conceptual Layer 9', 'Layer 9'),
    'legacy event-governor-dependent', 'Layer 9 event-governor-dependent'),
    'legacy event-risk surfaces', 'current Layer 9 event-risk surfaces'),
    'legacy event-overlay or abnormal-activity-only legacy Layer 8 / conceptual Layer 9 artifacts', 'superseded event-overlay or abnormal-activity-only Layer 9 artifacts'),
    'legacy event-governor', 'Layer 9 event-governor'),
    'legacy Layer 8', 'Layer 9'),
    'Legacy ', 'Current '),
    'legacy ', 'current '),
  updated_at = NOW();

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 5 AlphaConfidenceModel alpha_confidence_vector rows. Current physical script/model path is model_05_alpha_confidence.',
    updated_at = NOW()
WHERE id = 'scr_M5ACGEN';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 6 PositionProjectionModel position_projection_vector rows. Current physical script/model path is model_06_position_projection.',
    updated_at = NOW()
WHERE id = 'scr_M6PPGEN';

UPDATE trading_registry
SET note = 'Stable callable entrypoint for generating deterministic Layer 7 UnderlyingActionModel underlying_action_plan rows. Current physical script/model path is model_07_underlying_action.',
    updated_at = NOW()
WHERE id = 'scr_M7UAGEN';

UPDATE trading_registry
SET note = 'Layer 3+ base-stack Model Worker stages run against one selected target/instrument over the complete six-month rolling fold. Local input materializers must accept start_month/end_month ranges and must not assume one chronological month per run. Layer 9 event-governor materialization remains a separate overlay surface.',
    updated_at = NOW()
WHERE id = 'cfg_FOLDMAT001';

UPDATE trading_registry
SET note = 'Validates or explicitly dispatches bounded Layer 9 event-risk-feed provider acquisition from prepared task keys. Provider calls require --execute-provider-calls; model activation, broker execution, account mutation, and dashboard read-model writes remain forbidden.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTDIS001';

UPDATE trading_registry
SET note = 'Callable manager entrypoint that materializes current source_09 / Layer 9 event-risk-governor rows from local detector outputs over existing reviewed Layer 2 feed artifacts without provider dispatch.',
    updated_at = NOW()
WHERE id = 'scr_L8ERGMAT001';

UPDATE trading_registry
SET note = 'Builds the non-mutating EventRiskGovernor regeneration plan: preserve persistent Layer 1/2 data and valid base Layer 3-8 outputs where applicable, supersede old event-overlay or abnormal-activity-only Layer 9 artifacts, rebuild current Layer 9 event-risk surfaces only after reviewed event-feed coverage, and keep deletion dry-run-only until reviewed closeout.',
    updated_at = NOW()
WHERE id = 'scr_L8ERGREG001';

UPDATE trading_registry
SET note = 'Prepares reviewed monthly event-feed task keys required before rebuilding Layer 9 event-governor-dependent outputs. Preparation performs no provider calls, model activation, broker execution, account mutation, or dashboard read-model writes.',
    updated_at = NOW()
WHERE id = 'scr_L8EVTBF001';

UPDATE trading_registry
SET note = 'Layer 9 output that modifies the decision/risk record consumed by execution risk-control. It is not a broker order, route, time-in-force, or account mutation.',
    updated_at = NOW()
WHERE id = 'trm_ERI001';

UPDATE trading_registry
SET note = 'Current source_09 / Layer 9 event-risk-governor materialization accepts six-month folds, prepares detector task keys per symbol-month, and writes one fold-scoped source_09 task key for the event index.',
    updated_at = NOW()
WHERE id = 'term_FOLDMAT002';

UPDATE trading_registry
SET note = 'Current source_09 / Layer 9 event-risk write-mode materialization requires each required reviewed event-feed artifact family to contain at least one row in the requested [start_month, end_month_next) window. Artifact presence alone is not sufficient.',
    updated_at = NOW()
WHERE id = 'term_L8EVTCOV002';

UPDATE trading_registry
SET note = 'Current source_09 / Layer 9 event-source coverage requires reviewed local artifacts with requested-window row coverage for Alpaca news, GDELT news, SEC company financials, and Trading Economics calendar rows before event-governor-dependent outputs may advance.',
    updated_at = NOW()
WHERE id = 'term_L8EVTCOV001';

UPDATE trading_registry
SET note = 'Manager receipt for building current source_09 / Layer 9 event-risk overview rows from local source-detector outputs over already-reviewed Layer 2 bar artifacts. It performs no provider calls, model activation, broker execution, or storage lifecycle mutation.',
    updated_at = NOW()
WHERE id = 'trm_L8ERGMAT001';

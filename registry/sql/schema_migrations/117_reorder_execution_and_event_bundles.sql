UPDATE trading_registry
SET key = '06_POSITION_EXECUTION_MODEL_INPUTS',
    payload = '06_position_execution_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/06_position_execution_model_inputs',
    applies_to = 'trading-data;trading-model;position_execution_model',
    artifact_sync_policy = 'sync_artifact',
    note = '06 manager-facing PositionExecutionModel data bundle; writes selected option contract time series from entry through exit plus one hour for execution analysis',
    updated_at = CURRENT_TIMESTAMP
WHERE key = '06_EVENT_OVERLAY_MODEL_INPUTS';

UPDATE trading_registry
SET key = '07_EVENT_OVERLAY_MODEL_INPUTS',
    payload = '07_event_overlay_model_inputs',
    path = 'trading-data/src/trading_data/data_bundles/07_event_overlay_model_inputs',
    applies_to = 'trading-data;trading-model;event_overlay_model',
    artifact_sync_policy = 'sync_artifact',
    note = '07 manager-facing EventOverlayModel data bundle; writes one SQL event overview row per macro/news/SEC/abnormal-activity event with details behind references',
    updated_at = CURRENT_TIMESTAMP
WHERE key = '07_PORTFOLIO_RISK_MODEL_INPUTS';

DELETE FROM trading_registry
WHERE key IN (
  '06_EVENT_OVERLAY_MODEL_INPUTS_BUNDLE_CONFIG',
  '07_PORTFOLIO_RISK_MODEL_INPUTS_BUNDLE_CONFIG'
);

UPDATE trading_registry
SET applies_to = replace(applies_to, '06_event_overlay_model_inputs', '07_event_overlay_model_inputs'),
    path = replace(path, '06_event_overlay_model_inputs', '07_event_overlay_model_inputs'),
    updated_at = CURRENT_TIMESTAMP
WHERE applies_to LIKE '%06_event_overlay_model_inputs%'
   OR path LIKE '%06_event_overlay_model_inputs%';

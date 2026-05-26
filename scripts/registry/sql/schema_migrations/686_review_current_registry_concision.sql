-- Tighten current registry rows after full line-by-line review.
--
-- Keep append-only migration history intact, but make the active registry
-- smaller and more regular:
-- - remove generic glossary rows that belong outside the trading registry;
-- - keep term payloads as stable tokens instead of inline prose/lists;
-- - move policy/list rows from term to config;
-- - align script/template payloads with their narrowest kind.

DELETE FROM trading_registry
WHERE key IN (
  'CODEX',
  'GITHUB',
  'OPENCLAW',
  'POSTGRESQL',
  'SMB',
  'SQL',
  'TAILSCALE',
  'TRADING_MANAGER_REGISTRY'
);

UPDATE trading_registry
SET payload = 'dashboard_tasks_page_historical_task_progress_summary',
    updated_at = NOW()
WHERE key = 'DASHBOARD_HISTORICAL_TASK_PROGRESS_PAGE';

UPDATE trading_registry
SET payload = 'periodic_30s_storage_refresh;websocket_latest_json_push;http_fallback_polling_available',
    updated_at = NOW()
WHERE key = 'DASHBOARD_READ_MODEL_REFRESH_CADENCE';

UPDATE trading_registry
SET payload = 'vite;react;typescript',
    updated_at = NOW()
WHERE key = 'DASHBOARD_WEB_RUNTIME_STACK';

UPDATE trading_registry
SET payload = 'component_01_intake;candidate_entry_pool_to_component_02_entry;open_position_pool_to_component_03_lifecycle;component_02_03_to_component_04_option_review;component_04_to_component_05_order_intent;component_05_to_component_06_execution_gate;post_failure_to_component_07_failure_review',
    updated_at = NOW()
WHERE key = 'EXECUTION_RUNTIME_COMPONENT_SEQUENCE';

UPDATE trading_registry
SET payload_format = 'integer',
    payload = '25',
    updated_at = NOW()
WHERE key = 'LAYER_TWO_HISTORICAL_TRAINING_REQUEST_COUNT';

UPDATE trading_registry
SET payload = 'layer_02_sector_context_stage_coverage_by_request_id_and_universe',
    updated_at = NOW()
WHERE key = 'LAYER_TWO_STAGE_COVERAGE_GATE';

UPDATE trading_registry
SET payload = 'layer_01_feature_from_reviewed_feed_artifacts;provider_calls=0;model_activation=false;broker_execution=false',
    updated_at = NOW()
WHERE key = 'MANAGER_LAYER_ONE_FEATURE_FROM_FEED_ARTIFACTS_POLICY';

UPDATE trading_registry
SET payload = 'layer_02_feature_from_reviewed_feed_artifacts;provider_calls=0;model_activation=false;broker_execution=false',
    updated_at = NOW()
WHERE key = 'MANAGER_LAYER_TWO_FEATURE_FROM_FEED_ARTIFACTS_POLICY';

UPDATE trading_registry
SET payload = 'reviewed_not_yet_listed_accepted_skip;skip_future_matching=true;terminal_skip_not_ready',
    updated_at = NOW()
WHERE key = 'PREFLIGHT_ACCEPTED_SKIP_POLICY';

UPDATE trading_registry
SET payload = 'autonomous_historical_provider_acquisition_for_bounded_manager_request_ids;manual_per_batch_gate=false',
    updated_at = NOW()
WHERE key = 'PROVIDER_DISPATCH_EXECUTE_IS_AUTONOMOUS_HISTORICAL_ACQUISITION';

UPDATE trading_registry
SET payload = 'optional_command_override',
    updated_at = NOW()
WHERE key = 'TRADING_MANAGER_DASHBOARD_REFRESH_COMMAND';

UPDATE trading_registry
SET payload = 'M01=model_01_market_regime;M02=model_02_sector_context;M03=model_03_target_state_vector;M04=model_04_event_failure_risk;M05=model_05_alpha_confidence;M06=model_06_dynamic_risk_policy;M07=model_07_position_projection;M08=model_08_underlying_action;M09=model_09_option_expression;M10=model_10_event_risk_governor',
    updated_at = NOW()
WHERE key = 'TRADING_MODEL_SEQUENCE';

UPDATE trading_registry
SET kind = 'config',
    updated_at = NOW()
WHERE key IN (
  'CRYPTO_SINGLE_ASSET_ETF_TARGET_PROXY_BOUNDARY',
  'HISTORICAL_DATASET_UNIT_POLICY',
  'MODEL_PROMOTION_SCRIPT_CALLED_AGENT_DECISION_POLICY',
  'PROMOTION_NOT_ACTIVATION_POLICY',
  'REPLAY_EVENT_LAYER_ACQUISITION_FEEDS',
  'REPLAY_FEED_COVERAGE_STATUS_VALUES',
  'ROLLING_FOLD_FOUR_ONE_ONE_SPLIT',
  'SHARED_LAYER_PREFIXED_STATIC_FILE_NAMES'
);

UPDATE trading_registry
SET payload = 'fold_scoped_layer_03_target_state_inputs',
    updated_at = NOW()
WHERE key = 'FOLD_SCOPED_LAYER_03_TARGET_STATE_INPUTS';

UPDATE trading_registry
SET payload = 'fold_scoped_layer_10_event_risk_governor_inputs',
    updated_at = NOW()
WHERE key = 'FOLD_SCOPED_LAYER_10_EVENT_RISK_GOVERNOR_INPUTS';

UPDATE trading_registry
SET payload = 'historical_data_acquisition',
    updated_at = NOW()
WHERE key = 'HISTORICAL_DATA_ACQUISITION';

UPDATE trading_registry
SET payload = 'manager_stage_failure_register_proposal',
    updated_at = NOW()
WHERE key = 'MANAGER_STAGE_FAILURE_REGISTER_PROPOSAL';

UPDATE trading_registry
SET payload = 'official_macro_release_calendar',
    updated_at = NOW()
WHERE key = 'OFFICIAL_MACRO_RELEASE_CALENDAR';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/run_agent_error_agent.py',
    updated_at = NOW()
WHERE key = 'MANAGER_AGENT_ERROR_AGENT_RUNNER';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/tasks/run_safe_error_repair.py',
    updated_at = NOW()
WHERE key = 'MANAGER_SAFE_ERROR_REPAIR_RUNNER';

UPDATE trading_registry
SET kind = 'template',
    payload = 'trading-manager-historical-scheduler.service',
    updated_at = NOW()
WHERE key = 'MANAGER_HISTORICAL_SCHEDULER_SYSTEMD_SERVICE_TEMPLATE';

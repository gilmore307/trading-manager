-- Register formal realtime live-observe approval and execution path.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_RTLF001',
    'term',
    'REALTIME_LIVE_OBSERVE_APPROVAL',
    'text',
    'realtime_live_observe_approval_v1',
    'trading-execution/src/trading_execution/market_data/live_approval.py',
    'trading-execution;trading-manager;realtime_market_data_observe_only;provider_call_gate;no_model_activation;no_broker_execution;no_order_construction;no_account_mutation',
    'sync_artifact',
    'Reviewed approval artifact required before formal realtime provider observation. It bounds sources, instruments, expiry, provider-call budget, and explicitly forbids model activation, broker execution, order construction, and account mutation.'
  ),
  (
    'trm_RTLF002',
    'term',
    'REALTIME_LIVE_OBSERVE_APPROVAL_VALIDATION',
    'text',
    'realtime_live_observe_approval_validation_v1',
    'trading-execution/src/trading_execution/market_data/live_approval.py',
    'trading-execution;realtime_live_observe_approval_v1;approval_validation;provider_call_budget;source_scope;instrument_scope;expiry_check',
    'sync_artifact',
    'Validation result for realtime live-observe approval artifacts before any provider market-data call is attempted.'
  ),
  (
    'trm_RTLF003',
    'term',
    'EXECUTION_REALTIME_LIVE_OBSERVE_RESULT',
    'text',
    'execution_realtime_live_observe_result_v1',
    'trading-execution/src/trading_execution/market_data/live_provider.py',
    'trading-execution;realtime_live_observe_approval_v1;alpaca;thetadata;okx;read_only_provider_observation;realtime_capture_row_v1;realtime_feature_snapshot_v1;execution_model_decision_input_snapshot_v1',
    'sync_artifact',
    'Formal execution-side read-only provider observation result. It may include provider market-data calls only after validated approval and explicit execute flag; it still forbids model activation, broker execution, order construction, and account mutation.'
  ),
  (
    'trm_RTLF004',
    'term',
    'REALTIME_LIVE_OBSERVATION',
    'text',
    'realtime_live_observation_v1',
    'trading-execution/src/trading_execution/market_data/live_provider.py',
    'trading-execution;read_only_provider_observation;normalized_payload_ref;provider_status;approved_realtime_capture',
    'sync_artifact',
    'One approved read-only realtime provider observation with normalized payload reference and provider status.'
  ),
  (
    'scr_RTLF001',
    'script',
    'EXECUTION_REALTIME_LIVE_OBSERVE_EXECUTE',
    'command',
    'PYTHONPATH=src python3 scripts/execution/execute_live_observe.py --request ${REQUEST_JSON} --approval ${APPROVAL_JSON} --execute-live-observe',
    'trading-execution/scripts/execution/execute_live_observe.py',
    'trading-execution;realtime_live_observe_approval_v1;execution_realtime_live_observe_result_v1;approved_read_only_provider_call',
    'sync_artifact',
    'Executes reviewed read-only realtime provider observation. Without --execute-live-observe it remains plan/validation only.'
  ),
  (
    'cfg_RTLF001',
    'config',
    'REALTIME_FORMAL_INTEGRATION_POLICY',
    'text',
    'formal_realtime_provider_observe_requires_realtime_live_observe_approval_v1;manager_control_plane_rows_may_persist_only_on_explicit_persist_flag;model_activation_requires_separate_promotion_decision;broker_order_construction_and_account_mutation_require_separate_execution_gate',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;trading-manager;formal_realtime_integration;provider_observe;manager_persistence;model_activation_gate;broker_execution_gate',
    'sync_artifact',
    'Formal realtime integration policy separating approved provider observation and explicit manager evidence persistence from later model activation and broker/account mutation gates.'
  ),
  (
    'trm_RTLF005',
    'term',
    'MANAGER_REALTIME_SHADOW_HANDOFF_PERSISTENCE',
    'text',
    'manager_realtime_shadow_handoff_explicit_persistence_v1',
    'trading-manager/src/trading_manager_tasks/realtime_shadow_handoff.py',
    'trading-manager;manager_realtime_shadow_handoff_control_plane_bundle_v1;persist_completion_rows;run_manifest_v1;artifact_ref_v1;ready_signal_v1',
    'sync_artifact',
    'Manager realtime shadow handoff can now explicitly persist normalized run/artifact/ready rows when --persist-normalized-rows is supplied with a durable receipt URI/database context.'
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

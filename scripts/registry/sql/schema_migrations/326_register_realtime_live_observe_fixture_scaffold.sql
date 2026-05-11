-- Register realtime live-observe fixture scaffold and cross-repo rehearsal path.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_RTLV001',
    'term',
    'EXECUTION_REALTIME_LIVE_OBSERVE_ADAPTER_PLAN',
    'text',
    'execution_realtime_live_observe_adapter_plan_v1',
    'trading-execution/src/trading_execution/market_data/live_observe.py',
    'trading-execution;alpaca;thetadata;okx;calendar_discovery;execution_account_state;derived_model_context;live_observe_fixture;no_provider_calls;no_broker_calls',
    'sync_artifact',
    'Concrete side-effect-free realtime adapter plan row covering provider, event, account-context, and derived-model-context routes. It is fixture/shadow planning only and opens no sockets, calls no providers, resolves no secrets, activates no models, and mutates no broker/account state.'
  ),
  (
    'trm_RTLV002',
    'term',
    'EXECUTION_REALTIME_CAPTURE_FIXTURE_SET',
    'text',
    'execution_realtime_capture_fixture_set_v1',
    'trading-execution/src/trading_execution/market_data/live_observe.py',
    'trading-execution;realtime_capture_contract_v1;shadow_monitoring;forward_holdout;fixture_replay;no_persistence_by_default',
    'sync_artifact',
    'Fixture capture row bundle for provider/account/event realtime routes. Rows satisfy realtime capture validation for shadow rehearsal while preserving zero provider calls, zero broker calls, zero model activation, and zero account mutation.'
  ),
  (
    'trm_RTLV003',
    'term',
    'EXECUTION_REALTIME_SHADOW_FIXTURE_BUNDLE',
    'text',
    'execution_realtime_shadow_fixture_bundle_v1',
    'trading-execution/src/trading_execution/market_data/live_observe.py',
    'trading-execution;execution_realtime_live_observe_adapter_plan_v1;execution_realtime_capture_fixture_set_v1;realtime_feature_snapshot_v1;execution_model_decision_input_snapshot_v1',
    'sync_artifact',
    'Execution-side realtime shadow bundle that builds adapter plans, capture fixtures, realtime feature snapshots, and model decision input snapshots without live provider calls, model activation, order construction, persistence, or account mutation.'
  ),
  (
    'trm_RTLV004',
    'term',
    'MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSAL',
    'text',
    'manager_realtime_shadow_handoff_rehearsal_v1',
    'trading-manager/scripts/tasks/rehearse_realtime_shadow_handoff.py',
    'trading-manager;trading-execution;trading-model;execution_realtime_shadow_fixture_bundle_v1;model_realtime_decision_route_plan_v1;manager_realtime_shadow_handoff_control_plane_bundle_v1',
    'sync_artifact',
    'Cross-repository side-effect-free rehearsal: execution realtime fixture bundle -> model realtime route plan -> manager realtime shadow handoff receipt/control-plane bundle.'
  ),
  (
    'scr_RTLV001',
    'script',
    'EXECUTION_REALTIME_LIVE_OBSERVE_ADAPTER_PLAN_SCRIPT',
    'command',
    'PYTHONPATH=src python3 scripts/execution/plan_live_observe_adapters.py --mode fixture_replay --instrument-ref ${INSTRUMENT_REF}',
    'trading-execution/scripts/execution/plan_live_observe_adapters.py',
    'trading-execution;execution_realtime_live_observe_adapter_plan_v1;alpaca;thetadata;okx;calendar_discovery;execution_account_state;derived_model_context',
    'sync_artifact',
    'Builds concrete realtime live-observe fixture adapter plans for provider/account/event/model-context routes without executing streams or resolving secrets.'
  ),
  (
    'scr_RTLV002',
    'script',
    'EXECUTION_REALTIME_SHADOW_FIXTURE_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/execution/build_realtime_shadow_fixture.py --decision-time ${DECISION_TIME} --historical-dataset-snapshot-ref ${HISTORICAL_DATASET_SNAPSHOT_REF} --frozen-model-config-ref ${FROZEN_MODEL_CONFIG_REF}',
    'trading-execution/scripts/execution/build_realtime_shadow_fixture.py',
    'trading-execution;execution_realtime_shadow_fixture_bundle_v1;realtime_feature_snapshot_v1;execution_model_decision_input_snapshot_v1;fixture_replay',
    'sync_artifact',
    'Builds execution-side realtime shadow fixture bundle from adapter plans through model-decision input snapshot without provider calls, model activation, broker calls, order construction, persistence, or account mutation.'
  ),
  (
    'scr_RTLV003',
    'script',
    'MANAGER_REALTIME_SHADOW_HANDOFF_REHEARSE',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/rehearse_realtime_shadow_handoff.py --decision-time ${DECISION_TIME} --historical-dataset-snapshot-ref ${HISTORICAL_DATASET_SNAPSHOT_REF} --frozen-model-config-ref ${FROZEN_MODEL_CONFIG_REF}',
    'trading-manager/scripts/tasks/rehearse_realtime_shadow_handoff.py',
    'trading-manager;manager_realtime_shadow_handoff_rehearsal_v1;execution_realtime_shadow_fixture_bundle_v1;model_realtime_decision_route_plan_v1;manager_realtime_shadow_handoff_control_plane_bundle_v1',
    'sync_artifact',
    'Runs the cross-repo realtime shadow handoff rehearsal and emits execution fixture, model route plan, and manager receipt bundle without side effects.'
  ),
  (
    'cfg_RTLV001',
    'config',
    'REALTIME_LIVE_OBSERVE_FIXTURE_POLICY',
    'text',
    'fixture_replay_before_live_observe;alpaca_thetadata_okx_calendar_account_and_model_context_routes_scaffolded;live_observe_requires_reviewed_live_stream_approval_ref;no_provider_calls;no_secret_resolution;no_model_activation;no_broker_calls;no_order_construction;no_account_mutation',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;trading-manager;realtime_live_observe;fixture_replay;approval_gate;shadow_monitoring',
    'sync_artifact',
    'Realtime live-observe fixture policy: complete the route/capture/feature/handoff rehearsal before any real stream, and keep live stream/provider/broker/model activation behind explicit reviewed gates.'
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

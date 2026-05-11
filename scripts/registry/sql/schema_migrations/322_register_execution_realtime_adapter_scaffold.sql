-- Register execution realtime adapter planning and capture validation scaffold.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EXEC_RT003',
    'term',
    'EXECUTION_REALTIME_SUBSCRIPTION_PLAN',
    'text',
    'execution_realtime_subscription_plan_v1',
    'trading-execution/src/trading_execution/market_data/adapters.py',
    'trading-execution;realtime_market_data;alpaca;okx;thetadata;derived_model_context;calendar_discovery;execution_account_state;no_provider_calls',
    'sync_artifact',
    'Side-effect-free realtime subscription plan row for dry-run, fixture-replay, and approval-blocked live-observe routes. It plans source/interface/model-layer/instrument coverage without opening sockets, calling providers, resolving secrets, activating models, or mutating broker/account state.'
  ),
  (
    'trm_EXEC_RT004',
    'term',
    'EXECUTION_REALTIME_SUBSCRIPTION_PLAN_SET',
    'text',
    'execution_realtime_subscription_plan_set_v1',
    'trading-execution/src/trading_execution/market_data/adapters.py',
    'trading-execution;realtime_market_data;subscription_planning;no_provider_calls;no_broker_calls',
    'sync_artifact',
    'Serializable side-effect-free plan set emitted by realtime capture planning. Provider and broker call counts must remain zero.'
  ),
  (
    'trm_EXEC_RT005',
    'term',
    'REALTIME_CAPTURE_VALIDATION',
    'text',
    'realtime_capture_validation_v1',
    'trading-execution/src/trading_execution/market_data/capture.py',
    'trading-execution;realtime_capture_contract_v1;forward_holdout;shadow_monitoring;validation;no_provider_calls;no_broker_calls;no_model_activation',
    'sync_artifact',
    'Local validation result for candidate realtime capture rows. It checks required fields, dataset role, forbidden actions, parseable times, and label maturity without persistence, provider calls, broker calls, or model activation.'
  ),
  (
    'scr_EXEC_RT001',
    'script',
    'EXECUTION_REALTIME_CAPTURE_PLAN',
    'command',
    'PYTHONPATH=src python3 scripts/execution/plan_realtime_capture.py',
    'trading-execution/scripts/execution/plan_realtime_capture.py',
    'trading-execution;execution_realtime_subscription_plan_set_v1;realtime_market_data;dry_run;fixture_replay;live_observe_blocked;no_provider_calls',
    'sync_artifact',
    'Builds realtime subscription/capture plans without external calls. live_observe rows remain planning-only and require explicit future approval before any adapter opens streams.'
  ),
  (
    'scr_EXEC_RT002',
    'script',
    'EXECUTION_REALTIME_CAPTURE_VALIDATE',
    'command',
    'PYTHONPATH=src python3 scripts/execution/validate_realtime_capture.py ${CAPTURE_JSON}',
    'trading-execution/scripts/execution/validate_realtime_capture.py',
    'trading-execution;realtime_capture_validation_v1;realtime_capture_contract_v1;forward_holdout;shadow_monitoring',
    'sync_artifact',
    'Validates one candidate realtime capture JSON object against realtime_capture_contract_v1 without provider calls, broker calls, model activation, or persistence.'
  ),
  (
    'cfg_EXEC_RT004',
    'config',
    'EXECUTION_REALTIME_LIVE_OBSERVE_GATE_POLICY',
    'text',
    'live_observe_requires_live_stream_approval_ref_and_runtime_adapter_acceptance;dry_run_and_fixture_replay_only_until_approved;planning_does_not_execute_streams',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_market_data;live_observe;approval_gate;runtime_adapter_acceptance',
    'sync_artifact',
    'Policy that realtime adapter scaffolds may plan live_observe rows, but cannot open provider streams until explicit live-stream approval and runtime adapter acceptance exist.'
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

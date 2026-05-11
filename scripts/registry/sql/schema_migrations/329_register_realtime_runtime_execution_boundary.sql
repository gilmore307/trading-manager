-- Register execution-owned realtime runtime boundary.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_RTEB001',
    'term',
    'EXECUTION_REALTIME_RUNTIME_CONTROLLER',
    'text',
    'execution_realtime_runtime_controller_v1',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;realtime_monitoring;runtime_control;provider_stream_lifecycle;not_manager_controlled',
    'sync_artifact',
    'Execution-owned realtime monitoring runtime boundary. Trading-execution owns live observe processes, subscriptions, throttling, reconnect/backoff, provider stream lifecycle, and runtime health for realtime market monitoring.'
  ),
  (
    'trm_RTEB002',
    'term',
    'MANAGER_REALTIME_OBSERVATION_CONSUMER',
    'text',
    'manager_realtime_observation_consumer_v1',
    'trading-manager/docs/95_task_system.md',
    'trading-manager;realtime_receipts;append_only_evidence;shadow_handoff;not_runtime_controller',
    'sync_artifact',
    'Manager may consume execution-produced realtime receipts, summaries, coverage rows, and shadow evidence, but must not own or schedule the realtime monitoring runtime.'
  ),
  (
    'cfg_RTEB001',
    'config',
    'REALTIME_RUNTIME_ISOLATION_POLICY',
    'text',
    'realtime_monitoring_runtime_is_execution_owned;manager_may_consume_append_only_receipts_but_must_not_start_stop_schedule_throttle_or_reconnect_provider_streams;historical_scheduler_must_not_control_realtime_monitoring',
    'trading-execution/docs/09_realtime_data.md',
    'trading-execution;trading-manager;runtime_isolation;historical_scheduler_boundary;live_monitoring_priority',
    'sync_artifact',
    'Policy separating realtime monitoring runtime control from manager-owned historical modeling. Manager remains an evidence consumer and historical orchestration plane, not the live market monitor controller.'
  ),
  (
    'cfg_RTEB002',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_REALTIME_BOUNDARY',
    'text',
    'manager_historical_scheduler_reserves_capacity_for_realtime_monitoring_but_does_not_control_realtime_monitoring_runtime',
    'trading-manager/docs/98_automation_scheduler.md',
    'trading-manager;historical_scheduler;realtime_monitoring;capacity_reservation;not_runtime_control',
    'sync_artifact',
    'Historical scheduler policy: reserve capacity and back off for realtime monitoring/execution, but never start, stop, schedule, or reconnect realtime provider monitoring processes.'
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

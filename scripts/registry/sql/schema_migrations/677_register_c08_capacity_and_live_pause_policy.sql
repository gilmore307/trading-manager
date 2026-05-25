-- Register C08 capacity simulation and live-runtime historical task pause policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECSHADOW003',
    'artifact_type',
    'EXECUTION_C08_CAPACITY_SIMULATION',
    'text',
    'execution_c08_capacity_simulation',
    'trading-execution/docs/03_contracts.md;trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/scripts/execution/simulate_c08_capacity.py;trading-execution/src/trading_execution/model_lifecycle.py',
    'trading-execution;runtime_model_lifecycle;c08_shadow_runtime_component;capacity_simulation;side_effect_free',
    'sync_artifact',
    'Side-effect-free estimate of how many realtime model groups C08 can admit under CPU, memory, and p95 latency budgets. It performs no provider calls, model activation, broker calls, order construction, account mutation, or active-pointer writes.'
  ),
  (
    'cfg_LIVERUNTIME001',
    'config',
    'LIVE_RUNTIME_HISTORICAL_MODEL_TASK_PAUSE_POLICY',
    'text',
    'live_runtime_pauses_historical_model_tasks;realtime_trading_priority;c08_capacity_measured_without_historical_training_load',
    'trading-manager/docs/25_automation_scheduler.md;trading-manager/src/trading_manager_tasks/scheduler.py;trading-execution/docs/40_runtime_model_lifecycle.md',
    'trading-manager;scheduler;historical_model_tasks;live_runtime;resource_priority;c08_shadow_runtime_component',
    'sync_artifact',
    'When future live runtime is enabled, manager scheduler ticks must pause historical model tasks and return live_runtime_historical_model_tasks_paused. Realtime trading, market-data ingestion, broker gates, account freshness, and C08 model-group comparison keep resource priority.'
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

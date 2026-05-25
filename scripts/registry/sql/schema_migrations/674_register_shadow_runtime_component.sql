-- Register S01 as the separate intraday Shadow runtime component.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_EXECSHADOW001',
    'artifact_type',
    'EXECUTION_SHADOW_RUNTIME_COMPONENT',
    'text',
    'execution_shadow_runtime_component',
    'trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/src/trading_execution/model_lifecycle.py',
    'trading-execution;runtime_model_lifecycle;shadow_runtime_component;market_hours;active_shadow_model_comparison',
    'sync_artifact',
    'Execution-owned intraday Shadow component. It runs active and promoted shadow models over realtime market-hours snapshots, records comparable evidence, and feeds mature evidence into execution_shadow_cycle_selection. It is not used by promotion Replay and has no broker/order/account or active-pointer mutation authority.'
  ),
  (
    'art_EXECSHADOW002',
    'artifact_type',
    'EXECUTION_SHADOW_MODEL_RUNTIME_EVIDENCE',
    'text',
    'execution_shadow_model_runtime_evidence',
    'trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/src/trading_execution/model_lifecycle.py',
    'trading-execution;runtime_model_lifecycle;shadow_runtime_component;realtime_model_decision_effectiveness',
    'sync_artifact',
    'Evidence emitted by S01 Shadow Model Comparison from realtime market-hours active/shadow model runs. It may support later runtime roster selection but cannot authorize orders, active pointer writes, broker calls, or account mutation.'
  ),
  (
    'cfg_SHADOWS01001',
    'config',
    'SHADOW_RUNTIME_COMPONENT_POLICY',
    'text',
    's01_shadow_model_comparison_intraday_component;realtime_data_only;already_promoted_models_only;not_replay;active_model_only_trading_authority',
    'trading-execution/docs/40_runtime_model_lifecycle.md;trading-execution/docs/02_architecture.md;trading-execution/src/trading_execution/model_lifecycle.py',
    'trading-execution;runtime_model_lifecycle;shadow_runtime_component;execution_shadow_cycle_selection',
    'sync_artifact',
    'S01 Shadow Model Comparison is a separate market-hours component outside the C01-C07 trading decision graph. It compares the active model and already-promoted shadow models on realtime data. Shadow outputs are evidence only; only the current active model can route decisions into live C01-C06 trading authority until an execution_active_model_config_write gate changes the pointer.'
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

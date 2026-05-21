-- Route execution runtime status through storage-hosted dashboard WebSocket.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EXECREAL002',
    'config',
    'EXECUTION_REALTIME_RUNTIME_STATUS_WEBSOCKET_ROUTE',
    'text',
    '/ws/read-models/execution_realtime_trading_runtime_status/latest',
    'trading-storage/src/trading_storage/dashboard_execution_runtime.py;trading-dashboard/vite.config.ts',
    'trading-execution;trading-storage;trading-dashboard;websocket;realtime_trading_runtime;dashboard_read_model',
    'sync_artifact',
    'Storage-hosted dashboard read-model WebSocket route for execution_realtime_trading_runtime_status. Execution writes the readiness artifact, storage materializes the read model, and dashboard streams latest.json changes without provider calls, model activation, broker execution, order submission, or account mutation.'
  ),
  (
    'cfg_EXECREAL003',
    'config',
    'EXECUTION_REALTIME_RUNTIME_CHECK_PATH_TRIGGER',
    'text',
    'trading-execution-realtime-runtime-check.path;PathChanged=storage/04_execution_artifacts/runtime/active_model;refreshes_dashboard_read_model',
    'trading-execution/deploy/systemd/trading-execution-realtime-runtime-check.path;trading-execution/deploy/systemd/trading-execution-realtime-runtime-check.service',
    'trading-execution;systemd;active_model_pointer;runtime_status;websocket_updates',
    'sync_artifact',
    'Systemd path trigger for execution realtime runtime readiness. It replaces minute polling as the primary status refresh path by refreshing when the active model pointer changes and then materializing the storage-hosted WebSocket read model.'
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

UPDATE trading_registry
SET note = 'Deprecated fallback timer template for execution_realtime_trading_runtime_status. The primary route is EXECUTION_REALTIME_RUNTIME_CHECK_PATH_TRIGGER plus the storage-hosted WebSocket read-model route.',
    applies_to = 'trading-execution;systemd;realtime_trading_runtime;fallback_timer;deprecated_primary_route',
    updated_at = NOW()
WHERE id = 'cfg_EXECREAL001';

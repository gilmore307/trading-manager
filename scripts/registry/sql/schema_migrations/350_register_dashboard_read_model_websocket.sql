-- Register the first read-only dashboard read-model WebSocket stream.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM010',
    'config',
    'DASHBOARD_READ_MODEL_WEBSOCKET_STREAM',
    'text',
    '/ws/read-models/<contract_type>/latest',
    '/root/projects/trading-dashboard/vite.config.ts',
    'trading-dashboard;websocket;dashboard_read_model;historical_task_progress_summary_v1;read_only_stream',
    'sync_artifact',
    'Read-only WebSocket route that streams storage-hosted dashboard read-model latest.json snapshots to public dashboard clients. It performs no provider calls, manager dispatch, model activation, broker execution, account mutation, or storage writes.'
  ),
  (
    'cfg_DASHRM009',
    'config',
    'DASHBOARD_READ_MODEL_REFRESH_CADENCE',
    'text',
    '30s storage refresh; websocket pushes latest.json changes; HTTP fallback polling remains available',
    '/root/projects/trading-storage/deploy/systemd/trading-storage-dashboard-read-model-refresh.timer',
    'trading-storage;trading-dashboard;dashboard_read_model;refresh_cadence;websocket_stream',
    'sync_artifact',
    'Accepted near-real-time public dashboard status cadence. Storage owns periodic read-model refresh; dashboard streams storage-hosted latest.json changes without bypassing storage boundaries.'
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

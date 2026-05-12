-- Register the current system status dashboard read-model producer and refresh entrypoints.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM011',
    'config',
    'CURRENT_SYSTEM_STATUS_SUMMARY_BOUNDARY',
    'text',
    'server_status;dashboard_api;systemd_services;read_model_freshness;refresh_timer_status',
    '/root/projects/trading-storage/src/trading_storage/dashboard_system_status.py',
    'current_system_status_summary_v1;trading-storage;trading-dashboard;infrastructure_status;read_only',
    'sync_artifact',
    'Current Status page boundary: infrastructure/server/API/service/read-model-refresh posture only. Model workflow progress belongs to task-specific summaries, not Current Status.'
  ),
  (
    'cfg_DASHRM012',
    'config',
    'STORAGE_CURRENT_SYSTEM_STATUS_PRODUCER_MODULE',
    'text',
    'trading_storage.dashboard_system_status',
    '/root/projects/trading-storage/src/trading_storage/dashboard_system_status.py',
    'current_system_status_summary_v1;trading-storage;dashboard_read_model;semantic_producer;infrastructure_status',
    'sync_artifact',
    'Storage-owned read-only semantic producer for current_system_status_summary_v1. It observes host/systemd/read-model freshness and performs no provider calls, manager dispatch, model activation, broker execution, account mutation, or storage writes unless explicitly refreshing the storage dashboard output.'
  ),
  (
    'scr_DASHRM006',
    'script',
    'STORAGE_CURRENT_SYSTEM_STATUS_REFRESH',
    'command',
    'PYTHONPATH=src python3 scripts/dashboard/refresh_current_system_status_read_model.py',
    '/root/projects/trading-storage/scripts/dashboard/refresh_current_system_status_read_model.py',
    'current_system_status_summary_v1;trading-storage;dashboard_read_model;refresh;infrastructure_status',
    'sync_artifact',
    'Refresh current_system_status_summary_v1 into the storage-owned dashboard read-model layout.'
  ),
  (
    'scr_DASHRM007',
    'script',
    'STORAGE_PUBLIC_DASHBOARD_READ_MODELS_REFRESH',
    'command',
    'PYTHONPATH=src python3 scripts/dashboard/refresh_public_dashboard_read_models.py',
    '/root/projects/trading-storage/scripts/dashboard/refresh_public_dashboard_read_models.py',
    'trading-storage;dashboard_read_model;refresh_batch;current_system_status_summary_v1;historical_task_progress_summary_v1',
    'sync_artifact',
    'Refresh the public dashboard read-model set served to trading-dashboard: current infrastructure status plus historical task progress.'
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

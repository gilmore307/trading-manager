-- Register the storage-owned dashboard read-model refresh entrypoint and templates.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_DASHRM003',
    'script',
    'STORAGE_HISTORICAL_TASK_PROGRESS_READ_MODEL_REFRESH',
    'command',
    'PYTHONPATH=src python3 scripts/dashboard/refresh_historical_task_progress_read_model.py --trading-manager-root /root/projects/trading-manager --storage-root storage',
    '/root/projects/trading-storage/scripts/dashboard/refresh_historical_task_progress_read_model.py',
    'historical_task_progress_summary_v1;dashboard_read_model;trading-storage;refresh;materialization;trading-manager_producer',
    'sync_artifact',
    'Run the manager-owned historical_task_progress_summary_v1 semantic producer and materialize the validated dashboard read model under trading-storage storage/dashboard. Performs no provider calls, model activation, broker execution, or account mutation.'
  ),
  (
    'cfg_DASHRM005',
    'config',
    'STORAGE_DASHBOARD_READ_MODEL_REFRESH_MODULE',
    'text',
    'trading_storage.dashboard_refresh',
    '/root/projects/trading-storage/src/trading_storage/dashboard_refresh.py',
    'dashboard_read_model;trading-storage;refresh_orchestration;semantic_producer_bridge;storage_materialization',
    'sync_artifact',
    'Storage-side refresh orchestration module that runs accepted semantic producers and materializes validated dashboard read-model outputs.'
  ),
  (
    'tpl_DASHRM001',
    'template',
    'STORAGE_DASHBOARD_READ_MODEL_REFRESH_SYSTEMD_SERVICE',
    'text',
    'trading-storage-dashboard-read-model-refresh.service',
    '/root/projects/trading-storage/deploy/systemd/trading-storage-dashboard-read-model-refresh.service',
    'dashboard_read_model;trading-storage;systemd;service;periodic_refresh_template',
    'sync_artifact',
    'Reviewed systemd oneshot service template for storage-owned dashboard read-model refresh. Checked in only; installing or enabling remains operator-controlled.'
  ),
  (
    'tpl_DASHRM002',
    'template',
    'STORAGE_DASHBOARD_READ_MODEL_REFRESH_SYSTEMD_TIMER',
    'text',
    'trading-storage-dashboard-read-model-refresh.timer',
    '/root/projects/trading-storage/deploy/systemd/trading-storage-dashboard-read-model-refresh.timer',
    'dashboard_read_model;trading-storage;systemd;timer;periodic_refresh_template',
    'sync_artifact',
    'Reviewed systemd timer template for periodic storage-owned dashboard read-model refresh. Checked in only; installing or enabling remains operator-controlled.'
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

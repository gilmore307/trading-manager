-- Register the manager-owned historical task progress dashboard summary producer.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_DASHRM002',
    'script',
    'MANAGER_HISTORICAL_TASK_PROGRESS_SUMMARY_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/build_historical_task_progress_summary.py',
    '/root/projects/trading-manager/scripts/tasks/build_historical_task_progress_summary.py',
    'historical_task_progress_summary_v1;dashboard_read_model;trading-manager;historical_scheduler;owner_facing_summary',
    'sync_artifact',
    'Build the owner-facing historical_task_progress_summary_v1 dashboard payload from read-only scheduler/status evidence. Storage materialization remains trading-storage responsibility; this command performs no provider calls, model activation, broker execution, account mutation, or storage layout writes.'
  ),
  (
    'cfg_DASHRM004',
    'config',
    'MANAGER_HISTORICAL_TASK_PROGRESS_SUMMARY_MODULE',
    'text',
    'trading_manager_tasks.dashboard_read_models',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_read_models.py',
    'historical_task_progress_summary_v1;dashboard_read_model;trading-manager;semantic_summary_producer',
    'sync_artifact',
    'Manager-owned implementation module for dashboard semantic summary producers. The first accepted producer converts historical scheduler/status evidence into historical_task_progress_summary_v1 payloads.'
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

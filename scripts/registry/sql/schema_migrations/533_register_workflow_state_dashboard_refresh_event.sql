-- Register workflow-state write events as the primary dashboard refresh trigger.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_SCHEDDRAIN004',
    'config',
    'TRADING_MANAGER_DASHBOARD_REFRESH_ON_WORKFLOW_STATE_WRITE',
    'text',
    'true',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env;/root/projects/trading-manager/src/trading_manager_tasks/dashboard_refresh_events.py',
    'historical_scheduler;dashboard_read_model_refresh;workflow_state_write_event;websocket_updates',
    'sync_artifact',
    'Enables event-triggered dashboard read-model refresh whenever the manager writes workflow-state progress, including stage-start transitions. The periodic storage timer remains a fallback route.'
  ),
  (
    'cfg_SCHEDDRAIN005',
    'config',
    'TRADING_MANAGER_DASHBOARD_REFRESH_NO_BLOCK',
    'text',
    'true',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env;/root/projects/trading-manager/src/trading_manager_tasks/dashboard_refresh_events.py',
    'historical_scheduler;dashboard_read_model_refresh;workflow_state_write_event;systemd_no_block',
    'sync_artifact',
    'Starts the storage-owned dashboard refresh service with systemctl --no-block for workflow-state write events so progress updates do not wait on read-model materialization.'
  ),
  (
    'cfg_SCHEDDRAIN006',
    'config',
    'TRADING_MANAGER_DASHBOARD_REFRESH_TRIGGER_TIMEOUT_SECONDS',
    'text',
    '5',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env;/root/projects/trading-manager/src/trading_manager_tasks/dashboard_refresh_events.py',
    'historical_scheduler;dashboard_read_model_refresh;workflow_state_write_event;timeout',
    'sync_artifact',
    'Maximum seconds the scheduler waits for the dashboard refresh trigger command itself; read-model materialization is delegated to the storage service.'
  ),
  (
    'cfg_SCHEDDRAIN007',
    'config',
    'TRADING_MANAGER_DASHBOARD_REFRESH_COMMAND',
    'text',
    'optional command override',
    '/root/projects/trading-manager/src/trading_manager_tasks/dashboard_refresh_events.py',
    'historical_scheduler;dashboard_read_model_refresh;workflow_state_write_event;test_override',
    'sync_artifact',
    'Optional command override for tests or non-systemd deployments; when unset, manager starts TRADING_MANAGER_DASHBOARD_REFRESH_SERVICE_UNIT.'
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
SET note = 'Progress-event hook where manager workflow-state writes start the storage-owned dashboard read-model refresh service; scheduler-decision refresh and the storage timer remain fallback/calibration routes.',
    updated_at = NOW()
WHERE key = 'SCHEDULER_EVENT_DASHBOARD_REFRESH';

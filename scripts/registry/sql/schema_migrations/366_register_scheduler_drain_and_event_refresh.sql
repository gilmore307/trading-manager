-- Register historical scheduler drain mode and event-driven dashboard refresh terms.
-- The manager daemon owns scheduling decisions; trading-storage remains the dashboard read-model materializer.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_SCHEDDRAIN001',
    'term',
    'SCHEDULER_DRAIN_READY_STAGES',
    'text',
    'scheduler_drain_ready_stages',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md',
    'historical_scheduler;safe_task_drain;daemon_runtime',
    'sync_artifact',
    'Hybrid event-driven daemon mode: after a safe scheduler-owned task completes, immediately evaluate and run the next runnable safe task until blocked or drain limits are reached.'
  ),
  (
    'term_SCHEDDRAIN002',
    'term',
    'SCHEDULER_EVENT_DASHBOARD_REFRESH',
    'text',
    'scheduler_event_dashboard_refresh',
    'trading-manager/docs/81_decision.md;trading-manager/docs/98_automation_scheduler.md;trading-storage/docs/96_dashboard_read_models.md',
    'historical_scheduler;dashboard_read_model_refresh;websocket_updates',
    'sync_artifact',
    'Progress-event hook where the manager daemon starts the storage-owned dashboard read-model refresh service after executed scheduler decisions.'
  ),
  (
    'cfg_SCHEDDRAIN001',
    'config',
    'TRADING_MANAGER_DRAIN_MAX_STEPS',
    'text',
    '50',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env',
    'historical_scheduler;safe_task_drain;daemon_runtime',
    'sync_artifact',
    'Maximum scheduler decisions admitted back-to-back in one drain cycle before the daemon returns to its idle/backstop interval.'
  ),
  (
    'cfg_SCHEDDRAIN002',
    'config',
    'TRADING_MANAGER_DRAIN_MAX_SECONDS',
    'text',
    '300',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env',
    'historical_scheduler;safe_task_drain;daemon_runtime',
    'sync_artifact',
    'Maximum wall-clock seconds for one safe-task drain cycle before the daemon returns to its idle/backstop interval.'
  ),
  (
    'cfg_SCHEDDRAIN003',
    'config',
    'TRADING_MANAGER_DASHBOARD_REFRESH_SERVICE_UNIT',
    'text',
    'trading-storage-dashboard-read-model-refresh.service',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service;trading-manager/deploy/systemd/trading-manager-historical-scheduler.env',
    'historical_scheduler;dashboard_read_model_refresh;storage_service',
    'sync_artifact',
    'Storage-owned systemd oneshot service unit started by the manager daemon after progress events to refresh dashboard read models.'
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

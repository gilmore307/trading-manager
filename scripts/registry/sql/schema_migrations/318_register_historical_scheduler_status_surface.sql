-- Register historical scheduler status/readiness surface.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_MHSS001',
    'term',
    'MANAGER_HISTORICAL_SCHEDULER_STATUS',
    'text',
    'manager_historical_scheduler_status_v1',
    'trading-manager/src/trading_manager_tasks/scheduler_status.py',
    'trading-manager;scheduler;historical_training;daemon;observability;manager_scheduler_daemon_state_v1;manager_scheduler_decision_v1',
    'sync_artifact',
    'Read-only service status contract for the historical scheduler runtime. It reports service readiness, selected month/stage, lock state, latest decision, provider gate posture, failure evidence, gated mutation boundaries, and the next operator action without mutating runtime state.'
  ),
  (
    'scr_MHSS001',
    'script',
    'MANAGER_HISTORICAL_SCHEDULER_STATUS_INSPECT',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/inspect_historical_scheduler_status.py',
    'trading-manager/scripts/tasks/inspect_historical_scheduler_status.py',
    'trading-manager;scheduler;historical_training;daemon;observability;manager_historical_scheduler_status_v1',
    'sync_artifact',
    'Inspects historical scheduler service status without provider calls, model activation, broker execution, storage lifecycle mutation, or workflow advancement.'
  ),
  (
    'cfg_MHSS001',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_REQUIRED_SERVICE_FLAGS',
    'text',
    '--execute-safe-preparation;--execute-safe-offline-stages;--auto-select-next-work;--advance-month-on-complete',
    'trading-manager/src/trading_manager_tasks/scheduler_status.py',
    'trading-manager;scheduler;historical_training;daemon;systemd;observability;manager_historical_scheduler_status_v1',
    'sync_artifact',
    'Required reviewed daemon flags for service-owned historical operation. The status surface reports missing flags before host activation or restart.'
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

-- Register system-service ownership and chronological month cursor for historical modeling runtime.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_HMSR001',
    'term',
    'HISTORICAL_MODELING_SYSTEM_SERVICE_RUNTIME',
    'text',
    'manager_historical_modeling_system_service_runtime',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'historical_backfill;model_training_workflow;automation_scheduler;systemd;manager_scheduler_daemon_state_v1',
    'sync_artifact',
    'Historical data/modeling workflow is owned by a resident system service. Chat/manual CLI runs are fallback inspection, repair, smoke-test, or emergency-intervention tools, not the normal operating path.'
  ),
  (
    'cfg_MASR002',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_SERVICE_ENV',
    'text',
    'TRADING_MANAGER_HISTORICAL_START_MONTH;TRADING_MANAGER_HISTORICAL_END_MONTH;TRADING_MANAGER_HISTORICAL_INTERVAL_SECONDS',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.env',
    'trading-manager;scheduler;historical_training;daemon;systemd;service_env',
    'sync_artifact',
    'Reviewed environment override template for the historical scheduler systemd service. Defaults preserve chronological-forward monthly operation and can be overridden by host operators after review.'
  ),
  (
    'cfg_MASR003',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_MONTH_CURSOR',
    'text',
    'advance_month_on_complete',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py',
    'trading-manager;scheduler;historical_training;daemon;chronological_forward;manager_scheduler_daemon_state_v1',
    'sync_artifact',
    'Daemon option that advances the current YYYY-MM cursor after terminal workflow completion, preserving old-to-new historical backfill without manual script chaining.'
  ),
  (
    'scr_MASD001',
    'script',
    'MANAGER_AUTOMATION_SCHEDULER_DAEMON_RUN',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py --execute-safe-preparation --execute-safe-offline-stages --advance-month-on-complete',
    'trading-manager/scripts/tasks/run_automation_scheduler_daemon.py',
    'trading-manager;scheduler;historical_training;daemon;manager_scheduler_daemon_state_v1;manager_scheduler_decision_v1;chronological_month_advance',
    'sync_artifact',
    'Runs the persistent system-service-owned historical modeling scheduler daemon. The daemon loops over capacity-aware scheduler ticks, persists resume state, writes decision JSONL, enforces a single-instance lock, executes safe/offline stages, advances the chronological month cursor after completion, and preserves provider/model/broker/storage gates.'
  ),
  (
    'scr_MASV001',
    'script',
    'MANAGER_HISTORICAL_SCHEDULER_SYSTEMD_SERVICE_TEMPLATE',
    'text',
    'deploy/systemd/trading-manager-historical-scheduler.service',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service',
    'trading-manager;scheduler;historical_training;daemon;systemd;boot_autostart;chronological_month_advance',
    'sync_artifact',
    'Reviewed systemd template for host-level boot autostart and Restart=always supervision of the historical modeling scheduler daemon. The template enables safe preparation, safe offline stages, and automatic chronological month advancement; committing it does not install or enable the host service.'
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

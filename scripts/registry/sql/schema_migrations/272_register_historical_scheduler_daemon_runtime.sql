-- Register persistent historical-training scheduler daemon runtime.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_MASD001',
    'script',
    'MANAGER_AUTOMATION_SCHEDULER_DAEMON_RUN',
    'text',
    'PYTHONPATH=src python3 scripts/tasks/run_automation_scheduler_daemon.py',
    'trading-manager/scripts/tasks/run_automation_scheduler_daemon.py',
    'trading-manager;scheduler;historical_training;daemon;manager_scheduler_daemon_state_v1;manager_scheduler_decision_v1',
    'sync_artifact',
    'Runs the persistent historical-training scheduler daemon. The daemon loops over capacity-aware scheduler ticks, persists resume state, writes decision JSONL, enforces a single-instance lock, and preserves provider/model/broker gates.'
  ),
  (
    'art_MSDS001',
    'artifact_type',
    'MANAGER_SCHEDULER_DAEMON_STATE_V1',
    'text',
    'manager_scheduler_daemon_state_v1',
    'trading-manager/src/trading_manager_tasks/scheduler_daemon.py',
    'trading-manager;scheduler;historical_training;daemon;checkpoint;resume',
    'sync_artifact',
    'Checkpoint artifact for the resident historical-training scheduler daemon: records tick counters, last decision status/reason, next internal stage, last error, month scope, and resume support.'
  ),
  (
    'scr_MASV001',
    'script',
    'MANAGER_HISTORICAL_SCHEDULER_SYSTEMD_SERVICE_TEMPLATE',
    'text',
    'deploy/systemd/trading-manager-historical-scheduler.service',
    'trading-manager/deploy/systemd/trading-manager-historical-scheduler.service',
    'trading-manager;scheduler;historical_training;daemon;systemd;boot_autostart',
    'sync_artifact',
    'Reviewed systemd template for optional host-level boot autostart and Restart=always supervision of the historical-training scheduler daemon. Committing the template does not install or enable it.'
  ),
  (
    'cfg_MASR001',
    'config',
    'MANAGER_HISTORICAL_SCHEDULER_RUNTIME_FILES',
    'text',
    'state=storage/runtime/historical_scheduler_state.json;lock=storage/runtime/historical_scheduler.lock;decision_log=storage/runtime/historical_scheduler_decisions.jsonl',
    'trading-manager/docs/99_historical_scheduler_runtime.md',
    'trading-manager;scheduler;historical_training;daemon;runtime_files',
    'sync_artifact',
    'Default ignored runtime-file layout for the resident historical scheduler: checkpoint state, single-instance lock, and append-only decision JSONL log.'
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

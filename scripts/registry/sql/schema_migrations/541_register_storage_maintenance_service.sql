-- Register storage-owned scheduled maintenance service and runner.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_STORMAINT001',
    'artifact_type',
    'STORAGE_SCHEDULED_MAINTENANCE_SUMMARY',
    'text',
    'storage_scheduled_maintenance_summary',
    'trading-storage/src/trading_storage/storage_maintenance.py;trading-storage/scripts/lifecycle/run_storage_maintenance.py',
    'trading-storage;storage_lifecycle;scheduled_maintenance;local_retention;log_cleanup',
    'sync_artifact',
    'Storage-owned scheduled maintenance summary. Current phase reports local runtime retention, including timed log archive/delete behavior, while fold SQL backup execution remains not_configured until a reviewed storage executor consumes manager fold-backup plans.'
  ),
  (
    'scr_STORMAINT001',
    'script',
    'STORAGE_SCHEDULED_MAINTENANCE_RUN',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/run_storage_maintenance.py --root . --apply-local-retention',
    '/root/projects/trading-storage/scripts/lifecycle/run_storage_maintenance.py;/root/projects/trading-storage/src/trading_storage/storage_maintenance.py',
    'storage_scheduled_maintenance_summary;storage_lifecycle;local_retention;log_cleanup;plan_receipt',
    'sync_artifact',
    'Runs the storage-owned scheduled maintenance wrapper. The current reviewed phase applies local retention for storage/tmp, storage/cache, storage/staging, storage/logs, storage/runs, storage/outputs, and legacy local runtime roots; it performs no provider calls, model activation, broker execution, or account mutation.'
  ),
  (
    'cfg_STORMAINT001',
    'config',
    'STORAGE_MAINTENANCE_SYSTEMD_SERVICE',
    'text',
    'trading-storage-maintenance.service;trading-storage-maintenance.timer',
    '/root/projects/trading-storage/deploy/systemd/trading-storage-maintenance.service;/root/projects/trading-storage/deploy/systemd/trading-storage-maintenance.timer',
    'trading-storage;systemd;scheduled_maintenance;storage_lifecycle;log_cleanup;fold_sql_backup_future_phase',
    'sync_artifact',
    'Reviewed host service/timer templates for storage-owned scheduled maintenance. Host enablement is an operator deployment action. Backup and deletion phases belong here rather than in manager/model/data ad hoc timers.'
  ),
  (
    'cfg_STORMAINT002',
    'config',
    'STORAGE_MAINTENANCE_BACKUP_DELETE_BOUNDARY_POLICY',
    'text',
    'manager_plans_and_requests;storage_executes_backup_archive_delete;one_service_boundary;logs_included_in_scheduled_cleanup;fold_sql_backup_phase_pending',
    'trading-storage/docs/05_decision.md;trading-storage/docs/04_task.md;trading-storage/deploy/systemd/trading-storage-maintenance.service',
    'trading-storage;trading-manager;fold_cleanup;logical_backup;storage_lifecycle;scheduled_maintenance',
    'sync_artifact',
    'Backup and deletion actions are storage-owned scheduled maintenance phases. Manager emits plans/requests and observes receipts; storage executes physical backup/archive/delete work, including timed logs cleanup, through the maintenance service boundary.'
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

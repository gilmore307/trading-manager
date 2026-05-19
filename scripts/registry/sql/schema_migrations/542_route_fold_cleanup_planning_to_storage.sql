-- Route fold backup/cleanup planning out of manager and into storage maintenance.

DELETE FROM trading_registry
WHERE key IN (
  'MANAGER_FOLD_CLEANUP_PLAN',
  'MANAGER_FOLD_SQL_LOGICAL_BACKUP_PLAN',
  'MANAGER_FOLD_CLEANUP_LOGICAL_BACKUP_POLICY',
  'MANAGER_PLAN_FOLD_CLEANUP'
);

UPDATE trading_registry
SET payload = 'manager_exposes_fold_progress_state;storage_monitors_completed_folds;storage_executes_backup_archive_delete;one_service_boundary;logs_included_in_scheduled_cleanup',
    note = 'Backup and deletion actions are storage-owned scheduled maintenance phases. Manager exposes fold progress state only; storage monitors completed folds and executes physical backup/archive/delete work, including timed logs cleanup, through the maintenance service boundary.',
    updated_at = NOW()
WHERE key = 'STORAGE_MAINTENANCE_BACKUP_DELETE_BOUNDARY_POLICY';

UPDATE trading_registry
SET note = 'Storage-owned scheduled maintenance summary. Current phase reports local runtime retention and monitors manager fold-state files for completed model-worker folds. Completed folds become storage-owned SQL backup candidates; no manager-authored backup/cleanup plan is required.',
    updated_at = NOW()
WHERE key = 'STORAGE_SCHEDULED_MAINTENANCE_SUMMARY';

UPDATE trading_registry
SET payload = 'PYTHONPATH=src python3 scripts/lifecycle/run_storage_maintenance.py --root . --manager-root /root/projects/trading-manager --apply-local-retention',
    note = 'Runs the storage-owned scheduled maintenance wrapper. The current reviewed phase applies local retention for storage-owned runtime roots and monitors manager fold-state files for completed folds that should enter storage-owned SQL backup/lifecycle handling.',
    updated_at = NOW()
WHERE key = 'STORAGE_SCHEDULED_MAINTENANCE_RUN';

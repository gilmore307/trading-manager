-- Clarify that storage reads fold state directly; manager does not signal cleanup.

UPDATE trading_registry
SET payload = 'storage_reads_manager_fold_state;storage_monitors_completed_folds;storage_executes_backup_archive_delete;one_service_boundary;logs_included_in_scheduled_cleanup;no_manager_signal_or_request',
    note = 'Backup and deletion actions are storage-owned scheduled maintenance phases. Manager writes ordinary fold progress runtime state as part of scheduler operation; storage reads those state files directly and executes physical backup/archive/delete work, including timed logs cleanup, through the maintenance service boundary. No manager backup/cleanup signal, request, or plan is required.',
    updated_at = NOW()
WHERE key = 'STORAGE_MAINTENANCE_BACKUP_DELETE_BOUNDARY_POLICY';

UPDATE trading_registry
SET note = 'Storage-owned scheduled maintenance summary. Current phase reports local runtime retention and reads manager fold-state files directly for completed model-worker folds. Completed folds become storage-owned SQL backup candidates; no manager-authored backup/cleanup signal, request, or plan is required.',
    updated_at = NOW()
WHERE key = 'STORAGE_SCHEDULED_MAINTENANCE_SUMMARY';

UPDATE trading_registry
SET note = 'Runs the storage-owned scheduled maintenance wrapper. The current reviewed phase applies local retention for storage-owned runtime roots and reads manager fold-state files directly for completed folds that should enter storage-owned SQL backup/lifecycle handling.',
    updated_at = NOW()
WHERE key = 'STORAGE_SCHEDULED_MAINTENANCE_RUN';

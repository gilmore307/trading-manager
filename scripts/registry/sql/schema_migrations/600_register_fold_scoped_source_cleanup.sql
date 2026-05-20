-- Register fold-scoped source cleanup lifecycle terms.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_STORFOLD001',
    'artifact_type',
    'STORAGE_FOLD_SOURCE_CLEANUP_CANDIDATE',
    'text',
    'storage_fold_source_cleanup_candidate',
    'trading-storage/src/trading_storage/storage_maintenance.py;trading-storage/docs/20_storage_lifecycle_policy.md',
    'trading-storage;storage_lifecycle;scheduled_maintenance;fold_scoped_source_data;source_cleanup_candidate',
    'sync_artifact',
    'Storage-owned candidate emitted for storage/01_source_data/fold_scoped/<fold_id>/ folders after the corresponding ten-layer model-worker fold is complete. It is planning evidence only and performs no deletion; artifact-index coverage, protected-set clearance, quarantine/recheck, and deletion receipt evidence remain required.'
  ),
  (
    'term_STORFOLD001',
    'term',
    'FOLD_SCOPED_SOURCE_DATA_ROOT',
    'text',
    'storage/01_source_data/fold_scoped/<fold_id>/',
    'trading-storage/docs/20_storage_lifecycle_policy.md;trading-storage/docs/02_architecture.md',
    'trading-storage;storage_lifecycle;source_data;fold_scoped_source_data;target_symbol_source_data',
    'sync_artifact',
    'Accepted storage root pattern for target-specific or experiment-specific source data that is scoped to one model-worker fold. Reusable Layer 1/2 source foundations must not be placed under this root for deletion planning.'
  ),
  (
    'term_STORFOLD002',
    'term',
    'FOLD_COMPLETE_DELETE_ALLOWED_RETENTION_CLASS',
    'text',
    'fold_complete_delete_allowed',
    'trading-storage/src/trading_storage/lifecycle_planner.py;trading-storage/docs/30_artifact_index.md',
    'trading-storage;storage_lifecycle;retention_class;fold_scoped_source_data;quarantine_candidate',
    'sync_artifact',
    'Retention class for explicitly fold-scoped target/source artifacts that may become quarantine candidates only after full Layer 1-10 fold completion and protected-set clearance. It must not be used for reusable Layer 1/2 source foundations.'
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
SET note = 'Storage-owned scheduled maintenance summary. Current phase inventories all numbered storage roots, reports local runtime retention, and reads manager fold-state files directly for completed ten-layer model-worker folds. Completed folds become storage-owned SQL backup candidates; explicitly fold-scoped source folders under storage/01_source_data/fold_scoped/<fold_id>/ become cleanup candidates only after fold completion. No manager-authored backup/cleanup signal, request, or plan is required.',
    applies_to = 'trading-storage;storage_lifecycle;scheduled_maintenance;ordered_storage_roots;local_retention;log_cleanup;fold_sql_backup_candidate;fold_source_cleanup_candidate',
    updated_at = now()
WHERE id = 'art_STORMAINT001';

UPDATE trading_registry
SET note = 'Runs the storage-owned scheduled maintenance wrapper. The reviewed phase inventories storage/01_source_data through storage/90_lifecycle, applies local retention for storage-owned runtime roots, reads manager fold-state files directly for completed ten-layer folds, emits SQL backup candidates, and reports fold-scoped source cleanup candidates without performing deletion.',
    applies_to = 'storage_scheduled_maintenance_summary;storage_root_inventory_summary;storage_fold_source_cleanup_candidate;storage_lifecycle;ordered_storage_roots;local_retention;log_cleanup;plan_receipt',
    updated_at = now()
WHERE id = 'scr_STORMAINT001';

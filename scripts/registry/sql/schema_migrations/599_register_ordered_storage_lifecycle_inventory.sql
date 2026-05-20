-- Register ordered storage root inventory in scheduled lifecycle maintenance.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_STORINV001',
    'artifact_type',
    'STORAGE_ROOT_INVENTORY_SUMMARY',
    'text',
    'storage_root_inventory_summary',
    'trading-storage/src/trading_storage/storage_maintenance.py;trading-storage/scripts/lifecycle/run_storage_maintenance.py',
    'trading-storage;storage_lifecycle;scheduled_maintenance;ordered_storage_roots;storage_root_inventory',
    'sync_artifact',
    'Storage-owned summary of the numbered storage root inventory emitted by scheduled maintenance. It reports root existence, file counts, directory counts, byte counts, lifecycle role, and managed root ids for storage/01_source_data through storage/90_lifecycle without hashing payloads or authorizing lifecycle mutation.'
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
SET note = 'Storage-owned scheduled maintenance summary. Current phase inventories all numbered storage roots, reports local runtime retention, and reads manager fold-state files directly for completed ten-layer model-worker folds. Completed folds become storage-owned SQL backup candidates; no manager-authored backup/cleanup signal, request, or plan is required.',
    applies_to = 'trading-storage;storage_lifecycle;scheduled_maintenance;ordered_storage_roots;local_retention;log_cleanup;fold_sql_backup_candidate',
    updated_at = now()
WHERE id = 'art_STORMAINT001';

UPDATE trading_registry
SET note = 'Runs the storage-owned scheduled maintenance wrapper. The reviewed phase inventories storage/01_source_data through storage/90_lifecycle, applies local retention for storage-owned runtime roots, and reads manager fold-state files directly for completed ten-layer folds that should enter storage-owned SQL backup/lifecycle handling.',
    applies_to = 'storage_scheduled_maintenance_summary;storage_root_inventory_summary;storage_lifecycle;ordered_storage_roots;local_retention;log_cleanup;plan_receipt',
    updated_at = now()
WHERE id = 'scr_STORMAINT001';

UPDATE trading_registry
SET note = 'Build a conservative filesystem artifact-index inventory for storage-owned artifacts. Default scan covers storage/01_source_data, storage/02_control_plane, storage/03_model_artifacts, storage/04_execution_artifacts, storage/05_benchmark_datasets, and storage/06_dashboard_cache/read_models. The command mutates no indexed payloads and does not authorize production deletion, archive, SQL detach/drop, model activation, broker execution, or account mutation.',
    updated_at = now()
WHERE id = 'scr_SLC009';

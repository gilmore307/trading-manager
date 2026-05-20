-- Register lifecycle transient runtime evidence guard.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_STORLIFE005',
    'config',
    'STORAGE_LIFECYCLE_TRANSIENT_EVIDENCE_GUARD',
    'text',
    'runs_outputs_staging_are_transient;receipts_tombstones_plans_protected_sets_quarantine_recheck_are_canonical_evidence;retain_until_extracted',
    'trading-storage/src/trading_storage/lifecycle.py;trading-storage/docs/20_storage_lifecycle_policy.md;trading-storage/docs/05_decision.md',
    'trading-storage;storage_lifecycle;90_lifecycle;runs;outputs;staging;receipts;tombstones;protected_set;quarantine_recheck',
    'sync_artifact',
    'storage/90_lifecycle/runs, outputs, and staging are transient runtime folders. Ordinary files may roll off by TTL, but evidence-shaped receipts, manifests, tombstones, protected-set outputs, lifecycle plans, artifact indexes, and quarantine/recheck records must be retained until extracted to canonical lifecycle evidence directories.'
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
SET note = 'Storage-owned lifecycle policy. Manager may request or observe lifecycle work, but storage owns compression, archive, protected-set checks, deletion, restore, receipts, tombstones, and transient-run evidence guards.',
    updated_at = NOW()
WHERE id = 'cfg_SLC001';

UPDATE trading_registry
SET note = 'Runs the storage-owned scheduled maintenance wrapper. The reviewed phase inventories storage/01_source_data through storage/90_lifecycle, applies local retention for storage-owned runtime roots with transient lifecycle evidence guards, reads manager fold-state files directly for completed ten-layer folds, emits SQL backup candidates, and reports fold-scoped source cleanup candidates without performing deletion.',
    applies_to = 'storage_scheduled_maintenance_summary;storage_root_inventory_summary;storage_fold_source_cleanup_candidate;storage_lifecycle;ordered_storage_roots;local_retention;log_cleanup;transient_lifecycle_evidence_guard;plan_receipt',
    updated_at = NOW()
WHERE id = 'scr_STORMAINT001';

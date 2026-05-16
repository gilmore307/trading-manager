-- Register the storage-owned dashboard snapshot metadata pruning entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SDB004',
    'script',
    'STORAGE_DASHBOARD_SNAPSHOT_PRUNE',
    'command',
    'PYTHONPATH=src python3 scripts/dashboard/prune_dashboard_snapshots.py',
    '/root/projects/trading-storage/scripts/dashboard/prune_dashboard_snapshots.py',
    'dashboard_snapshot_prune_plan_v1;dashboard_snapshot_prune_receipt_v1;dashboard_snapshot_prune_summary_v1;dashboard_read_model_snapshot_metadata;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Plans or applies bounded deletion of old storage/dashboard/read_models/*/snapshots/**/*.json dashboard metadata snapshots. Default is dry-run; --apply deletes eligible snapshot files only. It preserves latest.json, schemas, dashboard index rows, Layer 1/2 persistent data, SQL data, model bodies, receipts, and manifests.'
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

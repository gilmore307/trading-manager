-- Register count-based dashboard snapshot retention.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_DASHRM015',
    'config',
    'DASHBOARD_SNAPSHOT_COUNT_RETENTION',
    'text',
    'keep_latest_10_snapshots_per_contract;count_based_default;optional_age_grace_only',
    'trading-storage/src/trading_storage/dashboard_snapshot_lifecycle.py;trading-storage/docs/40_dashboard_read_models.md;trading-storage/docs/41_dashboard_summary_layout.md',
    'trading-storage;trading-dashboard;dashboard_read_model;dashboard_snapshot_prune;storage_lifecycle;06_dashboard_cache',
    'sync_artifact',
    'Dashboard read-model snapshots under storage/06_dashboard_cache/read_models/<contract_type>/snapshots are metadata cache, not canonical evidence. The default retention plan keeps the latest 10 snapshots per contract and marks older snapshots as delete candidates; optional age grace is for short debugging windows only.'
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
SET note = 'Plans or applies bounded deletion of storage/06_dashboard_cache/read_models/*/snapshots/**/*.json dashboard metadata snapshots outside the latest-10-per-contract hot window. Default is dry-run; --apply deletes eligible snapshot files only and requires a reviewed approval reference. It preserves latest.json, schemas, dashboard index rows, Layer 1/2 persistent data, SQL data, model bodies, receipts, and manifests.',
    applies_to = 'dashboard_snapshot_prune_plan;dashboard_snapshot_prune_receipt;dashboard_snapshot_prune_summary;dashboard_read_model_snapshot_metadata;storage_lifecycle;trading-storage;count_based_retention',
    updated_at = NOW()
WHERE id = 'scr_SDB004';

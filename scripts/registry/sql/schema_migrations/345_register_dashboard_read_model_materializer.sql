-- Register the storage-side dashboard read-model materialization helper.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_DASHRM001',
    'script',
    'STORAGE_DASHBOARD_READ_MODEL_MATERIALIZE',
    'command',
    'PYTHONPATH=src python3 scripts/dashboard/materialize_read_model.py',
    '/root/projects/trading-storage/scripts/dashboard/materialize_read_model.py',
    'dashboard_read_model;trading-storage;storage/dashboard;latest_snapshot;schema_validation;dashboard_read_model_index',
    'sync_artifact',
    'Validate one producer-supplied dashboard read-model JSON envelope and materialize storage-owned snapshot/latest/schema/index files. This helper does not create semantic summaries, refresh jobs, dashboard UI, provider calls, model activation, broker execution, or account mutation.'
  ),
  (
    'cfg_DASHRM003',
    'config',
    'STORAGE_DASHBOARD_READ_MODEL_MATERIALIZER_MODULE',
    'text',
    'trading_storage.dashboard_read_models',
    '/root/projects/trading-storage/src/trading_storage/dashboard_read_models.py',
    'dashboard_read_model;trading-storage;validation;materialization;storage_layout',
    'sync_artifact',
    'Storage-side implementation module for dashboard read-model common-envelope validation, snapshot/latest/schema/index writes, checksum/byte-count index rows, and secret-like payload rejection.'
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

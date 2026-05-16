-- Register the storage-owned artifact-index builder entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC009',
    'script',
    'STORAGE_ARTIFACT_INDEX_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/build_artifact_index.py',
    '/root/projects/trading-storage/scripts/lifecycle/build_artifact_index.py',
    'storage_artifact_index_summary_v1;artifact_index;trading-storage;storage_lifecycle;protected_set_preparation',
    'sync_artifact',
    'Build a conservative filesystem artifact-index inventory for storage-owned artifacts. Default scan is bounded to storage/artifacts; callers may add explicit bounded include roots. The command mutates no indexed payloads and does not authorize production deletion, archive, SQL detach/drop, model activation, broker execution, or account mutation.'
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

-- Register the storage-owned protected-set builder entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC010',
    'script',
    'STORAGE_PROTECTED_SET_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/build_protected_set.py',
    '/root/projects/trading-storage/scripts/lifecycle/build_protected_set.py',
    'storage_protected_set_v1;storage_protected_set_summary_v1;protected_set;trading-storage;storage_lifecycle',
    'sync_artifact',
    'Build conservative protected-set safety evidence from storage artifact-index records plus optional protected reason refs, manual pins, and mutation candidates. The command mutates no indexed payloads and does not authorize production deletion, archive, SQL detach/drop, model activation, broker execution, or account mutation.'
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

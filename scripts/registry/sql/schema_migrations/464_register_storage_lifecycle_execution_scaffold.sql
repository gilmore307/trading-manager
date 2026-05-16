-- Register the storage-owned non-mutating lifecycle execution scaffold entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC013',
    'script',
    'STORAGE_LIFECYCLE_EXECUTION_SCAFFOLD_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/build_lifecycle_execution_scaffold.py',
    '/root/projects/trading-storage/scripts/lifecycle/build_lifecycle_execution_scaffold.py',
    'storage_lifecycle_execution_scaffold_v1;storage_lifecycle_execution_scaffold_summary_v1;compression_manifest_draft_v1;compression_receipt_draft_v1;sql_archive_manifest_draft_v1;archive_receipt_draft_v1;restore_receipt_draft_v1;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Build non-mutating compression/archive/restore manifest and receipt drafts from a dry-run storage lifecycle plan. The command records planned-not-executed compression, archive, and restore evidence only; it performs no compression, archive export, restore materialization, artifact-index mutation, lifecycle mutation, quarantine move, deletion, SQL detach/drop, model activation, broker execution, or account mutation.'
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

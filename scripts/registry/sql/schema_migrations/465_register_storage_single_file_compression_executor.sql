-- Register the storage-owned narrow single-file compression executor entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC014',
    'script',
    'STORAGE_SINGLE_FILE_COMPRESSION_EXECUTE',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/compress_single_file_candidates.py',
    '/root/projects/trading-storage/scripts/lifecycle/compress_single_file_candidates.py',
    'storage_single_file_compression_result_v1;storage_single_file_compression_summary_v1;compression_manifest_v1;compression_receipt_v1;restore_receipt_v1;compress_candidate;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Safely compress unprotected single-file storage lifecycle compress_candidate rows to zstd compressed copies under storage/archive/compressed. Default mode is dry-run; --apply writes compressed copies only, preserves originals, verifies decompression checksum smoke, and emits compression/restore receipts. The command performs no original deletion, artifact-index mutation, quarantine move, SQL archive/export, SQL detach/drop, model activation, broker execution, or account mutation.'
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

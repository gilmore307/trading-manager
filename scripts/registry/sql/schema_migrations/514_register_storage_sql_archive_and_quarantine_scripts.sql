-- Register storage lifecycle script entrypoints for reviewed SQL archive, restore verification,
-- and no-mutation quarantine/delete gate receipts.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC016',
    'script',
    'STORAGE_SQL_ARCHIVE_EXECUTE',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/execute_sql_archive.py',
    '/root/projects/trading-storage/scripts/lifecycle/execute_sql_archive.py;/root/projects/trading-storage/src/trading_storage/sql_archive.py',
    'storage_sql_archive_result_v1;storage_sql_archive_summary_v1;sql_archive_manifest_v1;archive_receipt_v1;restore_receipt_v1;archive_candidate;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Plan or execute reviewed file-backed SQL archive gzip copies for unprotected archive_candidate lifecycle rows. Default mode is dry-run; --apply-reviewed-archive writes archive copies only from already-materialized export files, preserves sources, verifies archive restore checksums, and performs no database connection, SQL detach/drop, source deletion, artifact-index mutation, quarantine move, model activation, broker execution, or account mutation.'
  ),
  (
    'scr_SLC017',
    'script',
    'STORAGE_SQL_ARCHIVE_RESTORE_VERIFY',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/verify_sql_archive_restore.py',
    '/root/projects/trading-storage/scripts/lifecycle/verify_sql_archive_restore.py;/root/projects/trading-storage/src/trading_storage/sql_archive.py',
    'storage_sql_archive_restore_verification_v1;storage_sql_archive_restore_verification_summary_v1;restore_receipt_v1;sql_archive_manifest_v1;archive_receipt_v1;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Verify reviewed file-backed SQL archive gzip copies by decompression and checksum comparison. The verifier is verification-only and performs no materialized database restore, SQL attach/detach/drop, payload mutation, model activation, broker execution, or account mutation.'
  ),
  (
    'scr_SLC018',
    'script',
    'STORAGE_QUARANTINE_DELETE_RESULT_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/build_quarantine_delete_result.py',
    '/root/projects/trading-storage/scripts/lifecycle/build_quarantine_delete_result.py;/root/projects/trading-storage/src/trading_storage/quarantine_delete_executor.py',
    'storage_quarantine_delete_result_v1;storage_quarantine_delete_summary_v1;quarantine_receipt_draft_v1;deletion_receipt_draft_v1;artifact_tombstone_draft_v1;storage_quarantine_recheck_evidence_v1;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Build no-mutation quarantine/delete gate receipts from quarantine/recheck evidence. Gate-clear records remain planned_not_executed; the command performs no physical quarantine move, deletion, artifact-index mutation, SQL detach/drop, model activation, broker execution, or account mutation.'
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

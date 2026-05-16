-- Register one-pass safe storage file lifecycle closeout helper.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'scr_SLC015',
  'script',
  'STORAGE_FILE_LIFECYCLE_CLOSEOUT_RUN',
  'command',
  'PYTHONPATH=src python3 scripts/lifecycle/run_file_lifecycle_closeout.py',
  '/root/projects/trading-storage/scripts/lifecycle/run_file_lifecycle_closeout.py;/root/projects/trading-storage/src/trading_storage/file_lifecycle_closeout.py',
  'storage_file_lifecycle_closeout_v1;storage_file_lifecycle_closeout_summary_v1;storage_artifact_index_v1;storage_protected_set_v1;storage_lifecycle_plan_v1;storage_quarantine_recheck_evidence_v1;storage_lifecycle_execution_scaffold_v1;storage_single_file_compression_result_v1;dashboard_snapshot_prune_plan_v1',
  'sync_artifact',
  'Runs the complete safe file-lifecycle pass: artifact index, protected set, dry-run lifecycle plan, quarantine/recheck evidence, execution scaffold, optional compressed-copy creation for unprotected compress_candidate files, and dashboard snapshot prune dry-run. It preserves originals and performs no artifact-index mutation, quarantine move, SQL mutation, model activation, broker execution, account mutation, or dashboard snapshot deletion unless a later explicitly approved apply flag is used.'
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

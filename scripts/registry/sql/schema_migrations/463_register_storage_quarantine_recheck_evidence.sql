-- Register the storage-owned dry-run quarantine/recheck evidence entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC012',
    'script',
    'STORAGE_QUARANTINE_RECHECK_EVIDENCE_BUILD',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/build_quarantine_recheck_evidence.py',
    '/root/projects/trading-storage/scripts/lifecycle/build_quarantine_recheck_evidence.py',
    'storage_quarantine_recheck_evidence_v1;storage_quarantine_recheck_summary_v1;storage_lifecycle_plan_v1;protected_set;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Build report-only quarantine/recheck evidence from a dry-run storage lifecycle plan and optional final protected-set evidence. The command records quarantine candidate, initial protection, and final recheck status only; it performs no lifecycle mutation, quarantine move, deletion, archive, SQL detach/drop, model activation, broker execution, or account mutation, and it never authorizes deletion.'
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

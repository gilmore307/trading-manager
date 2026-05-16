-- Register the storage-owned dry-run lifecycle planner entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_SLC011',
    'script',
    'STORAGE_LIFECYCLE_PLAN_DRY_RUN',
    'command',
    'PYTHONPATH=src python3 scripts/lifecycle/plan_storage_lifecycle.py',
    '/root/projects/trading-storage/scripts/lifecycle/plan_storage_lifecycle.py',
    'storage_lifecycle_plan_v1;storage_lifecycle_plan_summary_v1;artifact_index;protected_set;storage_lifecycle;trading-storage',
    'sync_artifact',
    'Build a dry-run durable-artifact lifecycle plan from storage artifact-index metadata, protected-set evidence, and reviewed policy rules. The command emits retain/compress/quarantine/archive candidate recommendations only; it performs no lifecycle mutation, deletion, archive, SQL detach/drop, model activation, broker execution, or account mutation.'
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

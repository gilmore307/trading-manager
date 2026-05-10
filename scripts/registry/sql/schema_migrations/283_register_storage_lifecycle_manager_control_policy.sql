-- Clarify that storage lifecycle maintenance is manager-visible through the unified task system.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_SLC008',
    'config',
    'STORAGE_LIFECYCLE_MANAGER_CONTROL_POLICY',
    'text',
    'manager_unified_request_task_summary_surface;storage_lifecycle_request_v1;manager_prioritizes_schedules_observes;trading_storage_protected_set_physical_execution',
    'trading-manager/docs/80_task.md',
    'trading-manager;trading-storage;storage_lifecycle;manager_request_v1;task_summary;storage_lifecycle_request_v1',
    'sync_artifact',
    'Storage lifecycle maintenance enters normal operation through manager unified requests/task summary. Manager requests, prioritizes, schedules, and observes; trading-storage owns protected-set checks and physical lifecycle execution.'
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

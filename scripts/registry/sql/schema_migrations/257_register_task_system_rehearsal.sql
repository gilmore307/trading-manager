-- Register deterministic manager task-system rehearsal entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MTS001',
    'artifact_type',
    'MANAGER_TASK_SYSTEM_REHEARSAL_V1',
    'text',
    'manager_task_system_rehearsal_v1',
    'trading-manager/docs/95_task_system.md',
    'task_system;manager_request_v1;run_manifest_v1;artifact_ref_v1;ready_signal_v1;task_summary;rehearsal',
    'sync_artifact',
    'Deterministic in-memory rehearsal artifact for exercising manager request, component completion receipt, run manifest, artifact ref, ready signal, and task-summary-like rows before SQL writes or live component dispatch.'
  ),
  (
    'scr_MTS004',
    'script',
    'MANAGER_TASK_SYSTEM_REHEARSAL',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/rehearse_task_system.py',
    '/root/projects/trading-manager/scripts/tasks/rehearse_task_system.py',
    'task_system;manager_request_v1;component_completion_receipt;run_manifest_v1;artifact_ref_v1;ready_signal_v1;task_summary;rehearsal',
    'sync_artifact',
    'Run a deterministic in-memory manager task-system rehearsal without provider calls or SQL writes. Default mixed scenario emits ready, partial, and failed task paths.'
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

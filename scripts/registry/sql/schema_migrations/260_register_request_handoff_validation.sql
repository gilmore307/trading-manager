-- Register manager request handoff validation entrypoint.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'scr_MTS006',
    'script',
    'MANAGER_REQUEST_HANDOFF_VALIDATE',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/validate_request_handoff.py',
    '/root/projects/trading-manager/scripts/tasks/validate_request_handoff.py',
    'task_system;manager_request_v1;input_binding_v1;parameter_ref;request_payload;component_handoff;dry_run_validation',
    'sync_artifact',
    'Validate materialized manager request payloads against component build_context handoff paths without dispatching work, calling providers, or writing completion receipts.'
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

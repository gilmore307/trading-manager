-- Register manager request payload materialization entrypoint and schema ref.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MTS002',
    'artifact_type',
    'MANAGER_REQUEST_PARAMETER_PAYLOAD_V1',
    'text',
    'manager_request_parameter_payload_v1',
    'trading-manager/docs/95_task_system.md',
    'task_system;manager_request_v1;input_binding_v1;parameter_ref;request_payload;monthly_backfill',
    'sync_artifact',
    'Component-readable request parameter payload stored behind manager_request.parameter_ref and recorded through request-scoped input_binding_v1 metadata; payload bodies remain out of manager SQL.'
  ),
  (
    'scr_MTS005',
    'script',
    'MANAGER_REQUEST_PAYLOAD_MATERIALIZE',
    'command',
    'PYTHONPATH=src python3 scripts/tasks/materialize_request_payloads.py',
    '/root/projects/trading-manager/scripts/tasks/materialize_request_payloads.py',
    'task_system;manager_request_v1;input_binding_v1;parameter_ref;request_payload;monthly_backfill',
    'sync_artifact',
    'Materialize manager request parameter payloads under storage://trading-manager/... locators and optionally persist input_binding_v1 rows for SQL-backed request handoff preparation.'
  ),
  (
    'cfg_MTS006',
    'config',
    'MANAGER_REQUEST_PAYLOAD_STORAGE_ROOT',
    'text',
    'storage',
    'trading-manager/docs/95_task_system.md',
    'task_system;parameter_ref;local_development_storage;request_payload',
    'sync_artifact',
    'Default local development root for materializing storage://trading-manager/... parameter payloads. Local fixture payloads are not production storage and must not be treated as production-ready artifacts.'
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

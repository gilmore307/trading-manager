-- Restore component output artifact registration and ensure request payload uses its own id.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'art_MTS002',
    'artifact_type',
    'COMPONENT_OUTPUT_ARTIFACT',
    'text',
    'component_output',
    'trading-manager/docs/95_task_system.md',
    'artifact_ref_v1;component_output_ref_v1;task_system;all_components',
    'registry_only',
    'Generic artifact type for output refs listed by a component completion receipt when the component does not provide a narrower registered artifact kind.'
  ),
  (
    'art_MTS003',
    'artifact_type',
    'MANAGER_REQUEST_PARAMETER_PAYLOAD_V1',
    'text',
    'manager_request_parameter_payload_v1',
    'trading-manager/docs/95_task_system.md',
    'task_system;manager_request_v1;input_binding_v1;parameter_ref;request_payload;monthly_backfill',
    'sync_artifact',
    'Component-readable request parameter payload stored behind manager_request.parameter_ref and recorded through request-scoped input_binding_v1 metadata; payload bodies remain out of manager SQL.'
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

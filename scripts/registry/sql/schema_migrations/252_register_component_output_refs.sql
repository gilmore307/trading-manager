-- Register generic component output references emitted by task-system receipt normalization.

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
    'mft_MTS002',
    'manifest_type',
    'COMPONENT_OUTPUT_REF_V1',
    'text',
    'component_output_ref_v1',
    'trading-manager/docs/95_task_system.md',
    'artifact_ref_v1;component_output;task_system;all_components',
    'registry_only',
    'Generic schema reference for concise component output refs normalized from completion receipts. Payload bytes and component-specific schemas remain outside manager SQL.'
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

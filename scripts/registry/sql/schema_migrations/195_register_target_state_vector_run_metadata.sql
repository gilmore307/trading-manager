-- Register additional top-level run and diagnostics metadata emitted by the current
-- TargetStateVector feature generator.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_TSV013',
    'field',
    'FEATURE_QUALITY_DIAGNOSTICS',
    'field_name',
    'feature_quality_diagnostics',
    NULL,
    'feature_03_target_state_vector;model_03_target_state_vector;target_state_vector_model',
    'registry_only',
    'Top-level TargetStateVector feature output block for coverage, context-availability, target-close/volume, spread, and other deterministic feature-quality diagnostics.'
  ),
  (
    'fld_TSV014',
    'field',
    'RUN_ID',
    'field_name',
    'run_id',
    NULL,
    'feature_03_target_state_vector;source_03_target_state',
    'registry_only',
    'Identifier for one invocation of a deterministic target-state feature generation run; source_run_ref remains the cross-surface evidence reference.'
  )
ON CONFLICT (id) DO UPDATE SET
    kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = CURRENT_TIMESTAMP;

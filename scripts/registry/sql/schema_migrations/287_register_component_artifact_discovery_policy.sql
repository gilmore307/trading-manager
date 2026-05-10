-- Register component receipt artifact discovery policy.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_MGRART001',
    'config',
    'MANAGER_COMPONENT_ARTIFACT_DISCOVERY_POLICY',
    'text',
    'outputs_are_downstream_artifacts;steps_references_are_supporting_artifacts;repo_scoped_storage_uris;infer_kind_media_type_row_count;collapse_duplicate_references;no_provider_calls_no_stage_unlock',
    'trading-manager/docs/95_task_system.md',
    'component_completion_receipt_v1;artifact_ref_v1;ready_signal_v1;manager_stage_coverage_v1',
    'sync_artifact',
    'Manager discovers artifact refs from component receipt outputs and step references. It records concise output/supporting artifact metadata without copying payloads; duplicate refs are collapsed; discovered artifacts do not imply additional provider calls or full stage coverage.'
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

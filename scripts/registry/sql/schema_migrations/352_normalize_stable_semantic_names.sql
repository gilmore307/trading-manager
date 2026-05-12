-- Normalize active registry semantic names so stable contract/business identifiers do not carry version suffixes.
-- Versions belong in schema metadata (for example schema_version/schema_ref), while registry row ids remain stable.

UPDATE trading_registry
SET key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_ARTIFACT',
    updated_at = NOW()
WHERE key = 'MANAGER_MODEL_TRAINING_WORKFLOW_PLAN_V1';

UPDATE trading_registry
SET key = 'MANAGER_TASK_SYSTEM_REHEARSAL_ARTIFACT',
    updated_at = NOW()
WHERE key = 'MANAGER_TASK_SYSTEM_REHEARSAL_V1';

UPDATE trading_registry
SET
  key = regexp_replace(regexp_replace(key, '_V1_', '_', 'g'), '_V1\M', '', 'g'),
  payload = regexp_replace(regexp_replace(payload, '_v1_', '_', 'g'), '_v1\M', '', 'g'),
  applies_to = regexp_replace(regexp_replace(applies_to, '_v1_', '_', 'g'), '_v1\M', '', 'g'),
  note = regexp_replace(regexp_replace(note, '_v1_', '_', 'g'), '_v1\M', '', 'g'),
  updated_at = NOW()
WHERE key ~ '_V1(\M|_)'
   OR payload ~ '_v1(\M|_)'
   OR applies_to ~ '_v1(\M|_)'
   OR note ~ '_v1(\M|_)';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES (
  'cfg_NAMING001',
  'config',
  'STABLE_SEMANTIC_CONTRACT_NAMING_POLICY',
  'text',
  'semantic_contract_names_are_stable_unversioned;schema_versions_live_in_schema_metadata;legacy_v1_names_are_read_compatibility_aliases_only;active_code_must_not_emit_v1_business_names',
  '/root/projects/trading-manager/docs/93_contracts.md',
  'trading-manager;trading-storage;trading-dashboard;trading-data;trading-model;trading-execution;contract_type;schema_ref;registry_naming',
  'sync_artifact',
  'Stable business/contract identifiers must not embed version suffixes such as _v1. Use stable semantic names in code and registry payloads; put version facts in schema_version/schema_ref or migration history. Existing _v1 artifacts may be accepted only as legacy read-compatibility aliases during migration.'
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

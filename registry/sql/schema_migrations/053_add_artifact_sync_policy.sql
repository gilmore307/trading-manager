-- Add artifact sync policy to each registry row and register policy values.
-- Target engine: PostgreSQL.

ALTER TABLE trading_registry
ADD COLUMN IF NOT EXISTS artifact_sync_policy TEXT NOT NULL DEFAULT 'registry_only';

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_artifact_sync_policy_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_artifact_sync_policy_check
CHECK (artifact_sync_policy IN (
  'registry_only',
  'sync_artifact',
  'review_on_merge'
));

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'output',
  'repo',
  'config',
  'term',
  'data_bundle',
  'data_kind',
  'script',
  'payload_format',
  'artifact_sync_policy',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type',
  'task_lifecycle_state',
  'review_readiness',
  'acceptance_outcome',
  'test_status',
  'maintenance_status',
  'docs_status'
));

-- Backfill current rows. Do this before replacing the updated_at trigger so the
-- first policy classification does not churn every existing row timestamp.
UPDATE trading_registry
SET artifact_sync_policy = 'sync_artifact'
WHERE kind = 'field';

UPDATE trading_registry
SET artifact_sync_policy = 'sync_artifact'
WHERE kind IN ('data_bundle', 'data_kind', 'script')
  AND COALESCE(BTRIM(path), '') <> '';

UPDATE trading_registry
SET artifact_sync_policy = 'sync_artifact'
WHERE kind IN ('payload_format', 'artifact_sync_policy');

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('asp_R4K8M2QJ', 'artifact_sync_policy', 'ARTIFACT_SYNC_POLICY_REGISTRY_ONLY', 'status_value', 'registry_only', NULL, 'trading_registry.artifact_sync_policy', 'sync_artifact', 'registry row edits normally do not require code/template/docs artifact follow-up when durable consumers use stable ids and no row is merged or deleted'),
  ('asp_Z7N3Q9TV', 'artifact_sync_policy', 'ARTIFACT_SYNC_POLICY_SYNC_ARTIFACT', 'status_value', 'sync_artifact', NULL, 'trading_registry.artifact_sync_policy', 'sync_artifact', 'registry row edits must be followed by matching code/template/docs artifact updates before acceptance'),
  ('asp_K2M8P5LD', 'artifact_sync_policy', 'ARTIFACT_SYNC_POLICY_REVIEW_ON_MERGE', 'status_value', 'review_on_merge', NULL, 'trading_registry.artifact_sync_policy', 'sync_artifact', 'registry row edits may be registry-only for simple label changes but require downstream review when merged, deleted, or semantically repurposed'),
  ('fld_R9K2H7AP', 'field', 'REGISTRY_ITEM_ARTIFACT_SYNC_POLICY', 'field_name', 'artifact_sync_policy', NULL, 'trading_registry', 'sync_artifact', 'canonical column name for trading_registry.artifact_sync_policy')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.path, NEW.applies_to, NEW.artifact_sync_policy, NEW.note)
     IS DISTINCT FROM
     ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.path, OLD.applies_to, OLD.artifact_sync_policy, OLD.note) THEN
    NEW.updated_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

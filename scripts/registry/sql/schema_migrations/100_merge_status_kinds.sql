-- Merge status-like registry kinds into one status_value kind.
-- The status slot/domain remains visible in applies_to; the kind only says that
-- the row registers an allowed status/policy value.

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

UPDATE trading_registry
SET applies_to = kind
WHERE kind IN (
  'task_lifecycle_state',
  'review_readiness',
  'acceptance_outcome',
  'test_status',
  'maintenance_status',
  'docs_status'
)
AND (applies_to IS NULL OR BTRIM(applies_to) = '');

UPDATE trading_registry
SET kind = 'status_value'
WHERE kind IN (
  'task_lifecycle_state',
  'review_readiness',
  'acceptance_outcome',
  'test_status',
  'maintenance_status',
  'docs_status',
  'artifact_sync_policy'
);

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'field',
  'repo',
  'config',
  'term',
  'data_bundle',
  'data_source',
  'source_capability',
  'data_kind',
  'template',
  'shared_artifact',
  'script',
  'payload_format',
  'status_value',
  'artifact_type',
  'manifest_type',
  'ready_signal_type',
  'request_type'
));

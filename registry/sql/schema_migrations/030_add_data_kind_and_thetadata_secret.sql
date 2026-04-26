-- Add data_kind registry kind and register ThetaData source-secret alias.
-- Target engine: PostgreSQL.

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

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('cfg_VS66QD19', 'config', 'THETADATA_SECRET_ALIAS', 'secret_alias', 'thetadata', '/root/secrets/thetadata.json', 'trading-data', 'source-level secret JSON alias for ThetaData credentials and subscription label; JSON keys include username, password, and subscription; secret values are stored outside Git')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

UPDATE trading_registry
SET note = 'approved provider terminology; source-level secret alias THETADATA_SECRET_ALIAS points to local credential JSON outside Git; ThetaTerminal JAR/runtime placement remains deferred until connector design'
WHERE key = 'THETADATA';

-- Current trading registry table definition.
-- Target engine: PostgreSQL.

CREATE TABLE IF NOT EXISTS trading_registry (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  key TEXT NOT NULL UNIQUE,
  payload_format TEXT NOT NULL,
  payload TEXT NOT NULL,
  path TEXT,
  applies_to TEXT,
  artifact_sync_policy TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_kind_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_kind_check
CHECK (kind IN (
  'artifact_type',
  'classification_field',
  'config',
  'data_feature',
  'data_feed',
  'data_kind',
  'data_source',
  'feed_capability',
  'field',
  'identity_field',
  'manifest_type',
  'parameter_field',
  'path_field',
  'payload_format',
  'provider',
  'ready_signal_type',
  'repo',
  'request_type',
  'script',
  'shared_artifact',
  'state_vector_value',
  'status_value',
  'systemd_unit',
  'temporal_field',
  'term',
  'text_field'
));

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_payload_format_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_payload_format_check
CHECK (payload_format IN (
  'boolean',
  'command',
  'decimal',
  'field_name',
  'file',
  'integer',
  'ipv4_address',
  'iso_date',
  'iso_datetime',
  'iso_duration',
  'iso_time',
  'json',
  'python_symbol',
  'repo_name',
  'secret_alias',
  'status_value',
  'text',
  'timezone'
));

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_artifact_sync_policy_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_artifact_sync_policy_check
CHECK (
  artifact_sync_policy IS NULL
  OR artifact_sync_policy IN (
    'registry_only',
    'review_on_merge',
    'sync_artifact'
  )
);

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_field_applies_to_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_field_applies_to_check
CHECK (kind <> 'field' OR (applies_to IS NOT NULL AND BTRIM(applies_to) <> ''));

CREATE INDEX IF NOT EXISTS idx_trading_registry_kind
ON trading_registry(kind);

CREATE INDEX IF NOT EXISTS idx_trading_registry_updated_at
ON trading_registry(updated_at);

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(
       NEW.kind,
       NEW.key,
       NEW.payload_format,
       NEW.payload,
       NEW.path,
       NEW.applies_to,
       NEW.artifact_sync_policy,
       NEW.note
     )
     IS DISTINCT FROM
     ROW(
       OLD.kind,
       OLD.key,
       OLD.payload_format,
       OLD.payload,
       OLD.path,
       OLD.applies_to,
       OLD.artifact_sync_policy,
       OLD.note
     ) THEN
    NEW.updated_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_trading_registry_updated_at ON trading_registry;
CREATE TRIGGER trg_trading_registry_updated_at
BEFORE UPDATE ON trading_registry
FOR EACH ROW
EXECUTE FUNCTION set_trading_registry_updated_at();

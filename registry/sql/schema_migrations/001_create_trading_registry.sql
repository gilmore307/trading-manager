-- Create the active trading registry and migration ledger.
-- Target engine: PostgreSQL.

CREATE TABLE IF NOT EXISTS trading_registry_schema_migrations (
  version TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  checksum_sha256 TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading_registry (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN (
    'field',
    'output',
    'repo',
    'config',
    'term',
    'script',
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
  )),
  key TEXT NOT NULL UNIQUE,
  payload_format TEXT NOT NULL CHECK (payload_format IN ('text', 'file')),
  payload TEXT NOT NULL,
  path TEXT,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trading_registry_kind
ON trading_registry(kind);

CREATE INDEX IF NOT EXISTS idx_trading_registry_updated_at
ON trading_registry(updated_at);

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.path, NEW.note)
     IS DISTINCT FROM
     ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.path, OLD.note) THEN
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

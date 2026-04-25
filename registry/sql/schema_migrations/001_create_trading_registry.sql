-- Create the long-lived trading-main registry active register and migration ledger.
-- Target engine: PostgreSQL.

CREATE TABLE IF NOT EXISTS trading_registry_schema_migrations (
  version TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  checksum_sha256 TEXT NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading_registry (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('field', 'output', 'repo', 'path', 'config', 'term', 'script', 'artifact_type', 'manifest_type', 'ready_signal_type', 'request_type', 'task_lifecycle_state', 'review_readiness', 'acceptance_outcome', 'test_status', 'maintenance_status', 'docs_status')),
  key TEXT NOT NULL UNIQUE,
  payload_format TEXT NOT NULL CHECK (payload_format IN ('text', 'file')),
  payload TEXT NOT NULL,
  note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trading_registry_kind
ON trading_registry(kind);

CREATE INDEX IF NOT EXISTS idx_trading_registry_updated_at
ON trading_registry(updated_at);

CREATE TABLE IF NOT EXISTS trading_registry_revisions (
  revision_id BIGSERIAL PRIMARY KEY,
  item_id TEXT NOT NULL,
  operation TEXT NOT NULL CHECK (operation IN ('insert', 'update')),
  kind TEXT NOT NULL,
  key TEXT NOT NULL,
  payload_format TEXT NOT NULL,
  payload TEXT NOT NULL,
  note TEXT,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_trading_registry_revisions_item_id
ON trading_registry_revisions(item_id);

CREATE INDEX IF NOT EXISTS idx_trading_registry_revisions_recorded_at
ON trading_registry_revisions(recorded_at);

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.note)
     IS DISTINCT FROM
     ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.note) THEN
    NEW.updated_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION record_trading_registry_revision()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO trading_registry_revisions (item_id, operation, kind, key, payload_format, payload, note)
    VALUES (NEW.id, 'insert', NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.note);
    RETURN NEW;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.note)
       IS DISTINCT FROM
       ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.note) THEN
      INSERT INTO trading_registry_revisions (item_id, operation, kind, key, payload_format, payload, note)
      VALUES (NEW.id, 'update', NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.note);
    END IF;
    RETURN NEW;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_trading_registry_updated_at ON trading_registry;
CREATE TRIGGER trg_trading_registry_updated_at
BEFORE UPDATE ON trading_registry
FOR EACH ROW
EXECUTE FUNCTION set_trading_registry_updated_at();

DROP TRIGGER IF EXISTS trg_trading_registry_revision ON trading_registry;
CREATE TRIGGER trg_trading_registry_revision
AFTER INSERT OR UPDATE ON trading_registry
FOR EACH ROW
EXECUTE FUNCTION record_trading_registry_revision();

INSERT INTO trading_registry_revisions (item_id, operation, kind, key, payload_format, payload, note)
SELECT id, 'insert', kind, key, payload_format, payload, note
FROM trading_registry item
WHERE NOT EXISTS (
  SELECT 1
  FROM trading_registry_revisions revision
  WHERE revision.item_id = item.id
);

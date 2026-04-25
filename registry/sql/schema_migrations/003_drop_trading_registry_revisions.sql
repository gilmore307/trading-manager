-- Remove full-row revision snapshots to keep the active database storage-efficient.
-- Target engine: PostgreSQL.

DROP TRIGGER IF EXISTS trg_trading_registry_revision ON trading_registry;
DROP FUNCTION IF EXISTS record_trading_registry_revision();
DROP TABLE IF EXISTS trading_registry_revisions;

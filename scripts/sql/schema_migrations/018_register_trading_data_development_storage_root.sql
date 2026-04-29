-- Register the development-stage local storage root for trading-data outputs.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('cfg_MGFGHOVH', 'config', 'TRADING_DATA_DEVELOPMENT_STORAGE_ROOT', 'file', 'data/storage', '/root/projects/trading-data/data/storage', 'trading-data', 'development-stage local file output root for trading-data task outputs and receipts; ignored by Git except documentation files; use instead of SQL until storage contracts are accepted')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

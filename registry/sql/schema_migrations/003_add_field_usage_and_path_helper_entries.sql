-- Add field usage metadata and register id-first path helper methods.
-- Target engine: PostgreSQL.

ALTER TABLE trading_registry
ADD COLUMN IF NOT EXISTS applies_to TEXT;

CREATE OR REPLACE FUNCTION set_trading_registry_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  IF ROW(NEW.kind, NEW.key, NEW.payload_format, NEW.payload, NEW.path, NEW.applies_to, NEW.note)
     IS DISTINCT FROM
     ROW(OLD.kind, OLD.key, OLD.payload_format, OLD.payload, OLD.path, OLD.applies_to, OLD.note) THEN
    NEW.updated_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_K8P3M6QA', 'field', 'REGISTRY_ITEM_APPLIES_TO', 'text', 'applies_to', NULL, 'trading_registry', 'canonical column name for trading_registry.applies_to'),
  ('scr_P9H4K2XM', 'script', 'GET_ITEM_PATH_BY_ID_HELPER', 'text', 'getItemPathById', '/root/projects/trading-main/helpers/registry/registry-reader.js', NULL, 'id-based optional path helper; returns path or null'),
  ('scr_D7Q6M1RA', 'script', 'REQUIRE_ITEM_PATH_BY_ID_HELPER', 'text', 'requireItemPathById', '/root/projects/trading-main/helpers/registry/registry-reader.js', NULL, 'id-based required path helper; returns path or throws'),
  ('scr_L3V8N5TK', 'script', 'GET_ITEM_PATH_BY_KEY_UNSAFE_HELPER', 'text', 'getItemPathByKeyUnsafe', '/root/projects/trading-main/helpers/registry/registry-reader.js', NULL, 'key-based optional path helper for human/debug use; key is renameable'),
  ('scr_W2C9F7QP', 'script', 'REQUIRE_ITEM_PATH_BY_KEY_UNSAFE_HELPER', 'text', 'requireItemPathByKeyUnsafe', '/root/projects/trading-main/helpers/registry/registry-reader.js', NULL, 'key-based required path helper for human/debug use; key is renameable')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

UPDATE trading_registry
SET applies_to = 'trading_registry'
WHERE kind = 'field'
  AND key IN (
    'REGISTRY_ITEM_ID',
    'REGISTRY_ITEM_KIND',
    'REGISTRY_ITEM_KEY',
    'REGISTRY_ITEM_PAYLOAD_FORMAT',
    'REGISTRY_ITEM_PAYLOAD',
    'REGISTRY_ITEM_PATH',
    'REGISTRY_ITEM_NOTE',
    'REGISTRY_ITEM_CREATED_AT',
    'REGISTRY_ITEM_UPDATED_AT'
  );

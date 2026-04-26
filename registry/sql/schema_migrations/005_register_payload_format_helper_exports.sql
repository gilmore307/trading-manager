-- Register Python helper exports for registry payload_format validation.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('scr_FMT2L9QA', 'script', 'REGISTRY_PAYLOAD_FORMATS_CONSTANT', 'python_symbol', 'PAYLOAD_FORMATS', '/root/projects/trading-main/helpers/trading_registry/payload_formats.py', 'trading_registry.payload_format', 'official Python helper export listing accepted registry payload_format values'),
  ('scr_FMV4K7RN', 'script', 'REGISTRY_IS_PAYLOAD_FORMAT_HELPER', 'python_symbol', 'is_payload_format', '/root/projects/trading-main/helpers/trading_registry/payload_formats.py', 'trading_registry.payload_format', 'official Python helper that returns whether a value is an accepted registry payload_format'),
  ('scr_FMA8P3TZ', 'script', 'REGISTRY_ASSERT_PAYLOAD_FORMAT_HELPER', 'python_symbol', 'assert_payload_format', '/root/projects/trading-main/helpers/trading_registry/payload_formats.py', 'trading_registry.payload_format', 'official Python helper that returns a valid payload_format or raises ValueError')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

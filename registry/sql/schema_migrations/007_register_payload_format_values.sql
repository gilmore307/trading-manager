-- Register accepted trading_registry.payload_format values as first-class registry rows.
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
  ('plf_KZS4GHGK', 'payload_format', 'PAYLOAD_FORMAT_TEXT', 'text', 'text', NULL, 'trading_registry.payload_format', 'registered payload_format value for general text fallback when no narrower format applies'),
  ('plf_AW2KVDIF', 'payload_format', 'PAYLOAD_FORMAT_FILE', 'text', 'file', NULL, 'trading_registry.payload_format', 'registered payload_format value for file references stored in payload'),
  ('plf_CITUC2LR', 'payload_format', 'PAYLOAD_FORMAT_JSON', 'text', 'json', NULL, 'trading_registry.payload_format', 'registered payload_format value for JSON-encoded payload values'),
  ('plf_DLKTPVQW', 'payload_format', 'PAYLOAD_FORMAT_INTEGER', 'text', 'integer', NULL, 'trading_registry.payload_format', 'registered payload_format value for base-10 integer payload values encoded as text'),
  ('plf_TY63EANP', 'payload_format', 'PAYLOAD_FORMAT_DECIMAL', 'text', 'decimal', NULL, 'trading_registry.payload_format', 'registered payload_format value for decimal numeric payload values encoded as text'),
  ('plf_KTDMGHCN', 'payload_format', 'PAYLOAD_FORMAT_BOOLEAN', 'text', 'boolean', NULL, 'trading_registry.payload_format', 'registered payload_format value for boolean payload values encoded as true or false'),
  ('plf_TIZBJLD3', 'payload_format', 'PAYLOAD_FORMAT_ISO_DATE', 'text', 'iso_date', NULL, 'trading_registry.payload_format', 'registered payload_format value for ISO 8601 calendar dates'),
  ('plf_RKXXANMZ', 'payload_format', 'PAYLOAD_FORMAT_ISO_TIME', 'text', 'iso_time', NULL, 'trading_registry.payload_format', 'registered payload_format value for ISO 8601 time-of-day values'),
  ('plf_GS5ZANQM', 'payload_format', 'PAYLOAD_FORMAT_ISO_DATETIME', 'text', 'iso_datetime', NULL, 'trading_registry.payload_format', 'registered payload_format value for ISO 8601 date-time values'),
  ('plf_3GLJMFRO', 'payload_format', 'PAYLOAD_FORMAT_ISO_DURATION', 'text', 'iso_duration', NULL, 'trading_registry.payload_format', 'registered payload_format value for ISO 8601 duration values'),
  ('plf_IDTPAWNN', 'payload_format', 'PAYLOAD_FORMAT_TIMEZONE', 'text', 'timezone', NULL, 'trading_registry.payload_format', 'registered payload_format value for IANA timezone names'),
  ('plf_6DRICAYQ', 'payload_format', 'PAYLOAD_FORMAT_SECRET_ALIAS', 'text', 'secret_alias', NULL, 'trading_registry.payload_format', 'registered payload_format value for local secret alias references'),
  ('plf_S2WDROG7', 'payload_format', 'PAYLOAD_FORMAT_REPO_NAME', 'text', 'repo_name', NULL, 'trading_registry.payload_format', 'registered payload_format value for Git repository names'),
  ('plf_3FMXRPA6', 'payload_format', 'PAYLOAD_FORMAT_FIELD_NAME', 'text', 'field_name', NULL, 'trading_registry.payload_format', 'registered payload_format value for canonical field names'),
  ('plf_6FYQDFNX', 'payload_format', 'PAYLOAD_FORMAT_STATUS_VALUE', 'text', 'status_value', NULL, 'trading_registry.payload_format', 'registered payload_format value for registered status or outcome values'),
  ('plf_T4YVVZPG', 'payload_format', 'PAYLOAD_FORMAT_COMMAND', 'text', 'command', NULL, 'trading_registry.payload_format', 'registered payload_format value for command or command fragment payloads'),
  ('plf_SBKQNAFE', 'payload_format', 'PAYLOAD_FORMAT_PYTHON_SYMBOL', 'text', 'python_symbol', NULL, 'trading_registry.payload_format', 'registered payload_format value for Python import/member symbols')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

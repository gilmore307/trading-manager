-- Register OKX access config aliases and allowlist metadata.
-- Target engine: PostgreSQL.

ALTER TABLE trading_registry
DROP CONSTRAINT IF EXISTS trading_registry_payload_format_check;

ALTER TABLE trading_registry
ADD CONSTRAINT trading_registry_payload_format_check
CHECK (payload_format IN (
  'text',
  'file',
  'json',
  'integer',
  'decimal',
  'boolean',
  'iso_date',
  'iso_time',
  'iso_datetime',
  'iso_duration',
  'timezone',
  'secret_alias',
  'repo_name',
  'field_name',
  'status_value',
  'command',
  'python_symbol',
  'ipv4_address'
));

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('plf_WJUDWYRD', 'payload_format', 'PAYLOAD_FORMAT_IPV4_ADDRESS', 'text', 'ipv4_address', NULL, 'trading_registry.payload_format', 'registered payload_format value for IPv4 address strings'),
  ('trm_C4BJ2YGX', 'term', 'OKX', 'text', 'OKX cryptocurrency exchange/API provider used for crypto data acquisition and trading', NULL, NULL, 'approved provider terminology; credential secret values are stored outside Git under /root/secrets and registry rows store aliases only'),
  ('cfg_NSDZZFP4', 'config', 'OKX_API_KEY_SECRET_ALIAS', 'secret_alias', 'okx/api-key', NULL, 'trading-data;trading-execution', 'secret alias for the OKX API key; secret value is stored outside Git'),
  ('cfg_SXDY2Z26', 'config', 'OKX_SECRET_KEY_SECRET_ALIAS', 'secret_alias', 'okx/secret-key', NULL, 'trading-data;trading-execution', 'secret alias for the OKX API secret key; secret value is stored outside Git'),
  ('cfg_HJZRAW6I', 'config', 'OKX_PASSPHRASE_SECRET_ALIAS', 'secret_alias', 'okx/passphrase', NULL, 'trading-data;trading-execution', 'secret alias for the OKX API passphrase; secret value is stored outside Git'),
  ('cfg_Z6YFODUW', 'config', 'OKX_ALLOWED_IP_ADDRESS', 'ipv4_address', '66.206.20.138', NULL, 'trading-data;trading-execution', 'server public IPv4 address allowlisted for OKX API access'),
  ('cfg_UQMQLQNU', 'config', 'OKX_API_KEY_REMARK_NAME', 'text', 'OpenClaw', NULL, 'trading-data;trading-execution', 'OKX API key remark/name used for the allowlisted OpenClaw server credential')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

-- Move OKX API-key metadata into the source-level OKX JSON secret file contract.
-- Target engine: PostgreSQL.

DELETE FROM trading_registry
WHERE id IN (
  'cfg_Z6YFODUW',
  'cfg_UQMQLQNU'
);

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_PSQTACLK', 'field', 'SOURCE_SECRET_ALLOWED_IP_ADDRESS', 'field_name', 'allowed_ip_address', NULL, 'source_secret_json', 'canonical JSON key for source-level allowlisted IPv4 address metadata in /root/secrets/<source>.json files'),
  ('fld_U5J2VL7P', 'field', 'SOURCE_SECRET_API_KEY_REMARK_NAME', 'field_name', 'api_key_remark_name', NULL, 'source_secret_json', 'canonical JSON key for source-level API key remark/name metadata in /root/secrets/<source>.json files')
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
SET note = 'source-level secret JSON alias for OKX credentials and credential metadata; JSON keys include api_key, secret_key, passphrase, allowed_ip_address, and api_key_remark_name; secret values are stored outside Git'
WHERE id = 'cfg_GWAWFQJ2';

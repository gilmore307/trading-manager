-- Consolidate source credentials to one JSON secret file per source.
-- Target engine: PostgreSQL.

DELETE FROM trading_registry
WHERE id IN (
  'cfg_NSDZZFP4',
  'cfg_SXDY2Z26',
  'cfg_HJZRAW6I'
);

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_WMIVZRL2', 'term', 'GITHUB', 'text', 'GitHub code hosting and git remote provider used for repository operations', NULL, 'git_operations', 'approved provider terminology; credential secret values are stored outside Git under source-level JSON secret files'),
  ('cfg_GWAWFQJ2', 'config', 'OKX_SECRET_ALIAS', 'secret_alias', 'okx', '/root/secrets/okx.json', 'trading-data;trading-execution', 'source-level secret JSON alias for OKX credentials; JSON keys include api_key, secret_key, and passphrase; secret values are stored outside Git'),
  ('cfg_USHCPJT2', 'config', 'GITHUB_SECRET_ALIAS', 'secret_alias', 'github', '/root/secrets/github.json', 'git_operations', 'source-level secret JSON alias for GitHub credentials; JSON keys include pat; secret values are stored outside Git'),
  ('fld_FKGJNUCL', 'field', 'SOURCE_SECRET_API_KEY', 'field_name', 'api_key', NULL, 'source_secret_json', 'canonical JSON key for source-level API keys in /root/secrets/<source>.json files'),
  ('fld_S7A3SCF3', 'field', 'SOURCE_SECRET_SECRET_KEY', 'field_name', 'secret_key', NULL, 'source_secret_json', 'canonical JSON key for source-level secret keys in /root/secrets/<source>.json files'),
  ('fld_5HL6TP3V', 'field', 'SOURCE_SECRET_PASSPHRASE', 'field_name', 'passphrase', NULL, 'source_secret_json', 'canonical JSON key for source-level passphrases in /root/secrets/<source>.json files'),
  ('fld_K7M3G5VB', 'field', 'SOURCE_SECRET_PAT', 'field_name', 'pat', NULL, 'source_secret_json', 'canonical JSON key for source-level personal access tokens in /root/secrets/<source>.json files')
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
SET
  note = 'official Python runtime helper that resolves a source-level JSON secret alias by stable config id and returns either the raw JSON text or one named JSON field value',
  applies_to = 'helpers/trading_registry;source_secret_json'
WHERE id = 'scr_LS5Q2K7W';

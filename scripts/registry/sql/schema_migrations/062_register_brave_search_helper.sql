-- Register Brave Search helper and local secret alias.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_BRAVESEARCH', 'config', 'BRAVE_SEARCH_SECRET_ALIAS', 'secret_alias', 'brave', '/root/secrets/brave.json', 'trading-main;trading-data', 'registry_only', 'source-level secret JSON alias for Brave Search API access; JSON key api_key is stored outside Git'),
  ('out_BRAVESEARCHHELPER', 'output', 'BRAVE_SEARCH_HELPER', 'file', 'src/trading_web_search/brave.py', '/root/projects/trading-main/src/trading_web_search/brave.py', 'trading-main-helpers', 'sync_artifact', 'shared Python helper for code-level Brave Search API calls using BRAVE_SEARCH_SECRET_ALIAS via trading registry secret resolution')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;

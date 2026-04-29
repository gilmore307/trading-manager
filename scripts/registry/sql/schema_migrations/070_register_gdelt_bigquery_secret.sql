-- Register GDELT BigQuery service-account secret alias.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('cfg_GDELTBQ1', 'config', 'GDELT_BIGQUERY_SECRET_ALIAS', 'secret_alias', 'gdelt', '/root/secrets/gdelt.json', 'trading-main;trading-data', 'review_on_merge', 'source-level Google service-account JSON alias for GDELT BigQuery access; secret values live only under /root/secrets/gdelt.json'),
  ('trm_GDELT001', 'term', 'GDELT', 'text', 'The GDELT Project global news/event/knowledge-graph source for political, economic, technology, geopolitical, sector, and broad-market event discovery', 'https://www.gdeltproject.org/', 'trading-data;event_database', 'review_on_merge', 'primary global news/event source for non-SEC/non-company-disclosure event discovery; use source events as evidence feeding unified event clustering, not duplicate alpha rows')
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

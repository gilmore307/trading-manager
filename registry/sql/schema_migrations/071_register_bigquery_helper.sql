-- Register shared BigQuery REST helper.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('scr_BQHELPER1', 'script', 'BIGQUERY_REST_QUERY_HELPER', 'text', 'trading_bigquery.bigquery_query', '/root/projects/trading-main/src/trading_bigquery/client.py', 'trading-main;trading-data;gdelt_news', 'sync_artifact', 'official shared Python helper for dependency-light BigQuery Standard SQL queries using registry-backed service-account JSON secrets; intended first consumer is GDELT BigQuery acquisition')
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

-- Register SQL-shaped long-term CSV template fields and paths.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_MAC001', 'field', 'MACRO_METRIC', 'field_name', 'metric', 'trading-data/storage/templates/data_kinds/macro/macro_release.preview.csv', 'macro_release_template', 'sync_artifact', 'macro release metric name; one macro_release table stores multiple macro metrics, so metric remains a row field'),
  ('fld_MAC002', 'field', 'MACRO_RELEASE_TIME', 'field_name', 'release_time', 'trading-data/storage/templates/data_kinds/macro/macro_release.preview.csv', 'macro_release_template', 'sync_artifact', 'actual public release timestamp when the macro value becomes visible to model simulations'),
  ('fld_MAC003', 'field', 'MACRO_EFFECTIVE_UNTIL', 'field_name', 'effective_until', 'trading-data/storage/templates/data_kinds/macro/macro_release.preview.csv', 'macro_release_template', 'sync_artifact', 'exclusive timestamp for when the next release supersedes this macro value; null/blank means latest known value'),
  ('fld_MAC004', 'field', 'OBSERVED_VALUE', 'field_name', 'value', 'trading-data/storage/templates/data_kinds/macro/macro_release.preview.csv', 'macro_release_template', 'sync_artifact', 'generic numeric/text observed value field for SQL-shaped long-term storage templates'),
  ('dki_MACREL01', 'data_kind', 'MACRO_RELEASE', 'text', 'macro_release', 'trading-data/storage/templates/data_kinds/macro/macro_release.preview.csv', 'macro_data', 'sync_artifact', 'SQL-shaped long-term macro release row; stores metric, release_time, effective_until, and value, then training jobs materialize daily Parquet feature matrices')
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

UPDATE trading_registry
SET note = 'canonical data_kind discriminator for legacy/provider payloads; SQL-shaped per-table long-term CSV templates do not repeat this column when the table/file name already owns the data kind'
WHERE key = 'DATA_KIND';

UPDATE trading_registry
SET note = 'provider/source field for documentation or shared mixed-source payloads; SQL-shaped per-source long-term CSV templates do not repeat this column when source is fixed by table/folder contract'
WHERE key = 'SOURCE';

UPDATE trading_registry
SET path = 'trading-data/storage/templates/data_kinds/thetadata/option_activity_event_detail.preview.csv',
    note = 'SQL-shaped CSV detail row for one option_activity_event; wide/nested contexts are encoded as JSON text columns until the future SQL table is materialized'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT_DETAIL';

UPDATE trading_registry
SET path = 'trading-data/storage/templates/data_kinds/thetadata/option_chain_snapshot.preview.csv',
    note = 'SQL-shaped CSV option-chain snapshot row; visible contracts are encoded as JSON text in the contracts column until the future SQL table is materialized'
WHERE kind = 'data_kind'
  AND key = 'OPTION_CHAIN_SNAPSHOT';

UPDATE trading_registry
SET note = note || '; SQL-shaped CSV template omits data_kind/source columns because the table/file contract already owns them'
WHERE kind = 'data_kind'
  AND key IN ('EQUITY_BAR', 'EQUITY_LIQUIDITY_BAR', 'EQUITY_NEWS', 'CRYPTO_BAR', 'CRYPTO_LIQUIDITY_BAR', 'OPTION_ACTIVITY_EVENT', 'OPTION_BAR');

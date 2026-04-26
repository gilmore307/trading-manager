-- Register Alpaca source-level secret alias for stock/ETF data acquisition.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_EOC5GSA5', 'term', 'ALPACA', 'text', 'Alpaca brokerage and market-data API provider used for stock and ETF bars, quotes, trades, and news data acquisition', NULL, 'trading-data', 'approved provider terminology; credential secret values are stored outside Git under source-level JSON secret files'),
  ('cfg_SJZQAJ2W', 'config', 'ALPACA_SECRET_ALIAS', 'secret_alias', 'alpaca', '/root/secrets/alpaca.json', 'trading-data', 'source-level secret JSON alias for Alpaca credentials and endpoint; JSON keys include api_key, secret_key, and endpoint; secret values are stored outside Git'),
  ('fld_QUP7M43B', 'field', 'SOURCE_SECRET_ENDPOINT', 'field_name', 'endpoint', NULL, 'source_secret_json', 'canonical JSON key for source-level API endpoints in /root/secrets/<source>.json files')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

-- Register economic/macro data provider source-level secret aliases.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_JJH2NQ4J', 'term', 'FRED', 'text', 'Federal Reserve Economic Data API provider used for macroeconomic and market-context data acquisition', NULL, 'trading-data', 'approved provider terminology; credential secret values are stored outside Git under source-level JSON secret files'),
  ('trm_EBCO7NKH', 'term', 'CENSUS', 'text', 'US Census API provider used for demographic and economic data acquisition', NULL, 'trading-data', 'approved provider terminology; credential secret values are stored outside Git under source-level JSON secret files'),
  ('trm_QEOTBESR', 'term', 'BEA', 'text', 'US Bureau of Economic Analysis API provider used for economic accounts and macroeconomic data acquisition', NULL, 'trading-data', 'approved provider terminology; credential secret values are stored outside Git under source-level JSON secret files'),
  ('trm_ZJYP6B4O', 'term', 'BLS', 'text', 'US Bureau of Labor Statistics API provider used for labor and economic data acquisition', NULL, 'trading-data', 'approved provider terminology; credential secret values are stored outside Git under source-level JSON secret files'),
  ('cfg_ZQVMQNHJ', 'config', 'FRED_SECRET_ALIAS', 'secret_alias', 'fred', '/root/secrets/fred.json', 'trading-data', 'source-level secret JSON alias for FRED credentials; JSON keys include api_key; secret values are stored outside Git'),
  ('cfg_QMYZOV7G', 'config', 'CENSUS_SECRET_ALIAS', 'secret_alias', 'census', '/root/secrets/census.json', 'trading-data', 'source-level secret JSON alias for US Census credentials; JSON keys include api_key; secret values are stored outside Git'),
  ('cfg_5H5JFTAE', 'config', 'BEA_SECRET_ALIAS', 'secret_alias', 'bea', '/root/secrets/bea.json', 'trading-data', 'source-level secret JSON alias for BEA credentials; JSON keys include api_key; secret values are stored outside Git'),
  ('cfg_2ZQJ5MSW', 'config', 'BLS_SECRET_ALIAS', 'secret_alias', 'bls', '/root/secrets/bls.json', 'trading-data', 'source-level secret JSON alias for BLS credentials; JSON keys include api_key; secret values are stored outside Git')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

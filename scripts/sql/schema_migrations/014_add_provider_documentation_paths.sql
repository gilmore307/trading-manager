-- Add official documentation URLs to provider term path fields.
-- Secret config rows keep local source-secret JSON file paths.
-- Target engine: PostgreSQL.

UPDATE trading_registry AS r
SET path = v.documentation_url
FROM (VALUES
  ('trm_C4BJ2YGX', 'https://www.okx.com/docs-v5/en/'),
  ('trm_EOC5GSA5', 'https://docs.alpaca.markets/'),
  ('trm_NRG6N2KE', 'https://http-docs.thetadata.us/'),
  ('trm_JJH2NQ4J', 'https://fred.stlouisfed.org/docs/api/fred/'),
  ('trm_EBCO7NKH', 'https://www.census.gov/data/developers/guidance/api-user-guide.html'),
  ('trm_QEOTBESR', 'https://apps.bea.gov/API/docs/index.htm'),
  ('trm_ZJYP6B4O', 'https://www.bls.gov/developers/api_signature_v2.htm')
) AS v(id, documentation_url)
WHERE r.id = v.id;

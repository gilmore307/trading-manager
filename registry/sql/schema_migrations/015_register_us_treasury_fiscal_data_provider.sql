-- Register U.S. Treasury Fiscal Data as a no-key/open API provider term.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_KYPNDRE6', 'term', 'US_TREASURY_FISCAL_DATA', 'text', 'U.S. Treasury Fiscal Data REST API provider for federal finance datasets including debt, revenue, spending, interest rates, and savings bonds', 'https://fiscaldata.treasury.gov/api-documentation/', 'trading-data', 'approved provider terminology and documentation locator; official docs describe the API as open and not requiring a user account or token, so no secret alias is registered yet')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

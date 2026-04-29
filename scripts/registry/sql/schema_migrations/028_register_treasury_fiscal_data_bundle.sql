-- Register U.S. Treasury Fiscal Data as its own no-key historical data acquisition bundle.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dbu_ZAP34060', 'data_bundle', 'TREASURY_FISCAL_DATA', 'text', 'treasury_fiscal_data', 'https://fiscaldata.treasury.gov/api-documentation/', 'trading-data', 'standalone no-key U.S. Treasury Fiscal Data bundle for federal finance datasets; task/run IDs should use treasury_fiscal_data-specific prefixes')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

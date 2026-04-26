-- Consolidate macro acquisition into one parameterized macro_data bundle.
-- Target engine: PostgreSQL.

DELETE FROM trading_registry
WHERE id IN ('dbu_1J9Y65GU', 'dbu_ZAP34060')
   OR key IN ('MACRO_RELEASE_BUNDLE_PATTERN', 'TREASURY_FISCAL_DATA');

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dbu_0A8O6R01', 'data_bundle', 'MACRO_DATA', 'text', 'macro_data', NULL, 'trading-data', 'single parameterized macro data acquisition bundle for FRED, BLS, Census, BEA, U.S. Treasury Fiscal Data, and official macro source pages; task params must select source, dataset/release/series, cadence, and output target')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

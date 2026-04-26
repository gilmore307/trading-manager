-- Register ThetaData as an options-data provider term.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('trm_NRG6N2KE', 'term', 'THETADATA', 'text', 'ThetaData options market-data provider intended for option chain timeline, quote, trade, OHLC, Greeks, and related options datasets', NULL, 'trading-data', 'approved provider terminology only; credentials and ThetaTerminal creds.txt/JAR placement are intentionally deferred until the source connector boundary is designed')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

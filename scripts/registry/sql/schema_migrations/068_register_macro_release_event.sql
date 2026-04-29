-- Register macro releases as first-class market-impact events.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dki_MACREVT1', 'data_kind', 'MACRO_RELEASE_EVENT', 'text', 'macro_release_event', 'trading-data/storage/templates/data_kinds/events/macro_release_event.preview.csv', 'macro_data;event_database', 'Market-impact event row for a macroeconomic data publication such as CPI, payrolls, PCE, GDP, or rates; complements macro_release fact rows and is the event-layer object used for event factors/reaction labels')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

UPDATE trading_registry
SET note = 'SQL-shaped long-term macro metric fact row; stores observed macro values and release-time validity while macro_release_event owns market-impact event semantics and downstream event factors'
WHERE kind = 'data_kind'
  AND key = 'MACRO_RELEASE';

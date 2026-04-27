-- Add impact scope fields to unified event database templates.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_EVT043', 'field', 'EVENT_IMPACT_SCOPE', 'text', 'impact_scope', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_factor_template;event_analysis_report_template', 'event impact layer such as market, sector, industry, theme, security, multi_security, macro, or unknown; used to avoid treating broad-market events as single-stock events'),
  ('fld_EVT044', 'field', 'EVENT_IMPACTED_UNIVERSE', 'text', 'impacted_universe', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_factor_template;event_analysis_report_template', 'semicolon-separated or JSON-text impacted market/sector/industry/theme/security identifiers affected by the event, e.g. US_MARKET, semiconductors, or AAPL'),
  ('fld_EVT045', 'field', 'EVENT_PRIMARY_IMPACT_TARGET', 'text', 'primary_impact_target', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_factor_template;event_analysis_report_template', 'primary modeled impact target for scoring/routing, distinct from source-mentioned symbols when a broad event affects a market or sector')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

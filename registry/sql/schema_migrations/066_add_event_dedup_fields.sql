-- Add unified event database fields for source priority and duplicate coverage.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_EVT039', 'field', 'EVENT_CANONICAL_EVENT_ID', 'text', 'canonical_event_id', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_factor_template;event_analysis_report_template', 'canonical event id after deduplication; equals event_id for canonical rows and points to the official/source-of-truth event when this row is covered by another event'),
  ('fld_EVT040', 'field', 'EVENT_DEDUP_STATUS', 'text', 'dedup_status', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_analysis_report_template', 'deduplication state such as canonical, covered_by_official_source, duplicate, related_followup, or unresolved; covered news should not create independent alpha events'),
  ('fld_EVT041', 'field', 'EVENT_SOURCE_PRIORITY', 'text', 'source_priority', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_analysis_report_template', 'numeric or ordinal source priority used to choose canonical events; official SEC/exchange/company/regulator disclosures outrank downstream news coverage'),
  ('fld_EVT042', 'field', 'EVENT_COVERAGE_REASON', 'text', 'coverage_reason', 'trading-data/storage/templates/data_kinds/events/README.md', 'trading_event_template;event_analysis_report_template', 'short explanation for why an event row is canonical or covered, including source overlap, same accession/event identity, or near-duplicate content/time/entity match')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

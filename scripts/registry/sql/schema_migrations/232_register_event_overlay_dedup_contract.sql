-- Register the active source_04_event_overlay canonical-event deduplication contract.
-- Duplicate SEC/company/regulatory coverage should not become duplicate alpha.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('fld_EVT039', 'identity_field', 'EVENT_CANONICAL_EVENT_ID', 'field_name', 'canonical_event_id', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Identity value for the canonical event after deduplication. Equals event_id for canonical rows and points to the official/source-of-truth event when derivative coverage is covered or duplicated.'),
  ('fld_EVT040', 'classification_field', 'EVENT_DEDUP_STATUS', 'field_name', 'dedup_status', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Stable lowercase status token for event deduplication: canonical, covered_by_canonical_event, duplicate_of_canonical_event, related_followup, new_information, or unresolved. Covered duplicate news must not create independent event-factor alpha.'),
  ('fld_EVT041', 'field', 'EVENT_SOURCE_PRIORITY', 'field_name', 'source_priority', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Ordinal source-priority token used to choose canonical event rows. Official SEC/exchange/company/regulatory disclosures outrank derivative news coverage.'),
  ('fld_EVT042', 'text_field', 'EVENT_COVERAGE_REASON', 'field_name', 'coverage_reason', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Text value explaining why an event row is canonical, covered by a canonical event, duplicate, related follow-up, new information, or unresolved.'),
  ('fld_EVT046', 'identity_field', 'EVENT_COVERED_BY_EVENT_ID', 'field_name', 'covered_by_event_id', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Identity value naming the canonical event that covers this derivative or duplicate evidence row. Usually equals canonical_event_id for covered_by_canonical_event and duplicate_of_canonical_event rows.'),
  ('cfg_EVD001', 'config', 'EVENT_DEDUP_STATUS_VALUES', 'text', 'canonical;covered_by_canonical_event;duplicate_of_canonical_event;related_followup;new_information;unresolved', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Allowed dedup_status values for source_04_event_overlay. Only canonical and genuinely new_information rows may create independent event-presence/factor evidence; covered/duplicate rows are supporting context.'),
  ('cfg_EVD002', 'config', 'EVENT_SOURCE_PRIORITY_VALUES', 'text', 'official_disclosure;official_data_release;company_disclosure;regulatory_disclosure;source_detector;verified_news;broad_news;derivative_news;unknown', 'trading-data/src/data_source/source_04_event_overlay/README.md', 'source_04_event_overlay;event_overlay_model;event_context_vector', 'sync_artifact', 'Allowed source_priority values for canonical-event selection. Official disclosure/data rows outrank derivative news; browser/agent article reading may support classification but does not change source priority by itself.')
ON CONFLICT (id) DO UPDATE SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note,
  updated_at = NOW();

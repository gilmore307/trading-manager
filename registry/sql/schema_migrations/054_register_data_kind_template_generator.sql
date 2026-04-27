-- Register data-kind preview template generator and align timestamp fields with generated detail templates.
-- Target engine: PostgreSQL.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  ('scr_DK7P2M4Q', 'script', 'DATA_KIND_TEMPLATE_GENERATOR', 'command', 'trading-data-generate-data-kind-templates', '/root/projects/trading-data/src/trading_data/template_generators/data_kind_previews.py', 'trading-data/templates/data_kinds', 'sync_artifact', 'generator that materializes final data-kind CSV/JSON output templates from stable registry ids and the current registry payload field names')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  artifact_sync_policy = EXCLUDED.artifact_sync_policy,
  note = EXCLUDED.note;

UPDATE trading_registry
SET applies_to = 'event_timeline_template;option_activity_event_detail_template',
    note = 'event/news or event-detail creation timestamp in America/New_York'
WHERE kind = 'field'
  AND key = 'TIMELINE_CREATED_AT_ET';

UPDATE trading_registry
SET applies_to = 'event_timeline_template;option_activity_event_detail_template',
    note = 'event/news or event-detail update timestamp in America/New_York'
WHERE kind = 'field'
  AND key = 'TIMELINE_UPDATED_AT_ET';

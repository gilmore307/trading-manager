-- Clarify generated source_04_event_overlay event identity discriminators.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_EVTID001',
    'config',
    'EVENT_ID_GENERATED_ID_DISCRIMINATORS',
    'text',
    'event_category_type;source_name;event_time;symbol;title_or_headline;reference',
    'trading-data/src/data_source/source_04_event_overlay/pipeline.py;trading-data/src/data_source/source_04_event_overlay/README.md',
    'source_04_event_overlay;event_id;event_identity;macro_calendar;event_artifact_paths',
    'sync_artifact',
    'Generated source_04_event_overlay event ids include title/headline in addition to category, source, time, symbol, and reference so same-timestamp calendar releases such as core CPI and CPI remain distinct rows.'
  )
ON CONFLICT (id) DO UPDATE
SET kind = EXCLUDED.kind,
    key = EXCLUDED.key,
    payload_format = EXCLUDED.payload_format,
    payload = EXCLUDED.payload,
    path = EXCLUDED.path,
    applies_to = EXCLUDED.applies_to,
    artifact_sync_policy = EXCLUDED.artifact_sync_policy,
    note = EXCLUDED.note,
    updated_at = NOW();

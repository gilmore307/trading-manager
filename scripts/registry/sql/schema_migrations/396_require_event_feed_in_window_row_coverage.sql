-- Require requested-window row coverage, not just artifact presence, for Layer 4 event feeds.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'term_L4EVTCOV002',
    'term',
    'LAYER_FOUR_EVENT_FEED_IN_WINDOW_ROW_COVERAGE',
    'text',
    'layer_four_event_feed_in_window_row_coverage',
    'trading-manager/src/trading_manager_tasks/layer_four_event_overlay.py;trading-manager/docs/81_decision.md;trading-manager/docs/95_task_system.md',
    'layer_04_event_overlay;source_04_event_overlay;event_source_coverage;event_feed_coverage;requested_window',
    'sync_artifact',
    'Layer 4 write-mode materialization requires each required reviewed event-feed artifact family to contain at least one row in the requested [start_month, end_month_next) window. Artifact presence alone is not sufficient.'
  ),
  (
    'fld_L4EVTCOV002',
    'field',
    'EVENT_FEED_ROW_COVERAGE',
    'field_name',
    'event_feed_row_coverage',
    'trading-manager/src/trading_manager_tasks/layer_four_event_overlay.py',
    'manager_layer_four_event_overlay_input_materialization;event_source_coverage;requested_window',
    'sync_artifact',
    'Summary field reporting requested-window row counts by required event feed source for the Layer 4 event-overlay coverage gate.'
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

UPDATE trading_registry
SET note = 'Layer 4 write-mode materialization must have reviewed local artifacts with requested-window row coverage for Alpaca news, GDELT news, SEC company financials, and Trading Economics calendar rows before downstream Layer 4+ model stages may advance.',
    updated_at = NOW()
WHERE id = 'term_L4EVTCOV001';

UPDATE trading_registry
SET note = 'Required reviewed saved feed artifacts for a complete Layer 4 event-overlay rebuild. Missing artifacts or zero requested-window row coverage block write-mode materialization.',
    updated_at = NOW()
WHERE id = 'cfg_L4EVTCOV001';

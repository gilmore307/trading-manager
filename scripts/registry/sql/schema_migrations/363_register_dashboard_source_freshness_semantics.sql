-- Register Dashboard Data source freshness semantics.
-- Dashboard source-output timestamps are source artifact write times, not dashboard read-model refresh times.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_DASHDATA001',
    'field',
    'DASHBOARD_SOURCE_OUTPUT_FRESHNESS_CLASS',
    'field_name',
    'freshness_class',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;dashboard_source_outputs;dashboard_data;source_artifact_freshness',
    'sync_artifact',
    'Classifies how a dashboard source artifact is expected to refresh. Heartbeat artifacts should move on scheduler heartbeat; event-driven artifacts move only when decisions or stage progress occur.'
  ),
  (
    'fld_DASHDATA002',
    'field',
    'DASHBOARD_SOURCE_OUTPUT_FRESHNESS_NOTE',
    'field_name',
    'freshness_note',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/09_dashboard_read_models.md',
    'current_system_status_summary;dashboard_source_outputs;dashboard_data;source_artifact_freshness',
    'sync_artifact',
    'Human-readable explanation of source artifact freshness behavior so old event-driven timestamps are not mistaken for dashboard refresh failures.'
  ),
  (
    'cfg_DASHDATA001',
    'config',
    'DASHBOARD_SOURCE_OUTPUT_FRESHNESS_CLASSES',
    'text',
    'heartbeat;event_driven',
    'trading-storage/docs/96_dashboard_read_models.md;trading-dashboard/docs/05_decision.md',
    'current_system_status_summary;dashboard_data;source_artifact_freshness;owner_facing_status',
    'sync_artifact',
    'Accepted freshness classes for Dashboard Data source-output rows. Heartbeat rows indicate service health; event-driven rows indicate latest source event/progress write.'
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

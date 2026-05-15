-- Register earnings/guidance event-overview materialization route.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'trm_EGFM001',
    'term',
    'EARNINGS_GUIDANCE_EVENT_OVERVIEW_ROW',
    'text',
    'earnings_guidance',
    'trading-data/src/data_source/source_04_event_overlay',
    'source_04_event_overlay;earnings_guidance_event_family;event_family_scouting_packet_v1',
    'sync_artifact',
    'Layer 4 source event category for earnings/guidance overview rows. Calendar rows are scheduled shells only; official SEC/company artifacts are result/guidance evidence.'
  ),
  (
    'cfg_EGFM001',
    'config',
    'EARNINGS_GUIDANCE_EVENT_OVERVIEW_MATERIALIZATION',
    'text',
    'nasdaq_release_calendar_to_scheduled_shell;sec_10q_10k_earnings_8k_to_result_artifact;news_as_discovery_or_narrative_residual_only;option_activity_as_bridge_evidence_only',
    'trading-data/src/data_source/source_04_event_overlay/feed_event_extraction.py',
    'earnings_guidance_event_family;source_04_event_overlay;event_interpretation_v1;event_activity_bridge',
    'sync_artifact',
    'Accepted first materialization route for earnings/guidance scouting. It creates point-in-time overview rows but does not perform final family interpretation, controls, model training, or promotion.'
  ),
  (
    'trm_EGFM002',
    'term',
    'APPROVED_CALENDAR_SOURCE_PRIORITY',
    'text',
    'approved_calendar',
    'trading-data/src/data_source/source_04_event_overlay/pipeline.py',
    'source_priority;source_04_event_overlay;calendar_discovery;earnings_guidance_event_family',
    'sync_artifact',
    'Source priority value for reviewed/approved calendar shells such as Nasdaq earnings calendar. It is weaker than official result disclosure and must not carry result facts.'
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

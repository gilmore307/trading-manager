-- Register option event timeline auto-enrichment inputs and ThetaData context endpoints.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'cfg_ABNCOV006',
    'config',
    'OPTION_EVENT_TIMELINE_AUTO_ENRICH_OPTION_CONTEXT',
    'field_name',
    'auto_enrich_option_context',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Task-key switch enabling point-in-time ThetaData context enrichment for OI, IV/change, skew, term structure, and underlying confirmation evidence.'
  ),
  (
    'cfg_ABNCOV007',
    'config',
    'OPTION_EVENT_TIMELINE_OPTION_CONTEXT_INTERVAL',
    'field_name',
    'option_context_interval',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'ThetaData historical Greeks interval for option context enrichment; default is 1m to avoid oversized one-second Greek responses.'
  ),
  (
    'cfg_ABNCOV008',
    'config',
    'OPTION_EVENT_TIMELINE_PRIOR_CONTEXT_DATE',
    'field_name',
    'prior_context_date',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Optional prior trading date used for point-in-time open-interest change comparison during option context enrichment.'
  ),
  (
    'cfg_ABNCOV009',
    'config',
    'OPTION_EVENT_TIMELINE_TERM_STRUCTURE_EXPIRATION',
    'field_name',
    'term_structure_expiration',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Optional comparison expiration used for same-strike term-structure context during option event enrichment.'
  ),
  (
    'api_THD011',
    'config',
    'THETADATA_OPTION_HISTORY_OPEN_INTEREST_ENDPOINT',
    'text',
    '/v3/option/history/open_interest',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;open_interest_context;option_abnormality_coverage',
    'sync_artifact',
    'ThetaData option history endpoint used to retrieve point-in-time open-interest snapshots for current/prior OI-change evidence.'
  ),
  (
    'api_THD012',
    'config',
    'THETADATA_OPTION_HISTORY_GREEKS_IMPLIED_VOLATILITY_ENDPOINT',
    'text',
    '/v3/option/history/greeks/implied_volatility',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;iv_context;skew_context;term_structure_context;underlying_context;option_abnormality_coverage',
    'sync_artifact',
    'ThetaData option history Greeks endpoint used to retrieve point-in-time IV/change, same-strike skew, term-structure, and underlying-price confirmation evidence.'
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

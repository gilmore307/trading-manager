-- Register concrete option abnormality coverage fields emitted by option event timeline.

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, artifact_sync_policy, note)
VALUES
  (
    'fld_OPD057',
    'field',
    'OPTION_EVENT_DETAIL_BID_TOUCH_RATIO',
    'field_name',
    'bid_touch_ratio',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Quote-touch ratio measuring proximity to bid; paired with ask_touch_ratio for side/aggressor evidence.'
  ),
  (
    'fld_OPD058',
    'field',
    'OPTION_EVENT_DETAIL_TRADE_NOTIONAL',
    'field_name',
    'trade_notional',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Event-local trade notional used by sweep/block and abnormal option activity evaluation.'
  ),
  (
    'fld_OPD059',
    'field',
    'OPTION_EVENT_DETAIL_TRADE_SIDE_EVIDENCE',
    'field_name',
    'trade_side_evidence',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Structured side/aggressor evidence including quote-touch classification and missing-status metadata.'
  ),
  (
    'fld_OPD060',
    'field',
    'OPTION_EVENT_DETAIL_SWEEP_OR_BLOCK_CONTEXT',
    'field_name',
    'sweep_or_block_context',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Sweep/block evidence and thresholds; missing if provider flags or reviewed block standards are absent.'
  ),
  (
    'fld_OPD061',
    'field',
    'OPTION_EVENT_DETAIL_OPEN_INTEREST_CONTEXT',
    'field_name',
    'open_interest_context',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Point-in-time open-interest context including before/after/change and source reference when available.'
  ),
  (
    'fld_OPD062',
    'field',
    'OPTION_EVENT_DETAIL_OPENING_OR_CLOSING_CONTEXT',
    'field_name',
    'opening_or_closing_context',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Opening/closing inference derived from OI change when present; volume-only first-seen evidence remains partial.'
  ),
  (
    'fld_OPD063',
    'field',
    'OPTION_EVENT_DETAIL_IV_CHANGE',
    'field_name',
    'iv_change',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Point-in-time implied-volatility change used for option abnormality coverage.'
  ),
  (
    'fld_OPD064',
    'field',
    'OPTION_EVENT_DETAIL_SKEW_DIRECTION',
    'field_name',
    'skew_direction',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Point-in-time skew direction evidence for option abnormality studies.'
  ),
  (
    'fld_OPD065',
    'field',
    'OPTION_EVENT_DETAIL_TERM_STRUCTURE_DIRECTION',
    'field_name',
    'term_structure_direction',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Point-in-time term-structure direction evidence for option abnormality studies.'
  ),
  (
    'fld_OPD066',
    'field',
    'OPTION_EVENT_DETAIL_UNDERLYING_CONFIRMATION_OR_DIVERGENCE',
    'field_name',
    'underlying_confirmation_or_divergence',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Point-in-time underlying confirmation/divergence context for option activity direction hypotheses.'
  ),
  (
    'fld_OPD067',
    'field',
    'OPTION_EVENT_DETAIL_DIRECTION_CONFIDENCE',
    'field_name',
    'direction_confidence',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;directional_activity_evidence',
    'sync_artifact',
    'Direction hypothesis confidence object; incomplete evidence must produce insufficient_evidence rather than a final label.'
  ),
  (
    'fld_OPD068',
    'field',
    'OPTION_EVENT_DETAIL_ABNORMALITY_EVIDENCE_COVERAGE',
    'field_name',
    'abnormality_evidence_coverage',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;proof_gate',
    'sync_artifact',
    'Coverage object listing present and missing required abnormality fields before directional or promotion judgment.'
  ),
  (
    'cfg_ABNCOV005',
    'config',
    'OPTION_EVENT_TIMELINE_ABNORMALITY_COVERAGE_OUTPUT_FIELDS',
    'text',
    'bid_touch_ratio;trade_notional;trade_side_evidence;sweep_or_block_context;open_interest_context;opening_or_closing_context;iv_change;skew_direction;term_structure_direction;underlying_confirmation_or_divergence;direction_confidence;abnormality_evidence_coverage',
    'trading-data/src/data_feed/11_feed_thetadata_option_event_timeline/pipeline.py',
    'option_activity_event_detail;option_abnormality_coverage;event_activity_bridge;proof_gate',
    'sync_artifact',
    'Concrete event-detail output fields used to decide whether option abnormality coverage is complete.'
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

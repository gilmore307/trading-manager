-- Add event-time current standards to option activity event details.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'Compact nested JSON detail artifact for one option_activity_event; event_id matches the stable random CSV id and triggered_indicators is an object keyed by abnormal indicator type with each child storing objective observed statistics plus the event-time current_standard produced by the detection model'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT_DETAIL';

UPDATE trading_registry
SET
  note = 'object keyed by abnormal indicator type; each child object owns objective observed statistics and the event-time current_standard used by the detection model for that indicator type'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_TRIGGERED_INDICATORS';

UPDATE trading_registry
SET
  note = 'nested objective observed statistical values for one triggered abnormal indicator type; compare with sibling current_standard for audit context'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_STATISTICS';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_OPD044', 'field', 'OPTION_EVENT_DETAIL_STANDARD_CONTEXT', 'field_name', 'standard_context', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'metadata for the model-produced event-time standard used to emit the option activity event'),
  ('fld_OPD045', 'field', 'OPTION_EVENT_DETAIL_STANDARD_SOURCE', 'field_name', 'standard_source', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'source that produced the event-time current standard, usually the option event detection model'),
  ('fld_OPD046', 'field', 'OPTION_EVENT_DETAIL_STANDARD_ID', 'field_name', 'standard_id', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'stable random identifier for the model-produced event-time standard snapshot'),
  ('fld_OPD047', 'field', 'OPTION_EVENT_DETAIL_STANDARD_GENERATED_AT_ET', 'field_name', 'standard_generated_at_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'timestamp in America/New_York when the model-produced current standard was generated or selected for this event'),
  ('fld_OPD048', 'field', 'OPTION_EVENT_DETAIL_CURRENT_STANDARD', 'field_name', 'current_standard', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'event-time standard produced by the detection model for one triggered indicator type; not a global fixed threshold and may change across model versions/runs'),
  ('fld_OPD049', 'field', 'OPTION_EVENT_STANDARD_MAX_PRICE_VS_ASK', 'field_name', 'max_price_vs_ask', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'current_standard value for maximum allowed trade price minus contemporaneous ask for ask-side activity'),
  ('fld_OPD050', 'field', 'OPTION_EVENT_STANDARD_MIN_ASK_TOUCH_RATIO', 'field_name', 'min_ask_touch_ratio', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'current_standard value for minimum ask-touch ratio for ask-side activity'),
  ('fld_OPD051', 'field', 'OPTION_EVENT_STANDARD_MIN_WINDOW_VOLUME', 'field_name', 'min_window_volume', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'current_standard value for minimum event-window volume for opening activity'),
  ('fld_OPD052', 'field', 'OPTION_EVENT_STANDARD_MIN_VOLUME_PERCENTILE_20D_SAME_TIME', 'field_name', 'min_volume_percentile_20d_same_time', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'current_standard value for minimum same-time 20-day volume percentile for opening activity'),
  ('fld_OPD053', 'field', 'OPTION_EVENT_STANDARD_MIN_IV_PERCENTILE_BY_EXPIRATION', 'field_name', 'min_iv_percentile_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'current_standard value for minimum expiration-cross-section IV percentile for high-IV activity'),
  ('fld_OPD054', 'field', 'OPTION_EVENT_STANDARD_MIN_IV_ZSCORE_BY_EXPIRATION', 'field_name', 'min_iv_zscore_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'current_standard value for minimum expiration-cross-section IV z-score for high-IV activity')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

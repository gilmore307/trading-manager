-- Refine option activity event ids, detail links, and per-trigger metric tables.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'Final news-like option activity event row using the minimal shared event/news timeline fields; every row has a stable random id, headline is human-facing, summary carries only abnormal indicator type names, url is <id>.json pointing to the detail artifact, and scoring/normal metrics belong to downstream models'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT';

UPDATE trading_registry
SET
  note = 'Compact nested JSON detail artifact for one option_activity_event; event_id matches the stable random CSV id and triggered_indicators is an object keyed by abnormal indicator type with each child storing its specific trigger metrics and thresholds'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT_DETAIL';

UPDATE trading_registry
SET
  note = 'short human-readable event/news summary; for option_activity_event this must contain only abnormal indicator type names and must not include normal metrics, trigger values, thresholds, or scoring values'
WHERE kind = 'field'
  AND key = 'TIMELINE_SUMMARY';

UPDATE trading_registry
SET
  note = 'link for a news/event timeline row; for equity_news this is the original article URL, and for option_activity_event this is the stable detail artifact filename <id>.json'
WHERE kind = 'field'
  AND key = 'TIMELINE_URL';

UPDATE trading_registry
SET
  note = 'stable random event detail identifier matching the option_activity_event CSV row id; do not encode timestamp, contract, or trigger semantics into the id'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_EVENT_ID';

UPDATE trading_registry
SET
  note = 'object keyed by abnormal indicator type; each child object owns the specific trigger metrics and thresholds for that event type'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_TRIGGERED_INDICATORS';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_OPD019', 'field', 'OPTION_EVENT_TRIGGER_TRADE_AT_ASK', 'field_name', 'trade_at_ask', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'triggered_indicators key for an option trade executed at or near the ask'),
  ('fld_OPD020', 'field', 'OPTION_EVENT_TRIGGER_OPENING_ACTIVITY', 'field_name', 'opening_activity', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'triggered_indicators key for opening option activity detected in the evidence window'),
  ('fld_OPD021', 'field', 'OPTION_EVENT_TRIGGER_IV_HIGH_CROSS_SECTION', 'field_name', 'iv_high_cross_section', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'triggered_indicators key for high implied volatility versus the expiration cross-section'),
  ('fld_OPD022', 'field', 'OPTION_EVENT_DETAIL_TRIGGER_METRICS', 'field_name', 'trigger_metrics', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested metric values that caused one abnormal indicator type to trigger'),
  ('fld_OPD023', 'field', 'OPTION_EVENT_DETAIL_THRESHOLDS', 'field_name', 'thresholds', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested threshold values used to evaluate one abnormal indicator type'),
  ('fld_OPD024', 'field', 'OPTION_EVENT_DETAIL_TRADE_PRICE', 'field_name', 'trade_price', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'trade price metric used inside a trigger-specific metric table'),
  ('fld_OPD025', 'field', 'OPTION_EVENT_DETAIL_QUOTE_BID', 'field_name', 'quote_bid', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'quote bid metric used inside a trigger-specific metric table'),
  ('fld_OPD026', 'field', 'OPTION_EVENT_DETAIL_QUOTE_ASK', 'field_name', 'quote_ask', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'quote ask metric used inside a trigger-specific metric table'),
  ('fld_OPD027', 'field', 'OPTION_EVENT_DETAIL_QUOTE_MID', 'field_name', 'quote_mid', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'quote midpoint metric used inside a trigger-specific metric table'),
  ('fld_OPD028', 'field', 'OPTION_EVENT_DETAIL_PRICE_VS_ASK', 'field_name', 'price_vs_ask', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'trade price minus ask metric used to identify ask-side activity'),
  ('fld_OPD029', 'field', 'OPTION_EVENT_DETAIL_MAX_PRICE_VS_ASK', 'field_name', 'max_price_vs_ask', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'threshold for maximum trade price minus ask distance allowed for ask-side activity'),
  ('fld_OPD030', 'field', 'OPTION_EVENT_DETAIL_WINDOW_TRADE_COUNT', 'field_name', 'window_trade_count', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'trade count metric accumulated in the event evidence window'),
  ('fld_OPD031', 'field', 'OPTION_EVENT_DETAIL_WINDOW_VOLUME', 'field_name', 'window_volume', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'contract volume metric accumulated in the event evidence window'),
  ('fld_OPD032', 'field', 'OPTION_EVENT_DETAIL_WINDOW_NOTIONAL', 'field_name', 'window_notional', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'notional value metric accumulated in the event evidence window'),
  ('fld_OPD033', 'field', 'OPTION_EVENT_DETAIL_FIRST_SEEN_IN_WINDOW', 'field_name', 'first_seen_in_window', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'boolean metric indicating the contract first appeared or first traded in the current event window'),
  ('fld_OPD034', 'field', 'OPTION_EVENT_DETAIL_MIN_WINDOW_VOLUME', 'field_name', 'min_window_volume', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'minimum window volume threshold for opening-activity detection'),
  ('fld_OPD035', 'field', 'OPTION_EVENT_DETAIL_IMPLIED_VOL', 'field_name', 'implied_vol', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'implied volatility value used in event-local IV context or trigger metrics'),
  ('fld_OPD036', 'field', 'OPTION_EVENT_DETAIL_MIN_IV_PERCENTILE_BY_EXPIRATION', 'field_name', 'min_iv_percentile_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'minimum expiration-cross-section IV percentile threshold for high-IV option activity')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

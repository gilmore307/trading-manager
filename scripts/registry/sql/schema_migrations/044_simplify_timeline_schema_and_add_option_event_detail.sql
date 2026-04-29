-- Simplify shared event/news timeline rows and register option event detail artifacts.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'Final persisted Alpaca stock/ETF news row using the minimal shared event/news timeline fields; source, author, image, and full article content metadata are omitted from the model-facing final row unless later proven useful'
WHERE kind = 'data_kind'
  AND key = 'EQUITY_NEWS';

UPDATE trading_registry
SET
  note = 'Final news-like option activity event row using the minimal shared event/news timeline fields; every row has a stable id, headline is human-facing, summary carries only triggered abnormal indicators, url links to the detail artifact, and scoring/normal metrics belong to downstream models'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('dki_OPDET01', 'data_kind', 'OPTION_ACTIVITY_EVENT_DETAIL', 'text', 'option_activity_event_detail', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'thetadata_option_event_timeline', 'Compact nested JSON detail artifact for one option_activity_event; stores event-local contract, trigger, quote, IV, and source-reference context linked from the CSV row url')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN ('TIMELINE_AUTHOR', 'TIMELINE_IMAGE_COUNT');

UPDATE trading_registry
SET
  note = 'link for a news/event timeline row; for equity_news this is the original article URL, and for option_activity_event this is the local or durable event detail artifact URI/path'
WHERE kind = 'field'
  AND key = 'TIMELINE_URL';

UPDATE trading_registry
SET
  note = 'short human-readable event/news summary; for option_activity_event this must contain only triggered abnormal indicators and must not include normal metrics or scoring values'
WHERE kind = 'field'
  AND key = 'TIMELINE_SUMMARY';

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_OPD001', 'field', 'OPTION_EVENT_DETAIL_EVENT_ID', 'field_name', 'event_id', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'event detail identifier matching the option_activity_event CSV row id'),
  ('fld_OPD002', 'field', 'OPTION_EVENT_DETAIL_CONTRACT', 'field_name', 'contract', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested option contract context for the emitted event'),
  ('fld_OPD003', 'field', 'OPTION_EVENT_DETAIL_CONTRACT_SYMBOL', 'field_name', 'symbol', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'human-readable option contract symbol for the emitted event'),
  ('fld_OPD004', 'field', 'OPTION_EVENT_DETAIL_TRIGGERED_INDICATORS', 'field_name', 'triggered_indicators', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'array of abnormal indicators that caused the option activity event to be emitted'),
  ('fld_OPD005', 'field', 'OPTION_EVENT_DETAIL_EVIDENCE_WINDOW', 'field_name', 'evidence_window', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested event-local window context used to evaluate abnormal activity'),
  ('fld_OPD006', 'field', 'OPTION_EVENT_DETAIL_WINDOW_START_ET', 'field_name', 'window_start_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'event detail evidence window start timestamp in America/New_York'),
  ('fld_OPD007', 'field', 'OPTION_EVENT_DETAIL_WINDOW_END_ET', 'field_name', 'window_end_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'event detail evidence window end timestamp in America/New_York'),
  ('fld_OPD008', 'field', 'OPTION_EVENT_DETAIL_TRIGGERING_TRADE', 'field_name', 'triggering_trade', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested triggering trade context for the emitted event'),
  ('fld_OPD009', 'field', 'OPTION_EVENT_DETAIL_SIDE_HINT', 'field_name', 'side_hint', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'derived side hint such as ask_side when the event fired'),
  ('fld_OPD010', 'field', 'OPTION_EVENT_DETAIL_QUOTE_CONTEXT', 'field_name', 'quote_context', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested quote context near the triggering event'),
  ('fld_OPD011', 'field', 'OPTION_EVENT_DETAIL_IV_CONTEXT', 'field_name', 'iv_context', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested implied-volatility context near the triggering event'),
  ('fld_OPD012', 'field', 'OPTION_EVENT_DETAIL_IV_PERCENTILE_BY_EXPIRATION', 'field_name', 'iv_percentile_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'cross-sectional IV percentile within the contract expiration used as event context'),
  ('fld_OPD013', 'field', 'OPTION_EVENT_DETAIL_SOURCE_REFS', 'field_name', 'source_refs', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested provider/source-reference metadata for the event detail artifact'),
  ('fld_OPD014', 'field', 'OPTION_EVENT_DETAIL_PROVIDER', 'field_name', 'provider', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'provider name for the event detail source context'),
  ('fld_OPD015', 'field', 'OPTION_EVENT_DETAIL_RAW_PERSISTENCE', 'field_name', 'raw_persistence', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'raw provider persistence rule for event-local source context'),
  ('fld_OPD016', 'field', 'OPTION_EVENT_DETAIL_TIMESTAMP_ET', 'field_name', 'timestamp_et', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested event detail timestamp in America/New_York'),
  ('fld_OPD017', 'field', 'OPTION_EVENT_DETAIL_PRICE', 'field_name', 'price', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'price value in event-local detail context'),
  ('fld_OPD018', 'field', 'OPTION_EVENT_DETAIL_SIZE', 'field_name', 'size', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'trade size value in event-local detail context')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;

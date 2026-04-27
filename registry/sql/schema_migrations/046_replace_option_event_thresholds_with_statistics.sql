-- Replace option activity event preset thresholds with objective observed statistics.
-- Target engine: PostgreSQL.

UPDATE trading_registry
SET
  note = 'Compact nested JSON detail artifact for one option_activity_event; event_id matches the stable random CSV id and triggered_indicators is an object keyed by abnormal indicator type with each child storing objective observed statistics, not preset trigger thresholds'
WHERE kind = 'data_kind'
  AND key = 'OPTION_ACTIVITY_EVENT_DETAIL';

UPDATE trading_registry
SET
  note = 'object keyed by abnormal indicator type; each child object owns objective observed statistics for that event type and must not persist preset trigger thresholds/configuration'
WHERE kind = 'field'
  AND key = 'OPTION_EVENT_DETAIL_TRIGGERED_INDICATORS';

DELETE FROM trading_registry
WHERE kind = 'field'
  AND key IN (
    'OPTION_EVENT_DETAIL_TRIGGER_METRICS',
    'OPTION_EVENT_DETAIL_THRESHOLDS',
    'OPTION_EVENT_DETAIL_MAX_PRICE_VS_ASK',
    'OPTION_EVENT_DETAIL_MIN_WINDOW_VOLUME',
    'OPTION_EVENT_DETAIL_MIN_IV_PERCENTILE_BY_EXPIRATION'
  );

INSERT INTO trading_registry (id, kind, key, payload_format, payload, path, applies_to, note)
VALUES
  ('fld_OPD022', 'field', 'OPTION_EVENT_DETAIL_STATISTICS', 'field_name', 'statistics', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'nested objective observed statistical values for one triggered abnormal indicator type'),
  ('fld_OPD037', 'field', 'OPTION_EVENT_DETAIL_ASK_TOUCH_RATIO', 'field_name', 'ask_touch_ratio', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed ratio/indicator showing how closely the triggering trade touched the contemporaneous ask'),
  ('fld_OPD038', 'field', 'OPTION_EVENT_DETAIL_CONTRACT_PRIOR_WINDOW_VOLUME', 'field_name', 'contract_prior_window_volume', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed contract volume in the immediately comparable prior evidence window'),
  ('fld_OPD039', 'field', 'OPTION_EVENT_DETAIL_VOLUME_VS_PRIOR_WINDOW_RATIO', 'field_name', 'volume_vs_prior_window_ratio', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed current-window volume divided by comparable prior-window volume when defined'),
  ('fld_OPD040', 'field', 'OPTION_EVENT_DETAIL_VOLUME_PERCENTILE_20D_SAME_TIME', 'field_name', 'volume_percentile_20d_same_time', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed percentile of current-window volume versus the last 20 comparable same-time windows'),
  ('fld_OPD041', 'field', 'OPTION_EVENT_DETAIL_EXPIRATION_CHAIN_CONTRACT_COUNT', 'field_name', 'expiration_chain_contract_count', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed number of contracts in the expiration cross-section used for IV context'),
  ('fld_OPD042', 'field', 'OPTION_EVENT_DETAIL_IV_RANK_IN_EXPIRATION', 'field_name', 'iv_rank_in_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed rank of the contract implied volatility within its expiration cross-section'),
  ('fld_OPD043', 'field', 'OPTION_EVENT_DETAIL_IV_ZSCORE_BY_EXPIRATION', 'field_name', 'iv_zscore_by_expiration', 'trading-data/templates/data_kinds/thetadata/option_activity_event_detail.preview.json', 'option_activity_event_detail_template', 'observed z-score of the contract implied volatility within its expiration cross-section')
ON CONFLICT (id) DO UPDATE
SET
  kind = EXCLUDED.kind,
  key = EXCLUDED.key,
  payload_format = EXCLUDED.payload_format,
  payload = EXCLUDED.payload,
  path = EXCLUDED.path,
  applies_to = EXCLUDED.applies_to,
  note = EXCLUDED.note;
